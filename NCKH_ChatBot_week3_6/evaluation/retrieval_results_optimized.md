# Retrieval Evaluation

Báo cáo này được sinh tự động từ `evaluation/evaluate_retrieval.py`.
Các biến thể hiện tại nhằm so sánh baseline dense retrieval, hậu xử lý file hint, và runtime optimization thật.

| Variant | Count | Hit@1 | Hit@3 | Hit@5 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_profile | 36 | 0.861 | 1.000 | 1.000 | 0.921 | 0.759 | 202.38 |

## Variant: `runtime_profile`

- Retrieval set: 36 câu hỏi có ground truth nguồn.
- Route accuracy: 0.759 | Avg route latency: 348.43 ms
- Route distribution: {"retrieval": 41, "tool": 13}

| Category | Count | Hit@3 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- |
| regulation_2021 | 18 | 1.000 | 0.917 | 0.889 | 202.29 |
| regulation_2025 | 18 | 1.000 | 0.926 | 0.889 | 202.47 |
| timetable_20252 | 0 | 0.000 | 0.000 | 0.500 | 0.00 |

| Difficulty | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| easy | 23 | 1.000 | 0.957 | 0.778 |
| hard | 2 | 1.000 | 1.000 | 0.500 |
| medium | 11 | 1.000 | 0.833 | 0.750 |

| Tenant | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| 01 | 18 | 1.000 | 0.917 | 0.889 |
| default | 0 | 0.000 | 0.000 | 0.500 |
| t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf | 18 | 1.000 | 0.926 | 0.889 |

### Hard Cases
- `R2021-18` | route `tool` vs `retrieval` | Hit@3=1 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2025-03` | route `tool` vs `retrieval` | Hit@3=1 | top sources=['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT-2021-upload.pdf']
- `R2025-07` | route `tool` vs `retrieval` | Hit@3=1 | top sources=['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- `R2021-04` | route `tool` vs `retrieval` | Hit@3=1 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
