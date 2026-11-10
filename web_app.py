"""
FixPack Facebook Auto-Pilot Web Application (FastAPI)
ระบบบริหารจัดการคอนเทนต์และโพสต์ Facebook อัตโนมัติ รองรับผู้ใช้หลายระดับ
"""
import os
import sys
import json
import time
import hashlib
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# บังคับ UTF-8 สำหรับ Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Response, Form, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from facebook_service import FacebookPoster
from content_generator import create_facebook_post_content, generate_post_with_ai
from create_ai_banner import create_ai_technician_banner, apply_brand_ci_to_uploaded_image
from scheduler_engine import (
    load_schedule, save_schedule, add_scheduled_post,
    execute_single_post, check_and_execute_due_posts,
    check_and_execute_autopilot_daily, AUTO_TOPIC_POOL,
    SCHEDULE_FILE
)
import pages_manager

USERS_FILE = "users.json"
BRAND_CONFIG_FILE = "brand_config.json"

# Utility: Hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def load_users() -> List[Dict[str, Any]]:
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users: List[Dict[str, Any]]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_brand_config() -> Dict[str, Any]:
    if not os.path.exists(BRAND_CONFIG_FILE):
        return {
            "brand_name": "FixPack",
            "tagline": "งานเล็กซ่อมครบ จบในแพ็กเดียว",
            "primary_color": "#0B3B60",
            "accent_color": "#FF5B00",
            "phone": "066-097-1257",
            "price_tag": "เหมาจ่าย 1,500.-",
            "daily_post_time": "09:30",
            "facebook_page_id": os.getenv("FACEBOOK_PAGE_ID", "764713456731551")
        }
    try:
        with open(BRAND_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_brand_config(config: Dict[str, Any]):
    with open(BRAND_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background Scheduler Task
    async def scheduler_loop():
        print("🚀 [FastAPI] ระบบ Background Auto-Pilot Scheduler เริ่มต้นทำงานแล้ว...")
        last_autopilot = {"date": ""}
        while True:
            try:
                poster = FacebookPoster()
                check_and_execute_due_posts(poster)
                check_and_execute_autopilot_daily(poster, last_autopilot)
            except Exception as e:
                print(f"⚠️ Scheduler background error: {e}")
            await asyncio.sleep(30)

    task = asyncio.create_task(scheduler_loop())
    yield
    task.cancel()

# Initialize FastAPI App
app = FastAPI(title="FixPack Facebook Auto-Pilot", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Auth Helper
def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    username = request.cookies.get("session_user")
    if not username:
        return None
    users = load_users()
    for u in users:
        if u["username"] == username:
            return u
    return None

def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        # ถ้าเป็น API call ให้คืนค่า 401 JSON แทนที่จะ Redirect เป็น HTML 307
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบก่อนดำเนินการ")
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})
    return user

def require_admin(request: Request):
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="สงวนสิทธิ์เฉพาะผู้ดูแลระบบ (Admin) เท่านั้น")
    return user

# ================= PAGE ROUTES =================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": error})

@app.post("/login")
async def login_submit(username: str = Form(...), password: str = Form(...)):
    users = load_users()
    h = hash_password(password)
    for u in users:
        if u["username"] == username and u["password_hash"] == h:
            resp = RedirectResponse("/", status_code=302)
            resp.set_cookie(key="session_user", value=username, max_age=86400 * 7, httponly=True)
            return resp
    
    return RedirectResponse("/login?error=ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", status_code=302)

@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session_user")
    return resp

@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    active_page = pages_manager.get_active_page() or {}
    all_pages = pages_manager.get_all_pages()
    brand = load_brand_config()

    return templates.TemplateResponse(request=request, name="index.html", context={
        "current_user": user,
        "brand": brand,
        "active_page": active_page,
        "all_pages": all_pages
    })

# ================= MULTI-PAGE MANAGEMENT APIS =================

@app.get("/api/pages")
async def get_pages_api(request: Request):
    require_auth(request)
    pages = pages_manager.get_all_pages()
    active_page = pages_manager.get_active_page()
    return {
        "active_page_id": active_page.get("id") if active_page else "",
        "active_page": active_page,
        "pages": pages
    }

class SwitchPageRequest(BaseModel):
    page_id: str

@app.post("/api/pages/switch")
async def switch_page_api(payload: SwitchPageRequest, request: Request):
    require_auth(request)
    success = pages_manager.set_active_page(payload.page_id)
    if success:
        active = pages_manager.get_active_page()
        # ซิงค์ค่า brand_config เข้ากับเพจใหม่
        if active:
            cfg = load_brand_config()
            cfg["brand_name"] = active.get("brand_name", cfg.get("brand_name"))
            cfg["tagline"] = active.get("tagline", cfg.get("tagline"))
            cfg["primary_color"] = active.get("primary_color", cfg.get("primary_color"))
            cfg["accent_color"] = active.get("accent_color", cfg.get("accent_color"))
            cfg["phone"] = active.get("phone", cfg.get("phone"))
            cfg["price_tag"] = active.get("price_tag", cfg.get("price_tag"))
            cfg["daily_post_time"] = active.get("daily_post_time", cfg.get("daily_post_time"))
            cfg["facebook_page_id"] = str(active.get("id"))
            save_brand_config(cfg)
        return {"success": True, "active_page": active}
    return {"success": False, "error": "ไม่พบรหัสเพจที่ต้องการสลับ"}

class SyncPagesRequest(BaseModel):
    user_token: str

@app.post("/api/pages/sync")
async def sync_pages_api(payload: SyncPagesRequest, request: Request):
    require_admin(request)
    result = pages_manager.sync_pages_from_facebook(payload.user_token)
    return result

class ConnectTokenRequest(BaseModel):
    token: str

@app.post("/api/pages/connect_token")
async def connect_token_api(payload: ConnectTokenRequest, request: Request):
    """
    รับ Facebook Token แล้วบันทึกใส่ .env และ managed_pages.json อัตโนมัติทันที
    """
    require_auth(request)
    result = pages_manager.auto_setup_token(payload.token)
    if result.get("success"):
        active = result.get("active_page")
        if active:
            cfg = load_brand_config()
            cfg["brand_name"] = active.get("brand_name", cfg.get("brand_name"))
            cfg["tagline"] = active.get("tagline", cfg.get("tagline"))
            cfg["primary_color"] = active.get("primary_color", cfg.get("primary_color"))
            cfg["accent_color"] = active.get("accent_color", cfg.get("accent_color"))
            cfg["phone"] = active.get("phone", cfg.get("phone"))
            cfg["price_tag"] = active.get("price_tag", cfg.get("price_tag"))
            cfg["daily_post_time"] = active.get("daily_post_time", cfg.get("daily_post_time"))
            cfg["facebook_page_id"] = str(active.get("id"))
            save_brand_config(cfg)
    return result

# ================= API ROUTES =================

@app.get("/api/posts")
async def get_posts(request: Request):
    require_auth(request)
    posts = load_schedule()
    # เรียงลำดับตามวันที่และเวลา
    posts.sort(key=lambda x: f"{x.get('date', '')} {x.get('time', '')}", reverse=True)
    return posts

class PostCreateRequest(BaseModel):
    date: str
    time: str
    topic: Optional[str] = ""
    content: Optional[str] = ""
    image_path: Optional[str] = None
    post_immediately: Optional[bool] = False

@app.post("/api/posts")
async def create_post(payload: PostCreateRequest, request: Request):
    user = require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = active_page.get("id")
    page_name = active_page.get("brand_name") or active_page.get("name")
    
    if payload.post_immediately:
        # สั่งโพสต์ขึ้น Facebook ทันที
        poster = FacebookPoster()
        item = {
            "id": f"post_{int(time.time())}",
            "page_id": page_id,
            "page_name": page_name,
            "date": payload.date,
            "time": payload.time,
            "topic": payload.topic,
            "content": payload.content,
            "image_path": payload.image_path,
            "status": "pending",
            "created_by": user["username"]
        }
        success = execute_single_post(item, poster)
        if success:
            posts = load_schedule()
            posts.append(item)
            save_schedule(posts)
            return {"success": True, "url": item.get("post_url")}
        else:
            return {"success": False, "error": item.get("error", "Failed to post")}

    # บันทึกลงตารางล่วงหน้า
    new_post = add_scheduled_post(
        date_str=payload.date,
        time_str=payload.time,
        content=payload.content or "",
        topic=payload.topic or "",
        image_path=payload.image_path,
        page_id=page_id,
        page_name=page_name
    )
    new_post["created_by"] = user["username"]
    posts = load_schedule()
    for p in posts:
        if p["id"] == new_post["id"]:
            p["created_by"] = user["username"]
    save_schedule(posts)

    return {"success": True, "post": new_post}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str, request: Request):
    require_auth(request)
    posts = load_schedule()
    posts = [p for p in posts if p["id"] != post_id]
    save_schedule(posts)
    return {"success": True}

@app.post("/api/posts/{post_id}/post_now")
async def post_item_now(post_id: str, request: Request):
    require_auth(request)
    posts = load_schedule()
    target_post = None
    for p in posts:
        if p["id"] == post_id:
            target_post = p
            break
    
    if not target_post:
        return {"success": False, "error": "ไม่พบรายการโพสต์ดังกล่าว"}

    poster = FacebookPoster()
    success = execute_single_post(target_post, poster)
    save_schedule(posts)
    return {"success": success, "error": target_post.get("error")}

# ================= IMAGE UPLOAD & AI BRANDING APIS =================

@app.post("/api/upload_image")
async def upload_image_api(request: Request, file: UploadFile = File(...), watermark: bool = Form(True)):
    require_auth(request)
    os.makedirs("static/uploads", exist_ok=True)
    clean_name = os.path.basename(file.filename or "image.jpg").replace(" ", "_")
    filename = f"user_{int(time.time())}_{clean_name}"
    save_path = os.path.join("static", "uploads", filename)

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    if watermark:
        try:
            active_page = pages_manager.get_active_page() or {}
            brand_dna = active_page.get("brand_dna", {}) or {}
            brand_name = active_page.get("brand_name") or brand_dna.get("brand_name") or "Official"
            phone = active_page.get("phone") or brand_dna.get("phone") or ""
            import image_service
            image_service.apply_subtle_watermark(
                save_path,
                brand_name=brand_name,
                phone=phone,
                page_id=active_page.get("id"),
                picture_url=active_page.get("picture_url")
            )
        except Exception as e:
            print(f"[Watermark Error on Upload] {e}")

    return {
        "success": True,
        "image_path": save_path,
        "url": f"/static/uploads/{filename}"
    }

class GenerateImageRequest(BaseModel):
    topic: Optional[str] = ""
    caption: Optional[str] = ""
    apply_watermark: Optional[bool] = True

@app.post("/api/ai/generate_image")
async def generate_image_api(payload: GenerateImageRequest, request: Request):
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    brand_dna = active_page.get("brand_dna", {}) or {}
    brand_name = active_page.get("brand_name") or brand_dna.get("brand_name") or active_page.get("name") or "Official"
    business_type = brand_dna.get("business_type") or active_page.get("category") or ""
    phone = active_page.get("phone") or brand_dna.get("phone") or ""

    import image_service
    result = image_service.generate_ai_image(
        topic=payload.topic or "ภาพถ่ายสินค้าและบริการมืออาชีพ",
        caption=payload.caption or "",
        brand_name=brand_name,
        business_type=business_type,
        phone=phone,
        page_id=active_page.get("id"),
        picture_url=active_page.get("picture_url"),
        apply_watermark=payload.apply_watermark if payload.apply_watermark is not None else True
    )
    return result

class WatermarkRequest(BaseModel):
    image_path: str

@app.post("/api/ai/apply_watermark")
async def apply_watermark_api(payload: WatermarkRequest, request: Request):
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    brand_dna = active_page.get("brand_dna", {}) or {}
    brand_name = active_page.get("brand_name") or brand_dna.get("brand_name") or active_page.get("name") or "Official"
    phone = active_page.get("phone") or brand_dna.get("phone") or ""
    import image_service
    out_path = image_service.apply_subtle_watermark(
        payload.image_path,
        brand_name=brand_name,
        phone=phone,
        page_id=active_page.get("id"),
        picture_url=active_page.get("picture_url")
    )
    rel_url = "/" + out_path.replace("\\", "/").lstrip("/")
    return {
        "success": True,
        "image_path": out_path,
        "url": rel_url
    }

class EnhanceImageRequest(BaseModel):
    image_path: str
    title: Optional[str] = "ผลงานซ่อมจริงจากช่าง FixPack"
    subtitle: Optional[str] = "งานเรียบร้อย ปลอดภัย จบไวในแพ็กเกจเดียว"
    price: Optional[str] = "เหมาจ่าย 1,500.- (3 งาน)"
    phone: Optional[str] = "066-097-1257"

@app.post("/api/ai/enhance_image")
async def enhance_image_api(payload: EnhanceImageRequest, request: Request):
    require_auth(request)
    brand = load_brand_config()
    os.makedirs("static/uploads", exist_ok=True)
    out_name = f"enhanced_{int(time.time())}.jpg"
    out_path = os.path.join("static", "uploads", out_name)

    title = payload.title or "ผลงานซ่อมจริงจากช่าง FixPack"
    price = payload.price or brand.get("price_tag", "เหมาจ่าย 1,500.- (3 งาน)")
    phone = payload.phone or brand.get("phone", "066-097-1257")

    result = apply_brand_ci_to_uploaded_image(
        image_path=payload.image_path,
        output_path=out_path,
        title=title,
        subtitle=payload.subtitle or "งานเรียบร้อย ปลอดภัย จบไวในแพ็กเกจเดียว",
        price=price,
        phone=phone
    )
    if result:
        return {
            "success": True,
            "image_path": out_path,
            "url": f"/static/uploads/{out_name}"
        }
    return {"success": False, "error": "ไม่สามารถตกแต่งรูปภาพได้ ตรวจสอบไฟล์ต้นฉบับ"}

class GenerateBannerRequest(BaseModel):
    topic: Optional[str] = ""
    subheadline: Optional[str] = ""
    price: Optional[str] = ""
    phone: Optional[str] = ""

@app.post("/api/ai/generate_banner")
async def generate_banner_api(payload: GenerateBannerRequest, request: Request):
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    brand = load_brand_config()
    os.makedirs("static/uploads", exist_ok=True)
    out_name = f"banner_{int(time.time())}.png"
    out_path = os.path.join("static", "uploads", out_name)

    headline = payload.topic or active_page.get("brand_name") or "บริการระดับมืออาชีพ"
    price = payload.price or active_page.get("price_tag") or brand.get("price_tag", "")
    subheadline = payload.subheadline or active_page.get("tagline") or "บริการคุณภาพ ใส่ใจทุกขั้นตอน มั่นใจได้"

    # ลองสร้างด้วย Dynamic Brand Banner Generator (ตาม CI สีและโลโก้จริงของเพจ)
    try:
        from banner_generator import create_brand_banner
        banner_ok = create_brand_banner(
            page_info=active_page,
            headline=headline[:35],
            subheadline=subheadline[:55],
            price_tag=price,
            output_path=out_path
        )
        if banner_ok:
            return {
                "success": True,
                "image_path": out_path,
                "url": f"/static/uploads/{out_name}"
            }
    except Exception as e:
        print(f"[Banner Error] Fallback to technician banner: {e}")

    result = create_ai_technician_banner(
        photo_path="ai_technician.jpg",
        output_path=out_path,
        headline=headline[:35],
        subheadline=subheadline,
        price=price or "เหมาจ่าย 1,500.-",
        phone=active_page.get("phone") or "066-097-1257"
    )
    if result:
        return {
            "success": True,
            "image_path": out_path,
            "url": f"/static/uploads/{out_name}"
        }
    return {"success": False, "error": "ไม่สามารถสร้างแบนเนอร์ใหม่ได้"}

@app.get("/api/ai/random_topic")
async def get_random_topic(request: Request):
    require_auth(request)
    topic = random.choice(AUTO_TOPIC_POOL)
    return {"success": True, "topic": topic}

# ================= AI GENERATION APIS =================

class CaptionFromImageRequest(BaseModel):
    image_path: str
    user_hint: Optional[str] = ""

@app.post("/api/ai/caption_from_image")
async def api_caption_from_image(payload: CaptionFromImageRequest, request: Request):
    """
    วิเคราะห์รูปภาพด้วย Gemini Multimodal AI แล้วสร้างหัวข้อและแคปชั่นตาม Brand DNA ของเพจที่เลือกอยู่
    """
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}

    from scheduler_engine import resolve_image_path
    actual_path = resolve_image_path(payload.image_path)
    if not actual_path:
        return {"success": False, "error": f"ไม่พบไฟล์รูปภาพ: {payload.image_path}"}

    from content_generator import generate_caption_from_image
    result = generate_caption_from_image(
        image_path=actual_path,
        page_info=active_page,
        user_hint=payload.user_hint
    )
    return result

class GenerateCaptionRequest(BaseModel):
    topic: str

@app.post("/api/ai/generate_caption")
async def api_generate_caption(payload: GenerateCaptionRequest, request: Request):
    require_auth(request)
    try:
        active_page = pages_manager.get_active_page() or {}
        brand_name = active_page.get("brand_name") or "แบรนด์คุณภาพ"
        topic = payload.topic.strip() or f"บริการแนะนำจาก {brand_name}"

        from content_generator import create_facebook_post_content
        caption = create_facebook_post_content(topic=topic, page_info=active_page)
        return {"success": True, "caption": caption}
    except Exception as e:
        return {"success": False, "error": str(e)}

class PlanTopicsRequest(BaseModel):
    days: int = 7

@app.post("/api/ai/plan_topics")
async def api_plan_topics(payload: PlanTopicsRequest, request: Request):
    require_auth(request)
    days = min(max(payload.days, 3), 30)
    active_page = pages_manager.get_active_page() or {}

    from content_generator import generate_brand_topics
    topics_data = generate_brand_topics(page_info=active_page, days=days)
    return {"success": True, "topics": topics_data}

@app.post("/api/brand/learn_now")
async def api_brand_learn_now(request: Request):
    """
    ให้ AI สแกนศึกษาข้อมูลเพจปัจจุบันจาก Facebook Graph API และอัปเดต Brand DNA ทันที
    """
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id"))
    token = active_page.get("access_token")
    if not page_id or not token:
        return {"success": False, "error": "เพจนี้ยังไม่มี Page Access Token กรุณาซิงค์ Token ก่อน"}

    try:
        from brand_knowledge_engine import analyze_page_brand
        brand_dna = analyze_page_brand(page_id=page_id, page_access_token=token)
        if not brand_dna:
            return {"success": False, "error": "ไม่สามารถดึงข้อมูลเพจจาก Facebook ได้"}

        # อัปเดตลง managed_pages.json
        data = pages_manager.load_pages_data()
        for p in data.get("pages", []):
            if str(p.get("id")) == page_id:
                p["brand_dna"] = brand_dna
                p["brand_name"] = brand_dna.get("brand_name", p.get("brand_name"))
                p["tagline"] = brand_dna.get("tagline", p.get("tagline"))
                p["primary_color"] = brand_dna.get("primary_color", p.get("primary_color"))
                p["accent_color"] = brand_dna.get("accent_color", p.get("accent_color"))
                p["phone"] = brand_dna.get("phone", p.get("phone"))
                p["price_tag"] = brand_dna.get("price_tag", p.get("price_tag"))
                break
        pages_manager.save_pages_data(data)

        # อัปเดต brand_config
        cfg = load_brand_config()
        cfg["brand_name"] = brand_dna.get("brand_name", cfg.get("brand_name"))
        cfg["tagline"] = brand_dna.get("tagline", cfg.get("tagline"))
        cfg["primary_color"] = brand_dna.get("primary_color", cfg.get("primary_color"))
        cfg["accent_color"] = brand_dna.get("accent_color", cfg.get("accent_color"))
        cfg["phone"] = brand_dna.get("phone", cfg.get("phone"))
        cfg["price_tag"] = brand_dna.get("price_tag", cfg.get("price_tag"))
        save_brand_config(cfg)

        return {
            "success": True,
            "brand_dna": brand_dna,
            "message": f"AI ศึกษาข้อมูลแบรนด์ '{brand_dna.get('brand_name')}' สำเร็จเรียบร้อยแล้ว!"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/autopilot/run_now")
async def api_autopilot_run_now(request: Request):
    require_auth(request)
    poster = FacebookPoster()
    chosen_topic = random.choice(AUTO_TOPIC_POOL)
    auto_post = {
        "id": f"auto_{int(time.time())}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "topic": chosen_topic,
        "content": "",
        "image_path": "fixpack_ai_banner.png",
        "status": "pending",
        "type": "autopilot_generated"
    }
    success = execute_single_post(auto_post, poster)
    posts = load_schedule()
    posts.append(auto_post)
    save_schedule(posts)
    return {"success": success, "error": auto_post.get("error")}

# ================= ADMIN & BRAND CI APIS =================

@app.get("/api/admin/brand")
async def get_brand(request: Request):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    cfg = load_brand_config()
    dna = active_page.get("brand_dna", {}) or {}

    core_services = dna.get("core_services", [])
    if isinstance(core_services, list):
        core_services_text = "\n".join(core_services)
    else:
        core_services_text = str(core_services or "")

    selling_points = dna.get("selling_points", [])
    if isinstance(selling_points, list):
        selling_points_text = "\n".join(selling_points)
    else:
        selling_points_text = str(selling_points or "")

    return {
        "brand_name": active_page.get("brand_name") or dna.get("brand_name") or cfg.get("brand_name", ""),
        "tagline": active_page.get("tagline") or dna.get("tagline") or cfg.get("tagline", ""),
        "business_type": dna.get("business_type") or active_page.get("category", ""),
        "brand_story": dna.get("brand_story") or active_page.get("brand_story", ""),
        "target_audience": dna.get("target_audience") or active_page.get("target_audience", ""),
        "core_services": core_services_text,
        "selling_points": selling_points_text,
        "tone_of_voice": dna.get("tone_of_voice") or active_page.get("tone_of_voice", ""),
        "negative_guidelines": dna.get("negative_guidelines") or active_page.get("negative_guidelines", ""),
        "primary_color": active_page.get("primary_color") or cfg.get("primary_color", "#0B3B60"),
        "accent_color": active_page.get("accent_color") or cfg.get("accent_color", "#FF5B00"),
        "phone": active_page.get("phone") or cfg.get("phone", "066-097-1257"),
        "price_tag": active_page.get("price_tag") or cfg.get("price_tag", ""),
        "daily_post_time": active_page.get("daily_post_time") or cfg.get("daily_post_time", "09:30"),
        "facebook_page_id": str(active_page.get("id", ""))
    }

class BrandConfigRequest(BaseModel):
    brand_name: str
    tagline: str
    primary_color: str
    accent_color: str
    phone: str
    price_tag: str
    daily_post_time: str
    business_type: Optional[str] = ""
    brand_story: Optional[str] = ""
    target_audience: Optional[str] = ""
    core_services: Optional[str] = ""
    selling_points: Optional[str] = ""
    tone_of_voice: Optional[str] = ""
    negative_guidelines: Optional[str] = ""

@app.post("/api/admin/brand")
async def update_brand(payload: BrandConfigRequest, request: Request):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))

    def _to_list(val: Optional[str]) -> List[str]:
        if not val:
            return []
        lines = [line.strip().lstrip("•-*1234567890. ") for line in val.replace(",", "\n").split("\n")]
        return [l for l in lines if l]

    core_services_list = _to_list(payload.core_services)
    selling_points_list = _to_list(payload.selling_points)

    # 1. Update managed_pages.json for active page
    if page_id:
        pages_data = pages_manager.load_pages_data()
        for p in pages_data.get("pages", []):
            if str(p.get("id")) == page_id:
                p["brand_name"] = payload.brand_name
                p["tagline"] = payload.tagline
                p["primary_color"] = payload.primary_color
                p["accent_color"] = payload.accent_color
                p["phone"] = payload.phone
                p["price_tag"] = payload.price_tag
                p["daily_post_time"] = payload.daily_post_time

                dna = p.get("brand_dna", {}) or {}
                dna["brand_name"] = payload.brand_name
                dna["tagline"] = payload.tagline
                dna["primary_color"] = payload.primary_color
                dna["accent_color"] = payload.accent_color
                dna["phone"] = payload.phone
                dna["price_tag"] = payload.price_tag
                dna["business_type"] = payload.business_type or dna.get("business_type", "")
                dna["brand_story"] = payload.brand_story or ""
                dna["target_audience"] = payload.target_audience or ""
                dna["core_services"] = core_services_list if core_services_list else dna.get("core_services", [])
                dna["selling_points"] = selling_points_list if selling_points_list else dna.get("selling_points", [])
                dna["tone_of_voice"] = payload.tone_of_voice or ""
                dna["negative_guidelines"] = payload.negative_guidelines or ""
                p["brand_dna"] = dna
                break
        pages_manager.save_pages_data(pages_data)

    # 2. Update brand_config.json
    cfg = load_brand_config()
    cfg.update(payload.dict())
    save_brand_config(cfg)

    return {"success": True, "message": "บันทึกการตั้งค่า CI และตัวตนแบรนด์เรียบร้อยแล้ว"}

# ================= BRAND DOCUMENTS & KNOWLEDGE APIS =================

@app.get("/api/brand/documents")
async def get_brand_documents_api(request: Request):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    import document_knowledge_engine as dke
    docs = dke.load_documents_metadata(page_id)
    return {"success": True, "documents": docs}

@app.post("/api/brand/documents/upload")
async def upload_brand_document_api(request: Request, file: UploadFile = File(...)):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    if not page_id:
        return {"success": False, "error": "ไม่พบรหัสเพจที่กำลังใช้งาน"}

    content = await file.read()
    if not content:
        return {"success": False, "error": "ไฟล์ว่างเปล่า"}

    import document_knowledge_engine as dke
    doc_info = dke.add_document(page_id, file.filename, content)
    return {"success": True, "document": doc_info}

@app.delete("/api/brand/documents/{doc_id}")
async def delete_brand_document_api(doc_id: str, request: Request):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    import document_knowledge_engine as dke
    deleted = dke.delete_document(page_id, doc_id)
    return {"success": deleted}

@app.post("/api/brand/documents/analyze")
async def analyze_brand_documents_api(request: Request):
    require_admin(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    if not page_id:
        return {"success": False, "error": "ไม่พบรหัสเพจ"}

    import document_knowledge_engine as dke
    current_dna = active_page.get("brand_dna", {}) or {}
    result = dke.analyze_documents_and_extract_brand_dna(page_id, current_dna)

    if result.get("success") and "brand_dna" in result:
        extracted = result["brand_dna"]
        pages_data = pages_manager.load_pages_data()
        for p in pages_data.get("pages", []):
            if str(p.get("id")) == page_id:
                p_dna = p.get("brand_dna", {}) or {}
                for k, v in extracted.items():
                    if v:
                        p_dna[k] = v
                p["brand_dna"] = p_dna
                if extracted.get("brand_name"):
                    p["brand_name"] = extracted["brand_name"]
                if extracted.get("tagline"):
                    p["tagline"] = extracted["tagline"]
                if extracted.get("phone"):
                    p["phone"] = extracted["phone"]
                if extracted.get("price_tag"):
                    p["price_tag"] = extracted["price_tag"]
                break
        pages_manager.save_pages_data(pages_data)

        # Update brand_config.json as well
        cfg = load_brand_config()
        if extracted.get("brand_name"):
            cfg["brand_name"] = extracted["brand_name"]
        if extracted.get("tagline"):
            cfg["tagline"] = extracted["tagline"]
        if extracted.get("phone"):
            cfg["phone"] = extracted["phone"]
        if extracted.get("price_tag"):
            cfg["price_tag"] = extracted["price_tag"]
        save_brand_config(cfg)

    return result

@app.get("/api/admin/users")
async def get_users_api(request: Request):
    require_admin(request)
    users = load_users()
    # ซ่อน password_hash เพื่อความปลอดภัย
    return [{"username": u["username"], "name": u["name"], "role": u["role"]} for u in users]

class UserAddRequest(BaseModel):
    username: str
    name: str
    password: str
    role: str

@app.post("/api/admin/users")
async def add_user_api(payload: UserAddRequest, request: Request):
    require_admin(request)
    users = load_users()
    if any(u["username"] == payload.username for u in users):
        return {"success": False, "error": "ชื่อผู้ใช้นี้มีในระบบแล้ว"}

    new_user = {
        "username": payload.username,
        "name": payload.name,
        "password_hash": hash_password(payload.password),
        "role": payload.role if payload.role in ["admin", "owner", "staff"] else "staff",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    users.append(new_user)
    save_users(users)
    return {"success": True}

@app.delete("/api/admin/users/{username}")
async def delete_user_api(username: str, request: Request):
    require_admin(request)
    if username == "admin":
        return {"success": False, "error": "ไม่อนุญาตให้ลบบัญชีผู้ดูแลระบบหลัก"}

    users = load_users()
    users = [u for u in users if u["username"] != username]
    save_users(users)
    return {"success": True}

import thai_holidays
from scheduler_engine import auto_schedule_holiday_post

# ================= THAI HOLIDAYS AUTO-PILOT APIS =================

@app.get("/api/holidays/upcoming")
async def get_upcoming_holidays_api(request: Request, days_ahead: int = 60):
    """
    ดึงรายการวันสำคัญและเทศกาลที่กำลังจะมาถึง พร้อมสถานะการตั้งเวลาโพสต์ของเพจที่กำลัง Active
    """
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    
    holidays = thai_holidays.get_upcoming_holidays(days_ahead=days_ahead)
    posts = load_schedule()
    
    enriched = []
    for h in holidays:
        h_copy = dict(h)
        matched_post = None
        for p in posts:
            same_h = (p.get("holiday_id") == h["id"]) or (
                p.get("date") == h["date"] and p.get("holiday_name") == h["name"]
            )
            same_page = (not page_id) or (not p.get("page_id")) or (str(p.get("page_id")) == page_id)
            if same_h and same_page:
                matched_post = p
                break
        
        if matched_post:
            h_copy["is_scheduled"] = True
            h_copy["scheduled_post_id"] = matched_post.get("id")
            h_copy["scheduled_status"] = matched_post.get("status")
            h_copy["scheduled_date"] = matched_post.get("date")
            h_copy["scheduled_time"] = matched_post.get("time")
            h_copy["scheduled_topic"] = matched_post.get("topic")
            h_copy["scheduled_image"] = matched_post.get("image_path")
        else:
            h_copy["is_scheduled"] = False
            h_copy["scheduled_post_id"] = None
            h_copy["scheduled_status"] = None
            h_copy["scheduled_date"] = None
            h_copy["scheduled_time"] = None
            h_copy["scheduled_topic"] = None
            h_copy["scheduled_image"] = None
            
        enriched.append(h_copy)
        
    return {
        "success": True,
        "count": len(enriched),
        "days_ahead": days_ahead,
        "active_page_id": page_id,
        "holidays": enriched
    }

class AutoScheduleAllHolidaysRequest(BaseModel):
    days_ahead: Optional[int] = 60
    auto_image: Optional[bool] = True

@app.post("/api/holidays/auto_schedule_all")
async def auto_schedule_all_holidays_api(request: Request, payload: Optional[AutoScheduleAllHolidaysRequest] = None):
    """
    1-Click Auto-Pilot: สร้างเนื้อหาและตั้งเวลาโพสต์วันสำคัญทั้งหมดล่วงหน้าใน 60-90 วันสำหรับเพจ Active
    """
    require_auth(request)
    days_ahead = payload.days_ahead if payload and payload.days_ahead else 60
    auto_image = payload.auto_image if payload and payload.auto_image is not None else True
    
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    page_name = active_page.get("brand_name") or active_page.get("name") or "Official"
    
    holidays = thai_holidays.get_upcoming_holidays(days_ahead=days_ahead)
    posts = load_schedule()
    
    scheduled_results = []
    for h in holidays:
        is_already = any(
            ((p.get("holiday_id") == h["id"]) or (p.get("date") == h["date"] and p.get("holiday_name") == h["name"]))
            and (not page_id or not p.get("page_id") or str(p.get("page_id")) == page_id)
            for p in posts
        )
        if not is_already:
            scheduled_post = auto_schedule_holiday_post(
                holiday=h,
                page_id=page_id,
                page_name=page_name,
                auto_image=auto_image
            )
            if scheduled_post:
                scheduled_results.append({
                    "holiday_id": h["id"],
                    "holiday_name": h["name"],
                    "date": h["date"],
                    "post_id": scheduled_post.get("id"),
                    "status": scheduled_post.get("status")
                })
                posts = load_schedule()
                
    return {
        "success": True,
        "scheduled_count": len(scheduled_results),
        "days_ahead": days_ahead,
        "page_id": page_id,
        "page_name": page_name,
        "scheduled_holidays": scheduled_results
    }

class ScheduleSingleHolidayRequest(BaseModel):
    holiday_id: str
    auto_image: Optional[bool] = True

@app.post("/api/holidays/schedule_single")
async def schedule_single_holiday_api(payload: ScheduleSingleHolidayRequest, request: Request):
    """
    สั่ง AI สร้างเนื้อหาและตั้งเวลาโพสต์เฉพาะวันสำคัญที่เลือก
    """
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    page_id = str(active_page.get("id", ""))
    page_name = active_page.get("brand_name") or active_page.get("name") or "Official"
    
    holiday = thai_holidays.get_holiday_by_id(payload.holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลวันสำคัญรหัส: {payload.holiday_id}")
        
    scheduled_post = auto_schedule_holiday_post(
        holiday=holiday,
        page_id=page_id,
        page_name=page_name,
        auto_image=payload.auto_image if payload.auto_image is not None else True
    )
    
    return {
        "success": True,
        "holiday": holiday,
        "post": scheduled_post
    }

# ================= ENTRY POINT =================

def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def run_server(host: str = "0.0.0.0", port: int = 5050):
    import uvicorn
    import traceback
    local_ip = get_local_ip()
    print("\n" + "="*65)
    print("🌐 เว็บแดชบอร์ด FixPack Auto-Pilot พร้อมใช้งานแล้ว!")
    print(f"👉 เข้าจากเครื่องนี้ (Local):       http://localhost:{port}")
    print(f"📱 เข้าจากมือถือในวง Wi-Fi เดียวกัน: http://{local_ip}:{port}")
    print("🌍 เข้าจากอินเตอร์เน็ตภายนอก:      ดูวิธีเปิดอุโมงค์ออนไลน์ใน README.md")
    print("="*65 + "\n")
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except BaseException as e:
        with open("server_exit.log", "w", encoding="utf-8") as f:
            f.write(f"Server exited with exception: {type(e).__name__}: {e}\n")
            f.write(traceback.format_exc())
        raise

if __name__ == "__main__":
    run_server()
