import factory

from apps.education.constants import Topic
from apps.education.models import Post


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Sequence(lambda n: f"Post {n}")
    body = "Conteúdo"
    topic = Topic.SCAMS
