from prepza_common.events.event_models import ProcessedEventColumns

from app.models.base import Base


class ProcessedEvent(ProcessedEventColumns, Base):
    """An event already added to the statistics; Pub/Sub may deliver it again."""

    __tablename__ = "processed_events"
