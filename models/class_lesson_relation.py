from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship

from models.base_class import Base
from models.lesson import Lesson
from models.class_ import Class


class ClassLessonRelation(Base):
    __tablename__ = 'class_lesson_relation'
    __table_args__ = (
        Index("class_id", "class_id", "lesson_id", unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    class_id = Column(ForeignKey('class.id', ondelete='CASCADE',
                      onupdate='CASCADE'), nullable=False, index=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE',
                       onupdate='CASCADE'), nullable=False, index=True)

    _class = relationship('Class')
    lesson = relationship('Lesson')
