# Yeu cau va Muc dich paper

Tài liệu này gộp lại toàn bộ phần giải thích về:

- mục đích thật sự của project
- điểm mới tiềm năng của paper
- cách định vị bài theo hướng systems-and-application
- những gì cần cải thiện trong source code để tăng độ phù hợp khi nhắm tới journal

Mục tiêu của file này là giúp nhóm không bị lẫn giữa:

- "mình đang làm một chatbot chạy được"
- và "mình đang xây một research system đủ chặt để viết journal paper"

## 1. Project này thực chất đang làm gì

Theo tiêu đề đề tài:

`Adaptive Multi-Path Inference for Multi-Tenant LLM Systems with Shared Models and LoRA-based Personalization`

project này không chỉ là một chatbot RAG thông thường.

Về bản chất, đây là một hệ thống LLM đa tenant, trong đó:

- nhiều tenant cùng dùng chung một base model để tiết kiệm tài nguyên
- mỗi tenant vẫn có thể có hành vi riêng thông qua LoRA-based personalization
- hệ thống không dùng một đường suy luận duy nhất, mà chọn giữa nhiều path khác nhau như:
  - `tool`
  - `retrieval`
  - `general`
- hệ thống cần cân bằng giữa:
  - chất lượng câu trả lời
  - độ trễ
  - chi phí tài nguyên
  - tenant isolation

Nói ngắn gọn:

đây là một bài toán về kiến trúc hệ thống LLM đa tenant có cá nhân hóa và có cơ chế chọn đường suy luận phù hợp theo truy vấn.

## 2. Mục tiêu nghiên cứu nên được hiểu như thế nào

Nếu viết paper theo hướng mạnh nhất, mục tiêu nghiên cứu của đề tài nên được hiểu là:

1. Xây dựng một kiến trúc multi-tenant LLM phục vụ nhiều người dùng/đơn vị trên cùng shared base model.
2. Dùng LoRA để cá nhân hóa theo tenant mà không phải nhân bản full model cho từng tenant.
3. Dùng adaptive multi-path inference để chọn đường xử lý phù hợp với từng loại query.
4. Chứng minh rằng kiến trúc này vừa hiệu quả tài nguyên vừa giữ được chất lượng trả lời và cách ly tenant.

Tức là paper không nên chỉ dừng ở:

- "chúng tôi có một chatbot"
- hoặc "chúng tôi có một pipeline RAG có thêm LoRA"

Mà nên đi đến:

- "chúng tôi đề xuất một kiến trúc hệ thống"
- "kiến trúc đó giải quyết trade-off giữa efficiency, personalization, và isolation"
- "kiến trúc đó được kiểm chứng bằng benchmark định lượng"

## 3. Định vị paper: systems-and-application

Định vị phù hợp nhất cho paper này không phải là:

- pure model paper
- pure LoRA algorithm paper
- pure retrieval paper

Mà nên là:

**systems-and-application paper**

Hoặc nói rõ hơn:

**a systems-and-application paper on multi-tenant LLM serving with adaptive inference and LoRA-based personalization**

Lý do:

- bạn không đề xuất một biến thể LoRA mới ở mức thuật toán nền tảng
- bạn không phát minh một embedding model mới
- bạn không phát minh một retriever hoàn toàn mới
- điểm mạnh của bạn nằm ở cách ghép các thành phần thành một hệ thống hoàn chỉnh có ý nghĩa thực tế

Nếu định vị đúng, bài của bạn sẽ xoay quanh:

- system architecture
- routing policy / inference policy
- multi-tenant resource sharing
- tenant personalization
- tenant isolation
- latency / memory / throughput / quality trade-off
- application thực tế trong môi trường tổ chức nhiều tenant

Đây là hướng hợp lý hơn với một journal thiên về ứng dụng AI trong bài toán engineering thực tế.

## 4. Điểm mới tiềm năng của project này

Điểm mới của bạn không nên được phát biểu kiểu:

- "chúng tôi dùng LoRA"
- "chúng tôi dùng RAG"
- "chúng tôi có router"

Vì từng phần riêng lẻ đó đều đã có nhiều paper làm trước.

Điểm mới nên được phát biểu ở mức hệ thống:

### 4.1. Kết hợp shared model và tenant-specific personalization

Nhiều hệ thống multi-tenant gặp trade-off:

- nếu mỗi tenant dùng model riêng thì tốn tài nguyên
- nếu tất cả dùng chung một model thì mất tính cá nhân hóa

Điểm mạnh của đề tài là:

- giữ shared base model để tiết kiệm tài nguyên
- dùng LoRA adapter để thêm hành vi riêng cho từng tenant

### 4.2. Adaptive multi-path inference thay vì one-path-fits-all

Nhiều hệ thống dùng một pipeline cố định cho mọi truy vấn.

Trong khi đó, đề tài của bạn đi theo hướng:

- query nào cần tool thì đi tool path
- query nào cần tài liệu nội bộ thì đi retrieval path
- query nào mang tính general thì đi general path

Nếu làm chặt hơn, đây sẽ là điểm rất đáng nói:

- hệ thống không chỉ "trả lời"
- mà còn "quyết định cách trả lời"

### 4.3. Tối ưu đồng thời quality và system efficiency

Nếu paper chứng minh được bằng benchmark, novelty mạnh sẽ nằm ở chỗ:

- không chỉ tăng answer quality
- mà còn giảm chi phí phục vụ nhờ shared serving
- vẫn giữ tenant-specific behavior
- vẫn giữ tenant isolation

### 4.4. Bài toán engineering thực tế

Project hiện đang gần với một application thực tế kiểu:

- trợ lý tài liệu nội bộ
- trợ lý học vụ / quy chế / biểu mẫu
- hệ thống hỏi đáp đa tenant trong tổ chức

Nếu viết tốt, đây là lợi thế với journal:

- novelty ở mức system design
- relevance ở mức application

## 5. Project này khác gì so với nhiều paper khác

Một cách đơn giản, bạn có thể hình dung mặt bằng paper liên quan thường rơi vào các nhóm sau:

### 5.1. Nhóm paper chỉ tập trung vào personalization / PEFT / LoRA

Các paper này chủ yếu trả lời:

- làm sao fine-tune rẻ hơn
- làm sao adapter gọn hơn
- làm sao chia sẻ tốt hơn giữa các task

Chúng không nhất thiết giải bài toán multi-tenant serving hoàn chỉnh.

### 5.2. Nhóm paper chỉ tập trung vào multi-tenant serving

Các paper này chủ yếu trả lời:

- làm sao serve nhiều adapter
- làm sao giảm memory footprint
- làm sao scheduling hiệu quả

Chúng không nhất thiết quan tâm đến retrieval, tool path, hoặc application-level routing.

### 5.3. Nhóm paper chỉ tập trung vào RAG / retrieval optimization

Các paper này tối ưu:

- retriever
- reranker
- query expansion
- grounding

Nhưng không đặt retrieval vào một kiến trúc multi-tenant có personalization rõ ràng.

### 5.4. Nhóm paper về routing / adaptive inference

Các paper này quan tâm:

- khi nào dùng model nhỏ
- khi nào dùng model lớn
- khi nào gọi tool
- khi nào đi retrieval

Nhưng thường không đồng thời xử lý:

- tenant isolation
- shared model efficiency
- LoRA personalization

### 5.5. Điểm khác biệt mong muốn của bài này

Nếu viết đúng, bài của bạn nổi bật ở chỗ:

- không tối ưu một module đơn lẻ
- mà đề xuất một hệ thống hoàn chỉnh
- tích hợp shared serving, adaptive path selection, retrieval, tool usage, và LoRA personalization trong bối cảnh multi-tenant

Nói ngắn gọn:

**điểm khác biệt nằm ở sự phối hợp giữa các thành phần trong một kiến trúc phục vụ thực tế**

## 6. Điểm mạnh hiện tại của repo

Repo hiện đã có một số tín hiệu tốt cho hướng systems paper:

- có workflow phân nhánh `tool / retrieval / general`
- có runtime manager cho index và storage theo tenant
- có benchmark retrieval và answer evaluation
- có workspace cho personalization theo tenant
- có Docker, Makefile, và launcher
- có ý thức khá rõ về benchmark, tuning, và artifacts

Điều này cho thấy project đã vượt qua mức prototype rất sơ khai.

## 7. Điểm yếu hiện tại làm novelty chưa đủ mạnh

Đây là phần rất quan trọng.

Ý tưởng paper của bạn có tiềm năng tốt, nhưng novelty ở mức paper claim hiện vẫn chưa đủ mạnh nếu nhìn từ source code hiện tại.

### 7.1. Adaptive multi-path hiện còn gần heuristic routing

Hiện router chủ yếu dựa trên:

- keyword
- file hint
- rule-based pattern

Điều này có nghĩa là reviewer có thể hỏi:

- adaptive ở đâu ngoài heuristic?
- policy chọn path được học hay được tối ưu như thế nào?
- có cost-quality trade-off thật sự không?

Nếu không trả lời được, chữ "Adaptive Multi-Path Inference" sẽ bị xem là hơi over-claim.

### 7.2. LoRA chưa gắn chặt vào runtime chính

Repo đã có pipeline train và smoke-test LoRA, nhưng nếu adapter vẫn đứng tách khỏi luồng trả lời chính thì reviewer sẽ hỏi:

- personalization có tác động trực tiếp lên serving path không?
- shared model + LoRA có thực sự là cơ chế vận hành chính hay chỉ là prototype phụ?

Nếu chưa nối được, claim "LoRA-based Personalization" sẽ yếu đi.

### 7.3. Benchmark vẫn còn nhỏ và dễ

Bộ test hiện tại chưa đủ mạnh để chứng minh một systems paper cấp journal:

- số lượng case còn ít
- lệch nhiều về easy cases
- hard cases rất ít
- chưa thấy benchmark adversarial hoặc cross-tenant leakage đủ mạnh

### 7.4. Chưa chứng minh isolation và efficiency một cách định lượng đủ mạnh

Với đề tài multi-tenant, reviewer thường rất quan tâm:

- tenant isolation có chắc không
- latency tăng thế nào khi số tenant tăng
- memory tiết kiệm được bao nhiêu so với per-tenant model
- personalization đổi được gì về quality

Nếu không có bảng số liệu rõ ràng, novelty hệ thống sẽ bị yếu.

## 8. Tôi nên hiểu paper này là gì trong một câu

Nếu cần một câu ngắn để tự nhắc mình khi sửa paper, bạn có thể dùng:

**Đây là một systems-and-application paper đề xuất kiến trúc LLM đa tenant dùng shared base model, adaptive multi-path inference, và LoRA-based personalization để tối ưu đồng thời tài nguyên, chất lượng trả lời, và tenant isolation.**

## 9. Source code cần cải thiện những gì để khớp với paper

Phần này là checklist hành động trực tiếp cho repo.

### 9.1. Ưu tiên 1: làm rõ adaptive inference

Cần bổ sung:

- routing policy rõ ràng hơn keyword heuristic
- confidence score hoặc utility score cho từng path
- log quyết định route
- benchmark so sánh:
  - fixed retrieval path
  - fixed general path
  - fixed tool path
  - adaptive path
- phân tích trade-off giữa latency, cost, quality

Mục tiêu:

biến "adaptive" thành một cơ chế có thể đo, thay vì chỉ là một rule router.

### 9.2. Ưu tiên 2: tích hợp LoRA vào runtime thật

Cần làm:

- load adapter theo tenant trong runtime chính
- định nghĩa rõ khi nào route dùng shared base model thuần, khi nào dùng adapter
- benchmark trước và sau personalization
- chứng minh LoRA có cải thiện thật trên tenant-specific queries

Mục tiêu:

biến LoRA từ pipeline phụ thành thành phần cốt lõi của hệ thống.

### 9.3. Ưu tiên 3: nâng benchmark lên mức journal

Cần làm:

- tăng số lượng test cases
- tăng hard cases
- thêm cross-tenant leakage tests
- thêm out-of-distribution cases
- thêm ablation study
- thêm answer-level evaluation rõ ràng

Mục tiêu:

chứng minh được contribution bằng benchmark nghiêm túc.

### 9.4. Ưu tiên 4: chứng minh system efficiency

Cần đo:

- latency theo từng path
- latency theo số tenant
- RAM / GPU usage
- throughput
- chi phí shared model so với per-tenant model
- ảnh hưởng của LoRA loading / switching

Mục tiêu:

để bài thực sự là systems paper chứ không chỉ là application demo.

### 9.5. Ưu tiên 5: chứng minh tenant isolation

Cần có:

- test retrieval đúng tenant
- test memory isolation
- test query chéo tenant
- test nguồn tài liệu không bị lẫn
- báo cáo leakage rate nếu có

Mục tiêu:

đưa tenant isolation thành contribution có thể kiểm chứng.

### 9.6. Ưu tiên 6: chuẩn hóa repo để tái lập

Cần cải thiện:

- thêm `README.md` gốc cho repo
- bỏ hoặc tách `venv`, `__pycache__`, runtime artifacts khỏi phần research code
- dùng đường dẫn tương đối thay vì đường dẫn tuyệt đối theo máy cá nhân
- chuẩn hóa cấu trúc `src / data / artifacts / reports / scripts`
- viết quy trình chạy lại benchmark từ đầu
- nếu có thể, chuẩn bị public hoặc sanitized dataset để người khác tái lập

Mục tiêu:

đưa repo từ "code đang dùng nội bộ" thành "research artifact có thể chia sẻ".

## 10. Những câu reviewer rất có thể sẽ hỏi

Bạn nên tự chuẩn bị trước cho các câu này:

1. Novelty chính xác của bài là gì ngoài việc ghép RAG, routing, và LoRA?
2. Adaptive path được quyết định theo cơ chế nào?
3. So với một fixed pipeline mạnh, adaptive path hơn ở điểm nào?
4. LoRA personalization có thật sự được dùng trong runtime chính không?
5. Shared model tiết kiệm được bao nhiêu tài nguyên?
6. Tenant isolation được kiểm chứng ra sao?
7. Benchmark có đủ lớn và đủ khó chưa?
8. Người khác có thể tái lập hệ thống trên dữ liệu công khai hoặc dữ liệu đã được làm sạch không?

Nếu paper và source code trả lời tốt 8 câu này, cơ hội của bài sẽ tốt hơn nhiều.

## 11. Kết luận ngắn

Nếu phải chốt lại trong vài dòng:

- Project này có hướng đi đúng cho một systems-and-application paper.
- Điểm mới mạnh nhất nằm ở kiến trúc kết hợp shared serving, adaptive multi-path inference, và LoRA personalization trong môi trường multi-tenant.
- Điểm yếu lớn nhất hiện tại là novelty mới mạnh ở mức ý tưởng hệ thống, nhưng còn cần benchmark, integration, và evidence định lượng để đủ sức thuyết phục reviewer journal.

## 12. Việc nên làm tiếp ngay

Nếu cần ưu tiên ngắn gọn, nên tập trung theo thứ tự:

1. Tích hợp LoRA vào runtime chính.
2. Nâng adaptive routing từ heuristic thành policy có log và benchmark.
3. Mở rộng benchmark và thêm cross-tenant isolation tests.
4. Đo latency, memory, throughput theo số tenant.
5. Làm sạch repo và chuẩn hóa tái lập.

Khi làm xong 5 việc này, paper sẽ được nâng rõ rệt cả ở:

- scientific contribution
- engineering credibility
- journal readiness

## 13. Bảng phân loại theo mức độ can thiệp

Bảng này giúp trả lời câu hỏi thực tế:

- phần nào giữ nguyên được
- phần nào chỉ cần sửa nhẹ
- phần nào phải nâng cấp mạnh để khớp claim của paper
- phần nào chưa cần ưu tiên ngay

| Thành phần | Trạng thái đề xuất | Lý do | Hành động ngắn gọn |
| --- | --- | --- | --- |
| Kiến trúc multi-tenant tổng thể | Giữ nguyên | Hướng đi đúng với đề tài, đã có tenant-aware runtime, storage, memory, config | Giữ khung chính, chỉ làm rõ hơn trong paper và docs |
| Ý tưởng shared base model + personalization | Giữ nguyên | Đây là trục đóng góp hợp lý nhất của paper | Giữ narrative này làm trục chính |
| Workflow đa path `tool / retrieval / general` | Giữ nguyên | Đây là xương sống rất đúng cho định vị systems-and-application | Không bỏ, chỉ nâng cấp cơ chế chọn path |
| Runtime manager theo tenant | Giữ nguyên | Đã có nền tảng tốt cho systems paper | Giữ cấu trúc, bổ sung logging và benchmark |
| Retrieval evaluation framework | Giữ nguyên | Đã có metric và khung benchmark tương đối tốt | Tiếp tục dùng làm nền, mở rộng dataset và ablation |
| Docker / launcher / Makefile | Giữ nguyên | Hữu ích cho reproducibility và dev flow | Giữ, chỉ dọn docs và câu lệnh |
| Router heuristic hiện tại | Sửa nhẹ | Khung router đúng, nhưng logic chọn route còn khá rule-based | Bổ sung confidence score, logging, route rationale chuẩn hóa |
| Docs setup và mô tả dự án | Sửa nhẹ | Đã có nhưng còn thiên về nội bộ dev, chưa tối ưu cho journal artifact | Viết lại theo hướng research artifact và reproducibility |
| Cấu trúc benchmark dataset hiện tại | Sửa nhẹ | Có form tốt, có tenant/category/difficulty, nhưng số lượng và độ khó chưa đủ | Mở rộng bộ test, thêm hard/adversarial/cross-tenant cases |
| Logging tài nguyên và latency | Sửa nhẹ | Nền đo thời gian/RAM đã có mầm trong runtime | Chuẩn hóa log thành artifact và bảng so sánh cho paper |
| Repo layout hiện tại | Sửa nhẹ | Dùng được để dev, nhưng còn lẫn artifacts và đường dẫn máy cá nhân | Dọn lại folder, tách artifacts, sửa absolute paths |
| LoRA pipeline train/test riêng | Sửa nhẹ | Pipeline đã có, không cần bỏ | Giữ pipeline, nhưng biến nó thành một phần của runtime chính |
| Adaptive inference claim | Phải nâng cấp mạnh | Hiện novelty này mới mạnh ở mức ý tưởng, chưa đủ evidence | Chuyển từ heuristic sang policy có benchmark, ablation, cost-quality analysis |
| LoRA integration vào serving runtime | Phải nâng cấp mạnh | Đây là chỗ dễ bị reviewer hỏi nhất nếu chưa nối vào luồng trả lời chính | Load adapter theo tenant trong runtime thật, benchmark before/after |
| Tenant isolation validation | Phải nâng cấp mạnh | Multi-tenant paper mà không có evidence isolation sẽ rất yếu | Viết test leakage, cross-tenant retrieval, memory isolation |
| Efficiency benchmark theo số tenant | Phải nâng cấp mạnh | Đây là phần chứng minh systems value | Đo latency, RAM/GPU, throughput, cost khi số tenant tăng |
| So sánh với fixed pipeline / baseline mạnh | Phải nâng cấp mạnh | Nếu không có baseline tốt thì adaptive claim yếu | Thêm ablation và baseline rõ ràng |
| Public hoặc sanitized reproducible dataset | Phải nâng cấp mạnh | Journal rất quan tâm tính tái lập | Chuẩn bị data package hoặc script build dữ liệu có thể chia sẻ |
| Viết model mới từ đầu | Chưa cần làm | Không phải trục mạnh nhất của paper | Không ưu tiên |
| Phát minh thuật toán LoRA mới | Chưa cần làm | Dễ lệch khỏi định vị systems-and-application | Không ưu tiên nếu mục tiêu là journal hiện tại |
| Thay toàn bộ framework bằng framework khác | Chưa cần làm | Bộ khung hiện tại đã đủ tốt để phát triển tiếp | Tập trung nâng cấp, không phá đi làm lại |
| Tối ưu UI demo quá nhiều | Chưa cần làm | Không phải phần quyết định novelty học thuật | Chỉ giữ đủ ổn để demo |

## 14. Tóm tắt rất ngắn theo 4 mức

### Giữ nguyên

- kiến trúc multi-tenant tổng thể
- shared model + personalization narrative
- workflow đa path
- runtime manager
- evaluation framework cơ bản
- Docker / launcher / Makefile

### Sửa nhẹ

- router heuristic
- docs và repo layout
- benchmark dataset
- logging tài nguyên
- LoRA pipeline hiện có

### Phải nâng cấp mạnh

- adaptive inference thành policy có chứng minh
- LoRA integration vào runtime chính
- tenant isolation validation
- efficiency benchmark theo số tenant
- baseline và ablation
- reproducible/public dataset

### Chưa cần làm

- model mới từ đầu
- thuật toán LoRA mới
- thay framework
- đầu tư mạnh vào UI

## 15. Cách đọc bảng này để đỡ bị quá tải

Nếu bạn bị cảm giác có quá nhiều việc, hãy đọc bảng theo cách sau:

1. Những mục "Giữ nguyên" là phần chứng minh rằng framework của bạn đã có nền tốt.
2. Những mục "Sửa nhẹ" là phần nên làm sớm vì chi phí không quá lớn nhưng tăng độ chuyên nghiệp rõ.
3. Những mục "Phải nâng cấp mạnh" là phần quyết định bài có đủ lực journal hay không.
4. Những mục "Chưa cần làm" là các việc dễ tốn thời gian nhưng không làm tăng cơ hội accept tương xứng ở giai đoạn này.
