# Documentation

이 문서는 `coding_agent` 프로젝트의 문서 허브입니다.
처음 보는 개발자는 아래 순서대로 읽으면 됩니다.

## Start Here

1. [Quickstart](./cookbook/start-here.md)
2. [First Run](./cookbook/first-run.md)
3. [Restore Workflow](./cookbook/restore-workflow.md)
4. [Architecture Overview](./reference/architecture.md)

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
- [Server And Runtime Tuning](./reference/server.md)
- [Current Status](./current-status.md)
- [Implementation Plan](./plan.md)

## Recommended Reading Paths

### I just want to run it

- [Quickstart](./cookbook/start-here.md)
- [First Run](./cookbook/first-run.md)

### I want to understand how it works

- [Architecture](./reference/architecture.md)
- [Tool Reference](./reference/tools.md)
- [Memory And Compact](./reference/memory.md)
- [Recovery And Rollback](./reference/recovery.md)

### I want to contribute

- [Current Status](./current-status.md)
- [Implementation Plan](./plan.md)
- [Architecture](./reference/architecture.md)

## Source Map

- Core code: [`coding_agent/`](../coding_agent/)
- Main entrypoints:
  - [`coding_agent/cli.py`](../coding_agent/cli.py)
  - [`coding_agent/agent.py`](../coding_agent/agent.py)
  - [`coding_agent/tools.py`](../coding_agent/tools.py)
  - [`coding_agent/server.py`](../coding_agent/server.py)
  - [`coding_agent/download.py`](../coding_agent/download.py)
