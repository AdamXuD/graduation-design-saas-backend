from sqlalchemy import Column, Text, String, ForeignKey
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import relationship

from models.base_class import Base


class Dynamic(Base):
    __tablename__ = 'dynamic'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE',
                       onupdate='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_time = Column(BIGINT(20), nullable=False)
    scope = Column(String(10), nullable=False)
    user_id = Column(String(10), nullable=False)

    lesson = relationship('Lesson')
