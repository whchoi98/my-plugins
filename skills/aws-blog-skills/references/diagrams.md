# 다이어그램 — 블로그 프로필

그림 하나마다 `.html`(렌더용), `.svg`(원본), `.png`(게시용) 세 파일을 만든다. 어느 도구로 그리든 아래 토큰, 타입 램프, 기하 규칙이 블로그 프로필이다.

## 도구 선택 (2026-11-01 추가)

| 그림 | 도구 | 산출과 후처리 |
|---|---|---|
| AWS 서비스 아키텍처 구성도(VPC, 서브넷, 서비스 간 데이터 경로, AgentCore 구성) | `/my-plugins:aws-diagram` | 공식 아이콘을 `find_icon.py`로 찾아 SVG를 만들고 `embed.py`로 아이콘을 내장. 블로그 프로필 크기(1280×720)와 한국어 라벨로 그린 뒤, SVG를 감싼 HTML을 `scripts/render_diagrams.py`로 렌더 |
| 구조 다이어그램(흐름도, 시퀀스, 상태 전이, 타임라인, 스윔레인, 계층, 사분면) | `/my-plugins:aws-diagram-design` | HTML로 그리고 `/my-plugins:export-diagram`으로 SVG와 PNG를 만든다. 플러그인의 `self_check.py`와 `verify-geometry.py`를 실행 |
| 기존 draw.io나 Mermaid 그림을 블로그용으로 다시 그리기 | `/my-plugins:import-drawio`, `/my-plugins:import-mermaid` | 다시 그린 HTML을 위와 같이 내보냄 |
| 손익분기 라인 차트, 비용 비교 막대, 블로그 고유의 구성 비교(A vs B) | 내부 `scripts/diagram_lib.py`(Canvas) | `scripts/render_diagrams.py`로 렌더. 기하 규칙을 assert로 강제 |

- aws-diagram이나 aws-diagram-design으로 그릴 때도 색은 아래 토큰을 쓴다. 특히 오렌지는 과금과 손익분기점에만 쓰고, 같은 비교 대상의 색은 그림 사이에서 고정한다
- 다이어그램 텍스트에는 아래 기하 규칙의 구분자 규칙(슬래시 구분자, 가운뎃점 금지)과 style.md 용어 표기를 그대로 적용한다
- 어느 도구로 만들었든 렌더 로그의 `fonts: True`와 `overflow: []`를 확인하고 PNG를 눈으로 본다

## 토큰

| 이름 | 값 | 용도 |
|---|---|---|
| paper | `#FFFFFF` | 배경, 라벨 플레이트 |
| ink | `#232F3E` | 노드 이름, 제목, 기존/종량제 계열 |
| muted | `#545B64` | 부제, 화살표, 범례 텍스트 |
| soft | `#7D8998` | 주석, 화살표 라벨 |
| rule | `rgba(35,47,62,0.12)` | 구분선 |
| accent | `#EC7211` | 과금($) 텍스트, 손익분기점, 절감률. **한 그림에 focal 노드 2개 이하** |
| series-teal | `#01A88D` | A 구성 |
| series-purple | `#8C4FFF` | B 구성 |
| link | `#0972D3` | 링크성 화살표 |

같은 비교 대상이 여러 그림에 나오면 색을 고정한다(기존/종량제 = ink, A = teal, B = purple). 오렌지는 돈과 손익분기점에만 쓴다.

## 타입 램프 (viewBox 1280×720)

| 요소 | 크기 | 굵기 | 폰트 |
|---|---|---|---|
| 그림 제목(캔버스 상단), 노드 이름, 존 제목, 축 카테고리 라벨 | 20px | 600 | Amazon Ember |
| sublabel, eyebrow, 화살표 라벨, 범례, 축 눈금, 주석 | 16px | 400 | sublabel·숫자는 Amazon Ember Mono |
| 화살표 라벨 플레이트 | 높이 24px/줄, 선에서 8px 간격 | | |
| 범례 제목 | "범례" 16px 600 muted, letter-spacing 없음 | | |

한글은 Noto Sans CJK KR로 폴백된다. 렌더 로그에서 `fonts: True`를 확인한다.

## 기하 규칙 (lib가 assert로 강제)

- 모든 좌표와 텍스트 baseline은 4의 배수
- 노드-노드 겹침 금지, 라벨 플레이트-노드 겹침 금지, 캔버스 밖 금지
- 같은 트래픽 흐름 위의 노드(예: DXGW → 전용 연결 → 고객 라우터)는 하단 변을 맞추고 화살표는 세로 중심선(같은 y)을 지난다 (2026-09-18 확정)
- sublabel은 노드 폭 안에 들어와야 한다. 세 항목 이상을 슬래시로 이을 때 반복 접두어("AWS 장비 A" → "장비 A")를 제거해 폭을 맞춘다 (2026-09-18 확정)
- 존 eyebrow(부제) 아래 첫 내부 존은 eyebrow baseline보다 최소 8px 아래에서 시작
- 텍스트 구분자는 슬래시 `/`, 가운뎃점 금지. `/ /` 충돌은 쉼표로 해소
- 범례는 캔버스 하단(y=648 또는 664), 항목 라벨은 한국어. 가로 폭이 넘치면 라벨을 줄인다(범례 폭 초과는 오버플로 게이트가 잡는다)

## 그림 유형별 관례

**아키텍처(기존 구성)**: AWS Cloud 존 > 리전 존(VPC, Direct Connect Gateway) → DX 로케이션 존(전용 연결 N개) → 온프레미스 존(고객 라우터). 과금 항목은 존 하단 주석에 `$`로, DTO 화살표는 accent. 회선이 많으면 2개 열로 배치하거나 캡션에서 간략화를 밝힌다.

**구성 비교(A vs B)**: 좌우 두 존. Resiliency Group은 점선 존, 예비 포트는 `standby`(점선 테두리) 노드. 존 하단에 정액 요금 합계와 장애 시 잔여 용량 주석.

**손익분기 라인 차트**: x = 월 DTO(TB), y = 월 비용(천 USD). 종량제 직선(ink 2.4px), 정액 수평선(teal/purple 2.4px), 교차점 accent 원(r=7) + 점선 드롭라인 + 라벨 "손익분기 A: 114 TB (평균 376 Mbps)". 실적·가상 청구서 점은 흰 채움 ink 테두리 원. 축 눈금은 4px 그리드에 맞는 간격으로 정한다(예: 폭 1,040px에 4,000 TB → 260px/1,000 TB; 폭 1,040px에 2,000 TB → 208px/400 TB). 라벨은 선과 교차하지 않는 위치에 두고 PNG를 눈으로 확인한다.

**비용 비교 막대**: 그룹당 최대 3개 막대(기존/A/B). 종량제 막대는 포트(진한)와 DTO(연한)로 쌓아 나눌 수 있다. 값 라벨은 막대 위 16px mono, 그룹 라벨 20px 600, 그 아래 절감률 16px accent mono. 음수 절감률은 `A -6.9%`처럼 표기하고 범례에 "음수 = 종량제가 저렴"을 적는다.

## 렌더 파이프라인

```bash
# 폰트 설치(처음 한 번). 자산 경로는 플러그인 설치 위치에 따라 다르므로 diagram_lib이 찾게 한다
ASSETS=$(python3 "${CLAUDE_SKILL_DIR}/scripts/diagram_lib.py" --assets)
if ! fc-list | grep -qi "Amazon Ember"; then
  mkdir -p ~/.local/share/fonts/ember            # macOS는 ~/Library/Fonts/
  cp "$ASSETS/fonts/ttf/"*.ttf ~/.local/share/fonts/ember/
  fc-cache -f
fi

# 생성 → 렌더 (diagram_lib.py와 diagrams.py는 작업 폴더 $W/diagrams/에 복사해 둔 것)
(cd "$W/diagrams" && BLOG_IMAGES="$W/images" python3 diagrams.py)   # Canvas.write(html, svg), check()로 기하 검증
uv run --no-project --with playwright==1.64.1 python "${CLAUDE_SKILL_DIR}/scripts/render_diagrams.py" "$W/images"   # 2560×1440 PNG
```

`render_diagrams.py`는 `document.fonts.ready` 대기 후 Ember/Noto 로드 여부와 `<text>` getBBox 오버플로를 로그로 출력한다. `overflow: []`가 아니면 라벨을 줄이거나 옮긴다. aws-diagram-design skill의 `scripts/verify-geometry.py`와 `scripts/self_check.py`도 html에 대해 실행해 0 finding을 확인한다.

## 아이콘

aws-diagram-design skill `assets/aws-icons/` 아래 공식 아이콘을 base64 data URI로 노드에 삽입한다(`diagram_lib.ICONS`에 경로 등록). 자주 쓰는 것: Direct Connect, Direct Connect Gateway, VPC, Customer Gateway, Servers(온프레미스 라우터). 브랜드 캐릭터나 비공식 아이콘은 쓰지 않는다.

## 수정 요청 처리

- "하단 박스 수평 정렬": 대상 노드의 y를 같은 값으로, 화살표 y를 중심선으로, 밀려난 주석 y를 재배치, sublabel 폭 재확인
- 라벨이 선과 겹침: 라벨을 선의 반대편 또는 선이 지나지 않는 x 구간으로 이동. 계산으로 선의 y를 구해 확인
- 텍스트가 노드 밖으로 나감: 노드 폭 확대(존 안 패딩 16~24 유지) 또는 텍스트 축약
