from sqlalchemy.exc import IntegrityError

from app.core.casl import Ability, Action, accessible_by
from app.features.roles.models import ADMIN_ROLE, Policy, Role
from app.features.roles.repository import RolesRepository
from app.features.roles.schemas import PolicyIn, RoleCreate, RoleUpdate


class RoleError(Exception):
    status_code = 400


class NotFoundError(RoleError):
    status_code = 404


class ConflictError(RoleError):
    status_code = 409


class RolesService:
    def __init__(self, repo: RolesRepository, ability: Ability) -> None:
        self.repo = repo
        self.ability = ability

    # ---- roles
    def list_roles(self) -> list[Role]:
        return self.repo.find(accessible_by(self.ability, Action.READ, Role))

    def get_role(self, role_id: int, action: Action = Action.READ) -> Role:
        role = self.repo.get(role_id)
        if role is None:
            raise NotFoundError("Role not found")
        self.ability.authorize(action, role)
        return role

    def create_role(self, data: RoleCreate) -> Role:
        role = Role(name=data.name, description=data.description)
        self.ability.authorize(Action.CREATE, role)
        if self.repo.get_by_name(data.name) is not None:
            raise ConflictError(f"Role '{data.name}' already exists")
        try:
            return self.repo.save(role)
        except IntegrityError:
            self.repo.session.rollback()
            raise ConflictError(f"Role '{data.name}' already exists") from None

    def update_role(self, role_id: int, data: RoleUpdate) -> Role:
        role = self.get_role(role_id, Action.UPDATE)
        role.description = data.description
        return self.repo.save(role)

    def delete_role(self, role_id: int) -> None:
        role = self.get_role(role_id, Action.DELETE)
        if role.is_system:
            raise ConflictError("System roles cannot be deleted")
        if self.repo.count_users(role.name) > 0:
            raise ConflictError("Role is still assigned to users; reassign them first")
        self.repo.delete(role)

    # ---- policies
    @staticmethod
    def _ensure_editable(role: Role) -> None:
        if role.name == ADMIN_ROLE:
            raise ConflictError("The admin role's policies cannot be changed")

    def list_policies(self, role_id: int) -> list[Policy]:
        role = self.get_role(role_id)
        return [p for p in self.repo.policies(role.id) if self.ability.can(Action.READ, p)]  # type: ignore[arg-type]

    @staticmethod
    def _to_policy(role_id: int, data: PolicyIn) -> Policy:
        return Policy(role_id=role_id, **data.model_dump())

    def add_policy(self, role_id: int, data: PolicyIn) -> Policy:
        role = self.get_role(role_id, Action.UPDATE)
        self._ensure_editable(role)
        policy = self._to_policy(role.id, data)  # type: ignore[arg-type]
        self.ability.authorize(Action.CREATE, policy)
        return self.repo.save_policy(policy)

    def replace_policies(self, role_id: int, items: list[PolicyIn]) -> list[Policy]:
        role = self.get_role(role_id, Action.UPDATE)
        self._ensure_editable(role)
        new = [self._to_policy(role.id, d) for d in items]  # type: ignore[arg-type]
        for policy in new:
            self.ability.authorize(Action.CREATE, policy)
        return self.repo.replace_policies(role.id, new)  # type: ignore[arg-type]

    def _get_policy(self, policy_id: int, action: Action) -> Policy:
        policy = self.repo.get_policy(policy_id)
        if policy is None:
            raise NotFoundError("Policy not found")
        self.ability.authorize(action, policy)
        role = self.repo.get(policy.role_id)
        if role is not None:
            self._ensure_editable(role)
        return policy

    def update_policy(self, policy_id: int, data: PolicyIn) -> Policy:
        policy = self._get_policy(policy_id, Action.UPDATE)
        for key, value in data.model_dump().items():
            setattr(policy, key, value)
        return self.repo.save_policy(policy)

    def delete_policy(self, policy_id: int) -> None:
        self.repo.delete_policy(self._get_policy(policy_id, Action.DELETE))
