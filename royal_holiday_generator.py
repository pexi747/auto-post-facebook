"""
โมดูลสร้างภาพกราฟิกวันสำคัญและวันพระราชพิธีแบบเป็นทางการ (Royal & Memorial Holiday Poster Generator)
สไตล์สมพระเกียรติ สวยงาม ประณีต ตามแบบฉบับทางการ เช่น วันปิยมหาราช วันนวมินทรมหาราช วันจักรี ฯลฯ
- แสดงภาพพระบรมฉายาลักษณ์ / ภาพสัญลักษณ์วันสำคัญ
- วันที่ภาษาไทย (เลขไทย)
- ชื่อวันสำคัญตัวอักษรสีทองอร่าม
- คำน้อมรำลึกในพระมหากรุณาธิคุณ / บทถวายพระพร
- ลวดลายคั่นกนกทอง
- ข้อความท้ายภาพแสดงความจงรักภักดี:
  "ข้าพระพุทธเจ้า คณะผู้บริหารและพนักงาน"
  ตามด้วย "ชื่อเพจ/ชื่อบริษัท" ที่เปลี่ยนตามเพจที่เลือกใช้งานจริง
"""
import os
import sys
import re
from typing import Optional, Dict, Any, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter

THAI_NUMERALS = {
    '0': '๐', '1': '๑', '2': '๒', '3': '๓', '4': '๔',
    '5': '๕', '6': '๖', '7': '๗', '8': '๘', '9': '๙'
}

def to_thai_numerals(text: str) -> str:
    """แปลงเลขอารบิกในข้อความเป็นเลขไทย เช่น 23 ตุลาคม 2569 -> ๒๓ ตุลาคม ๒๕๖๙"""
    res = []
    for ch in str(text):
        res.append(THAI_NUMERALS.get(ch, ch))
    return "".join(res)

def get_thai_font(size: int, bold: bool = False):
    """เลือกฟอนต์ภาษาไทยที่เหมาะสมและคมชัดบน Windows"""
    candidates = [
        "C:/Windows/Fonts/leelawdb.ttf" if bold else "C:/Windows/Fonts/leelawad.ttf",
        "C:/Windows/Fonts/LeelaUIb.ttf" if bold else "C:/Windows/Fonts/LeelawUI.ttf",
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/angsana.ttc",
        "C:/Windows/Fonts/cordia.ttc"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    image_width: int,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    shadow_color: Optional[Tuple[int, int, int]] = None,
    shadow_offset: int = 1
) -> int:
    """วาดข้อความกึ่งกลางภาพ คืนค่าความสูงบรรทัด"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (image_width - text_width) // 2

    if shadow_color:
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)
    return text_height

def draw_golden_ornament_divider(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    y: int,
    width: int = 260,
    color: Tuple[int, int, int] = (225, 195, 115)
):
    """วาดลวดลายคั่นกนกทองแบบเรียบหรูทางการกึ่งกลางภาพ"""
    half = width // 2
    # เส้นทองไล่ระดับ
    draw.line([(center_x - half, y), (center_x - 35, y)], fill=(*color, 140), width=2)
    draw.line([(center_x + 35, y), (center_x + half, y)], fill=(*color, 140), width=2)
    
    # ลายเพชรกนกตรงกลาง
    draw.polygon([
        (center_x, y - 7),
        (center_x + 12, y),
        (center_x, y + 7),
        (center_x - 12, y)
    ], fill=color)
    draw.ellipse([(center_x - 24, y - 3), (center_x - 18, y + 3)], fill=color)
    draw.ellipse([(center_x + 18, y - 3), (center_x + 24, y + 3)], fill=color)
    draw.ellipse([(center_x - 32, y - 2), (center_x - 28, y + 2)], fill=color)
    draw.ellipse([(center_x + 28, y - 2), (center_x + 32, y + 2)], fill=color)

def is_royal_or_memorial_holiday(holiday: Dict[str, Any]) -> bool:
    """ตรวจสอบว่าเป็นวันสำคัญราชพิธี หรือวันรำลึกบูรพมหากษัตริย์ที่ต้องใช้รูปแบบทางการหรือไม่"""
    h_name = holiday.get("name", "")
    h_id = holiday.get("id", "")
    keywords = [
        "ปิยมหาราช", "นวมินทรมหาราช", "จักรี", "ฉัตรมงคล",
        "เฉลิมพระชนมพรรษา", "วันพ่อแห่งชาติ", "วันแม่แห่งชาติ"
    ]
    return any(k in h_name for k in keywords) or any(k in h_id for k in ["chulalongkorn", "navamindra", "chakri", "coronation", "queen", "king"])

def render_customized_royal_banner(
    holiday: Dict[str, Any],
    page_name: str,
    output_path: str,
    target_size: Tuple[int, int] = (1080, 1080)
) -> bool:
    """
    สร้างภาพกราฟิกวันสำคัญทางการสมพระเกียรติ โดยเปลี่ยนชื่อหน่วยงาน/ชื่อเพจด้านล่างตาม active page
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    h_name = holiday.get("name", "")

    # ตรวจสอบว่าเป็นวันปิยมหาราชและมีเทมเพลตต้นแบบตรงตามที่ผู้ใช้กำหนด
    template_path = "static/assets/royal/chulalongkorn_template.jpg"
    
    if "ปิย" in h_name and os.path.exists(template_path):
        try:
            base_img = Image.open(template_path).convert("RGB")
            orig_w, orig_h = base_img.size

            # ลบข้อความองค์กรเดิมที่ตำแหน่งล่าง (ตั้งแต่ y=472 ถึง 526)
            for y in range(470, 526):
                left_c = base_img.getpixel((35, y))
                right_c = base_img.getpixel((orig_w - 35, y))
                for x in range(35, orig_w - 35):
                    factor = (x - 35) / float(orig_w - 70)
                    r = int(left_c[0] * (1 - factor) + right_c[0] * factor)
                    g = int(left_c[1] * (1 - factor) + right_c[1] * factor)
                    b = int(left_c[2] * (1 - factor) + right_c[2] * factor)
                    base_img.putpixel((x, y), (r, g, b))

            # ขยายความละเอียดเป็นขนาด 1080x1080 ให้คมชัด
            hi_res_img = base_img.resize(target_size, Image.Resampling.LANCZOS)
            
            # เบลอเบาๆ ตรงรอยต่อด้านล่างเพื่อให้พื้นหลังสมูทเนียนสนิท
            box_area = (int(target_size[0]*0.05), int(target_size[1]*0.88), int(target_size[0]*0.95), target_size[1]-10)
            patch = hi_res_img.crop(box_area)
            patch_blurred = patch.filter(ImageFilter.GaussianBlur(radius=3))
            hi_res_img.paste(patch_blurred, box_area)

            # พิมพ์ข้อความทางการด้วยชื่อเพจ/ชื่อบริษัทปัจจุบัน
            draw = ImageDraw.Draw(hi_res_img)
            font_tribute = get_thai_font(26, bold=False)
            font_org = get_thai_font(28, bold=True)

            line1 = "ข้าพระพุทธเจ้า คณะผู้บริหารและพนักงาน"
            clean_name = page_name.strip()
            # จัดรูปแบบชื่อ เช่น "บริษัท ... จำกัด" หรือ "เพจ ..."
            line2 = clean_name if any(prefix in clean_name for prefix in ["บริษัท", "ห้างหุ้นส่วน", "ร้าน", "เพจ", "ทีมงาน"]) else f"เพจ {clean_name}"

            gold_text_color = (255, 235, 175)
            shadow_c = (50, 25, 5)

            y_pos = int(target_size[1] * 0.905)
            draw_centered_text(draw, line1, y_pos, target_size[0], font_tribute, fill=gold_text_color, shadow_color=shadow_c, shadow_offset=1)
            draw_centered_text(draw, line2, y_pos + 38, target_size[0], font_org, fill=gold_text_color, shadow_color=shadow_c, shadow_offset=1)

            hi_res_img.save(output_path, "JPEG", quality=95)
            print(f"✅ [Royal Holiday] สร้างภาพวันปิยมหาราชทางการสำเร็จ: {output_path} (เพจ: {page_name})")
            return True
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการสร้างภาพจากเทมเพลตปิยมหาราช: {e}")

    # กรณีเป็นวันสำคัญทางการอื่นๆ (วันนวมินทรมหาราช, วันจักรี ฯลฯ) ที่ใช้โครงสร้างทางการ
    return _render_generic_royal_poster(holiday, page_name, output_path, target_size)

def _render_generic_royal_poster(
    holiday: Dict[str, Any],
    page_name: str,
    output_path: str,
    target_size: Tuple[int, int] = (1080, 1080)
) -> bool:
    """สร้างโปสเตอร์ทางการสไตล์ทองหรูสำหรับวันสำคัญทางการอื่นๆ"""
    try:
        w, h = target_size
        img = Image.new("RGB", (w, h), (40, 22, 8))
        draw = ImageDraw.Draw(img)

        # Gradient พื้นหลังโทนน้ำตาลทองหรูหรา
        for y in range(h):
            ratio = y / float(h)
            # จากบน (45, 25, 10) -> กลาง (100, 70, 35) -> ล่าง (40, 22, 8)
            if ratio < 0.5:
                sub_r = ratio / 0.5
                r = int(45 + (100 - 45) * sub_r)
                g = int(25 + (70 - 25) * sub_r)
                b = int(10 + (35 - 10) * sub_r)
            else:
                sub_r = (ratio - 0.5) / 0.5
                r = int(100 + (40 - 100) * sub_r)
                g = int(70 + (22 - 70) * sub_r)
                b = int(35 + (8 - 35) * sub_r)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # กรอบทองบางๆ สองชั้นรอบภาพ
        border_inset = 35
        gold_border = (200, 165, 90)
        draw.rectangle([border_inset, border_inset, w - border_inset, h - border_inset], outline=gold_border, width=2)
        draw.rectangle([border_inset + 6, border_inset + 6, w - border_inset - 6, h - border_inset - 6], outline=(*gold_border, 80), width=1)

        # วันที่ภาษาไทย (เลขไทย)
        h_date_th = holiday.get("formatted_date_th") or holiday.get("date", "")
        h_date_thai_num = to_thai_numerals(h_date_th)
        font_date = get_thai_font(32, bold=False)
        draw_centered_text(draw, h_date_thai_num, int(h * 0.48), w, font_date, fill=(230, 210, 160))

        # ชื่อวันสำคัญ (สีทองเหลืองอร่าม)
        h_name = holiday.get("name", "วันสำคัญ")
        font_title = get_thai_font(56, bold=True)
        draw_centered_text(draw, h_name, int(h * 0.53), w, font_title, fill=(255, 225, 140), shadow_color=(20, 10, 0), shadow_offset=2)

        # ข้อความน้อมรำลึก
        greeting = holiday.get("greeting") or "น้อมรำลึกในพระมหากรุณาธิคุณอันหาที่สุดมิได้"
        font_desc = get_thai_font(26, bold=False)
        
        # ตัดคำให้อยู่ใน 2-3 บรรทัด
        lines = []
        if len(greeting) > 50:
            mid = len(greeting) // 2
            split_idx = greeting.rfind(" ", 0, mid + 15)
            if split_idx == -1: split_idx = mid
            lines.append(greeting[:split_idx].strip())
            lines.append(greeting[split_idx:].strip())
        else:
            lines.append(greeting)

        desc_y = int(h * 0.63)
        for line in lines:
            draw_centered_text(draw, line, desc_y, w, font_desc, fill=(240, 225, 190), shadow_color=(20, 10, 0), shadow_offset=1)
            desc_y += 38

        # ลายกนกทองคั่น
        draw_golden_ornament_divider(draw, w // 2, int(h * 0.77))

        # ข้าพระพุทธเจ้า ... ชื่อเพจ
        font_bottom1 = get_thai_font(24, bold=False)
        font_bottom2 = get_thai_font(28, bold=True)
        gold_bottom = (255, 235, 175)

        line1 = "ข้าพระพุทธเจ้า คณะผู้บริหารและพนักงาน"
        clean_name = page_name.strip()
        line2 = clean_name if any(prefix in clean_name for prefix in ["บริษัท", "ห้างหุ้นส่วน", "ร้าน", "เพจ", "ทีมงาน"]) else f"เพจ {clean_name}"

        y_bot = int(h * 0.83)
        draw_centered_text(draw, line1, y_bot, w, font_bottom1, fill=gold_bottom, shadow_color=(20, 10, 0), shadow_offset=1)
        draw_centered_text(draw, line2, y_bot + 40, w, font_bottom2, fill=gold_bottom, shadow_color=(20, 10, 0), shadow_offset=1)

        img.save(output_path, "JPEG", quality=95)
        print(f"✅ [Royal Holiday] สร้างภาพวันสำคัญทางการสำเร็จ: {output_path}")
        return True
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการสร้าง Generic Royal Poster: {e}")
        return False
