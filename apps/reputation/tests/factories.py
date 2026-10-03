import factory

from apps.reputation.constants import Verdict
from apps.reputation.models import MessageClassification, NumberReport, PhoneNumber


class PhoneNumberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PhoneNumber

    number = factory.Sequence(lambda n: f"+25884{n:07d}")


class MessageClassificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MessageClassification

    phone_number = factory.SubFactory(PhoneNumberFactory)
    message = "Ganhou um prémio, envie o seu PIN"
    verdict = Verdict.FRAUD
    provider = "rule_based"


class NumberReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NumberReport

    phone_number = factory.SubFactory(PhoneNumberFactory)
    behavior = "Pediu o PIN do M-Pesa"
