# Email texts in Hebrew, with straight quotes, which read the same right to left. Values are filled
# in with str.format; the HTML version escapes them.

# The footer of reminders to a company's owners and admins.
MEMBER_FOOTER = "הודעה זו נשלחה אל {email} כי יש לכם תפקיד של בעלים או מנהל בחברה ב-prepza."

TEXTS = {
    "candidate": {
        "subject": "קיבלת הזמנה לראיון מ-{company}",
        "preheader": 'ראיון "{title}" ב-prepza. יש להתחבר עם {email} כדי להתחיל.',
        "heading": "הזמנה לראיון",
        "lines": [
            'קיבלת הזמנה מ-{company} לראיון "{title}" ב-prepza.',
            "יש להתחבר עם {email} כדי להתחיל. רק כתובת זו יכולה לגשת לראיון, ויש ניסיון אחד בלבד.",
        ],
        "button": "פתיחת ההזמנה",
    },
    "joined": {
        "subject": 'הקישור שלך להמשך "{title}"',
        "preheader": "אם יוצאים מהראיון, אפשר להמשיך בקישור הזה. יש להתחבר עם {email}.",
        "heading": "הקישור לראיון שלך",
        "lines": [
            'התחלת את הראיון "{title}" של {company} ב-prepza.',
            (
                "אם יוצאים, ממשיכים בקישור הזה: יש להתחבר עם {email}. הוא ממשיך לעבוד גם אם {company} "
                "תשבית את הקישור שממנו התחלת. הזמן ממשיך לרוץ בזמן ההיעדרות."
            ),
        ],
        "button": "המשך הראיון",
        "footer": "הודעה זו נשלחה אל {email} כי ראיון ב-prepza התחיל עם הכתובת הזו.",
    },
    "reminder": {
        "subject": "תזכורת: {company} מחכה לראיון שלך",
        "preheader": 'ראיון "{title}" עדיין פתוח. יש להתחבר עם {email} כדי להתחיל.',
        "heading": "הראיון שלך מחכה",
        "lines": [
            (
                'קיבלת הזמנה מ-{company} לראיון "{title}" ב-prepza לפני כמה ימים, ועדיין לא '
                "התחלת אותו."
            ),
            (
                "יש להתחבר עם {email} כדי להתחיל. רק כתובת זו יכולה לגשת לראיון, ויש ניסיון "
                "אחד בלבד. תוקף ההזמנה פג 30 ימים אחרי שליחתה."
            ),
        ],
        "button": "פתיחת ההזמנה",
    },
    "member": {
        "subject": "קיבלת הזמנה מ-{inviter} להצטרף לצוות של {company} ב-prepza",
        "preheader": (
            "הצטרפות לצוות של {company} בתפקיד {role}. יש להתחבר עם {email} כדי לקבל את ההזמנה."
        ),
        "heading": "הזמנה להצטרף לצוות",
        "lines": [
            "קיבלת הזמנה מ-{inviter} להצטרף לצוות של {company} ב-prepza בתפקיד {role}.",
            "יש להתחבר עם {email} כדי לקבל את ההזמנה. רק כתובת זו יכולה לקבל את ההזמנה.",
        ],
        "button": "פתיחת ההזמנה",
        # The role's name as the lines use it.
        "roles": {"admin": "מנהל", "viewer": "צופה"},
    },
    "report": {
        "subject": "דוח מועמד: {candidate}",
        "preheader": '{candidate} ניגש/ה ל-"{title}" ב-{company}. הדוח מצורף.',
        "heading": "דוח מועמד",
        "lines": [
            '{sender} מ-{company} שיתף/ה את הדוח של {candidate} בראיון "{title}".',
            (
                "הוא מצורף כקובץ PDF בן עמוד אחד: הציון הכולל, הציון בכל נושא ומה שהדפדפן "
                "של המועמד הראה. אפשר להשיב לאימייל הזה כדי לענות ל-{sender}."
            ),
        ],
        "button": "כניסה ל-prepza",
        "footer": "הודעה זו נשלחה אל {email} כי {sender} שיתף/ה דוח מועמד עם הכתובת הזו "
        "ב-prepza. אם לא ציפית לה, אפשר להתעלם ממנה.",
    },
    "candidates": {
        "subject": "דוח של כל המועמדים: {title}",
        "preheader": 'כל המועמדים ל-"{title}" ב-{company}. הדוח מצורף.',
        "heading": "דוח מועמדים",
        "lines": [
            '{sender} מ-{company} שיתף/ה את הדוח של כל המועמדים בראיון "{title}".',
            (
                "הוא מצורף כקובץ PDF: הציון של כל מועמד, ההתקדמות שלו ומה שהדפדפן שלו הראה, "
                "מהטוב ביותר ומטה. אפשר להשיב לאימייל הזה כדי לענות ל-{sender}."
            ),
        ],
        "button": "כניסה ל-prepza",
        "footer": "הודעה זו נשלחה אל {email} כי {sender} שיתף/ה דוח מועמדים עם הכתובת הזו "
        "ב-prepza. אם לא ציפית לה, אפשר להתעלם ממנה.",
    },
    "digest": {
        "subject": "סיכום הפעילות שלכם ב-prepza",
        "preheader": "מה קרה בחברות שלכם ב-24 השעות האחרונות.",
        "heading": "סיכום הפעילות שלכם",
        "lines": [
            "זה מה שקרה בחברות שלכם ב-prepza ב-24 השעות האחרונות.",
        ],
        "rows": {
            "candidate_finished": 'מועמדים שסיימו: {count} · "{title}"',
            "invite_undelivered": 'הזמנות שלא נמסרו: {count} · "{title}"',
            "ats_not_invited": "מועמדים מ-{ats} שלא הוזמנו: {count}",
            "interview_ready": 'ראיון מוכן: "{title}"',
        },
        "button": "פתיחת prepza",
        "footer": (
            "הודעה זו נשלחה אל {email} כי אתם חברים בחברה ב-prepza ומקבלים את סיכום הפעילות שלה."
        ),
    },
    "low_credits": {
        "subject": "הקרדיטים שלכם עומדים להיגמר",
        "preheader": "טענו כדי להמשיך להזמין מועמדים.",
        "heading": "הקרדיטים עומדים להיגמר",
        "lines": [
            "לחברות האלה אין מספיק קרדיטים כדי להזמין עוד מועמד. טענו כדי להמשיך להזמין מועמדים.",
        ],
        "rows": {
            "company": "{company} · קרדיטים זמינים: {available}",
        },
        "button": "טעינה",
        "footer": MEMBER_FOOTER,
    },
    "no_candidates": {
        "subject": "ממתינים למועמדים",
        "preheader": "הזמינו מועמדים באימייל או שתפו את הקישור לראיון.",
        "heading": "ממתינים למועמדים",
        "lines": [
            (
                "הראיונות האלה מוכנים כבר כמה ימים, אבל עדיין לא הוזמן אף אחד. הזמינו "
                "מועמדים באימייל או שתפו את הקישור לראיון."
            ),
        ],
        "rows": {
            "interview": '"{title}" · {company}',
        },
        "button": "הזמנת מועמדים",
        "footer": MEMBER_FOOTER,
    },
    "review_waiting": {
        "subject": "הנושאים שלכם ממתינים לבדיקה",
        "preheader": "אשרו את הנושאים והשאלות ייווצרו.",
        "heading": "בדקו את הנושאים",
        "lines": [
            (
                "הנושאים של הראיונות שהתחלתם ממתינים לבדיקה שלכם. ברגע שתאשרו אותם, השאלות "
                "ייווצרו. בדיקה שנשארת פתוחה 14 ימים מבוטלת."
            ),
        ],
        "rows": {
            "interview": "{company} · ימי המתנה: {days}",
        },
        "button": "בדיקת הנושאים",
        "footer": MEMBER_FOOTER,
    },
    # Notices of a significant change to a legal document, sent at least 14 days before it
    # applies; service emails, whatever the email settings.
    "legal_terms": {
        "subject": "אנחנו מעדכנים את תנאי השימוש של prepza ב-{date}",
        "preheader": "תנאי השימוש החדשים חלים מ-{date}.",
        "heading": "אנחנו מעדכנים את תנאי השימוש",
        "lines": [
            (
                "פרסמנו גרסה חדשה של תנאי השימוש של prepza. היא חלה מ-{date}; עד אז חלים תנאי "
                "השימוש הנוכחיים."
            ),
            (
                "שימוש ב-prepza אחרי {date} פירושו שאתם מקבלים את התנאים החדשים. אם אינכם "
                "מסכימים, אפשר למחוק את החשבון בהגדרות לפני כן."
            ),
        ],
        "button": "קריאת התנאים החדשים",
        "footer": (
            "הודעה זו נשלחה אל {email} כי יש לכם חשבון ב-prepza. זו הודעה על תנאי השימוש "
            "שלנו, ולכן היא נשלחת בלי קשר להגדרות האימייל שלכם."
        ),
    },
    "legal_privacy": {
        "subject": "אנחנו מעדכנים את מדיניות הפרטיות של prepza ב-{date}",
        "preheader": "מדיניות הפרטיות החדשה חלה מ-{date}.",
        "heading": "אנחנו מעדכנים את מדיניות הפרטיות",
        "lines": [
            (
                "פרסמנו גרסה חדשה של מדיניות הפרטיות של prepza, שמסבירה איך אנחנו משתמשים בנתונים "
                "שלכם. היא חלה מ-{date}; עד אז חלה הגרסה הנוכחית."
            ),
            "אפשר להוריד או למחוק את הנתונים שלכם בהגדרות בכל עת.",
        ],
        "button": "קריאת מדיניות הפרטיות החדשה",
        "footer": (
            "הודעה זו נשלחה אל {email} כי יש לכם חשבון ב-prepza. זו הודעה על האופן שבו אנחנו "
            "משתמשים בנתונים שלכם, ולכן היא נשלחת בלי קשר להגדרות האימייל שלכם."
        ),
    },
    "legal_dpa": {
        "subject": "אנחנו מעדכנים את הסכם עיבוד הנתונים של prepza ב-{date}",
        "preheader": "ההסכם החדש חל על החברה שלכם מ-{date}.",
        "heading": "אנחנו מעדכנים את הסכם עיבוד הנתונים",
        "lines": [
            (
                "פרסמנו גרסה חדשה של הסכם עיבוד הנתונים שלפיו prepza מעבדת את הנתונים של המועמדים "
                "שלכם. היא חלה מ-{date}; עד אז חלה הגרסה הנוכחית."
            ),
            (
                "חברה שמתנגדת מטעמים סבירים של הגנת נתונים יכולה להפסיק להשתמש ב-prepza ולמחוק את "
                "החברה שלה לפני כן."
            ),
        ],
        "button": "קריאת ההסכם החדש",
        "footer": (
            "הודעה זו נשלחה אל {email} כי יש לכם תפקיד של בעלים או מנהל בחברה ב-prepza. זו "
            "הודעה על ההסכם שלנו עם החברה שלכם, ולכן היא נשלחת בלי קשר להגדרות האימייל שלכם."
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
        "open_site": "פתיחת prepza",
        "footer": "הודעה זו נשלחה אל {email} כי בחרתם לקבל מ-prepza עדכוני מוצר וחדשות.",
    },
    "promotions": {
        "subject": "{subject}",
        "preheader": "{preheader}",
        "heading": "{subject}",
        "lines": [],
        "button": "{button}",
        "open_site": "פתיחת prepza",
        "footer": "הודעה זו נשלחה אל {email} כי בחרתם לקבל מ-prepza מבצעים והטבות.",
    },
    "top_up_failed": {
        "subject": "הטעינה האוטומטית נכשלה עבור {company}",
        "preheader": "לא ניתן היה לחייב את הכרטיס. טענו כדי להמשיך להזמין מועמדים.",
        "heading": "הטעינה האוטומטית נכשלה",
        "lines": [
            "הטעינה האוטומטית לא הצליחה לחייב את הכרטיס עבור {company}, ולכן לא נוספו קרדיטים.",
            "טענו כדי להמשיך להזמין מועמדים. הטעינה האוטומטית תנסה לחייב את הכרטיס שוב מאוחר יותר.",
        ],
        "button": "טעינה",
        "footer": (
            "הודעה זו נשלחה אל {email} כי יש לכם תפקיד של בעלים או מנהל ב-{company} "
            "ב-prepza. היא עוסקת בחיוב של החברה שלכם, ולכן נשלחת בלי קשר להגדרות האימייל "
            "שלכם."
        ),
    },
    "footer": "הודעה זו נשלחה אל {email} כי מישהו הזמין את הכתובת הזו ב-prepza. אם לא ציפית לה, "
    "אפשר להתעלם ממנה.",
    # An invite from a company prepza hasn't verified, at the end of the footer.
    "unverified": "prepza לא אימתה את {company}.",
    "paste_link": "או להדביק את הקישור הזה בדפדפן",
    # The footer's links: optional emails' unsubscribe and settings, and a candidate's own.
    "unsubscribe": "ביטול הרשמה",
    "email_settings": "שינוי הגדרות האימייל",
    "stop_reminders": "לא לשלוח לי תזכורות לראיון הזה",
    "stop_company": "לא לשלוח לי אימיילים מטעם {company}",
    # Who runs prepza, at the end of every email.
    "operator": "prepza מופעלת על ידי {name}, {address}.",
}
