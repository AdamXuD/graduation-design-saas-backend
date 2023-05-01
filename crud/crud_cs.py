from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from crud.base import CRUDBase
from models.cloud_share import CloudShare
from schemas.cloud_share import CloudShareCreate, CloudShareUpdate


class CRUDCloudShare(CRUDBase[CloudShare, CloudShareCreate, CloudShareUpdate]):
    async def getByKey(self, db: AsyncSession, key: str) -> Optional[CloudShare]:
        query = select(
            CloudShare
        ).filter(
            CloudShare.key == key
        )
        return (await db.execute(query)).scalars().first()

    async def getByPath(self, db: AsyncSession, path: str) -> Optional[CloudShare]:
        query = select(
            CloudShare
        ).filter(
            CloudShare.path == path
        )
        return (await db.execute(query)).scalars().first()


cloudShare = CRUDCloudShare(CloudShare)
