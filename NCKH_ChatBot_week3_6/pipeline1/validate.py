import json

def validate_dataset(input_path, output_path):
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    validated = []

    for item in data:
        print("\n----------------------")
        print("Q:", item["question"])
        print("A:", item["answer"])

        ok = input("Keep? (y/n): ")

        if ok.lower() == "y":
            validated.append(item)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validated, f, ensure_ascii=False, indent=2)