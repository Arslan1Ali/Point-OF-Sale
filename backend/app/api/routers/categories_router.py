from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import ALL_AUTHENTICATED_ROLES, MANAGEMENT_ROLES, require_roles
from app.api.dependencies.cache import get_cache_service
from app.application.common.cache import CacheService
from app.api.schemas.category import CategoryCreate, CategoryListMetaOut, CategoryListOut, CategoryOut
from app.application.catalog.use_cases.create_category import (
    CreateCategoryInput,
    CreateCategoryUseCase,
)
from app.application.catalog.use_cases.list_categories import ListCategoriesInput, ListCategoriesUseCase
from app.domain.auth.entities import User
from app.infrastructure.db.repositories.category_repository import SqlAlchemyCategoryRepository
from app.infrastructure.db.session import get_session

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
    cache: CacheService = Depends(get_cache_service),
    _: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> CategoryOut:
    repo = SqlAlchemyCategoryRepository(session)
    use_case = CreateCategoryUseCase(repo)
    category = await use_case.execute(
        CreateCategoryInput(
            name=payload.name,
            description=payload.description,
        )
    )
    await cache.clear_prefix("categories:list")
    return CategoryOut.model_validate(category)


@router.get("", response_model=CategoryListOut)
async def list_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1),
    session: AsyncSession = Depends(get_session),
    cache: CacheService = Depends(get_cache_service),
    _: User = Depends(require_roles(*ALL_AUTHENTICATED_ROLES)),
) -> CategoryListOut:
    cache_key = f"categories:list:{page}:{limit}:{search}"
    cached = await cache.get(cache_key)
    if cached:
        return CategoryListOut(**cached)

    repo = SqlAlchemyCategoryRepository(session)
    use_case = ListCategoriesUseCase(repo)
    result = await use_case.execute(
        ListCategoriesInput(page=page, limit=limit, search=search)
    )
    items = [CategoryOut.model_validate(cat) for cat in result.categories]
    meta = CategoryListMetaOut(
        page=result.page,
        limit=result.limit,
        total=result.total,
        pages=result.pages,
    )
    response = CategoryListOut(items=items, meta=meta)
    await cache.set(cache_key, response.model_dump(), ttl=300)
    return response
