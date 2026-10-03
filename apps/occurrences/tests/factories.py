import datetime

import factory

from apps.occurrences.constants import DocumentType
from apps.occurrences.models import LostDocumentOccurrence


class LostDocumentOccurrenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LostDocumentOccurrence

    document_type = DocumentType.BI
    document_number = factory.Sequence(lambda n: f"1100{n:08d}A")
    owner_name = factory.Faker("name")
    lost_at = factory.LazyFunction(datetime.date.today)
    location = "Mercado Central"
    station_name = "Esquadra da Polícia Nº 1"
