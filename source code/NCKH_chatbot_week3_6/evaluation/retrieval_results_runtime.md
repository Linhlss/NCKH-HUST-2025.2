# Retrieval Evaluation

Báo cáo này được sinh tự động từ `evaluation/evaluate_retrieval.py`.
Các biến thể hiện tại nhằm so sánh baseline dense retrieval, hậu xử lý file hint, và runtime optimization thật.

| Variant | Count | Hit@1 | Hit@3 | Hit@5 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dense_raw | 36 | 0.278 | 0.472 | 0.611 | 0.399 | 0.759 | 2.56 |
| dense_prioritized | 36 | 0.167 | 0.444 | 0.611 | 0.321 | 0.759 | 2.25 |
| runtime_profile | 36 | 0.306 | 0.611 | 0.806 | 0.497 | 0.759 | 6.49 |

## Variant: `dense_raw`

- Retrieval set: 36 câu hỏi có ground truth nguồn.
- Route accuracy: 0.759 | Avg route latency: 352.99 ms
- Route distribution: {"retrieval": 41, "tool": 13}

| Category | Count | Hit@3 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- |
| regulation_2021 | 18 | 0.500 | 0.497 | 0.889 | 2.53 |
| regulation_2025 | 18 | 0.444 | 0.301 | 0.889 | 2.59 |
| timetable_20252 | 0 | 0.000 | 0.000 | 0.500 | 0.00 |

| Difficulty | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| easy | 23 | 0.391 | 0.317 | 0.778 |
| hard | 2 | 0.500 | 0.500 | 0.500 |
| medium | 11 | 0.636 | 0.553 | 0.750 |

| Tenant | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| 01 | 18 | 0.500 | 0.497 | 0.889 |
| default | 0 | 0.000 | 0.000 | 0.500 |
| t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf | 18 | 0.444 | 0.301 | 0.889 |

### Hard Cases
- `R2025-07` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2021-04` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT_2025_5445_QD-DHBK.pdf']
- `R2025-03` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2025-09` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2025-14` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']

## Variant: `dense_prioritized`

- Retrieval set: 36 câu hỏi có ground truth nguồn.
- Route accuracy: 0.759 | Avg route latency: 351.62 ms
- Route distribution: {"retrieval": 41, "tool": 13}

| Category | Count | Hit@3 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- |
| regulation_2021 | 18 | 0.611 | 0.386 | 0.889 | 2.07 |
| regulation_2025 | 18 | 0.278 | 0.257 | 0.889 | 2.43 |
| timetable_20252 | 0 | 0.000 | 0.000 | 0.500 | 0.00 |

| Difficulty | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| easy | 23 | 0.478 | 0.297 | 0.778 |
| hard | 2 | 0.500 | 0.167 | 0.500 |
| medium | 11 | 0.364 | 0.400 | 0.750 |

| Tenant | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| 01 | 18 | 0.611 | 0.386 | 0.889 |
| default | 0 | 0.000 | 0.000 | 0.500 |
| t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf | 18 | 0.278 | 0.257 | 0.889 |

### Hard Cases
- `R2025-03` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2025-07` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf']
- `R2025-16` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2021-16` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- `R2025-15` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']

## Variant: `runtime_profile`

- Retrieval set: 36 câu hỏi có ground truth nguồn.
- Route accuracy: 0.759 | Avg route latency: 363.89 ms
- Route distribution: {"retrieval": 41, "tool": 13}

| Category | Count | Hit@3 | MRR | Route Acc. | Avg Retrieval Latency (ms) |
| --- | --- | --- | --- | --- | --- |
| regulation_2021 | 18 | 0.667 | 0.481 | 0.889 | 6.02 |
| regulation_2025 | 18 | 0.556 | 0.513 | 0.889 | 6.96 |
| timetable_20252 | 0 | 0.000 | 0.000 | 0.500 | 0.00 |

| Difficulty | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| easy | 23 | 0.652 | 0.496 | 0.778 |
| hard | 2 | 0.000 | 0.171 | 0.500 |
| medium | 11 | 0.636 | 0.558 | 0.750 |

| Tenant | Count | Hit@3 | MRR | Route Acc. |
| --- | --- | --- | --- | --- |
| 01 | 18 | 0.667 | 0.481 | 0.889 |
| default | 0 | 0.000 | 0.000 | 0.500 |
| t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf | 18 | 0.556 | 0.513 | 0.889 |

### Hard Cases
- `R2021-18` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- `R2025-07` | route `tool` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2025-11` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- `R2021-07` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- `R2025-17` | route `retrieval` vs `retrieval` | Hit@3=0 | top sources=['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
