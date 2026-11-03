# Kiro 사용 가이드 (IDE · CLI)

Kiro는 IDE와 CLI 모두 Anthropic 형식 Agent Skills(SKILL.md)를 네이티브로 읽는다. my-plugins 클론의 `skills/aws-diagram-design/`을 그대로 스킬 디렉터리에 넣으면 동작한다. my-plugins는 Claude Code 플러그인 매니페스트(`.claude-plugin/`)만 두고 Kiro Power용 루트 `plugin.json`은 두지 않으므로, Power 설치는 지원하지 않는다.

## 설치

먼저 저장소를 받는다:

```bash
git clone https://github.com/whchoi98/my-plugins.git
```

### 방법 1 — 사용자 레벨 스킬 (권장)

모든 워크스페이스에서 동작한다:

```bash
mkdir -p ~/.kiro/skills
cp -r my-plugins/skills/aws-diagram-design ~/.kiro/skills/                        # ~/.kiro/skills/aws-diagram-design/ 에 복사
ln -s "$PWD/my-plugins/skills/aws-diagram-design" ~/.kiro/skills/aws-diagram-design   # 복사 대신 심링크 (저장소 수정이 즉시 반영, 개발용)
```

두 명령 중 하나만 쓴다.

### 방법 2 — 워크스페이스 스킬

특정 프로젝트에만 쓰고 팀과 커밋으로 공유하려면:

```bash
cd <프로젝트 루트>
mkdir -p .kiro/skills && cp -r <my-plugins 클론>/skills/aws-diagram-design .kiro/skills/   # .kiro/skills/ 에 복사
```

같은 이름이 양쪽에 있으면 워크스페이스 스킬이 우선한다.

### 방법 3 — IDE 임포트 UI

Kiro IDE의 Agent Steering & Skills 패널 → `+` → Import a skill → Local folder에서 `skills/aws-diagram-design` 폴더를 선택한다. GitHub URL로 임포트할 때는 저장소 루트가 아니라 **스킬 서브디렉터리**(`github.com/whchoi98/my-plugins/tree/main/skills/aws-diagram-design`)를 가리켜야 한다. 임포트는 복사 방식이라 이후 저장소 변경을 따라가지 않는다.

AWS 서비스 구성도용 `skills/aws-diagram/`도 같은 방법으로 넣을 수 있다.

## 사용법

- 기본 에이전트(IDE 채팅, `kiro-cli chat`)는 스킬을 자동 발견한다. "AWS 아키텍처 다이어그램 그려줘" 같은 요청이면 description 매칭으로 활성화된다.
- 명시 호출: `/aws-diagram-design` (CLI 2.1 이상에서 스킬이 슬래시 커맨드로 노출된다). Kiro에는 Claude Code 플러그인 이름 공간이 없으므로 `my-plugins:`를 붙이지 않는다.
- Claude Code용 슬래시 커맨드(`commands/`, Claude Code에서는 `/my-plugins:export-diagram` 등)는 Kiro가 읽지 않는다. draw.io·Mermaid 임포트와 내보내기는 자연어로 요청하면 스킬 본문의 라우팅이 처리한다. 예: "이 diagram.drawio를 슬라이드용으로 다시 그려줘", "방금 만든 HTML을 PNG로 내보내줘".

### 커스텀 에이전트 주의

커스텀 에이전트(`kiro-cli chat --agent <이름>`)는 스킬을 자동 상속하지 않는 빌드가 있다. 에이전트 설정(`.kiro/agents/<이름>.json`)에 리소스를 선언한다:

```json
{
  "resources": [
    "skill://~/.kiro/skills/**/SKILL.md",
    "skill://.kiro/skills/**/SKILL.md"
  ]
}
```

## 내보내기·검증

Kiro 에이전트는 셸 실행이 가능하므로 Claude Code와 동일하게 동작한다:

```bash
bash <my-plugins 클론>/skills/setup/scripts/setup.sh install   # Playwright Chromium, Amazon Ember 등 내보내기 사전 준비 (1회)
python3 <스킬 경로>/scripts/self_check.py <생성된.html>          # 산출물 자체 점검
```

`setup.sh`는 인자 없이 실행하면 점검만 하고, 시스템 라이브러리에 sudo가 필요하면 `install --sudo`로 다시 실행한다([setup-dependencies.md](../runbooks/setup-dependencies.md)). `drawio_extract.py`, `mermaid_extract.py`도 스킬 폴더에 함께 설치되므로 임포트 시 에이전트가 직접 실행한다.

## 제약 요약

| 항목 | 내용 |
|------|------|
| 슬래시 커맨드 | Claude Code `commands/`는 미지원 — 스킬 슬래시(`/aws-diagram-design`) 또는 자연어로 대체 |
| Power | my-plugins에는 Kiro Power용 루트 `plugin.json`이 없어 미지원 — 방법 1~3으로 설치 |
| GitHub 임포트 | 스킬 서브디렉터리 URL만 허용, 복사 방식이라 업데이트 추적 없음 |
| 스티어링 | 이 스킬에는 불필요 — 스티어링은 상시 로드라 레퍼런스가 매 프롬프트에 끌려 들어간다 |
| 폰트 | Amazon Ember 로컬 설치 필요 (`skills/setup/scripts/setup.sh install`이 설치) |
