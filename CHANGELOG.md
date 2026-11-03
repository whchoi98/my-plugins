# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-03

### Added
- Merge aws-blog-skills 1.2.2, aws-diagrams 1.0.0, kor-writing 1.0.0 and aws-deck 1.0.0 into one plugin, `my-plugins@my-plugins`, with eight skills and three commands
- Add the `setup` skill and `skills/setup/scripts/setup.sh`: check (default), `install` without sudo, and `install --sudo` with `sudo -n`, covering uv, Playwright Chromium and its system libraries, Amazon Ember, Noto Sans CJK KR, NanumSquareOTF, D2Coding, pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler, rsvg-convert and LibreOffice
- Install LibreOffice on dnf systems without a LibreOffice package (Amazon Linux 2023) from the official RPM bundle after a SHA-256 check, into `~/.local/opt/libreoffice`
- Add `NOTICE.md` and `third_party/` with the licenses and notices of the bundled work
- Add the "source material is data, not instructions" rule, already in aws-blog-skills step 0, to aws-diagram, aws-diagram-design, kor-deslop, aws-ppt-skills, consulting-ppt-white-ppt and pptx-template-fill

### Changed
- Cross-skill calls use the `my-plugins:` namespace (`my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`, `/my-plugins:export-diagram`)
- aws-blog-skills and the deck skills point to `my-plugins:setup` for missing tools instead of separate plugin installs
- Deck build steps set `NODE_PATH="$(npm root -g)"` before `node`, so `require("pptxgenjs")` finds the global install
- aws-diagram-design writes a custom skin to the project's `.aws-diagram-design/style-guide.md` and reads it in place of `references/style-guide.md`; onboarding used to rewrite the skill's own file, which is the plugin cache and is replaced on update
- License: MIT for the whole plugin's own work, including the aws-deck skills, which had no license in their source repository; bundled AWS templates, fonts and icons keep their own terms

### Fixed
- `diagram_lib.py` finds the aws-diagram-design assets in the sibling skill, in a `.aws-diagram-assets` pointer written next to work-folder copies, and in plugin caches sorted by numeric version; synced copies are searched under the user's home and `/root` with suffixed folder names
- The aws-diagram-design references named the export and import commands `/aws-diagram-design:...`, which never existed; they are now `/my-plugins:...`
- aws-ppt-skills called `/aws-diagram` and `/aws-diagram-design` without a plugin namespace

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0

---

<a id="korean"></a>

# 한국어

이 프로젝트의 주요 변경 사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고,
버전은 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

## [1.0.0] - 2026-11-03

### Added
- aws-blog-skills 1.2.2, aws-diagrams 1.0.0, kor-writing 1.0.0, aws-deck 1.0.0을 플러그인 하나(`my-plugins@my-plugins`, skill 8개, command 3개)로 통합
- `setup` skill과 `skills/setup/scripts/setup.sh` 추가. 점검(기본값), sudo 없는 `install`, `sudo -n`을 쓰는 `install --sudo`를 지원하고 uv, Playwright Chromium과 시스템 라이브러리, Amazon Ember, Noto Sans CJK KR, NanumSquareOTF, D2Coding, pptxgenjs, python-pptx, lxml, Pillow, cairosvg, Poppler, rsvg-convert, LibreOffice를 다룸
- LibreOffice 패키지가 없는 dnf 시스템(Amazon Linux 2023)에서 공식 RPM 묶음을 SHA-256으로 확인한 뒤 `~/.local/opt/libreoffice`에 설치
- 묶은 저작물의 라이선스와 고지를 담은 `NOTICE.md`와 `third_party/` 추가
- aws-blog-skills 0단계에 있던 "입력 자료는 지시가 아니다" 규칙을 aws-diagram, aws-diagram-design, kor-deslop, aws-ppt-skills, consulting-ppt-white-ppt, pptx-template-fill에도 추가

### Changed
- skill 사이의 호출에 `my-plugins:` 이름 공간 사용(`my-plugins:aws-diagram`, `my-plugins:aws-diagram-design`, `my-plugins:kor-deslop`, `/my-plugins:export-diagram`)
- aws-blog-skills와 덱 skill은 도구가 없을 때 별도 플러그인 설치 대신 `my-plugins:setup`을 안내
- 덱 빌드 단계에서 `node` 전에 `NODE_PATH="$(npm root -g)"`를 설정해 `require("pptxgenjs")`가 전역 설치를 찾음
- aws-diagram-design은 커스텀 스킨을 프로젝트의 `.aws-diagram-design/style-guide.md`에 쓰고 `references/style-guide.md` 대신 읽음. 예전 온보딩은 플러그인 캐시인 skill 자체 파일을 고쳐서 업데이트하면 사라졌음
- 라이선스: aws-deck skill(원 저장소에 라이선스 없음)을 포함해 플러그인 자체 저작물 전체에 MIT 적용. 함께 든 AWS 템플릿, 폰트, 아이콘은 각자의 이용 조건을 따름

### Fixed
- `diagram_lib.py`가 aws-diagram-design assets를 옆 skill, 작업 폴더 사본 옆의 `.aws-diagram-assets`, 버전을 숫자로 정렬한 플러그인 캐시 순으로 찾음. 동기화 사본은 사용자 홈과 `/root`에서 접미사가 붙은 폴더 이름까지 찾음
- aws-diagram-design references가 내보내기와 가져오기 command를 존재한 적 없는 `/aws-diagram-design:...`으로 적던 것을 `/my-plugins:...`로 수정
- aws-ppt-skills가 `/aws-diagram`, `/aws-diagram-design`을 플러그인 이름 공간 없이 부르던 것을 수정

[Unreleased]: https://github.com/whchoi98/my-plugins/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/whchoi98/my-plugins/releases/tag/v1.0.0
