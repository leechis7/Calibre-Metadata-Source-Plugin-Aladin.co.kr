# 릴리즈 안내

이 문서는 저장소 쓰기 권한이 있는 유지보수자를 위한 절차입니다. 기본 배포 경로는 GitHub Actions입니다. **`v*` 태그를 원격에 push하면 검사 후 공개 GitHub Release가 자동 생성됩니다.** 일반 `main` push와 PR은 테스트·빌드만 실행합니다.

## 1. 로컬 준비

새 버전을 정하고 다음 파일을 함께 갱신합니다. 아래 명령의 `v1.2.5`는 예시이며, 실제로 정한 새 버전으로 바꾸세요. 이미 공개한 태그·버전은 재사용하지 않습니다.

- `plugins/aladin/__init__.py`, `plugins/yes24/__init__.py`, `plugins/kyobo/__init__.py`: 같은 `version` 튜플
- `CHANGELOG.md`: 새 버전의 변경 내용과 날짜
- `release-notes.md`: 이번 릴리즈의 문제·개선 사항·검증 결과·업데이트 안내
- `README.md`: 다운로드 링크와 달라진 사용자 안내

개발환경 준비는 [개발·빌드 안내](development.md)를 따릅니다.

```sh
python -m unittest discover -s tests -v
python scripts/build.py
python scripts/release.py
git diff --check
git diff
```

`scripts/release.py`를 옵션 없이 실행하면 세 ZIP을 빌드하고 업로드 계획만 출력합니다. 태그 생성·push·업로드는 하지 않습니다. 파서·다운로드 변경은 실제 Calibre로 관련 도서와 기존 도서를 시험하고 결과를 릴리즈 노트에 적습니다.

`dist/`에서 현재 버전의 ZIP 세 개와 `SHA256SUMS.txt`를 확인합니다. 이전 버전 ZIP이 남아 있으면 현재 릴리즈에 섞이지 않도록 별도 보관하세요. 자동 워크플로는 새 체크아웃에서 빌드하므로 이전 ZIP을 포함하지 않습니다.

## 2. 변경 검토와 커밋

```sh
git status --short
git add <검토한 파일 경로들>
git diff --cached
git commit -m "Release 1.2.5: describe the change"
git tag v1.2.5
```

커밋·태그는 로컬 준비입니다. 원격 배포 전에 변경 파일, 검사 결과, 태그와 업로드 파일을 검토합니다. 이 저장소에서 에이전트가 작업할 때는 push·태그 push·릴리즈 생성 전에 소유자 승인을 받습니다.

## 3. 승인 후 자동 배포

원격 브랜치가 변경돼 push가 거절되면 `git fetch origin`으로 변경을 확인하고 보존해 통합합니다. 통합 후 다시 검증하며, 아직 공개하지 않은 릴리즈 태그도 검증한 커밋을 가리키게 합니다. 원격 이력이나 공개 태그를 강제로 덮어쓰지 않습니다.

승인을 받은 뒤 브랜치와 태그를 함께 올립니다.

```sh
git push --atomic origin main v1.2.5
```

[Actions](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/actions)에서 다음 단계를 확인합니다.

1. 개발 의존성 설치와 회귀 테스트
2. 독립 ZIP 세 개와 체크섬 생성
3. 태그와 세 플러그인 버전의 일치 확인
4. 공개 Release 생성과 ZIP·체크섬 업로드

검사에 실패하면 `release` 작업은 실행되지 않습니다. 일반 push·PR·브랜치 대상 수동 워크플로 실행은 배포하지 않습니다. 태그 대상으로 수동 워크플로를 실행하면 배포 작업이 실행될 수 있으므로 이미 공개된 태그에는 사용하지 마세요.

## 4. 배포 후 확인

[Releases](https://github.com/leechis7/Calibre-Metadata-Source-Plugins-Korea/releases)에서 버전·릴리즈 노트·ZIP 세 개·체크섬을 확인합니다. 설치 파일을 내려받아 체크섬과 대조하고, Calibre에서 업데이트·재시작 후 해당 버전이 로그에 표시되는지 확인합니다.

Windows PowerShell:

```powershell
Get-FileHash .\Calibre-Metadata-Plugin-YES24-v1.2.5.zip -Algorithm SHA256
```

Linux:

```sh
sha256sum -c SHA256SUMS.txt
```

macOS:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

## 수동 배포와 초안 Release

GitHub CLI(`gh`)와 저장소에 릴리즈를 만들 수 있는 인증이 필요합니다. 기본 자동 배포와 동시에 사용하면 동일 태그의 Release 생성이 충돌합니다. 수동·초안 배포를 선택했다면 **태그 push 전에** 관리자가 `release.yml` 워크플로를 일시 중지해야 합니다. 중지·재활성화도 원격 설정 변경이므로 에이전트는 승인을 받습니다.

승인받은 관리자의 수동 배포 예제:

```sh
gh auth status
gh workflow disable release.yml
git push --atomic origin main v1.2.5
python scripts/release.py --publish --draft
gh workflow enable release.yml
```

작업이 실패해도 워크플로 재활성화 여부를 확인하세요. 초안은 내용을 검토한 뒤 별도 승인을 받아 GitHub에서 공개합니다. 수동으로 곧바로 공개할 때는 `--draft`를 생략합니다.

수동 스크립트는 깨끗한 작업 트리, 로컬 태그 존재, 태그가 현재 HEAD를 가리키는지 확인한 뒤 원격 태그와 `gh` 인증을 확인합니다. 빌드 대상 버전의 ZIP 세 개와 체크섬만 업로드합니다.

## 실패 대응

- 테스트·빌드 실패: 로그를 확인하고 로컬에서 재현합니다. 자동 공개는 진행되지 않습니다.
- 태그·버전 불일치: 세 버전과 태그를 확인합니다. 공개 태그를 이동시키는 대신 새 버전으로 수정합니다.
- 테스트는 성공했으나 Release 생성 실패: 기존 Release와 Assets가 일부 생성됐는지 먼저 확인합니다. 같은 태그로 생성 명령을 반복하지 말고, 원인을 파악한 후 관리자 승인 아래 누락된 자산만 복구합니다.
- 공개한 플러그인의 결함: 기존 버전 파일을 조용히 교체하지 않고 수정 버전을 릴리즈합니다.
