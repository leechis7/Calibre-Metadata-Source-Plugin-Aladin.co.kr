"""Opt-in live source tests with real mechanize HTTP, using Calibre API doubles.

Exercises ZIP source identify/cover methods end to end, rather than only parsers.
Does not install plugins or modify the user's Calibre library.
"""
import argparse
from pathlib import Path
from queue import Queue
import sys
import traceback
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_calibre_contract import load_source, Log
import mechanize


class LiveLog(Log):
    def exception(self, *args):
        super().exception(*args)
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title', default='트렌드 코리아 2027')
    parser.add_argument('--isbn', default='9791124073483')
    parser.add_argument('--store', choices=('all', 'yes24', 'kyobo'), default='all')
    args = parser.parse_args()
    for store in ('yes24', 'kyobo'):
        if args.store not in ('all', store):
            continue
        source = load_source(store)
        browser = mechanize.Browser()
        browser.set_handle_robots(False)
        browser.set_handle_gzip(True)
        browser.addheaders = [('User-Agent', 'Mozilla/5.0')]
        source.browser = browser
        for title, identifiers in ((args.title, {}), (None, {'isbn': args.isbn})):
            queue, log = Queue(), LiveLog()
            source.identify(log, queue, Event(), title=title, identifiers=identifiers, timeout=30)
            results = []
            while not queue.empty():
                results.append(queue.get_nowait())
            if not results:
                raise AssertionError('%s returned no metadata: %s' % (store, log.exceptions))
            match = next((mi for mi in results if mi.isbn == args.isbn), None)
            assert match is not None, [(mi.title, mi.isbn) for mi in results]
            covers = Queue()
            source.download_cover(log, covers, Event(), identifiers=match.identifiers, timeout=30)
            _, image = covers.get_nowait()
            assert image.startswith((b'\xff\xd8', b'\x89PNG', b'RIFF', b'GIF')), 'Not an image'
            assert not log.exceptions, log.exceptions
            print('%s %s: %s / %s / %d metadata results / cover %d bytes' %
                  (store, 'title' if title else 'ISBN', match.title, match.isbn, len(results), len(image)))


if __name__ == '__main__':
    main()
