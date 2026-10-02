from types import SimpleNamespace

from apps.core.permissions import HasPermission, require_permissions


class FakeView:
    @require_permissions("a:read", "b:read")
    def get(self): ...

    @require_permissions("a:create")
    def post(self): ...

    def delete(self): ...


def _request(method="GET", perms=None, auth=True):
    token = {"permissions": perms or []} if auth else None
    return SimpleNamespace(method=method, auth=token)


def test_decorator_exposes_codes_on_handler():
    assert FakeView.get.required_permissions == ("a:read", "b:read")


def test_requires_all_permissions_of_the_method():
    assert not HasPermission().has_permission(_request("GET", ["a:read"]), FakeView())
    assert HasPermission().has_permission(_request("GET", ["a:read", "b:read", "c"]), FakeView())


def test_permissions_are_granular_per_method():
    assert not HasPermission().has_permission(_request("POST", ["a:read", "b:read"]), FakeView())
    assert HasPermission().has_permission(_request("POST", ["a:create"]), FakeView())


def test_undecorated_method_only_needs_authentication():
    assert HasPermission().has_permission(_request("DELETE", []), FakeView())


def test_missing_token_denied():
    assert not HasPermission().has_permission(_request("GET", auth=False), FakeView())
