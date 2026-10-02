import factory

from apps.audit_log.models import ActionLog


class ActionLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionLog

    action = "test.action"
    resource_type = "test"
    method = "POST"
    path = "/api/v1/test/"
    status_code = 200
