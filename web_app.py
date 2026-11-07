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
        poster = FacebookPoster()
        last_autopilot = {"date": ""}
        while True:
            try:
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
    image_path: Optional[str] = "fixpack_ai_banner.png"
    post_immediately: Optional[bool] = False

@app.post("/api/posts")
async def create_post(payload: PostCreateRequest, request: Request):
    user = require_auth(request)
    
    if payload.post_immediately:
        # สั่งโพสต์ขึ้น Facebook ทันที
        poster = FacebookPoster()
        item = {
            "id": f"post_{int(time.time())}",
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
        image_path=payload.image_path or ""
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
async def upload_image_api(request: Request, file: UploadFile = File(...)):
    require_auth(request)
    os.makedirs("static/uploads", exist_ok=True)
    clean_name = os.path.basename(file.filename or "image.jpg").replace(" ", "_")
    filename = f"user_{int(time.time())}_{clean_name}"
    save_path = os.path.join("static", "uploads", filename)

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    return {
        "success": True,
        "image_path": save_path,
        "url": f"/static/uploads/{filename}"
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
    topic: Optional[str] = "เลือกซ่อมได้เอง 3 งานในบ้าน"
    subheadline: Optional[str] = "ไฟฟ้า • ประปา • ประตูหน้าต่าง • ติดตั้ง"
    price: Optional[str] = "เหมาจ่าย 1,500.-"
    phone: Optional[str] = "066-097-1257"

@app.post("/api/ai/generate_banner")
async def generate_banner_api(payload: GenerateBannerRequest, request: Request):
    require_auth(request)
    brand = load_brand_config()
    os.makedirs("static/uploads", exist_ok=True)
    out_name = f"banner_{int(time.time())}.png"
    out_path = os.path.join("static", "uploads", out_name)

    headline = payload.topic or "เลือกซ่อมได้เอง 3 งานในบ้าน"
    price = payload.price or brand.get("price_tag", "เหมาจ่าย 1,500.-")
    phone = payload.phone or brand.get("phone", "066-097-1257")

    result = create_ai_technician_banner(
        photo_path="ai_technician.jpg",
        output_path=out_path,
        headline=headline[:35],
        subheadline=payload.subheadline or "ไฟฟ้า • ประปา • ประตูหน้าต่าง • ติดตั้ง",
        price=price,
        phone=phone
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
    วิเคราะห์รูปภาพด้วย Gemini Multimodal AI แล้วสร้างหัวข้อและแคปชั่นตาม CI ของเพจที่เลือกอยู่
    """
    require_auth(request)
    active_page = pages_manager.get_active_page() or {}
    brand = load_brand_config()

    brand_name = active_page.get("brand_name") or brand.get("brand_name", "FixPack")
    tagline = active_page.get("tagline") or brand.get("tagline", "")
    phone = active_page.get("phone") or brand.get("phone", "066-097-1257")
    price = active_page.get("price_tag") or brand.get("price_tag", "")
    category = active_page.get("category", "บริการทั่วไป")

    from scheduler_engine import resolve_image_path
    actual_path = resolve_image_path(payload.image_path)
    if not actual_path:
        return {"success": False, "error": f"ไม่พบไฟล์รูปภาพ: {payload.image_path}"}

    from content_generator import generate_caption_from_image
    result = generate_caption_from_image(
        image_path=actual_path,
        brand_name=brand_name,
        tagline=tagline,
        phone=phone,
        price=price,
        category=category,
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
        brand = load_brand_config()
        brand_name = active_page.get("brand_name") or brand.get("brand_name", "FixPack")
        tagline = active_page.get("tagline") or brand.get("tagline", "")
        product_name = f"{brand_name} {tagline}".strip()

        topic = payload.topic.strip() or f"บริการจาก {brand_name}"
        caption = create_facebook_post_content(topic=topic, product=product_name)
        return {"success": True, "caption": caption}
    except Exception as e:
        return {"success": False, "error": str(e)}

class PlanTopicsRequest(BaseModel):
    days: int = 7

@app.post("/api/ai/plan_topics")
async def api_plan_topics(payload: PlanTopicsRequest, request: Request):
    require_auth(request)
    days = min(max(payload.days, 3), 30)

    # พยายามใช้ Gemini สร้างหัวข้อที่หลากหลาย
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
คุณเป็นผู้เชี่ยวชาญการวางแผนคอนเทนต์ Facebook สำหรับแบรนด์ 'FixPack งานเล็กซ่อมครบจบในแพ็กเดียว' 
(บริการช่างซ่อมบ้าน คอนโด งานเล็กๆ เช่น ประปา, ไฟฟ้า, ประตูหน้าต่าง, ยาแนวกระเบื้อง, ติดตั้งชั้นวาง, เหมา 3 งาน 1,500 บาท)

กรุณาวางแผนหัวข้อโพสต์จำนวน {days} วัน ในรูปแบบ JSON Array ตามตัวอย่าง:
[
  {{"topic": "ชื่อหัวข้อโพสต์ที่น่าสนใจ", "brief": "แนวทางการเล่าสั้นๆ", "category": "หมวดหมู่เช่น ประปา / ไฟฟ้า / โปรโมชั่น"}}
]
ตอบกลับเฉพาะโค้ด JSON เท่านั้น ห้ามมีคำอธิบายอื่น
"""
            resp = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
            clean_json = resp.text.strip().replace("```json", "").replace("```", "").strip()
            topics_data = json.loads(clean_json)
            return {"success": True, "topics": topics_data}
        except Exception:
            pass

    # Fallback สุ่มจากคลังหัวข้อ
    shuffled = list(AUTO_TOPIC_POOL)
    random.shuffle(shuffled)
    fallback_topics = []
    for i in range(days):
        t = shuffled[i % len(shuffled)]
        fallback_topics.append({
            "topic": t,
            "brief": "ให้ความรู้และนำเสนอแพ็กเกจเหมาซ่อม 3 งาน 1,500 บาทของ FixPack",
            "category": "งานซ่อมบำรุงบ้าน"
        })
    return {"success": True, "topics": fallback_topics}

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

# ================= ADMIN APIS =================

@app.get("/api/admin/brand")
async def get_brand(request: Request):
    require_admin(request)
    return load_brand_config()

class BrandConfigRequest(BaseModel):
    brand_name: str
    tagline: str
    primary_color: str
    accent_color: str
    phone: str
    price_tag: str
    daily_post_time: str

@app.post("/api/admin/brand")
async def update_brand(payload: BrandConfigRequest, request: Request):
    require_admin(request)
    cfg = load_brand_config()
    cfg.update(payload.dict())
    save_brand_config(cfg)
    return {"success": True}

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
