"""
โมดูลสำหรับสร้างเนื้อหาโพสต์ Facebook (ด้วย AI Gemini หรือ Marketing Templates)
"""
import os
import sys
import random
from typing import Optional

# รองรับ UTF-8 สำหรับ Windows Console ป้องกันปัญหาเรื่อง Emoji และภาษาไทย
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def generate_post_with_ai(topic: str, tone: str = "น่าสนใจและเป็นกันเอง", product_or_service: str = "FixPack งานเล็กซ่อมครบจบในแพ็กเดียว") -> str:
    """สร้างเนื้อหาโพสต์ด้วย Google Gemini AI (ใช้โมเดลรุ่นล่าสุด gemini-3.1-flash-lite)"""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return ""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านการเขียน Copywriting และการตลาดบน Facebook ภาษาไทย
กรุณาเขียนโพสต์ Facebook จำนวน 1 โพสต์ สำหรับหัวข้อ: "{topic}"
สินค้า/บริการ: {product_or_service}
โทนเสียง: {tone}

โครงสร้างของโพสต์ที่ต้องการ:
1. Hook (พาดหัวหยุดนิ้วโป้งคนอ่าน 1-2 บรรทัด มีอีโมจิที่ดึงดูด)
2. ปัญหาที่ลูกค้าเจ้าของบ้านหรือคอนโดมักเจอ (Pain Point / Story)
3. ทางออกและจุดเด่นของ FixPack (Value / Solution: งานเล็กซ่อมครบจบในแพ็กเดียว ช่างมืออาชีพ ไว้ใจได้ ไม่ทิ้งงาน)
4. Call to Action (ชวนทักแชท Inbox ส่งรูปหน้างานมาประเมินราคาฟรี)
5. แฮชแท็กที่เกี่ยวข้อง 3-5 แท็ก

ข้อกำหนดสำคัญ:
- ใช้ภาษาไทยธรรมชาติ น่าอ่าน ไม่แข็งเหมือนหุ่นยนต์แปลมา
- จัดย่อหน้าและเว้นบรรทัดให้อ่านสบายตาบนมือถือ
- ไม่ต้องใส่คำอธิบายเพิ่มเติมหรือใส่คำว่า "พาดหัว:", "เนื้อหา:" ให้เขียนเป็นข้อความตัวโพสต์เพียวๆ พร้อมกดโพสต์ได้ทันที
"""
        # ลองใช้ gemini-3.1-flash-lite เป็นตัวหลัก (เสถียรและเร็วที่สุด)
        for model_choice in ["gemini-3.1-flash-lite", "gemini-3.8-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_choice,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue

        return ""
    except Exception as e:
        print(f"⚠️ การเรียกใช้ Gemini AI ขัดข้อง: {e}")
        return ""

def generate_post_from_template(topic: str = "บริการซ่อมแซมบ้าน", product: str = "FixPack งานเล็กซ่อมครบจบในแพ็กเดียว") -> str:
    """สร้างโพสต์ตัวอย่างตามโครงสร้าง Copywriting มืออาชีพสำหรับ FixPack"""
    hooks = [
        f"🚨 งานช่างในบ้านเรื่องเล็กๆ แต่อย่าปล่อยให้กลายเป็นเรื่องใหญ่! 🛠️",
        f"💡 ปวดหัวกับงานซ่อมในบ้านไหม? ก๊อกน้ำรั่ว ไฟดับ ปั๊มน้ำพัง FixPack ช่วยคุณได้! ✨",
        f"🏠 รวมงานซ่อมจุดเล็กๆ ในบ้านไว้ที่เดียว ซ่อมครบ จบไว งบไม่บานปลาย 👍",
        f"✨ รู้หรือไม่? งานซ่อมแซมเล็กๆ ในบ้าน ถ้ารอช่างใหญ่อาจไม่คุ้ม แต่ FixPack เราพร้อมดูแลทันที!"
    ]

    bodies = [
        f"หลายบ้านมักเจอปัญหานี้... ก๊อกน้ำหยด ไฟกระพริบ ประตูฝืด หรือกระเบื้องร่อน จะเรียกช่างก็หายาก ช่างใหญ่ก็ไม่ค่อยรับงานเล็กๆ\n\nแต่ที่ {product} เราเข้าใจคุณดี! ไม่ว่าจะงานเล็กงานน้อย เราจัดการให้เรียบร้อย:\n\n1️⃣ ช่างมืออาชีพ ตรงต่อเวลา ไว้ใจได้\n2️⃣ ประเมินงานชัดเจน ราคามาตรฐาน ไม่มีค่าใช้จ่ายแอบแฝง\n3️⃣ บริการรวดเร็ว จบงานสะอาด สบายใจทั้งบ้าน",
        f"ไม่ต้องเสียเวลาหาช่างหลายรอบ! ให้ {product} ดูแลครบทุกจุดในบ้านคุณ ไม่ว่าจะระบบน้ำ ระบบไฟ ซ่อมแซมทั่วไป บริการด้วยมาตรฐานและใส่ใจทุกรายละเอียด\n\nงานเล็กแค่ไหนเราก็ยินดีให้บริการครับ!",
        f"เปลี่ยนบ้านพังให้กลับมาปัง ด้วยบริการงานซ่อมด่วนถึงบ้านจาก {product}\nซ่อมเร็ว เก็บงานเนี๊ยบ ปลอดภัย พร้อมรับประกันงานซ่อม ให้คุณอุ่นใจได้ทุกวัน"
    ]

    ctas = [
        "👇 บ้านไหนมีจุดที่ต้องซ่อมอยู่ ทักแชท Inbox ส่งรูปหน้างานมาประเมินราคาฟรีได้เลยครับ!",
        "💬 ปรึกษาหรือนัดหมายช่างได้ง่ายๆ ทัก Inbox เพจ FixPack ได้ทันที ทีมงานพร้อมดูแลครับ!",
        "📞 จองคิวช่างหรือสอบถามรายละเอียด ทักข้อความเพจ FixPack งานเล็กซ่อมครบจบในแพ็กเดียว ได้ตลอดเลยครับ",
        "📌 เซฟโพสต์นี้ไว้เผื่อฉุกเฉิน หรือแชร์บอกต่อคนในบ้านได้เลยนะครับ!"
    ]

    hashtags = [
        "#FixPack #งานเล็กซ่อมครบจบในแพ็กเดียว #ช่างซ่อมบ้าน #ซ่อมประปา #ซ่อมไฟ #ช่างประจำบ้าน #ซ่อมบ้านด่วน",
        "#FixPack #บริการซ่อมบ้าน #ช่างซ่อมคอนโด #งานซ่อมบ้าน #ดูแลบ้าน #ช่างมืออาชีพ",
        "#FixPack #ซ่อมบ้านครบวงจร #หมดปัญหาเรื่องช่าง #บริการถึงบ้าน"
    ]

    hook = random.choice(hooks)
    body = random.choice(bodies)
    cta = random.choice(ctas)
    tag = random.choice(hashtags)

    post_content = f"{hook}\n\n{body}\n\n{cta}\n\n{tag}"
    return post_content

def create_facebook_post_content(topic: str = "บริการช่างซ่อมแซมบ้าน", tone: str = "น่าเชื่อถือ เป็นกันเอง ให้คำแนะนำ", product: str = "FixPack งานเล็กซ่อมครบจบในแพ็กเดียว") -> str:
    """ฟังก์ชันหลักสำหรับสร้างเนื้อหาโพสต์ (ลองใช้ AI ก่อน หากไม่มี API Key ให้ใช้ Template)"""
    # 1. ลองใช้ Gemini AI ก่อน
    ai_content = generate_post_with_ai(topic=topic, tone=tone, product_or_service=product)
    if ai_content:
        return ai_content

    # 2. ถ้าไม่มี AI Key หรือ Error ให้ใช้ Template คุณภาพสูง
    return generate_post_from_template(topic=topic, product=product)
