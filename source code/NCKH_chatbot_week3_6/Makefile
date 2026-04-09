COMPOSE ?= docker compose

.PHONY: dev-build dev-up dev-shell app-up app-down logs ps bootstrap benchmark benchmark-adaptive benchmark-fixed-retrieval benchmark-fixed-general lora-train lora-test

dev-build:
	$(COMPOSE) build dev

dev-up:
	$(COMPOSE) up -d dev

dev-shell:
	$(COMPOSE) exec dev bash

app-up:
	$(COMPOSE) up -d api ui

app-down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

bootstrap: dev-build dev-up app-up

logs:
	$(COMPOSE) logs -f api ui

benchmark:
	$(COMPOSE) exec dev python run_me.py benchmark --setup none --dataset evaluation/test_queries.json

benchmark-adaptive:
	$(COMPOSE) exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label adaptive_baseline

benchmark-fixed-retrieval:
	$(COMPOSE) exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_retrieval --fixed-route-mode retrieval

benchmark-fixed-general:
	$(COMPOSE) exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_general --fixed-route-mode general

lora-train:
	$(COMPOSE) exec dev python pipeline2/train_lora.py --tenant-id default

lora-test:
	$(COMPOSE) exec dev python pipeline3/test_lora.py --tenant-id default --prompt "Chính sách nghỉ phép của công ty là gì?"
