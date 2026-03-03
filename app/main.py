from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# استيراد الراوترات (تأكد أن الملفات موجودة في مجلد app)
from app.routes import router as chat_router
from app.admin_routes import router as admin_router
import uvicorn

app = FastAPI()

# 👇👇 أهم جزء: إعدادات السماح (CORS) 👇👇
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح لأي رابط بالاتصال (للراحة أثناء التطوير)
    allow_credentials=True,
    allow_methods=["*"],  # السماح بكل أنواع الطلبات (GET, POST, etc)
    allow_headers=["*"],
)

# تسجيل المسارات
app.include_router(chat_router) # مسار الشات
app.include_router(admin_router, prefix="/admin") # مسار لوحة التحكم

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)