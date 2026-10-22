"""How pages reach browsers (.claude/rules/performance.md, Delivery): streamed through the
gateway unbuffered."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def page_block() -> str:
    conf = (ROOT / "gateway/nginx.conf").read_text()

    return conf[conf.index("    location / {") :]


def test_the_gateway_streams_pages_as_production_does():
    assert "proxy_buffering off;" in page_block()
