from functools import reduce
from operator import or_

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import Q

from .exceptions import NotFoundException


class BaseRepository[T: models.Model]:
    """Único ponto de acesso à BD. Declare `select_related`/`prefetch_related` para evitar N+1."""

    model: type[T]
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    filter_fields: tuple[str, ...] = ()  # query params permitidos como filtro exacto
    search_fields: tuple[str, ...] = ()  # campos usados em ?search=

    def get_queryset(self) -> models.QuerySet[T]:
        qs = self.model.objects.all()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_related:
            qs = qs.prefetch_related(*self.prefetch_related)
        return qs

    def list(self, params=None) -> models.QuerySet[T]:
        params = params or {}
        qs = self.get_queryset()
        filters = {f: params[f] for f in self.filter_fields if f in params}
        if filters:
            qs = qs.filter(**filters)
        search = params.get("search")
        if search and self.search_fields:
            qs = qs.filter(reduce(or_, (Q(**{f"{f}__icontains": search}) for f in self.search_fields)))
        return qs

    def get(self, pk) -> T:
        try:
            return self.get_queryset().get(pk=pk)
        except (self.model.DoesNotExist, ValueError, TypeError, DjangoValidationError):
            raise NotFoundException(f"{self.model._meta.verbose_name} não encontrado.") from None

    def create(self, *, actor=None, **data) -> T:
        plain, m2m = self._split(data)
        if actor is not None and hasattr(self.model, "created_by"):
            plain.update(created_by=actor, updated_by=actor)
        instance = self.model.objects.create(**plain)
        self._set_m2m(instance, m2m)
        return instance

    def update(self, instance: T, *, actor=None, **data) -> T:
        plain, m2m = self._split(data)
        for field, value in plain.items():
            setattr(instance, field, value)
        if actor is not None and hasattr(instance, "updated_by"):
            instance.updated_by = actor
        instance.save()
        self._set_m2m(instance, m2m)
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()

    def _split(self, data: dict) -> tuple[dict, dict]:
        m2m_names = {f.name for f in self.model._meta.many_to_many}
        plain = {k: v for k, v in data.items() if k not in m2m_names}
        return plain, {k: v for k, v in data.items() if k in m2m_names}

    @staticmethod
    def _set_m2m(instance, m2m: dict) -> None:
        for name, values in m2m.items():
            getattr(instance, name).set(values)
