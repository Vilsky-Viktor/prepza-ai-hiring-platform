from testee_common.events.event_models import ProcessedEventColumns

from companies.models.base import Base


class ProcessedEvent(ProcessedEventColumns, Base):
    """An event whose notification was already saved; Pub/Sub may deliver it again."""

    __tablename__ = "processed_events"
