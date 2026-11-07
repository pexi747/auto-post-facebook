"""
โมดูลสร้างรูปภาพประกอบโพสต์ Facebook ตาม CI แบรนด์ FixPack (ขนาด 1080x1080)
CI แบรนด์:
- สีหลัก (Primary): Deep Navy Blue (#0B3B60 / #0B2540)
- สีเด่น (Accent): Vibrant Orange (#FF5B00)
- สีข้อความ/พื้นหลัง: ขาว (#FFFFFF), เทาอ่อน (#F4F6F9)
"""
import os
import sys

# รองรับ UTF-8 สำหรับ Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from PIL import Image, ImageDraw, ImageFont

# ค้นหา Font ที่รองรับภาษาไทยใน Windows
def get_thai_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/leelawad.ttf", # Leelawadee
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/angsana.ttc",
        "arial.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_fixpack_banner(
    headline: str = "เลือกซ่อมได้เอง 3 งานในบ้าน",
    subheadline: str = "ก๊อกน้ำ ไฟฟ้า ประตู หน้าต่าง ซ่อมครบในแพ็กเดียว",
    bullet_points: list = None,
    price_tag: str = "ราคาเหมาเพียง 1,500.-",
    output_path: str = "fixpack_post_banner.png",
    background_image_path: str = None
) -> str:
    """สร้างรูปภาพโปรโมท Facebook สไตล์ CI FixPack ขนาด 1080x1080 พิกเซล"""
    width, height = 1080, 1080
    
    # 1. สร้าง Canvas พื้นหลัง
    if background_image_path and os.path.exists(background_image_path):
        bg = Image.open(background_image_path).convert("RGBA").resize((width, height))
        # ใส่ Overlay สีน้ำเงินเข้มโปร่งแสง เพื่อให้ตัวหนังสืออ่านชัดเจน
        overlay = Image.new("RGBA", (width, height), (11, 59, 96, 210))
        img = Image.alpha_composite(bg, overlay)
    else:
        # พื้นหลัง Gradient หรือ Solid Navy Blue (#0B3B60)
        img = Image.new("RGBA", (width, height), (11, 59, 96, 255))
        draw_temp = ImageDraw.Draw(img)
        # ทำแถบเฉดสี
        for y in range(height):
            r = int(11 + (15 - 11) * (y / height))
            g = int(59 + (37 - 59) * (y / height))
            b = int(96 + (64 - 96) * (y / height))
            draw_temp.line([(0, y), (width, y)], fill=(r, g, b, 255))

    draw = ImageDraw.Draw(img)

    # 2. ใส่ Logo FixPack ด้านบนซ้าย
    logo_path = "profile.jpg"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA").resize((130, 130))
        # ทำกรอบมุมโค้งสีขาวให้โลโก้
        mask = Image.new('L', (130, 130), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (130, 130)], radius=20, fill=255)
        img.paste(logo, (60, 50), mask)
    
    # แบรนด์เนมด้านบน
    font_brand = get_thai_font(42, bold=True)
    font_brand_sub = get_thai_font(26)
    draw.text((210, 65), "FixPack", font=font_brand, fill=(255, 255, 255, 255))
    draw.text((210, 120), "งานเล็กซ่อมครบ จบในแพ็กเดียว", font=font_brand_sub, fill=(255, 165, 0, 255))

    # Badge การันตี / สัญลักษณ์ด้านบนขวา
    badge_box = [(720, 60), (1020, 140)]
    draw.rounded_rectangle(badge_box, radius=40, fill=(255, 91, 0, 255))
    font_badge = get_thai_font(28, bold=True)
    draw.text((755, 80), "🛠️ ช่างมืออาชีพ", font=font_badge, fill=(255, 255, 255, 255))

    # 3. กล่องการ์ดเนื้อหาหลักตรงกลาง (White Card สไตล์โมเดิร์น)
    card_box = [(60, 210), (1020, 890)]
    draw.rounded_rectangle(card_box, radius=28, fill=(255, 255, 255, 250))

    # เส้นตกแต่งแถบสีส้มด้านบนของการ์ด
    draw.rounded_rectangle([(60, 210), (1020, 226)], radius=8, fill=(255, 91, 0, 255))

    # พาดหัวหลัก (Headline)
    font_headline = get_thai_font(52, bold=True)
    draw.text((100, 260), headline, font=font_headline, fill=(11, 59, 96, 255))

    # คำโปรยย่อย (Subheadline)
    font_sub = get_thai_font(32)
    draw.text((100, 335), subheadline, font=font_sub, fill=(90, 105, 120, 255))

    # เส้นแบ่งเบาๆ
    draw.line([(100, 400), (980, 400)], fill=(230, 235, 240, 255), width=2)

    # Bullet Points (ตัวอย่างงานที่เลือกได้)
    if not bullet_points:
        bullet_points = [
            "🔧 ซ่อม/เปลี่ยนก๊อกน้ำ สะดืออ่าง ท่อน้ำรั่วซึม",
            "⚡ เปลี่ยนปลั๊ก สวิตช์ไฟ หลอดไฟ โคมไฟ",
            "🚪 ซ่อมประตู หน้าต่าง บานพับ ลูกบิดฝืด",
            "🧱 อุดรอยร้าว ยาแนวกระเบื้อง ซ่อมงานฝ้า",
            "🖼️ เจาะ แขวน ติดตั้งชั้นวาง ราวผ้า รูปภาพ"
        ]

    font_bullet = get_thai_font(30, bold=True)
    start_y = 430
    for bp in bullet_points[:5]:
        # วาดพื้นหลังแถบข้อความอ่อนๆ
        draw.rounded_rectangle([(100, start_y - 6), (980, start_y + 44)], radius=12, fill=(245, 248, 252, 255))
        draw.text((120, start_y), bp, font=font_bullet, fill=(20, 45, 70, 255))
        start_y += 66

    # 4. แถบราคาโปรโมชั่น (Price Tag Banner)
    price_box = [(100, 780), (980, 865)]
    draw.rounded_rectangle(price_box, radius=20, fill=(255, 91, 0, 255))
    font_price = get_thai_font(42, bold=True)
    font_price_sub = get_thai_font(24)
    draw.text((130, 795), f"📌 {price_tag}", font=font_price, fill=(255, 255, 255, 255))
    draw.text((620, 810), "(ประเมินราคาฟรี ไม่ทิ้งงาน)", font=font_price_sub, fill=(255, 240, 220, 255))

    # 5. แถบ Footer ล่างสุด (Call to Action & ติดต่อ)
    footer_box = [(0, 930), (width, height)]
    draw.rectangle(footer_box, fill=(6, 24, 43, 255))
    font_footer = get_thai_font(30, bold=True)
    draw.text((80, 970), "📞 โทร: 066-097-1257", font=font_footer, fill=(255, 255, 255, 255))
    draw.text((580, 970), "💬 ทักแชท Inbox เพจ FixPack ได้ทันที", font=font_footer, fill=(255, 165, 0, 255))

    # บันทึกไฟล์ภาพ
    img = img.convert("RGB")
    img.save(output_path, "PNG", quality=95)
    print(f"✅ สร้างรูปภาพตาม CI แบรนด์สำเร็จ: {output_path}")
    return output_path

if __name__ == "__main__":
    create_fixpack_banner()
