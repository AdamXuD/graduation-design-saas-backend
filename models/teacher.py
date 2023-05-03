from sqlalchemy import Column, String, Text
from models.base_class import Base


class Teacher(Base):
    __tablename__ = 'teacher'

    id = Column(String(10), primary_key=True)
    name = Column(String(16), nullable=False)
    phone = Column(String(16), nullable=False)
    email = Column(String(255), nullable=False)
    introduction = Column(Text, nullable=False)
    avatar = Column(Text, nullable=False)
    hashed_password = Column(String(60), nullable=False)
