"""
โมดูลบริการสร้างรูปภาพด้วย AI และระบบใส่ลายน้ำป้องกันการคัดลอก (AI Image & Watermark Service)
หน้าที่:
1. สร้างภาพประกอบโพสต์ด้วย AI ตามหัวข้อ/แคปชั่น และ Brand DNA (AI-Generated Commercial Image)
2. ใส่ลายน้ำแบรนด์ (Subtle Watermark) เล็กน้อยแบบมืออาชีพ ป้องกันการนำรูปไปใช้ทุกครั้ง
"""
import os
import sys
import time
import urllib.parse
import urllib.request
import re
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv(override=True)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

UPLOADS_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _get_thai_font(size: int):
    """ค้นหาฟอนต์ที่รองรับภาษาไทยบนระบบ"""
    font_paths = [
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/leelawad.ttf",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def apply_subtle_watermark(
    image_path: str,
    brand_name: str = "Brand",
    phone: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    ใส่ลายน้ำแบรนด์แบบเรียบหรูและแนบเนียน ป้องกันการคัดลอกรูปไปใช้:
    1. ป้ายระบุความเป็นเจ้าของที่มุมขวาล่าง (Subtle Pill Badge) พร้อมชื่อแบรนด์และเบอร์โทร
    2. ลายน้ำจางๆ กึ่งกลางภาพ (Diagonal Watermark ความโปร่งแสง ~18%) ป้องกันการครอปรูป
    """
    if not os.path.exists(image_path):
        return image_path

    if not output_path:
        output_path = image_path

    try:
        base_img = Image.open(image_path).convert("RGBA")
        width, height = base_img.size

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        clean_brand = str(brand_name).strip() or "Official"

        # 1. Subtle central diagonal watermark (ลายน้ำจางกึ่งกลาง ป้องกันการขโมยรูป)
        font_size_center = max(24, int(width * 0.045))
        font_center = _get_thai_font(font_size_center)

        wm_text = f"© {clean_brand}"
        txt_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)

        # คำนวณตำแหน่งกึ่งกลาง
        cx = width // 2 - int(width * 0.16)
        cy = height // 2 - int(height * 0.05)
        txt_draw.text((cx, cy), wm_text, fill=(255, 255, 255, 42), font=font_center)

        # หมุนองศา 25 องศา
        rotated_txt = txt_img.rotate(25, resample=Image.BICUBIC)
        overlay = Image.alpha_composite(overlay, rotated_txt)
        draw = ImageDraw.Draw(overlay)

        # 2. Corner Badge (มุมขวาล่าง เรียบหรู ดูเป็นมืออาชีพ)
        font_size_corner = max(14, int(width * 0.026))
        font_corner = _get_thai_font(font_size_corner)

        corner_text = f"© {clean_brand}"
        if phone and str(phone).strip():
            corner_text += f" • {str(phone).strip()}"

        bbox = draw.textbbox((0, 0), corner_text, font=font_corner)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        pad_x = int(width * 0.018)
        pad_y = int(height * 0.012)
        badge_w = tw + pad_x * 2
        badge_h = th + pad_y * 2

        badge_x = width - badge_w - int(width * 0.03)
        badge_y = height - badge_h - int(height * 0.03)

        # พื้นหลังแคปซูลโปร่งแสงสีเข้ม (Dark Slate Translucent)
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=10,
            fill=(15, 23, 42, 175),
            outline=(255, 255, 255, 75),
            width=1
        )
        # ข้อความลายน้ำสีขาวคมชัด
        draw.text((badge_x + pad_x, badge_y + pad_y), corner_text, fill=(255, 255, 255, 240), font=font_corner)

        # ประกอบภาพรวมและบันทึก
        result_img = Image.alpha_composite(base_img, overlay).convert("RGB")
        result_img.save(output_path, "JPEG", quality=95)
        return output_path
    except Exception as e:
        print(f"⚠️ Error applying watermark: {e}")
        return image_path


def craft_visual_prompt_with_gemini(
    topic: str,
    caption: Optional[str] = None,
    brand_name: str = "",
    business_type: str = ""
) -> str:
    """
    ใช้ Gemini แปลงหัวข้อและแคปชั่นภาษาไทยให้กลายเป็น Prompt ภาพถ่ายเชิงพาณิชย์ระดับมืออาชีพ
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    fallback_prompt = f"Professional commercial photography of {business_type or brand_name or 'service'}, modern bright clean lighting, award winning product photo, 4k"

    if not api_key:
        return fallback_prompt

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt_maker = f"""
คุณเป็นผู้เชี่ยวชาญด้าน Creative Art Director และ AI Image Prompt Engineer
กรุณาเปลี่ยนหัวข้อและเนื้อหาแคปชั่นภาษาไทยต่อไปนี้ ให้เป็น "English Prompt" สั้นๆ (ความยาวไม่เกิน 40 คำ) 
สำหรับสร้างภาพถ่ายสต็อกเชิงพาณิชย์ (Commercial Photography) ที่สวยงาม น่าเชื่อถือ และเข้ากับบริบท:

- แบรนด์: {brand_name}
- ประเภทธุรกิจ: {business_type}
- หัวข้อโพสต์: {topic}
- เนื้อหาแคปชั่น: {(caption or '')[:300]}

ข้อกำหนด:
- ต้องเป็นคำอธิบายภาพสไตล์ภาพถ่ายจริง (Photorealistic commercial photography, clean, studio lighting, modern, professional)
- ห้ามมีข้อความตัวหนังสือ หรือตัวอักษรใดๆ ในภาพ (No text, no typography, no watermarks, no logos)
- ตอบเฉพาะข้อความภาษาอังกฤษ 1 ย่อหน้าเท่านั้น ห้ามมีคำอธิบายอื่น
"""
        resp = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt_maker)
        if resp and resp.text:
            cleaned = resp.text.strip().replace('"', '').replace('\n', ' ')
            return cleaned[:300]
    except Exception as e:
        print(f"⚠️ Prompt crafting error: {e}")

    return fallback_prompt


def generate_ai_image(
    topic: str,
    caption: Optional[str] = None,
    brand_name: str = "",
    business_type: str = "",
    phone: Optional[str] = None,
    apply_watermark: bool = True
) -> Dict[str, Any]:
    """
    สร้างรูปภาพด้วย AI ตามหัวข้อ/แคปชั่น และใส่ลายน้ำแบรนด์ป้องกันการคัดลอกอัตโนมัติ
    """
    # 1. เขียน Prompt ภาษาอังกฤษด้วย Gemini
    english_prompt = craft_visual_prompt_with_gemini(
        topic=topic,
        caption=caption,
        brand_name=brand_name,
        business_type=business_type
    )

    # เติมสไตล์เน้นความชัดและตัดตัวหนังสือออก
    final_prompt = f"{english_prompt}, hyperrealistic, sharp focus, 8k resolution, commercial advertising style, no text, no watermark"
    encoded_prompt = urllib.parse.quote(final_prompt)
    seed = int(time.time()) % 100000

    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"

    filename = f"ai_gen_{int(time.time())}.jpg"
    out_path = os.path.join(UPLOADS_DIR, filename)

    try:
        req = urllib.request.Request(
            pollinations_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            image_bytes = response.read()

        if len(image_bytes) < 1000:
            return {"success": False, "error": "รูปภาพที่ได้รับจาก AI ไม่สมบูรณ์"}

        with open(out_path, "wb") as f:
            f.write(image_bytes)

        # 2. ใส่ลายน้ำแบรนด์ป้องกันการคัดลอก (Subtle Watermark)
        if apply_watermark:
            apply_subtle_watermark(
                image_path=out_path,
                brand_name=brand_name or "Official",
                phone=phone,
                output_path=out_path
            )

        return {
            "success": True,
            "image_path": out_path,
            "url": f"/static/uploads/{filename}",
            "prompt_used": english_prompt
        }
    except Exception as e:
        return {"success": False, "error": f"ไม่สามารถสร้างรูปภาพได้: {str(e)}"}
