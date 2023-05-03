from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from models.base_class import Base
from models.class_ import Class


class Student(Base):
    __tablename__ = 'student'

    id = Column(String(10), primary_key=True)
    name = Column(String(16), nullable=False)
    class_id = Column(ForeignKey('class.id', onupdate='CASCADE'),
                      nullable=False, index=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(16), nullable=False)
    introduction = Column(Text, nullable=False)
    avatar = Column(Text, nullable=False)
    hashed_password = Column(String(60), nullable=False)

    _class = relationship('Class')
