---
title: "Phỏng vấn kỹ sư trong thời đại AI: nên kiểm tra gì bây giờ"
seoTitle: "Phỏng vấn kỹ thuật thời AI: nên đánh giá ứng viên ra sao"
description: "Trợ lý AI đã là một phần công việc hằng ngày của kỹ sư. Điều đó thay đổi nội dung phỏng vấn, cách công ty thích ứng và vai trò của bài kiểm tra kiến thức."
updated: "2026-10-29"
---

# Phỏng vấn kỹ sư trong thời đại AI: nên kiểm tra gì bây giờ

Trong nhiều năm, buổi phỏng vấn kỹ thuật kinh điển yêu cầu ứng viên viết code từ đầu: đảo ngược một danh sách, cài đặt một cache, giải một câu đố trên bảng trắng hoặc trong trình soạn thảo dùng chung. Ý tưởng rất đơn giản: nếu ai đó viết được code, có lẽ họ làm được việc.

Các trợ lý lập trình AI đã làm mối liên hệ đó yếu đi. Nhiều đoạn code thông thường giờ đây có thể được trợ lý viết nháp trong vài giây, cả khi làm việc lẫn, nếu bạn không ngăn chặn, trong một buổi phỏng vấn từ xa. Điều đó không khiến kỹ năng kỹ thuật kém quan trọng đi. Nó thay đổi những kỹ năng nào quan trọng nhất, và vì thế thay đổi những gì một buổi phỏng vấn nên kiểm tra.

Hướng dẫn này điểm lại những gì đã thay đổi, cách một số công ty đang thích ứng, và cách thiết kế quy trình phỏng vấn vẫn cho bạn biết ai làm được việc. Bài viết dành cho hiring manager và trưởng nhóm kỹ thuật.

## Điều gì đã thay đổi

Trợ lý AI giờ là một phần công việc hằng ngày của nhiều lập trình viên. Trong Khảo sát Lập trình viên Stack Overflow 2025, 84% người trả lời cho biết họ đang dùng hoặc dự định dùng công cụ AI trong quá trình phát triển, và 51% lập trình viên chuyên nghiệp cho biết họ dùng hằng ngày ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)). Báo cáo Octoverse 2025 của GitHub cho biết 80% lập trình viên mới trên GitHub dùng Copilot ngay trong tuần đầu tiên ([GitHub, tháng 10/2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)).

Cũng khảo sát đó cho thấy các giới hạn. Số người không tin vào độ chính xác của kết quả AI (khoảng 46%) nhiều hơn số người tin (khoảng 33%). Nỗi bực bội phổ biến nhất, được 66% nhắc đến, là "giải pháp AI gần đúng, nhưng chưa hẳn đúng", và 45% cho biết debug code do AI tạo ra tốn nhiều thời gian hơn ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)).

Gộp lại, các con số này mô tả một sự dịch chuyển trong chính công việc. Viết bản nháp đầu tiên của code ngày càng rẻ. Đánh giá bản nháp đó có đúng không, và sửa khi nó sai, là nơi tập trung phần lớn kỹ năng hiện nay.

## Các công ty đang thích ứng thế nào

Ngành vẫn chưa có một câu trả lời chung. Các cách làm được công bố đi theo những hướng khác nhau:

- **Cho phép hoặc yêu cầu dùng AI trong phỏng vấn.** Tháng 6/2025, Canva cho biết họ giờ kỳ vọng ứng viên backend, machine learning và frontend dùng các công cụ AI như Copilot, Cursor và Claude trong một vòng mới "Lập trình có AI hỗ trợ" (AI-Assisted Coding). Vòng này đánh giá ứng viên có thể "chia nhỏ các yêu cầu phức tạp, mơ hồ", "phát hiện và sửa lỗi trong code do AI tạo ra" và "bảo đảm giải pháp do AI tạo ra đạt chuẩn production" hay không ([Canva Engineering, tháng 6/2025](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)).
- **Thử nghiệm vòng lập trình có AI hỗ trợ.** Tháng 7/2025, Business Today, dẫn nguồn 404 Media, đưa tin Meta đang xây dựng một vòng phỏng vấn lập trình trong đó ứng viên có trợ lý AI. Bài báo trích lời Meta rằng cách này "phản ánh sát hơn môi trường phát triển mà nhân viên tương lai của chúng tôi sẽ làm việc, đồng thời khiến việc gian lận bằng LLM kém hiệu quả hơn" ([Business Today, tháng 7/2025](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)).
- **Hạn chế công cụ và gặp mặt trực tiếp.** Tháng 3/2025, CNBC đưa tin về một công cụ được tạo ra để giúp ứng viên dùng AI mà không bị phát hiện trong các buổi phỏng vấn lập trình từ xa. Cũng trong bài báo đó, Amazon cho biết ứng viên phải cam kết không dùng công cụ trái phép, CEO của Google gợi ý hiring manager cân nhắc một số buổi phỏng vấn trực tiếp, và Deloitte đã khôi phục phỏng vấn trực tiếp cho chương trình tuyển sinh viên mới tốt nghiệp tại Anh ([CNBC qua NBC New York, tháng 3/2025](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)).

Đây chỉ là vài công ty lớn, không phải một khảo sát thị trường, và chính sách có thể thay đổi. Nhưng chúng cùng chỉ về một hướng: một bài "viết đoạn này từ đầu" làm từ xa giờ khó tin cậy hơn, và câu hỏi đáng quan tâm đã chuyển từ "bạn có viết được code không?" sang "bạn có hiểu code đủ rõ để đánh giá nó không?"

## Vì sao kiến thức quan trọng hơn ở vòng lọc đầu

Nếu trợ lý có thể viết nháp code, điều gì phân biệt kỹ sư giỏi với kỹ sư yếu? Chủ yếu là những thứ trợ lý không thể cung cấp thay họ:

- **Khái niệm và lý thuyết.** Biết cơ sở dữ liệu dùng index thế nào, vì sao race condition xảy ra, hay một framework làm gì trong mỗi request giúp kỹ sư nhận ra khi code được tạo ra bị sai.
- **Đọc code.** Trước khi dùng kết quả của AI, phải có người đọc nó và biết nó sẽ in ra, trả về hoặc thay đổi gì.
- **Debug.** Khi đoạn code "gần đúng" bị lỗi, cách sửa đến từ việc hiểu vì sao.
- **Khả năng phán đoán.** Lựa chọn giữa hai cách làm đều chạy được đòi hỏi hiểu biết về các đánh đổi: hiệu năng, bảo mật, khả năng bảo trì.

Đây là các kỹ năng kiến thức và suy luận, và có thể kiểm tra trực tiếp, nhanh chóng. Nghiên cứu tuyển dụng vốn đã xếp bài kiểm tra kiến thức chuyên môn vào nhóm các yếu tố dự báo hiệu suất công việc tốt hơn, tính trung bình: trong một phân tích lại năm 2022 về các nghiên cứu suốt nhiều thập kỷ, Sackett, Zhang, Berry và Lievens ước tính độ hiệu lực của bài kiểm tra kiến thức chuyên môn là .40, gần với phỏng vấn có cấu trúc ở mức .42 ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Nghiên cứu đó ra đời trước các trợ lý AI, nên không chứng minh được điều gì về công việc trong thời đại AI. Nhưng nó ủng hộ việc dùng một bài kiểm tra kiến thức gắn với công việc làm vòng lọc đầu, và sự dịch chuyển nêu trên khiến phần kiến thức được kiểm tra trở nên trọng tâm hơn với công việc, chứ không phải kém đi.

## Bài tập thực hành vẫn có chỗ đứng

Không điều nào ở trên khiến bài tập lập trình trở nên vô dụng. Nó thay đổi thời điểm bạn dùng chúng và hình thức của chúng:

- **Làm cặp với AI.** Như vòng của Canva, đưa cho ứng viên một trợ lý AI và một nhiệm vụ mở, sát thực tế. Quan sát cách họ chia nhỏ vấn đề, hỏi trợ lý những gì, và chấp nhận hay bác bỏ điều gì.
- **Review code.** Đưa một pull request, có thể do AI viết, chứa vài lỗi thật. Hỏi họ sẽ sửa gì và vì sao.
- **Debug.** Đưa một codebase nhỏ có một test bị lỗi. Điều này rất gần với công việc hằng ngày mà khảo sát mô tả và khó giả mạo.
- **Thiết kế hệ thống.** Với vị trí senior, một buổi thảo luận về các đánh đổi cho thấy khả năng phán đoán mà không một câu lệnh prompt nào tạo ra được.

Các bài tập này tốn thời gian của kỹ sư để tổ chức và chấm. Đó là lý do chính để đặt một bước kiểm tra kiến thức nhanh, bao quát trước chúng, để chúng dành cho những ứng viên có nhiều khả năng thành công nhất.

## Quy trình cho thời đại AI

1. **Sàng lọc hồ sơ chỉ theo yêu cầu bắt buộc:** quyền làm việc, địa điểm, kinh nghiệm tiên quyết.
2. **Tổ chức một bài kiểm tra kiến thức ngắn** về khái niệm, lý thuyết và đọc code cho stack của bạn.
3. **Tổ chức một bài tập thực hành** theo hình thức phù hợp với cách nhóm bạn làm việc: làm cặp có AI hỗ trợ, review code hoặc debug, từ xa hoặc trực tiếp.
4. **Thêm thiết kế hệ thống** cho vị trí senior.
5. **Tổ chức một buổi phỏng vấn có cấu trúc** với bộ câu hỏi cố định và tiêu chí chấm, bao gồm cách ứng viên dùng công cụ AI và kiểm tra kết quả của chúng.
6. **Để con người quyết định,** với mỗi kết quả là một yếu tố đầu vào.

Cho ứng viên biết trước những công cụ nào được phép ở mỗi giai đoạn. Một quy tắc rõ ràng công bằng hơn trò chơi đoán ý, và giúp kết quả dễ so sánh hơn.

Để xem phiên bản đầy đủ từng bước, đọc [Cách tuyển kỹ sư phần mềm](/guides/hiring-engineers).

## prepza phù hợp ở đâu

prepza rất phù hợp với bước 2. prepza biến mô tả công việc của bạn thành một buổi phỏng vấn kiến thức trắc nghiệm có tính giờ, và bạn duyệt các chủ đề được đề xuất trước khi bất kỳ câu hỏi nào được viết, nên bài kiểm tra chỉ bao quát stack của bạn.

- **Khái niệm và lý thuyết từ mô tả công việc:** cơ sở dữ liệu, API, kiến trúc, cách một framework hoạt động, các thực hành bảo mật.
- **Câu hỏi đọc code:** một đoạn code ngắn kèm câu hỏi nó in ra hoặc trả về gì, nó làm gì, vì sao nó lỗi, hoặc thay đổi nào sửa được nó. Đó chính là kỹ năng review mà công việc có AI hỗ trợ phụ thuộc vào.
- **Đồng hồ cho từng câu hỏi:** mỗi câu có đồng hồ đếm ngược riêng, do máy chủ áp dụng, và mỗi ứng viên nhận bộ câu hỏi ngẫu nhiên của riêng mình. Điều đó khiến việc tra cứu đáp án, kể cả hỏi trợ lý AI, khó hơn. Nó không khiến việc đó trở nên bất khả thi.
- **Tín hiệu cảnh báo:** bảng điểm đánh dấu các câu trả lời quá nhanh để kịp đọc câu hỏi, số lần ứng viên rời khỏi trang và các lần cố sao chép. Khi ứng viên làm xong, báo cáo của họ còn chỉ ra những mẫu trả lời thường xuất hiện khi ai đó chuyển câu hỏi cho AI rồi chép lại đáp án: mọi câu hỏi tốn gần như cùng một khoảng thời gian bất kể độ dài hay độ khó, hoặc câu khó thì đúng trong khi câu dễ lại sai. Một cảnh báo hay một mẫu trả lời là lý do để xem kỹ hơn, không phải bằng chứng gian lận.
- **Câu hỏi cho buổi phỏng vấn trực tiếp:** báo cáo gợi ý tối đa 3 câu ứng viên đã trả lời đúng, thuộc những chủ đề họ mạnh nhất, để trao đổi trong buổi phỏng vấn trực tiếp, nơi không AI nào có thể trả lời thay họ.

Những gì prepza không làm: ứng viên không viết, chạy hay debug code trong prepza, và prepza không quan sát họ dùng trợ lý AI. Phần đó thuộc giai đoạn thực hành, tổ chức nội bộ hoặc trên một nền tảng dành cho lập trình viên, bổ sung cho bài kiểm tra kiến thức. Xem [bài kiểm tra kỹ năng theo vị trí](/tests) để có sẵn bài kiểm tra làm điểm xuất phát, và [phỏng vấn AI](/ai-interviews) để biết prepza dùng AI thế nào và để lại những gì cho con người.

## Công bằng và trải nghiệm ứng viên

Thay đổi quy trình là thời điểm tốt để kiểm tra xem nó có công bằng không:

- **Nói rõ quy tắc về AI** ở mọi giai đoạn, bằng văn bản.
- **Giữ điều kiện như nhau** cho mọi người ở cùng một giai đoạn.
- **Điều chỉnh hợp lý,** chẳng hạn thêm thời gian, cho ứng viên có yêu cầu.
- **Đừng coi một tín hiệu là phán quyết.** Ngập ngừng, nhìn đi chỗ khác hay trả lời nhanh đều có thể có nguyên nhân vô hại.
- **Giữ ngắn gọn.** Mỗi giai đoạn bạn thêm vào đều lấy đi thời gian của ứng viên giỏi, thời gian mà họ có thể dành cho một offer khác.

## Tóm tắt

Trợ lý AI khiến việc tạo ra code rẻ hơn và việc đánh giá code quan trọng hơn. Một quy trình tốt phản ánh điều đó: kiểm tra kiến thức, lý thuyết và đọc code từ sớm, nơi việc này nhanh và, với đồng hồ cho từng câu hỏi, khó nhờ người khác làm hộ hơn; sau đó dùng bài tập thực hành, thường cho phép dùng AI, để xem ứng viên làm việc thế nào. Nói rõ quy tắc, và để con người nắm quyền quyết định.

## Nguồn tham khảo

- Stack Overflow, [2025 Developer Survey: AI](https://survey.stackoverflow.co/2025/ai).
- GitHub, [Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), 28/10/2025.
- Canva Engineering, [Yes, you can use AI in our interviews](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews), 11/6/2025.
- Business Today, [Meta to test job applicants with AI-assisted coding interviews](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31), 31/7/2025, dẫn nguồn 404 Media.
- CNBC qua NBC New York, [Meet the 21-year-old helping coders use AI to cheat in Google and other tech job interviews](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1), 9/3/2025.
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Đọc thêm

- [Cách tuyển kỹ sư phần mềm](/guides/hiring-engineers)
- [Bài kiểm tra kỹ năng theo vị trí](/tests)
- [Gian lận trong bài kiểm tra trực tuyến và cách phòng chống hiệu quả](/guides/cheating-in-online-assessments)
- [Phỏng vấn AI: là gì và cách dùng công bằng](/ai-interviews)
- [Bài kiểm tra kỹ năng và sàng lọc CV](/guides/skills-tests-vs-cv-screening)
