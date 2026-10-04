"""Regression tests execute the existing parser methods without loading Qt."""
import ast
import datetime
from pathlib import Path
import re
from collections import OrderedDict
from types import SimpleNamespace
import unittest

from lxml.html import fromstring, tostring
from support import ROOT


def parser_class():
    tree = ast.parse((ROOT / 'plugins/aladin/worker.py').read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Worker')
    cls.bases = []
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name != '__init__']
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    config = SimpleNamespace(STORE_NAME='Aladin_co_kr', KEY_GET_ALL_AUTHORS='getAllAuthors',
        KEY_APPEND_TOC='appendTOC', KEY_COMMENTS_SUFFIX='commentsSuffix',
        DEFAULT_STORE_VALUES={'getAllAuthors':False, 'appendTOC':True, 'commentsSuffix':''},
        plugin_prefs={'Aladin_co_kr':{}})
    env = dict(re=re, datetime=datetime, OrderedDict=OrderedDict, fromstring=fromstring,
               tostring=tostring, unicode=str, cfg=config, clean_ascii_chars=lambda x:x,
               sanitize_comments_html=lambda x:x)
    exec(compile(module, 'aladin-parser-methods', 'exec'), env)
    return env['Worker']


class AladinTests(unittest.TestCase):
    def setUp(self):
        self.worker = parser_class()()

    def test_title_span_and_link(self):
        for tag in ('span', 'a'):
            root = fromstring('<div><%s class="Ere_bo_title">테스트 도서</%s></div>' % (tag,tag))
            self.assertEqual(self.worker.parse_title_series(root), ('테스트 도서',None,None))

    def test_isbn_and_identifier(self):
        root = fromstring('<meta property="books:isbn" content="9788936434267"><meta property="og:url" content="https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=123">')
        self.assertEqual(self.worker.parse_isbn(root), '9788936434267')
        self.assertEqual(self.worker.parse_aladin_id('https://www.aladin.co.kr/shop/wproduct.aspx?ISBN=9788936434267', root), '123')

    def test_toc_fallback(self):
        root = fromstring('<div id="div_TOC_Short"><p>1장<br/>2장</p></div>')
        self.assertIn('1장', self.worker._find_toc_html(root))

    def test_description_section_and_sanitization(self):
        root = fromstring('<div><div class="Ere_prod_mconts_box"><div class="Ere_prod_mconts_LS">출판사 제공 책소개</div><div class="Ere_prod_mconts_R">소개<script>bad()</script></div></div></div>')
        node = self.worker._find_aladin_content_node(root, ['출판사 제공 책소개'])
        html = self.worker._content_node_to_comments_html(node)
        self.assertIn('소개', html)
        self.assertNotIn('bad()', html)
