from sqlalchemy import Column
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.mysql import INTEGER

from db.base_class import Base


class Option(Base):
    __tablename__ = 'option'

    id = Column(INTEGER(11), primary_key=True)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
