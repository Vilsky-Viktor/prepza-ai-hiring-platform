# A campaign's text: the few marks its editor writes (bold, italic, links and lists, in
# Markdown) as an email's HTML, styled inline as mail clients need, and as plain text.
from html import escape

from markdown_it import MarkdownIt

# Only what the editor writes: raw HTML stays text, and unsafe links (javascript:) aren't links.
PARSER = MarkdownIt("zero", {"breaks": True}).enable(["emphasis", "link", "list", "newline"])

# Each opening tag as the email's other paragraphs and links look.
STYLED = {
    "paragraph_open": '<p style="margin:0 0 16px;font-size:16px;line-height:24px;color:#404040;">',
    # A list's indent is on its start side: the right in a right-to-left language.
    "bullet_list_open": '<ul style="margin:0 0 16px;padding-{start}:24px;font-size:16px;'
    'line-height:24px;color:#404040;">',
    "ordered_list_open": '<ol style="margin:0 0 16px;padding-{start}:24px;font-size:16px;'
    'line-height:24px;color:#404040;">',
    "list_item_open": '<li style="margin:0 0 4px;">',
    "strong_open": '<strong style="font-weight:600;color:#0a0a0a;">',
}
LINK = '<a href="{url}" target="_blank" style="color:#0071e0;text-decoration:underline;">'


def _styled(tag: str):
    def render(self, tokens, index, options, env) -> str:
        token = tokens[index]

        # A list's items hold their text without a paragraph of their own.
        if token.type == "paragraph_open" and token.hidden:
            return ""

        return tag.replace("{start}", "right" if env.get("rtl") else "left")

    return render


def _link(self, tokens, index, options, env) -> str:
    return LINK.format(url=escape(tokens[index].attrGet("href") or ""))


for _type, _tag in STYLED.items():
    PARSER.add_render_rule(_type, _styled(_tag))

PARSER.add_render_rule("link_open", _link)


def markdown_html(text: str, rtl: bool = False) -> str:
    """`text` as the email's HTML, its lists indented on the right when `rtl`; everything else
    in it is escaped."""
    return PARSER.render(text, {"rtl": rtl})


def markdown_plain(text: str) -> str:
    """`text`'s words alone, without its marks: for the line inboxes show after the subject."""
    blocks = [
        "".join(
            child.content if child.type == "text" else " "
            for child in token.children or []
            if child.type in ("text", "softbreak", "hardbreak")
        )
        for token in PARSER.parse(text)
        if token.type == "inline"
    ]

    return " ".join(" ".join(blocks).split())
