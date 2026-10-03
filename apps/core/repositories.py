import datetime
from functools import reduce
from operator import or_

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date as _parse_date
from django.utils.dateparse import parse_datetime as _parse_datetime

from .exceptions import NotFoundException, ValidationException


def parse_date(value: str):
    try:
        return _parse_date(value)
    except ValueError:  # bem formatada mas impossível (ex.: mês 13)
        return None


def parse_datetime(value: str):
    try:
        return _parse_datetime(value)
    except ValueError:
        return None


class BaseRepository[T: models.Model]:
    """Único ponto de acesso à BD. Declare `select_related`/`prefetch_related` para evitar N+1."""

    model: type[T]
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    filter_fields: tuple[str, ...] = ()  # query params permitidos como filtro exacto
    search_fields: tuple[str, ...] = ()  # campos usados em ?search=
    # param -> (campo, "gte" | "lte"); aceita AAAA-MM-DD (dia inteiro) ou data-hora ISO em campos DateTimeField
    range_fields: dict[str, tuple[str, str]] = {}
    ordering_fields: tuple[str, ...] = ()  # campos permitidos em ?ordering=a,-b

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
        qs = self._apply_ranges(qs, params)
        return self._apply_ordering(qs, params.get("ordering"))

    def _apply_ranges(self, qs, params):
        bounds: dict[str, dict[str, tuple[object, str]]] = {}
        for param, (field, lookup) in self.range_fields.items():
            raw = params.get(param)
            if not raw:
                continue
            value, django_lookup = self._parse_bound(param, field, lookup, raw)
            bounds.setdefault(field, {})[lookup] = (value, django_lookup)
            qs = qs.filter(**{f"{field}__{django_lookup}": value})
        for field, pair in bounds.items():
            if len(pair) == 2:
                (start, _), (end, end_lookup) = pair["gte"], pair["lte"]
                if start > end or (end_lookup == "lt" and start >= end):
                    raise ValidationException(
                        "O início do intervalo é posterior ao fim.",
                        code="invalid_filter",
                        details={"field": field},
                    )
        return qs

    def _is_datetime(self, field: str) -> bool:
        return isinstance(self.model._meta.get_field(field), models.DateTimeField)

    def _parse_bound(self, param: str, field: str, lookup: str, raw: str):
        """(valor, lookup Django). Data-hora sem fuso assume o fuso actual; `lte` com um dia inteiro vira `lt` do dia seguinte."""
        if self._is_datetime(field):
            if (day := parse_date(raw)) is None and (value := parse_datetime(raw)) is not None:
                return (timezone.make_aware(value) if timezone.is_naive(value) else value), lookup
            if day is not None:
                start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
                return (start, "gte") if lookup == "gte" else (start + datetime.timedelta(days=1), "lt")
        elif (value := parse_date(raw)) is not None:
            return value, lookup
        raise ValidationException(
            f"Valor inválido em '{param}': use AAAA-MM-DD.", code="invalid_filter", details={"param": param}
        )

    def _apply_ordering(self, qs, ordering):
        if not ordering:
            return qs
        fields = [f.strip() for f in ordering.split(",") if f.strip()]
        invalid = [f for f in fields if f.lstrip("-") not in self.ordering_fields]
        if invalid:
            raise ValidationException(
                "Campo de ordenação inválido.",
                code="invalid_filter",
                details={"param": "ordering", "allowed": list(self.ordering_fields)},
            )
        return qs.order_by(*fields, "-pk")

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
