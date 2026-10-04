"""Use Calibre's native settings UI for Qt5/Qt6 compatibility."""
from calibre.ebooks.metadata.sources.base import Option


def source_options():
    return (
        Option('max_results', 'number', 5, '최대 검색 결과 수', '검색 결과에서 가져올 도서 수 (1~20).'),
        Option('append_toc', 'bool', True, '목차 포함', '책소개 뒤에 목차를 붙입니다.'),
        Option('get_tags', 'bool', True, '분류를 태그로 가져오기', '서점이 제공하는 도서 분류를 태그로 사용합니다.'),
    )
