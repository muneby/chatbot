from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router # <-- لاحظ كيف استدعينا الراوتر

app = FastAPI()

# إعدادات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ربط الراوتر بالتطبيق
app.include_router(router)

@app.get("/")
def home():
    return {"status": "System is Optimized & Running 🚀"}