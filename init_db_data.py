import sys
import os

# إضافة المجلد الحالي للمسار عشان بايثون يشوف مجلد app
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models import Merchant, Bot, Product
from app.auth import get_password_hash

def init_db():
    print("🔄 جاري تهيئة قاعدة البيانات...")

    # 1. إنشاء الجداول
    # هذا السطر هو الذي ينشئ الملف chatbot.db والجداول داخله
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 2. إنشاء السوبر أدمن الافتراضي
        admin_username = "admin"
        admin_password = "admin123"
        
        existing_admin = db.query(Merchant).filter(Merchant.username == admin_username).first()
        
        if not existing_admin:
            super_admin = Merchant(
                username=admin_username,
                hashed_password=get_password_hash(admin_password),
                is_superuser=True
            )
            db.add(super_admin)
            db.commit()
            print(f"✅ تم إنشاء السوبر أدمن: (User: {admin_username} / Pass: {admin_password})")
        else:
            print("ℹ️ السوبر أدمن موجود مسبقاً.")

    except Exception as e:
        print(f"❌ حدث خطأ أثناء التهيئة: {e}")
    finally:
        db.close()
        print("🚀 انتهت العملية.")

if __name__ == "__main__":
    init_db()