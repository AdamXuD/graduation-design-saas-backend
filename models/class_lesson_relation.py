from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship

from db.base_class import Base
from models.lesson import Lesson
from models.the_class import Class


class ClassLessonRelation(Base):
    __tablename__ = 'class_lesson_relation'

    id = Column(INTEGER(11), primary_key=True)
    class_id = Column(ForeignKey('the_class.id', ondelete='CASCADE',
                      onupdate='CASCADE'), nullable=False, index=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE',
                       onupdate='CASCADE'), nullable=False, index=True)

    _class = relationship('Class')
    lesson = relationship('Lesson')
