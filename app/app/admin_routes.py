from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone
import re
import httpx
from app.database import SessionLocal
from app.models import Bot, Product, BotIntegration, Merchant, BotCreate, ProductCreate, LoginRequest, BotResponse, ProductResponse, IntegrationConfig, CreateUserRequest, UpdateUserRequest, BusinessProfile
from app.auth import get_password_hash, verify_password, create_access_token, oauth2_scheme, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
router = APIRouter()

# دالة الاتصال بالداتابيس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------
# 🔐 دوال مساعدة (لجلب المستخدم الحالي)
# ---------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(Merchant).filter(Merchant.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ---------------------------------------------
# 🚀 التسجيل والدخول
# ---------------------------------------------

@router.post("/signup")
def create_merchant(user: LoginRequest, db: Session = Depends(get_db)):
    if db.query(Merchant).filter(Merchant.username == user.username).first():
        raise HTTPException(status_code=400, detail="المستخدم موجود مسبقاً")
    
    new_merchant = Merchant(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_superuser=False 
    )
    db.add(new_merchant)
    db.commit()
    return {"message": "تم إنشاء الحساب بنجاح", "role": "client"}

@router.post("/login")
def login(user: LoginRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.username == user.username).first()
    if not merchant or not verify_password(user.password, merchant.hashed_password):
        raise HTTPException(status_code=401, detail="بيانات خاطئة")
    
    access_token = create_access_token(data={"sub": merchant.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "is_superuser": merchant.is_superuser,
        "username": merchant.username
    }

# ---------------------------------------------
# 👤 منطقة العميل (Client Area)
# ---------------------------------------------
@router.post("/my-bots")
def create_my_bot(bot: BotCreate, 
                  current_user: Merchant = Depends(get_current_user), 
                  db: Session = Depends(get_db)):
    
    new_bot = Bot(
        name=bot.name,
        business_type=bot.business_type,
        system_prompt=bot.system_prompt,
        welcome_message=bot.welcome_message,
        tone=bot.tone,
        primary_color=bot.primary_color,
        bot_persona_name=bot.bot_persona_name,
        language=bot.language,
        avatar_emoji=bot.avatar_emoji,
        currency=bot.currency,
        working_hours=bot.working_hours,
        fallback_message=bot.fallback_message,
        contact_info=bot.contact_info,
        owner_id=current_user.id
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return {"message": "تم إنشاء البوت", "bot_id": new_bot.id}

# 2. جلب البوتات (Read)
@router.get("/my-bots", response_model=List[BotResponse])
def get_my_bots(current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    return current_user.bots

# تعديل (Update)
@router.put("/my-bots/{bot_id}")
def update_my_bot(bot_id: int, bot_update: BotCreate, 
                  current_user: Merchant = Depends(get_current_user), 
                  db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    bot.name             = bot_update.name
    bot.business_type    = bot_update.business_type
    bot.system_prompt    = bot_update.system_prompt
    bot.welcome_message  = bot_update.welcome_message
    bot.tone             = bot_update.tone
    bot.primary_color    = bot_update.primary_color
    bot.bot_persona_name = bot_update.bot_persona_name
    bot.language         = bot_update.language
    bot.avatar_emoji     = bot_update.avatar_emoji
    bot.currency         = bot_update.currency
    bot.working_hours    = bot_update.working_hours
    bot.fallback_message = bot_update.fallback_message
    bot.contact_info     = bot_update.contact_info

    db.commit()
    return {"message": "Updated"}

# حذف (Delete)
@router.delete("/my-bots/{bot_id}")
def delete_my_bot(bot_id: int, 
                  current_user: Merchant = Depends(get_current_user), 
                  db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="غير موجود")
        
    db.delete(bot)
    db.commit()
    return {"message": "Deleted"}
# ---------------------------------------------
# 📦 إدارة المنتجات (Product Management)
# ---------------------------------------------

@router.get("/my-bots/{bot_id}/products", response_model=List[ProductResponse])
def get_products(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    return bot.products

@router.post("/my-bots/{bot_id}/products", response_model=ProductResponse)
def create_product(bot_id: int, product: ProductCreate, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    new_product = Product(bot_id=bot_id, **product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.put("/my-bots/{bot_id}/products/{product_id}", response_model=ProductResponse)
def update_product(bot_id: int, product_id: int, product: ProductCreate, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    db_product = db.query(Product).filter(Product.id == product_id, Product.bot_id == bot_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/my-bots/{bot_id}/products/{product_id}")
def delete_product(bot_id: int, product_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    db_product = db.query(Product).filter(Product.id == product_id, Product.bot_id == bot_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    db.delete(db_product)
    db.commit()
    return {"message": "Deleted"}

# ---------------------------------------------
# 👑 منطقة السوبر أدمن (Super Admin Area)
# ---------------------------------------------

# ---------------------------------------------
# 🔌 تكامل المنصات التجارية (Platform Integration)
# ---------------------------------------------

def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r'<[^>]+>', '', text or '').strip()[:500]

def _own_bot(bot_id: int, user: Merchant, db: Session) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.owner_id == user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    return bot

@router.get("/my-bots/{bot_id}/integration")
def get_integration(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    _own_bot(bot_id, current_user, db)
    integ = db.query(BotIntegration).filter(BotIntegration.bot_id == bot_id).first()
    if not integ:
        return {"platform": "none", "store_url": "", "api_key": "", "api_secret": "", "store_id": "", "last_synced": "", "synced_count": 0}
    return {
        "platform":     integ.platform,
        "store_url":    integ.store_url    or "",
        "api_key":      integ.api_key      or "",
        "api_secret":   integ.api_secret   or "",
        "store_id":     integ.store_id     or "",
        "last_synced":  integ.last_synced  or "",
        "synced_count": integ.synced_count or 0,
    }

@router.post("/my-bots/{bot_id}/integration")
def save_integration(bot_id: int, config: IntegrationConfig, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    _own_bot(bot_id, current_user, db)
    integ = db.query(BotIntegration).filter(BotIntegration.bot_id == bot_id).first()
    if integ:
        integ.platform   = config.platform
        integ.store_url  = config.store_url
        integ.api_key    = config.api_key
        integ.api_secret = config.api_secret
        integ.store_id   = config.store_id
    else:
        integ = BotIntegration(
            bot_id=bot_id, platform=config.platform,
            store_url=config.store_url, api_key=config.api_key,
            api_secret=config.api_secret, store_id=config.store_id,
        )
        db.add(integ)
    db.commit()
    return {"message": "تم حفظ إعدادات التكامل"}

@router.delete("/my-bots/{bot_id}/integration")
def delete_integration(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    _own_bot(bot_id, current_user, db)
    integ = db.query(BotIntegration).filter(BotIntegration.bot_id == bot_id).first()
    if integ:
        db.delete(integ)
        db.commit()
    return {"message": "تم قطع الاتصال"}

@router.post("/my-bots/{bot_id}/integration/sync")
async def sync_products(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    _own_bot(bot_id, current_user, db)
    integ = db.query(BotIntegration).filter(BotIntegration.bot_id == bot_id).first()
    if not integ or integ.platform == "none":
        raise HTTPException(status_code=400, detail="لا يوجد تكامل مُعد لهذا البوت")

    fetched: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:

            # ── Salla ────────────────────────────────────────
            if integ.platform == "salla":
                r = await client.get(
                    "https://api.salla.dev/admin/v2/products",
                    headers={"Authorization": f"Bearer {integ.api_key}"},
                    params={"per_page": 100},
                )
                r.raise_for_status()
                items = r.json().get("data", {})
                if isinstance(items, dict):
                    items = items.get("data", [])
                for it in items:
                    fetched.append({
                        "name":        it.get("name", ""),
                        "price":       float(it.get("price", {}).get("amount", 0) if isinstance(it.get("price"), dict) else it.get("price", 0)),
                        "stock":       int(it.get("quantity", 0)),
                        "description": _strip_html(it.get("description", "")),
                        "category":    (it.get("categories") or [{}])[0].get("name", ""),
                        "tags":        it.get("sku", ""),
                    })

            # ── Zid ──────────────────────────────────────────
            elif integ.platform == "zid":
                r = await client.get(
                    "https://api.zid.sa/v1/products",
                    headers={"Authorization": f"Bearer {integ.api_key}", "store-id": integ.store_id},
                )
                r.raise_for_status()
                for it in r.json().get("products", []):
                    name = it.get("name", "")
                    if isinstance(name, dict):
                        name = name.get("ar") or name.get("en") or ""
                    desc = it.get("description", "")
                    if isinstance(desc, dict):
                        desc = desc.get("ar") or desc.get("en") or ""
                    fetched.append({
                        "name":        name,
                        "price":       float(it.get("price", 0)),
                        "stock":       int(it.get("quantity", 0)),
                        "description": _strip_html(desc),
                        "category":    "",
                        "tags":        "",
                    })

            # ── WooCommerce ──────────────────────────────────
            elif integ.platform == "woocommerce":
                base = integ.store_url.rstrip("/")
                r = await client.get(
                    f"{base}/wp-json/wc/v3/products",
                    params={"consumer_key": integ.api_key, "consumer_secret": integ.api_secret, "per_page": 100, "status": "publish"},
                )
                r.raise_for_status()
                for it in r.json():
                    fetched.append({
                        "name":        it.get("name", ""),
                        "price":       float(it.get("regular_price") or it.get("price") or 0),
                        "stock":       int(it.get("stock_quantity") or 0),
                        "description": _strip_html(it.get("description", "")),
                        "category":    (it.get("categories") or [{}])[0].get("name", ""),
                        "tags":        ", ".join(t.get("name", "") for t in it.get("tags", [])),
                    })

            # ── Shopify ──────────────────────────────────────
            elif integ.platform == "shopify":
                shop = integ.store_url.replace("https://", "").replace("http://", "").rstrip("/")
                r = await client.get(
                    f"https://{shop}/admin/api/2024-01/products.json",
                    headers={"X-Shopify-Access-Token": integ.api_key},
                    params={"limit": 250},
                )
                r.raise_for_status()
                for it in r.json().get("products", []):
                    variant = (it.get("variants") or [{}])[0]
                    fetched.append({
                        "name":        it.get("title", ""),
                        "price":       float(variant.get("price", 0)),
                        "stock":       int(variant.get("inventory_quantity", 0)),
                        "description": _strip_html(it.get("body_html", "")),
                        "category":    it.get("product_type", ""),
                        "tags":        it.get("tags", ""),
                    })

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"رفض المنصة الطلب ({e.response.status_code}). تحقق من صحة بيانات الاتصال.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="تعذّر الوصول إلى المنصة. تحقق من الاتصال أو عنوان المتجر.")

    # Delete previously synced products from this platform, keep manual ones
    db.query(Product).filter(Product.bot_id == bot_id, Product.source == integ.platform).delete()

    for p in fetched:
        db.add(Product(bot_id=bot_id, source=integ.platform, **p))

    integ.last_synced  = datetime.now(timezone.utc).isoformat()
    integ.synced_count = len(fetched)
    db.commit()
    return {"synced": len(fetched), "message": f"تم جلب {len(fetched)} منتج بنجاح"}

# ---------------------------------------------
# 👤 ملف المستخدم التجاري (Business Profile)
# ---------------------------------------------

def _profile_dict(m: Merchant) -> dict:
    return {
        "username":        m.username,
        "business_name":   m.business_name   or "",
        "business_sector": m.business_sector or "",
        "country":         m.country         or "",
        "city":            m.city            or "",
        "phone":           m.phone           or "",
        "email":           m.email           or "",
        "website":         m.website         or "",
        "employee_count":  m.employee_count  or "",
        "bio":             m.bio             or "",
    }

@router.get("/my-profile")
def get_my_profile(current_user: Merchant = Depends(get_current_user)):
    return _profile_dict(current_user)

@router.put("/my-profile")
def update_my_profile(profile: BusinessProfile, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(Merchant).filter(Merchant.id == current_user.id).first()
    for field, value in profile.model_dump().items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    return _profile_dict(user)

# ---------------------------------------------
# 👑 منطقة السوبر أدمن (Super Admin Area)
# ---------------------------------------------

@router.get("/super-admin/stats")
def get_global_stats(current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    return {
        "total_clients": db.query(Merchant).count(),
        "total_active_bots": db.query(Bot).count(),
        "total_demo_bots": db.query(Bot).filter(Bot.is_demo == True).count(),
        "status": "Healthy"
    }

@router.get("/super-admin/users")
def get_all_users(current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    rows = (
        db.query(Merchant, func.count(Bot.id).label("bot_count"))
        .outerjoin(Bot, Bot.owner_id == Merchant.id)
        .group_by(Merchant.id)
        .all()
    )
    return [
        {
            "id":              m.id,
            "username":        m.username,
            "is_superuser":    m.is_superuser,
            "bot_count":       count,
            "business_name":   m.business_name   or "",
            "business_sector": m.business_sector or "",
            "country":         m.country         or "",
            "city":            m.city            or "",
            "phone":           m.phone           or "",
            "email":           m.email           or "",
            "website":         m.website         or "",
            "employee_count":  m.employee_count  or "",
            "bio":             m.bio             or "",
        }
        for m, count in rows
    ]

@router.delete("/super-admin/users/{user_id}")
def delete_user(user_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكنك حذف حسابك الخاص")
    user = db.query(Merchant).filter(Merchant.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    db.delete(user)
    db.commit()
    return {"message": "Deleted"}

@router.get("/super-admin/bots")
def get_all_bots(current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    bots = db.query(Bot).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "is_demo": b.is_demo,
            "owner_username": b.owner.username if b.owner else "—",
        }
        for b in bots
    ]

@router.patch("/super-admin/bots/{bot_id}/toggle-demo")
def toggle_demo(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    bot.is_demo = not bot.is_demo
    db.commit()
    return {"bot_id": bot_id, "is_demo": bot.is_demo}

@router.post("/super-admin/users")
def admin_create_user(user: CreateUserRequest, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    if db.query(Merchant).filter(Merchant.username == user.username).first():
        raise HTTPException(status_code=400, detail="اسم المستخدم مستخدم مسبقاً")
    new_user = Merchant(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_superuser=user.is_superuser
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "is_superuser": new_user.is_superuser, "bot_count": 0}

@router.put("/super-admin/users/{user_id}")
def admin_update_user(user_id: int, data: UpdateUserRequest, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    user = db.query(Merchant).filter(Merchant.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    if user_id == current_user.id and data.is_superuser is False:
        raise HTTPException(status_code=400, detail="لا يمكنك إزالة صلاحياتك الخاصة")
    if data.new_password:
        user.hashed_password = get_password_hash(data.new_password)
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    db.commit()
    return {"message": "تم التحديث بنجاح"}

@router.delete("/super-admin/bots/{bot_id}")
def admin_delete_bot(bot_id: int, current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="البوت غير موجود")
    db.delete(bot)
    db.commit()
    return {"message": "Deleted"}

@router.get("/super-admin/analytics")
def get_analytics(current_user: Merchant = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية المدير العام")

    total_bots     = db.query(Bot).count()
    total_products = db.query(Product).count()

    # Bots by business type
    type_counts = {}
    for btype in ["store", "restaurant", "service"]:
        type_counts[btype] = db.query(Bot).filter(Bot.business_type == btype).count()

    # Demo vs live
    demo_count = db.query(Bot).filter(Bot.is_demo == True).count()

    # Top 5 users by bot count
    top_users_rows = (
        db.query(Merchant.username, func.count(Bot.id).label("cnt"))
        .outerjoin(Bot, Bot.owner_id == Merchant.id)
        .group_by(Merchant.id)
        .order_by(func.count(Bot.id).desc())
        .limit(5)
        .all()
    )
    top_users = [{"username": r.username, "bot_count": r.cnt} for r in top_users_rows]

    # Bots that have at least one product
    bots_with_products = (
        db.query(Bot.id)
        .join(Product, Product.bot_id == Bot.id)
        .distinct()
        .count()
    )

    avg_products = round(total_products / total_bots, 1) if total_bots > 0 else 0

    return {
        "total_bots": total_bots,
        "total_products": total_products,
        "bots_by_type": type_counts,
        "demo_count": demo_count,
        "live_count": total_bots - demo_count,
        "top_users": top_users,
        "bots_with_products": bots_with_products,
        "avg_products_per_bot": avg_products,
    }