from pydantic import BaseModel
import json

# ==========================================
# 1. قاعدة بيانات المنتجات (المخزون) 🎒
# ==========================================
products_db = {
    "اقلام": [
        {"id": 101, "name": "طقم أقلام يوني بول (أسود)", "price": 45, "stock": 20, "desc": "حبر سائل، 0.7 ملم، مضاد للماء", "category": "أقلام"},
        {"id": 102, "name": "أقلام رصاص روكو (علبة)", "price": 12, "stock": 100, "desc": "HB كلاسيك، خشب عالي الجودة", "category": "أقلام"},
        {"id": 103, "name": "أقلام تحديد هايلايتر (4 ألوان)", "price": 18, "stock": 0, "desc": "ألوان فاقعة باستيل، لا تجف بسرعة", "category": "أقلام"}
    ],
    "دفاتر": [
        {"id": 201, "name": "دفتر سلك A4 مسطر", "price": 25, "stock": 50, "desc": "غلاف مقوى، 200 ورقة، ورق 80 جرام", "category": "دفاتر"},
        {"id": 202, "name": "كراسة رسم كانسون", "price": 35, "stock": 15, "desc": "ورق خشن للألوان المائية، A3", "category": "رسم"}
    ],
    "شنط": [
        {"id": 301, "name": "شنطة ظهر أديداس", "price": 180, "stock": 5, "desc": "لون أسود، مناسبة للابتوب 15 إنش", "category": "شنط مدرسية"}
    ]
}

# ==========================================
# 2. قاعدة بيانات الطلبات (العملاء) 📦
# ==========================================
orders_db = {
    "0501111111": {
        "name": "أحمد", 
        "status": "تم الشحن 🚚", 
        "items": ["طقم أقلام يوني بول", "دفتر سلك A4"], 
        "total": 70,
        "date": "2024-10-01"
    },
    "0502222222": {
        "name": "سارة", 
        "status": "قيد التجهيز 📦", 
        "items": ["كراسة رسم كانسون", "ألوان خشبية"], 
        "total": 90,
        "date": "2024-10-03"
    },
    "0503333333": {
        "name": "خالد", 
        "status": "ملغي ❌", 
        "items": ["شنطة ظهر أديداس"], 
        "total": 180, 
        "reason": "نعتذر، المنتج نفد من المخزون بعد الطلب"
    }
}

# ==========================================
# 3. دوال البحث (Logic) 🧠
# ==========================================

# دالة البحث عن منتج (ذكية تبحث في كل الأقسام)
def search_product(query: str):
    """تبحث عن منتج بالاسم وترجع تفاصيله"""
    results = []
    query = query.lower() # توحيد البحث
    
    # نلف على كل الأقسام (أقلام، دفاتر، شنط...)
    for category, items in products_db.items():
        for item in items:
            if query in item["name"].lower() or query in item["category"]:
                # إضافة حالة التوفر
                availability = "متوفر ✅" if item["stock"] > 0 else "نفدت الكمية ❌"
                item_info = {
                    "المنتج": item["name"],
                    "السعر": f"{item['price']} ريال",
                    "الوصف": item["desc"],
                    "حالة التوفر": availability
                }
                results.append(item_info)
    
    if results:
        return json.dumps(results, ensure_ascii=False)
    else:
        return json.dumps({"message": "للأسف ما حصلت منتج بهذا الاسم، جرب تبحث بكلمة عامة مثل 'قلم' أو 'دفتر'"}, ensure_ascii=False)

# دالة الاستعلام عن الطلب
def get_order_status(phone_number: str):
    """تجلب تفاصيل الطلب برقم الجوال"""
    phone = phone_number.replace(" ", "")
    order = orders_db.get(phone)
    if order:
        return json.dumps(order, ensure_ascii=False)
    else:
        return json.dumps({"error": "رقم الجوال هذا غير مسجل في طلباتنا الحالية"}, ensure_ascii=False)

# نموذج استقبال الرسائل (للسيرفر)
class MessageInput(BaseModel):
    text: str