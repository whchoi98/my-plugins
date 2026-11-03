# 참고용 모범 블로그

잘 쓴 AWS 한국 테크 블로그 선집. **품질 기준 참고용이지 문체 복제용이 아니다** — 저자의 톤은 저자 본인 글(또는 사용자와의 합의)에서 가져오고, 여기서는 구조·검증 밀도·표와 다이어그램 사용법을 배운다.

각 글에서 참고할 것과 참고하지 말 것:

## 1. AI Agent를 위한 OpenSearch 검색 품질 평가하기 (Part 1)

https://aws.amazon.com/ko/blogs/tech/evaluate-ai-agent-search-quality-with-amazon-opensearch-service-1/

- **참고할 것**: 실무 질문("검색 품질을 어떻게 측정하고 계신가요?")으로 열고 마치며가 그 질문에 답하는 수미상관. 실측 밀도 — 검증 수치(Spearman 0.94), 함정(형태소 분석기 누락 시 NDCG 급락), 실패 사례(Cohen's Kappa=0.0)까지 공개하는 정직한 서술. 표 도입 문장이 실험 맥락만 설명하고 표 내용을 중복하지 않음

## 2. AWS Graviton으로 EKS 비용 최적화 하기

https://aws.amazon.com/ko/blogs/tech/aws-graviton-eks-optimization/

- **참고할 것**: 전 항목 균형의 표본. 헤딩 없는 리드 문단, 고객 실측 사례(P90 레이턴시 48.2% 개선)와 실제 명령어(docker buildx)의 공존, "프로젝트의 언어·CI/CD·안정성 요구에 따라 적합한 방식이 달라진다"처럼 표의 존재 이유를 설명하는 도입 문장

## 3. 엔터프라이즈 보안 요구사항을 충족하는 프라이빗 Amazon Bedrock AgentCore 구축하기

https://aws.amazon.com/ko/blogs/tech/agentcore-for-enterprise/

- **참고할 것**: 도입에서 구체적 질문 3개를 던지고 마치며가 셋 모두 되짚는 구조. 실배포에서 나온 함정(Keycloak audience mapper, Private DNS 요구사항)과 트래픽 방향별 선택 표

## 4. 백패커의 Amazon EKS 운영 최적화 여정 1부

https://aws.amazon.com/ko/blogs/tech/optimizing-amazon-eks-journey-of-backpackr-part1/

- **참고할 것**: 장애 트러블슈팅 서사 — before/after 수치(에러 주 200건→0건)가 근본 원인 분석(ndots 튜닝 등)과 항상 짝을 이룸. 다이어그램 12개+가 각 장애 시점을 본문 서사와 정합하게 뒷받침
- **참고하지 말 것**: 도입이 문제 제기가 아닌 회사 소개로 시작 — 고객 사례 글의 관행이지만 리드 문단 원칙에 어긋남

## 5. Amazon Bedrock AgentCore Observability로 프로덕션 준비된 AI 에이전트 구축 (산문 가독성 기준)

https://aws.amazon.com/ko/blogs/tech/amazon-bedrock-agentcore-observability-production-ready-ai-agent/

- **참고할 것**: 문장 길이와 리듬. 한 문장에 한 생각, 개념 정의 뒤 곧바로 설정 예시. 이 글의 읽기 난도가 레벨 200~300 원고의 기준선이다

## 6. 이 스킬로 만든 원고 (구조 기준)

- 2026-09-18 "월 DTO가 얼마를 넘으면 정액제가 유리한가 – AWS Direct Connect 정액 요금제(Flat-rate) 손익분기점 분석": 질문형 제목, 가상 청구서 1건 기준 계산, 손익분기 라인 차트 + 요금제별 막대, 문서 상충 병기(6.2절), 전환 절차 번호 목록, 게시 전 확인 항목 전달. 예시 구성 변경(6회선 → 2회선 20 Gbps → 8월 가상 청구서) 요청을 세 번 받아 본문·표·그림·마치며를 매번 한 턴에 재계산한 사례

