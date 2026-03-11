# Hoan tat tuan 1 - handoff cho Duong

## Muc tieu da chot
- Bot doc duoc tai lieu PDF/XLSX/TXT/MD tu thu muc `data/files`
- Chunking va lap chi muc bang ChromaDB
- Tra loi duoc cau hoi dua tren ngu canh truy xuat
- Co memory hoi thoai co ban
- Co launcher `run_me.py` de cai dat va chay

## Loi da sua
1. **Sua `project_root/memory_store.py`**
   - File bi ghi de sai noi dung
   - Da khoi phuc class `MemoryStore`

2. **Sua `project_root/config.py`**
   - Duong dan du lieu, storage, memory, config truoc do tro sai vao `project_root/...`
   - Da chinh de tro dung ve thu muc goc cua project

3. **Sua `run_me.py`**
   - Da uu tien chay `project_root/main.py`
   - Da kiem tra day du bo file modular
   - Van fallback duoc neu sau nay can giu `app.py`

4. **Don dep cau truc de demo tuan 1**
   - Giu module code trong `project_root/`
   - Giu du lieu that trong `data/`
   - Giu vector db trong `storage/`
   - Giu lich su hoi thoai trong `memory/`

## Cach chay
```bash
python run_me.py
```
Hoac neu da co virtualenv va da cai thu vien:
```bash
python project_root/main.py
```

## Kiem tra nhanh sau khi chay
- `/status`
- `/listdocs`
- hoi 1 cau lien quan toi cac file trong `data/files`

## Ban giao cho Duong
Duong co the bat dau tuan 2 tren nen tang nay:
1. Chot base model de fine-tune (Qwen/Mistral/Llama qua Ollama hoac Colab)
2. Tao dataset style/instruction cho LoRA
3. Train adapter LoRA dau tien
4. So sanh model goc va model sau LoRA
5. Chuan bi quy uoc adapter theo tenant
