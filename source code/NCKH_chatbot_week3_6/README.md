# Adaptive Multi-Path Inference for Multi-Tenant LLM Systems

This repository contains the implementation workspace for the project:

`Adaptive Multi-Path Inference for Multi-Tenant LLM Systems with Shared Models and LoRA-based Personalization`

The project is being developed as a:

- systems-and-application study
- multi-tenant LLM serving architecture
- Docker-first research artifact

Its central goal is not to propose a new base model, a new LoRA algorithm, or a new retriever in isolation.  
Instead, it focuses on how to combine:

- adaptive multi-path inference
- shared-model serving
- LoRA-based tenant personalization
- tenant-aware runtime
- tenant isolation

into one practical serving architecture for heterogeneous enterprise workloads.

## 1. Core Idea

The system is designed for multi-tenant environments where:

- multiple tenants share a common LLM serving backbone
- different tenants still require tenant-specific customization
- incoming queries are heterogeneous
- a fixed one-path pipeline is inefficient

Instead of forcing all requests through the same inference path, the system supports:

- `tool` path
- `retrieval` path
- `general` path
- `out_of_scope` path

The runtime can operate in:

- `adaptive` mode
- `fixed retrieval` mode
- `fixed general` mode
- `fixed tool` mode when applicable

This enables benchmarking and ablation around the project’s central research question:

**Can adaptive multi-path serving improve efficiency while maintaining quality in multi-tenant LLM systems with shared models and LoRA-based personalization?**

## 2. Repository Structure

- `project_root/`
  Runtime, router, workflow, retrieval, API, runtime manager, memory, tools.
- `evaluation/`
  Retrieval evaluation, answer evaluation, benchmark runner, generated reports and artifacts.
- `pipeline1/`
  Dataset generation and preparation for tenant-specific QA / instruction data.
- `pipeline2/`
  LoRA training pipeline for tenant-specific adapters.
- `pipeline3/`
  LoRA loading and smoke-test utilities.
- `personalization/`
  Tenant-scoped data, datasets, adapters, and reports.
- `docs/`
  Project direction, checklist, setup guide, machine-transfer guide, paper framing notes.
- `run_me.py`
  Launcher for local / unified execution flows.

## 3. Current Research Direction

The repo is being developed according to these priorities:

1. Make the runtime truly reflect the paper title
2. Validate tenant isolation and multi-tenant behavior
3. Build benchmark and ablation evidence
4. Measure systems efficiency
5. Improve reproducibility and artifact packaging

See:

- [docs/Yeu cau va Muc dich paper.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/Yeu%20cau%20va%20Muc%20dich%20paper.md)
- [docs/CHECKLIST.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/CHECKLIST.md)

## 4. Recommended Environment

### Official environment

`Docker`

Docker should be treated as the standard environment for:

- runtime execution
- benchmark runs
- adaptive vs fixed-route comparison
- reproducibility across machines

### Secondary environment

`venv`

Use `venv` only for:

- quick debugging
- exploratory local scripting
- lightweight development tasks

Short version:

- `Docker-first`
- `venv-second`

## 5. Quick Start

### Step 1: Create `.env`

```bash
cp .env.example .env
```

### Step 2: Build and start services

```bash
make bootstrap
```

This starts:

- `dev` container for development and benchmark commands
- `api` service
- `ui` service

Default endpoints:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`

### Step 3: Check service state

```bash
make ps
```

### Step 4: Open a dev shell

```bash
make dev-shell
```

## 6. Environment Variables

Important variables in `.env.example`:

- `OLLAMA_MODEL`
- `SHARED_OLLAMA_MODEL`
- `OLLAMA_BASE_URL`
- `API_PORT`
- `STREAMLIT_PORT`
- `ENABLE_PERSONALIZATION`
- `FIXED_ROUTE_MODE`

Recommended default:

- `FIXED_ROUTE_MODE=adaptive`

Override this only when running fixed-route benchmarks.

## 7. API and Runtime Checks

### Health check

- `GET /health`

### Runtime status

- `GET /status?tenant_id=default&user_id=guest`

### Chat endpoint

The `/chat` endpoint now supports route telemetry in metadata, including:

- `route_reason`
- `route_score`
- `route_candidates`
- `route_features`
- `route_mode`
- `route_policy`
- `shared_model_name`
- `adapter_enabled`
- `adapter_available`
- `adapter_path`

It also accepts optional `fixed_route_mode` values:

- `adaptive`
- `retrieval`
- `general`
- `tool`
- `out_of_scope`

## 8. Benchmark Commands

### Adaptive baseline

```bash
make benchmark-adaptive
```

Equivalent command:

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label adaptive_baseline
```

### Fixed retrieval baseline

```bash
make benchmark-fixed-retrieval
```

Equivalent command:

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_retrieval --fixed-route-mode retrieval
```

### Fixed general baseline

```bash
make benchmark-fixed-general
```

Equivalent command:

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_general --fixed-route-mode general
```

### Legacy benchmark command

```bash
make benchmark
```

## 9. Personalization Workflow

### Place source files

Put tenant-specific source files in:

```text
personalization/data/<tenant_id>/files/
```

### Run the pipeline

```bash
docker compose exec dev python pipeline1/run_pipeline1.py --tenant-id default
docker compose exec dev python personalization/clean_dataset.py --tenant-id default
docker compose exec dev python pipeline2/train_lora.py --tenant-id default
docker compose exec dev python pipeline3/test_lora.py --tenant-id default --prompt "Chính sách nghỉ phép của công ty là gì?"
```

### Important note

The LoRA pipeline is available and adapter state is now exposed in runtime metadata.  
However, full LoRA serving integration into the main shared-model runtime is still an active development item under Checklist 1.

## 10. Working Across Multiple Machines

This project is intended to be portable across development machines.

Recommended transfer workflow:

1. clone or copy the repository
2. copy `.env.example` to `.env`
3. run `make bootstrap`
4. verify `/health` and `/status`
5. run adaptive benchmark

See:

- [docs/MOVE_TO_NEW_MACHINE.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/MOVE%20TO%20NEW%20MACHINE.md)

## 11. Important Docs

Read these files in order:

1. [docs/Yeu cau va Muc dich paper.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/Yeu%20cau%20va%20Muc%20dich%20paper.md)
2. [docs/CHECKLIST.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/CHECKLIST.md)
3. [docs/Huong sua Abstract va Introduction.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/Huong%20sua%20Abstract%20va%20Introduction.md)
4. [docs/SETUP_AND_DEV_GUIDE.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/SETUP_AND_DEV_GUIDE.md)
5. [docs/MOVE_TO_NEW_MACHINE.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/MOVE%20TO%20NEW%20MACHINE.md)

## 12. Current Status

The project already has:

- multi-path workflow structure
- tenant-aware runtime
- route telemetry
- fixed-route benchmark support
- Docker-first workflow
- tenant-specific personalization workspace

Still in progress:

- full LoRA serving integration into the main runtime
- stronger tenant isolation validation
- expanded benchmark and ablation coverage
- systems-level performance reporting

## 13. Short Summary

This repository should be understood as:

- not just a chatbot implementation
- not just a RAG prototype
- but a research system for adaptive multi-path, multi-tenant LLM serving with shared models and LoRA-based personalization
