from testee_common.events.event_models import OutboxColumns

from api.models.base import Base


class OutboxEvent(OutboxColumns, Base):
    __tablename__ = "outbox"
