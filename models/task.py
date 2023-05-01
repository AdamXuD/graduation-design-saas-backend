from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import relationship

from db.base_class import Base
from models.lesson import Lesson


class Task(Base):
    __tablename__ = 'task'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE',
                       onupdate='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_time = Column(BIGINT(20), nullable=False)
    deadline = Column(BIGINT(20), nullable=False)

    lesson = relationship('Lesson')
