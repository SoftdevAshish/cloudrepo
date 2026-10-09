from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.core.casl import Ability, Action
from app.core.database import get_session
from app.modules.auth.dependencies import check_policies, get_ability
from app.modules.roles import registry
from app.modules.roles.models import Policy, Role
from app.modules.roles.repository import RolesRepository
from app.modules.roles.schemas import (
    PolicyIn,
    PolicyRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)
from app.modules.roles.service import RoleError, RolesService

router = APIRouter(prefix="/roles", tags=["roles"])
policies_router = APIRouter(prefix="/policies", tags=["policies"])


def get_roles_service(
    session: Session = Depends(get_session), ability: Ability = Depends(get_ability)
) -> RolesService:
    return RolesService(RolesRepository(session), ability)


def _http(exc: RoleError) -> HTTPException:
    return HTTPException(exc.status_code, str(exc))


@router.get(
    "", response_model=list[RoleRead], dependencies=[Depends(check_policies(Action.READ, Role))]
)
def list_roles(service: RolesService = Depends(get_roles_service)) -> list[Role]:
    return service.list_roles()


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_policies(Action.CREATE, Role))],
)
def create_role(data: RoleCreate, service: RolesService = Depends(get_roles_service)) -> Role:
    try:
        return service.create_role(data)
    except RoleError as exc:
        raise _http(exc) from None


@router.get("/{role_id}", response_model=RoleRead)
def read_role(role_id: int, service: RolesService = Depends(get_roles_service)) -> Role:
    try:
        return service.get_role(role_id)
    except RoleError as exc:
        raise _http(exc) from None


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(
    role_id: int, data: RoleUpdate, service: RolesService = Depends(get_roles_service)
) -> Role:
    try:
        return service.update_role(role_id, data)
    except RoleError as exc:
        raise _http(exc) from None


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, service: RolesService = Depends(get_roles_service)) -> Response:
    try:
        service.delete_role(role_id)
    except RoleError as exc:
        raise _http(exc) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{role_id}/policies", response_model=list[PolicyRead])
def list_policies(role_id: int, service: RolesService = Depends(get_roles_service)) -> list[Policy]:
    try:
        return service.list_policies(role_id)
    except RoleError as exc:
        raise _http(exc) from None


@router.post("/{role_id}/policies", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def add_policy(
    role_id: int, data: PolicyIn, service: RolesService = Depends(get_roles_service)
) -> Policy:
    try:
        return service.add_policy(role_id, data)
    except RoleError as exc:
        raise _http(exc) from None


@router.put("/{role_id}/policies", response_model=list[PolicyRead])
def replace_policies(
    role_id: int, data: list[PolicyIn], service: RolesService = Depends(get_roles_service)
) -> list[Policy]:
    """Replace the role's whole rule set atomically."""
    try:
        return service.replace_policies(role_id, data)
    except RoleError as exc:
        raise _http(exc) from None


@policies_router.get("/meta", dependencies=[Depends(check_policies(Action.READ, Policy))])
def policy_meta() -> dict[str, Any]:
    """Valid actions, subjects (with their fields), operators and placeholders."""
    return registry.describe()


@policies_router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: int, data: PolicyIn, service: RolesService = Depends(get_roles_service)
) -> Policy:
    try:
        return service.update_policy(policy_id, data)
    except RoleError as exc:
        raise _http(exc) from None


@policies_router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: int, service: RolesService = Depends(get_roles_service)) -> Response:
    try:
        service.delete_policy(policy_id)
    except RoleError as exc:
        raise _http(exc) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
