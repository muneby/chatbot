from fastapi import APIRouter, Request, HTTPException
from .models import MessageInput
from .services import get_ai_response, system_instruction

router = APIRouter()

# الرمز السري للمصافحة (نفسه اللي بنكتبه في فيسبوك)
VERIFY_TOKEN = "saudi_vision_2030"

# الذاكرة المؤقتة
chat_history = [{"role": "system", "content": system_instruction}]

# ---------------------------------------------------------
# 1. نقطة المصافحة (GET Webhook)
# Meta تزور هذا الرابط عشان تتأكد أن السيرفر شغال
# ---------------------------------------------------------
@router.get("/webhook")
async def verify_webhook(request: Request):
    # استقبال البيانات من رابط المصافحة
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")

    # التحقق: هل الرمز صحيح؟
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ WEBHOOK_VERIFIED")
        # لازم نرجع رقم التحدي (challenge) كرقم صحيح
        return int(hub_challenge)
    
    # لو الرمز غلط
    raise HTTPException(status_code=403, detail="Verification failed")

# ---------------------------------------------------------
# 2. نقطة استلام الرسائل (POST Webhook)
# هنا توصل رسائل الواتساب الحقيقية
# ---------------------------------------------------------
@router.post("/webhook")
async def receive_whatsapp_message(request: Request):
    data = await request.json()
    
    # طباعة الرسالة في سجلات السيرفر (Logs) عشان نشوفها
    print("📩 Received Data:", data)
    
    # (لاحقاً بنضيف هنا كود الرد بالذكاء الاصطناعي)
    
    return {"status": "received"}

# ---------------------------------------------------------
# نقاط الشات القديمة (عشان الموقع يظل شغال)
# ---------------------------------------------------------
@router.post("/chat")
async def chat_endpoint(data: MessageInput):
    reply = await get_ai_response(data.text, chat_history)
    return {"reply": reply}

@router.post("/reset")
def reset_memory():
    global chat_history
    chat_history = [{"role": "system", "content": system_instruction}]
    return {"status": "Memory Cleared 🧹"}