# 블로그 저장소에 올리기

대상은 `whchoi98.github.io` 저장소(Jekyll, GitHub Pages)다. 저장소의 `CLAUDE.md`와 `docs/CLAUDE.md`가 이 문서보다 우선한다. 두 문서가 다르면 저장소 쪽을 따르고 차이를 사용자에게 알린다.

## 게시물 한 편의 파일

```
docs/techblog/<분류 폴더>/
  <slug>.md               front matter만 있는 파일 (layout: report)
  <slug>-report.html      한영 리포트 페이지. report 레이아웃이 iframe으로 넣는다
  <slug>-assets/          리포트가 가리키는 그림
```

- `<slug>.md`에는 본문을 쓰지 않는다. `report_src`가 리포트 주소를 가리킨다.
- 분류는 `_config.yml`의 `blog_categories`에 있는 이름만 쓴다. 새 분류는 폴더, `index.md`, `_config.yml` 등록, 아이콘이 함께 필요하므로 사용자에게 먼저 묻는다.
- 목록(홈, 분류, 태그)은 `date` 최신순으로 5개씩 보인다. 옮겨 싣는 글은 원문 게시일을 `date`로 쓴다.

## 배치와 빌드

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/place_post.py" "$W/out" <블로그 저장소> --build
```

1. 같은 slug의 글이 있으면 멈춘다. 고친 글을 다시 올릴 때만 `--replace`를 붙인다.
2. 배치한 파일에 `check_post.py --blog`를 다시 실행한다(분류, 아이콘, `report_src` 확인).
3. `--build`는 블로그 저장소에 `scripts/build-lab-zip.sh`가 있으면 먼저 실행하고, `~/.local/share/gem/ruby/*/bin`을 PATH에 더한 뒤 `bundle exec jekyll build -d _site`를 실행한다. 그 다음 글 페이지와 리포트가 `_site`에 생겼는지 본다. Bundler와 Jekyll은 블로그 저장소의 README대로 설치한다(이 플러그인의 setup은 설치하지 않는다).
4. 마지막에 `git add <파일>` 줄을 파일마다 출력한다. 스크립트는 git을 실행하지 않는다.

배치 뒤 검사나 빌드가 실패해도 복사한 파일은 남는다. 작업 폴더에서 고쳐 다시 빌드한 뒤 `--replace`로 배치한다.

## 눈으로 확인

빌드한 사이트를 로컬 서버로 띄워 글꼴까지 불러온 화면을 캡처한다.

```bash
(cd <블로그 저장소>/_site && python3 -m http.server 4173 >/dev/null 2>&1 &)
uv run --no-project --with playwright==1.64.1 python "${CLAUDE_SKILL_DIR}/scripts/preview.py" \
  "http://localhost:4173/docs/techblog/<분류 폴더>/<slug>-report.html" --out-dir "$W/out/preview"
uv run --no-project --with playwright==1.64.1 python "${CLAUDE_SKILL_DIR}/scripts/preview.py" \
  "http://localhost:4173/docs/techblog/<분류 폴더>/<slug>/" --out-dir "$W/out/preview-embedded" --embedded
```

PNG를 Read 도구로 열어 본다. 확인할 것은 다음과 같다.

- 글꼴 줄에 `NanumSquareOTF_ac`와 `D2Coding`이 보이는가(없으면 대체 글꼴로 그려진 것이다)
- 두 언어에서 같은 자리에 같은 요소가 있는가
- 다크에서 표 머리, 코드 상자, 알약의 글자가 읽히는가
- 휴대폰 폭에서 페이지가 옆으로 밀리지 않고 넓은 그림만 상자 안에서 밀리는가
- 임베드 화면에서 리포트의 상단 막대가 숨겨지고 높이가 본문에 맞는가

끝나면 로컬 서버를 내린다. Playwright나 Chromium이 없으면 `my-plugins:setup`을 불러 설치한다.

## git

- `git add -A`를 쓰지 않는다. `place_post.py`가 출력한 파일을 하나씩 스테이징한다.
- 커밋 메시지는 Conventional Commits(`docs:`, `feat:`, `fix:`)다. 저장소의 기존 메시지 언어를 따른다.
- **main에 push하면 곧 배포다.** 커밋과 push는 사용자가 하라고 한 때에만 한다. push 전에 빌드 결과와 올라갈 파일 목록을 보여 준다.
- 배포 뒤에는 글 주소(`https://whchoi98.github.io/docs/techblog/<분류 폴더>/<slug>/`)가 200으로 응답하는지 확인하고 알린다.

## 글을 내리거나 지울 때

게시물을 지우면 그 주소가 404가 된다. 지우는 범위(md, 리포트, 그림 폴더)와 시점은 사용자가 정한다. `git rm`도 파일을 하나씩 지정한다.

## 공개 전 확인

- 계정 ID, 내부 주소, 고객 이름, 시크릿이 본문, 코드, 그림에 없는가. 사내 자료에서 가져온 내용은 공개 문서로 확인되는 것만 싣는다.
- 다른 곳에 먼저 게시한 글이면 `origin`으로 원문을 밝혔는가. 전문을 다시 싣는 것이 원래 게시처의 기준에 맞는지는 사용자가 판단한다.
