import unittest
import gzip
from support import load_adapter

cleaner = load_adapter('yes24').__dict__
from calibre_plugins.yes24_com.text_cleaner import clean_html, comments, decode_html, isbn_key, parse_date


class CleanerTests(unittest.TestCase):
    def test_unsafe_html_removed(self):
        html = clean_html('<div onclick="bad()"><script>bad()</script><iframe src="https://example.com"></iframe><a href="javascript:bad()">link</a><img src="//image.yes24.com/a.jpg" onerror="bad()"></div>')
        self.assertNotIn('bad()', html)
        self.assertNotIn('<iframe', html)
        self.assertIn('https://image.yes24.com/a.jpg', html)

    def test_toc_option_and_plain_text(self):
        html = comments([('책소개', '소개\n다음 줄'), ('목차', '목차 내용')], False)
        self.assertNotIn('목차', html)
        self.assertIn('<br/>', html)

    def test_encoding_and_date(self):
        self.assertEqual(decode_html('한국어'.encode('cp949')), '한국어')
        self.assertEqual(decode_html(gzip.compress('한국어'.encode('utf-8'))), '한국어')
        self.assertEqual(parse_date('20240328').day, 28)
        self.assertEqual(parse_date('2024년 03월 28일').year, 2024)
        self.assertIsNone(parse_date('2024-02-30'))

    def test_equivalent_isbn(self):
        self.assertEqual(isbn_key('8936434268'), isbn_key('9788936434267'))
