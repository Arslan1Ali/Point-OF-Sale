from __future__ import annotations

from dataclasses import dataclass

from app.application.auth.ports import UserRepositoryPort
from app.domain.auth.entities import User, UserRole
from app.shared.pagination import Page, PageMeta, PageParams


@dataclass
class ListUsersInput:
    params: PageParams
    email: str | None = None
    role: UserRole | None = None
    active: bool | None = None


@dataclass
class ListUsersResult:
    items: list[User]
    meta: PageMeta


class ListUsersUseCase:
    def __init__(self, repo: UserRepositoryPort):
        self._repo = repo

    async def execute(self, data: ListUsersInput) -> ListUsersResult:
        items, total = await self._repo.search(
            email=data.email,
            role=data.role,
            active=data.active,
            params=data.params,
        )
        page = Page.build(items=list(items), total=total, params=data.params)
        return ListUsersResult(items=page.items, meta=page.meta)
