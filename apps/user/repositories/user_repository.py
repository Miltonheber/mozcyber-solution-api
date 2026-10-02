from apps.core.repositories import BaseRepository
from apps.user.models import User


class UserRepository(BaseRepository[User]):
    model = User
    prefetch_related = ("profiles",)
    filter_fields = ("is_active",)
    search_fields = ("email", "name")

    def get_active_by_id(self, pk) -> User | None:
        return self.model.objects.filter(pk=pk, is_active=True).first()
