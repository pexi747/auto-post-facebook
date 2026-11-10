"""
ระบบจัดการตารางโพสต์ล่วงหน้าและโพสต์อัตโนมัติ (Auto-Pilot Content Scheduler) สำหรับ FixPack
คุณสมบัติ:
1. ใส่ข้อมูลโพสต์ล่วงหน้าได้ (ระบุ วันที่, เวลา, ข้อความเอง หรือระบุแค่หัวข้อให้ AI แต่ง)
2. วันไหนไม่มีโพสต์ที่ตั้งไว้ ระบบจะคิดหัวข้อใหม่ + สร้างโพสต์ด้วย AI + แนบภาพ CI แบรนด์ ให้เองอัตโนมัติ!
3. บันทึกประวัติและสถานะการโพสต์ลงไฟล์ scheduled_posts.json
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# บังคับ UTF-8 สำหรับ Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from dotenv import load_dotenv
load_dotenv()

from facebook_service import FacebookPoster
from content_generator import create_facebook_post_content, generate_post_with_ai
from create_ai_banner import create_ai_technician_banner

SCHEDULE_FILE = "scheduled_posts.json"
DEFAULT_DAILY_TIME = os.getenv("DAILY_POST_TIME", "09:30") # เวลาโพสต์เริ่มต้นหากไม่ได้กำหนด

# คลังหัวข้องานซ่อมและดูแลบ้านสำหรับ FixPack (กรณี AI คิดหัวข้ออัตโนมัติ)
AUTO_TOPIC_POOL = [
    "เช็ค 4 สัญญาณเตือนก๊อกน้ำและท่อประปาเริ่มรั่วซึม ก่อนค่าน้ำพุ่ง",
    "เปลี่ยนปลั๊กไฟและสวิตช์เก่า ป้องกันไฟไหม้และไฟฟ้าลัดวงจร",
    "หมดปัญหากลอนประตูฝืด ลูกบิดพัง บานพับตก ซ่อมง่ายจบในแพ็กเดียว",
    "เทคนิคการดูแลยาแนวกระเบื้องห้องน้ำ ไม่ให้ขึ้นราดำและน้ำรั่วซึม",
    "เจาะผนังแขวนของยังไงให้แข็งแรง ไม่ทำลายโครงสร้างบ้าน",
    "รวมงานซ่อมแซมเล็กๆ ในบ้านที่คุณไม่ต้องเสียเวลาทำเอง",
    "ข้อดีของบริการช่างซ่อมบ้านแบบเหมาจบ 3 งาน 1,500 บาท",
    "เตรียมบ้านรับมือหน้าฝน อุดรอยรั่วซึมขอบหน้าต่างและฝ้าเพดาน",
    "เปลี่ยนหลอดไฟธรรมดาเป็น LED ประหยัดไฟและยืดอายุการใช้งาน",
    "ทำไมคนอยู่คอนโดและบ้านยุคใหม่ถึงเลือกใช้บริการ FixPack"
]

def load_schedule() -> List[Dict[str, Any]]:
    """โหลดรายการโพสต์ที่ตั้งเวลาไว้"""
    if not os.path.exists(SCHEDULE_FILE):
        return []
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ ไม่สามารถอ่านไฟล์ {SCHEDULE_FILE} ได้: {e}")
        return []

def save_schedule(posts: List[Dict[str, Any]]):
    """บันทึกรายการโพสต์ลงไฟล์"""
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ ไม่สามารถบันทึกไฟล์ {SCHEDULE_FILE} ได้: {e}")

def add_scheduled_post(
    date_str: str,
    time_str: str = "09:30",
    content: str = "",
    topic: str = "",
    image_path: Optional[str] = None,
    page_id: Optional[str] = None,
    page_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    เพิ่มโพสต์ลงในตารางล่วงหน้า
    :param date_str: วันที่ในรูปแบบ YYYY-MM-DD เช่น 2026-11-07
    :param time_str: เวลาในรูปแบบ HH:MM เช่น 10:00
    :param content: ข้อความที่ต้องการโพสต์ (หากเว้นว่าง ระบบจะนำ topic ไปให้ AI เขียนให้)
    :param topic: หัวข้อสำหรับให้ AI เขียนโพสต์
    :param image_path: รูปภาพที่จะแนบ
    :param page_id: ID ของเพจ Facebook ปลายทาง
    :param page_name: ชื่อเพจหรือแบรนด์
    """
    posts = load_schedule()
    new_id = f"post_{int(time.time())}_{len(posts) + 1}"
    
    post_item = {
        "id": new_id,
        "page_id": page_id,
        "page_name": page_name,
        "date": date_str,
        "time": time_str,
        "topic": topic,
        "content": content,
        "image_path": image_path,
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "posted_at": None,
        "post_url": None
    }
    posts.append(post_item)
    # เรียงลำดับตามวันและเวลา
    posts.sort(key=lambda x: f"{x.get('date', '')} {x.get('time', '')}")
    save_schedule(posts)
    return post_item

def resolve_image_path(path: Optional[str]) -> Optional[str]:
    """ค้นหาไฟล์ภาพจาก path ต่างๆ ให้เจออย่างแม่นยำ"""
    if not path:
        return None
    cleaned = path.strip().lstrip("/")
    candidates = [
        cleaned,
        os.path.join("static", cleaned),
        os.path.basename(cleaned),
        os.path.join("static", os.path.basename(cleaned)),
        os.path.join("static", "uploads", os.path.basename(cleaned))
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return c
    return None

def execute_single_post(post: Dict[str, Any], poster: FacebookPoster) -> bool:
    """สั่งโพสต์ข้อมูล 1 โพสต์ขึ้นเพจ Facebook"""
    if post.get("page_id") and str(post.get("page_id")) != str(poster.page_id):
        try:
            import pages_manager
            target_page = pages_manager.get_page(post.get("page_id"))
            if target_page and target_page.get("access_token"):
                poster = FacebookPoster(page_id=str(post.get("page_id")), access_token=target_page.get("access_token"))
        except Exception as e:
            print(f"⚠️ ไม่สามารถสลับไปยังเพจ {post.get('page_id')}: {e}")

    content = post.get("content", "").strip()
    topic = post.get("topic", "").strip()

    # หากไม่มีเนื้อหาเตรียมไว้ ให้ AI ช่วยเขียนตามหัวข้อ
    if not content:
        if not topic:
            topic = random.choice(AUTO_TOPIC_POOL)
        print(f"\n🤖 กำลังให้ AI เขียนแคปชั่นโพสต์สำหรับหัวข้อ: '{topic}'...")
        content = create_facebook_post_content(topic=topic)
        post["content"] = content

    image_path = post.get("image_path")
    # หากระบุภาพไว้แต่ไฟล์ยังไม่ถูกสร้าง หรือเป็น default ให้ตรวจสอบ
    if image_path == "fixpack_ai_banner.png" and not os.path.exists(image_path):
        print("🎨 กำลังสร้างรูปภาพแบนเนอร์ช่าง AI อัตโนมัติ...")
        create_ai_technician_banner()

    resolved_img = resolve_image_path(image_path)
    print(f"\n📤 กำลังโพสต์ไปยัง Facebook Page (ID: {post.get('id')})...")
    if resolved_img:
        result = poster.post_image(resolved_img, caption=content)
    else:
        result = poster.post_text(content)

    if result["success"]:
        post["status"] = "posted"
        post["posted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post["post_url"] = result.get("url")
        print(f"✅ โพสต์สำเร็จเรียบร้อยแล้ว!")
        print(f"🔗 ลิงก์โพสต์: {result.get('url')}")
        return True
    else:
        post["status"] = "failed"
        post["error"] = result.get("error")
        print(f"❌ โพสต์ไม่สำเร็จ: {result.get('error')}")
        return False

def check_and_execute_due_posts(poster: FacebookPoster):
    """ตรวจสอบว่ามีโพสต์ล่วงหน้าถึงเวลาที่ต้องโพสต์แล้วหรือไม่"""
    posts = load_schedule()
    now = datetime.now()
    now_date = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M")
    
    updated = False
    for post in posts:
        if post.get("status") == "pending":
            post_date = post.get("date")
            post_time = post.get("time", "09:30")
            
            # ถ้าถึงหรือเลยเวลาที่กำหนดแล้ว
            if (post_date < now_date) or (post_date == now_date and post_time <= now_time):
                print(f"\n⏰ ตรวจพบโพสต์ตามกำหนดการ: {post_date} {post_time}")
                success = execute_single_post(post, poster)
                updated = True

    if updated:
        save_schedule(posts)

# ================= THAI HOLIDAYS AUTO-PILOT SCHEDULER =================

# Diff / Replacement for scheduler_engine.py:

def auto_schedule_holiday_post(
    holiday: Dict[str, Any],
    page_id: Optional[str] = None,
    page_name: Optional[str] = None,
    auto_image: bool = True,
    user_config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    posts = load_schedule()
    target_pid = str(page_id) if page_id else ""
    h_id = holiday.get("id")
    h_name = holiday.get("name")
    h_date = holiday.get("date")

    # 1. ป้องกันการตั้งเวลาซ้ำซ้อน
    for p in posts:
        same_h = (p.get("holiday_id") == h_id) or (
            p.get("date") == h_date and p.get("holiday_name") == h_name
        )
        same_page = (not target_pid) or (not p.get("page_id")) or (str(p.get("page_id")) == target_pid)
        if same_h and same_page:
            return p

    # 2. ดึงข้อมูลเพจ
    target_page_info = None
    try:
        import pages_manager
        if target_pid:
            target_page_info = pages_manager.get_page(target_pid)
        if not target_page_info:
            target_page_info = pages_manager.get_active_page() or {}
    except Exception:
        target_page_info = {}

    display_page_name = page_name or (target_page_info.get("brand_name") or target_page_info.get("name") or "FixPack")

    # 3. ให้ AI ร่างเนื้อหาเฉพาะวันสำคัญ
    from content_generator import generate_holiday_post
    holiday_content = generate_holiday_post(holiday, page_info=target_page_info, user_config=user_config)
    topic = holiday_content.get("topic") or f"สุขสันต์{h_name}"
    content = holiday_content.get("content") or ""
    visual_concept = holiday_content.get("visual_concept") or holiday.get("visual_theme") or topic

    # 4. สร้างรูปภาพประกอบวันสำคัญแท้จริง (ไม่ส่ง business_type เพื่อไม่ให้มีช่างหรือเครื่องมือ)
    image_path = None
    if auto_image:
        try:
            import image_service
            phone = target_page_info.get("phone") or (target_page_info.get("brand_dna", {}) or {}).get("phone")
            pic_url = target_page_info.get("picture_url")

            print(f"🎨 [Thai Holiday AI Image] กำลังสร้างภาพประกอบวัฒนธรรมสำหรับ {h_name}...")
            img_res = image_service.generate_ai_image(
                topic=topic,
                caption=visual_concept,
                brand_name=display_page_name,
                business_type="",  # ห้ามส่ง business_type สำหรับวันสำคัญ
                phone=phone,
                page_id=target_pid,
                picture_url=pic_url,
                apply_watermark=True,
                user_config=user_config
            )
            if img_res.get("success") and img_res.get("image_path"):
                image_path = img_res["image_path"]
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการสร้างภาพ AI วันสำคัญ: {e}")

    # หมายเหตุ: นำ fallback fixpack_ai_banner.png ออก เพื่อไม่ให้ติดภาพช่างซ่อมในวันสำคัญ

    # 5. บันทึกลงตารางโพสต์
    new_id = f"holiday_{h_id}_{int(time.time())}_{random.randint(100, 999)}"
    post_item = {
        "id": new_id,
        "page_id": target_pid,
        "page_name": display_page_name,
        "date": h_date,
        "time": holiday.get("default_time", "08:30"),
        "topic": topic,
        "content": content,
        "image_path": image_path,
        "status": "pending",
        "type": "holiday_auto_scheduled",
        "holiday_id": h_id,
        "holiday_name": h_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "posted_at": None,
        "post_url": None
    }

    posts.append(post_item)
    posts.sort(key=lambda x: f"{x.get('date', '')} {x.get('time', '')}")
    save_schedule(posts)
    print(f"✅ [Auto-Pilot Holiday] ตั้งเวลาโพสต์วันสำคัญสำเร็จ: {h_name} ({h_date} {post_item['time']} น.)")
    return post_item


def cleanup_holiday_banner_images() -> int:
    """
    ตรวจจับโพสต์วันสำคัญใน scheduled_posts.json ที่ติดภาพ fixpack_ai_banner.png
    แล้วสร้างภาพวัฒนธรรมวันสำคัญจริงมาแทนที่ทันที
    """
    posts = load_schedule()
    updated_count = 0
    import image_service

    for post in posts:
        is_holiday = (post.get("type") == "holiday_auto_scheduled") or post.get("holiday_id")
        img = post.get("image_path")
        if is_holiday and (img == "fixpack_ai_banner.png" or not img):
            h_name = post.get("holiday_name") or post.get("topic") or "วันสำคัญ"
            print(f"🔄 [Holiday Realignment] สร้างภาพวันสำคัญแท้จริงแทนที่แบนเนอร์ช่าง: {h_name}...")
            img_res = image_service.generate_ai_image(
                topic=post.get("topic") or h_name,
                caption=post.get("content") or "",
                brand_name=post.get("page_name") or "FixPack",
                business_type="",  # ไม่ใส่ business_type เพื่อภาพวัฒนธรรมแท้จริง
                page_id=post.get("page_id"),
                apply_watermark=True
            )
            if img_res.get("success") and img_res.get("image_path"):
                post["image_path"] = img_res["image_path"]
                updated_count += 1
                print(f"✅ ปรับภาพวันสำคัญสำเร็จ: {h_name} -> {img_res['image_path']}")

    if updated_count > 0:
        save_schedule(posts)
        print(f"🎉 อัปเดตภาพวันสำคัญใน scheduled_posts.json ทั้งหมด {updated_count} รายการ")

    return updated_count

def check_and_execute_autopilot_daily(poster: FacebookPoster, last_autopilot_date: Dict[str, str]):
    """
    ระบบ Auto-Pilot:
    1. ตรวจสอบและตั้งเวลาโพสต์วันสำคัญล่วงหน้า 7 วันอัตโนมัติ (Thai Holidays Auto-Pilot)
    2. วันไหนไม่มีโพสต์ที่ตั้งไว้ เมื่อถึงเวลาประจำวัน จะคิดหัวข้อและโพสต์ให้อัตโนมัติทันที
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M")

    # 1. ตรวจสอบวันสำคัญล่วงหน้า 7 วัน และตั้งเวลาให้อัตโนมัติ
    try:
        import thai_holidays
        upcoming_holidays = thai_holidays.get_upcoming_holidays(from_date=today_str, days_ahead=7)
        if upcoming_holidays:
            target_pid = str(poster.page_id) if poster and poster.page_id else ""
            target_pname = ""
            try:
                import pages_manager
                active_p = pages_manager.get_page(target_pid) or pages_manager.get_active_page() or {}
                target_pname = active_p.get("brand_name") or active_p.get("name") or "FixPack"
            except Exception:
                target_pname = "FixPack"

            for nh in upcoming_holidays:
                auto_schedule_holiday_post(
                    holiday=nh,
                    page_id=target_pid,
                    page_name=target_pname,
                    auto_image=True
                )
    except Exception as e:
        print(f"⚠️ ตรวจสอบวันสำคัญอัตโนมัติขัดข้อง: {e}")

    # 2. Auto-Pilot ประจำวัน (กรณีไม่มีโพสต์ใดๆ ในวันนี้)
    if last_autopilot_date.get("date") == today_str:
        return

    if now_time >= DEFAULT_DAILY_TIME:
        posts = load_schedule()
        has_user_post_today = any(p.get("date") == today_str for p in posts)
        
        if not has_user_post_today:
            print(f"\n💡 [Auto-Pilot FixPack] วันนี้ ({today_str}) ยังไม่มีรายการโพสต์ที่ตั้งไว้ล่วงหน้า")
            print("🚀 ระบบกำลังเริ่มกระบวนการคิดหัวข้อและโพสต์ให้อัตโนมัติ...")
            
            chosen_topic = random.choice(AUTO_TOPIC_POOL)
            auto_post = {
                "id": f"auto_{int(time.time())}",
                "date": today_str,
                "time": now_time,
                "topic": chosen_topic,
                "content": "",
                "image_path": "fixpack_ai_banner.png",
                "status": "pending",
                "type": "autopilot_generated"
            }
            
            success = execute_single_post(auto_post, poster)
            posts.append(auto_post)
            save_schedule(posts)
            last_autopilot_date["date"] = today_str

def run_autopilot_service(check_interval_seconds: int = 30):
    """เริ่มรัน Service โพสต์อัตโนมัติในพื้นหลัง (ทำงานวนรอบ)"""
    poster = FacebookPoster()
    val = poster.validate_credentials()
    if not val["success"]:
        print(f"❌ ไม่สามารถเริ่มระบบได้: {val.get('error')}")
        return

    print("=" * 60)
    print("🤖 ระบบ AUTO-PILOT โพสต์ Facebook ทำงานแล้ว!")
    print(f"📌 เพจเป้าหมาย: {val.get('page_name')}")
    print(f"⏰ เวลาโพสต์อัตโนมัติประจำวัน (กรณีไม่ได้ใส่ล่วงหน้า): ทุกวัน {DEFAULT_DAILY_TIME} น.")
    print(f"📂 ไฟล์ตารางโพสต์: {SCHEDULE_FILE}")
    print("ℹ️ กด Ctrl + C เพื่อหยุดการทำงานของระบบ")
    print("=" * 60)

    last_autopilot_date = {"date": ""}

    while True:
        try:
            # 1. ตรวจสอบโพสต์ล่วงหน้าที่ผู้ใช้กำหนดไว้
            check_and_execute_due_posts(poster)
            
            # 2. ตรวจสอบระบบ Auto-Pilot สำหรับวันที่ไม่ได้กำหนดโพสต์
            check_and_execute_autopilot_daily(poster, last_autopilot_date)
            
            time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 หยุดการทำงานของระบบ Auto-Pilot แล้ว")
            break
        except Exception as e:
            print(f"\n⚠️ เกิดข้อผิดพลาดชั่วคราวในลูปการทำงาน: {e}")
            time.sleep(15)

if __name__ == "__main__":
    run_autopilot_service()
