# Implementation Plan

기준 시각: 2026-04-04

## Goal

이 프로젝트를 "로컬에서 실무에 쓸 수 있는 코딩 에이전트"로 다듬는다.
핵심은 모델 자체보다 도구 계층, 검증 루프, 메모리 compact, 복구 가능성이다.

## Priorities

### 1. Runtime Tuning

- RTX 5080 16GB 기준 현실적인 `gpu-util`, `max-len` 기본값 적용
- 사용 시나리오별 서버 프로필 문서화
- 모델별 서버 옵션 분리

### 2. Verification Quality

- 수정 후 어떤 검증을 돌릴지 더 잘 고르는 루프 추가
- 실패 로그 요약 강화
- self-check를 검증 단계에 더 명시적으로 통합

### 3. Planning Quality

- 문서 기반 planner 강화
- 큰 작업을 하위 단계로 나누는 흐름 개선
- plan과 실제 결과를 비교하는 post-check 추가

### 4. Memory Quality

- compact summary의 품질 개선
- 최근 도구 결과에서 중요한 정보만 더 잘 추출
- 장기적으로 SQLite 전환 여부 검토

### 5. Docs Quality

- cookbook 확장
- 기능별 reference 유지
- 파라미터 튜닝 문서 강화

## Workstreams

### Tooling

- 도구별 반환 형식 정리
- 더 정밀한 패치/편집 기능 검토

### Recovery

- 복구 대상을 1건 이상 선택할 수 있는 UX
- 복구 전 미리보기 기능 검토

### CLI

- `status` 확장
- working memory 상태 요약 표시 검토

## Definition Of Better

- 처음 보는 개발자가 문서만 읽고 실행 가능
- 에이전트가 수정 후 검증까지 수행 가능
- 잘못 고치면 복구 가능
- 긴 세션에서도 컨텍스트가 무너지지 않음

## Related Docs

- [Documentation Hub](./README.md)
- [Server And Runtime Tuning](./reference/server.md)
- [Memory And Compact](./reference/memory.md)
- [Recovery And Rollback](./reference/recovery.md)
