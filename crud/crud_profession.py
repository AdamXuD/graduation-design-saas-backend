from typing import Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from crud.base import CRUDBase
from models.profession import Profession
from schemas.profession import ProfessionCreate, ProfessionUpdate


class CRUDProfession(CRUDBase[Profession, ProfessionCreate, ProfessionUpdate]):
    async def getPaginatedMultiByOptionalKeyword(
            self,
            db: AsyncSession,
            keyword: Optional[str] = None,
            offset: int = 0,
            limit: int = 10) -> Tuple[List[Profession], int]:
        if keyword == None or keyword == "":
            baseQuery = select(
                Profession
            )
        else:
            baseQuery = select(
                Profession
            ).where(
                Profession.name.like(f"%{keyword}%")
            )

        totalQuery = select(func.count()).select_from(baseQuery)
        paginateQuery = baseQuery.offset(offset).limit(limit)

        return (await db.execute(paginateQuery)).scalars().all(), (await db.execute(totalQuery)).scalar()


profession = CRUDProfession(Profession)
