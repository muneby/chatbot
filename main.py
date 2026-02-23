from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- تأكد أن هذا السطر موجود
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os
import json
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# ==========================================
# 🔓 تصريح المرور (CORS) - أهم جزء الآن
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح للجميع
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ==========================================
# ---------------------------------------------------------
# 1. قاعدة البيانات الوهمية (Mock Database) 🗄️
# تخيل أن هذه جاية من Excel أو SQL
# ---------------------------------------------------------
fake_db = {
    "0501111111": {"name": "أحمد", "status": "تم الشحن 🚚", "item": "آيفون 15 برو"},
    "0502222222": {"name": "سارة", "status": "قيد التجهيز 📦", "item": "سماعة آبل"},
    "0503333333": {"name": "خالد", "status": "ملغي ❌", "item": "شاحن جداري"}
}

# ---------------------------------------------------------
# 2. الأداة البرمجية (The Function) 🛠️
# هذه الدالة الـ AI راح "يناديها" لما يحتاج معلومات
# ---------------------------------------------------------
def get_order_status(phone_number: str):
    """جلب حالة الطلب باستخدام رقم الجوال"""
    # تنظيف الرقم (شيل المسافات لو وجدت)
    phone = phone_number.replace(" ", "")
    
    # البحث في الداتابيس
    customer = fake_db.get(phone)
    
    if customer:
        return json.dumps(customer, ensure_ascii=False)
    else:
        return json.dumps({"error": "الرقم غير مسجل عندنا"}, ensure_ascii=False)

# تعريف الأداة لـ OpenAI (عشان يفهم إنها موجودة)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "استخدم هذه الأداة عندما يسأل العميل عن حالة طلبه أو تتبعه. يجب أن تطلب رقم الجوال أولاً.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "رقم جوال العميل السعودي (يبدأ بـ 05)"},
                },
                "required": ["phone_number"],
            },
        }
    }
]

# ---------------------------------------------------------
# 2. الذاكرة (Memory) - هنا نخزن تاريخ الشات
# ---------------------------------------------------------
# ملاحظة: في المشاريع الكبيرة نستخدم داتابيس، هنا نستخدم قائمة بسيطة للتجربة
chat_history = []

# ==========================================
# 🧠 منطقة العقل (System Instruction)
# هنا تكتب شخصية البوت وقوانين المتجر
# ==========================================
system_instruction = """
أنت مساعد خدمة عملاء ذكي ومحترم لمتجر اسمه "متجر البوادي" متخصص في قرطاسية المكتبية  في السعودية.
- لهجتك: سعودية بيضاء، ودودة، ومختصرة (لا تكتب جرائد).
- العملة: الريال السعودي (SAR).

معلومات المتجر (Knowledge Base):
الدفع
يوفر الموقع إمكانية شراء المنتج (المنتجات) عبر الإنترنت وتسوية الدفع عبر الإنترنت أو الدفع عند التسليم بناءً على طريقة الشحن / التسليم المتاحة في المملكة العربية السعودية. تكون معاملات الدفع بما في ذلك التفويضات والتسويات بالريال السعودي.
نقبل وسائل الدفع التالية:
بطاقات الائتمان والخصم (فيزا . ماستركارد . مدى . تمارا . اموال  ).
المعاملات المباشرة
نحن لا نخزن تفاصيل بطاقتك الائتمانية على الموقع. يتم تشفير جميع تفاصيل الدفع التي يتم إدخالها من خلال بوابة دفع الموقع عند إدخالها. يتم تشفير الاتصال من وإلى موقع مقدم الخدمة أيضًا.
لا يمكننا تقديم أي من معلومات الدفع الخاصة بك التي تم الحصول عليها عبر الويب إلى شركات أو أفراد آخرين ما لم يقتضي القانون ذلك. تتم معالجة هذه المعلومات من قبل الدفع التجارى لدينا.
ستكون تفاصيل بطاقة الائتمان التي قدمتها للاستفادة من الخدمة عبرالإنترنت حقيقية وصحيحة ودقيقة ، ويجب عليك استخدام بطاقة الائتمان التي تمتلكها بشكل قانوني. لن يتم استخدام المعلومات المذكورة ومشاركتها بواسطة الخدمة عبر الإنترنت مع أي من الأطراف الثالثة ما لم يكن ذلك مطلوبًا للتحقق من الاحتيال أو بموجب القانون أو اللائحة أو أمر المحكمة. لن تكون خدمة الانترنت مسؤولة عن أي احتيال على بطاقات الائتمان. تقع مسؤولية استخدام البطاقة بطريقة احتيالية على عاتقك ، وتقع مسؤولية إثبات خلاف ذلك على عاتقك حصريًا.
في حالة عدم قدرتنا على توريد الطلب بالكامل أو جزء منه ، فسنبلغك بذلك. سيتم استرداد المبلغ بالكامل أو جزئيًا – من خلال بطاقة الائتمان – حيث تم تحصيل الرسوم منك بالفعل.
يشيراستخدام وسيلة الدفع عبرموقع الإنترنت إلى قبولك هذه الشروط. إذا كنت لا توافق على هذه الشروط ، يرجى عدم استخدام هذه الوسيلة
إلغاء الطلب
يحتفظ موقع albawadi.sa بالحق في إلغاء الطلب لأي من الأسباب التالية ، على سبيل المثال لا الحصر:
رفض الدفع
الطلبات المقدمة أثناء تغيرات الأسعار ، أو الطلبات المقدمة على المنتجات التي بها تغيرات أسعار خاطئة.
أوامر وضعت خلال تغييرات المخزون.
لم يستوفِ الطلب أيًا من شروط وأحكام موقع التسوق الإلكتروني.
عنوان تسليم خاطئ مقدم من العميل. أو تفاصيل اتصال خاطئة. أو بسبب العميل لا يمكن الوصول إليه.
الإلغاء من قبل العميل: لمعالجة إلغاء الطلب ، يرجى الاتصال بنا. يمكنك إلغاء الطلب لأي من الأسباب التالية:
 لم يتم شحن المنتج (المنتجات) إليك بعد. في حالة الإلغاء بعد شحن الطلب إليك ، فسيتم إعادته. لدينا الحق الكامل في توضيح ما إذا كان قد تم شحن الطلب إليك في وقت طلب الإلغاء.
 يتم توصيل المنتج (المنتجات) خلال (10) أيام عمل من تاريخ تأكيدنا لطلبك.
للإرجاع والاسترداد والتبديل ، يرجى الرجوع إلى سياسة الإرجاع والاستبدال.
يجوز لـ albawadi.sa تعديل شروط وأحكام الموقع في أي وقت دون ارسال إخطار مسبق لك. يمكنك الوصول إلى أحدث نسخة من الشروط والأحكام في أي وقت الوقت على موقعنا. في حالة عدم قبولك الشروط والأحكام المعدلة ، يجب عليك التوقف عن استخدام الخدمة. ومع ذلك ، إذا واصلت استخدام الخدمة ، فسيتم اعتبار أنك وافقت على قبول شروط وأحكام الاستخدام المعدلة لهذا الموقع والالتزام بها.
الشحن المجاني
الشحن المجاني يغطي وزن الطلب حتى 10 كيلوجرامات بتكلفة تصل إلى 27 ريال سعودي. في حال تجاوز وزن الطلب 10 كيلوجرامات، يتحمل العميل تكلفة إضافية قدرها 2.3 ريال لكل كيلوجرام زائد.
قواعد الرد:
- اذا سأل العميل عن حالة الطلب، اطلب منه "رقم الطلب".
- اذا كان العميل معصب، حاول تمتص غضبه بلطف.
- جاوب فقط من المعلومات أعلاه، لا تألف معلومات من عندك.
"""
# ==========================================
# نضيف تعليمات النظام كأول رسالة في الذاكرة
if len(chat_history) == 0:
    chat_history.append({"role": "system", "content": system_instruction})

def get_order_status(phone_number: str):
    phone = phone_number.replace(" ", "")
    customer = fake_db.get(phone)
    if customer:
        return json.dumps(customer, ensure_ascii=False)
    else:
        return json.dumps({"error": "الرقم غير مسجل"}, ensure_ascii=False)

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "جلب حالة الطلب وسبب الإلغاء. يطلب رقم الجوال.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string"},
                },
                "required": ["phone_number"],
            },
        }
    }
]

class MessageInput(BaseModel):
    text: str
 
# نقطة تصفير الذاكرة (New Chat)
@app.post("/reset")
def reset_memory():
    global chat_history
    chat_history = []  # تصفير القائمة
    # إعادة تعليمات النظام عشان ما ينسى هويته
    chat_history.append({"role": "system", "content": system_instruction})
    return {"status": "Memory Cleared 🧹"}

@app.post("/chat")
def chat_with_ai(data: MessageInput):
    # 1. نضيف رسالة المستخدم الجديدة للذاكرة
    chat_history.append({"role": "user", "content": data.text})

    # 2. نرسل الذاكرة كاملة للـ AI (وليس الرسالة فقط)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_history, # <-- السر هنا: نرسل التاريخ كله
        tools=tools_schema,
        tool_choice="auto" 
    )
    

    response_message = response.choices[0].message

    # 3. إذا طلب البوت استخدام أداة
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        if function_name == "get_order_status":
            function_response = get_order_status(
                phone_number=function_args.get("phone_number")
            )
            
            # نضيف رد الأداة للذاكرة عشان البوت يشوفه ويتذكره
            chat_history.append(response_message) 
            chat_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response
            })

            # البوت يحلل البيانات ويعطي الرد النهائي
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_history
            )
            ai_reply = final_response.choices[0].message.content
            
            # نحفظ رد البوت النهائي في الذاكرة
            chat_history.append({"role": "assistant", "content": ai_reply})
            return {"reply": ai_reply}
    
    # 4. إذا كان رد عادي (بدون أدوات)
    ai_reply = response_message.content
    chat_history.append({"role": "assistant", "content": ai_reply})
    
    return {"reply": ai_reply}