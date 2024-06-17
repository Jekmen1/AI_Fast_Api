from fastapi import status, FastAPI, Depends, HTTPException, Path, APIRouter
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .auth import get_current_user
from models import Users, Chat_History



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

@router.get('/chat_history/{user_id}', status_code=status.HTTP_200_OK)
async def get_user_chat_history(user: user_dependency, db: Session = Depends(get_db), user_id: int = Path(..., gt=0)):

    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=401, detail='Authentication failed!')


    target_user = db.query(Users).filter(Users.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_history_records = db.query(Chat_History).filter(Chat_History.user_id == target_user.id).all()


    chat_history = [
        {
            "username": target_user.username,
            "message": record.message,
            "response": record.response,
            "timestamp": record.timestamp
        }
        for record in chat_history_records
    ]

    return chat_history
