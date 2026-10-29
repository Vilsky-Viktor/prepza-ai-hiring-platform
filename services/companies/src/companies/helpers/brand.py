from prepza_common.i18n.i18n import translate

from companies.constants.brand import (
    CONTRAST_RULES,
    PREPZA_BUTTON_RADIUS,
    PREPZA_COLORS,
    PREPZA_FONT,
    PREPZA_RADIUS,
    BrandFont,
    Theme,
)


def luminance(color: str) -> float:
    """A "#rrggbb" color's relative luminance, as WCAG defines it."""
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    red, green, blue = [
        value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]

    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)

    return (lighter + 0.05) / (darker + 0.05)


def unreadable(colors: dict[str, str]) -> str | None:
    """Why these colors would make some text hard to read, or None when every text reads."""
    for text, background, minimum, message in CONTRAST_RULES:
        if contrast(colors[text], colors[background]) < minimum:
            return message

    return None


def color_sets(saved: dict | None) -> dict[str, dict[str, str]]:
    """The colors a company's candidates see, by theme: its own set, or prepza's for a theme it
    has none for, or whose set a stricter check now finds hard to read (saved before it)."""
    sets = {}

    for theme in Theme:
        colors = (saved or {}).get(theme)
        sets[theme] = colors if colors and not unreadable(colors) else PREPZA_COLORS[theme]

    return sets


def brand_problems(saved: dict | None, language: str) -> dict[str, str]:
    """Why each theme's saved colors are refused now, in the user's language: a check added
    since they were saved. Their brand settings show the colors with it, to adjust."""
    return {
        theme: translate(problem, language)
        for theme, colors in (saved or {}).items()
        if colors and (problem := unreadable(colors))
    }


def style_of(company) -> dict:
    """A company's font and corner rounding, prepza's where it has none."""

    def saved(value, default):
        return default if company is None or value is None else value

    return {
        # A font no longer offered is prepza's.
        "font": font if (font := company and company.brand_font) in set(BrandFont) else PREPZA_FONT,
        "radius": saved(company and company.brand_radius, PREPZA_RADIUS),
        "button_radius": saved(company and company.brand_button_radius, PREPZA_BUTTON_RADIUS),
    }
