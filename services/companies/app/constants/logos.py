# Company logos: PNG, JPEG or WebP up to this size, recognised by their first bytes. SVG isn't
# accepted: it can carry scripts.
MAX_LOGO_BYTES = 500_000
WEBP_TYPE = "image/webp"
# A WebP logo is decoded (to keep it as PNG) only up to this many pixels a side: 500 KB of
# WebP can declare an image far larger than an instance's memory.
MAX_LOGO_SIDE = 4096
# A WebP logo is kept as PNG, which every email client shows.
PNG_TYPE = "image/png"
LOGO_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", PNG_TYPE),
    (b"\xff\xd8\xff", "image/jpeg"),
)
# Where the site serves a logo (through the gateway); `v` changes with every upload.
LOGO_PATH = "/api/companies/companies/{company_id}/logo?v={version}"
# A versioned logo never changes, so browsers and email clients keep it.
LOGO_CACHE = "public, max-age=31536000, immutable"
