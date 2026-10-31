from testee_common.events.event_models import OutboxColumns

from companies.models.base import Base


class OutboxEvent(OutboxColumns, Base):
    __tablename__ = "outbox"
