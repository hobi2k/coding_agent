# Documentation

이 문서는 `coding_agent` 프로젝트의 문서 허브입니다. 현재 문서는 GGUF + Ollama 아키텍처를 기준으로 정리되어 있습니다.

## Start Here

1. [Quickstart](./cookbook/start-here.md)
2. [First Run](./cookbook/first-run.md)
3. [Architecture Overview](./reference/architecture.md)
4. [Tool Reference](./reference/tools.md)

## Cookbook

- [Quickstart](./cookbook/start-here.md)
- [First Run](./cookbook/first-run.md)
- [Restore Workflow](./cookbook/restore-workflow.md)
- [Working With Memory](./cookbook/working-with-memory.md)

## Reference

- [Architecture](./reference/architecture.md)
- [Tool Reference](./reference/tools.md)
- [Memory And Compact](./reference/memory.md)
- [Recovery And Rollback](./reference/recovery.md)
- [Server And Runtime](./reference/server.md)
- [Current Status](./current-status.md)
- [Implementation Plan](./plan.md)
- [Style Guide](./styleguide.md)

## Reading Paths

### 지금 바로 실행하고 싶다

- [Quickstart](./cookbook/start-here.md)
- [First Run](./cookbook/first-run.md)
- [Server And Runtime](./reference/server.md)

### 원리와 구조를 이해하고 싶다

- [Architecture](./reference/architecture.md)
- [Tool Reference](./reference/tools.md)
- [Memory And Compact](./reference/memory.md)
- [Recovery And Rollback](./reference/recovery.md)

### 기여하거나 확장하고 싶다

- [Current Status](./current-status.md)
- [Implementation Plan](./plan.md)
- [Style Guide](./styleguide.md)

## Source Map

- 코어 코드: [`coding_agent/`](/home/hosung/pytorch-demo/coding_agent/coding_agent)
- 메인 엔트리포인트:
  - [`cli.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/cli.py)
  - [`agent.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/agent.py)
  - [`tools.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/tools.py)
  - [`server.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/server.py)
  - [`download.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/download.py)
