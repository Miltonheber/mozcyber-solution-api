import factory

from apps.user.models import Permission, Profile, User

DEFAULT_PASSWORD = "Passw0rd!123"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or DEFAULT_PASSWORD)
        if create:
            self.save(update_fields=["password"])


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    code = factory.Sequence(lambda n: f"res{n}:read")
    name = factory.SelfAttribute("code")


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    code = factory.Sequence(lambda n: f"profile-{n}")
    name = factory.Sequence(lambda n: f"Profile {n}")
