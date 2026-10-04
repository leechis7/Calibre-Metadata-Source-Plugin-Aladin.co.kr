"""Pure parsing helpers shared by independently packaged sources (GPL-3.0)."""
import gzip
import re
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlsplit

from lxml.html import fragment_fromstring, tostring


def decode_html(raw):
    if isinstance(raw, str):
        return raw
    if raw.startswith(b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    for encoding in ('utf-8-sig', 'cp949', 'euc-kr'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode('utf-8', errors='replace')


def text(node):
    return ' '.join(node.text_content().split()) if node is not None else ''


def first_text(root, xpath):
    nodes = root.xpath(xpath)
    return text(nodes[0]) if nodes else ''


def meta(root, name):
    values = root.xpath('//meta[@property=$name or @name=$name]/@content', name=name)
    return values[0].strip() if values else ''


def safe_url(url):
    url = str(url or '').strip()
    if url.startswith('//'):
        url = 'https:' + url
    return url if urlsplit(url).scheme in ('http', 'https') else ''


def clean_html(value):
    if not value or not str(value).strip():
        return ''
    value = str(value)
    if not re.search(r'<[a-zA-Z][^>]*>', value):
        return '<p>' + escape(value).replace('\n', '<br/>') + '</p>'
    root = fragment_fromstring(value, create_parent='div')
    for bad in root.xpath('.//script|.//style|.//iframe|.//object|.//form|.//button|.//input|.//textarea|.//noscript'):
        bad.drop_tree()
    for node in root.iter():
        for key in list(node.attrib):
            if key not in ('href', 'src', 'alt', 'title'):
                del node.attrib[key]
            elif key in ('href', 'src'):
                url = safe_url(node.attrib[key])
                if url:
                    node.attrib[key] = url
                else:
                    del node.attrib[key]
    return tostring(root, encoding='unicode', method='html')


def comments(sections, append_toc=True):
    result = []
    for heading, value in sections:
        if heading == '목차' and not append_toc:
            continue
        html = clean_html(value)
        if html:
            result.append('<h3>%s</h3>%s' % (escape(heading), html))
    return ''.join(result)


def parse_date(value):
    match = re.search(r'(\d{4})\D*(\d{2})\D*(\d{2})', str(value or ''))
    if match:
        try:
            return datetime(*map(int, match.groups()), tzinfo=timezone.utc)
        except ValueError:
            pass


def normalized(value):
    return re.sub(r'[^\w]', '', str(value or '')).casefold()


def isbn_key(value):
    value = re.sub(r'[^\dXx]', '', str(value or '')).upper()
    if len(value) == 10:
        value = '978' + value[:9]
        value += str((-sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(value))) % 10)
    return value
