---
title: "Agent AI, MCP và API: là gì và cách dùng trong tuyển dụng"
seoTitle: "Agent AI, MCP và API trong tuyển dụng: là gì và cách dùng"
description: "Agent AI, MCP và API là gì, cách dùng an toàn trong tuyển dụng, và cách vận hành prepza từ trợ lý AI của nó, từ Claude, ChatGPT hoặc nền tảng của bạn."
updated: "2026-10-22"
---

# Agent AI, MCP và API: là gì và cách dùng trong tuyển dụng

Hầu hết mọi người làm quen với AI lần đầu qua một cửa sổ chat: bạn hỏi, AI trả lời. Agent AI tiến thêm một bước. Nó có thể tra cứu trong các công cụ của bạn và, khi bạn yêu cầu, thực hiện việc trong đó: tạo một buổi phỏng vấn, mời cả một danh sách ứng viên, cho bạn biết ai đạt điểm cao nhất tuần trước. Model Context Protocol (MCP) là tiêu chuẩn cho phép ứng dụng chat AI bạn đang dùng, như Claude hay ChatGPT, kết nối với những công cụ như vậy. Còn API là cách lâu đời hơn và chính xác hơn để phần mềm giao tiếp với phần mềm, không có AI ở giữa.

Hướng dẫn này giải thích cả ba bằng ngôn ngữ dễ hiểu: chúng hữu ích gì trong tuyển dụng, cần lưu ý điều gì, và cách dùng chúng với prepza.

## Agent AI là gì

Chatbot chỉ viết ra văn bản. Agent AI là một mô hình ngôn ngữ có **công cụ (tools)**: những thao tác nhỏ, được định nghĩa rõ ràng mà nó được phép gọi, chẳng hạn "liệt kê ứng viên của buổi phỏng vấn này" hay "mời email này". Khi bạn hỏi, agent quyết định dùng công cụ nào, đọc kết quả trả về và trả lời dựa trên đó, chứ không dựa vào trí nhớ.

| Chatbot | Agent AI |
| --- | --- |
| Trả lời từ những gì đã học khi huấn luyện | Trả lời từ dữ liệu hiện tại của bạn, được đọc qua công cụ |
| Chỉ có thể mô tả cách làm một việc | Có thể làm việc đó, khi bạn yêu cầu và cho phép |
| Đoán khi không biết | Tra cứu, hoặc nói rằng nó không làm được |
| Chỉ nằm trong một cửa sổ | Làm việc bên trong các công cụ bạn kết nối với nó |

Chính các công cụ làm nên giá trị của agent AI, và cũng quyết định nó an toàn hay không. Một agent tốt chỉ dùng được những công cụ được cấp, chỉ trong phạm vi quyền của bạn, và chỉ làm những gì bạn yêu cầu.

## MCP là gì

Model Context Protocol là một tiêu chuẩn mở do Anthropic giới thiệu vào cuối năm 2024 và hiện được Claude, ChatGPT cùng nhiều ứng dụng AI và công cụ lập trình khác hỗ trợ. MCP thường được ví như cổng USB-C cho AI: thay vì mỗi ứng dụng AI tự xây kết nối riêng tới từng công cụ, một công cụ cung cấp một **máy chủ MCP**, và bất kỳ ứng dụng AI nào hỗ trợ MCP đều dùng được.

Máy chủ MCP cho ứng dụng AI biết ba điều:

1. **Có những công cụ nào**, kèm tên, mô tả và các thông tin mà mỗi công cụ cần.
2. **Công cụ nào chỉ đọc** và công cụ nào thay đổi dữ liệu, để ứng dụng AI hỏi bạn trước khi thay đổi.
3. **Bạn là ai**, qua bước đăng nhập mà bạn chỉ cần chấp thuận một lần, để mọi lệnh gọi đều chạy dưới danh nghĩa của bạn, với quyền của bạn.

Với bạn, điều này có nghĩa là bạn có thể làm việc với một công cụ ngay từ cửa sổ chat đang dùng, không cần sao chép dữ liệu qua lại giữa các cửa sổ.

## API là gì, và khác ở đâu

API (giao diện lập trình ứng dụng) là một tập hợp các yêu cầu cố định mà một chương trình có thể gửi cho chương trình khác: "liệt kê ứng viên của buổi phỏng vấn này", "mời email này". Lập trình viên của bạn viết mã để gửi các yêu cầu đó. Không có AI tham gia: cùng một yêu cầu luôn cho cùng một kết quả, đúng như điều bạn cần cho tự động hóa chạy một mình.

| | Mira, trợ lý AI (trong ứng dụng) | MCP (trong Claude hoặc ChatGPT) | API |
| --- | --- | --- | --- |
| Ai sử dụng | Bạn, trong prepza | Bạn, trong chat AI của bạn | Mã của nền tảng bạn |
| Cách yêu cầu | Bằng lời của chính bạn | Bằng lời của chính bạn | Các yêu cầu cố định do lập trình viên viết |
| Ai duyệt thay đổi | Bạn, trên một thẻ | Bạn, trong ứng dụng AI của bạn | Mã của bạn, theo đúng cách đã viết |
| Phù hợp nhất cho | Câu hỏi và việc nhanh | Kết hợp prepza với các công cụ và tệp khác của bạn | Tự động hóa chạy mà không cần ai theo dõi |
| Đăng nhập với tư cách | Bạn | Bạn | Một khóa của công ty |

Hãy dùng Mira hoặc MCP khi có người trực tiếp tham gia. Hãy dùng API khi hệ thống của bạn cần tự mời ứng viên và thu thập kết quả, ví dụ từ trang tuyển dụng hoặc một công cụ nhân sự nội bộ.

## Hữu ích gì trong tuyển dụng

Tuyển dụng có rất nhiều bước nhỏ, lặp đi lặp lại, nằm rải rác trên nhiều công cụ. Agent AI làm tốt chính những việc đó:

- **Câu hỏi về quy trình tuyển dụng của bạn.** "Những ứng viên Senior Backend nào đã đạt trong tuần này?", "Ai chưa bắt đầu buổi phỏng vấn?", "Điểm trung bình của chúng ta cho vị trí data analyst là bao nhiêu?"
- **Thiết lập.** "Tạo buổi phỏng vấn từ mô tả công việc này", "Đặt điểm đạt là 70%", "Cho ứng viên này thêm 50% thời gian."
- **Việc hàng loạt.** "Mời 12 người này tham gia buổi phỏng vấn frontend", dán thẳng từ email hoặc bảng tính.
- **Kết hợp nhiều nguồn.** Trong Claude hoặc ChatGPT, bạn có thể kết hợp prepza với các công cụ và tệp khác đã kết nối: so sánh mô tả công việc trong tài liệu của bạn với các chủ đề của buổi phỏng vấn, hoặc soạn tin nhắn cho các ứng viên lọt vào danh sách rút gọn.

Điều nó không nên làm là đưa ra quyết định tuyển dụng. Điểm số hỗ trợ đánh giá của con người, không thay thế nó. Hãy để agent sắp xếp, tóm tắt và chuẩn bị, còn quyết định thì để con người đưa ra. Xem [Dùng AI trong tuyển dụng có hợp pháp ở EU không?](/guides/is-ai-hiring-legal-in-the-eu) để hiểu vì sao điều đó cũng quan trọng về mặt pháp lý.

## Cần lưu ý điều gì

Kết nối AI với dữ liệu tuyển dụng cần được cân nhắc cẩn thận như khi cấp quyền truy cập cho một đồng nghiệp.

| Rủi ro | Điều giúp ích |
| --- | --- |
| Agent làm điều bạn không có ý định | Thay đổi cần bạn duyệt trước, và nó chỉ làm đúng điều bạn yêu cầu |
| Nó thấy nhiều hơn mức cần thiết | Nó hành động dưới danh nghĩa của bạn: thấy những gì bạn thấy, không hơn |
| Chỉ dẫn ẩn trong dữ liệu | Tên, câu trả lời và tài liệu của ứng viên là dữ liệu, không bao giờ là chỉ dẫn để làm theo |
| Thông tin bí mật lọt vào chat | Khóa API và mật khẩu không bao giờ đi qua chat |
| Sai lầm không thể hoàn tác | Việc xóa tài khoản hoặc công ty vẫn nằm trong ứng dụng, với bước xác nhận riêng |
| Dữ liệu rời khỏi công cụ của bạn | Dữ liệu đến ứng dụng AI bạn kết nối, theo điều khoản của ứng dụng đó: chỉ kết nối những ứng dụng công ty bạn cho phép |
| Sử dụng mất kiểm soát | Giới hạn số thao tác được chạy mỗi giờ |

Trước khi kết nối bất kỳ ứng dụng AI nào với dữ liệu công việc, hãy xem chính sách của công ty bạn về công cụ AI, và cho ứng viên biết trong thông báo quyền riêng tư những dịch vụ nào xử lý dữ liệu của họ.

## Ba cách làm việc với prepza ngoài các trang của nó

### 1. Mira, trợ lý AI tích hợp sẵn

Chọn **hỏi Mira** ở thanh đầu trang của bất kỳ trang nào. Mira, trợ lý AI của prepza, biết các công ty, buổi phỏng vấn, ứng viên, credit và tích hợp của bạn, cũng như cách prepza hoạt động. Nó trả lời bằng ngôn ngữ của bạn, và bạn có thể gõ hoặc nói.

- **Nó trả lời từ dữ liệu của bạn**, với cùng phạm vi bạn thấy: quản trị viên thấy những gì quản trị viên thấy, người xem thấy những gì người xem thấy.
- **Nó biết bạn đang ở trang nào.** Hỏi "Tôi có thể làm gì trên trang này?" để xem hướng dẫn của trang đó, hoặc "Ai là người giỏi nhất ở đây?" trong danh sách ứng viên của một buổi phỏng vấn, và nó trả lời về buổi phỏng vấn đó mà không hỏi lại là buổi nào.
- **Nó chuẩn bị thay đổi, bạn xác nhận.** Khi được yêu cầu mời ứng viên, nó hiển thị một thẻ ghi đúng những gì sẽ xảy ra, chẳng hạn "Mời 12 ứng viên tham gia Backend developer". Không có gì chạy cho đến khi bạn chọn xác nhận.
- **Nó cho thấy nguồn.** Bên dưới câu trả lời, bạn thấy các ứng viên hoặc buổi phỏng vấn nó đã dùng và đường dẫn đến trang gốc.
- **Nó bám sát chủ đề.** Nó trả lời về prepza và việc tuyển dụng với prepza, và từ chối những câu hỏi khác.

### 2. prepza trong Claude hoặc ChatGPT, qua MCP

Nếu bạn đã làm việc trong Claude hoặc ChatGPT, bạn có thể đưa prepza vào đó. Máy chủ MCP của prepza cung cấp cùng các công cụ như Mira, trợ lý tích hợp sẵn.

**Cách kết nối:**

1. Trong prepza, mở tab **Tích hợp** của một công ty và chọn **Ứng dụng AI**. Sao chép địa chỉ máy chủ: `https://prepza.ai/mcp`.
2. **Trong Claude:** mở Settings, rồi Connectors, và thêm một custom connector với địa chỉ đó. **Trong Claude Code:** chạy `claude mcp add --transport http prepza https://prepza.ai/mcp`. **Trong ChatGPT:** thêm nó dưới dạng custom connector trong phần cài đặt ứng dụng và connector.
3. Ứng dụng AI của bạn mở trang đăng nhập của prepza. Đăng nhập, kiểm tra ứng dụng nào đang yêu cầu, rồi chọn **Cho phép**. Để ứng dụng chỉ có thể đọc, hãy tắt **Cho phép thay đổi** trước.

Từ đó trở đi, hãy hỏi trong chat như khi hỏi một đồng nghiệp: "Trong prepza, ba ứng viên hàng đầu cho Product designer là ai?" Hầu hết ứng dụng AI sẽ hỏi bạn trước khi thay đổi, và cảnh báo trước bất kỳ thao tác nào không thể hoàn tác: prepza cho chúng biết thao tác nào thay đổi hoặc xóa dữ liệu.

**Những gì vẫn giống như trong ứng dụng:**

- **Quyền của bạn.** Nó hành động dưới danh nghĩa của bạn, ở mọi công ty bạn tham gia, với vai trò của bạn ở từng nơi.
- **Credit và giới hạn.** Mời một ứng viên tốn đúng như trong ứng dụng, và áp dụng cùng các giới hạn email.
- **Ghi nhận.** Mọi việc một ứng dụng AI làm thay bạn đều hiện trong nhật ký thao tác của công ty là đã thực hiện qua ứng dụng AI, từ duyệt chủ đề và xem kết quả đến cho thêm thời gian hay thu hồi ứng viên. Chủ sở hữu công ty xem nhật ký này trong thẻ **Nhật ký thao tác** của công ty.
- **Công ty quyết định.** Chủ sở hữu và quản trị viên có thể ngăn ứng dụng AI dùng dữ liệu của công ty bằng **Cho phép ứng dụng AI trong công ty này** trên trang ứng dụng AI của công ty.
- **Những gì nó không làm được.** Nó không thấy mật khẩu hay khóa API của bạn, và không thể xóa tài khoản của bạn hoặc một công ty. Những việc đó vẫn nằm trong ứng dụng.

**Để ngắt kết nối,** hãy gỡ connector trong ứng dụng AI của bạn, hoặc chọn **Ngắt kết nối** bên cạnh nó trong mục **Ứng dụng AI** ở tab Tích hợp. Kết nối dừng ngay lập tức.

**Ứng dụng khác và agent của riêng bạn.** [Tab MCP](/api-docs?tab=mcp) trong tài liệu cho nhà phát triển có các bước cho Gemini CLI, Cursor, VS Code và Le Chat, cùng các agent mẫu hoàn chỉnh bằng Python và TypeScript. Agent chạy trên máy chủ, không có ai để duyệt đăng nhập, sẽ dùng khóa API của công ty có quyền **Dùng với agent AI (MCP)**: agent chỉ hoạt động trong công ty đó, và chỉ với những công cụ mà các quyền khác của khóa cho phép.

### 3. Nền tảng riêng của bạn, qua API

Để tự động hóa không cần AI, prepza có API, được mô tả trong [tài liệu cho nhà phát triển](/api-docs).

1. Chủ sở hữu hoặc quản trị viên mở tab **Tích hợp** của một công ty, rồi **API**, và chọn **Khóa mới**. Đặt tên theo nền tảng sẽ dùng nó, chọn thời điểm hết hạn và chỉ đánh dấu những gì nó cần: khóa của bảng điều khiển chỉ đọc, khóa của trang tuyển dụng còn mời ứng viên. Sau này bạn có thể thêm hoặc bớt quyền. Khóa chỉ hiển thị một lần; hãy lưu ở nơi an toàn.
2. Nền tảng của bạn gửi yêu cầu bằng khóa đó: liệt kê các buổi phỏng vấn của công ty, liệt kê hoặc xem ứng viên cùng điểm, kết quả đạt hay không và các cảnh báo về tính trung thực, và mời ứng viên.
3. Thêm một **webhook**: một địa chỉ trên nền tảng của bạn mà prepza gọi tới, có chữ ký, khi một ứng viên bắt đầu, làm xong, không nhận được lời mời, hết hạn lời mời hoặc bị xóa khỏi buổi phỏng vấn, và khi một buổi phỏng vấn sẵn sàng, để bạn không phải hỏi đi hỏi lại. Trang API có thể gửi cho webhook này một sự kiện thử nghiệm và hiển thị nhật ký gửi của nó.

Mỗi ứng viên đi kèm đường dẫn đến toàn bộ kết quả trong prepza và, cho đến khi làm xong, đường dẫn mời riêng của họ, để nền tảng của bạn có thể gửi nó trong tin nhắn của chính mình nếu bạn muốn. Khi nền tảng của bạn đã biết ứng viên là ai, hãy mời họ mà không cần đăng nhập: prepza không gửi email nào, và ứng viên làm bài phỏng vấn từ đường dẫn mà không cần đăng nhập vào prepza, vì vậy chỉ gửi đường dẫn cho chính họ. Lời mời cũng có thể đưa ứng viên quay lại trang web của bạn (bất kỳ địa chỉ https nào) bằng một nút trên trang hoàn thành, và đặt giao diện sáng hoặc tối theo màu của công ty bạn. Với SDK của prepza, chính trang của bạn có thể hiển thị buổi phỏng vấn, nhưng chỉ trên các trang web mà công ty bạn cho phép trên trang API. API và webhook không phụ thuộc vào các trang web đó: thay vào đó, mỗi khóa có thể được giới hạn ở địa chỉ IP của các máy chủ của bạn. Việc xác minh chỉ thêm huy hiệu công ty đã xác minh.

Quy tắc vẫn như mọi nơi khác: điểm số hỗ trợ quyết định của con người, nên đừng tự động loại ứng viên dựa trên điểm.

## Khi nào dùng cách nào

Hãy bắt đầu từ việc ai làm và làm thường xuyên đến đâu.

| Tình huống của bạn | Dùng |
| --- | --- |
| Bạn đang ở trong prepza và muốn câu trả lời nhanh: ai đã đạt, ai chưa bắt đầu, còn bao nhiêu credit | Mira, trợ lý tích hợp sẵn |
| Bạn muốn thiết lập một việc bằng vài lời: buổi phỏng vấn từ mô tả công việc, điểm đạt, thêm thời gian | Mira, trợ lý tích hợp sẵn |
| Bạn đã làm việc cả ngày trong Claude hoặc ChatGPT và muốn có prepza ở đó | MCP |
| Công việc cần prepza cùng thứ khác: tài liệu của bạn, bản nháp email, một công cụ đã kết nối khác | MCP |
| Một recruiter đang di chuyển muốn kiểm tra quy trình tuyển dụng từ ứng dụng AI trên điện thoại | MCP |
| Trang tuyển dụng hoặc hệ thống nhân sự của bạn cần tự mời ứng viên, không cần ai nhấp | API |
| Kết quả cần về cơ sở dữ liệu hoặc bảng điều khiển của bạn ngay khi ứng viên làm xong | API, kèm webhook |
| ATS của bạn là một trong những hệ thống prepza kết nối được (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Không cách nào trong số này: hãy kết nối ATS ở tab Tích hợp. Xem [Cách kết nối bài kiểm tra kỹ năng với ATS](/guides/ats-integration-skills-tests) |

Một nguyên tắc đơn giản:

- **Một người hỏi và kiểm tra từng thay đổi:** Mira trong prepza, hoặc MCP nếu người đó làm việc cả ngày trong Claude hay ChatGPT.
- **Phần mềm tự hành động, lần nào cũng như nhau:** API.
- **Mới bắt đầu:** hãy thử Mira, trợ lý tích hợp sẵn, trước. Nó không cần thiết lập, và những gì bạn học được cũng áp dụng cho MCP.

Chúng cũng có thể dùng cùng nhau. Một nhóm có thể gửi lời mời từ hệ thống nhân sự qua API, trong khi các recruiter hỏi Mira hoặc chat AI của họ về kết quả.

## Để có kết quả tốt

- **Gọi đúng tên.** "Buổi phỏng vấn Senior Backend" hiệu quả hơn "buổi phỏng vấn đó".
- **Yêu cầu từng bước một** khi việc đó quan trọng. Kiểm tra kết quả, rồi mới yêu cầu bước tiếp theo.
- **Đọc yêu cầu phê duyệt trước khi cho phép.** Nó cho thấy chính xác những gì sẽ chạy.
- **Hỏi một con số từ đâu ra.** Một agent tốt có thể chỉ ra các ứng viên hoặc trang đứng sau con số đó.
- **Để con người quyết định.** Dùng agent AI để tìm, sắp xếp và chuẩn bị; còn quyết định là của bạn.

## Giá

Mira, kết nối MCP và API đều miễn phí. Bạn chỉ trả tiền cho ứng viên, như mọi khi: tính theo mỗi ứng viên trả lời ít nhất một câu hỏi, không có gói đăng ký. Xem [bảng giá](/pricing).

## Đọc thêm

- [Cách kết nối bài kiểm tra kỹ năng với ATS](/guides/ats-integration-skills-tests)
- [Phỏng vấn kỹ sư trong thời đại AI: nên kiểm tra gì bây giờ](/guides/interviewing-in-the-age-of-ai)
- [Dùng AI trong tuyển dụng có hợp pháp ở EU không?](/guides/is-ai-hiring-legal-in-the-eu)
