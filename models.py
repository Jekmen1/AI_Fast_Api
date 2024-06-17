from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime,  CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

class Users(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)
    is_verified = Column(Boolean, server_default='false', nullable=False)
    verification_token = Column(String(255), unique=True, nullable=True)

    chat_histories = relationship('Chat_History', back_populates='user')
    __table_args__ = (
        CheckConstraint("role = 'user'", name='check_role_user'),
    )


class Chat_History(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


    user = relationship('Users', back_populates='chat_histories')


