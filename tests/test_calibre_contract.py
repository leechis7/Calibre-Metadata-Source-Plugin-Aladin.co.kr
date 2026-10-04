"""Integration contract tests with small doubles; not a Calibre installation test."""
import importlib
from io import BytesIO
from queue import Queue
import re
import sys
from threading import Event
import types
import unittest
from unittest.mock import patch

from support import fixture, load_adapter, ROOT


def check_isbn(value):
    value = re.sub(r'[^0-9Xx]', '', str(value or '')).upper()
    if len(value) == 13 and value.isdigit():
        return value if sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(value)) % 10 == 0 else None
    if len(value) == 10:
        try:
            return value if sum((10-i) * (10 if c == 'X' else int(c)) for i,c in enumerate(value)) % 11 == 0 else None
        except ValueError:
            pass


class Metadata:
    def __init__(self, title, authors):
        self.title, self.authors, self.identifiers = title, authors, {}
        self.isbn = None
    def set_identifier(self, key, value):
        self.identifiers[key] = value


class Source:
    name = 'Trivial Plugin'
    def __init__(self):
        self.prefs = {o.name: o.default for o in self.options}
        self.ids, self.covers = {}, {}
    def cache_isbn_to_identifier(self, isbn, id_):
        self.ids[isbn] = id_
    def cached_isbn_to_identifier(self, isbn):
        return self.ids.get(isbn)
    def cache_identifier_to_cover_url(self, id_, url):
        self.covers[id_] = url
    def cached_identifier_to_cover_url(self, id_):
        return self.covers.get(id_)
    def clean_downloaded_metadata(self, mi):
        mi.isbn = check_isbn(mi.isbn)
        if mi.isbn:
            mi.identifiers['isbn'] = mi.isbn
    def identify_results_keygen(self, **kwargs):
        return lambda mi: mi.source_relevance


class Option:
    def __init__(self, name, type_, default, label, desc):
        self.name, self.default = name, default


class Browser:
    def __init__(self, routes):
        self.routes, self.calls = routes, []
        self.addheaders = []
    def open_novisit(self, url, timeout):
        self.calls.append(url)
        self.last_timeout = timeout
        return BytesIO(self.routes[url])


class Log:
    def __init__(self):
        self.exceptions = []
    def error(self, *args):
        pass
    def exception(self, *args):
        self.exceptions.append(args)


def load_source(store):
    worker = load_adapter(store)
    namespace = worker.__package__
    modules = {}
    for name in ('calibre', 'calibre.ebooks', 'calibre.ebooks.metadata', 'calibre.ebooks.metadata.book',
                 'calibre.ebooks.metadata.book.base', 'calibre.ebooks.metadata.sources',
                 'calibre.ebooks.metadata.sources.base', 'calibre.library', 'calibre.library.comments'):
        modules[name] = types.ModuleType(name)
        modules[name].__path__ = []
    modules['calibre.ebooks.metadata'].check_isbn = check_isbn
    modules['calibre.ebooks.metadata.book.base'].Metadata = Metadata
    modules['calibre.ebooks.metadata.sources.base'].Source = Source
    modules['calibre.ebooks.metadata.sources.base'].Option = Option
    modules['calibre.library.comments'].sanitize_comments_html = lambda html: html
    env = {'__name__': namespace}
    with patch.dict(sys.modules, modules):
        exec((ROOT / 'plugins' / store / '__init__.py').read_text(encoding='utf-8'), env)
    # Match Calibre's class-selection rule (shallowest module wins).
    classes = [v for v in env.values() if isinstance(v, type) and issubclass(v, Source) and v.name != 'Trivial Plugin']
    classes.sort(key=lambda c: c.__module__.count('.'))
    return classes[0]()


class CalibreContractTests(unittest.TestCase):
    def yes24(self):
        source = load_source('yes24')
        source.browser = Browser({
            source.search_url.format(query='9791171711673'): fixture('yes24_search.html').encode(),
            source.detail_url.format(id='125557465'): fixture('yes24_detail.html').encode(),
            'https://image.yes24.com/goods/125557465/xl': b'cover-bytes',
        })
        return source

    def test_identify_and_cover_cache(self):
        source, queue, log = self.yes24(), Queue(), Log()
        source.identify(log, queue, Event(), identifiers={'isbn': '9791171711673'})
        self.assertEqual(queue.qsize(), 1)
        mi = queue.get()
        self.assertEqual(mi.identifiers['yes24.com'], '125557465')
        self.assertEqual(mi.languages, ['kor'])
        self.assertIn('목차', mi.comments)
        covers = Queue()
        source.download_cover(log, covers, Event(), identifiers={'isbn': '9791171711673'})
        self.assertEqual(covers.get_nowait(), (source, b'cover-bytes'))
        self.assertEqual(len(source.browser.calls), 3)
        self.assertFalse(log.exceptions)

    def test_uncached_cover_identifies(self):
        source, queue, log = self.yes24(), Queue(), Log()
        source.download_cover(log, queue, Event(), identifiers={'yes24.com': '125557465'})
        self.assertEqual(queue.get_nowait(), (source, b'cover-bytes'))
        self.assertFalse(log.exceptions)

    def test_abort_before_request(self):
        source, queue, abort = self.yes24(), Queue(), Event()
        abort.set()
        source.identify(Log(), queue, abort, title='제목')
        source.download_cover(Log(), queue, abort, title='제목')
        self.assertTrue(queue.empty())
        self.assertFalse(source.browser.calls)

    def test_expired_timeout(self):
        source, queue = self.yes24(), Queue()
        source.identify(Log(), queue, Event(), identifiers={'yes24.com':'125557465'}, timeout=0)
        self.assertTrue(queue.empty())
        self.assertFalse(source.browser.calls)

    def test_empty_response_retry(self):
        source, queue, log = self.yes24(), Queue(), Log()
        original = source.browser.open_novisit
        calls = []
        def open_(url, timeout):
            calls.append(url)
            if len(calls) == 1:
                return BytesIO(b'')
            return original(url.split('?_calibre=')[0], timeout)
        source.browser.open_novisit = open_
        source.identify(log, queue, Event(), identifiers={'yes24.com':'125557465'})
        self.assertEqual(queue.qsize(), 1)
        self.assertEqual(len(calls), 2)
        self.assertIn('?_calibre=', calls[1])
        self.assertFalse(log.exceptions)

    def test_abort_after_http_response(self):
        source, queue, abort = self.yes24(), Queue(), Event()
        original = source.browser.open_novisit
        def open_(url, timeout):
            result = original(url, timeout)
            abort.set()
            return result
        source.browser.open_novisit = open_
        source.identify(Log(), queue, abort, identifiers={'yes24.com':'125557465'})
        self.assertTrue(queue.empty())
        self.assertFalse(source.covers)

    def test_optional_api_failure_keeps_metadata(self):
        source = load_source('kyobo')
        source.browser = Browser({source.detail_url.format(id='S000000610625'): fixture('kyobo_detail.html').encode()})
        queue, log = Queue(), Log()
        source.identify(log, queue, Event(), identifiers={'kyobobook.co.kr':'S000000610625'})
        self.assertEqual(queue.get_nowait().title, '아몬드')
        self.assertEqual(len(log.exceptions), 1)

    def test_wrong_isbn_rejected(self):
        source, queue = self.yes24(), Queue()
        source.browser.routes[source.search_url.format(query='9788936434267')] = fixture('yes24_search.html').encode()
        source.identify(Log(), queue, Event(), identifiers={'isbn':'9788936434267'})
        self.assertTrue(queue.empty())

    def test_options(self):
        source, queue = self.yes24(), Queue()
        source.prefs.update(append_toc=False, get_tags=False)
        source.identify(Log(), queue, Event(), identifiers={'yes24.com':'125557465'})
        mi = queue.get_nowait()
        self.assertNotIn('<h3>목차</h3>', mi.comments)
        self.assertEqual(mi.tags, [])

    def test_independent_namespaces_and_kyobo_api(self):
        source = load_source('kyobo')
        source.browser = Browser({source.detail_url.format(id='S000000610625'): fixture('kyobo_detail.html').encode(),
            'https://product.kyobobook.co.kr/api/gw/pdt/v2/product/component/S000000610625/middle': fixture('kyobo_middle.json').encode()})
        queue, log = Queue(), Log()
        source.identify(log, queue, Event(), identifiers={'kyobobook.co.kr':'S000000610625'})
        mi = queue.get_nowait()
        self.assertIn('프롤로그', mi.comments)
        self.assertEqual(mi.identifiers['kyobobook.co.kr'], 'S000000610625')
        self.assertNotIn('yes24.com', mi.identifiers)
        self.assertFalse(log.exceptions)
