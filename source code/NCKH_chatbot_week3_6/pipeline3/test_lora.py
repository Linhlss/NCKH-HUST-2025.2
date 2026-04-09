from __future__ import annotations

import argparse

from lora_loader import load_model_with_lora


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test a tenant LoRA adapter.")
    parser.add_argument("--tenant-id", default="default")
    parser.add_argument("--prompt", default="Chính sách nghỉ phép của công ty là gì?")
    parser.add_argument("--max-new-tokens", type=int, default=50)
    args = parser.parse_args()

    model, tokenizer = load_model_with_lora(args.tenant_id)
    inputs = tokenizer(args.prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=args.max_new_tokens)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(f"Tenant: {args.tenant_id}")
    print(f"Prompt: {args.prompt}")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
