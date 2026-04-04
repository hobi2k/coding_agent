# Style Guide

이 문서는 `coding_agent` 프로젝트의 코드 스타일 기준을 설명합니다.

## Goals

- 처음 보는 개발자도 빠르게 이해할 수 있는 코드 유지
- 과한 주석보다 필요한 설명만 남기기
- 함수 설명 형식을 프로젝트 전체에서 통일하기

## Comments

### General Rules

- 주석은 "코드가 무엇을 하는지"보다 "왜 이렇게 하는지"를 설명할 때만 쓴다.
- 한 줄만 읽어도 자명한 코드는 주석을 달지 않는다.
- 복잡한 분기, 안전 장치, 복구 로직, 메모리 compact 같은 부분에만 짧게 주석을 남긴다.
- 주석은 코드와 멀어지지 않게 바로 위에 둔다.
- TODO 주석은 남발하지 않는다. 남길 경우 작업 이유가 분명해야 한다.

### Good

```python
# 오래된 대화는 요약으로 압축하고 최근 메시지만 유지한다.
self.history, compact_summary = _compact_history(self.history)
```

### Avoid

```python
# history를 compact한다.
self.history, compact_summary = _compact_history(self.history)
```

## Docstrings

### Required Format

함수 독스트링은 아래 형식을 따른다.

```python
"""함수 동작

Args:
    arg_name: 설명

Returns:
    반환값 설명
"""
```

### Important Rule

- `Args:`가 필요 없으면 `Args:` 섹션은 생략한다.
- `Returns:`가 필요 없으면 `Returns:` 섹션은 생략한다.
- 즉 모든 함수에 무조건 `Args:`와 `Returns:`를 쓰는 것이 아니라, 필요한 섹션만 남긴다.

## Docstring Examples

### No Args, No Returns Section

```python
def reset(self):
    """대화 히스토리를 초기화한다."""
```

### Args Only

```python
def log_event(message: str) -> None:
    """로그 이벤트를 기록한다.

    Args:
        message: 저장할 로그 메시지.
    """
```

### Args And Returns

```python
def check_server_connection(base_url: str, timeout: float = 3.0) -> tuple[bool, str]:
    """서버 연결 상태를 점검한다.

    Args:
        base_url: 점검할 서버 주소.
        timeout: 요청 타임아웃 초 단위 값.

    Returns:
        연결 성공 여부와 상태 설명 문자열.
    """
```

### Returns Only

```python
def current_platform_name() -> str:
    """현재 플랫폼 이름을 반환한다.

    Returns:
        현재 플랫폼 이름.
    """
```

## Naming

- 함수명은 동작이 드러나게 짓는다.
- 불리언 함수는 가능하면 `is_`, `has_`, `should_`, `can_` 같은 접두어를 사용한다.
- 내부 헬퍼는 `_` 접두어를 사용해 공개 API와 구분한다.

## Project-Specific Guidance

- 복구 관련 함수는 "무엇을 복구하는지"가 이름에서 보여야 한다.
- 메모리 관련 함수는 `working_memory`, `summary`, `compact` 같은 용어를 일관되게 사용한다.
- 도구 함수는 에이전트가 읽기 쉬운 반환값을 우선한다.

## Related Docs

- [Documentation Hub](./README.md)
- [Tool Reference](./reference/tools.md)
- [Memory And Compact](./reference/memory.md)
