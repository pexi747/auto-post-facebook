"""
โมดูลเรียนรู้และวิเคราะห์ข้อมูลแบรนด์ (Brand Knowledge Engine)
ทำการดึงข้อมูลจริงจาก Facebook Graph API (Profile, About, Description, Feed)
แล้วใช้ Gemini AI สังเคราะห์เป็น Brand DNA / Brand Knowledge Profile ประจำแต่ละเพจ
เพื่อให้ AI นำไปใช้คิดหัวข้อ แคปชั่น และออกแบบรูปภาพได้อย่างตรงกับธุรกิจ 100%
"""
import os
import sys
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv(override=True)

def fetch_raw_facebook_page_data(page_id: str, access_token: str) -> Dict[str, Any]:
    """ดึงข้อมูลดิบของเพจจาก Facebook Graph API"""
    profile_url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "fields": "id,name,about,description,bio,category,phone,website,single_line_address,picture.type(large)",
        "access_token": access_token
    }
    raw = {}
    try:
        res = requests.get(profile_url, params=params, timeout=12)
        if res.status_code == 200:
            raw = res.json()
    except Exception as e:
        print(f"⚠️ Error fetching profile for {page_id}: {e}")

    # ดึงตัวอย่างโพสต์จริงจากหน้าเพจ
    feed_url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    feed_params = {
        "fields": "message,created_time",
        "limit": 5,
        "access_token": access_token
    }
    recent_posts = []
    try:
        r_feed = requests.get(feed_url, params=feed_params, timeout=12)
        if r_feed.status_code == 200:
            for item in r_feed.json().get("data", []):
                msg = item.get("message", "").strip()
                if msg and len(msg) > 10:
                    recent_posts.append(msg[:300])
    except Exception as e:
        print(f"⚠️ Error fetching feed for {page_id}: {e}")

    raw["recent_posts"] = recent_posts[:3]
    return raw

def synthesize_brand_dna_with_ai(page_name: str, raw_fb_data: Dict[str, Any], current_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """ใช้ Gemini AI วิเคราะห์ข้อมูลที่ดึงมาจาก Facebook แล้วสรุป Brand DNA"""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    current_info = current_info or {}

    about = raw_fb_data.get("about") or current_info.get("tagline") or ""
    description = raw_fb_data.get("description") or ""
    category = raw_fb_data.get("category") or current_info.get("category") or "ธุรกิจทั่วไป"
    phone = raw_fb_data.get("phone") or current_info.get("phone") or "066-097-1257"
    website = raw_fb_data.get("website") or current_info.get("website") or ""
    recent_posts = "\n---\n".join(raw_fb_data.get("recent_posts", []))

    prompt = f"""
คุณเป็น Brand Strategist และ Creative Director ผู้เชี่ยวชาญระดับแนวหน้า
กรุณาวิเคราะห์ข้อมูลของเพจ Facebook ต่อไปนี้ แล้วสร้าง "Brand DNA & Content Strategy" ภาษาไทย:

ชื่อเพจ: {page_name}
หมวดหมู่บน Facebook: {category}
ข้อมูลเกี่ยวกับ (About): {about}
คำอธิบาย (Description): {description}
เบอร์โทร: {phone}
เว็บไซต์: {website}
ตัวอย่างโพสต์จริงในอดีต:
{recent_posts if recent_posts else 'ไม่มีข้อมูลโพสต์เดิม'}

คำสั่ง:
จงวิเคราะห์และตอบกลับในรูปแบบ JSON เท่านั้น โดยมีโครงสร้างดังนี้:
{{
  "brand_name": "ชื่อแบรนด์สั้นๆ ที่จดจำง่าย เช่น FixPack, Clean4U, สำรับคุณแม่",
  "business_type": "ประเภทธุรกิจแบบกระชับ เช่น บริการทำความสะอาดบ้านและออฟฟิศ, อาหารจัดเลี้ยงและข้าวกล่องเดลิเวอรี่, บริการซ่อมรถฉุกเฉินถึงที่",
  "tagline": "สโลแกนหรือคำโปรยประจำแบรนด์ที่ติดหูและน่าสนใจ",
  "target_audience": "กลุ่มลูกค้าเป้าหมายหลัก เช่น เจ้าของบ้าน/คอนโด, พนักงานออฟฟิศ, คนรักสุขภาพ",
  "core_services": [
    "บริการหรือสินค้าเด่นรายการที่ 1",
    "บริการหรือสินค้าเด่นรายการที่ 2",
    "บริการหรือสินค้าเด่นรายการที่ 3",
    "บริการหรือสินค้าเด่นรายการที่ 4"
  ],
  "selling_points": [
    "จุดเด่น/การรับประกันที่ 1 เช่น ช่างมืออาชีพผ่านการคัดกรอง",
    "จุดเด่นที่ 2 เช่น ราคาชัดเจนไม่มีบวกเพิ่ม",
    "จุดเด่นที่ 3 เช่น บริการถึงที่ภายใน 1 ชม."
  ],
  "tone_of_voice": "น้ำเสียงการสื่อสาร เช่น อบอุ่น เป็นกันเอง ชวนหิว หรือ น่าเชื่อถือ มั่นใจ รวดเร็ว",
  "primary_color": "รหัสสีหลัก Hex Code ที่เข้ากับธุรกิจนี้มากที่สุด เช่น #0B3B60, #2B6CB0, #C53030",
  "accent_color": "รหัสสีเด่น Hex Code เช่น #FF5B00, #38B2AC, #E53E3E, #DD6B20",
  "price_tag": "ข้อเสนอราคาหรือโปรโมชั่นตัวอย่าง เช่น เหมาจ่าย 1,500.-, เริ่มต้น 490.-, ส่งฟรีไม่มีขั้นต่ำ",
  "sample_hooks": [
    "ตัวอย่างพาดหัวโพสต์หยุดนิ้วโป้ง 1",
    "ตัวอย่างพาดหัวโพสต์หยุดนิ้วโป้ง 2",
    "ตัวอย่างพาดหัวโพสต์หยุดนิ้วโป้ง 3"
  ],
  "hashtags": [
    "#แท็กหลัก1",
    "#แท็กหลัก2",
    "#แท็กหลัก3",
    "#แท็กหลัก4"
  ]
}}
ตอบเป็น JSON เพียวๆ เท่านั้น
"""
    if not api_key:
        return {}

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for m in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]:
            try:
                resp = client.models.generate_content(model=m, contents=prompt)
                if resp and resp.text:
                    import re
                    match = re.search(r"\{.*\}", resp.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        data["model"] = m
                        return data
            except Exception as e:
                print(f"Model {m} error: {e}")
                continue
    except Exception as e:
        print(f"AI synthesis error: {e}")

    return {}
