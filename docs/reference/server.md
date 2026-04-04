# Server And Runtime Tuning

이 문서는 `agent-server` 실행과 런타임 파라미터를 설명합니다.

## Current Situation

프로젝트의 기본 모델은 `bigatuna/Qwen3.5-9b-Sushi-Coder`입니다.
하지만 16GB VRAM 환경에서는 보수적인 기본값이 더 현실적입니다.

## Important Parameters

### `--gpu-util`

- vLLM이 GPU 메모리를 얼마나 공격적으로 사용할지 정함
- 공유 GPU 환경에서는 낮게 잡는 편이 좋음

### `--max-len`

- 컨텍스트 길이
- 길수록 KV cache 메모리 부담이 커짐

## Practical Profiles

### Shared GPU Profile

권장:

```bash
uv run agent-server --gpu-util 0.70 --max-len 8192
```

### Conservative Profile

권장:

```bash
uv run agent-server --gpu-util 0.60 --max-len 4096
```

### Dedicated GPU Profile

예시:

```bash
uv run agent-server --gpu-util 0.80 --max-len 8192
```

## Why This Matters

- `gpu-util=0.90`
- `max-len=32768`

같은 값은 16GB VRAM 단일 GPU에서 다른 작업과 병행하기엔 과할 수 있습니다.

## Source

- [`coding_agent/server.py`](../../coding_agent/server.py)
