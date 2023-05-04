import ujson
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from crud.base import CRUDBase
from models.option import Option
from schemas.option import OptionCreate, OptionUpdate


class CRUDOption(CRUDBase[Option, OptionCreate, OptionUpdate]):
    async def getOptions(self, db: AsyncSession) -> Optional[List[Option]]:
        query = select(
            Option
        )
        return (await db.execute(query)).scalars().all()

    async def getByKey(self, db: AsyncSession, key: str) -> Optional[Option]:
        query = select(
            Option
        ).filter(
            Option.key == key
        )
        return (await db.execute(query)).scalars().first()

    async def getSemester(self, db: AsyncSession) -> Optional[Option]:
        query = select(
            Option
        ).filter(
            Option.key == 'semester'
        )
        result = (await db.execute(query)).scalars().first()
        return ujson.loads(result.value) if result else None


option = CRUDOption(Option)
