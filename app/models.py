from pydantic import BaseModel
import json
import difflib  # 👈 (تمت الإضافة) ضرورية للبحث الذكي
from .database import SessionLocal, Product, Order

# دالة مساعدة للبحث (تفتح اتصال وتغلقه)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# دوال البحث (SQLAlchemy + Smart Fuzzy Search) 🕵️‍♂️
# ---------------------------------------------------------

def search_product(query: str):
    db = SessionLocal() # فتح اتصال
    results = []
    
    # 1. جلب منتجات المتجر الحالي (رقم 1)
    # ملاحظة: في المشاريع الكبيرة نستخدم فلاتر SQL، هنا بنجيبها بايثون عشان difflib
    products = db.query(Product).filter(Product.bot_id == 1).all()
    
    query = query.lower().strip()
    
    for item in products:
        # نجمع النصوص (الاسم + الوصف + التاجز)
        # item.tags قد تكون None، لذا نستخدم "or ''" لتجنب الأخطاء
        tags = item.tags or ""
        item_content = f"{item.name} {item.description} {item.category} {tags}".lower()
        
        # 2. البحث المباشر (Direct Match)
        if query in item_content:
            availability = "متوفر ✅" if item.stock > 0 else "نفدت الكمية ❌"
            results.append({
                "المنتج": item.name,
                "السعر": f"{item.price} ريال",
                "الوصف": item.description,
                "التوفر": availability
            })
            continue # لقيناه، روح للي بعده

        # 3. البحث التقريبي (Fuzzy Match) - "تسامح مع الأخطاء"
        # نقسم استعلام العميل لكلمات ونشوف لو فيه تشابه
        for word in query.split():
            # نبحث عن تشابه بنسبة 60%
            matches = difflib.get_close_matches(word, item_content.split(), n=1, cutoff=0.6)
            if matches:
                availability = "متوفر ✅" if item.stock > 0 else "نفدت الكمية ❌"
                results.append({
                    "المنتج": item.name,
                    "السعر": f"{item.price} ريال",
                    "الوصف": item.description,
                    "التوفر": availability
                })
                break # يكفي تطابق واحد

    db.close() # إغلاق الاتصال
    
    if results:
        # نرجع أول 5 نتائج فقط
        return json.dumps(results[:5], ensure_ascii=False)
    else:
        return json.dumps({"message": "عذراً، لم نجد منتجاً مطابقاً في قاعدة البيانات."}, ensure_ascii=False)

def get_order_status(phone_number: str):
    db = SessionLocal()
    phone = phone_number.replace(" ", "")
    
    # استعلام SQL للبحث عن الطلب
    order = db.query(Order).filter(Order.customer_phone == phone, Order.bot_id == 1).first()
    
    db.close()
    
    if order:
        order_data = {
            "name": order.customer_name,
            "status": order.status,
            "items": order.items,
            "total": order.total_price
        }
        return json.dumps(order_data, ensure_ascii=False)
    else:
        return json.dumps({"error": "رقم الجوال غير مسجل"}, ensure_ascii=False)

class MessageInput(BaseModel):
    text: str