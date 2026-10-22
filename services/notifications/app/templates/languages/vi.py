# Email texts in Vietnamese. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "Email này được gửi đến {email} vì bạn là chủ sở hữu hoặc quản trị viên của một công ty"
    " trên prepza."
)

TEXTS = {
    "candidate": {
        "subject": "Lời mời phỏng vấn từ {company}",
        "preheader": "Tham gia phỏng vấn “{title}” trên prepza. Đăng nhập bằng {email} để bắt đầu.",
        "heading": "Lời mời phỏng vấn",
        "lines": [
            "{company} mời bạn tham gia buổi phỏng vấn “{title}” trên prepza.",
            (
                "Đăng nhập bằng {email} để bắt đầu. Chỉ địa chỉ này mới có thể tham "
                "gia phỏng vấn và bạn chỉ có một lần làm bài."
            ),
        ],
        "button": "Mở lời mời",
    },
    "joined": {
        "subject": "Liên kết của bạn tới “{title}”",
        "preheader": "Nếu rời buổi phỏng vấn, hãy tiếp tục bằng liên kết này. Đăng nhập bằng {email}.",
        "heading": "Liên kết phỏng vấn của bạn",
        "lines": [
            "Bạn đã bắt đầu buổi phỏng vấn “{title}” của {company} trên prepza.",
            (
                "Nếu rời đi, hãy tiếp tục bằng liên kết này: đăng nhập bằng {email}. Liên kết "
                "vẫn hoạt động ngay cả khi {company} tắt liên kết bạn đã dùng để bắt đầu. Thời "
                "gian vẫn tiếp tục chạy khi bạn rời đi."
            ),
        ],
        "button": "Tiếp tục phỏng vấn",
        "footer": (
            "Email này được gửi đến {email} vì một buổi phỏng vấn trên prepza đã được bắt đầu "
            "bằng địa chỉ này."
        ),
    },
    "reminder": {
        "subject": "Nhắc nhở: buổi phỏng vấn với {company}",
        "preheader": "“{title}” vẫn đang mở. Đăng nhập bằng {email} để bắt đầu.",
        "heading": "Buổi phỏng vấn đang chờ bạn",
        "lines": [
            (
                "{company} đã mời bạn tham gia buổi phỏng vấn “{title}” trên prepza vài ngày "
                "trước, và bạn vẫn chưa bắt đầu."
            ),
            (
                "Đăng nhập bằng {email} để bắt đầu. Chỉ địa chỉ này mới có thể tham gia phỏng "
                "vấn và bạn chỉ có một lần làm bài. Lời mời hết hạn sau 30 ngày kể từ khi gửi."
            ),
        ],
        "button": "Mở lời mời",
    },
    "member": {
        "subject": "Tham gia {company} trên prepza",
        "preheader": (
            "Tham gia nhóm {company} với vai trò {role}. Đăng nhập bằng {email} để chấp nhận lời "
            "mời."
        ),
        "heading": "Lời mời tham gia nhóm",
        "lines": [
            "{inviter} mời bạn tham gia nhóm {company} trên prepza với vai trò {role}.",
            (
                "Đăng nhập bằng {email} để chấp nhận lời mời. Chỉ địa chỉ này mới có thể chấp nhận "
                "lời mời."
            ),
        ],
        "button": "Mở lời mời",
        # The role's name as the lines use it.
        "roles": {"admin": "quản trị viên", "viewer": "người xem"},
    },
    "report": {
        "subject": "Báo cáo: {candidate}",
        "preheader": "{candidate} đã tham gia phỏng vấn “{title}” tại {company}. Báo cáo được đính kèm.",
        "heading": "Báo cáo ứng viên",
        "lines": [
            (
                "{sender} từ {company} đã chia sẻ báo cáo của {candidate} cho buổi phỏng vấn "
                "“{title}”."
            ),
            (
                "Báo cáo được đính kèm dưới dạng PDF một trang: điểm tổng, điểm từng chủ đề và "
                "những gì trình duyệt của ứng viên ghi nhận. Trả lời email này để phản hồi {sender}."
            ),
        ],
        "button": "Truy cập prepza",
        "footer": "Email này được gửi đến {email} vì {sender} đã chia sẻ một báo cáo ứng viên "
        "với địa chỉ này trên prepza. Nếu bạn không mong đợi email này, bạn có thể bỏ qua.",
    },
    "candidates": {
        "subject": "Tất cả ứng viên: {title}",
        "preheader": "Tất cả ứng viên của buổi phỏng vấn “{title}” tại {company}. Báo cáo được đính kèm.",
        "heading": "Báo cáo ứng viên",
        "lines": [
            (
                "{sender} từ {company} đã chia sẻ báo cáo tất cả ứng viên cho buổi phỏng vấn "
                "“{title}”."
            ),
            (
                "Báo cáo được đính kèm dưới dạng PDF: điểm, tiến độ của từng ứng viên và những gì "
                "trình duyệt của họ ghi nhận, xếp từ cao xuống thấp. Trả lời email này để phản hồi "
                "{sender}."
            ),
        ],
        "button": "Truy cập prepza",
        "footer": "Email này được gửi đến {email} vì {sender} đã chia sẻ một báo cáo ứng viên "
        "với địa chỉ này trên prepza. Nếu bạn không mong đợi email này, bạn có thể bỏ qua.",
    },
    "digest": {
        "subject": "Tóm tắt hoạt động của bạn trên prepza",
        "preheader": "Những gì đã diễn ra ở các công ty của bạn trong 24 giờ qua.",
        "heading": "Tóm tắt hoạt động của bạn",
        "lines": [
            "Đây là những gì đã diễn ra ở các công ty của bạn trên prepza trong 24 giờ qua.",
        ],
        "rows": {
            "candidate_finished": "Ứng viên đã hoàn thành: {count} · “{title}”",
            "invite_undelivered": "Lời mời chưa được gửi đến: {count} · “{title}”",
            "ats_not_invited": "Ứng viên từ {ats} chưa được mời: {count}",
            "interview_ready": "Buổi phỏng vấn đã sẵn sàng: “{title}”",
        },
        "button": "Mở prepza",
        "footer": (
            "Email này được gửi đến {email} vì bạn là thành viên của một công ty trên "
            "prepza và nhận tóm tắt hoạt động của công ty đó."
        ),
    },
    "low_credits": {
        "subject": "Credit của bạn sắp hết",
        "preheader": "Hãy nạp thêm để tiếp tục mời ứng viên.",
        "heading": "Credit sắp hết",
        "lines": [
            (
                "Các công ty này không còn đủ credit để mời thêm một ứng viên. Hãy nạp thêm"
                " để tiếp tục mời ứng viên."
            ),
        ],
        "rows": {
            "company": "{company} · credit khả dụng: {available}",
        },
        "button": "Nạp credit",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "Đang chờ ứng viên",
        "preheader": "Mời ứng viên qua email hoặc chia sẻ liên kết của buổi phỏng vấn.",
        "heading": "Đang chờ ứng viên",
        "lines": [
            (
                "Các buổi phỏng vấn này đã sẵn sàng được vài ngày nhưng chưa có ai được "
                "mời. Hãy mời ứng viên qua email hoặc chia sẻ liên kết của buổi phỏng vấn."
            ),
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "Mời ứng viên",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "Các chủ đề đang chờ bạn duyệt",
        "preheader": "Xác nhận các chủ đề để câu hỏi được tạo.",
        "heading": "Duyệt các chủ đề",
        "lines": [
            (
                "Các chủ đề của những buổi phỏng vấn bạn đã bắt đầu đang chờ bạn duyệt. Khi"
                " bạn xác nhận, câu hỏi sẽ được tạo. Phần duyệt để mở quá 14 ngày sẽ bị "
                "hủy."
            ),
        ],
        "rows": {
            "interview": "{company} · số ngày chờ: {days}",
        },
        "button": "Duyệt các chủ đề",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "Điều khoản sử dụng mới từ {date}",
        "preheader": "Điều khoản sử dụng mới có hiệu lực từ {date}.",
        "heading": "Chúng tôi cập nhật điều khoản sử dụng",
        "lines": [
            (
                "Chúng tôi đã công bố phiên bản mới của điều khoản sử dụng prepza. Phiên bản này "
                "có hiệu lực từ {date}; trước đó, điều khoản hiện hành vẫn được áp dụng."
            ),
            (
                "Nếu bạn tiếp tục dùng prepza sau {date}, nghĩa là bạn chấp nhận điều khoản mới. "
                "Nếu không đồng ý, bạn có thể xóa tài khoản trong Cài đặt trước ngày đó."
            ),
        ],
        "button": "Đọc điều khoản mới",
        "footer": (
            "Email này được gửi đến {email} vì bạn có tài khoản prepza. Đây là thông báo về "
            "điều khoản sử dụng của chúng tôi nên luôn được gửi, bất kể cài đặt email của "
            "bạn."
        ),
    },
    "legal_privacy": {
        "subject": "Chính sách quyền riêng tư mới từ {date}",
        "preheader": "Chính sách quyền riêng tư mới có hiệu lực từ {date}.",
        "heading": "Chúng tôi cập nhật chính sách quyền riêng tư",
        "lines": [
            (
                "Chúng tôi đã công bố phiên bản mới của chính sách quyền riêng tư prepza, cho "
                "biết cách chúng tôi sử dụng dữ liệu của bạn. Phiên bản này có hiệu lực từ "
                "{date}; trước đó, phiên bản hiện hành vẫn được áp dụng."
            ),
            "Bạn có thể tải xuống hoặc xóa dữ liệu của mình trong Cài đặt bất cứ lúc nào.",
        ],
        "button": "Đọc chính sách quyền riêng tư mới",
        "footer": (
            "Email này được gửi đến {email} vì bạn có tài khoản prepza. Đây là thông báo về "
            "cách chúng tôi sử dụng dữ liệu của bạn nên luôn được gửi, bất kể cài đặt email "
            "của bạn."
        ),
    },
    "legal_dpa": {
        "subject": "Thỏa thuận xử lý dữ liệu mới từ {date}",
        "preheader": "Thỏa thuận mới áp dụng cho công ty bạn từ {date}.",
        "heading": "Chúng tôi cập nhật thỏa thuận xử lý dữ liệu",
        "lines": [
            (
                "Chúng tôi đã công bố phiên bản mới của thỏa thuận xử lý dữ liệu mà prepza dựa "
                "vào để xử lý dữ liệu ứng viên của bạn. Phiên bản này có hiệu lực từ {date}; "
                "trước đó, phiên bản hiện hành vẫn được áp dụng."
            ),
            (
                "Công ty nào phản đối vì lý do bảo vệ dữ liệu hợp lý có thể ngừng sử dụng prepza "
                "và xóa công ty của mình trước ngày đó."
            ),
        ],
        "button": "Đọc thỏa thuận mới",
        "footer": (
            "Email này được gửi đến {email} vì bạn là chủ sở hữu hoặc quản trị viên của một "
            "công ty trên prepza. Đây là thông báo về thỏa thuận giữa chúng tôi và công ty "
            "bạn nên luôn được gửi, bất kể cài đặt email của bạn."
        ),
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Mở prepza",
        "footer": (
            "Email này được gửi đến {email} vì bạn đã chọn nhận cập nhật sản phẩm và tin tức từ"
            " prepza."
        ),
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "Mở prepza",
        "footer": "Email này được gửi đến {email} vì bạn đã chọn nhận ưu đãi và khuyến mãi từ prepza.",
    },
    "top_up_failed": {
        "subject": "Tự động nạp thất bại: {company}",
        "preheader": "Không trừ tiền được từ thẻ. Hãy nạp thêm để tiếp tục mời ứng viên.",
        "heading": "Tự động nạp không thành công",
        "lines": [
            (
                "Tự động nạp không trừ tiền được từ thẻ của {company}, nên chưa có credit "
                "nào được thêm."
            ),
            "Hãy nạp thêm để tiếp tục mời ứng viên. Tự động nạp sẽ thử lại thẻ sau.",
        ],
        "button": "Nạp credit",
        "footer": (
            "Email này được gửi đến {email} vì bạn là chủ sở hữu hoặc quản trị viên của "
            "{company} trên prepza. Email liên quan đến việc thanh toán của công ty bạn nên"
            " luôn được gửi, bất kể cài đặt email của bạn."
        ),
    },
    "top_up_paused": {
        "subject": "Tự động nạp đã tạm dừng: {company}",
        "preheader": "Thẻ bị từ chối. Hãy cập nhật thẻ để bật lại tự động nạp.",
        "heading": "Tự động nạp đã tạm dừng",
        "lines": [
            (
                "Thẻ dùng cho tự động nạp của {company} bị từ chối và thử lại cũng không giúp "
                "được, nên tự động nạp đã tạm dừng và sẽ không trừ tiền từ thẻ này."
            ),
            (
                "Hãy cập nhật thẻ trên trang thanh toán để bật lại tự động nạp. Trong lúc đó, hãy "
                "nạp thủ công để tiếp tục mời ứng viên."
            ),
        ],
        "button": "Cập nhật thẻ",
        "footer": (
            "Email này được gửi đến {email} vì bạn là chủ sở hữu hoặc quản trị viên của "
            "{company} trên prepza. Email liên quan đến việc thanh toán của công ty bạn nên"
            " luôn được gửi, bất kể cài đặt email của bạn."
        ),
    },
    "top_up_price_change": {
        "subject": "Giá tự động nạp mới cho {company}",
        "preheader": "Từ {date}, mỗi lần tự động nạp có giá {new_price} thay vì {price}.",
        "heading": "Giá tự động nạp sẽ thay đổi",
        "lines": [
            (
                "Từ {date}, mỗi lần tự động nạp cho {company} có giá {new_price} thay vì {price}, "
                "cộng thêm VAT hoặc thuế bán hàng nếu có. Số ứng viên vẫn như cũ."
            ),
            (
                "Các lần trừ tiền trước ngày đó vẫn có giá {price}. Nếu bạn muốn số tiền khác, "
                "hãy thay đổi hoặc tắt tự động nạp trên trang thanh toán trước {date}."
            ),
        ],
        "button": "Mở trang thanh toán",
        "footer": (
            "Email này được gửi đến {email} vì bạn là chủ sở hữu hoặc quản trị viên của "
            "{company} trên prepza. Email liên quan đến việc thanh toán của công ty bạn nên"
            " luôn được gửi, bất kể cài đặt email của bạn."
        ),
    },
    "footer": "Email này được gửi đến {email} vì có người đã mời địa chỉ này trên prepza. Nếu "
    "bạn không mong đợi email này, bạn có thể bỏ qua.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza chưa xác minh {company}.",
    "paste_link": "Hoặc dán liên kết này vào trình duyệt của bạn",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "Hủy đăng ký",
    "email_settings": "Thay đổi cài đặt email",
    "stop_reminders": "Đừng gửi lời nhắc về buổi phỏng vấn này cho tôi",
    "stop_company": "Đừng gửi email từ {company} cho tôi",
    # Who runs prepza, at the end of every email.
    "operator": "prepza do {name}, {address} vận hành.",
}
