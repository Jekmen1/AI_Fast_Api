import google.generativeai as genai
from fastapi import Depends, HTTPException, APIRouter, status, Path
from models import Users, Chat_History
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from .users import user_dependency
import os

api_key = os.getenv('API_KEY')

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

genai.configure(api_key=api_key)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Message(BaseModel):
    message: str


@router.get('/chat_history', status_code=status.HTTP_200_OK)
async def get_user_chat_hisroty(user: user_dependency, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user.get('id')).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_history_records = db.query(Chat_History).filter(Chat_History.user_id == user.id).all()
    chat_history = [
            {
                "username": user.username,
                "message": record.message,
                "response": record.response,
                "timestamp": record.timestamp
            }
            for record in chat_history_records
        ]

    return chat_history

@router.post("/send_message/", status_code=status.HTTP_201_CREATED)
async def send_message(user: user_dependency, msg: Message, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == user.get('id')).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(msg.message)

    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response")


    chat_history = Chat_History(
        user_id=user.id,
        message=msg.message,
        response=response.text
    )
    db.add(chat_history)
    db.commit()

    return {"user": user.username, "response": response.text}

@router.delete('/delete_chat_history/{chat_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_chat_history(user: user_dependency, db: Session = Depends(get_db), chat_id: int = Path(gt=0)):
    user = db.query(Users).filter(Users.id == user.get('id')).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_history = db.query(Chat_History).filter(Chat_History.user_id == user.id).all()
    if chat_history is None:
        raise HTTPException(status_code=404, detail='todo not found')
    db.query(Chat_History).filter(Chat_History.user_id == user.id).delete(synchronize_session=False)
    db.commit()

    return {"message": f"Deleted {chat_history} chat history entries for user {user.username}"}


