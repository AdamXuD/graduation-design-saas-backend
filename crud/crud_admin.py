from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core import security
from crud.base import CRUDBase
from models.admin import Admin
from schemas.admin import AdminCreate, AdminUpdate


class CRUDAdmin(CRUDBase[Admin, AdminCreate, AdminUpdate]):
    async def authenticate(self, db: AsyncSession, id: str, password: str) -> Optional[Admin]:
        admin = await self.get(db, id=id)
        if not admin:
            return None
        if not security.verifyPassword(password, admin.hashed_password):
            return None
        return admin


admin = CRUDAdmin(Admin)
