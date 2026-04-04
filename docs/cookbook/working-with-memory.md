# Working With Memory

이 문서는 에이전트가 긴 세션을 어떻게 버티는지 설명합니다.

## Why It Exists

로컬 GPU 환경에서는 컨텍스트 길이를 무한정 늘리는 방식이 비효율적입니다.
그래서 이 프로젝트는 "큰 컨텍스트"보다 "짧은 작업 메모 + compact + 필요 시 재조회" 구조를 사용합니다.

## Saved Files

- `.agent_state/working_memory.json`
- `.agent_state/session_summary.md`

## What Is Stored

- 현재 작업
- 마지막 응답
- 최근 변경 요약
- 최근 검증 결과
- 최근 도구 사용 기록
- compact summary

## Compact Strategy

히스토리가 길어지면 오래된 대화를 `[COMPACT SUMMARY]` 시스템 메시지로 압축하고, 최신 메시지만 유지합니다.

## Why This Helps

- GPU 메모리 사용 압박 감소
- 대화가 길어져도 핵심 상태 유지
- 원문이 필요하면 도구로 다시 읽을 수 있음

## Related Docs

- [Memory And Compact](../reference/memory.md)
- [Tool Reference](../reference/tools.md)
