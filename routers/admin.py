from fastapi import status, FastAPI, Depends, HTTPException, Path, APIRouter
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from models import Users



router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



@router.get('/', status_code=status.HTTP_200_OK)
async def get_users(user: user_dependency, db: db_dependency):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication failed!')
    return db.query(Users).all()

