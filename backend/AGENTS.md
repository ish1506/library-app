# Backend Agent Instructions

## FastAPI dependency defaults

Do not call `Depends(...)` directly in a function argument default. Define dependency objects at module scope and reference those objects in endpoint or dependency signatures instead.

Example:

```python
DB_DEPENDENCY = Depends(get_db)


async def handler(db: AsyncSession = DB_DEPENDENCY) -> Response:
    ...
```

Apply this pattern consistently to nested dependencies as well:

```python
CURRENT_USER_DEPENDENCY = Depends(get_current_user)


async def require_admin(user: User = CURRENT_USER_DEPENDENCY) -> User:
    ...
```
