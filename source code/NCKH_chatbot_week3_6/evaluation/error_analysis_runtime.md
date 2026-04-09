# Error Analysis

Tài liệu này được sinh tự động từ các truy vấn thất bại trong benchmark retrieval.

## Variant: `dense_raw`

- missed_relevant_source: 10
- route_mismatch: 3
- top1_wrong_source: 5

### R2025-07
- Query: Mục lục của quy chế đào tạo 2025 có Điều 9 về nội dung gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2021-04
- Query: Điều 9 của QCDT 2021 nói về nội dung gì?
- Tenant: `01` | Category: `regulation_2021` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT-2021-upload.pdf']
- Top retrieved: ['', '', 'QCDT_2025_5445_QD-DHBK.pdf']
- Notes: Không có ghi chú.

### R2025-03
- Query: Điều 1 của quy chế đào tạo 2025 nói về nội dung gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2025-09
- Query: QCDT 2025 có chương nào về đào tạo đại học không?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2025-14
- Query: Trong QCDT 2025, Điều 8 nói về việc gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `medium`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

## Variant: `dense_prioritized`

- missed_relevant_source: 10
- route_mismatch: 2
- top1_wrong_source: 9

### R2025-03
- Query: Điều 1 của quy chế đào tạo 2025 nói về nội dung gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2025-07
- Query: Mục lục của quy chế đào tạo 2025 có Điều 9 về nội dung gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['', 'QCDT-2021-upload.pdf', '']
- Notes: Không có ghi chú.

### R2025-16
- Query: Trong phần ký văn bản của QCDT 2025, người ký với chức vụ gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `hard`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', '', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2021-16
- Query: Trong QCDT 2021, Điều 20 nói về việc xử lý vi phạm đối với ai?
- Tenant: `01` | Category: `regulation_2021` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT-2021-upload.pdf']
- Top retrieved: ['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- Notes: Không có ghi chú.

### R2025-15
- Query: Quy chế đào tạo 2025 được giới thiệu là ban hành kèm theo quyết định của ai?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `medium`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

## Variant: `runtime_profile`

- missed_relevant_source: 10
- route_mismatch: 2
- top1_wrong_source: 9

### R2021-18
- Query: Điều 21 trong QCDT 2021 thuộc chương nào và nói về nội dung gì?
- Tenant: `01` | Category: `regulation_2021` | Difficulty: `hard`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT-2021-upload.pdf']
- Top retrieved: ['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- Notes: Không có ghi chú.

### R2025-07
- Query: Mục lục của quy chế đào tạo 2025 có Điều 9 về nội dung gì?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `tool`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2025-11
- Query: QCDT 2025 có Điều 4 về tín chỉ và học phần đúng không?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.

### R2021-07
- Query: QCDT 2021 có Điều 11 về nội dung nào?
- Tenant: `01` | Category: `regulation_2021` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT-2021-upload.pdf']
- Top retrieved: ['QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf', 'QCDT_2025_5445_QD-DHBK.pdf']
- Notes: Không có ghi chú.

### R2025-17
- Query: Quy chế đào tạo 2025 có phạm vi điều chỉnh và đối tượng áp dụng ở điều nào?
- Tenant: `t_m_t_t_file_qcdt_2025_5445_qd-dhbk_pdf` | Category: `regulation_2025` | Difficulty: `easy`
- Expected route: `retrieval` | Predicted route: `retrieval`
- Relevant sources: ['QCDT_2025_5445_QD-DHBK.pdf']
- Top retrieved: ['QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf', 'QCDT-2021-upload.pdf']
- Notes: Không có ghi chú.
