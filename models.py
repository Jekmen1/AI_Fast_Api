from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Users(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)


