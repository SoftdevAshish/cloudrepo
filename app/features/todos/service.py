from app.core.casl import Ability, Action, accessible_by
from app.features.todos.models import Todo, utcnow
from app.features.todos.repository import TodosRepository
from app.features.todos.schemas import TodoCreate, TodoUpdate
from app.features.todos.tasks import notify_todo_created
from app.features.users.models import User


class TodoNotFoundError(Exception):
    pass


class TodosService:
    def __init__(self, repo: TodosRepository, ability: Ability, actor: User, db_name: str) -> None:
        self.repo = repo
        self.ability = ability
        self.actor = actor
        self.db_name = db_name

    def create(self, data: TodoCreate) -> Todo:
        todo = Todo(**data.model_dump(), owner_id=self.actor.id)  # type: ignore[arg-type]
        self.ability.authorize(Action.CREATE, todo)  # conditions on owner_id are enforced
        todo = self.repo.save(todo)
        assert todo.id is not None  # noqa: S101
        notify_todo_created.delay(todo.id, self.db_name)
        return todo

    def list(self, completed: bool | None, offset: int, limit: int) -> list[Todo]:
        where = accessible_by(self.ability, Action.READ, Todo)
        return self.repo.list(where, completed, offset, limit)

    def get(self, todo_id: int, action: Action = Action.READ) -> Todo:
        todo = self.repo.get(todo_id)
        if todo is None:
            raise TodoNotFoundError(todo_id)
        self.ability.authorize(action, todo)
        return todo

    def update(self, todo_id: int, data: TodoUpdate) -> Todo:
        todo = self.get(todo_id, Action.UPDATE)
        todo.sqlmodel_update(data.model_dump(exclude_unset=True))
        todo.updated_at = utcnow()
        return self.repo.save(todo)

    def delete(self, todo_id: int) -> None:
        self.repo.delete(self.get(todo_id, Action.DELETE))
