"""Calibre integration; each archive gets its own copy and cache namespace."""
import importlib
import time
from queue import Queue
from urllib.parse import quote

from calibre.ebooks.metadata import check_isbn
from calibre.ebooks.metadata.book.base import Metadata
from calibre.ebooks.metadata.sources.base import Source
from calibre.library.comments import sanitize_comments_html


class KoreanBookSource(Source):
    author = 'leechis7'
    minimum_calibre_version = (5, 0, 0)
    capabilities = frozenset(('identify', 'cover'))
    has_html_comments = True
    supports_gzip_transfer_encoding = True
    namespace = identifier = detail_url = search_url = ''
    referer = ''

    def adapter(self):
        return importlib.import_module('calibre_plugins.' + self.namespace + '.worker')

    def get_book_url(self, identifiers):
        value = identifiers.get(self.identifier)
        if value and self.adapter().valid_id(str(value)):
            return self.identifier, str(value), self.detail_url.format(id=value)

    def get_cached_cover_url(self, identifiers):
        value = identifiers.get(self.identifier)
        if not value:
            isbn = check_isbn(identifiers.get('isbn'))
            if isbn:
                value = self.cached_isbn_to_identifier(isbn)
        return self.cached_identifier_to_cover_url(value) if value else None

    def create_query(self, log, title=None, authors=None, identifiers=None):
        identifiers = identifiers or {}
        isbn = check_isbn(identifiers.get('isbn'))
        keyword = isbn or ' '.join([title or ''] + list((authors or [])[:1])).strip()
        return self.search_url.format(query=quote(keyword)) if keyword else None

    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers=None, timeout=30):
        if abort.is_set():
            return
        identifiers = identifiers or {}
        adapter = self.adapter()
        cleaner = importlib.import_module('calibre_plugins.' + self.namespace + '.text_cleaner')
        deadline = time.monotonic() + timeout
        browser = self.browser
        if self.referer:
            browser.addheaders = [(k,v) for k,v in browser.addheaders if k.lower() != 'referer'] + [('Referer', self.referer)]

        def fetch(url):
            if abort.is_set():
                raise InterruptedError('Metadata download cancelled')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Metadata download timed out')
            with browser.open_novisit(url, timeout=remaining) as response:
                raw = response.read()
            if not raw.strip() and not abort.is_set():
                # Some CDN entries return a cached empty 200 response. Retry once
                # with a distinct cache key, under the original request deadline.
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Metadata download timed out')
                retry = url + ('&' if '?' in url else '?') + '_calibre=' + str(time.time_ns())
                with browser.open_novisit(retry, timeout=remaining) as response:
                    raw = response.read()
            if not raw.strip():
                raise ValueError('Empty HTTP response: ' + url)
            return cleaner.decode_html(raw)

        book_url = self.get_book_url(identifiers)
        isbn = check_isbn(identifiers.get('isbn'))
        try:
            if book_url:
                candidates = [book_url[2]]
            else:
                query = self.create_query(log, title, authors, identifiers)
                if not query:
                    log.error('검색에 필요한 제목, 저자 또는 ISBN이 없습니다.')
                    return
                candidates = adapter.search_results(fetch(query))
            found = 0
            max_results = max(1, min(20, int(self.prefs['max_results'])))
            # Bound detail requests independently of the number of accepted books.
            for url in candidates[:max_results * 3]:
                if abort.is_set() or time.monotonic() >= deadline:
                    break
                try:
                    book = adapter.parse_details(fetch(url), url)
                    if not book.get('title') or not book.get('authors') or not book.get('id'):
                        log.error('도서 필수 정보를 찾을 수 없습니다: %s' % url)
                        continue
                    if isbn and cleaner.isbn_key(book.get('isbn')) != cleaner.isbn_key(isbn):
                        continue
                    if not isbn and not book_url and title:
                        requested, actual = cleaner.normalized(title), cleaner.normalized(book['title'])
                        if requested not in actual and actual not in requested:
                            continue
                    if not isbn and not book_url and authors:
                        wanted = [cleaner.normalized(a) for a in authors]
                        actual_authors = [cleaner.normalized(a) for a in book['authors']]
                        if not any(a and b and (a in b or b in a) for a in wanted for b in actual_authors):
                            continue
                    if hasattr(adapter, 'enrich'):
                        try:
                            adapter.enrich(book, fetch)
                        except InterruptedError:
                            raise
                        except Exception:
                            log.exception('추가 도서정보를 가져오지 못했습니다: %s' % url)
                    mi = Metadata(book['title'], book['authors'])
                    mi.set_identifier(self.identifier, book['id'])
                    mi.isbn = check_isbn(book.get('isbn'))
                    mi.publisher = book.get('publisher') or None
                    mi.pubdate = cleaner.parse_date(book.get('pubdate'))
                    mi.languages = book.get('languages') or []
                    mi.tags = book.get('tags', []) if self.prefs['get_tags'] else []
                    mi.rating = book.get('rating')
                    if book.get('series'):
                        mi.series = book['series']
                    mi.comments = sanitize_comments_html(cleaner.comments(book.get('sections', []), self.prefs['append_toc']))
                    cover = book.get('cover')
                    mi.has_cover = bool(cover)
                    mi.source_relevance = found
                    self.clean_downloaded_metadata(mi)
                    if abort.is_set():
                        return
                    if mi.isbn:
                        self.cache_isbn_to_identifier(mi.isbn, book['id'])
                    if cover:
                        self.cache_identifier_to_cover_url(book['id'], cover)
                    result_queue.put(mi)
                    found += 1
                    if found >= max_results:
                        break
                except (InterruptedError, TimeoutError):
                    break
                except Exception:
                    log.exception('도서 상세정보 처리 실패: %s' % url)
            if not found and identifiers and title and not abort.is_set():
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    self.identify(log, result_queue, abort, title, authors, timeout=remaining)
        except InterruptedError:
            return
        except Exception:
            log.exception('메타데이터 검색 실패')

    def download_cover(self, log, result_queue, abort, title=None, authors=None, identifiers=None, timeout=30, get_best_cover=False):
        if abort.is_set():
            return
        identifiers = identifiers or {}
        deadline = time.monotonic() + timeout
        url = self.get_cached_cover_url(identifiers)
        if not url:
            matches = Queue()
            self.identify(log, matches, abort, title, authors, identifiers, timeout)
            results = []
            while not matches.empty():
                results.append(matches.get_nowait())
            results.sort(key=self.identify_results_keygen(title=title, authors=authors, identifiers=identifiers))
            for mi in results:
                url = self.get_cached_cover_url(mi.identifiers)
                if url:
                    break
        remaining = deadline - time.monotonic()
        if not url or abort.is_set() or remaining <= 0:
            return
        try:
            with self.browser.open_novisit(url, timeout=remaining) as response:
                raw = response.read()
            if raw and not abort.is_set():
                result_queue.put((self, raw))
        except Exception:
            log.exception('표지 다운로드 실패: %s' % url)
