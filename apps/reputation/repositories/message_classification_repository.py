from apps.core.repositories import BaseRepository
from apps.reputation.models import MessageClassification


class MessageClassificationRepository(BaseRepository[MessageClassification]):
    model = MessageClassification
    select_related = ("phone_number",)
    filter_fields = ("verdict", "category")
    search_fields = ("phone_number__number", "message")
