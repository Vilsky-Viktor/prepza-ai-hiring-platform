# The contact page's message, as prepza's inbox gets it. English only: it's for the team.
CONTACT_SUBJECT = "Contact form: {name}"

CONTACT_TEXT = """\
From: {name} <{email}>
Page language: {language}

{message}
"""

CONTACT_HTML = """\
<!doctype html>
<html lang="en">
<body style="margin:0;padding:24px;font-family:Arial,Helvetica,sans-serif;color:#0a0a0a;">
<p style="margin:0 0 4px;font-size:14px;color:#404040;">From: {name} &lt;{email}&gt;</p>
<p style="margin:0 0 16px;font-size:14px;color:#404040;">Page language: {language}</p>
<p style="margin:0;font-size:16px;line-height:24px;white-space:pre-wrap;">{message}</p>
</body>
</html>
"""
