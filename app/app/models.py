from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, Session
from app.database import Base
from pydantic import BaseModel
from typing import List, Optional

# ----------------------
# 1. جداول قاعدة البيانات (SQLAlchemy)
# ----------------------

class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = {'extend_existing': True}

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String, unique=True, index=True)
    hashed_password  = Column(String)
    is_superuser     = Column(Boolean, default=False)

    # Business metadata
    business_name    = Column(String,  default="")
    business_sector  = Column(String,  default="")   # retail, food_beverage, services, real_estate, education, healthcare, beauty, tech, other
    country          = Column(String,  default="")
    city             = Column(String,  default="")
    phone            = Column(String,  default="")
    email            = Column(String,  default="")
    website          = Column(String,  default="")
    employee_count   = Column(String,  default="")   # solo, small (2-10), medium (11-50), large (50+)
    bio              = Column(Text,    default="")

    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")

class Bot(Base):
    __tablename__ = "bots"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    business_type = Column(String)
    system_prompt = Column(String)
    
    welcome_message  = Column(String, default="أهلاً بك! كيف يمكنني مساعدتك؟")
    tone             = Column(String, default="friendly")   # friendly, formal, funny
    primary_color    = Column(String, default="#008069")    # hex color for embed widget
    bot_persona_name = Column(String, default="")           # public display name in chat
    is_demo          = Column(Boolean, default=False)       # shown in /demo page

    # Extended metadata
    language         = Column(String, default="ar")         # ar, en, bilingual
    avatar_emoji     = Column(String, default="🤖")         # visual identity emoji
    currency         = Column(String, default="SAR")        # SAR, AED, KWD, USD, EGP
    working_hours    = Column(String, default="")           # e.g. "9 ص - 11 م"
    fallback_message = Column(String, default="")           # when bot can't help
    contact_info     = Column(String, default="")

    owner_id = Column(Integer, ForeignKey("merchants.id"))

    owner       = relationship("Merchant", back_populates="bots")
    products    = relationship("Product", back_populates="bot", cascade="all, delete-orphan")
    integration = relationship("BotIntegration", back_populates="bot", uselist=False, cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id          = Column(Integer, primary_key=True, index=True)
    bot_id      = Column(Integer, ForeignKey("bots.id"))
    name        = Column(String)
    price       = Column(Integer)
    stock       = Column(Integer)
    description = Column(String)
    category    = Column(String)
    tags        = Column(String)
    source      = Column(String, default="manual")   # manual | salla | zid | woocommerce | shopify

    bot = relationship("Bot", back_populates="products")


class BotIntegration(Base):
    __tablename__ = "bot_integrations"
    __table_args__ = {'extend_existing': True}

    id           = Column(Integer, primary_key=True, index=True)
    bot_id       = Column(Integer, ForeignKey("bots.id"), unique=True)
    platform     = Column(String, default="none")   # salla | zid | woocommerce | shopify | none
    store_url    = Column(String, default="")       # woocommerce / shopify domain
    api_key      = Column(String, default="")       # primary token / consumer key
    api_secret   = Column(String, default="")       # woocommerce consumer secret
    store_id     = Column(String, default="")       # zid store id
    last_synced  = Column(String, default="")       # ISO datetime string
    synced_count = Column(Integer, default=0)

    bot = relationship("Bot", back_populates="integration")

# ----------------------
# 2. نماذج البيانات (Pydantic)
# ----------------------

class HistoryMessage(BaseModel):
    role: str      # "user" أو "assistant"
    content: str

class MessageInput(BaseModel):
    text: str
    bot_id: int
    history: List[HistoryMessage] = []

class BotCreate(BaseModel):
    name: str
    business_type: str
    system_prompt: str
    welcome_message: str = "أهلاً بك! تفضل بالسؤال."
    tone: str = "friendly"
    primary_color: str = "#008069"
    bot_persona_name: str = ""
    language: str = "ar"
    avatar_emoji: str = "🤖"
    currency: str = "SAR"
    working_hours: str = ""
    fallback_message: str = ""
    contact_info: str = ""

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    description: str
    category: str
    tags: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    is_superuser: bool = False

class UpdateUserRequest(BaseModel):
    new_password: Optional[str] = None
    is_superuser: Optional[bool] = None

class BusinessProfile(BaseModel):
    business_name:   Optional[str] = ""
    business_sector: Optional[str] = ""
    country:         Optional[str] = ""
    city:            Optional[str] = ""
    phone:           Optional[str] = ""
    email:           Optional[str] = ""
    website:         Optional[str] = ""
    employee_count:  Optional[str] = ""
    bio:             Optional[str] = ""

class IntegrationConfig(BaseModel):
    platform:   str
    store_url:  str = ""
    api_key:    str = ""
    api_secret: str = ""
    store_id:   str = ""

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    description: str
    category: str
    tags: str
    source: str = "manual"

    class Config:
        from_attributes = True

class BotResponse(BaseModel):
    id: int
    name: str
    business_type: str
    system_prompt: str
    welcome_message: str
    tone: str
    primary_color: str
    bot_persona_name: str
    language: str = "ar"
    avatar_emoji: str = "🤖"
    currency: str = "SAR"
    working_hours: str = ""
    fallback_message: str = ""
    contact_info: str = ""

    class Config:
        from_attributes = True

# ----------------------
# 3. الدوال المساعدة
# ----------------------
# (اترك الدوال المساعدة كما هي get_bot_instruction, etc...)
def get_bot_instruction(bot_id: int, db: Session):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    return bot.system_prompt if bot else "أنت مساعد ذكي."

def search_product(query: str, bot_id: int, db: Session):
    products = db.query(Product).filter(
        Product.bot_id == bot_id, 
        Product.name.contains(query)
    ).all()
    if not products: return None
    result = "وجدنا هذه المنتجات:\n"
    for p in products:
        result += f"- {p.name} بسعر {p.price} ريال\n"
    return result

def get_order_status(order_id: str):
    return f"الطلب رقم {order_id} قيد التجهيز حالياً 📦"