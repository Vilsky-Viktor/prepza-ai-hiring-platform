from pydantic import BaseModel, Field

from companies.constants.brand import (
    HEX_COLOR,
    MAX_RADIUS,
    PREPZA_BUTTON_RADIUS,
    PREPZA_HEADING_FONT,
    PREPZA_RADIUS,
    PREPZA_TEXT_FONT,
    BrandFont,
    Theme,
)
from companies.constants.logos import MAX_LOGO_BYTES


class LogoIn(BaseModel):
    """The logo image, base64-encoded."""

    image: str = Field(min_length=1, max_length=MAX_LOGO_BYTES * 4 // 3 + 4)


class LogoOut(BaseModel):
    logo_url: str | None


class BrandColors(BaseModel):
    """A company's colors on its candidates' pages, by group: each background and its text."""

    background: str = Field(pattern=HEX_COLOR)
    foreground: str = Field(pattern=HEX_COLOR)
    card: str = Field(pattern=HEX_COLOR)
    card_foreground: str = Field(pattern=HEX_COLOR)
    primary: str = Field(pattern=HEX_COLOR)
    primary_foreground: str = Field(pattern=HEX_COLOR)
    muted: str = Field(pattern=HEX_COLOR)
    muted_foreground: str = Field(pattern=HEX_COLOR)
    border: str = Field(pattern=HEX_COLOR)


class BrandColorsIn(BaseModel):
    # None goes back to prepza's own.
    colors: BrandColors | None


class BrandColorsOut(BaseModel):
    colors: BrandColors | None


class SavedBrandColors(BaseModel):
    """The sets a company saved, by theme; a theme without one uses prepza's."""

    light: BrandColors | None = None
    dark: BrandColors | None = None


class BrandColorSets(BaseModel):
    """The colors a candidate's pages use, by theme: the company's, or prepza's where it has
    none."""

    light: BrandColors
    dark: BrandColors


class BrandStyle(BaseModel):
    """A company's fonts, for titles and for the text, and its cards' and buttons' corner
    rounding (px), on its candidates' pages."""

    heading_font: BrandFont = PREPZA_HEADING_FONT
    text_font: BrandFont = PREPZA_TEXT_FONT
    radius: int = Field(default=PREPZA_RADIUS, ge=0, le=MAX_RADIUS)
    button_radius: int = Field(default=PREPZA_BUTTON_RADIUS, ge=0, le=MAX_RADIUS)


class PrepzaBrand(BaseModel):
    colors: BrandColorSets
    style: BrandStyle


class BrandOut(BaseModel):
    """Who a candidate's interview is for, shown while they take it."""

    company: str
    logo_url: str | None
    # For the candidate invited through the API with a return_url: where "Continue" takes them
    # once they've finished, with their invite's id.
    return_url: str | None = None
    # The interview's colors by theme, and the theme its invite asked for (None: the
    # candidate's own).
    brand_colors: BrandColorSets | None = None
    theme: Theme | None = None
    brand_style: BrandStyle | None = None
