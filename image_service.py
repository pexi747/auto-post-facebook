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


def resolve_page_logo_path(
    page_id: Optional[str] = None,
    picture_url: Optional[str] = None
) -> Optional[str]:
    """
    ค้นหาหรือดาวน์โหลดไฟล์โลโก้ของเพจมาเก็บไว้ที่ static/logos/logo_{page_id}.jpg
    เพื่อให้พร้อมนำไปทำเป็นลายน้ำโปร่งแสงบางๆ สวยงาม
    """
    logos_dir = os.path.join("static", "logos")
    os.makedirs(logos_dir, exist_ok=True)

    if page_id:
        local_jpg = os.path.join(logos_dir, f"logo_{page_id}.jpg")
        if os.path.exists(local_jpg) and os.path.getsize(local_jpg) > 100:
            return local_jpg
        local_png = os.path.join(logos_dir, f"logo_{page_id}.png")
        if os.path.exists(local_png) and os.path.getsize(local_png) > 100:
            return local_png

    # ถ้ามี picture_url ที่เป็นเว็บ ให้ดาวน์โหลดมาแคชไว้ในเครื่อง
    if picture_url and str(picture_url).startswith("http"):
        dest_filename = f"logo_{page_id or int(time.time())}.jpg"
        dest_path = os.path.join(logos_dir, dest_filename)
        try:
            req = urllib.request.Request(picture_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp, open(dest_path, "wb") as f:
                f.write(resp.read())
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100:
                return dest_path
        except Exception as e:
            pass

    # Fallbacks
    for fallback in ["static/profile.jpg", "static/logos/logo_764713456731551.jpg"]:
        if os.path.exists(fallback):
            return fallback

    return None


def create_circular_logo(logo_path: str, size: int) -> Image.Image:
    """แปลงรูปภาพโลโก้ให้เป็นวงกลมขอบมนเรียบเนียน พร้อม Alpha Channel แบบ Supersampling"""
    from PIL import ImageOps
    img = Image.open(logo_path).convert("RGBA")
    img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
    
    mask_scale = 4
    mask = Image.new("L", (size * mask_scale, size * mask_scale), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size * mask_scale - 1, size * mask_scale - 1), fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    
    circle_logo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circle_logo.paste(img, (0, 0), mask=mask)
    return circle_logo


def apply_transparency(img: Image.Image, opacity: float) -> Image.Image:
    """ปรับความโปร่งแสง (Opacity 0.0 - 1.0) ของรูปภาพ RGBA"""
    r, g, b, a = img.split()
    a = a.point(lambda p: int(p * opacity))
    return Image.merge("RGBA", (r, g, b, a))


def apply_subtle_watermark(
    image_path: str,
    brand_name: str = "Brand",
    phone: Optional[str] = None,
    page_id: Optional[str] = None,
    picture_url: Optional[str] = None,
    logo_path: Optional[str] = None,
    output_path: Optional[str] = None,
    include_center_mark: bool = True
) -> str:
    """
    ใส่ลายน้ำแบรนด์ด้วยรูปโลโก้จริงแบบโปร่งแสงบางๆ สวยงามระดับมืออาชีพ (Frosted Glass & Translucent Logo):
    1. ป้ายแคปซูล Frosted Glass ที่มุมขวาล่าง: โลโก้วงกลมโปร่งแสง + ชื่อแบรนด์และเบอร์โทร
    2. โลโก้วงกลมโปร่งแสงบางเฉียบ (~14% opacity) กึ่งกลางภาพ ป้องกันการขโมยรูปหรือตัดครอป
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

        # ค้นหาไฟล์โลโก้
        resolved_logo = logo_path or resolve_page_logo_path(page_id=page_id, picture_url=picture_url)

        # 1. ลายน้ำโลโก้โปร่งแสงบางๆ กึ่งกลางภาพ (Central Translucent Logo Mark, Opacity ~14%)
        if include_center_mark and resolved_logo and os.path.exists(resolved_logo):
            try:
                center_size = int(min(width, height) * 0.30)
                center_logo = create_circular_logo(resolved_logo, center_size)
                center_trans = apply_transparency(center_logo, 0.14)
                cx = (width - center_size) // 2
                cy = (height - center_size) // 2
                overlay.paste(center_trans, (cx, cy), center_trans)
            except Exception as e:
                pass

        # 2. ป้ายแคปซูลแก้วโปร่งแสงที่มุมขวาล่าง (Frosted Glass Pill Badge)
        margin_x = int(width * 0.035)
        margin_y = int(height * 0.035)
        pill_logo_size = max(34, int(min(width, height) * 0.065))
        
        font_size = max(13, int(pill_logo_size * 0.42))
        font = _get_thai_font(font_size)

        label_text = f"© {clean_brand}"
        if phone and str(phone).strip():
            label_text += f" • {str(phone).strip()}"

        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pad_h = int(pill_logo_size * 0.22)
        pad_w = int(pill_logo_size * 0.35)

        has_logo = resolved_logo and os.path.exists(resolved_logo)
        if has_logo:
            pill_w = pill_logo_size + text_w + pad_w * 3
            pill_h = pill_logo_size + pad_h * 2
        else:
            pill_w = text_w + pad_w * 2
            pill_h = text_h + pad_h * 2

        pill_x = width - margin_x - pill_w
        pill_y = height - margin_y - pill_h

        # วาดพื้นหลังแคปซูล Frosted Glass แบบบางใส (~35% opacity)
        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=pill_h // 2,
            fill=(10, 15, 25, 90),
            outline=(255, 255, 255, 60),
            width=1
        )

        if has_logo:
            try:
                circ_logo = create_circular_logo(resolved_logo, pill_logo_size)
                logo_trans = apply_transparency(circ_logo, 0.70)
                lx = pill_x + pad_w
                ly = pill_y + pad_h
                overlay.paste(logo_trans, (lx, ly), logo_trans)
                
                # เส้นวงแหวนรอบโลโก้สีขาวบางๆ
                draw.ellipse(
                    [lx - 1, ly - 1, lx + pill_logo_size + 1, ly + pill_logo_size + 1],
                    outline=(255, 255, 255, 80),
                    width=1
                )
                text_x = pill_x + pad_w + pill_logo_size + int(pad_w * 0.8)
                text_y = pill_y + (pill_h - text_h) // 2 - 1
            except Exception as e:
                text_x = pill_x + pad_w
                text_y = pill_y + (pill_h - text_h) // 2
        else:
            text_x = pill_x + pad_w
            text_y = pill_y + (pill_h - text_h) // 2

        # วาดข้อความสีขาวคมชัด โปร่งแสงนุ่มนวล
        draw.text((text_x, text_y), label_text, fill=(255, 255, 255, 225), font=font)

        # รวมเลเยอร์ภาพและบันทึก
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
    page_id: Optional[str] = None,
    picture_url: Optional[str] = None,
    logo_path: Optional[str] = None,
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
                page_id=page_id,
                picture_url=picture_url,
                logo_path=logo_path,
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
