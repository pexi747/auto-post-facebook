import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from PIL import Image, ImageDraw, ImageFont

def get_thai_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/leelawad.ttf", # Leelawadee
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/angsana.ttc",
        "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/tlwg/Waree-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Waree.ttf",
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
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

def draw_checkmark(draw, x, y, color=(255, 91, 0, 255)):
    """วาดไอคอนเครื่องหมายถูกสวยๆ คมชัด"""
    # วงกลม
    draw.ellipse([(x, y), (x + 22, y + 22)], fill=(255, 240, 230, 255), outline=color, width=2)
    # ขีดถูก
    draw.line([(x + 5, y + 11), (x + 9, y + 16)], fill=color, width=3)
    draw.line([(x + 9, y + 16), (x + 17, y + 7)], fill=color, width=3)

def create_ai_technician_banner(
    photo_path: str = "ai_technician.jpg",
    output_path: str = "fixpack_ai_banner.png",
    headline: str = "เลือกซ่อมได้เอง 3 งานในบ้าน",
    subheadline: str = "ไฟฟ้า • ประปา • ประตูหน้าต่าง • ติดตั้ง",
    price: str = "เหมาจ่าย 1,500.-",
    phone: str = "066-097-1257"
):
    """นำรูปช่าง AI มาใส่ Text และ CI แบรนด์ FixPack ที่ฝั่งซ้ายของภาพอย่างประณีต"""
    if not os.path.exists(photo_path):
        print(f"❌ ไม่พบรูปภาพ: {photo_path}")
        return None

    img = Image.open(photo_path).convert("RGBA").resize((1080, 1080))
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. แถบการ์ดขาวโปร่งแสงฝั่งซ้าย (Modern Frosted Glass effect)
    left_card = [(40, 40), (520, 940)]
    draw.rounded_rectangle(left_card, radius=28, fill=(255, 255, 255, 245))
    # ขอบตกแต่งสีน้ำเงินแบรนด์
    draw.rounded_rectangle(left_card, radius=28, outline=(11, 59, 96, 180), width=3)
    # แถบสีส้มด้านบนของการ์ด
    draw.rounded_rectangle([(40, 40), (520, 52)], radius=6, fill=(255, 91, 0, 255))

    # 2. ใส่โลโก้ FixPack
    if os.path.exists("profile.jpg"):
        logo = Image.open("profile.jpg").convert("RGBA").resize((95, 95))
        overlay.paste(logo, (65, 70))
        font_brand = get_thai_font(34, bold=True)
        font_tagline = get_thai_font(21)
        draw.text((175, 78), "FixPack", font=font_brand, fill=(11, 59, 96, 255))
        draw.text((175, 122), "ซ่อมครบ จบในแพ็กเดียว", font=font_tagline, fill=(255, 91, 0, 255))

    # เส้นคั่น
    draw.line([(65, 185), (495, 185)], fill=(230, 235, 240, 255), width=2)

    # 3. ข้อความหลัก (Headline)
    font_hl = get_thai_font(34, bold=True)
    draw.text((65, 205), headline, font=font_hl, fill=(11, 59, 96, 255))

    font_sub = get_thai_font(22)
    draw.text((65, 255), subheadline, font=font_sub, fill=(100, 115, 130, 255))

    # 4. รายการงานซ่อมยอดฮิต (Bullets)
    bullets = [
        "ซ่อม/เปลี่ยนก๊อกน้ำ สะดืออ่าง ท่อรั่ว",
        "เปลี่ยนปลั๊ก สวิตช์ไฟ หลอดไฟ โคมไฟ",
        "ซ่อมประตู หน้าต่าง บานพับ ลูกบิด",
        "ยาแนวกระเบื้อง อุดรอยร้าว เก็บฝ้า",
        "เจาะ แขวนชั้นวาง รูปภาพ ราวผ้า"
    ]
    font_b = get_thai_font(21, bold=True)
    start_y = 305
    for b in bullets:
        draw.rounded_rectangle([(65, start_y - 4), (495, start_y + 36)], radius=8, fill=(245, 248, 252, 255))
        draw_checkmark(draw, 75, start_y + 4, color=(255, 91, 0, 255))
        draw.text((108, start_y), b, font=font_b, fill=(20, 45, 70, 255))
        start_y += 50

    # 5. Badge ราคา 1,500 บาท
    price_box = [(65, 575), (495, 680)]
    draw.rounded_rectangle(price_box, radius=18, fill=(255, 91, 0, 255))
    font_p_title = get_thai_font(22)
    font_p = get_thai_font(40, bold=True)
    draw.text((90, 590), "ราคาเหมาจ่ายเพียง", font=font_p_title, fill=(255, 255, 255, 255))
    draw.text((90, 620), price, font=font_p, fill=(255, 255, 255, 255))

    # 6. จุดเด่นการบริการ
    features = [
        "ช่างมืออาชีพ ตรงเวลา ไว้ใจได้",
        "ประเมินราคาฟรี ไม่มีบวกเพิ่ม",
        "ดูแลงานซ่อมครบ จบ ไม่ทิ้งงาน"
    ]
    font_feat = get_thai_font(21, bold=True)
    f_y = 705
    for feat in features:
        draw_checkmark(draw, 75, f_y + 2, color=(11, 59, 96, 255))
        draw.text((108, f_y), feat, font=font_feat, fill=(11, 59, 96, 255))
        f_y += 44

    # 7. แถบติดต่อด้านล่างสุด
    bot_bar = [(50, 855), (510, 920)]
    draw.rounded_rectangle(bot_bar, radius=14, fill=(11, 59, 96, 255))
    font_call = get_thai_font(24, bold=True)
    draw.text((70, 872), f"โทร {phone} | ทัก Inbox เพจ", font=font_call, fill=(255, 255, 255, 255))

    # รวมเลเยอร์ภาพ
    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(output_path, "PNG", quality=95)
    print(f"✅ บันทึกรูปภาพแบนเนอร์ช่าง AI สำเร็จ: {output_path}")
    return output_path

def apply_brand_ci_to_uploaded_image(
    image_path: str,
    output_path: str,
    title: str = "ผลงานซ่อมจริงจากช่าง FixPack",
    subtitle: str = "งานเรียบร้อย ปลอดภัย จบไวในแพ็กเกจเดียว",
    price: str = "เหมาจ่าย 1,500.- (3 งาน)",
    phone: str = "066-097-1257"
):
    """
    นำรูปถ่ายหน้างานจริงที่ผู้ใช้อัปโหลด มาใส่กรอบและ Badge CI ของ FixPack ให้เป็นภาพโฆษณาพรีเมียม
    - โทนสีกรมท่า (#0B3B60) และสีส้มสด (#FF5B00)
    - โลโก้ FixPack
    - ป้ายราคาเหมา 1,500.-
    - เบอร์โทรและช่องทางติดต่อ
    """
    from PIL import ImageOps
    if not os.path.exists(image_path):
        print(f"❌ ไม่พบรูปภาพต้นฉบับ: {image_path}")
        return None

    # โหลดและครอบตัดรูปให้เป็น 1080x1080 (Square Cover)
    raw_img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(raw_img, (1080, 1080), method=Image.Resampling.LANCZOS).convert("RGBA")

    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. แถบหัวด้านบน (Top Header Bar)
    top_bar = [(30, 30), (1050, 120)]
    draw.rounded_rectangle(top_bar, radius=20, fill=(11, 59, 96, 235))
    draw.rounded_rectangle([(30, 30), (1050, 38)], radius=4, fill=(255, 91, 0, 255))

    # โลโก้
    if os.path.exists("profile.jpg"):
        logo = Image.open("profile.jpg").convert("RGBA").resize((70, 70))
        overlay.paste(logo, (50, 40))
        font_logo_t = get_thai_font(28, bold=True)
        font_logo_sub = get_thai_font(18)
        draw.text((135, 42), "FixPack", font=font_logo_t, fill=(255, 255, 255, 255))
        draw.text((135, 78), "งานเล็กซ่อมครบ จบในแพ็กเดียว", font=font_logo_sub, fill=(255, 175, 125, 255))

    # Badge มุมขวาบน "การันตีผลงาน"
    draw.rounded_rectangle([(820, 50), (1030, 100)], radius=12, fill=(255, 91, 0, 255))
    font_badge = get_thai_font(20, bold=True)
    draw.text((840, 62), "✓ มาตรฐานช่างมืออาชีพ", font=font_badge, fill=(255, 255, 255, 255))

    # 2. การ์ดรายละเอียดด้านล่าง (Bottom Content Card)
    bottom_card = [(30, 810), (1050, 1050)]
    draw.rounded_rectangle(bottom_card, radius=24, fill=(255, 255, 255, 245))
    draw.rounded_rectangle(bottom_card, radius=24, outline=(11, 59, 96, 200), width=3)

    # แถบสีส้มบนขอบการ์ดล่าง
    draw.rounded_rectangle([(30, 810), (1050, 822)], radius=6, fill=(255, 91, 0, 255))

    # หัวข้อเรื่องที่ซ่อม
    font_title = get_thai_font(32, bold=True)
    font_sub = get_thai_font(20)
    draw.text((60, 835), title[:40], font=font_title, fill=(11, 59, 96, 255))
    draw.text((60, 882), subtitle[:55], font=font_sub, fill=(90, 105, 120, 255))

    # ป้ายราคาฝั่งขวา
    price_tag = [(720, 835), (1020, 935)]
    draw.rounded_rectangle(price_tag, radius=16, fill=(255, 91, 0, 255))
    font_p_title = get_thai_font(18)
    font_p_val = get_thai_font(30, bold=True)
    draw.text((740, 846), "แพ็กเกจสุดคุ้ม", font=font_p_title, fill=(255, 255, 255, 255))
    draw.text((740, 876), price, font=font_p_val, fill=(255, 255, 255, 255))

    # เส้นคั่น
    draw.line([(60, 950), (1020, 950)], fill=(220, 230, 240, 255), width=2)

    # แถบติดต่อด้านล่างสุด
    font_contact = get_thai_font(22, bold=True)
    draw_checkmark(draw, 60, 975, color=(11, 59, 96, 255))
    draw.text((95, 973), "รับประกันงานซ่อม ไม่ทิ้งงาน", font=get_thai_font(20, bold=True), fill=(11, 59, 96, 255))

    contact_box = [(520, 962), (1020, 1030)]
    draw.rounded_rectangle(contact_box, radius=12, fill=(11, 59, 96, 255))
    draw.text((545, 978), f"📞 นัดคิวช่าง: {phone} | ทัก Inbox เพจ", font=font_contact, fill=(255, 255, 255, 255))

    # รวมภาพ
    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(output_path, "JPEG", quality=92)
    print(f"✅ บันทึกรูปตกแต่ง CI สำเร็จ: {output_path}")
    return output_path

if __name__ == "__main__":
    create_ai_technician_banner()
