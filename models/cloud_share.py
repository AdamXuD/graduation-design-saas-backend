from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.mysql import INTEGER
from models.base_class import Base


class CloudShare(Base):
    __tablename__ = 'cloud_share'

    id = Column(INTEGER(11), primary_key=True)
    key = Column(String(6), nullable=False)
    type = Column(String(6), nullable=False)
    path = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    expire = Column(INTEGER(11), nullable=False)
