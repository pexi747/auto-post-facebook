"""
โมดูลสร้างรูปภาพประกอบโพสต์ Facebook อัตโนมัติตามแบรนด์และ CI ของแต่ละเพจ (ขนาด 1080x1080)
รองรับทั้ง 17 เพจแบบ Dynamic:
- ดึงโลโก้จริงของเพจ
- ใช้โทนสีประจำแบรนด์ (Primary & Accent Colors)
- แสดงหัวข้อ จุดเด่นบริการ (Bullets) ราคา และข้อมูลติดต่อ
- รองรับทั้งกรณีมีภาพถ่ายหน้างานจริงที่ผู้ใช้อัปโหลด หรือให้สร้างกราฟิกแบรนด์ใหม่ทั้งหมด
"""
import os
import sys
import requests
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def hex_to_rgb(hex_str: Optional[str], default: Tuple[int, int, int] = (11, 59, 96)) -> Tuple[int, int, int]:
    """แปลงรหัสสี Hex (#0B3B60) เป็น Tuple RGB (11, 59, 96)"""
    if not hex_str:
        return default
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join([c * 2 for c in clean])
    if len(clean) != 6:
        return default
    try:
        return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
    except Exception:
        return default

def get_thai_font(size: int, bold: bool = False):
    """ค้นหา Font ที่รองรับภาษาไทยในระบบอย่างคมชัด"""
    candidates = [
        "C:/Windows/Fonts/leelawad.ttf", # Leelawadee
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/angsana.ttc",
        "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/tlwg/Waree-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Waree.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "arial.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_or_download_brand_logo(page_id: str, picture_url: Optional[str] = None) -> Optional[Image.Image]:
    """ดาวน์โหลดหรือดึงรูปโลโก้ของเพจมาใช้งาน"""
    os.makedirs("static/logos", exist_ok=True)
    local_logo_path = os.path.join("static", "logos", f"logo_{page_id}.jpg")

    if os.path.exists(local_logo_path):
        try:
            return Image.open(local_logo_path).convert("RGBA")
        except Exception:
            pass

    if picture_url and picture_url.startswith("http"):
        try:
            r = requests.get(picture_url, timeout=8)
            if r.status_code == 200:
                with open(local_logo_path, "wb") as f:
                    f.write(r.content)
                return Image.open(local_logo_path).convert("RGBA")
        except Exception as e:
            print(f"⚠️ ไม่สามารถดาวน์โหลดโลโก้ {picture_url}: {e}")

    # Fallback to local profile.jpg
    if os.path.exists("profile.jpg"):
        try:
            return Image.open("profile.jpg").convert("RGBA")
        except Exception:
            pass
    if os.path.exists("static/profile.jpg"):
        try:
            return Image.open("static/profile.jpg").convert("RGBA")
        except Exception:
            pass

    return None

def draw_checkmark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 24, color: Tuple[int, int, int] = (255, 91, 0)):
    """วาดไอคอนเครื่องหมายถูกวงกลมสวยงาม"""
    draw.ellipse([(x, y), (x + size, y + size)], fill=(*color, 45), outline=(*color, 255), width=2)
    # เส้นเช็คถูก
    offset_x = x + size // 4
    offset_y = y + size // 2
    draw.line([(offset_x, offset_y), (offset_x + 4, offset_y + 4)], fill=(*color, 255), width=3)
    draw.line([(offset_x + 4, offset_y + 4), (offset_x + 11, offset_y - 4)], fill=(*color, 255), width=3)

def create_brand_banner(
    page_info: Dict[str, Any],
    headline: Optional[str] = None,
    subheadline: Optional[str] = None,
    bullet_points: Optional[List[str]] = None,
    price_tag: Optional[str] = None,
    background_image_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    สร้างภาพแบนเนอร์โฆษณา Facebook ระดับมืออาชีพ ขนาด 1080x1080 พิกเซล
    ปรับเปลี่ยนองค์ประกอบ โลโก้ สี และเนื้อหาตามแบรนด์ของเพจโดยอัตโนมัติ
    """
    width, height = 1080, 1080
    brand_name = page_info.get("brand_name") or page_info.get("name") or "FixPack"
    tagline = page_info.get("tagline") or "บริการมาตรฐาน ไว้ใจได้"
    business_type = page_info.get("business_type") or page_info.get("category") or "บริการทั่วไป"
    phone = page_info.get("phone") or "066-097-1257"
    page_id = str(page_info.get("id", "default"))
    picture_url = page_info.get("picture_url")

    # ดึงค่าสีประจำแบรนด์
    primary_rgb = hex_to_rgb(page_info.get("primary_color"), default=(11, 59, 96))
    accent_rgb = hex_to_rgb(page_info.get("accent_color"), default=(255, 91, 0))

    if not headline:
        dna = page_info.get("brand_dna", {})
        hooks = dna.get("sample_hooks", [])
        headline = hooks[0] if hooks else f"บริการคุณภาพจาก {brand_name}"

    if not subheadline:
        subheadline = tagline or business_type

    if not bullet_points:
        dna = page_info.get("brand_dna", {})
        bullet_points = dna.get("core_services") or dna.get("selling_points") or [
            "บริการคุณภาพ มาตรฐานระดับมืออาชีพ",
            "ตรงต่อเวลา ไว้ใจได้ ตรวจสอบได้ทุกขั้นตอน",
            "ราคามาตรฐาน คุ้มค่า สบายใจ 100%"
        ]

    if not price_tag:
        price_tag = page_info.get("price_tag") or "ปรึกษา & ประเมินราคาฟรี"

    if not output_path:
        os.makedirs("static/uploads", exist_ok=True)
        import time
        output_path = os.path.join("static", "uploads", f"brand_banner_{page_id}_{int(time.time())}.png")

    # 1. จัดการพื้นหลังภาพ
    has_bg_photo = False
    if background_image_path and os.path.exists(background_image_path):
        try:
            bg = Image.open(background_image_path).convert("RGBA")
            # Center crop to 1080x1080
            bg_w, bg_h = bg.size
            min_dim = min(bg_w, bg_h)
            crop_box = (
                (bg_w - min_dim) // 2,
                (bg_h - min_dim) // 2,
                (bg_w + min_dim) // 2,
                (bg_h + min_dim) // 2
            )
            bg = bg.crop(crop_box).resize((width, height), Image.Resampling.LANCZOS)
            # Overlay มืดเล็กน้อยเพื่อให้ภาพดูมีมิติ
            dim_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 60))
            canvas = Image.alpha_composite(bg, dim_overlay)
            has_bg_photo = True
        except Exception:
            canvas = Image.new("RGBA", (width, height), (*primary_rgb, 255))
    else:
        # สร้าง Gradient Background ตามสีหลักของแบรนด์
        canvas = Image.new("RGBA", (width, height), (*primary_rgb, 255))
        draw_grad = ImageDraw.Draw(canvas)
        pr, pg, pb = primary_rgb
        # ทำการไล่เฉดสีให้ดูโมเดิร์น
        for y in range(height):
            ratio = y / height
            cr = max(0, int(pr * (1.0 - ratio * 0.45)))
            cg = max(0, int(pg * (1.0 - ratio * 0.45)))
            cb = max(0, int(pb * (1.0 - ratio * 0.45)))
            draw_grad.line([(0, y), (width, y)], fill=(cr, cg, cb, 255))

        # วาดวงกลม Accent Glow ด้านขวาบน
        ar, ag, ab = accent_rgb
        glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_draw.ellipse([(700, -150), (1250, 400)], fill=(ar, ag, ab, 35))
        glow_draw.ellipse([(850, -50), (1150, 250)], fill=(ar, ag, ab, 45))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(50))
        canvas = Image.alpha_composite(canvas, glow_layer)

    draw = ImageDraw.Draw(canvas)

    # 2. กรณีมีภาพถ่ายหน้างานจริง: ทำเป็นการ์ดสไตล์ Side Card หรือ Bottom Showcase
    if has_bg_photo:
        card_box = [(40, 40), (540, 940)]
        card_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(card_layer)
        c_draw.rounded_rectangle(card_box, radius=24, fill=(255, 255, 255, 248))
        c_draw.rounded_rectangle(card_box, radius=24, outline=(*primary_rgb, 140), width=2)
        # แถบสี Accent ด้านบนการ์ด
        c_draw.rounded_rectangle([(40, 40), (540, 50)], radius=4, fill=(*accent_rgb, 255))
        canvas = Image.alpha_composite(canvas, card_layer)
        draw = ImageDraw.Draw(canvas)

        # โลโก้แบรนด์
        logo_img = get_or_download_brand_logo(page_id, picture_url)
        if logo_img:
            logo_resized = logo_img.resize((90, 90), Image.Resampling.LANCZOS)
            mask = Image.new('L', (90, 90), 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (90, 90)], radius=16, fill=255)
            canvas.paste(logo_resized, (65, 68), mask)

        font_brand = get_thai_font(30, bold=True)
        font_tagline = get_thai_font(18)
        draw.text((170, 75), brand_name[:18], font=font_brand, fill=(*primary_rgb, 255))
        draw.text((170, 118), tagline[:26], font=font_tagline, fill=(*accent_rgb, 255))

        draw.line([(65, 175), (515, 175)], fill=(230, 235, 240, 255), width=2)

        # พาดหัวและเนื้อหา
        font_hl = get_thai_font(28, bold=True)
        draw.text((65, 195), headline[:24], font=font_hl, fill=(*primary_rgb, 255))

        font_sub = get_thai_font(19)
        draw.text((65, 240), subheadline[:32], font=font_sub, fill=(80, 95, 110, 255))

        # Bullets (แสดง 4 รายการ)
        start_y = 290
        font_b = get_thai_font(18, bold=True)
        for bp in bullet_points[:4]:
            draw.rounded_rectangle([(65, start_y - 3), (515, start_y + 36)], radius=8, fill=(245, 248, 252, 255))
            draw_checkmark(draw, 75, start_y + 4, size=20, color=accent_rgb)
            draw.text((105, start_y + 4), bp[:26], font=font_b, fill=(30, 45, 60, 255))
            start_y += 48

        # Badge ราคา
        draw.rounded_rectangle([(65, start_y + 10), (515, start_y + 68)], radius=14, fill=(*accent_rgb, 255))
        font_p = get_thai_font(24, bold=True)
        draw.text((85, start_y + 22), f"✨ {price_tag}", font=font_p, fill=(255, 255, 255, 255))

        # ข้อมูลติดต่อล่างสุด
        draw.rounded_rectangle([(40, 880), (540, 940)], radius=16, fill=(*primary_rgb, 255))
        font_c = get_thai_font(20, bold=True)
        draw.text((65, 896), f"📞 โทร {phone} | ทัก Inbox เพจ", font=font_c, fill=(255, 255, 255, 255))

        # ป้ายการันตีภาพถ่ายจริงที่มุมขวาบนของภาพถ่าย
        draw.rounded_rectangle([(760, 40), (1040, 95)], radius=28, fill=(0, 0, 0, 180))
        font_verified = get_thai_font(19, bold=True)
        draw.text((785, 55), "📷 ภาพผลงานจริง", font=font_verified, fill=(255, 255, 255, 255))

    else:
        # 3. กรณีไม่มีภาพถ่าย: สร้าง Full Card โฆษณาที่สวยงามสะดุดตา
        logo_img = get_or_download_brand_logo(page_id, picture_url)
        if logo_img:
            logo_resized = logo_img.resize((120, 120), Image.Resampling.LANCZOS)
            mask = Image.new('L', (120, 120), 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (120, 120)], radius=20, fill=255)
            canvas.paste(logo_resized, (60, 50), mask)

        font_brand = get_thai_font(42, bold=True)
        font_tagline = get_thai_font(24)
        draw.text((200, 65), brand_name[:20], font=font_brand, fill=(255, 255, 255, 255))
        draw.text((200, 120), tagline[:32], font=font_tagline, fill=(*accent_rgb, 255))

        # Badge ด้านบนขวา
        draw.rounded_rectangle([(720, 60), (1020, 130)], radius=35, fill=(*accent_rgb, 255))
        font_badge = get_thai_font(24, bold=True)
        draw.text((755, 78), f"⭐ {business_type[:15]}", font=font_badge, fill=(255, 255, 255, 255))

        # กล่องการ์ดเนื้อหาตรงกลาง (White Card สไตล์โมเดิร์น)
        card_box = [(60, 195), (1020, 885)]
        draw.rounded_rectangle(card_box, radius=28, fill=(255, 255, 255, 255))
        draw.rounded_rectangle([(60, 195), (1020, 210)], radius=8, fill=(*accent_rgb, 255))

        # พาดหัวหลัก (Headline)
        font_hl = get_thai_font(46, bold=True)
        draw.text((100, 240), headline[:32], font=font_hl, fill=(*primary_rgb, 255))

        # คำโปรยย่อย (Subheadline)
        font_sub = get_thai_font(28)
        draw.text((100, 310), subheadline[:45], font=font_sub, fill=(90, 105, 120, 255))

        draw.line([(100, 370), (980, 370)], fill=(230, 235, 240, 255), width=2)

        # รายการจุดเด่นบริการ (Bullets)
        start_y = 400
        font_b = get_thai_font(28, bold=True)
        for bp in bullet_points[:5]:
            draw.rounded_rectangle([(100, start_y - 6), (980, start_y + 46)], radius=12, fill=(245, 248, 252, 255))
            draw_checkmark(draw, 115, start_y + 4, size=26, color=accent_rgb)
            draw.text((155, start_y), bp[:38], font=font_b, fill=(25, 45, 65, 255))
            start_y += 66

        # แถบราคาโปรโมชั่น
        price_box = [(100, 775), (980, 855)]
        draw.rounded_rectangle(price_box, radius=20, fill=(*accent_rgb, 255))
        font_price = get_thai_font(38, bold=True)
        draw.text((130, 792), f"📌 {price_tag}", font=font_price, fill=(255, 255, 255, 255))
        draw.text((620, 804), f"({brand_name} ดูแลทุกขั้นตอน)", font=get_thai_font(22), fill=(255, 240, 220, 255))

        # แถบ Footer ล่างสุด
        footer_box = [(0, 930), (width, height)]
        draw.rectangle(footer_box, fill=(*primary_rgb, 255))
        font_footer = get_thai_font(28, bold=True)
        draw.text((80, 965), f"📞 โทร: {phone}", font=font_footer, fill=(255, 255, 255, 255))
        draw.text((560, 965), f"💬 ทักแชท Inbox เพจ {brand_name}", font=font_footer, fill=(*accent_rgb, 255))

    canvas = canvas.convert("RGB")
    canvas.save(output_path, "PNG", quality=95)
    print(f"✅ สร้างแบนเนอร์แบรนด์ '{brand_name}' สำเร็จ: {output_path}")
    return output_path

# Alias for backwards-compatibility
def create_fixpack_banner(*args, **kwargs):
    page_info = {
        "id": "764713456731551",
        "brand_name": "FixPack",
        "tagline": "งานเล็กซ่อมครบ จบในแพ็กเดียว",
        "business_type": "บริการซ่อมบ้านครบวงจร",
        "primary_color": "#0B3B60",
        "accent_color": "#FF5B00",
        "phone": "066-097-1257",
        "price_tag": "เหมาจ่าย 1,500.- (3 งาน)"
    }
    return create_brand_banner(page_info=page_info, *args, **kwargs)

if __name__ == "__main__":
    test_page = {
        "id": "692403317575521",
        "brand_name": "สำรับคุณแม่",
        "tagline": "ความอร่อยจากครัวคุณแม่ส่งตรงถึงบ้านคุณ",
        "business_type": "อาหารจัดเลี้ยง & เดลิเวอรี่",
        "primary_color": "#8B4513",
        "accent_color": "#FF8C00",
        "phone": "099-265-6361",
        "price_tag": "ส่งฟรีไม่มีขั้นต่ำ (สยาม-สีลม-เพลินจิต)"
    }
    create_brand_banner(test_page, headline="เมนูเด็ดรสมือแม่ พร้อมส่งถึงที่!", output_path="test_banner.png")
