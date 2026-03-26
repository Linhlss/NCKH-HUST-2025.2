from segment import load_documents, segment_documents
from qa_generator import generate_dataset, save_dataset
from export_dataset import export_lora_format

DATA_PATH = "data/files"

def run():
    print("1. Loading documents...")
    docs = load_documents(DATA_PATH)

    print("2. Segmenting...")
    chunks = segment_documents(docs)

    print(f"Chunks created: {len(chunks)}")

    print("3. Generating QA...")
    dataset = generate_dataset(chunks)

    save_dataset(dataset, "pipeline1/generated_qa.json")

    print("4. Exporting LoRA dataset...")
    export_lora_format(
        "pipeline1/generated_qa.json",
        "pipeline1/lora_dataset.json"
    )

    print("DONE!")

if __name__ == "__main__":
    run()