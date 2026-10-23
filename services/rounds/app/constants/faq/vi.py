# The FAQ in vi; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "prepza là gì?",
        "answer": "Một buổi phỏng vấn có tính giờ được tạo từ mô tả công việc của bạn, cho mọi vị trí. Dùng nó để sàng lọc ứng viên trước khi gặp họ, hoặc làm chính một bước tuyển dụng: dù cách nào, bạn cũng thấy ai thật sự thạo việc.",
    },
    {
        "key": "roles",
        "question": "Tôi có thể tuyển cho những vị trí nào?",
        "answer": "Mọi vị trí cần đến kiến thức: hỗ trợ khách hàng, bán hàng, tài chính, y tế, nghề kỹ thuật, kỹ sư, marketing và nhiều hơn nữa. Nếu bạn mô tả được công việc, prepza có thể tạo buổi phỏng vấn cho nó.",
    },
    {
        "key": "hiring",
        "question": "Cách hoạt động thế nào?",
        "answer": "Dán mô tả công việc trên trang chủ, đặt tên công ty và kiểm tra các chủ đề prepza đề xuất. Sau đó mời ứng viên: nhập email của họ, dán danh sách hoặc tải tệp lên. Ứng viên chưa bắt đầu sau vài ngày sẽ nhận một lời nhắc. Mỗi ứng viên có bộ câu hỏi riêng với thời gian giới hạn cho từng câu, và bạn thấy điểm cùng mọi câu trả lời của họ ngay khi họ làm xong.",
    },
    {
        "key": "link",
        "question": "Tôi có thể đặt buổi phỏng vấn vào tin tuyển dụng không?",
        "answer": "Có. Bật liên kết chia sẻ của buổi phỏng vấn trong thẻ Cài đặt và dán vào tin tuyển dụng. Ai mở liên kết sẽ đăng nhập và tham gia phỏng vấn, và mỗi người được tính phí như một ứng viên được mời. Liên kết tự tắt khi bạn đánh dấu buổi phỏng vấn là đã tuyển.",
    },
    {
        "key": "preview",
        "question": "Tôi có thể thử buổi phỏng vấn trước khi mời ai không?",
        "answer": "Có. Mở buổi phỏng vấn của bạn với tư cách ứng viên từ trang của nó, miễn phí: các lần xem trước không xuất hiện trong danh sách ứng viên hay trong thống kê câu hỏi. Bạn cũng có thể làm bất kỳ buổi phỏng vấn luyện tập miễn phí nào.",
    },
    {
        "key": "cheating",
        "question": "Ứng viên có thể dùng AI hoặc tra cứu đáp án không?",
        "answer": "Mỗi ứng viên nhận bộ câu hỏi ngẫu nhiên riêng theo thứ tự riêng, với [thời gian giới hạn cho từng câu](/guides/skills-test-timing-and-extra-time) do máy chủ của chúng tôi theo dõi, nên có rất ít thời gian để tra cứu đáp án hay hỏi AI. Bảng điểm cũng cho thấy khi ứng viên rời trang, sao chép văn bản hoặc trả lời quá nhanh để kịp đọc câu hỏi. Trước khi bắt đầu, mỗi ứng viên cũng xác nhận sẽ tự trả lời, không dùng công cụ AI hay nhờ người khác, và bảng điểm sẽ cho thấy điều đó.",
    },
    {
        "key": "cost",
        "question": "Chi phí bao nhiêu?",
        "answer": "Tạo buổi phỏng vấn là miễn phí. Mỗi ứng viên trả lời ít nhất một câu hỏi tốn {candidate} credit ({candidate_price}), và rẻ hơn với credit từ các lần nạp lớn hơn, xuống tới {cheapest_price}. Công ty đầu tiên của bạn nhận {company} credit miễn phí, đủ cho {company_candidates} ứng viên đầu tiên. [Trang bảng giá](/pricing) liệt kê mọi mức giá.",
    },
    {
        "key": "charged",
        "question": "Khi nào tôi bị tính phí cho một ứng viên?",
        "answer": "Nếu ứng viên đã trả lời ít nhất một câu hỏi: khi buổi phỏng vấn của họ kết thúc (họ tự hoàn thành, hoặc hết giờ trong lúc họ vắng mặt), hoặc khi bạn thu hồi ứng viên. Câu hỏi hết giờ mà chưa chọn câu trả lời thì không được tính. Tín dụng của họ được giữ lại khi bạn mời họ, và được hoàn lại nếu bạn thu hồi họ trước khi họ trả lời bất cứ câu nào, nếu họ không bao giờ bắt đầu, hoặc nếu buổi phỏng vấn của họ kết thúc mà không có câu nào được trả lời.",
    },
    {
        "key": "compare_hiring",
        "question": "Giá so với các công cụ đánh giá khác thế nào?",
        "answer": "Nhiều công cụ đánh giá được bán theo gói đăng ký theo tháng hoặc năm, phải trả dù bạn không kiểm tra ai. Với prepza, bạn chỉ trả theo ứng viên: {candidate} credit ({candidate_price}) mỗi ứng viên, không hợp đồng, không phí theo người dùng và không tốn phí tạo buổi phỏng vấn. Một công ty mời {example_candidates} ứng viên mỗi tháng trả khoảng {example_year_price} mỗi năm. Nếu bạn kiểm tra nhiều ứng viên mỗi tháng, gói đăng ký có thể rẻ hơn, nên hãy so sánh với số liệu của bạn.",
    },
    {
        "key": "expire",
        "question": "Credit có hết hạn không?",
        "answer": "Không. Credit không bao giờ hết hạn, và không có gói đăng ký trả phí. Nếu bạn bật tự động nạp (không bắt buộc), Paddle lưu thẻ của bạn dưới dạng một gói đăng ký {zero_price}; bạn chỉ trả cho những lần nạp thực tế.",
    },
    {
        "key": "currency",
        "question": "Tôi thanh toán bằng đồng tiền nào?",
        "answer": "Giá được tính bằng đồng tiền địa phương tại Canada, Úc, Israel, Ba Lan, Thụy Sĩ, Nhật Bản, Hàn Quốc, Đài Loan, Hồng Kông, Thái Lan, Singapore và Ấn Độ; bằng euro tại các nước còn lại của EU và tại Iceland, Liechtenstein và Na Uy; bằng bảng Anh tại Vương quốc Anh; và bằng đô la Mỹ ở những nơi khác. Tài khoản của bạn và mỗi công ty giữ đồng tiền của quốc gia nơi chúng được tạo, dù bạn đi đâu: đổi đồng tiền của bạn trong Cài đặt, và của một công ty bên cạnh nút Nạp credit của công ty đó (chủ sở hữu và quản trị viên). Các lần nạp của một công ty, kể cả tự động nạp, luôn được tính bằng đồng tiền của công ty.",
    },
    {
        "key": "refunds",
        "question": "Tôi có được hoàn tiền không?",
        "answer": "Có, với credit bạn mua trong 14 ngày gần nhất và chưa dùng: qua Paddle hoặc bằng cách viết cho chúng tôi. Credit miễn phí, như quà chào mừng, không được hoàn. Chi tiết có trong [điều khoản](/terms).",
    },
    {
        "key": "scorecards",
        "question": "Bảng điểm cho thấy gì?",
        "answer": 'Mọi câu trả lời, đúng hay sai và mất bao lâu. Điểm là tỷ lệ phần trăm điểm đạt được: mỗi câu hỏi có một điểm, câu "chọn tất cả đáp án đúng" được một phần điểm cho mỗi đáp án đúng đã chọn, và không được điểm nào nếu chọn một đáp án sai. Điểm hiện màu xanh hoặc đỏ so với điểm đạt bạn đặt cho buổi phỏng vấn. Bảng điểm cũng đánh dấu các câu trả lời quá nhanh để kịp đọc câu hỏi, những lần ứng viên rời trang và các lần định sao chép.',
    },
    {
        "key": "reports",
        "question": "Tôi có thể chia sẻ kết quả với quản lý tuyển dụng không?",
        "answer": "Có. Tải xuống báo cáo PDF cho một ứng viên hoặc cho tất cả ứng viên của một buổi phỏng vấn, gửi qua email thẳng từ prepza, hoặc gửi bản tóm tắt ngắn qua WhatsApp, Telegram, Viber hay LINE.",
    },
    {
        "key": "action_log",
        "question": "Tôi có thể xem ai đã làm gì trong công ty mình không?",
        "answer": "Có, nếu bạn là chủ sở hữu công ty. Tab Nhật ký thao tác của công ty liệt kê mọi việc các thành viên đã làm, mới nhất trước: mời hoặc xóa ứng viên, xem kết quả, thay đổi buổi phỏng vấn, nhóm, thanh toán và tích hợp, kèm theo ai đã làm, khi nào, và trợ lý, một ứng dụng AI hay API có làm thay họ không. Bạn có thể lọc theo thành viên, loại thao tác và ngày. Các thao tác được lưu trong 12 tháng.",
    },
    {
        "key": "integrations",
        "question": "prepza có hoạt động với ATS hoặc các công cụ khác của tôi không?",
        "answer": "Có, không mất thêm phí. Kết nối Workable, Greenhouse, Teamtailor, Recruitee hoặc Breezy HR trong tab Tích hợp của công ty bạn: ứng viên bạn chuyển sang một giai đoạn sẽ nhận buổi phỏng vấn, và kết quả được gửi lại ATS ([cách kết nối bài kiểm tra kỹ năng với ATS](/guides/ats-integration-skills-tests)). Slack có thể đăng thông báo của công ty vào một kênh, còn API cho phép nền tảng của riêng bạn tạo buổi phỏng vấn, mời và quản lý ứng viên, và nhận kết quả của họ, mỗi khóa API chỉ làm được những gì bạn đánh dấu cho nó; xem [Tài liệu API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Tôi có thể dùng prepza từ Claude, ChatGPT hoặc agent AI của riêng tôi không?",
        "answer": "Có. Thêm prepza vào Claude hoặc ChatGPT dưới dạng trình kết nối (các bước có trong tab Tích hợp của công ty bạn) rồi cho phép trên prepza. Sau đó, ứng dụng sẽ thay mặt bạn, với quyền của bạn, làm việc với các công ty, buổi phỏng vấn và kết quả của ứng viên; hầu hết ứng dụng sẽ hỏi bạn trước khi thay đổi bất cứ điều gì. Tài khoản hoặc công ty chỉ có thể xóa trong prepza. Dữ liệu ứng dụng đọc được sẽ đến nhà cung cấp của ứng dụng đó theo điều khoản của ứng dụng. Bạn có thể ngắt kết nối bất cứ lúc nào trong cùng tab. Các ứng dụng AI khác và agent do bạn tự xây dựng cũng kết nối được: [tab MCP](/api-docs?tab=mcp) trong tài liệu cho nhà phát triển có các bước và agent mẫu, và agent chạy trên máy chủ có thể đăng nhập bằng khóa API có quyền dành cho agent AI. [Hướng dẫn về agent AI, MCP và API](/guides/ai-agents-mcp-and-api) giải thích mỗi thứ dùng để làm gì.",
    },
    {
        "key": "candidates",
        "question": "Ứng viên thấy gì?",
        "answer": "Tên và logo công ty của bạn, với màu sắc và phông chữ của công ty bạn (đặt trong thẻ Thương hiệu), những gì cần biết trước khi bắt đầu, rồi lần lượt từng câu hỏi có giới hạn thời gian. Họ không bao giờ thấy điểm của mình hay câu trả lời có đúng không.",
    },
    {
        "key": "verified",
        "question": "Dấu xác minh có nghĩa là gì?",
        "answer": "Nghĩa là chủ sở hữu hoặc quản trị viên của công ty đã đăng nhập bằng email công việc trên website của công ty, như you@acme.com, và sau đó đội ngũ của chúng tôi đã xem xét công ty. Thêm website bằng nút Xác minh ở phần đầu trang công ty; dịch vụ email miễn phí không được tính. Trong khi chờ xem xét, nhóm của bạn thấy biểu tượng đồng hồ cạnh tên, và đổi tên công ty sẽ gửi công ty đi xem xét lại. Dấu xác minh hiện cạnh tên công ty của bạn, kể cả trong lời mời.",
    },
    {
        "key": "languages",
        "question": "Hỗ trợ những ngôn ngữ nào?",
        "answer": "{count} ngôn ngữ, cho trang web, các buổi phỏng vấn và email. Hãy chọn ngôn ngữ viết buổi phỏng vấn, bất kể mô tả công việc được viết bằng ngôn ngữ nào.",
    },
    {
        "key": "privacy",
        "question": "Mô tả công việc và câu trả lời được xử lý thế nào?",
        "answer": "Mô tả công việc được dùng để tạo các buổi phỏng vấn của công ty bạn, và câu trả lời của ứng viên để chấm điểm cho công ty bạn. Các câu hỏi prepza tạo cũng có thể được tái sử dụng trong các buổi phỏng vấn và luyện tập của công ty khác, mà không kèm bất cứ thông tin nào nhận dạng bạn, công ty của bạn hay bất kỳ ai khác; bạn có thể loại các câu hỏi của một buổi phỏng vấn khỏi việc này trong phần cài đặt của buổi phỏng vấn đó. prepza cũng học các mẫu chung, đã ẩn danh hóa, về chất lượng câu hỏi từ cách các câu hỏi được trả lời, để cải thiện cách tạo câu hỏi. [Chính sách quyền riêng tư](/privacy) giải thích chúng tôi lưu gì, trong bao lâu, và quyền của mọi người.",
    },
    {
        "key": "eu_ai_law",
        "question": "Dùng AI để sàng lọc ứng viên ở EU có hợp pháp không?",
        "answer": "Có, nhưng phải theo quy định. Theo Đạo luật AI của EU (EU AI Act), các công cụ chấm điểm ứng viên rất có thể thuộc nhóm rủi ro cao, với các nghĩa vụ áp dụng từ ngày 2/12/2027, và GDPR thì đã áp dụng: con người đưa ra quyết định tuyển dụng, ứng viên được thông báo rằng AI được sử dụng, và hồ sơ được lưu giữ. prepza hoạt động đúng như vậy: AI soạn câu hỏi, người trong công ty bạn xem xét kết quả và quyết định, và ứng viên được thông báo trước khi bắt đầu. Đây không phải là tư vấn pháp lý; [Dùng AI trong tuyển dụng có hợp pháp ở EU không?](/guides/is-ai-hiring-legal-in-the-eu) giải thích các quy định và mốc thời gian.",
    },
    {
        "key": "emails",
        "question": "prepza gửi những email nào, và làm sao để dừng nhận?",
        "answer": 'Email dịch vụ, như lời mời, báo cáo, vấn đề thanh toán và thay đổi điều khoản của chúng tôi, luôn được gửi. Những email còn lại, như tóm tắt hoạt động hằng ngày, lời nhắc và cập nhật sản phẩm, bạn chọn trong Cài đặt, mục Email, hoặc dừng bằng liên kết "Hủy đăng ký" trong mỗi email. Ứng viên có thể dừng nhận email từ công ty bạn, hoặc lời nhắc của một buổi phỏng vấn, bằng các liên kết trong lời mời và lời nhắc của họ.',
    },
    {
        "key": "delete",
        "question": "Tôi có thể xóa tài khoản không?",
        "answer": "Có, trong Cài đặt. Tài khoản và dữ liệu của bạn bị xóa, và trước đó bạn có thể tải xuống bản sao dữ liệu. Tin tức của prepza hiển thị trong thông báo của bạn, biểu tượng chuông ở trên cùng; tin quan trọng cũng được gửi qua email dưới dạng cập nhật sản phẩm, chỉ khi cài đặt đó đang bật.",
    },
    {
        "key": "report",
        "question": "Làm sao để báo cáo sự cố?",
        "answer": "Hãy viết cho chúng tôi qua [trang liên hệ](/contact) và dán ID của đối tượng liên quan: “sao chép id” nằm dưới tên của công ty, buổi phỏng vấn hoặc ứng viên, còn ID tài khoản của bạn nằm trong menu tài khoản và trong Cài đặt. Có ID, chúng tôi tìm thấy ngay.",
    },
]
