# aws-blog-skills

AWS Korea Tech Blog 한국어 원고 통합 스킬. SKILL.md의 워크플로우를 따르고 references/를 단계별로 읽는다.

- references/structure.md   원고 골격, 바이라인, 캡션, 저자 소개
- references/style.md       금지어, 용어 표기, 권고 표현, 출처 서술
- references/humanize-checklist.md  AI 티 점검
- references/verification.md 사실 검증, 카테고리 검증, 문서 상충
- references/diagrams.md     다이어그램 블로그 프로필
- references/exemplars.md    모범 글
- references/collaboration.md 공동 저자 원고
- scripts/diagram_lib.py     SVG Canvas 라이브러리(기하 assert 포함)
- scripts/example_diagrams.py 그림 4장 생성 예시(아키텍처, 비교, 손익분기 차트, 막대)
- scripts/render_diagrams.py Playwright 렌더(폰트·오버플로 게이트)
- scripts/lint_prose.py      금지어·AI 티 스윕
- scripts/check_structure.py 구조 검사
- scripts/check_urls.py      URL 전수 확인(HTTP 200, 다른 페이지로 리디렉션 여부)
- scripts/package_blog.sh    번들 조립 → 구조 검사, lint → zip(기본 출력 <작업 폴더>/out)
- assets/templates/blog-template.md 원고 템플릿

의존: 같은 my-plugins 플러그인의 aws-diagram, aws-diagram-design(아이콘, Amazon Ember TTF), kor-deslop skill. Playwright chromium, Noto Sans CJK KR은 `/my-plugins:setup`으로 설치. 선택: humanize-korean 플러그인(metrics_v2.py).
규칙을 확정하면 references에 "(YYYY-MM-DD 확정)"으로 추가하고 패치 파일을 함께 전달한다.
