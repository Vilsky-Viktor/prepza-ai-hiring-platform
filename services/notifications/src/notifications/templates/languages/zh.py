# Email texts in Chinese (Simplified). Values are filled in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = "这封邮件发送到 {email}，因为你是 prepza 上某家公司的所有者或管理员。"

TEXTS = {
    "candidate": {
        "subject": "{company} 的面试邀请",
        "preheader": "在 prepza 上完成“{title}”。使用 {email} 登录即可开始。",
        "heading": "面试邀请",
        "lines": [
            "{company} 邀请你在 prepza 上参加“{title}”面试。",
            "使用 {email} 登录即可开始。只有这个邮箱地址可以参加面试，并且只有一次机会。",
        ],
        "button": "打开邀请",
    },
    "joined": {
        "subject": "“{title}”的链接",
        "preheader": "如果离开面试，请用这个链接继续。使用 {email} 登录。",
        "heading": "你的面试链接",
        "lines": [
            "你已在 prepza 上开始 {company} 的“{title}”面试。",
            "如果离开，请用这个链接继续：使用 {email} 登录。即使 {company} 关闭了你开始时使用的链接，它也依然有效。你离开期间，时间会继续计算。",
        ],
        "button": "继续面试",
        "footer": "这封邮件发送到 {email}，因为有人用这个地址在 prepza 上开始了面试。",
    },
    "reminder": {
        "subject": "提醒：你在 {company} 的面试",
        "preheader": "“{title}”仍然开放。使用 {email} 登录即可开始。",
        "heading": "你的面试尚未开始",
        "lines": [
            "{company} 几天前邀请你在 prepza 上参加“{title}”面试，你还没有开始。",
            "使用 {email} 登录即可开始。只有这个邮箱地址可以参加面试，并且只有一次机会。邀请在发送 30 天后失效。",
        ],
        "button": "打开邀请",
    },
    "member": {
        "subject": "加入 prepza 上的 {company}",
        "preheader": "以{role}身份加入 {company} 团队。使用 {email} 登录即可接受邀请。",
        "heading": "团队邀请",
        "lines": [
            "{inviter} 邀请你以{role}身份加入 prepza 上的 {company} 团队。",
            "使用 {email} 登录即可接受邀请。只有这个邮箱地址可以接受邀请。",
        ],
        "button": "打开邀请",
        # The role's name as the lines use it.
        "roles": {"admin": "管理员", "viewer": "查看者"},
    },
    "report": {
        "subject": "报告：{candidate}",
        "preheader": "{candidate} 参加了 {company} 的“{title}”。报告已附上。",
        "heading": "候选人报告",
        "lines": [
            "{company} 的 {sender} 分享了 {candidate} 在“{title}”面试中的报告。",
            "报告以一页 PDF 附上：总成绩、每个主题的分数，以及候选人浏览器记录的情况。直接回复此邮件即可回复 {sender}。",
        ],
        "button": "访问 prepza",
        "footer": "这封邮件发送到 {email}，因为 {sender} 在 prepza 上与这个地址分享了一份候选人报告。如果这封邮件与你无关，可以忽略。",
    },
    "candidates": {
        "subject": "全部候选人：{title}",
        "preheader": "{company} 的“{title}”的全部候选人。报告已附上。",
        "heading": "全部候选人报告",
        "lines": [
            "{company} 的 {sender} 分享了“{title}”面试全部候选人的报告。",
            "报告以 PDF 附上：每位候选人的成绩、进度以及浏览器记录的情况，按成绩从高到低排列。直接回复此邮件即可回复 {sender}。",
        ],
        "button": "访问 prepza",
        "footer": "这封邮件发送到 {email}，因为 {sender} 在 prepza 上与这个地址分享了一份全部候选人的报告。如果这封邮件与你无关，可以忽略。",
    },
    "digest": {
        "subject": "你在 prepza 的动态摘要",
        "preheader": "过去 24 小时你的公司里发生的事。",
        "heading": "你的动态摘要",
        "lines": [
            "以下是过去 24 小时你在 prepza 上的公司里发生的事。",
        ],
        "rows": {
            "candidate_finished": "已完成面试的候选人：{count} · “{title}”",
            "invite_undelivered": "未送达的邀请：{count} · “{title}”",
            "ats_not_invited": "未被邀请的 {ats} 候选人：{count}",
            "interview_ready": "已就绪的面试：“{title}”",
            "note_added": "团队的新备注：{count} · “{title}”",
            "note": "{author}：“{excerpt}”",
            "note_by_former": "前成员：“{excerpt}”",
        },
        "button": "打开 prepza",
        "footer": "这封邮件发送到 {email}，因为你是 prepza 上某家公司的成员，并接收它的动态摘要。",
    },
    "low_credits": {
        "subject": "你的点数即将用完",
        "preheader": "充值后才能继续邀请候选人。",
        "heading": "点数即将用完",
        "lines": [
            "这些公司的点数已不够再邀请一位候选人。充值后才能继续邀请候选人。",
        ],
        "rows": {
            "company": "{company} · 可用点数：{available}",
        },
        "button": "充值",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "等待候选人",
        "preheader": "通过邮件邀请候选人，或分享面试链接。",
        "heading": "等待候选人",
        "lines": [
            "这些面试已就绪好几天了，但还没有邀请任何人。通过邮件邀请候选人，或分享面试链接。",
        ],
        "rows": {
            "interview": "“{title}” · {company}",
        },
        "button": "邀请候选人",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "你的主题正在等待审阅",
        "preheader": "确认主题后即会生成题目。",
        "heading": "审阅你的主题",
        "lines": [
            "你开始创建的面试的主题正在等待你审阅。确认后即会生成题目。审阅保持未完成满 14 天将被取消。",
        ],
        "rows": {
            "interview": "{company} · 已等待天数：{days}",
        },
        "button": "审阅主题",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "服务条款将于 {date} 更新",
        "preheader": "新的服务条款自 {date} 起生效。",
        "heading": "我们正在更新服务条款",
        "lines": [
            "我们发布了新版 prepza 服务条款，自 {date} 起生效；在此之前，现行条款继续适用。",
            "在 {date} 之后继续使用 prepza，即表示你接受新的条款。如果你不接受，可以在此之前在设置中删除你的账户。",
        ],
        "button": "阅读新条款",
        "footer": "这封邮件发送到 {email}，因为你有 prepza 账户。这是关于我们服务条款的通知，因此无论你的邮件设置如何都会发送。",
    },
    "legal_privacy": {
        "subject": "隐私政策将于 {date} 更新",
        "preheader": "新的隐私政策自 {date} 起生效。",
        "heading": "我们正在更新隐私政策",
        "lines": [
            "我们发布了新版 prepza 隐私政策，其中说明了我们如何使用你的数据。新版自 {date} 起生效；在此之前，现行版本继续适用。",
            "你可以随时在设置中下载或删除你的数据。",
        ],
        "button": "阅读新的隐私政策",
        "footer": "这封邮件发送到 {email}，因为你有 prepza 账户。这是关于我们如何使用你的数据的通知，因此无论你的邮件设置如何都会发送。",
    },
    "legal_dpa": {
        "subject": "数据处理协议将于 {date} 更新",
        "preheader": "新协议自 {date} 起适用于你的公司。",
        "heading": "我们正在更新数据处理协议",
        "lines": [
            "我们发布了新版数据处理协议，prepza 依据该协议处理你的候选人的数据。新版自 {date} 起生效；在此之前，现行版本继续适用。",
            "如果公司出于合理的数据保护理由提出异议，可以在此之前停止使用 prepza 并删除该公司。",
        ],
        "button": "阅读新协议",
        "footer": "这封邮件发送到 {email}，因为你是 prepza 上某个公司的所有者或管理员。这是关于我们与你公司之间协议的通知，因此无论你的邮件设置如何都会发送。",
    },
    # Campaigns (services/campaign_sends.py), named after the setting they need: a superadmin's
    # subject and text, and its button's text, or "open_site" when it has none.
    "updates": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "打开 prepza",
        "footer": "这封邮件发送到 {email}，因为你选择了接收 prepza 的产品更新与新闻。",
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "打开 prepza",
        "footer": "这封邮件发送到 {email}，因为你选择了接收 prepza 的优惠与促销。",
    },
    # An important notice: a service email about prepza itself (a security incident, planned
    # downtime, a change to how it works), whatever the email settings; never a promotion.
    "notices": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "打开 prepza",
        "footer": "这封邮件发送到 {email}，因为你有 prepza 账户。这是关于服务的重要通知，例如其安全性或可用性，因此无论你的邮件设置如何都会发送。",
    },
    "top_up_failed": {
        "subject": "自动充值失败：{company}",
        "preheader": "无法从银行卡扣款。充值后才能继续邀请候选人。",
        "heading": "自动充值失败",
        "lines": [
            "自动充值无法从 {company} 的银行卡扣款，因此没有添加点数。",
            "充值后才能继续邀请候选人。自动充值稍后会再次尝试扣款。",
        ],
        "button": "充值",
        "footer": "这封邮件发送到 {email}，因为你是 prepza 上 {company} 的所有者或管理员。它与你公司的账单有关，因此无论你的邮件设置如何都会发送。",
    },
    "top_up_paused": {
        "subject": "自动充值已暂停：{company}",
        "preheader": "银行卡被拒。请更新银行卡以重新开启自动充值。",
        "heading": "自动充值已暂停",
        "lines": [
            "{company} 自动充值所用的银行卡被拒，重试也无济于事，因此自动充值已暂停，不会再从这张卡扣款。",
            "请在账单页面更新银行卡，以重新开启自动充值。在此之前，请手动充值，以便继续邀请候选人。",
        ],
        "button": "更新银行卡",
        "footer": "这封邮件发送到 {email}，因为你是 prepza 上 {company} 的所有者或管理员。它与你公司的账单有关，因此无论你的邮件设置如何都会发送。",
    },
    "top_up_price_change": {
        "subject": "{company} 的自动充值新价格",
        "preheader": "自 {date} 起，每次自动充值的价格从 {price} 调整为 {new_price}。",
        "heading": "自动充值价格即将调整",
        "lines": [
            "自 {date} 起，{company} 每次自动充值的价格从 {price} 调整为 {new_price}，如适用，另加增值税或销售税。每次充值包含的候选人数量不变。",
            "在此之前的扣款仍为 {price}。如果你想要其他金额，请在 {date} 之前到账单页面更改或关闭自动充值。",
        ],
        "button": "打开账单",
        "footer": "这封邮件发送到 {email}，因为你是 prepza 上 {company} 的所有者或管理员。它与你公司的账单有关，因此无论你的邮件设置如何都会发送。",
    },
    "footer": "这封邮件发送到 {email}，因为有人在 prepza 上邀请了这个地址。如果这封邮件与你无关，可以忽略。",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza 尚未验证 {company}。",
    "paste_link": "或者将此链接粘贴到浏览器中",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "退订",
    "email_settings": "更改邮件设置",
    "stop_reminders": "不再给我发送此面试的提醒",
    "stop_company": "不再给我发送来自 {company} 的邮件",
    # Who runs prepza, at the end of every email.
    "operator": "prepza 由 {name}（{address}）运营。",
}
