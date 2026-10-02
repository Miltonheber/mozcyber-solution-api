from .repositories import BaseRepository


class BaseService:
    """Regras de negócio. Recebe o repository por injecção (facilita testes com mocks)."""

    repository_class: type[BaseRepository]

    def __init__(self, repository: BaseRepository | None = None):
        self.repository = repository or self.repository_class()

    def list(self, params=None):
        return self.repository.list(params)

    def get(self, pk):
        return self.repository.get(pk)

    def create(self, data: dict, actor=None):
        instance = self.repository.create(actor=actor, **data)
        return self.repository.get(instance.pk)  # recarrega com select/prefetch

    def update(self, instance, data: dict, actor=None):
        instance = self.repository.update(instance, actor=actor, **data)
        return self.repository.get(instance.pk)

    def delete(self, pk) -> None:
        self.repository.delete(self.repository.get(pk))
