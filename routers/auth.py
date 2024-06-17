from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from passlib.context import CryptContext
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import Users
from database import SessionLocal
import os
import secrets
import logging
import asyncio
import aiosmtplib

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class UserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expire = datetime.utcnow() + expires_delta
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_verification_token():
    return secrets.token_hex(16)

async def send_email(sender_email, receiver_email, subject, message_body):
    smtp_server = 'smtp.gmail.com'
    port = 587
    sender_password = os.getenv('EMAIL_PASSWORD')

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(message_body, 'plain'))

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=port,
            start_tls=True,
            username=sender_email,
            password=sender_password,
        )
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: UserRequest):
    verification_token = generate_verification_token()
    new_user = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role='user',
        hashed_password=bcrypt_context.hash(create_user_request.password),
        verification_token=verification_token
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Send verification email
    await send_email('jemal.kobakhidze.1@btu.edu.ge', new_user.email, 'Verify Your Email Address', f'Your verification token is: {verification_token}')

    return {"message": "User created successfully"}

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
