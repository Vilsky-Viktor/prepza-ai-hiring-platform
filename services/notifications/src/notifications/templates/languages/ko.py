# Email texts in Korean. Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = (
    "prepza에서 회사의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다."
)

TEXTS = {
    "candidate": {
        "subject": "{company} 면접 초대",
        "preheader": "prepza에서 “{title}” 면접을 보세요. {email}(으)로 로그인하면 시작할 수 있습니다.",
        "heading": "면접 초대",
        "lines": [
            "{company}에서 prepza의 “{title}” 면접에 초대했습니다.",
            "{email}(으)로 로그인하면 시작할 수 있습니다. 이 주소로만 면접을 볼 수 있으며, 기회는 한 번뿐입니다.",
        ],
        "button": "초대 열기",
    },
    "joined": {
        "subject": "“{title}” 면접 링크",
        "preheader": "면접을 떠나면 이 링크로 이어서 보세요. {email}(으)로 로그인하세요.",
        "heading": "면접 링크",
        "lines": [
            "prepza에서 {company}의 “{title}” 면접을 시작했습니다.",
            (
                "면접을 떠나면 이 링크로 이어서 보세요. {email}(으)로 로그인하면 됩니다. 시작할 때 사용한 링크를 {company}에서 비활성화해도 "
                "이 링크는 계속 작동합니다. 자리를 비운 동안에도 시간은 계속 흐릅니다."
            ),
        ],
        "button": "면접 이어서 보기",
        "footer": "이 주소로 prepza에서 면접이 시작되어 {email}(으)로 이 이메일이 발송되었습니다.",
    },
    "reminder": {
        "subject": "알림: {company} 면접",
        "preheader": "“{title}” 면접이 아직 열려 있습니다. {email}(으)로 로그인하면 시작할 수 있습니다.",
        "heading": "아직 응시하지 않은 면접이 있습니다",
        "lines": [
            "며칠 전 {company}에서 prepza의 “{title}” 면접에 초대했지만, 아직 시작하지 않으셨습니다.",
            "{email}(으)로 로그인하면 시작할 수 있습니다. 이 주소로만 면접을 볼 수 있으며, 기회는 한 번뿐입니다. 초대는 발송 후 30일이 지나면 만료됩니다.",
        ],
        "button": "초대 열기",
    },
    "member": {
        "subject": "prepza에서 {company} 팀에 참여하세요",
        "preheader": "{role}로 {company} 팀에 참여하세요. {email}(으)로 로그인하면 초대를 수락할 수 있습니다.",
        "heading": "팀 초대",
        "lines": [
            "{inviter}에게서 prepza의 {company} 팀에 {role}로 참여하라는 초대가 도착했습니다.",
            "{email}(으)로 로그인하면 초대를 수락할 수 있습니다. 이 주소로만 초대를 수락할 수 있습니다.",
        ],
        "button": "초대 열기",
        # The role's name as the lines use it.
        "roles": {"admin": "관리자", "viewer": "뷰어"},
    },
    "report": {
        "subject": "보고서: {candidate}",
        "preheader": "{candidate} 님이 {company}의 “{title}” 면접을 봤습니다. 보고서가 첨부되어 있습니다.",
        "heading": "지원자 보고서",
        "lines": [
            "{company}의 {sender} 님이 “{title}” 면접에 대한 {candidate} 님의 보고서를 공유했습니다.",
            "한 페이지 PDF로 첨부되어 있습니다: 전체 점수, 주제별 점수, 지원자의 브라우저에 기록된 내용. {sender} 님에게 답하려면 이 이메일에 회신하세요.",
        ],
        "button": "prepza 방문",
        "footer": "{sender} 님이 prepza에서 이 주소로 지원자 보고서를 공유하여 {email}(으)로 이 이메일이 발송되었습니다. 예상하지 못한 이메일이라면 무시하셔도 됩니다.",
    },
    "candidates": {
        "subject": "전체 지원자: {title}",
        "preheader": "{company}의 “{title}” 면접 전체 지원자입니다. 보고서가 첨부되어 있습니다.",
        "heading": "전체 지원자 보고서",
        "lines": [
            "{company}의 {sender} 님이 “{title}” 면접의 전체 지원자 보고서를 공유했습니다.",
            "PDF로 첨부되어 있습니다: 각 지원자의 점수, 진행률, 브라우저에 기록된 내용이 점수가 높은 순으로 정리되어 있습니다. {sender} 님에게 답하려면 이 이메일에 회신하세요.",
        ],
        "button": "prepza 방문",
        "footer": "{sender} 님이 prepza에서 이 주소로 전체 지원자 보고서를 공유하여 {email}(으)로 이 이메일이 발송되었습니다. 예상하지 못한 이메일이라면 무시하셔도 됩니다.",
    },
    "digest": {
        "subject": "prepza 활동 요약",
        "preheader": "지난 24시간 동안 회사에서 있었던 일입니다.",
        "heading": "활동 요약",
        "lines": [
            "지난 24시간 동안 prepza의 회사에서 있었던 일입니다.",
        ],
        "rows": {
            "candidate_finished": "면접을 완료한 지원자: {count} · “{title}”",
            "invite_undelivered": "전달되지 않은 초대: {count} · “{title}”",
            "ats_not_invited": "초대되지 않은 {ats} 지원자: {count}",
            "interview_ready": "준비된 면접: “{title}”",
            "note_added": "팀의 새 메모: {count} · “{title}”",
            "note": "{author}: “{excerpt}”",
            "note_by_former": "이전 멤버: “{excerpt}”",
        },
        "button": "prepza 열기",
        "footer": "prepza에서 회사 멤버로 활동 요약을 받고 있으므로 {email}(으)로 이 이메일이 발송되었습니다.",
    },
    "low_credits": {
        "subject": "크레딧이 곧 소진됩니다",
        "preheader": "지원자를 계속 초대하려면 충전하세요.",
        "heading": "크레딧이 곧 소진됩니다",
        "lines": [
            "이 회사들은 지원자를 한 명 더 초대할 크레딧이 부족합니다. 지원자를 계속 초대하려면 충전하세요.",
        ],
        "rows": {
            "company": "{company} · 사용 가능한 크레딧: {available}",
        },
        "button": "충전",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "지원자를 기다리고 있습니다",
        "preheader": "이메일로 지원자를 초대하거나 면접 링크를 공유하세요.",
        "heading": "지원자를 기다리고 있습니다",
        "lines": [
            "이 면접들은 며칠 전에 준비되었지만 아직 아무도 초대되지 않았습니다. 이메일로 지원자를 초대하거나 면접 링크를 공유하세요.",
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "지원자 초대",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "주제 검토를 기다리고 있습니다",
        "preheader": "주제를 확정하면 문제가 만들어집니다.",
        "heading": "주제 검토",
        "lines": [
            "시작하신 면접의 주제가 검토를 기다리고 있습니다. 주제를 확정하면 문제가 만들어집니다. 14일 동안 검토하지 않으면 취소됩니다.",
        ],
        "rows": {
            "interview": "{company} · 대기 일수: {days}",
        },
        "button": "주제 검토하기",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "{date}부터 이용약관 변경",
        "preheader": "새 이용약관은 {date}부터 적용됩니다.",
        "heading": "이용약관이 변경됩니다",
        "lines": [
            "prepza 이용약관의 새 버전을 게시했습니다. {date}부터 적용되며, 그 전까지는 현재 이용약관이 적용됩니다.",
            "{date} 이후에 prepza를 이용하면 새 이용약관에 동의한 것으로 간주됩니다. 동의하지 않으면 그 전에 설정에서 계정을 삭제할 수 있습니다.",
        ],
        "button": "새 이용약관 보기",
        "footer": "prepza 계정이 있으므로 {email}(으)로 이 이메일이 발송되었습니다. 이용약관에 관한 안내이므로 이메일 설정과 관계없이 발송됩니다.",
    },
    "legal_privacy": {
        "subject": "{date}부터 개인정보처리방침 변경",
        "preheader": "새 개인정보처리방침은 {date}부터 적용됩니다.",
        "heading": "개인정보처리방침이 변경됩니다",
        "lines": [
            "데이터 이용 방식을 설명하는 prepza 개인정보처리방침의 새 버전을 게시했습니다. {date}부터 적용되며, 그 전까지는 현재 버전이 적용됩니다.",
            "언제든지 설정에서 데이터를 다운로드하거나 삭제할 수 있습니다.",
        ],
        "button": "새 개인정보처리방침 보기",
        "footer": "prepza 계정이 있으므로 {email}(으)로 이 이메일이 발송되었습니다. 데이터 이용 방식에 관한 안내이므로 이메일 설정과 관계없이 발송됩니다.",
    },
    "legal_dpa": {
        "subject": "{date}부터 데이터 처리 계약 변경",
        "preheader": "새 계약은 {date}부터 회사에 적용됩니다.",
        "heading": "데이터 처리 계약이 변경됩니다",
        "lines": [
            "prepza가 지원자 데이터를 처리하는 근거인 데이터 처리 계약의 새 버전을 게시했습니다. {date}부터 적용되며, 그 전까지는 현재 버전이 적용됩니다.",
            "데이터 보호와 관련된 합리적인 이유로 이의가 있는 회사는 그 전에 prepza 이용을 중단하고 회사를 삭제할 수 있습니다.",
        ],
        "button": "새 계약 보기",
        "footer": "prepza에서 회사의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사와의 계약에 관한 안내이므로 이메일 설정과 관계없이 발송됩니다.",
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza 열기",
        "footer": "prepza의 제품 업데이트 및 소식을 받기로 선택하셨으므로 {email}(으)로 이 이메일이 발송되었습니다.",
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza 열기",
        "footer": "prepza의 혜택 및 프로모션을 받기로 선택하셨으므로 {email}(으)로 이 이메일이 발송되었습니다.",
    },
    # An important notice: a service email about prepza itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "prepza 열기",
        "footer": (
            "prepza 계정이 있으므로 {email}(으)로 이 이메일이 발송되었습니다. 보안이나 가용성 등 서비스에 관한 중요 공지이므로 이메일 설정과"
            " 관계없이 발송됩니다."
        ),
    },
    "top_up_failed": {
        "subject": "자동 충전 실패: {company}",
        "preheader": "카드 결제에 실패했습니다. 지원자를 계속 초대하려면 충전하세요.",
        "heading": "자동 충전 실패",
        "lines": [
            "{company}의 자동 충전 중 카드 결제에 실패하여 크레딧이 추가되지 않았습니다.",
            "지원자를 계속 초대하려면 충전하세요. 자동 충전은 나중에 카드 결제를 다시 시도합니다.",
        ],
        "button": "충전",
        "footer": (
            "prepza에서 {company}의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사 결제에 관한 내용이므로 "
            "이메일 설정과 관계없이 발송됩니다."
        ),
    },
    "top_up_paused": {
        "subject": "자동 충전 일시 중지: {company}",
        "preheader": "카드가 거절되었습니다. 자동 충전을 다시 켜려면 카드를 업데이트하세요.",
        "heading": "자동 충전 일시 중지",
        "lines": [
            "{company}의 자동 충전 카드가 거절되었고 다시 시도해도 해결되지 않아, 자동 충전을 일시 중지했으며 이 카드로 결제하지 않습니다.",
            "자동 충전을 다시 켜려면 결제 페이지에서 카드를 업데이트하세요. 그때까지 지원자를 계속 초대하려면 직접 충전하세요.",
        ],
        "button": "카드 업데이트",
        "footer": (
            "prepza에서 {company}의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사 결제에 관한 내용이므로 "
            "이메일 설정과 관계없이 발송됩니다."
        ),
    },
    "top_up_on": {
        "subject": "자동 충전 켜짐: {company}",
        "preheader": "사용 가능한 크레딧이 {threshold} 미만이 될 때마다 {price}(세금 별도)가 결제됩니다.",
        "heading": "자동 충전이 켜졌습니다",
        "lines": [
            (
                "{company}의 자동 충전이 켜졌습니다. 사용 가능한 크레딧이 {threshold} 미만이 될 때마다 자동 충전이 꺼질 때까지 저장된 "
                "카드에서 {price} 결제가 이루어지며, 해당되는 경우 부가가치세(VAT) 또는 판매세가 추가됩니다."
            ),
            "결제할 때마다 회사의 소유자와 관리자에게 이메일로 알리며, 당사의 재판매자인 Paddle이 영수증을 이메일로 보냅니다.",
            "끄려면 결제 페이지에서 자동 충전을 열고 ‘끄기’를 선택하세요. 즉시 중지되며 더 이상 결제되지 않습니다.",
        ],
        "button": "결제 페이지 열기",
        "footer": (
            "prepza에서 {company}의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사 결제에 관한 내용이므로 "
            "이메일 설정과 관계없이 발송됩니다."
        ),
    },
    "top_up_charged": {
        "subject": "자동 충전 결제: {company}",
        "preheader": "{date}에 {credits} 크레딧 충전, {price} 결제.",
        "heading": "자동 충전으로 카드가 결제되었습니다",
        "lines": [
            (
                "{date}에 {company}의 자동 충전으로 카드에서 {price}(세금 포함)가 결제되었고 {credits} 크레딧이 추가되었습니다. 현재 "
                "{company}의 사용 가능한 크레딧은 {available}입니다."
            ),
            "당사의 재판매자인 Paddle이 영수증을 이메일로 보냅니다.",
            "이 결제를 중지하려면 결제 페이지에서 자동 충전을 열고 ‘끄기’를 선택하세요. 즉시 중지되며 더 이상 결제되지 않습니다.",
        ],
        "button": "결제 페이지 열기",
        "footer": (
            "prepza에서 {company}의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사 결제에 관한 내용이므로 "
            "이메일 설정과 관계없이 발송됩니다."
        ),
    },
    "top_up_price_change": {
        "subject": "{company} 자동 충전 가격 변경",
        "preheader": "{date}부터 자동 충전 1회 가격이 {price}에서 {new_price}(으)로 바뀝니다.",
        "heading": "자동 충전 가격 변경 안내",
        "lines": [
            (
                "{date}부터 {company}의 자동 충전 1회 가격이 {price}에서 {new_price}(으)로 바뀌며, 해당되는 경우 "
                "부가가치세(VAT) 또는 판매세가 추가됩니다. 충전으로 초대할 수 있는 지원자 수는 같습니다."
            ),
            "그 전의 결제는 계속 {price}입니다. 다른 금액을 원하시면 {date} 전에 결제 페이지에서 자동 충전을 변경하거나 끄세요.",
        ],
        "button": "결제 페이지 열기",
        "footer": (
            "prepza에서 {company}의 소유자 또는 관리자이므로 {email}(으)로 이 이메일이 발송되었습니다. 회사 결제에 관한 내용이므로 "
            "이메일 설정과 관계없이 발송됩니다."
        ),
    },
    "footer": "prepza에서 누군가 이 주소를 초대하여 {email}(으)로 이 이메일이 발송되었습니다. 예상하지 못한 이메일이라면 무시하셔도 됩니다.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza는 {company}을(를) 인증하지 않았습니다.",
    "paste_link": "또는 이 링크를 브라우저에 붙여 넣으세요",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "수신 거부",
    "email_settings": "이메일 설정 변경",
    "stop_reminders": "이 면접의 알림 받지 않기",
    "stop_company": "{company}의 이메일 받지 않기",
    # Who runs prepza, at the end of every email.
    "operator": "prepza는 {name}({address})이(가) 운영합니다.",
}
