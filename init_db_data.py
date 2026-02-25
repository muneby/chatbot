# init_db_data.py
from app.database import init_db, SessionLocal, Bot, Product, Order

# 1. إنشاء الجداول
init_db()
db = SessionLocal()

# 2. هل البوت موجود؟ إذا لا، ننشئه
existing_bot = db.query(Bot).filter(Bot.id == 1).first()
if not existing_bot:
    print("🚀 جاري إنشاء بوت مكتبة البوادي...")
    
    # إنشاء البوت
    bawadi_bot = Bot(
        id=1,
        name="مكتبة البوادي",
        business_type="store",
        system_prompt="أنت المساعد الذكي لمكتبة البوادي. تقع في جدة. الشحن مجاني فوق 199 ريال."
    )
    db.add(bawadi_bot)
    db.commit()

    # إضافة المنتجات (لاحظ كيف ربطناها بـ bot_id=1)
    products = [
        Product(bot_id=1, name="ألوان أكريليك Dandy", price=15, stock=50, description="ألوان عالية الجودة", category="فنية", tags="رسم تلوين لوح"),
        Product(bot_id=1, name="بخاخ بوية إسباني", price=39, stock=20, description="سريعة الجفاف", category="فنية", tags="جدار جرافيتي صبغ"),
        Product(bot_id=1, name="ورق تصوير روكو A4", price=18, stock=200, description="ورق 80 جرام", category="مكتبية", tags="طباعة تصوير اوراق"),
        Product(bot_id=1, name="شنطة ظهر Best Life", price=43, stock=10, description="مريحة للطلاب", category="مدرسية", tags="حقيبة لابتوب ظهر")
    ]
    
    # إضافة الطلبات الوهمية
    orders = [
        Order(bot_id=1, customer_phone="0501111111", customer_name="عبدالرحمن", status="تم الشحن 🚚", items="ألوان أكريليك", total_price=45),
        Order(bot_id=1, customer_phone="0502222222", customer_name="منى", status="قيد التجهيز 📦", items="ورق تصوير", total_price=50)
    ]

    db.add_all(products)
    db.add_all(orders)
    db.commit()
    print("✅ تم تجهيز قاعدة البيانات بنجاح!")
else:
    print("⚠️ البيانات موجودة مسبقاً.")

db.close()