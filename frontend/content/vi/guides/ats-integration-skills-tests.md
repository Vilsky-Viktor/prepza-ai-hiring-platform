---
title: "Cách kết nối bài kiểm tra kỹ năng với ATS"
seoTitle: "Kết nối bài kiểm tra kỹ năng với ATS: hướng dẫn thực tế"
description: "Tự động gửi bài kiểm tra kỹ năng và nhận kết quả qua ATS, để con người giữ quyền quyết định tuyển dụng và biết cần kiểm tra điều gì trước."
updated: "2026-10-21"
---

# Cách kết nối bài kiểm tra kỹ năng với ATS

Hầu hết đội tuyển dụng quản lý ứng viên trong hệ thống theo dõi ứng viên (ATS) và tổ chức bài kiểm tra kỹ năng trên một công cụ khác. Nếu hai hệ thống không được kết nối, sẽ có người phải sao chép email từ ATS, gửi lời mời thủ công, chờ đợi, rồi chép điểm ngược lại. Với năm ứng viên thì vẫn ổn. Với năm mươi ứng viên, lời mời gửi đi trễ, kết quả nằm ở một tab thứ hai không ai mở, và những ứng viên giỏi nhận offer khác trong lúc chờ.

Hướng dẫn này giải thích một kết nối tốt giữa ATS và công cụ kiểm tra làm được gì, cần kiểm tra điều gì trước khi dựa vào nó, và cách thiết lập để tự động hóa lo phần việc lặt vặt trong khi con người vẫn đưa ra mọi quyết định tuyển dụng.

## Vì sao nên kết nối

| Không có kết nối | Có kết nối |
| --- | --- |
| Có người xuất hoặc sao chép email của ứng viên | Chuyển ứng viên sang một giai đoạn sẽ gửi lời mời |
| Lời mời được gửi khi có người rảnh | Lời mời được gửi trong vài phút sau khi chuyển |
| Kết quả nằm trong công cụ kiểm tra | Kết quả hiện trên hồ sơ ứng viên trong ATS |
| Hiring manager hỏi: "Đã có ai kiểm tra họ chưa?" | ATS cho thấy ai đã làm bài và kết quả thế nào |
| Gõ sai email và bỏ sót ứng viên | ATS là danh sách duy nhất về những người đã ứng tuyển |

Tốc độ quan trọng hơn bạn nghĩ. Khoảng cách giữa lúc ứng tuyển và lúc nhận phản hồi càng dài, càng nhiều ứng viên bỏ cuộc hoặc nhận việc khác. Tỷ lệ rơi rụng cụ thể thay đổi nhiều theo vị trí và thị trường, nên hãy thận trọng với các con số được công bố, nhưng xu hướng thì nhất quán: quy trình chậm sẽ mất người, và những ứng viên giỏi nhất thường có nhiều lựa chọn nhất.

## Một quy trình tốt trông như thế nào

Một tích hợp tốt bám theo các giai đoạn bạn đang dùng. Nó không tạo ra quy trình mới.

1. **Ứng viên nộp đơn** và vào ATS của bạn như bình thường.
2. **Một người chuyển ứng viên sang giai đoạn kiểm tra,** ví dụ "Kiểm tra kỹ năng". Việc chuyển này là điểm kích hoạt, nên con người vẫn quyết định ai được kiểm tra.
3. **Công cụ kiểm tra tự động gửi lời mời** cho bài kiểm tra gắn với tin tuyển dụng đó.
4. **Ứng viên làm bài** vào thời gian thuận tiện, trong hạn bạn đặt ra.
5. **Kết quả được ghi lại vào hồ sơ ứng viên trong ATS:** điểm số, có đạt hay không, các cảnh báo về tính trung thực và đường dẫn đến toàn bộ câu trả lời.
6. **Một người xem xét kết quả** và chuyển ứng viên sang bước tiếp theo, hoặc không.

Có hai việc được cố ý giữ thủ công: chọn ai được kiểm tra và quyết định bước tiếp theo. Kết nối chỉ loại bỏ phần sao chép ở giữa.

### Vì sao không kích hoạt với mọi hồ sơ mới?

Một số công cụ mời tất cả những ai ứng tuyển. Cách này có thể ổn với các vị trí tuyển số lượng lớn, nơi mọi ứng viên làm cùng một bài. Nhưng một giai đoạn mà bạn chủ động chuyển ứng viên vào thì dễ kiểm soát hơn: bạn có thể bỏ qua những ứng viên rõ ràng không đáp ứng yêu cầu bắt buộc (không có giấy phép lao động, sai địa điểm), và bạn không bao giờ phải kiểm tra, hay trả tiền cho, người mà đằng nào bạn cũng sẽ loại.

## Cần kiểm tra gì trước khi chọn một tích hợp

Không phải lời quảng cáo "tích hợp với ATS của bạn" nào cũng có nghĩa như nhau. Hãy đặt những câu hỏi này trước khi kết nối bất cứ thứ gì.

| Câu hỏi | Vì sao quan trọng | Một câu trả lời tốt |
| --- | --- | --- |
| Kết nối bằng cách nào? | Mật khẩu dùng chung và tài khoản do nhà cung cấp giữ khó kiểm soát hoặc thu hồi | Một khóa API hoặc token do công ty bạn tạo và có thể xóa bất cứ lúc nào |
| Khóa được phép làm gì? | Một khóa có toàn quyền là rủi ro nếu bị lộ | Quyền tối thiểu mà tích hợp cần, được liệt kê trong tài liệu |
| Điều gì kích hoạt lời mời? | Bạn cần biết chính xác khi nào ứng viên nhận email | Một giai đoạn cụ thể do bạn chọn cho từng tin tuyển dụng |
| Kết quả hiển thị ở đâu? | Kết quả không ai nhìn thấy thì vô ích | Trên hồ sơ ứng viên, dưới dạng ghi chú hoặc bình luận mà đội của bạn vẫn đọc |
| Điều gì xảy ra khi lời mời gửi thất bại? | Hết credit, gõ sai, tài khoản bị tạm dừng: ứng viên bị kẹt mà không ai hay | Có người được báo, và ứng viên có thể được mời lại |
| Một sự kiện có thể bị xử lý hai lần không? | ATS gửi lại sự kiện; ứng viên không nên nhận hai lời mời | Mỗi ứng viên chỉ được mời một lần cho mỗi bài kiểm tra, dù sự kiện đến bao nhiêu lần |
| Sự kiện gửi đến được xác minh thế nào? | Một địa chỉ không xác minh có thể nhận sự kiện giả mạo | Yêu cầu có chữ ký mà công cụ kiểm tra |
| Dữ liệu ứng viên được lưu bao lâu? | Các luật bảo vệ dữ liệu như GDPR yêu cầu thời hạn lưu trữ rõ ràng | Một thời hạn cụ thể, và xóa khi bạn xóa tin tuyển dụng, bài kiểm tra hoặc tài khoản |
| Chi phí bao nhiêu? | Gói tính theo người dùng có thể khiến tự động hóa trở nên đắt đỏ | Chi phí dự đoán được cho mỗi ứng viên được kiểm tra |

Nếu nhà cung cấp không trả lời rõ được các câu hỏi về lỗi và trùng lặp, hãy chuẩn bị tinh thần tự phát hiện ra theo cách khó khăn.

### Bảo vệ dữ liệu

Kết nối hai hệ thống nghĩa là dữ liệu ứng viên, ít nhất là tên và email, được chuyển giữa hai công ty. Theo GDPR và các luật tương tự, nhà cung cấp bài kiểm tra thường là bên xử lý dữ liệu của bạn, nên bạn cần một thỏa thuận xử lý dữ liệu và nên thông báo cho ứng viên, trong thông báo quyền riêng tư hoặc trong lời mời, rằng bài kiểm tra kỹ năng là một phần của quy trình. Chỉ chuyển những dữ liệu tối thiểu mà bài kiểm tra cần. Để hiểu thêm về khía cạnh pháp lý của bài kiểm tra và AI trong tuyển dụng, xem [Dùng AI trong tuyển dụng có hợp pháp ở EU không?](/guides/is-ai-hiring-legal-in-the-eu)

## Danh sách kiểm tra khi thiết lập

Trước khi bật cho một vị trí đang tuyển thật:

1. **Tạo một giai đoạn chỉ dành cho kiểm tra** trong ATS, chẳng hạn "Kiểm tra kỹ năng". Đừng dùng lại một giai đoạn mang ý nghĩa khác, nếu không ứng viên sẽ bị mời nhầm.
2. **Tạo khóa từ một tài khoản quản trị** thấy được mọi tin tuyển dụng bạn muốn liên kết, chỉ với các quyền mà tài liệu liệt kê.
3. **Liên kết mỗi tin tuyển dụng với bài kiểm tra của nó** và chọn giai đoạn kích hoạt lời mời.
4. **Thiết lập webhook** nếu ATS yêu cầu làm thủ công, và dán khóa bí mật của nó vào chỗ công cụ yêu cầu.
5. **Tự thử với chính mình.** Thêm một ứng viên bằng email của bạn, chuyển sang giai đoạn đó, làm bài và kiểm tra xem ghi chú có xuất hiện trong ATS không.
6. **Quyết định ai theo dõi lỗi:** ai được báo khi không gửi được lời mời, và ai xử lý.
7. **Thống nhất cách đọc kết quả.** Điểm đạt là mức tham khảo, không phải lý do loại tự động. Hãy quyết định trước khi có kết quả, không phải sau.

## Những sai lầm thường gặp

- **Tự động hóa quyết định thay vì giấy tờ.** Tự động loại mọi ứng viên dưới một mức điểm sẽ bỏ đi bước kiểm tra của con người, vốn phát hiện được câu hỏi kém hoặc ứng viên gặp sự cố mạng. Hãy để điểm số sắp xếp; để con người quyết định.
- **Kích hoạt từ sai giai đoạn.** Một giai đoạn mà recruiter dùng cho mục đích khác sẽ gửi bài kiểm tra cho những người không nên nhận.
- **Một bài kiểm tra cho mọi tin tuyển dụng.** Kết nối khiến việc gửi cùng một bài kiểm tra cho mọi nơi trở nên dễ dàng. Bài kiểm tra hữu ích nhất khi được xây dựng cho đúng vị trí đó. Xem [Bài kiểm tra kỹ năng và sàng lọc CV](/guides/skills-tests-vs-cv-screening).
- **Không ai theo dõi lỗi.** Nếu lời mời thất bại mà không ai hay, ứng viên chờ một email không bao giờ đến, còn bạn nghĩ họ đã phớt lờ.
- **Khóa gắn với người sắp nghỉ việc.** Một số khóa ATS hoạt động dưới danh nghĩa người đã tạo ra chúng. Khi tài khoản người đó bị đóng, kết nối dừng lại. Hãy dùng một tài khoản sẽ còn tồn tại, và kết nối lại khi mọi người đổi vai trò.
- **Quên ứng viên ngoài ATS.** Ứng viên được giới thiệu và ứng viên ứng tuyển trực tiếp không bao giờ vào ATS vẫn cần lời mời. Hãy giữ cả cách mời thủ công.

## Cách testee thực hiện

testee kết nối với **Workable, Greenhouse, Teamtailor, Recruitee và Breezy HR**, theo đúng quy trình ở trên.

- **Khóa của bạn, bạn kiểm soát.** Chủ sở hữu hoặc quản trị viên kết nối ATS trong tab Tích hợp của công ty bằng một khóa do công ty bạn tạo trong ATS. testee kiểm tra khóa trước khi lưu, lưu trữ ở dạng mã hóa và không bao giờ hiển thị lại. Ngắt kết nối sẽ xóa ngay khóa và các tin tuyển dụng đã liên kết.
- **Liên kết một tin tuyển dụng với một buổi phỏng vấn.** Chọn một tin tuyển dụng trong ATS và giai đoạn kích hoạt lời mời, rồi liên kết với một buổi phỏng vấn có sẵn trong testee hoặc tạo buổi mới từ nội dung tin tuyển dụng trong ATS. Bạn xem lại các chủ đề trước khi bất kỳ câu hỏi nào được viết.
- **Chuyển ứng viên là lời mời được gửi.** Mỗi ứng viên chỉ được mời một lần cho mỗi buổi phỏng vấn, kể cả khi ATS gửi cùng một sự kiện hai lần.
- **Kết quả trở lại ATS.** Khi ứng viên làm xong, testee thêm một ghi chú hoặc bình luận vào hồ sơ của họ trong ATS, gồm điểm, có đạt hay không, các cảnh báo về tính trung thực (rời khỏi trang, cố sao chép, chọn câu trả lời quá nhanh để kịp đọc câu hỏi) và đường dẫn đến bảng điểm với mọi câu trả lời.
- **Lỗi không bị bỏ qua.** Nếu không mời được một ứng viên, chẳng hạn vì công ty hết credit, chạm giới hạn email hoặc testee đã tạm dừng lời mời, mọi thành viên của công ty đều nhận được thông báo ghi rõ tên ATS. Những ứng viên chưa được mời vì thiếu credit sẽ được mời tự động sau khi nạp credit, và các ứng viên đang chờ của bất kỳ tin tuyển dụng nào cũng có thể được mời lại chỉ với một cú nhấp.
- **Slack, nếu bạn dùng.** testee có thể đăng thông báo, chẳng hạn một ứng viên đã làm xong hoặc một ứng viên từ ATS không mời được, lên kênh Slack do bạn chọn.
- **Nền tảng riêng của bạn.** Nếu ATS của bạn không có trong danh sách, [API](/api-docs) của testee cho phép bạn mời ứng viên bằng khóa API và nhận một webhook có chữ ký khi ứng viên bắt đầu, làm xong, không nhận được lời mời, hết hạn lời mời hoặc bị xóa khỏi buổi phỏng vấn, và khi một buổi phỏng vấn sẵn sàng.
- **Dữ liệu được lưu trong thời hạn xác định.** Ứng viên được lưu từ ATS sẽ bị xóa sau 365 ngày, hoặc sớm hơn cùng với buổi phỏng vấn hoặc công ty của họ.

Một số ATS cần một bước ở phía họ. Greenhouse, Teamtailor và Recruitee yêu cầu bạn thêm webhook thủ công; hộp thoại Hướng dẫn của testee hiển thị địa chỉ và chỗ dán khóa bí mật. testee tự thiết lập webhook cho Workable và Breezy HR.

Giá tính theo ứng viên, không có gói đăng ký: bạn chỉ trả tiền cho những ứng viên trả lời ít nhất một câu hỏi, $5 mỗi người với gói nạp $50, $4 từ gói nạp $200, $3 từ gói nạp $600 và $2 từ gói nạp $1.000. Giá ở đây tính bằng đô la Mỹ, và bằng đồng tiền địa phương ở Canada, Úc, Israel, Ba Lan, Thụy Sĩ, Nhật Bản, Hàn Quốc, Đài Loan, Hồng Kông, Thái Lan, Singapore, Ấn Độ, phần còn lại của châu Âu và Vương quốc Anh; VAT hoặc thuế bán hàng được xử lý khi thanh toán. Kết nối ATS và tạo buổi phỏng vấn là miễn phí, và 3 ứng viên đầu tiên của công ty đầu tiên của bạn được miễn phí. Xem [bảng giá](/pricing).

## Đọc thêm

- [Cách sàng lọc 100 ứng viên trong một ngày](/guides/screen-100-applicants-in-a-day)
- [Bài kiểm tra kỹ năng và sàng lọc CV](/guides/skills-tests-vs-cv-screening)
- [Kiểm tra trước tuyển dụng: hướng dẫn thực tế](/pre-employment-testing)
