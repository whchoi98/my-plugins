# Claude Code 사용 가이드

my-plugins에 든 aws-diagram-design 스킬과 슬래시 커맨드 3종을 Claude Code에서 쓰는 방법이다. aws-diagrams 플러그인에 있던 aws-diagram-design 문서를 my-plugins 설치 방식과 이름 공간에 맞게 고쳤다.

## 설치

### 방법 1 — 플러그인 (권장)

스킬과 슬래시 커맨드 3종이 my-plugins 플러그인에 함께 들어 있다. 터미널에서:

```bash
claude plugin marketplace add whchoi98/my-plugins
claude plugin install my-plugins@my-plugins
```

Claude Code 세션 안에서는 `/plugin marketplace add whchoi98/my-plugins`, `/plugin install my-plugins@my-plugins`로 같은 일을 한다. 설치 후 `/reload-plugins`를 실행하거나 세션을 재시작한다. 로컬 클론에서 설치할 때는 `whchoi98/my-plugins` 대신 클론 경로를 준다.

예전 단독 플러그인 `aws-diagrams@aws-diagrams`를 설치했다면 제거한다. 남겨두면 같은 스킬이 예전 이름으로 한 번 더 로드된다. 제거 명령과 claude.ai 동기화 사본 정리는 README의 "단독 플러그인에서 옮겨 올 때" 절에 있다. 갱신은 `claude plugin marketplace update my-plugins` 뒤 `claude plugin update my-plugins@my-plugins`다.

### 방법 2 — 스킬 단독

슬래시 커맨드 없이 스킬만 쓰려면 심링크 하나로 충분하다:

```bash
ln -s <my-plugins 클론>/skills/aws-diagram-design ~/.claude/skills/aws-diagram-design
```

심링크라 저장소를 수정하면 즉시 반영된다. 단독 스킬에는 `my-plugins:` 이름 공간과 커맨드가 없으므로 내보내기와 가져오기는 자연어로 요청한다. 플러그인 전체를 작업 트리 그대로 시험할 때는 클론에서 `claude --plugin-dir .`을 쓴다.

## 기존 diagram-design 플러그인 정리

이 플러그인은 "marketplace판 diagram-design + AWS 스킨 오버레이" 구성을 대체한다. 둘을 같이 켜두면 트리거 조건이 겹치는 스킬 두 개가 경쟁하므로 다음을 정리한다.

1. 기존 플러그인 제거: `/plugin` → diagram-design → uninstall. disable만 하면 캐시 트리(`~/.claude/plugins/cache/diagram-design/`)가 남아 SessionStart 훅이 계속 그 트리를 대상으로 삼는다 — 지금은 스킨 마커(`.aws-skin-applied`)가 있어 조용할 뿐, 오버레이의 `SKIN_VERSION`을 올리면 비활성화된 플러그인을 다시 패치한다.
2. SessionStart 훅 정리: `~/.claude/settings.json`의 `apply_aws_skin.py` 훅은 실패하지 않지만(항상 exit 0) 플러그인 uninstall 뒤에는 세션마다 `[aws-diagram-skin] diagram-design plugin not found; nothing to do.` 한 줄을 출력한다. 훅 항목을 제거하면 이 출력도 사라진다. `~/.claude/aws-diagram-skin/` 디렉터리는 업스트림 신규 버전에 AWS 스킨을 재적용할 때 다시 쓸 수 있으므로 남겨두는 편이 낫다.

## 사용법

### 자동 트리거

"AWS 아키텍처 다이어그램 그려줘", "구성도 만들어줘", "이 흐름을 플로차트로" 같은 요청이면 스킬이 자동으로 걸린다. 영어·한글 트리거 모두 SKILL.md description에 들어 있다.

```
빗썸 시세 수집 파이프라인 아키텍처 다이어그램 그려줘.
API Gateway → Lambda → Kinesis → S3, 모니터링은 CloudWatch.
```

AWS 서비스를 지명하면 공식 아이콘이 자동으로 들어가고, VPC·서브넷·계정 경계는 공식 그룹 컨벤션(테두리 색 + 좌상단 배지)으로 그려진다. 명시 호출은 `/my-plugins:aws-diagram-design`이다. 공식 아이콘 조회나 Bedrock AgentCore 아이콘이 필요한 AWS 서비스 구성도는 같은 플러그인의 `/my-plugins:aws-diagram`이 맡는다.

### 슬래시 커맨드

| 커맨드 | 역할 |
|--------|------|
| `/my-plugins:export-diagram <html> [--svg-only\|--png-only] [--scale=N] [--output=<path>]` | 생성된 HTML을 .svg/.png로 내보내기 |
| `/my-plugins:import-drawio <file.drawio>` | draw.io 원본을 에디토리얼 스타일로 다시 그리기 |
| `/my-plugins:import-mermaid <file.mmd>` | Mermaid 원본을 다시 그리기 |

임포트 커맨드 둘은 `--format=html|svg|png|html+png`, `--size=<프리셋>`, `--detail=faithful|balanced|simplified`, `--audience=engineer|mixed|executive`, `--variant=light|dark|full`, `--output=<경로>`, 페이지 선택(`--page`/`--diagram`)까지 받는다. 전체 시그니처의 기준은 각 `commands/*.md`의 argument-hint다.

### PNG/SVG 내보내기 사전 준비

내보내기는 headless Chromium을 쓴다. `/my-plugins:setup`이 Playwright Chromium과 시스템 라이브러리, Amazon Ember를 한 번에 점검하고 설치한다. 클론에서 직접 실행할 때는:

```bash
bash skills/setup/scripts/setup.sh install
```

시스템 라이브러리에 sudo가 필요하면 `install --sudo`로 다시 실행한다. 모드와 Amazon Linux 2023의 동작은 [setup-dependencies.md](../runbooks/setup-dependencies.md)에 있다.

## 산출물 검증

저장소를 체크아웃한 상태라면 생성된 다이어그램을 스크립트로 검증할 수 있다:

```bash
python3 skills/aws-diagram-design/scripts/self_check.py <생성된.html>   # 접근성·단일 파일 계약
python3 scripts/diagrams/verify-geometry.py <생성된.html>               # 라벨 마스크-노드 겹침
python3 scripts/diagrams/verify-motion.py <생성된.html>                 # 모션 사용 시
```

설치된 스킬로 쓸 때도 `self_check.py`는 스킬 디렉터리에 함께 배포되므로 그대로 실행된다.

## 폰트

Amazon Ember가 로컬에 설치돼 있어야 지정 서체로 렌더링된다. 브라우저·스크린샷 결과가 Helvetica로 보이면 폰트 미설치 상태다. `fc-list | grep -i "Amazon Ember"`로 확인하고, 없으면 `/my-plugins:setup`으로 설치한다. 폰트 파일은 `skills/aws-diagram-design/assets/fonts/`에 들어 있다.
