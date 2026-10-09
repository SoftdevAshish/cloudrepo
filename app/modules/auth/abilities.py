import logging
from collections.abc import Iterable

from app.core.casl import Ability, Rule, interpolate
from app.modules.auth.constants import SYSTEM
from app.modules.roles.models import Policy
from app.modules.roles.registry import validate_rule
from app.modules.users.models import User

logger = logging.getLogger(__name__)

__all__ = ["SYSTEM", "define_abilities"]


def define_abilities(user: User, policies: Iterable[Policy]) -> Ability:
    """Build the user's ability from the policies stored for their role.

    Placeholders such as `${user.id}` are resolved against the current user. A stored rule that
    no longer validates (e.g. a column was renamed) is skipped and logged rather than failing
    every request.
    """
    rules: list[Rule] = []
    for policy in policies:
        try:
            validate_rule(policy.action, policy.subject, policy.conditions, policy.fields)
            conditions = (
                interpolate(policy.conditions, {"user": user}) if policy.conditions else None
            )
        except ValueError:
            logger.warning("Skipping invalid policy id=%s", policy.id)
            continue
        rules.append(
            Rule(
                policy.action,
                policy.subject,
                conditions,
                tuple(policy.fields) if policy.fields else None,
                policy.inverted,
            )
        )
    return Ability(rules)
