from app.core.casl import Ability, AbilityBuilder, Action
from app.modules.todos.models import Todo
from app.modules.users.models import Role, User

SYSTEM = "System"  # operational endpoints: tasks, database list


def define_abilities(user: User) -> Ability:
    """The single place that states who may do what (cf. a CASL ability factory)."""
    builder = AbilityBuilder()
    if user.role == Role.ADMIN:
        builder.can(Action.MANAGE, "all")
    else:
        builder.can(Action.MANAGE, Todo, {"owner_id": user.id})
        builder.can([Action.READ, Action.UPDATE], User, {"id": user.id})
        builder.cannot(Action.UPDATE, User, fields=["role", "is_active"])
    return builder.build()
