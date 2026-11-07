"""
โมดูลสำหรับจัดการระบบหลายเพจ (Multi-Page Management System)
รองรับ:
1. ซิงค์ดึงเพจทั้งหมดจากบัญชี Facebook อัตโนมัติด้วย 1 คลิก
2. สลับเพจที่กำลังจัดการ (Active Page Switcher)
3. แยกตารางโพสต์และค่า CI แบรนด์ของแต่ละเพจออกจากกัน
"""
import os
import sys
import json
import requests
from typing import List, Dict, Any, Optional

PAGES_CONFIG_FILE = "managed_pages.json"

def load_pages_data() -> Dict[str, Any]:
    """โหลดข้อมูลเพจทั้งหมดจากไฟล์"""
    if not os.path.exists(PAGES_CONFIG_FILE):
        # สร้างข้อมูลเพจเริ่มต้น (FixPack) จาก .env หรือค่า default
        default_page_id = os.getenv("FACEBOOK_PAGE_ID", "764713456731551")
        default_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        
        initial_data = {
            "active_page_id": default_page_id,
            "pages": [
                {
                    "id": default_page_id,
                    "name": "FixPack งานเล็กซ่อมครบจบในแพ็กเดียว",
                    "category": "Local service",
                    "access_token": default_token,
                    "brand_name": "FixPack",
                    "tagline": "งานเล็กซ่อมครบ จบในแพ็กเดียว",
                    "primary_color": "#0B3B60",
                    "accent_color": "#FF5B00",
                    "phone": "066-097-1257",
                    "price_tag": "เหมาจ่าย 1,500.-",
                    "daily_post_time": "09:30",
                    "auto_pilot_enabled": True
                }
            ]
        }
        save_pages_data(initial_data)
        return initial_data

    try:
        with open(PAGES_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ ไม่สามารถอ่านไฟล์ {PAGES_CONFIG_FILE}: {e}")
        return {"active_page_id": "", "pages": []}

def save_pages_data(data: Dict[str, Any]):
    """บันทึกข้อมูลเพจลงไฟล์"""
    try:
        with open(PAGES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ ไม่สามารถบันทึกไฟล์ {PAGES_CONFIG_FILE}: {e}")

def get_all_pages() -> List[Dict[str, Any]]:
    """คืนค่ารายชื่อเพจทั้งหมดที่อยู่ในระบบ"""
    data = load_pages_data()
    return data.get("pages", [])

def get_active_page() -> Optional[Dict[str, Any]]:
    """คืนค่าเพจที่กำลังใช้งานอยู่ปัจจุบัน"""
    data = load_pages_data()
    active_id = data.get("active_page_id")
    pages = data.get("pages", [])

    for p in pages:
        if str(p.get("id")) == str(active_id):
            return p

    if pages:
        return pages[0]
    return None

def set_active_page(page_id: str) -> bool:
    """สลับเพจที่กำลังใช้งาน"""
    data = load_pages_data()
    page_id_str = str(page_id)
    exists = any(str(p.get("id")) == page_id_str for p in data.get("pages", []))
    if not exists:
        return False

    data["active_page_id"] = page_id_str
    save_pages_data(data)

    # อัปเดตไฟล์ .env ให้ตรงกับเพจที่สลับ
    active_p = get_active_page()
    if active_p:
        update_env_active_page(active_p.get("id"), active_p.get("access_token"))

    return True

def update_env_active_page(page_id: str, access_token: str):
    """
    อัปเดตไฟล์ .env และหน่วยความจำ (os.environ) อัตโนมัติทันที
    เพื่อให้ระบบทุกส่วนสลับไปใช้ Page ID และ Token ของเพจใหม่แบบ Real-Time
    """
    env_path = ".env"
    lines = []
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    new_lines = []
    has_page_id = False
    has_token = False

    for line in lines:
        if line.startswith("FACEBOOK_PAGE_ID="):
            new_lines.append(f"FACEBOOK_PAGE_ID={page_id}\n")
            has_page_id = True
        elif line.startswith("FACEBOOK_PAGE_ACCESS_TOKEN="):
            new_lines.append(f"FACEBOOK_PAGE_ACCESS_TOKEN={access_token or ''}\n")
            has_token = True
        else:
            new_lines.append(line)

    if not has_page_id:
        new_lines.insert(0, f"FACEBOOK_PAGE_ID={page_id}\n")
    if not has_token:
        new_lines.insert(1, f"FACEBOOK_PAGE_ACCESS_TOKEN={access_token or ''}\n")

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"📝 [Auto-Env] อัปเดต .env อัตโนมัติ: FACEBOOK_PAGE_ID={page_id}")
    except Exception as e:
        print(f"⚠️ ไม่สามารถบันทึก .env: {e}")

    # อัปเดต os.environ ทันที เพื่อให้ทุก Service ใช้งานได้เลยโดยไม่ต้องรีสตาร์ท
    os.environ["FACEBOOK_PAGE_ID"] = str(page_id)
    if access_token:
        os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"] = str(access_token)

def auto_setup_token(token: str) -> Dict[str, Any]:
    """
    รับ Access Token (ทั้ง User Token และ Page Token)
    ตรวจจับอัตโนมัติ ดึงรายชื่อเพจและ Page Token ของทุกเพจ
    แล้วบันทึกลง .env และ managed_pages.json ทันที!
    """
    token = token.strip()
    if not token:
        return {"success": False, "error": "กรุณาระบุ Facebook Access Token"}

    try:
        # 1. ตรวจสอบข้อมูลเบื้องต้นจาก /me
        me_url = "https://graph.facebook.com/v21.0/me"
        r_me = requests.get(me_url, params={"fields": "id,name", "access_token": token}, timeout=15)
        me_data = r_me.json()

        if r_me.status_code != 200:
            err_msg = me_data.get("error", {}).get("message", "Token ไม่ถูกต้องหรือหมดอายุ")
            return {"success": False, "error": f"Facebook Error: {err_msg}"}

        me_id = str(me_data.get("id"))
        me_name = me_data.get("name", "")

        # 2. ลองดึง /me/accounts เผื่อเป็น User Token ที่ดูแลหลายเพจ
        acc_url = "https://graph.facebook.com/v21.0/me/accounts"
        params = {
            "fields": "id,name,category,access_token,picture.type(large)",
            "limit": 100,
            "access_token": token
        }
        r_acc = requests.get(acc_url, params=params, timeout=15)
        acc_data = r_acc.json()
        fb_pages = acc_data.get("data", [])

        current_data = load_pages_data()
        existing_pages = {str(p["id"]): p for p in current_data.get("pages", [])}

        synced_count = 0

        if fb_pages:
            # กรณีเป็น User Token ที่ได้รับรายการเพจพร้อม Page Token
            for p in fb_pages:
                p_id = str(p.get("id"))
                p_name = p.get("name")
                p_cat = p.get("category", "General")
                p_token = p.get("access_token")
                pic_url = p.get("picture", {}).get("data", {}).get("url")

                if p_id in existing_pages:
                    existing_pages[p_id]["access_token"] = p_token
                    existing_pages[p_id]["name"] = p_name
                    if pic_url:
                        existing_pages[p_id]["picture_url"] = pic_url
                else:
                    existing_pages[p_id] = {
                        "id": p_id,
                        "name": p_name,
                        "category": p_cat,
                        "access_token": p_token,
                        "picture_url": pic_url,
                        "brand_name": p_name.split(" ")[0],
                        "tagline": p_name,
                        "primary_color": "#0B3B60",
                        "accent_color": "#FF5B00",
                        "phone": "066-097-1257",
                        "price_tag": "เหมาจ่าย 1,500.-",
                        "daily_post_time": "09:30",
                        "auto_pilot_enabled": True
                    }
                synced_count += 1
        else:
            # กรณีผู้ใช้ส่ง Page Token ของเพจใดเพจหนึ่งมาโดยตรง
            if me_id in existing_pages:
                existing_pages[me_id]["access_token"] = token
                existing_pages[me_id]["name"] = me_name
            else:
                existing_pages[me_id] = {
                    "id": me_id,
                    "name": me_name,
                    "category": "Facebook Page",
                    "access_token": token,
                    "brand_name": me_name.split(" ")[0],
                    "tagline": me_name,
                    "primary_color": "#0B3B60",
                    "accent_color": "#FF5B00",
                    "phone": "066-097-1257",
                    "price_tag": "เหมาจ่าย 1,500.-",
                    "daily_post_time": "09:30",
                    "auto_pilot_enabled": True
                }
            synced_count = 1

        current_data["pages"] = list(existing_pages.values())

        # กำหนด Active Page: ถ้ามี FixPack ให้เลือก FixPack ก่อน หรือเลือกเพจที่ส่ง Token มา
        fixpack_id = "764713456731551"
        if not fb_pages:
            current_data["active_page_id"] = me_id
        elif fixpack_id in existing_pages and existing_pages[fixpack_id].get("access_token"):
            current_data["active_page_id"] = fixpack_id
        elif not current_data.get("active_page_id") and current_data["pages"]:
            current_data["active_page_id"] = current_data["pages"][0]["id"]

        save_pages_data(current_data)

        # บันทึกลง .env ทันที!
        active_page = None
        for p in current_data["pages"]:
            if str(p.get("id")) == str(current_data.get("active_page_id")):
                active_page = p
                break

        if active_page:
            update_env_active_page(active_page.get("id"), active_page.get("access_token"))

        return {
            "success": True,
            "count": synced_count,
            "active_page": active_page,
            "pages": current_data["pages"]
        }
    except Exception as e:
        return {"success": False, "error": f"Exception: {str(e)}"}

def add_or_update_page(page_info: Dict[str, Any]) -> Dict[str, Any]:
    """เพิ่มหรืออัปเดตเพจ"""
    data = load_pages_data()
    pages = data.get("pages", [])
    p_id = str(page_info.get("id"))

    found = False
    for i, p in enumerate(pages):
        if str(p.get("id")) == p_id:
            pages[i].update(page_info)
            found = True
            break

    if not found:
        # กำหนดค่าเริ่มต้นตามประเภทเพจ
        if "brand_name" not in page_info:
            page_info["brand_name"] = page_info.get("name", "My Brand").split(" ")[0]
        if "primary_color" not in page_info:
            page_info["primary_color"] = "#0B3B60"
        if "accent_color" not in page_info:
            page_info["accent_color"] = "#FF5B00"
        if "daily_post_time" not in page_info:
            page_info["daily_post_time"] = "09:30"
        if "auto_pilot_enabled" not in page_info:
            page_info["auto_pilot_enabled"] = True
            
        pages.append(page_info)

    if not data.get("active_page_id"):
        data["active_page_id"] = p_id

    data["pages"] = pages
    save_pages_data(data)
    return page_info

def delete_page(page_id: str) -> bool:
    """ลบเพจออกจากระบบ"""
    data = load_pages_data()
    pages = data.get("pages", [])
    p_id = str(page_id)
    new_pages = [p for p in pages if str(p.get("id")) != p_id]
    
    if len(new_pages) == len(pages):
        return False

    data["pages"] = new_pages
    if str(data.get("active_page_id")) == p_id:
        data["active_page_id"] = new_pages[0]["id"] if new_pages else ""

    save_pages_data(data)
    return True

def sync_pages_from_facebook(user_token: str) -> Dict[str, Any]:
    """
    ดึงรายชื่อเพจทั้งหมดที่ User เป็นแอดมิน ผ่าน Facebook Graph API (/me/accounts)
    พร้อม Page Access Token ของแต่ละเพจมาให้อัตโนมัติ!
    """
    if not user_token or not user_token.strip():
        return {"success": False, "error": "กรุณาระบุ User Access Token"}

    url = "https://graph.facebook.com/v21.0/me/accounts"
    params = {
        "fields": "id,name,category,access_token,tasks,picture.type(large)",
        "limit": 100,
        "access_token": user_token.strip()
    }

    try:
        res = requests.get(url, params=params, timeout=20)
        data = res.json()

        if res.status_code != 200:
            err_msg = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": f"Facebook Error ({res.status_code}): {err_msg}"}

        fb_pages = data.get("data", [])
        if not fb_pages:
            return {"success": False, "error": "ไม่พบเพจที่บัญชีนี้ดูแลอยู่ หรือไม่ได้ให้สิทธิ์เข้าถึงเพจ"}

        synced_count = 0
        current_data = load_pages_data()
        existing_pages = {str(p["id"]): p for p in current_data.get("pages", [])}

        for p in fb_pages:
            p_id = str(p.get("id"))
            p_name = p.get("name")
            p_cat = p.get("category", "General")
            p_token = p.get("access_token")
            pic_url = p.get("picture", {}).get("data", {}).get("url")

            if p_id in existing_pages:
                # อัปเดตเฉพาะ Token และรูปภาพ
                existing_pages[p_id]["access_token"] = p_token
                existing_pages[p_id]["name"] = p_name
                if pic_url:
                    existing_pages[p_id]["picture_url"] = pic_url
            else:
                # สร้างเพจใหม่
                existing_pages[p_id] = {
                    "id": p_id,
                    "name": p_name,
                    "category": p_cat,
                    "access_token": p_token,
                    "picture_url": pic_url,
                    "brand_name": p_name.split(" ")[0],
                    "tagline": p_name,
                    "primary_color": "#0B3B60",
                    "accent_color": "#FF5B00",
                    "phone": "066-097-1257",
                    "price_tag": "โปรโมชั่นพิเศษ",
                    "daily_post_time": "09:30",
                    "auto_pilot_enabled": True
                }
            synced_count += 1

        current_data["pages"] = list(existing_pages.values())
        if not current_data.get("active_page_id") and current_data["pages"]:
            current_data["active_page_id"] = current_data["pages"][0]["id"]

        save_pages_data(current_data)
        return {
            "success": True,
            "count": synced_count,
            "pages": current_data["pages"]
        }
    except Exception as e:
        return {"success": False, "error": f"Exception: {str(e)}"}
