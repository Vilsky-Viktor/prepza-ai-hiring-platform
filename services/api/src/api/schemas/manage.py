from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from api.constants.api import MAX_NAME_LENGTH, MAX_URL_LENGTH, KeyExpiry
from api.constants.permissions import DEFAULT_PERMISSIONS, Permission


class KeyOut(BaseModel):
    id: UUID
    name: str
    # The key's first characters, to tell keys apart.
    shown: str
    created_at: datetime
    # None: it never expires.
    expires_at: datetime | None
    expired: bool
    last_used_at: datetime | None
    permissions: list[Permission]


class NewKeyOut(KeyOut):
    # The whole key, shown this once.
    key: str


class KeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    expiry: KeyExpiry
    # At least one; the reads they imply are added.
    permissions: list[Permission] = Field(
        default_factory=lambda: list(DEFAULT_PERMISSIONS), min_length=1
    )


class KeyPermissionsIn(BaseModel):
    # Only ones the key already has, at least one; the reads they imply are kept.
    permissions: list[Permission] = Field(min_length=1)


class WebhookOut(BaseModel):
    id: UUID
    url: str
    created_at: datetime
    # It didn't take an event for days (it was dropped), and has taken none since.
    failing: bool
    # The member who added it is no longer an owner or admin: it gets no events.
    stopped: bool = False


class NewWebhookOut(WebhookOut):
    # The signing secret, shown this once.
    secret: str


class NewSecretOut(BaseModel):
    # The web hook's new signing secret, shown this once.
    secret: str
    # Until when the old secret signs too.
    previous_until: datetime


class WebhookIn(BaseModel):
    url: str = Field(min_length=1, max_length=MAX_URL_LENGTH)


class ApiSettingsOut(BaseModel):
    keys: list[KeyOut]
    # When a new key can expire, in order.
    expiries: list[str]
    webhooks: list[WebhookOut]
    # The permissions a key can have, by what they touch, in order; the read each one that
    # changes something comes with; and what a new key starts with.
    permission_groups: dict[str, list[Permission]]
    implied: dict[Permission, Permission]
    default_permissions: list[Permission]


class WebhookTestOut(BaseModel):
    # Whether the web hook took the test event.
    ok: bool


class WebhookAttemptOut(BaseModel):
    """A send in a web hook's delivery log."""

    event_type: str
    ok: bool
    # "delivered", the status the endpoint answered, the error, or why it was skipped.
    result: str
    at: datetime
