from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, func, select

from app.modules.roles.models import Policy, Role
from app.modules.users.models import User


class RolesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # roles
    def get(self, role_id: int) -> Role | None:
        return self.session.get(Role, role_id)

    def get_by_name(self, name: str) -> Role | None:
        return self.session.exec(select(Role).where(Role.name == name)).first()

    def find(self, where: ColumnElement[bool]) -> list[Role]:
        return list(self.session.exec(select(Role).where(where).order_by(col(Role.id))))

    def save(self, role: Role) -> Role:
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def count_users(self, role_name: str) -> int:
        stmt = select(func.count()).select_from(User).where(User.role == role_name)
        return int(self.session.exec(stmt).one())

    def delete(self, role: Role) -> None:
        for policy in self.policies(role.id):  # type: ignore[arg-type]
            self.session.delete(policy)
        self.session.delete(role)
        self.session.commit()

    # policies
    def policies(self, role_id: int) -> list[Policy]:
        stmt = select(Policy).where(Policy.role_id == role_id).order_by(col(Policy.id))
        return list(self.session.exec(stmt))

    def policies_for_role_name(self, role_name: str) -> list[Policy]:
        stmt = (
            select(Policy)
            .join(Role, col(Role.id) == col(Policy.role_id))
            .where(Role.name == role_name)
            .order_by(col(Policy.id))
        )
        return list(self.session.exec(stmt))

    def get_policy(self, policy_id: int) -> Policy | None:
        return self.session.get(Policy, policy_id)

    def save_policy(self, policy: Policy) -> Policy:
        self.session.add(policy)
        self.session.commit()
        self.session.refresh(policy)
        return policy

    def delete_policy(self, policy: Policy) -> None:
        self.session.delete(policy)
        self.session.commit()

    def replace_policies(self, role_id: int, new: list[Policy]) -> list[Policy]:
        """Swap a role's whole rule set in one transaction (all or nothing)."""
        for old in self.policies(role_id):
            self.session.delete(old)
        self.session.add_all(new)
        self.session.commit()
        return self.policies(role_id)
