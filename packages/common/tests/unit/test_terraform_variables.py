"""No secret comes into Terraform as an input variable (the security rules: secrets only in
Secret Manager): variables.tf declares none marked sensitive, nor one named as a secret, key or
token, unless it's public by design and listed here with why."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SECRET_NAME = re.compile(r"secret|key|token|password", re.IGNORECASE)
# Public by design: the Firebase web app's apiKey and Paddle.js's client token ship to every
# browser.
PUBLIC = {"firebase_web_api_key", "paddle_client_token"}


def test_no_secret_is_a_terraform_variable():
    text = (ROOT / "infra/terraform/variables.tf").read_text()
    blocks = re.findall(r'variable "(\w+)" \{(.*?)\n\}', text, re.DOTALL)
    sensitive = [name for name, body in blocks if re.search(r"sensitive\s*=\s*true", body)]
    named = [name for name, _ in blocks if SECRET_NAME.search(name) and name not in PUBLIC]

    assert len(blocks) > 10
    assert (sensitive, named) == ([], [])
