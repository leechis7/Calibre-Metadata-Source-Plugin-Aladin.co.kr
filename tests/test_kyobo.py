import json
import unittest
from support import fixture, load_adapter

worker = load_adapter('kyobo')


class KyoboTests(unittest.TestCase):
    def test_real_structure_search(self):
        self.assertEqual(worker.search_results(fixture('kyobo_search.html')), ['https://product.kyobobook.co.kr/detail/S000000610625'])

    def test_flight_details_and_api(self):
        book = worker.parse_details(fixture('kyobo_detail.html'), 'https://product.kyobobook.co.kr/detail/S000000610625')
        self.assertEqual(book['title'], '아몬드')
        self.assertEqual(book['authors'], ['손원평'])
        self.assertEqual(book['isbn'], '9788936434267')
        self.assertEqual(book['publisher'], '창비')
        self.assertIn('/1000x0/', book['cover'])
        self.assertEqual(book['rating'], 4.85)
        urls = []
        def fetch(url):
            urls.append(url)
            return fixture('kyobo_middle.json')
        worker.enrich(book, fetch)
        self.assertEqual(urls, ['https://product.kyobobook.co.kr/api/gw/pdt/v2/product/component/S000000610625/middle'])
        self.assertIn('프롤로그', dict(book['sections'])['목차'])
        self.assertTrue(dict(book['sections'])['출판사 리뷰'])

    def test_flight_split_chunks(self):
        raw = fixture('kyobo_detail.html')
        root = worker.fromstring(raw)
        node = root.xpath('//script')[0]
        record = json.loads(node.text[node.text.index('(')+1:node.text.rindex(')')])[1]
        prefix = raw[:raw.index('<script>')]
        raw = prefix + ''.join('<script>self.__next_f.push(' + json.dumps([1, x]) + ')</script>' for x in (record[:71], record[71:])) + '</body></html>'
        self.assertEqual(worker.parse_details(raw, '')['isbn'], '9788936434267')

    def test_next_data_compatible_shape(self):
        root = worker.fromstring(fixture('kyobo_detail.html'))
        data = worker.product_data(root, 'S000000610625')
        raw = '<script id="__NEXT_DATA__">' + json.dumps({'props': {'pageProps': {'product': data}}}) + '</script>'
        self.assertEqual(worker.product_data(worker.fromstring(raw), 'S000000610625'), data)

    def test_does_not_take_recommended_product(self):
        with self.assertRaises(ValueError):
            worker.product_data(worker.fromstring(fixture('kyobo_detail.html')), 'S000000000001')

    def test_missing_result(self):
        self.assertEqual(worker.search_results('<html>검색 결과 없음</html>'), [])
