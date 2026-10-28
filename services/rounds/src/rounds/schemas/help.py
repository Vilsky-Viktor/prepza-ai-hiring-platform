from typing import Literal

from pydantic import BaseModel


class FaqItemOut(BaseModel):
    key: str
    question: str
    answer: str


class LegalSectionOut(BaseModel):
    heading: str
    paragraphs: list[str] = []
    items: list[str] = []


class LegalOut(BaseModel):
    # The language of the text: the one asked for when it's translated, otherwise English.
    language: str
    intro: str
    # The day this text applies from, the newest version's, the one that applies today, and every
    # published one, newest first.
    version: str
    state: Literal["in_force", "upcoming", "replaced"]
    current: str
    in_force: str
    versions: list[str]
    sections: list[LegalSectionOut]


class GuideItemOut(BaseModel):
    """A guide article of the site: its title and summary in `language` (English until it's
    translated), and where the site shows it."""

    slug: str
    language: str
    title: str
    description: str
    updated: str
    path: str


class GuideOut(GuideItemOut):
    """A guide article with its Markdown text."""

    body: str


class PageGuideOut(BaseModel):
    """A page's guide: what it's for (`text`), what you can do there, tips, and the guide
    article to read more in, if the page has one."""

    key: str
    title: str
    text: str
    actions: list[str]
    tips: list[str]
    article: GuideItemOut | None = None


class HelpKnowledgeOut(BaseModel):
    """What the help chat answers from, in English: the platform guide (with the prices in the
    visitor's currency) and the guide of the page asked on, as text, if it's a known page."""

    knowledge: str
    page_guide: str | None = None
