"""
โมดูลสำหรับจัดการการโพสต์ไปยัง Facebook Page ผ่าน Meta Graph API
"""
import os
import sys
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

class FacebookPoster:
    def __init__(self, page_id: Optional[str] = None, access_token: Optional[str] = None, api_version: str = "v21.0"):
        # โหลดค่าล่าสุดจาก .env เสมอ (override ค่าเดิมในหน่วยความจำ)
        load_dotenv(override=True)

        # 1. ดึงข้อมูลจากเพจที่กำลัง Active ในระบบเป็นอันดับแรก เพื่อให้ตรงกับที่เลือกบนหน้าเว็บเสมอ
        active = {}
        target_token = access_token
        try:
            import pages_manager
            active = pages_manager.get_active_page() or {}
            if page_id and not target_token:
                target_p = pages_manager.get_page(page_id)
                if target_p and target_p.get("access_token"):
                    target_token = target_p.get("access_token")
        except Exception:
            pass

        self.page_id = str(page_id or active.get("id") or os.getenv("FACEBOOK_PAGE_ID", "")).strip()
        self.access_token = str(target_token or active.get("access_token") or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")).strip()
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self._ensure_page_token()

    def _update_env_token(self, new_token: str):
        """บันทึก Page Access Token ลงไฟล์ .env เพื่อใช้ครั้งต่อไปโดยอัตโนมัติ"""
        env_path = ".env"
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    if line.startswith("FACEBOOK_PAGE_ACCESS_TOKEN="):
                        new_lines.append(f"FACEBOOK_PAGE_ACCESS_TOKEN={new_token}\n")
                    else:
                        new_lines.append(line)
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception:
                pass

    def _ensure_page_token(self):
        """
        ตรวจสอบว่า Token ที่ได้เป็น Page Access Token หรือ User Access Token
        หากเป็น User Token จะทำการแปลงเป็น Page Access Token ให้เพจเป้าหมายโดยอัตโนมัติ
        เพื่อป้องกัน Error: publish_actions are not available
        """
        if not self.access_token or not self.page_id:
            return

        try:
            # 1. เช็คว่า Token ปัจจุบันเป็นของ Page หรือของ User
            check_url = f"{self.base_url}/me"
            r = requests.get(check_url, params={"access_token": self.access_token}, timeout=10)
            data = r.json()

            # ถ้า id ตรงกับ page_id แสดงว่าเป็น Page Token แล้ว
            if str(data.get("id")) == str(self.page_id):
                return

            # ถ้าไม่ใช่ แสดงว่าเป็น User Token -> ดึง Page Token จาก /me/accounts
            accounts_url = f"{self.base_url}/me/accounts"
            r_acc = requests.get(accounts_url, params={"access_token": self.access_token, "limit": 100}, timeout=10)
            acc_data = r_acc.json().get("data", [])
            for page in acc_data:
                if str(page.get("id")) == str(self.page_id):
                    self.access_token = page.get("access_token")
                    print(f"🔄 ตรวจพบ User Token: ระบบทำการสลับเป็น Page Access Token ให้เพจ '{page.get('name')}' อัตโนมัติเรียบร้อย")
                    self._update_env_token(self.access_token)
                    break
        except Exception:
            pass

    def validate_credentials(self) -> Dict[str, Any]:
        """ตรวจสอบความถูกต้องของ Page ID และ Access Token"""
        if not self.page_id or not self.access_token:
            return {
                "success": False,
                "error": "กรุณาระบุ FACEBOOK_PAGE_ID และ FACEBOOK_PAGE_ACCESS_TOKEN ในไฟล์ .env"
            }
        
        try:
            url = f"{self.base_url}/{self.page_id}"
            params = {
                "fields": "id,name,category",
                "access_token": self.access_token
            }
            res = requests.get(url, params=params, timeout=15)
            data = res.json()
            
            if res.status_code == 200:
                return {
                    "success": True,
                    "page_name": data.get("name"),
                    "page_id": data.get("id"),
                    "category": data.get("category")
                }
            else:
                err_msg = data.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Facebook API Error ({res.status_code}): {err_msg}"
                }
        except Exception as e:
            return {"success": False, "error": f"Connection Error: {str(e)}"}

    def post_text(self, message: str) -> Dict[str, Any]:
        """โพสต์ข้อความ (Text Post) ไปยัง Facebook Page"""
        if not message or not message.strip():
            return {"success": False, "error": "ข้อความโพสต์ต้องไม่เป็นค่าว่าง"}

        check = self.validate_credentials()
        if not check["success"]:
            return check

        url = f"{self.base_url}/{self.page_id}/feed"
        payload = {
            "message": message,
            "access_token": self.access_token
        }

        try:
            res = requests.post(url, data=payload, timeout=20)
            data = res.json()

            if res.status_code == 200 and "id" in data:
                return {
                    "success": True,
                    "post_id": data["id"],
                    "url": f"https://facebook.com/{data['id']}"
                }
            else:
                err_msg = data.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Failed to post ({res.status_code}): {err_msg}"
                }
        except Exception as e:
            return {"success": False, "error": f"Request exception: {str(e)}"}

    def post_image(self, image_path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """โพสต์รูปภาพพร้อมแคปชั่นไปยัง Facebook Page"""
        # Resolve image path cleanly
        actual_path = image_path
        if not os.path.exists(actual_path):
            candidates = [
                image_path.lstrip("/"),
                os.path.join("static", image_path.lstrip("/")),
                os.path.basename(image_path),
                os.path.join("static", os.path.basename(image_path)),
                os.path.join("static", "uploads", os.path.basename(image_path))
            ]
            for c in candidates:
                if os.path.exists(c) and os.path.isfile(c):
                    actual_path = c
                    break

        if not os.path.exists(actual_path):
            return {"success": False, "error": f"ไม่พบไฟล์รูปภาพที่: {image_path}"}
        image_path = actual_path

        check = self.validate_credentials()
        if not check["success"]:
            return check

        url = f"{self.base_url}/{self.page_id}/photos"
        data = {
            "access_token": self.access_token
        }
        if caption:
            data["caption"] = caption

        try:
            with open(image_path, "rb") as img_file:
                files = {"source": img_file}
                res = requests.post(url, data=data, files=files, timeout=40)
            
            resp_data = res.json()
            if res.status_code == 200 and "id" in resp_data:
                return {
                    "success": True,
                    "photo_id": resp_data["id"],
                    "post_id": resp_data.get("post_id", resp_data["id"]),
                    "url": f"https://facebook.com/{resp_data.get('post_id', resp_data['id'])}"
                }
            else:
                err_msg = resp_data.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Failed to post image ({res.status_code}): {err_msg}"
                }
        except Exception as e:
            return {"success": False, "error": f"Request exception: {str(e)}"}
