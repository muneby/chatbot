from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import MessageInput, Bot
from app.services import get_ai_response

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/demo-bots")
def get_demo_bots(db: Session = Depends(get_db)):
    bots = db.query(Bot).filter(Bot.is_demo == True).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "bot_persona_name": b.bot_persona_name,
            "business_type": b.business_type,
            "welcome_message": b.welcome_message,
            "primary_color": b.primary_color,
        }
        for b in bots
    ]

@router.get("/chat/bot/{bot_id}")
def get_bot_info(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    return {
        "id": bot.id,
        "name": bot.name,
        "welcome_message": bot.welcome_message,
        "tone": bot.tone,
        "primary_color": bot.primary_color,
        "bot_persona_name": bot.bot_persona_name,
    }

@router.post("/chat")
def chat_endpoint(message: MessageInput, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == message.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود 🚫")

    try:
        history = [{"role": m.role, "content": m.content} for m in message.history]
        response = get_ai_response(message.text, message.bot_id, db, history)
        return {"response": response}
    except Exception as e:
        return {"response": f"عذراً، حدث خطأ في المعالجة: {str(e)}"}