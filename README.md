# Calibre Metadata Source Plugins Korea

Calibre에서 **알라딘·YES24·교보문고**의 도서 메타데이터와 표지를 가져옵니다. 하나의 저장소에서 개발하고 **서점별 독립 ZIP 3개**로 배포합니다. 원하는 서점만 설치하거나 모두 설치해 Calibre의 메타데이터 다운로드 설정에서 소스별 사용 여부와 우선순위를 지정할 수 있습니다.

## 설치

| 서점 | Calibre 표시 이름 | v1.2.3 설치 파일 |
| --- | --- | --- |
| 알라딘 | `Aladin.co.kr` | [Aladin ZIP](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/releases/download/v1.2.3/Calibre-Metadata-Plugin-Aladin-v1.2.3.zip) |
| YES24 | `YES24.com` | [YES24 ZIP](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/releases/download/v1.2.3/Calibre-Metadata-Plugin-YES24-v1.2.3.zip) |
| 교보문고 | `Kyobobook.co.kr` | [Kyobo ZIP](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/releases/download/v1.2.3/Calibre-Metadata-Plugin-Kyobo-v1.2.3.zip) |

위 링크는 **v1.2.3 Release 공개 후** 사용할 수 있습니다. 공개 전에는 아래 빌드 명령으로 생성한 `dist/`의 ZIP을 사용합니다. 실제 배포된 버전은 [전체 릴리즈](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/releases)에서 확인합니다.

1. 원하는 ZIP을 다운로드합니다. 압축을 풀지 않습니다.
2. Calibre `환경설정 → 고급 → 플러그인 → 파일에서 플러그인 불러오기`에서 설치합니다.
3. Calibre를 재시작하고 `환경설정 → 메타데이터 다운로드`에서 사용할 소스와 옵션을 설정합니다.
4. 도서의 `메타데이터 편집 → 메타데이터 다운로드`를 실행합니다.

최소 Calibre 버전은 5.0.0입니다. 새 소스의 설정은 Calibre 기본 UI를 사용합니다. 기존 알라딘의 표시 이름, `aladin.co.kr` 식별자와 `plugins/Aladin` 설정 저장소는 유지하여 업데이트할 수 있습니다.

## 지원 정보

| 기능 | 알라딘 | YES24 | 교보문고 |
| --- | --- | --- | --- |
| 제목·저자·ISBN·출판사·출간일 | 지원 | 지원 | 지원 |
| 책소개·저자소개·출판사 리뷰·목차 | 제공 시 지원 | 제공 시 지원 | 제공 시 지원 |
| 표지 | cover500 / 작은 표지 옵션 | XL | 최대 1000px 요청 |
| 평점·분류 태그·언어 | 지원 | 제공 시 지원 | 제공 시 지원 |
| 시리즈 | 지원 | 제공 시 지원 | 미지원 |

- 알라딘: 기존 HTML 파서, Search3Ajax 검색과 `getContents.aspx` 책소개를 유지합니다.
- YES24: HTML 및 JSON-LD를 읽습니다. textarea에 저장된 책소개·목차·서평도 처리합니다.
- 교보: 현재 Next.js Flight JSON(`self.__next_f.push`)을 실행 없이 읽고 요청한 상품 ID의 데이터만 선택합니다. 상품 middle API로 목차·저자소개·서평을 보완합니다. `__NEXT_DATA__`에 동일 상품 구조가 있는 경우도 읽습니다.
- 새 소스는 ISBN-10/13의 같은 판본을 확인합니다. ISBN 없이 검색하면 제목·저자가 맞는 결과를 선택합니다. 식별자 검색 실패 시 제목 정보로 재검색합니다.
- YES24·교보 설정: 최대 결과 수(기본 5, 적용 범위 1~20), 목차 포함, 분류 태그 사용.
- 사이트가 제공하지 않는 항목은 비어 있을 수 있습니다. 교보 추가 API가 실패해도 기본 도서정보를 반환합니다.

## 구조와 빌드

```text
plugins/aladin/        기존 알라딘 Source, worker, 설정, 번역
plugins/yes24/         YES24 Source, worker, 설정
plugins/kyobo/         교보 Source, worker, 설정
shared/               공통 파싱·Calibre 인터페이스·설정·기존 Qt 헬퍼
scripts/build.py      독립 ZIP 생성과 SHA-256 체크섬
scripts/release.py    GitHub CLI 릴리즈 미리보기/업로드
scripts/smoke.py      선택 실행 실시간 HTTP 검사
scripts/smoke_calibre.py 실제 Calibre 런타임·ZIP 설치·검색·표지 검사
tests/                서점별 회귀·인터페이스·ZIP 검사
.github/workflows/    태그 기반 검사·빌드·Release 자동화
```

공통 모듈은 각 ZIP 루트에 복사됩니다. 고유한 `plugin-import-name-*.txt`를 사용해 서로 다른 `calibre_plugins` 네임스페이스로 로드되므로 다른 ZIP이나 이 저장소 없이 설치할 수 있습니다. 실행 의존성은 Calibre가 제공합니다.

일반 Python 3.8 이상으로 빌드할 수 있으며 테스트에는 lxml이 필요합니다.

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/build.py          # 3개 일괄 빌드
python scripts/build.py yes24    # 한 서점만 빌드
python scripts/smoke.py          # 네트워크 접근, 실시간 검사
python scripts/smoke.py --store kyobo
python scripts/smoke_mechanize.py # 실제 mechanize로 소스 identify/cover 실행
```

`dist/`에 ZIP 3개와 `SHA256SUMS.txt`가 생성됩니다. 빌드는 Python 문법, 필수 마커, 파일 이름 충돌과 통합 버전을 확인하며 동일 소스로 동일 ZIP을 생성합니다. ZIP은 Git에 추가하지 않습니다.

검사에는 축약한 실제 HTML/JSON 구조, 알라딘 파서 회귀, 새 소스의 큐·캐시·취소·제한시간·옵션·ISBN 확인, ZIP 구조와 재현성 검증이 포함됩니다. Calibre 메타데이터 API는 대역을 사용하지만 HTTP 응답은 실제 mechanize.response_seek_wrapper로도 검사합니다. 앱 설치 검사를 대체하지 않습니다.

2026-10-05에는 Portable Calibre 9.15.0의 실제 플러그인 로더·브라우저·메타데이터 객체로 세 서점의 ‘트렌드 코리아 2027’ 제목/ISBN 검색, 책소개·목차 및 표지 다운로드를 확인했습니다. YES24의 첫 요청이 세션 확인 후 홈페이지로 이동하는 현상을 재현하고 자동 재요청으로 회복되는 것도 확인했습니다. 외국도서 The Book of Debugging(9781718504066)의 제목/제목+저자/ISBN 검색 및 표지도 확인했고, 전체 회귀 테스트 42개가 통과했습니다. GUI 조작 검증은 별도입니다.

실제 Calibre 검사는 작업 폴더에 별도 설정을 만들어 실행합니다. 먼저 ZIP을 빌드한 뒤 PowerShell에서 실행하세요.

```powershell
$env:CALIBRE_CONFIG_DIRECTORY = Join-Path (Get-Location) '.dev-deps\calibre-smoke-settings'
& 'C:\tools\Calibre Portable\Calibre\calibre-debug.exe' -e scripts/smoke_calibre.py
# YES24만 검사: 마지막에 -- --store yes24 추가
# 외국도서 예제 (해당 YES24 상품에는 목차가 없음)
& 'C:\tools\Calibre Portable\Calibre\calibre-debug.exe' -e scripts/smoke_calibre.py -- --store yes24 --title 'The Book of Debugging' --isbn 9781718504066 --author 'Johannes Kuhlmann' --allow-missing-toc
```

## Release

세 플러그인의 `version`을 함께 변경하고 `release-notes.md`, README 다운로드 링크와 `changelog.txt`를 갱신합니다.

```sh
python scripts/release.py        # 빌드하고 업로드 계획만 표시
git add <변경한 파일>
git commit -m "Release 1.2.3: include YES24 foreign books"
git tag v1.2.3
git push origin main
git push origin v1.2.3
```

태그가 올라가면 GitHub Actions가 테스트·빌드하고, 태그와 모든 플러그인 버전이 일치할 때 ZIP 3개와 체크섬을 Release에 업로드합니다. 사이트 상태에 영향을 받는 실시간 smoke는 CI에서 자동 실행하지 않습니다.

GitHub Actions 대신 로컬에서 업로드하려면 GitHub CLI(`gh`) 인증과 원격 태그가 필요합니다. 자동 Release와 동시에 실행하지 않습니다.

```sh
python scripts/release.py --publish --draft
# 공개 릴리즈: --draft 생략
```

로컬 업로드는 깨끗한 작업 트리와 현재 HEAD를 가리키는 릴리즈 태그를 확인합니다. 빌드·미리보기 명령은 커밋·태그·업로드를 하지 않습니다.

## 출처와 라이선스

알라딘 플러그인은 YongSeok Choi(`sseeookk`)의 [원본 GPL-3.0 플러그인](https://github.com/sseeookk/Calibre-Aladin.co.kr-Metadata-Source-Plugin)을 기반으로 한 유지보수 포크입니다. 원본은 Grant Drake의 Goodreads/Barnes 플러그인과 공통 GUI 코드에 기반합니다. 원 저작권 고지와 [GPL-3.0 라이선스](LICENSE)를 유지하고 각 ZIP에도 라이선스를 포함합니다.

`leechis7`는 2026-06-02부터 유지보수했으며 v1.2.0에서 YES24·교보와 모노레포 빌드를 추가했습니다.

[알라딘 MobileRead 포럼](https://www.mobileread.com/forums/showthread.php?t=236797)
