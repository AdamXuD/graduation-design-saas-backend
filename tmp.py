# coding: utf-8
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, SMALLINT, TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class CloudShare(Base):
    __tablename__ = 'cloud_share'

    id = Column(INTEGER(11), primary_key=True)
    key = Column(String(6), nullable=False)
    type = Column(String(6), nullable=False)
    path = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    expire = Column(INTEGER(11), nullable=False)


class Profession(Base):
    __tablename__ = 'profession'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(24), nullable=False)


class Teacher(Base):
    __tablename__ = 'teacher'

    id = Column(String(10), primary_key=True)
    name = Column(String(16), nullable=False)
    phone = Column(String(16), nullable=False)
    email = Column(String(255), nullable=False)
    introduction = Column(Text, nullable=False)
    avatar = Column(Text, nullable=False)
    hashed_password = Column(String(60), nullable=False)


class Lesson(Base):
    __tablename__ = 'lesson'

    id = Column(INTEGER(11), primary_key=True)
    thumbnail = Column(Text, nullable=False)
    title = Column(String(32), nullable=False)
    teacher_id = Column(ForeignKey('teacher.id', onupdate='CASCADE'), nullable=False, index=True)
    year = Column(SMALLINT(6), nullable=False)
    term = Column(TINYINT(4), nullable=False)
    is_over = Column(TINYINT(4), nullable=False)
    notice = Column(Text, nullable=False)
    courseware = Column(Text, nullable=False)

    teacher = relationship('Teacher')


class TheClas(Base):
    __tablename__ = 'the_class'

    id = Column(INTEGER(11), primary_key=True)
    grade = Column(SMALLINT(6), nullable=False)
    profession_id = Column(ForeignKey('profession.id', onupdate='CASCADE'), nullable=False, index=True)
    name = Column(String(32), nullable=False)

    profession = relationship('Profession')


class ClassLessonRelation(Base):
    __tablename__ = 'class_lesson_relation'

    id = Column(INTEGER(11), primary_key=True)
    class_id = Column(ForeignKey('the_class.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

    _class = relationship('TheClas')
    lesson = relationship('Lesson')


class Dynamic(Base):
    __tablename__ = 'dynamic'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_time = Column(BIGINT(20), nullable=False)
    scope = Column(String(10), nullable=False)
    user_id = Column(String(10), nullable=False)

    lesson = relationship('Lesson')


class LessonRecord(Base):
    __tablename__ = 'lesson_record'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    time = Column(INTEGER(11), nullable=False)
    data = Column(Text, nullable=False)

    lesson = relationship('Lesson')


class Student(Base):
    __tablename__ = 'student'

    id = Column(String(10), primary_key=True)
    name = Column(String(16), nullable=False)
    class_id = Column(ForeignKey('the_class.id', onupdate='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(16), nullable=False)
    introduction = Column(Text, nullable=False)
    avatar = Column(Text, nullable=False)
    hashed_password = Column(String(60), nullable=False)

    _class = relationship('TheClas')


class Task(Base):
    __tablename__ = 'task'

    id = Column(INTEGER(11), primary_key=True)
    lesson_id = Column(ForeignKey('lesson.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_time = Column(BIGINT(20), nullable=False)
    deadline = Column(BIGINT(20), nullable=False)

    lesson = relationship('Lesson')


class StudentTaskStatu(Base):
    __tablename__ = 'student_task_status'

    id = Column(INTEGER(11), primary_key=True)
    student_id = Column(ForeignKey('student.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    task_id = Column(ForeignKey('task.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    status = Column(String(16), nullable=False)
    text = Column(Text, nullable=False)
    files = Column(Text, nullable=False)
    score = Column(INTEGER(11), nullable=False)

    student = relationship('Student')
    task = relationship('Task')
