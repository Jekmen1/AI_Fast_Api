from fastapi import status, Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from models import Users
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix='/users',
    tags=['users']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)



@router.get('/', status_code=status.HTTP_200_OK)
async def get_users(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    return db.query(Users).filter(Users.id == user.get('id')).first()




