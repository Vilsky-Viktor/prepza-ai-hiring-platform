"""How pages reach browsers (.claude/rules/performance.md, Delivery): compressed once, at Cloud
CDN in production (Brotli where the browser takes it) and at the gateway locally, never by the
frontend itself, and streamed through the gateway unbuffered."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def page_block() -> str:
    conf = (ROOT / "gateway/nginx.conf").read_text()

    return conf[conf.index("    location / {") :]


def test_the_cdn_compresses_the_frontends_responses():
    balancer = (ROOT / "infra/terraform/load_balancer.tf").read_text()

    assert re.search(r'compression_mode\s*=\s*each\.key == "frontend" \? "AUTOMATIC"', balancer)


def test_the_frontend_leaves_compression_to_what_is_in_front_of_it():
    config = (ROOT / "frontend/next.config.ts").read_text()

    assert re.search(r"^\s*compress: false,$", config, re.MULTILINE)


def test_the_gateway_streams_and_compresses_pages_as_production_does():
    block = page_block()

    assert "proxy_buffering off;" in block
    assert "gzip on;" in block
