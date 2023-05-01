from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.mysql import SMALLINT, INTEGER
from sqlalchemy.orm import relationship

from db.base_class import Base
from models.profession import Profession


class Class(Base):
    __tablename__ = 'the_class'

    id = Column(INTEGER(11), primary_key=True)
    grade = Column(SMALLINT(6), nullable=False)
    profession_id = Column(ForeignKey(
        'profession.id', onupdate='CASCADE'), nullable=False, index=True)
    name = Column(String(32), nullable=False)

    profession = relationship('Profession')
