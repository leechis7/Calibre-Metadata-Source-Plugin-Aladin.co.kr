Calibre-Metadata-Source-Plugin-Aladin.co.kr
===========================================

[Calibre](https://calibre-ebook.com/)에서 [Aladin.co.kr](http://www.aladin.co.kr)의 도서 메타데이터와 표지를 가져오는 메타데이터 소스 플러그인입니다.

현재 버전
---------
1.1.1

주요 변경 사항
--------------
- aladin.co.kr ID, 제목, 저자, 시리즈, ISBN, 책소개, 목차, 평점, 출판사, 출간일, 태그, 언어, 표지 이미지를 가져옵니다.
- 일반 검색 페이지에서 사용할 수 있는 도서 목록을 찾지 못하면 알라딘 Search3Ajax 검색 결과를 대신 사용합니다.
- 알라딘 검색 응답에 문자셋 정보가 있으면 해당 문자셋으로 디코딩합니다.
- 플러그인 옵션이 켜져 있고 목차 데이터가 있으면 알라딘 목차를 책소개 뒤에 붙입니다.
- 알라딘이 제공하는 저자소개, 출판사 리뷰 정보가 있으면 책소개에 함께 포함합니다.

설치 방법
---------
1. [releases](https://github.com/sseeookk/Calibre-Metadata-Source-Plugin-Aladin.co.kr/releases)에서 최신 버전 zip 파일을 다운로드합니다. 예: `Calibre-Metadata-Source-Plugin-Aladin.co.kr-v1.1.1.zip`
2. Calibre에서 `Preferences`를 엽니다.
3. `Advanced` -> `Plugins`로 이동합니다.
4. `Load plugin from file`을 누르고 다운로드한 zip 파일을 선택합니다.
5. `Metadata source plugins`에서 `Aladin.co.kr`를 선택하고, 필요하면 활성화합니다.
6. 도서의 `Edit metadata` 창에서 `Download metadata`를 눌러 책 정보와 표지를 가져옵니다.

Calibre Plugins Forum
---------------------
[Metadata Source Plugin] Aladin.co.kr (KO) - MobileRead Forums.  
https://www.mobileread.com/forums/showthread.php?t=236797

