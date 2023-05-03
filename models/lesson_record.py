

from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship

from models.base_class import Base


class LessonRecord(Base):
    __tablename__ = 'lesson_record'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE',
                       onupdate='CASCADE'), nullable=False, index=True)
    time = Column(INTEGER(11), nullable=False)
    data = Column(Text, nullable=False)

    lesson = relationship('Lesson')
