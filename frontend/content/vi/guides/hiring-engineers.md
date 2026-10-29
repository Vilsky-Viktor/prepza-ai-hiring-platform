---
title: "Cách tuyển kỹ sư phần mềm: quy trình bài bản từ mô tả công việc đến offer"
seoTitle: "Cách tuyển kỹ sư phần mềm: quy trình tuyển dụng bài bản"
description: "Quy trình từng bước tuyển kỹ sư phần mềm: hồ sơ vị trí, sàng lọc CV, bài kiểm tra kiến thức, lập trình, thiết kế hệ thống, phỏng vấn có cấu trúc và offer."
updated: "2026-10-29"
---

# Cách tuyển kỹ sư phần mềm: quy trình bài bản từ mô tả công việc đến offer

Tuyển kỹ sư tốn kém theo một cách dễ bị bỏ qua: phần lớn chi phí là thời gian của chính các kỹ sư của bạn. Mỗi giờ họ ngồi phỏng vấn một người không nắm được stack công nghệ là một giờ họ không dành cho việc xây dựng sản phẩm. Một quy trình tốt đặt các bước kiểm tra rẻ, bao quát lên trước và để dành các bước sâu, tốn kém cho số ít người có nhiều khả năng thành công.

Hướng dẫn này đi qua quy trình đó từng bước. Hướng dẫn dựa trên các nghiên cứu về tuyển dụng ở những chỗ nghiên cứu cho kết luận rõ ràng, và nói rõ ở những chỗ chưa rõ ràng.

## Tổng quan quy trình

| Giai đoạn | Kiểm tra điều gì | Ai bỏ thời gian |
| --- | --- | --- |
| 1. Hồ sơ vị trí và mô tả công việc | Công việc thực sự cần gì | Hiring manager, một kỹ sư senior |
| 2. Sàng lọc CV hoặc hồ sơ ứng tuyển | Chỉ các yêu cầu bắt buộc | Chuyên viên tuyển dụng hoặc hiring manager |
| 3. Bài kiểm tra kiến thức | Ứng viên biết gì về stack của bạn | Ứng viên; bạn chỉ đọc kết quả |
| 4. Bài tập về nhà hoặc lập trình trực tiếp | Họ có viết được code chạy được không | Một hoặc hai kỹ sư |
| 5. Thiết kế hệ thống (vị trí senior) | Cách họ suy luận về hệ thống lớn hơn | Một kỹ sư senior |
| 6. Phỏng vấn hành vi có cấu trúc | Cách họ làm việc với người khác | Hiring manager, một đồng nghiệp ngang cấp |
| 7. Kiểm tra tham chiếu | Xác nhận những gì bạn đã nghe | Hiring manager |
| 8. Quyết định và gửi offer | Một quyết định công bằng, có ghi chép | Nhóm tuyển dụng |

## Nghiên cứu nói gì

Các tổng quan lớn về nghiên cứu tuyển dụng so sánh các phương pháp theo mức độ kết quả của chúng liên quan đến hiệu suất công việc sau này. Tổng quan lớn gần đây nhất, của Sackett, Zhang, Berry và Lievens (2022), đã điều chỉnh giảm các ước tính trước đó và nhận thấy các yếu tố dự báo mạnh nhất, tính trung bình, đều là các phương pháp đo lường gắn với công việc cụ thể ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Các ước tính của họ, trên thang đo mà 0 là không có liên hệ và 1 là liên hệ hoàn hảo:

| Phương pháp | Độ hiệu lực ước tính |
| --- | --- |
| Phỏng vấn có cấu trúc | .42 |
| Bài kiểm tra kiến thức chuyên môn | .40 |
| Bài kiểm tra mẫu công việc | .33 |
| Phỏng vấn không cấu trúc | .19 |
| Số năm kinh nghiệm | .07 |

Từ đó rút ra ba bài học cho việc tuyển kỹ sư:

- **Cấu trúc quan trọng hơn hình thức.** Cùng một buổi phỏng vấn, nếu có bộ câu hỏi cố định và hướng dẫn chấm điểm, sẽ dự báo tốt hơn nhiều so với một cuộc trò chuyện không cấu trúc.
- **Số năm kinh nghiệm tự nó nói lên rất ít.** "Năm năm Java" là một tín hiệu yếu so với những gì một người thực sự biết và làm được.
- **Kết hợp các phương pháp.** Không phương pháp nào đủ mạnh để dùng một mình.

Đây là các con số trung bình trên nhiều công việc và nhiều nghiên cứu, không phải sự bảo đảm cho vị trí của bạn. Các tác giả cũng lưu ý rằng bài kiểm tra kiến thức và mẫu công việc phù hợp với những vị trí mà ứng viên được kỳ vọng đã có đào tạo hoặc kinh nghiệm. Điều đó đúng với phần lớn việc tuyển kỹ sư, nhưng không đúng với vị trí học việc.

## Bước 1: Viết hồ sơ vị trí và mô tả công việc rõ ràng

Trước khi đăng bất cứ thứ gì, hãy ghi ra người được tuyển sẽ làm gì trong sáu tháng đầu và phải biết gì ngay từ ngày đầu tiên. Hãy cụ thể:

- **Phải biết:** "Viết và review truy vấn PostgreSQL, bao gồm join và index" là kiểm tra được. "Kỹ năng cơ sở dữ liệu tốt" thì không.
- **Sẽ học trong lúc làm:** công cụ nội bộ, lĩnh vực nghiệp vụ, những phần của stack mà bạn sẽ đào tạo.
- **Cấp bậc:** trong nhóm của bạn, điều gì phân biệt một người middle với một người senior, chẳng hạn tự chịu trách nhiệm một service từ đầu đến cuối hoặc dẫn dắt các quyết định thiết kế.

Thống nhất điều này với tất cả những người tham gia tuyển dụng. Sau đó viết mô tả công việc dựa trên nó. Một mô tả công việc khớp với công việc thực tế sẽ thu hút đúng người và giúp mọi bước sau dễ thiết lập hơn, vì mỗi bài kiểm tra và mỗi buổi phỏng vấn đều có thể đối chiếu ngược lại với nó.

Giữ phần "ưu tiên" thật ngắn. Danh sách yêu cầu dài khiến những người đủ năng lực nhưng không đáp ứng đủ mọi gạch đầu dòng ngần ngại ứng tuyển.

## Bước 2: Sàng lọc CV chỉ theo yêu cầu bắt buộc

Dùng CV hoặc hồ sơ ứng tuyển cho các kiểm tra có/không: quyền làm việc, địa điểm hoặc múi giờ nếu vị trí yêu cầu, ngoại ngữ bắt buộc, và bất kỳ điều kiện tiên quyết nào mà công việc thực sự không thể thiếu.

Đừng xếp hạng ứng viên theo CV. Chức danh, tên công ty cũ và số năm kinh nghiệm là những yếu tố dự báo yếu, và CV rất khó so sánh công bằng: một CV ấn tượng có thể phản ánh khả năng viết tốt chẳng kém gì phản ánh làm việc tốt. Hãy coi CV là bộ lọc cho những gì không thể kiểm tra, và chuyển tất cả những ai đạt sang bài kiểm tra kiến thức.

## Bước 3: Tổ chức một bài kiểm tra kiến thức ngắn

Đây là bước tiết kiệm nhiều thời gian nhất cho các kỹ sư của bạn. Trước khi bất kỳ ai dành một giờ cho buổi phỏng vấn trực tiếp, hãy kiểm tra mỗi ứng viên biết gì về stack của bạn.

Một bài kiểm tra kiến thức tốt cần:

- **Gắn với công việc:** kiểm tra ngôn ngữ, framework, cơ sở dữ liệu và cách làm việc trong hồ sơ vị trí của bạn, không phải kiến thức đố vui chung chung.
- **Ngắn:** vài chủ đề, mỗi chủ đề khoảng 10 câu hỏi, để các ứng viên giỏi đang có offer khác vẫn làm hết.
- **Giống nhau cho mọi người:** cùng chủ đề, cùng số câu hỏi và cùng giới hạn thời gian.

Đây là chỗ prepza phát huy tác dụng. prepza biến mô tả công việc của bạn thành một buổi phỏng vấn kiến thức trắc nghiệm có tính giờ. Bạn duyệt các chủ đề được đề xuất trước khi bất kỳ câu hỏi nào được viết, nên bài kiểm tra chỉ bao quát stack của bạn. Với vị trí kỹ thuật, bài kiểm tra có thể gồm:

- **Câu hỏi đọc code:** một đoạn code ngắn kèm câu hỏi nó in ra hoặc trả về gì, nó làm gì, vì sao nó lỗi, hoặc thay đổi nào sửa được nó.
- **SQL:** một bảng nhỏ và một truy vấn, kèm câu hỏi những dòng nào được trả về.
- **Kiến thức kiến trúc và framework:** các đánh đổi, cách một framework hoạt động, điều gì hỏng khi tải cao.

Mỗi ứng viên nhận bộ câu hỏi ngẫu nhiên của riêng mình, mỗi câu có đồng hồ đếm ngược. Bạn xem một bảng điểm với từng câu trả lời và thời gian trả lời, cùng các cảnh báo về trả lời quá nhanh, rời khỏi trang, cố sao chép và những điểm bất thường trong câu trả lời và thời gian trả lời. Một cảnh báo là lý do để xem kỹ hơn, không phải bằng chứng cho điều gì. Báo cáo cũng gợi ý những câu ứng viên đã trả lời đúng để hỏi lại trong buổi phỏng vấn tiếp theo.

Những gì prepza không làm: ứng viên không viết, chạy hay debug code trong prepza. Đọc code và viết code là hai kỹ năng khác nhau, nên bước tiếp theo vẫn quan trọng. Xem [bài kiểm tra kỹ năng theo vị trí](/tests) để có sẵn bài kiểm tra làm điểm xuất phát.

## Bước 4: Bài tập về nhà hoặc lập trình trực tiếp

Giờ là lúc kiểm tra ứng viên có viết được code chạy được hay không. Đây là giai đoạn viết, chạy và debug code, bằng bài tập của riêng bạn hoặc trên một nền tảng dành cho lập trình viên. Xem [các lựa chọn thay thế HackerRank](/compare/hackerrank-alternatives) để biết bài kiểm tra kiến thức và nền tảng lập trình bổ sung cho nhau thế nào.

Hai hình thức phổ biến:

- **Bài tập về nhà:** sát thực tế và ít áp lực, nhưng chiếm thời gian buổi tối của ứng viên. Giới hạn tối đa vài giờ, nói rõ cần bao lâu, và chấm theo bộ tiêu chí viết sẵn.
- **Lập trình trực tiếp (live coding):** ngắn hơn và khó nhờ người khác làm hộ hơn, nhưng căng thẳng hơn. Cùng giải một bài toán sát thực tế, cho ứng viên dùng ngôn ngữ họ thạo nhất, và đánh giá cách họ suy luận, không chỉ việc họ có hoàn thành hay không.

Dù chọn cách nào, hãy chấm theo tiêu chí đã thống nhất trước: tính đúng đắn, dễ đọc, có test, cách xử lý các trường hợp biên. Vì bài kiểm tra kiến thức đã lọc nhóm ứng viên, bạn chỉ thực hiện bước này với vài người thay vì tất cả.

## Bước 5: Thiết kế hệ thống cho vị trí senior

Với kỹ sư senior, thêm một buổi thảo luận thiết kế: "Bạn sẽ xây dựng một service làm X như thế nào?" Quan sát cách họ làm rõ yêu cầu, lựa chọn giữa các đánh đổi và nhận ra điểm có thể hỏng. Hiếm khi có một đáp án đúng duy nhất, nên bộ tiêu chí chấm là thiết yếu. Hãy viết ra câu trả lời yếu, đạt và xuất sắc trông như thế nào trước buổi phỏng vấn đầu tiên.

Bỏ qua bước này với vị trí junior, vì ở đó nó chủ yếu kiểm tra sự tự tin hơn là kỹ năng.

## Bước 6: Phỏng vấn hành vi có cấu trúc kèm tiêu chí chấm

Phỏng vấn có cấu trúc là yếu tố dự báo đơn lẻ mạnh nhất trong nghiên cứu của Sackett và cộng sự (2022). Có cấu trúc nghĩa là:

- **Cùng một bộ câu hỏi cho mọi ứng viên,** gắn với hồ sơ vị trí: "Hãy kể về một lần bạn không đồng ý với một quyết định thiết kế. Bạn đã làm gì?"
- **Tiêu chí chấm cho từng câu hỏi,** kèm ví dụ về câu trả lời yếu, đạt và xuất sắc.
- **Chấm điểm độc lập:** mỗi người phỏng vấn chấm trước khi thảo luận với người khác, để ý kiến to tiếng nhất không quyết định kết quả.

Dùng giai đoạn này cho những gì bài kiểm tra không thể hiện được: hợp tác, tinh thần trách nhiệm, cách tiếp nhận góp ý, giao tiếp với người không làm kỹ thuật.

## Bước 7: Kiểm tra tham chiếu

Kiểm tra tham chiếu có thể xác nhận những gì bạn đã biết và phát hiện điểm đáng lo, nhưng hãy coi đó là bước kiểm tra cuối cùng, không phải bài kiểm tra quyết định. Sackett và cộng sự không đưa ra ước tính độ hiệu lực cho kiểm tra tham chiếu vì nghiên cứu hiện có quá ít, nên có rất ít bằng chứng về việc nó dự báo hiệu suất tốt đến đâu. Nếu thực hiện, hãy hỏi mọi người tham chiếu cùng vài câu hỏi về hành vi cụ thể.

## Bước 8: Trải nghiệm ứng viên và thời gian đến khi gửi offer

Các kỹ sư giỏi thường tham gia nhiều quy trình tuyển dụng cùng lúc. Một quy trình chậm hoặc khó hiểu sẽ khiến bạn mất họ.

- **Cho ứng viên biết toàn bộ quy trình ngay từ đầu:** các giai đoạn, mỗi giai đoạn mất bao lâu và khi nào họ nhận được phản hồi.
- **Giữ quy trình ngắn gọn.** Xếp lịch các giai đoạn sau sát nhau, và quyết định sớm sau buổi phỏng vấn cuối cùng.
- **Tôn trọng thời gian của họ.** Một bài kiểm tra kiến thức ngắn ở đầu quy trình giúp ít người phải ngồi qua những buổi phỏng vấn dài mà họ khó có khả năng vượt qua.
- **Phản hồi kịp thời cho mọi người,** kể cả những người bạn không chọn đi tiếp.

## Công bằng xuyên suốt quy trình

Một quy trình có cấu trúc cũng công bằng hơn, nhưng chỉ khi bạn thực hiện nó nhất quán:

- **Câu hỏi nhất quán** ở mọi giai đoạn, cho mọi ứng viên cùng một vị trí.
- **Tiêu chí chấm viết sẵn từ trước,** để mọi người được đánh giá theo cùng tiêu chí.
- **Điều chỉnh hợp lý:** cho thêm thời gian hoặc hình thức khác với ứng viên có yêu cầu, ví dụ do khuyết tật. Trong prepza, bạn có thể cho một ứng viên thêm thời gian trước khi họ bắt đầu.
- **Theo dõi kết quả.** Các phương pháp khác nhau cho thấy chênh lệch điểm giữa các nhóm khác nhau. Sackett và cộng sự nhận thấy chênh lệch trung bình ở bài kiểm tra kiến thức chuyên môn và mẫu công việc lớn hơn ở phỏng vấn có cấu trúc, thêm một lý do để kết hợp các phương pháp. Hãy theo dõi tỷ lệ đạt ở từng giai đoạn.
- **Con người quyết định.** Điểm số hỗ trợ một quyết định; nó không đưa ra quyết định. Hãy xem các câu trả lời trước khi loại bất kỳ ai.

Về các vấn đề pháp lý cơ bản, bao gồm Đạo luật AI của EU (EU AI Act) và các quy định của Mỹ về tỷ lệ tuyển chọn, xem [Kiểm tra trước tuyển dụng](/pre-employment-testing).

## Tóm tắt

Đặt các bước kiểm tra bao quát, rẻ lên trước và các bước sâu, tốn kém về sau. Sàng lọc CV theo yêu cầu bắt buộc, tổ chức một bài kiểm tra kiến thức ngắn, rồi dành thời gian của kỹ sư cho lập trình, thiết kế và phỏng vấn có cấu trúc với số ít người còn lại. Chấm theo tiêu chí viết sẵn từ trước, và giữ quy trình nhanh, rõ ràng.

## Nguồn tham khảo

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Đọc thêm

- [Bài kiểm tra kỹ năng theo vị trí](/tests)
- [Các lựa chọn thay thế HackerRank](/compare/hackerrank-alternatives)
- [Hướng dẫn kiểm tra trước tuyển dụng](/pre-employment-testing)
- [Bài kiểm tra kỹ năng và sàng lọc CV](/guides/skills-tests-vs-cv-screening)
- [Phỏng vấn kỹ sư trong thời đại AI](/guides/interviewing-in-the-age-of-ai)
