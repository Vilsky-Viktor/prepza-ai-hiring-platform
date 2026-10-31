from testee_common.events.event_models import OutboxColumns

from site_content.models.base import Base


class OutboxEvent(OutboxColumns, Base):
    __tablename__ = "outbox"
