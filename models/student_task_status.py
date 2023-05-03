from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER

from models.base_class import Base
from models.student import Student
from models.task import Task


class StudentTaskStatus(Base):
    __tablename__ = 'student_task_status'
    __table_args__ = (
        Index("student_id", "student_id", "task_id", unique=True),
    )

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
