#!/usr/bin/env python
"""Opt-in live HTTP checks. Does not install plugins or modify a Calibre library."""
import argparse
from pathlib import Path
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from support import load_adapter
from test_aladin import parser_class
from lxml.html import fromstring


def fetch(url):
    headers = {'User-Agent':'Mozilla/5.0'}
    if 'kyobobook.co.kr' in url:
        headers['Referer'] = 'https://www.kyobobook.co.kr/'
    elif 'aladin.co.kr' in url:
        headers['Referer'] = 'https://www.aladin.co.kr/shop/wproduct.aspx?ISBN=9788936434267'
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        raw = response.read()
    if not raw.strip():
        retry = url + ('&' if '?' in url else '?') + '_calibre=' + str(time.time_ns())
        with urlopen(Request(retry, headers=headers), timeout=30) as response:
            raw = response.read()
    from calibre_plugins.yes24_com.text_cleaner import decode_html
    value = decode_html(raw)
    if not value.strip():
        raise ValueError('Empty HTTP response: ' + url)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', choices=('all','aladin','yes24','kyobo'), default='all')
    args = parser.parse_args()
    yes24, kyobo = load_adapter('yes24'), load_adapter('kyobo')
    for store, worker, query, expected_isbn, expected_title in (
        ('yes24', yes24, 'https://www.yes24.com/Product/Search?domain=BOOK&query=9791171711673', '9791171711673', '하루 한 장 나의 어휘력을 위한 필사 노트'),
        ('kyobo', kyobo, 'https://search.kyobobook.co.kr/search?keyword=9788936434267', '9788936434267', '아몬드'),
    ):
        if args.store not in ('all',store):
            continue
        urls = worker.search_results(fetch(query))
        if not urls:
            raise AssertionError(store + ' search returned no books')
        book = worker.parse_details(fetch(urls[0]), urls[0])
        assert book['isbn'] == expected_isbn, book['isbn']
        assert book['title'] == expected_title, book['title']
        assert book['authors'] and book['publisher'] and book['cover']
        title_query = query.replace(expected_isbn, quote(expected_title))
        title_results = worker.search_results(fetch(title_query))
        assert title_results, 'Title search returned no books'
        for title_url in title_results[:5]:
            title_book = worker.parse_details(fetch(title_url), title_url)
            if expected_title in title_book['title']:
                break
        else:
            raise AssertionError('Title search did not return a matching title')
        if hasattr(worker, 'enrich'):
            worker.enrich(book, fetch)
        assert dict(book['sections'])['책소개']
        assert dict(book['sections'])['목차']
        assert dict(book['sections'])['출판사 리뷰']
        with urlopen(Request(book['cover'],headers={'User-Agent':'Mozilla/5.0'}), timeout=30) as image:
            raw = image.read()
        assert raw.startswith((b'\xff\xd8', b'\x89PNG', b'RIFF', b'GIF')), 'Cover is not an image'
        print('%s: %s / %s / %s / cover %d bytes / all sections OK' % (store,book['title'],','.join(book['authors']),book['isbn'],len(raw)))
    if args.store in ('all','aladin'):
        worker = parser_class()()
        root = fromstring(fetch('https://www.aladin.co.kr/shop/wproduct.aspx?ISBN=9788936434267'))
        assert worker.parse_isbn(root) == '9788936434267'
        title = worker.parse_title_series(root)[0]
        assert title and '아몬드' in title
        from datetime import datetime
        contents = [fromstring(fetch('https://www.aladin.co.kr/shop/product/getContents.aspx?ISBN=9788936434267&name=' + name + '&type=0&date=' + str(datetime.now().hour))) for name in ('Introduce','PublisherDesc')]
        assert any(worker._find_aladin_content_node(node, ['책소개','출판사 제공 책소개']) is not None for node in contents)
        toc = any(worker._find_toc_html(node) for node in contents)
        print('aladin: %s / ISBN and asynchronous description OK / TOC %s' % (title, 'present' if toc else 'not provided for this edition'))


if __name__ == '__main__':
    main()
