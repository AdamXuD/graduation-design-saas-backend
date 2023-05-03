from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import INTEGER

from models.base_class import Base


class Profession(Base):
    __tablename__ = 'profession'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(24), nullable=False)
