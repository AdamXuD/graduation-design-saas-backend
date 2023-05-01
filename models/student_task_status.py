from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER

from db.base_class import Base
from models.student import Student
from models.task import Task


class StudentTaskStatus(Base):
    __tablename__ = 'student_task_status'

    id = Column(INTEGER(11), primary_key=True)
    student_id = Column(ForeignKey('student.id', ondelete='CASCADE',
                        onupdate='CASCADE'), nullable=False, index=True)
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE',
                     onupdate='CASCADE'), nullable=False, index=True)
    status = Column(String(16), nullable=False)
    text = Column(Text, nullable=False)
    files = Column(Text, nullable=False)
    score = Column(INTEGER(11), nullable=False)

    student = relationship('Student')
    task = relationship('Task')
