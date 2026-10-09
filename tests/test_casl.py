import pytest
from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.core.casl import ALL, AbilityBuilder, Action, ForbiddenError, accessible_by


class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    author_id: int
    status: str = "draft"


class Comment:
    pass


def test_nothing_allowed_by_default():
    ability = AbilityBuilder().build()
    assert ability.cannot(Action.READ, Post)


def test_manage_all_is_a_wildcard():
    ability = AbilityBuilder().can(Action.MANAGE, ALL).build()
    assert ability.can(Action.DELETE, Post)
    assert ability.can(Action.READ, "anything")


def test_conditions_apply_to_instances_but_not_classes():
    ability = AbilityBuilder().can(Action.UPDATE, Post, {"author_id": 1}).build()
    assert ability.can(Action.UPDATE, Post)  # class-level: could update some post
    assert ability.can(Action.UPDATE, Post(author_id=1))
    assert not ability.can(Action.UPDATE, Post(author_id=2))
    assert not ability.can(Action.READ, Post(author_id=1))


def test_later_cannot_overrides_earlier_can():
    ability = (
        AbilityBuilder()
        .can(Action.MANAGE, Post)
        .cannot(Action.DELETE, Post, {"status": "published"})
        .build()
    )
    assert ability.can(Action.DELETE, Post(author_id=1, status="draft"))
    assert not ability.can(Action.DELETE, Post(author_id=1, status="published"))
    assert ability.can(Action.DELETE, Post)  # conditional cannot doesn't deny the class


def test_operators():
    ability = AbilityBuilder().can(Action.READ, Post, {"status": {"$in": ["a", "b"]}}).build()
    assert ability.can(Action.READ, Post(author_id=1, status="a"))
    assert not ability.can(Action.READ, Post(author_id=1, status="c"))


def test_field_level_rules():
    ability = (
        AbilityBuilder()
        .can(Action.UPDATE, Post)
        .cannot(Action.UPDATE, Post, fields=["status"])
        .build()
    )
    assert ability.can(Action.UPDATE, Post(author_id=1), "author_id")
    assert not ability.can(Action.UPDATE, Post(author_id=1), "status")
    assert ability.can(Action.UPDATE, Post(author_id=1))


def test_authorize_raises_forbidden_error():
    ability = AbilityBuilder().build()
    with pytest.raises(ForbiddenError, match="Cannot read Post"):
        ability.authorize(Action.READ, Post)


def test_lists_of_actions_and_subjects():
    ability = AbilityBuilder().can([Action.READ, Action.UPDATE], [Post, Comment]).build()
    assert ability.can(Action.UPDATE, Comment)
    assert not ability.can(Action.DELETE, Comment)


def test_accessible_by_builds_sql_filter():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    ability = (
        AbilityBuilder()
        .can(Action.READ, Post, {"author_id": 1})
        .can(Action.READ, Post, {"status": "published"})
        .cannot(Action.READ, Post, {"status": "banned"})
        .build()
    )
    with Session(engine) as s:
        s.add_all(
            [
                Post(author_id=1, status="draft"),  # own          -> visible
                Post(author_id=2, status="draft"),  # other draft  -> hidden
                Post(author_id=2, status="published"),  # public   -> visible
                Post(author_id=1, status="banned"),  # banned      -> hidden
            ]
        )
        s.commit()
        rows = s.exec(select(Post).where(accessible_by(ability, Action.READ, Post))).all()
    assert sorted((p.author_id, p.status) for p in rows) == [(1, "draft"), (2, "published")]
    nothing = AbilityBuilder().build()
    with Session(engine) as s:
        assert s.exec(select(Post).where(accessible_by(nothing, Action.READ, Post))).all() == []


def test_interpolate_resolves_placeholders_keeping_types():
    from app.core.casl import interpolate

    class U:
        id = 7
        email = "a@b.c"

    cond = {"owner_id": "${user.id}", "x": {"$in": ["${user.email}", "lit"]}, "n": 1}
    assert interpolate(cond, {"user": U()}) == {
        "owner_id": 7,
        "x": {"$in": ["a@b.c", "lit"]},
        "n": 1,
    }


def test_interpolate_refuses_unknown_names_and_private_attrs():
    from app.core.casl import interpolate

    with pytest.raises(ValueError, match="unknown placeholder"):
        interpolate("${other.id}", {"user": object()})
    with pytest.raises(ValueError, match="unknown placeholder"):
        interpolate("${user._secret}", {"user": object()})
