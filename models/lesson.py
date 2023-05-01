from sqlalchemy import SMALLINT, Column, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import SMALLINT, TINYINT, INTEGER
from sqlalchemy.orm import relationship

from db.base_class import Base
from models.teacher import Teacher


class Lesson(Base):
    __tablename__ = 'lesson'

    id = Column(INTEGER(11), primary_key=True)
    thumbnail = Column(Text, nullable=False)
    title = Column(String(32), nullable=False)
    teacher_id = Column(ForeignKey(
        'teacher.id', onupdate='CASCADE'), nullable=False, index=True)
    year = Column(SMALLINT(6), nullable=False)
    term = Column(TINYINT(4), nullable=False)
    is_over = Column(TINYINT(4), nullable=False)
    notice = Column(Text, nullable=False)
    courseware = Column(Text, nullable=False)

    teacher = relationship('Teacher')
