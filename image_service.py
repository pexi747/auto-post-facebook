import ai_client_resolver
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

# Diff / Replacement for image_service.py:


# คลังข้อมูลธีมภาพถ่าย 25 วันสำคัญไทย (Authentic Cultural Visual Themes)
THAI_HOLIDAYS_THEMES_TABLE = [
    {
        "id": "loy_krathong", "name": "วันลอยกระทง",
        "keywords": ["ลอยกระทง", "กระทง", "วันเพ็ญเดือนสิบสอง", "loy krathong"],
        "visual_theme": "Illuminated banana leaf Krathong with candle and fresh lotus flowers floating peacefully on calm river under luminous full moon, ethereal golden reflections, traditional Thai celebration photography"
    },
    {
        "id": "fathers_day", "name": "วันพ่อแห่งชาติ / วันชาติ",
        "keywords": ["วันพ่อ", "วันพ่อแห่งชาติ", "วันชาติ", "5 ธันวา", "๕ ธันวา", "รัชกาลที่ 9", "รัชกาลที่ ๙", "fathers day"],
        "visual_theme": "Respectful tribute on Thai Father's Day, golden yellow Ratchaphruek blossoms, warm morning sunlight, peaceful Thai reverence atmosphere, elegant traditional composition"
    },
    {
        "id": "mothers_day", "name": "วันแม่แห่งชาติ",
        "keywords": ["วันแม่", "วันแม่แห่งชาติ", "12 สิงหา", "๑๒ สิงหา", "mothers day"],
        "visual_theme": "Warm heartfelt Thai Mother's Day scene, delicate fragrant white Jasmine garland Malai on ornate silver tray, gentle soft morning sunlight, symbol of maternal love"
    },
    {
        "id": "songkran", "name": "เทศกาลสงกรานต์",
        "keywords": ["สงกรานต์", "วันสงกรานต์", "ปีใหม่ไทย", "songkran"],
        "visual_theme": "Traditional Thai Songkran festival, splashing clean sparkling water drops in joyful celebration, floral jasmine scented water in traditional brass bowl, warm festive sunlight"
    },
    {
        "id": "visakha_bucha", "name": "วันวิสาขบูชา",
        "keywords": ["วิสาขบูชา", "วิสาขะ", "visakha bucha"],
        "visual_theme": "Serene Thai Buddhist temple courtyard at twilight, gentle candlelight procession Wian Tian, glowing lotus flowers, peaceful spiritual ambiance, warm golden temple reflections"
    },
    {
        "id": "makha_bucha", "name": "วันมาฆบูชา",
        "keywords": ["มาฆบูชา", "มาฆะ", "makha bucha"],
        "visual_theme": "Spiritual Makha Bucha candlelight ceremony at tranquil golden Thai pagoda, soft glowing candles held in prayer, peaceful evening meditation atmosphere, serene Buddhist spirituality"
    },
    {
        "id": "asalha_bucha", "name": "วันอาสาฬหบูชา",
        "keywords": ["อาสาฬหบูชา", "อาสาฬหะ", "asalha bucha"],
        "visual_theme": "Serene Buddhist Asalha Bucha reflection, golden Dharma wheel emblem, fresh lotus offerings at ancient tranquil Thai temple, calm morning natural light"
    },
    {
        "id": "khao_phansa", "name": "วันเข้าพรรษา",
        "keywords": ["เข้าพรรษา", "khao phansa", "buddhist lent"],
        "visual_theme": "Magnificent intricately carved Thai Khao Phansa Buddhist Lent beeswax candle, glowing gently in traditional temple sanctuary, peaceful spiritual atmosphere"
    },
    {
        "id": "awk_phansa", "name": "วันออกพรรษา",
        "keywords": ["ออกพรรษา", "awk phansa"],
        "visual_theme": "Glowing illuminated boat procession on Thai river during Awk Phansa festival, colorful lanterns reflecting on calm water under moonlit evening sky"
    },
    {
        "id": "new_year", "name": "วันขึ้นปีใหม่",
        "keywords": ["วันขึ้นปีใหม่", "ปีใหม่", "สวัสดีปีใหม่", "happy new year", "new year"],
        "visual_theme": "Joyful modern celebratory New Year scene, magnificent warm golden fireworks illuminating night sky, festive celebration photography, elegant bokeh lights"
    },
    {
        "id": "christmas", "name": "วันคริสต์มาส",
        "keywords": ["คริสต์มาส", "คริสต์มาสอีฟ", "christmas", "xmas"],
        "visual_theme": "Cozy festive Christmas scene, sparkling warm golden fairy lights, beautifully decorated green pine tree, elegant celebratory gifts, cinematic cozy warm lighting"
    },
    {
        "id": "chinese_new_year", "name": "เทศกาลตรุษจีน",
        "keywords": ["ตรุษจีน", "วันตรุษจีน", "chinese new year", "cny"],
        "visual_theme": "Vibrant festive Chinese New Year celebration, red silk lanterns, blooming pink peach blossoms, lucky golden mandarins, auspicious holiday celebration photography"
    },
    {
        "id": "children_day", "name": "วันเด็กแห่งชาติ",
        "keywords": ["วันเด็ก", "วันเด็กแห่งชาติ", "childrens day"],
        "visual_theme": "Cheerful smiling Thai children in bright happy creative environment, colorful balloons and toys, joyful playful atmosphere, natural warm sunlight"
    },
    {
        "id": "teachers_day", "name": "วันครู",
        "keywords": ["วันครู", "วันครูแห่งชาติ", "teachers day"],
        "visual_theme": "Respectful Thai Teachers Day tribute, traditional floral phan wai kru flower tray, open classic books under gentle morning library sunlight, honoring education"
    },
    {
        "id": "chulalongkorn_day", "name": "วันปิยมหาราช",
        "keywords": ["ปิยมหาราช", "23 ตุลา", "๒๓ ตุลา", "รัชกาลที่ 5", "รัชกาลที่ ๕", "chulalongkorn"],
        "visual_theme": "Solemn commemorative tribute with pink and white roses, dignified memorial tribute composition, gentle soft morning light, peaceful Thai historical remembrance"
    },
    {
        "id": "navamindra_day", "name": "วันนวมินทรมหาราช",
        "keywords": ["นวมินทร", "นวมินทรมหาราช", "13 ตุลา", "๑๓ ตุลา", "วันคล้ายวันสวรรคต ร.9"],
        "visual_theme": "Solemn and respectful Thai tribute, golden yellow Dok Dao Ruang marigold blossoms, soft warm morning light, profound national remembrance"
    },
    {
        "id": "chakri_day", "name": "วันจักรี",
        "keywords": ["วันจักรี", "จักรี", "6 เมษา", "๖ เมษา", "chakri memorial"],
        "visual_theme": "Royal Chakri remembrance tribute, auspicious golden ornamentation, traditional Thai royal tribute flowers, dignified peaceful heritage photography"
    },
    {
        "id": "constitution_day", "name": "วันรัฐธรรมนูญ",
        "keywords": ["วันรัฐธรรมนูญ", "รัฐธรรมนูญ", "10 ธันวา", "๑๐ ธันวา", "constitution day"],
        "visual_theme": "Thai Constitution remembrance tribute, golden constitutional tray phan decoration, dignified respectful national celebration, clean bright architectural lighting"
    },
    {
        "id": "coronation_day", "name": "วันฉัตรมงคล",
        "keywords": ["ฉัตรมงคล", "4 พฤษภา", "๔ พฤษภา", "coronation day"],
        "visual_theme": "Dignified coronation tribute scene, royal yellow and golden Thai flowers, respectful celebratory ambiance, elegant traditional composition"
    },
    {
        "id": "royal_ploughing", "name": "วันพืชมงคล",
        "keywords": ["พืชมงคล", "จรดพระนังคัล", "royal ploughing"],
        "visual_theme": "Lush vibrant green fertile rice paddies under morning sun, traditional Thai agricultural ceremony celebration, golden ripe rice ears, natural vitality"
    },
    {
        "id": "valentines_day", "name": "วันวาเลนไทน์",
        "keywords": ["วาเลนไทน์", "valentine"],
        "visual_theme": "Warm romantic Valentine celebration, elegant fresh velvet red roses, delicate heart motif, soft bokeh romantic ambient photography, clean modern aesthetic"
    },
    {
        "id": "womens_day", "name": "วันสตรีสากล",
        "keywords": ["สตรีสากล", "วันสตรี", "womens day", "iwd"],
        "visual_theme": "Inspiring celebration of International Women's Day, purple ribbons and blooming purple orchids, graceful radiant morning lighting, empowering atmosphere"
    },
    {
        "id": "labour_day", "name": "วันแรงงาน",
        "keywords": ["วันแรงงาน", "วันแรงงานแห่งชาติ", "1 พฤษภา", "๑ พฤษภา", "labour day", "labor day"],
        "visual_theme": "Dignified celebration of dedication and craftsmanship, warm golden sunrise, honest inspiring composition, celebrating hard work and community"
    },
    {
        "id": "thai_language_day", "name": "วันภาษาไทยแห่งชาติ",
        "keywords": ["ภาษาไทยแห่งชาติ", "วันภาษาไทย", "29 กรกฎา", "๒๙ กรกฎา"],
        "visual_theme": "Traditional Thai palm leaf manuscript, vintage Thai script calligraphy, serene wooden desk with fresh lotus blossom, warm library morning light"
    },
    {
        "id": "environment_day", "name": "วันสิ่งแวดล้อม",
        "keywords": ["สิ่งแวดล้อม", "วันสิ่งแวดล้อมไทย", "วันสิ่งแวดล้อมโลก", "environment day"],
        "visual_theme": "Lush vibrant green tropical Thai rainforest canopy, glistening dew drops on fresh emerald leaves, crystal clear pristine nature, bright morning sunlight"
    }
]

def detect_holiday_theme(topic: str, caption: str = "") -> Optional[Dict[str, Any]]:
    """
    ตรวจจับหัวข้อวันสำคัญและเทศกาลของไทย เพื่อแปลงเป็นแนวคิดรูปภาพเชิงวัฒนธรรมที่แท้จริง
    โดยไม่ปะปนกับอุปกรณ์ช่างหรืองานซ่อม
    """
    text = f"{topic or ''} {caption or ''}".lower()
    
    # 1. Match from predefined 25 Thai holidays table
    for h in THAI_HOLIDAYS_THEMES_TABLE:
        for kw in h["keywords"]:
            if kw.lower() in text:
                return {
                    "holiday_id": h["id"],
                    "holiday_name": h["name"],
                    "visual_theme": h["visual_theme"],
                    "is_holiday": True
                }

    # 2. Check thai_holidays registry if available
    try:
        import thai_holidays
        for event in thai_holidays.HOLIDAYS_DATABASE:
            if event.get("name") and event["name"].lower() in text:
                return {
                    "holiday_id": event.get("id"),
                    "holiday_name": event.get("name"),
                    "visual_theme": event.get("visual_theme"),
                    "is_holiday": True
                }
    except Exception:
        pass

    return None

def craft_visual_prompt_with_gemini(
    topic: str,
    caption: Optional[str] = None,
    brand_name: str = "",
    business_type: str = "",
    user_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    สร้าง Prompt ภาษาอังกฤษสำหรับ AI Image Generator:
    - ถ้าเป็นวันสำคัญ: บังคับตัด business_type ออก 100% และใช้ Visual Theme วัฒนธรรมแท้จริง
    - ถ้าเป็นโพสต์ทั่วไป: ใช้ AI สร้าง Prompt เชิงพาณิชย์ตาม Brand DNA
    """
    holiday = detect_holiday_theme(topic=topic, caption=caption or "")

    if holiday:
        # วันสำคัญ: ห้ามใส่ business_type และ Fallback ต้องเป็นธีมวันสำคัญเท่านั้น!
        fallback_prompt = holiday["visual_theme"]

        prompt_maker = f"""
You are an expert Creative Art Director and AI Image Prompt Engineer.
Create a short, culturally authentic English prompt (max 35 words) for stock photography of the Thai holiday: "{holiday['holiday_name']}".

Context Theme: {holiday['visual_theme']}
Additional details: {(caption or '')[:180]}

STRICT REQUIREMENTS:
- Depict ONLY the authentic cultural celebration, traditional symbols, warm festive lighting, and natural/temple atmosphere.
- ABSOLUTELY NO handyman tools, repair work, commercial products, or business props.
- ABSOLUTELY NO text, letters, watermarks, or logos in the image.
- Return ONLY 1 concise English paragraph without explanations.
"""
        try:
            ai_res = ai_client_resolver.call_ai_completion(prompt_maker, user_config=user_config)
            if ai_res and len(ai_res.strip()) > 10:
                cleaned = ai_res.strip().replace('"', '').replace('\n', ' ')
                return cleaned[:300]
        except Exception as e:
            print(f"⚠️ Holiday prompt crafting error: {e}")

        return fallback_prompt

    # โพสต์ธุรกิจปกติ
    fallback_prompt = f"Professional commercial photography of {business_type or brand_name or 'service'}, modern bright clean lighting, award winning product photo, 4k"

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
    try:
        ai_res = ai_client_resolver.call_ai_completion(prompt_maker, user_config=user_config)
        if ai_res and len(ai_res.strip()) > 10:
            cleaned = ai_res.strip().replace('"', '').replace('\n', ' ')
            return cleaned[:300]
    except Exception as e:
        print(f"⚠️ Prompt crafting error: {e}")

    return fallback_prompt

def craft_visual_prompt_from_reference_image(
    image_path: str,
    topic: str,
    brand_name: str = "",
    user_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    วิเคราะห์ภาพตัวอย่าง (Reference Image) เพื่อถอดแบบสไตล์ภาพ แสง สี โทน อารมณ์ และมุมกล้อง
    แล้วสร้าง English Prompt คุณภาพสูงสำหรับสร้างภาพใหม่ในหัวข้อ topic ที่กำหนด
    """
    fallback_prompt = f"Professional commercial photography of {topic}, {brand_name}, modern clean studio lighting, award winning product photo, 8k, photorealistic"
    
    if not os.path.exists(image_path):
        return fallback_prompt

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if user_config and user_config.get("api_key") and user_config.get("provider") == "gemini":
        api_key = user_config.get("api_key")

    prompt_maker = f"""You are an elite Commercial Art Director and AI Image Prompt Engineer.
Look at this reference image carefully and analyze its artistic aesthetic:
1. Photography lighting (e.g. dramatic shadows, bright softbox studio, warm golden hour, natural cinematic ambient)
2. Color grading & palette (e.g. warm earth tones, vibrant saturated, cool moody, minimalist pastel)
3. Composition, camera depth of field, framing, perspective, and background texture.

Now, write a short, highly-detailed English prompt (maximum 40 words) for a BRAND NEW commercial photograph about:
- Subject / Topic: "{topic}"
- Brand context: "{brand_name}"

STRICT REQUIREMENTS:
- The new image must mimic the EXACT photographic style, lighting atmosphere, color palette, and premium aesthetic of this reference image.
- Do NOT describe what is currently in the reference image. Describe ONLY the new subject matching the topic.
- High-end commercial advertising photography style, sharp focus, 8k, hyperrealistic.
- ABSOLUTELY NO text, typography, letters, logos, or watermarks.
- Return ONLY 1 concise English paragraph without quotes or extra explanation.
"""

    if api_key:
        try:
            from PIL import Image
            from google import genai
            client = genai.Client(api_key=api_key)
            img = Image.open(image_path)
            
            models_to_try = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-1.5-flash"]
            for m in models_to_try:
                try:
                    resp = client.models.generate_content(model=m, contents=[prompt_maker, img])
                    if resp and resp.text:
                        cleaned = resp.text.strip().replace('"', '').replace('\n', ' ')
                        cleaned = re.sub(r'^(Prompt:\s*|Here is\s*.*:\s*)', '', cleaned, flags=re.IGNORECASE).strip()
                        if len(cleaned) > 15:
                            return cleaned[:300]
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ Reference prompt analysis error: {e}")

    try:
        text_prompt = f"""You are an expert Commercial Art Director.
Generate a high quality English commercial photography prompt (max 35 words) for Facebook advertising:
Topic: {topic}
Brand: {brand_name}
Style: Photorealistic, cinematic lighting, modern commercial advertising aesthetic, sharp focus, 8k resolution, no text, no watermark.
Return only the prompt paragraph."""
        ai_res = ai_client_resolver.call_ai_completion(text_prompt, user_config=user_config)
        if ai_res and len(ai_res.strip()) > 10:
            return ai_res.strip().replace('"', '').replace('\n', ' ')[:300]
    except Exception:
        pass

    return fallback_prompt

def generate_ai_image(
    topic: str = "",
    caption: Optional[str] = None,
    brand_name: str = "",
    business_type: str = "",
    phone: Optional[str] = None,
    page_id: Optional[str] = None,
    picture_url: Optional[str] = None,
    logo_path: Optional[str] = None,
    apply_watermark: bool = True,
    user_config: Optional[Dict[str, Any]] = None,
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    สร้างรูปภาพด้วย AI พร้อมแยกแยะวันสำคัญกับโพสต์ธุรกิจอย่างแม่นยำ (หรือใช้ Custom Prompt ที่ระบุ)
    """
    holiday = detect_holiday_theme(topic=topic, caption=caption or "")

    if holiday:
        effective_biz = ""
        style_tags = "hyperrealistic, sharp focus, 8k resolution, authentic cultural photography, soft natural lighting, no text, no watermark"
    else:
        effective_biz = business_type
        style_tags = "hyperrealistic, sharp focus, 8k resolution, commercial advertising style, no text, no watermark"

    if prompt and prompt.strip():
        english_prompt = prompt.strip()
    else:
        english_prompt = craft_visual_prompt_with_gemini(
            topic=topic,
            caption=caption,
            brand_name=brand_name,
            business_type=effective_biz,
            user_config=user_config
        )

    final_prompt = f"{english_prompt}, {style_tags}"
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
