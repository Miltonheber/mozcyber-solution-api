from apps.core.repositories import BaseRepository
from apps.user.models import Profile


class ProfileRepository(BaseRepository[Profile]):
    model = Profile
    prefetch_related = ("permissions",)
    search_fields = ("code", "name")
