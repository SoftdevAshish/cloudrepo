"""Unit tests for the policy engine, without HTTP (REQ-AUTHZ-1..3)."""

from app.models import Todo, User
from app.policies import Action, can

alice = User(id=1, email="a@x.com", password_hash="x", role="user")
bob = User(id=2, email="b@x.com", password_hash="x", role="user")
admin = User(id=3, email="c@x.com", password_hash="x", role="admin")
ghost = User(id=4, email="d@x.com", password_hash="x", role="ghost")
todo_of_alice = Todo(id=1, owner_id=1, title="t")


def test_user_policy_is_owner_only():
    for action in Action:
        assert can(alice, action, todo_of_alice)
        assert not can(bob, action, todo_of_alice)


def test_admin_policy_allows_everything():
    for action in Action:
        assert can(admin, action, todo_of_alice)


def test_default_deny_for_unknown_role():
    for action in Action:
        assert not can(ghost, action, todo_of_alice)
        assert not can(ghost, action)


def test_class_level_check_without_instance():
    assert can(alice, Action.CREATE)
