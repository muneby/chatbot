from pydantic import BaseModel
import json

# ==========================================
# 1. قاعدة بيانات منتجات مكتبة البوادي 🏛️
#
# ==========================================
products_db = {
    "فنية": [
        {"id": 101, "name": "ألوان أكريليك Dandy (6 ألوان)", "price": 15, "stock": 50, "desc": "ألوان عالية الجودة مع فرشاة وباليتة صغيرة، مناسبة للرسم على الكانفس", "category": "فنية وأشغال يدوية"},
        {"id": 102, "name": "بخاخ بوية إسباني (أخضر فالي)", "price": 39, "stock": 20, "desc": "400 مل، تغطية ممتازة وسريعة الجفاف للأعمال الفنية والديكور", "category": "فنية وأشغال يدوية"},
        {"id": 103, "name": "طقم فرش رسم DANDY (9 فرش)", "price": 17, "stock": 15, "desc": "مقاسات متنوعة تناسب الألوان المائية والزيتية", "category": "فنية وأشغال يدوية"}
    ],
    "مكتبية": [
        {"id": 201, "name": "ورق تصوير روكو A4 (500 ورقة)", "price": 18, "stock": 200, "desc": "ورق أبيض ناصع 80 جرام، مثالي للطابعات وآلات التصوير", "category": "أدوات مكتبية"},
        {"id": 202, "name": "آلة تغليف حراري DANDY A3", "price": 250, "stock": 5, "desc": "تغليف حراري للمستندات حتى مقاس A3، 4 رولات تسخين", "category": "إلكترونيات ومعدات"},
        {"id": 203, "name": "فلاش ميموري SanDisk 64GB", "price": 35, "stock": 30, "desc": "سعة تخزين عالية، USB 3.0 لنقل البيانات بسرعة", "category": "إلكترونيات"}
    ],
    "مدرسية": [
        {"id": 301, "name": "شنطة ظهر Best Life", "price": 43, "stock": 10, "desc": "شنطة عملية ومريحة للطلاب، جودة عالية", "category": "شنط مدرسية"},
        {"id": 302, "name": "ألوان مائية Maped (12 لون)", "price": 13, "stock": 60, "desc": "ألوان زاهية وآمنة للأطفال، سهلة الغسل", "category": "أدوات مدرسية"}
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
# دوال البحث (للتذكير، تأكد أنها موجودة)
def search_product(query: str):
    results = []
    query = query.lower()
    for category, items in products_db.items():
        for item in items:
            if query in item["name"].lower() or query in item["category"] or query in item["desc"]:
                availability = "متوفر ✅" if item["stock"] > 0 else "نفدت الكمية ❌"
                item_info = {
                    "المنتج": item["name"],
                    "السعر": f"{item['price']} ريال (شامل الضريبة)",
                    "الوصف": item["desc"],
                    "التوفر": availability
                }
                results.append(item_info)
    if results:
        return json.dumps(results, ensure_ascii=False)
    else:
        return json.dumps({"message": "عذراً، المنتج غير موجود حالياً. لدينا تشكيلة واسعة من الأدوات الفنية والمكتبية، جرب البحث بكلمة عامة."}, ensure_ascii=False)

def get_order_status(phone_number: str):
    phone = phone_number.replace(" ", "")
    order = orders_db.get(phone)
    if order:
        return json.dumps(order, ensure_ascii=False)
    else:
        return json.dumps({"error": "رقم الجوال غير مسجل في طلبات المتجر الإلكتروني"}, ensure_ascii=False)

class MessageInput(BaseModel):
    text: str