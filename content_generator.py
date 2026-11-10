"""
โมดูลสำหรับสร้างเนื้อหาโพสต์ Facebook ตามแนวทางของแต่ละแบรนด์ (Brand-Aware AI Content Generator)
รองรับ:
1. การสร้างเนื้อหาโพสต์ตาม Brand DNA ของแต่ละเพจ (วิเคราะห์กลุ่มเป้าหมาย จุดขาย บริการ และโทนเสียง)
2. วิเคราะห์รูปภาพที่อัปโหลดด้วย Gemini Multimodal AI แล้วสร้างหัวข้อและแคปชั่นตามแนวทางแบรนด์
3. วางแผนหัวข้อโพสต์อัตโนมัติประจำสัปดาห์/เดือน ตามเอกลักษณ์ของแต่ละเพจ
4. ระบบ Fallback Template คุณภาพสูงกรณีไม่เชื่อมต่อ API
"""
import os
import sys
import json
import random
import re
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv(override=True)

# รองรับ UTF-8 สำหรับ Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


def _resolve_brand_context(page_info: Optional[Dict[str, Any]] = None, product_or_service: Optional[str] = None, tone: Optional[str] = None) -> Dict[str, Any]:
    """
    รวบรวมและสกัดข้อมูล Brand DNA ของเพจที่กำลังใช้งาน
    """
    if not page_info:
        try:
            import pages_manager
            page_info = pages_manager.get_active_page() or {}
        except Exception:
            page_info = {}

    brand_dna = page_info.get("brand_dna", {}) or {}

    brand_name = (
        page_info.get("brand_name")
        or brand_dna.get("brand_name")
        or (page_info.get("name", "").split(" ")[0] if page_info.get("name") else None)
        or "FixPack"
    )

    business_type = (
        brand_dna.get("business_type")
        or page_info.get("category")
        or "บริการและสินค้าคุณภาพ"
    )

    tagline = (
        page_info.get("tagline")
        or brand_dna.get("tagline")
        or page_info.get("name")
        or ""
    )

    target_audience = (
        brand_dna.get("target_audience")
        or "ลูกค้าทั่วไปและผู้ที่มองหาบริการคุณภาพ"
    )

    core_services = brand_dna.get("core_services", [])
    if isinstance(core_services, list) and core_services:
        core_services_str = ", ".join(core_services)
    else:
        core_services_str = str(core_services or "บริการครบวงจร")

    selling_points = brand_dna.get("selling_points", [])
    if isinstance(selling_points, list) and selling_points:
        selling_points_str = ", ".join(selling_points)
    else:
        selling_points_str = str(selling_points or "ทีมงานมืออาชีพ รวดเร็ว ไว้ใจได้")

    tone_of_voice = (
        tone
        or brand_dna.get("tone_of_voice")
        or "น่าเชื่อถือ เป็นกันเอง ให้คำแนะนำและเชิญชวนอย่างอบอุ่น"
    )

    phone = page_info.get("phone") or brand_dna.get("phone") or os.getenv("BRAND_PHONE", "066-097-1257")
    price_tag = page_info.get("price_tag") or brand_dna.get("price_tag") or ""
    page_name = page_info.get("name", brand_name)

    # ข้อมูลอัตลักษณ์ตัวตนเพิ่มเติม
    page_id = str(page_info.get("id") or "")
    brand_story = page_info.get("brand_story") or brand_dna.get("brand_story") or ""
    negative_guidelines = page_info.get("negative_guidelines") or brand_dna.get("negative_guidelines") or ""

    # ดึงข้อมูลจากเอกสารประกอบที่แนบไว้
    docs_knowledge = ""
    if page_id:
        try:
            import document_knowledge_engine
            docs_knowledge = document_knowledge_engine.get_all_documents_context(page_id, max_chars=3500)
        except Exception:
            pass

    if product_or_service:
        display_product = product_or_service
    else:
        display_product = f"{brand_name} ({business_type})"

    return {
        "page_id": page_id,
        "brand_name": brand_name,
        "page_name": page_name,
        "business_type": business_type,
        "tagline": tagline,
        "brand_story": brand_story,
        "negative_guidelines": negative_guidelines,
        "docs_knowledge": docs_knowledge,
        "target_audience": target_audience,
        "core_services": core_services,
        "core_services_str": core_services_str,
        "selling_points": selling_points,
        "selling_points_str": selling_points_str,
        "tone_of_voice": tone_of_voice,
        "phone": phone,
        "price_tag": price_tag,
        "display_product": display_product,
        "page_info": page_info
    }


def generate_post_with_ai(
    topic: str,
    tone: Optional[str] = None,
    page_info: Optional[Dict[str, Any]] = None,
    product_or_service: Optional[str] = None
) -> str:
    """
    สร้างเนื้อหาโพสต์ด้วย Google Gemini AI โดยคำนึงถึง Brand DNA ของแต่ละเพจโดยตรง
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return ""

    ctx = _resolve_brand_context(page_info=page_info, product_or_service=product_or_service, tone=tone)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        story_line = f"- เรื่องราว/ตัวตนของแบรนด์: {ctx['brand_story']}\n" if ctx.get('brand_story') else ""
        negative_line = f"- ข้อควรระวัง/สิ่งที่ไม่ควรพูด: {ctx['negative_guidelines']}\n" if ctx.get('negative_guidelines') else ""
        docs_section = f"\nข้อมูลสำคัญจากเอกสารประกอบ/สินค้าจริง:\n{ctx['docs_knowledge']}\n" if ctx.get('docs_knowledge') else ""

        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านการเขียน Copywriting และการตลาดบน Facebook ภาษาไทย สำหรับแบรนด์ "{ctx['brand_name']}"

ข้อมูลอัตลักษณ์ของแบรนด์ (Brand DNA & Identity):
- ชื่อเพจ/แบรนด์: {ctx['page_name']}
- ประเภทธุรกิจ: {ctx['business_type']}
- สโลแกน / คอนเซ็ปต์: {ctx['tagline']}
{story_line}- กลุ่มลูกค้าเป้าหมาย: {ctx['target_audience']}
- สินค้าหรือบริการหลัก: {ctx['core_services_str']}
- จุดเด่นและจุดขายที่แตกต่าง: {ctx['selling_points_str']}
- โทนเสียงและการสื่อสาร: {ctx['tone_of_voice']}
{negative_line}- ช่องทางติดต่อ: โทร {ctx['phone']} หรือทักแชท Inbox เพจ
- ข้อมูลราคา/โปรโมชั่น: {ctx['price_tag'] or 'สอบถามเพิ่มเติมทาง Inbox'}
{docs_section}
โจทย์: กรุณาเขียนโพสต์ Facebook 1 โพสต์ สำหรับหัวข้อ: "{topic}"

โครงสร้างของโพสต์ที่ต้องการ:
1. Hook พาดหัวหยุดนิ้วโป้ง (1-2 บรรทัด มีอีโมจิที่ดึงดูด น่าสนใจ เข้ากับกลุ่มเป้าหมาย)
2. ปัญหาหรือความต้องการของลูกค้า ({ctx['target_audience']})
3. การตอบโจทย์และจุดเด่นของแบรนด์ {ctx['brand_name']} (นำจุดขาย {ctx['selling_points_str']} มาใช้เป็นข้อย่อยอ่านง่าย)
4. Call to Action (กระตุ้นให้ทักแชท Inbox เพจ หรือโทร {ctx['phone']})
5. แฮชแท็กที่ตรงกับแบรนด์และหัวข้อ 3-5 แท็ก (รวมถึง #{ctx['brand_name'].replace(' ', '')})

ข้อกำหนดสำคัญ:
- ใช้ภาษาไทยธรรมชาติ สอดคล้องกับโทน "{ctx['tone_of_voice']}" ไม่แข็งเหมือนหุ่นยนต์
- จัดย่อหน้าและเว้นบรรทัดให้อ่านสบายตาบนมือถือ
- ไม่ต้องใส่คำอธิบายเพิ่มเติม ไม่ต้องมี "พาดหัว:", "เนื้อหา:" ให้เขียนเป็นข้อความตัวโพสต์เพียวๆ พร้อมกดโพสต์ได้ทันที
"""
        models_to_try = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
        for model_choice in models_to_try:
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


def generate_caption_from_image(
    image_path: str,
    page_info: Optional[Dict[str, Any]] = None,
    brand_name: Optional[str] = None,
    tagline: Optional[str] = None,
    phone: Optional[str] = None,
    price: Optional[str] = None,
    category: Optional[str] = None,
    user_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    วิเคราะห์รูปภาพด้วย Gemini Multimodal Vision แล้วแต่งแคปชั่นและตั้งชื่อหัวข้อ
    ให้สอดคล้องกับสิ่งที่เห็นในภาพและ Brand DNA ของเพจที่กำลังใช้งาน
    """
    if not os.path.exists(image_path):
        return {"success": False, "error": f"ไม่พบไฟล์รูปภาพ: {image_path}"}

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {
            "success": False,
            "error": "กรุณาระบุ GEMINI_API_KEY ในไฟล์ .env เพื่อใช้งานระบบ AI วิเคราะห์ภาพ"
        }

    ctx = _resolve_brand_context(page_info=page_info)
    b_name = brand_name or ctx["brand_name"]
    b_tagline = tagline or ctx["tagline"]
    b_phone = phone or ctx["phone"]
    b_price = price or ctx["price_tag"]
    b_category = category or ctx["business_type"]

    try:
        from PIL import Image
        from google import genai
        client = genai.Client(api_key=api_key)
        img = Image.open(image_path)

        story_line = f"- เรื่องราว/ตัวตนของแบรนด์: {ctx['brand_story']}\n" if ctx.get('brand_story') else ""
        negative_line = f"- ข้อควรระวัง/สิ่งที่ไม่ควรพูด: {ctx['negative_guidelines']}\n" if ctx.get('negative_guidelines') else ""
        docs_section = f"\nข้อมูลสำคัญจากเอกสารประกอบ/สินค้าจริง:\n{ctx['docs_knowledge']}\n" if ctx.get('docs_knowledge') else ""

        prompt = f"""
คุณเป็นสุดยอดผู้เชี่ยวชาญด้าน Copywriting และการตลาดบน Facebook ภาษาไทย สำหรับแบรนด์ "{b_name}"

ข้อมูลอัตลักษณ์ของแบรนด์:
- ชื่อแบรนด์/เพจ: {ctx['page_name']}
- ประเภทธุรกิจ: {b_category}
- สโลแกน/จุดยืน: {b_tagline}
{story_line}- กลุ่มลูกค้าเป้าหมาย: {ctx['target_audience']}
- สินค้าหรือบริการหลัก: {ctx['core_services_str']}
- จุดเด่นและจุดขายสำคัญ: {ctx['selling_points_str']}
- โทนเสียงและการเล่าเรื่อง: {ctx['tone_of_voice']}
{negative_line}- เบอร์โทรติดต่อ: {b_phone}
- ราคา/โปรโมชั่น: {b_price or 'สอบถามเพิ่มเติมทาง Inbox'}
- ข้อมูลเพิ่มเติม/คำบอกใบ้จากผู้ใช้: {user_hint or 'ไม่มี (ให้วิเคราะห์จากภาพเป็นหลัก)'}
{docs_section}

คำสั่ง:
1. ดูและวิเคราะห์รูปภาพนี้อย่างละเอียด: มีองค์ประกอบอะไรบ้าง อาหาร รถยนต์ อะไหล่ งานช่าง เอกสาร พื้นที่ ความรู้สึก หรือสิ่งที่เกิดขึ้นในภาพคืออะไร
2. เชื่อมโยงสิ่งที่เห็นในภาพเข้ากับสินค้า/บริการและจุดขายของแบรนด์ "{b_name}" อย่างกลมกลืนเป็นธรรมชาติ
3. เขียนหัวข้อโพสต์สั้นๆ ที่หยุดนิ้วโป้ง (topic) ความยาวไม่เกิน 40 ตัวอักษร
4. เขียนแคปชั่น Facebook ฉบับเต็ม (caption) ที่พร้อมโพสต์:
   - มี Hook เปิดหัวที่ดึงดูด
   - เนื้อหาบรรยายเชื่อมโยงกับสิ่งที่เห็นในภาพ
   - นำเสนอคุณค่าและจุดเด่นของบริการ {b_name} (ใช้สัญลักษณ์ ✅ หรือ 🔹)
   - Call to Action ชวนทัก Inbox หรือโทร {b_phone}
   - แฮชแท็กที่ตรงกับสิ่งที่เห็นในภาพและแบรนด์ 3-5 แท็ก

ให้ตอบกลับเฉพาะ JSON รูปแบบนี้เท่านั้น ห้ามมี markdown code block อื่น:
{{
  "topic": "ชื่อหัวข้อโพสต์สั้นๆ",
  "caption": "เนื้อหาแคปชั่นฉบับเต็ม..."
}}
"""
        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]
        for m in models_to_try:
            try:
                resp = client.models.generate_content(model=m, contents=[prompt, img])
                if resp and resp.text:
                    # ค้นหาบล็อก JSON
                    json_match = re.search(r"\{.*\}", resp.text, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0))
                            return {
                                "success": True,
                                "topic": data.get("topic", f"บริการจาก {b_name}"),
                                "caption": data.get("caption", "").strip(),
                                "model": m
                            }
                        except Exception:
                            pass

                    # Fallback หากไม่ใช่ JSON: ใช้บรรทัดแรกเป็น Topic และทั้งหมดเป็น Caption
                    lines = [ln.strip() for ln in resp.text.strip().split("\n") if ln.strip()]
                    suggested_top = lines[0].replace("#", "").replace("*", "").strip() if lines else f"บริการจาก {b_name}"
                    return {
                        "success": True,
                        "topic": suggested_top[:40],
                        "caption": resp.text.strip(),
                        "model": m
                    }
            except Exception:
                continue

        return {"success": False, "error": "AI ไม่สามารถประมวลผลรูปภาพได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_post_from_template(
    topic: str = "",
    page_info: Optional[Dict[str, Any]] = None,
    product: Optional[str] = None
) -> str:
    """
    สร้างโพสต์จาก Template ตาม Brand DNA กรณีไม่มี AI API Key
    """
    ctx = _resolve_brand_context(page_info=page_info, product_or_service=product)
    b_name = ctx["brand_name"]
    topic = topic or f"บริการคุณภาพจาก {b_name}"

    hooks = [
        f"✨ มองหา {ctx['business_type']} ที่มั่นใจได้อยู่ใช่ไหม? {b_name} พร้อมดูแลคุณครับ! 🌟",
        f"💡 ปัญหาที่คุณกังวล ให้ {b_name} ช่วยดูแล ครบ จบ สะดวก สบายใจ 👍",
        f"🎯 ยกระดับความสะดวกสบายด้วยบริการมาตรฐานจาก {b_name} ✨",
        f"📢 รวมทุกเรื่องเกี่ยวกับ {ctx['business_type']} ไว้ที่นี่! {b_name} ยินดีให้บริการครับ"
    ]

    services_bullets = ""
    if ctx.get("core_services") and isinstance(ctx["core_services"], list):
        for s in ctx["core_services"][:3]:
            services_bullets += f"✅ {s}\n"
    if not services_bullets:
        services_bullets = f"✅ บริการตรงจุด ใส่ใจทุกขั้นตอน\n✅ ทีมงานมืออาชีพ ไว้ใจได้\n✅ ราคามาตรฐาน ประเมินชัดเจน\n"

    selling_str = ctx["selling_points_str"]

    bodies = [
        f"ไม่ว่าจะเป็นเรื่อง {topic} หรือความต้องการใดๆ เกี่ยวกับ {ctx['business_type']} วางใจให้ {b_name} ดูแลได้เลยครับ!\n\nจุดเด่นของเรา:\n{services_bullets}\n{selling_str}",
        f"เรื่อง {ctx['business_type']} อย่าปล่อยให้กวนใจคุณ! ให้ทีมงาน {b_name} เข้าไปช่วยดูแล\n\n{services_bullets}\nเพราะความพึงพอใจและความสะดวกสบายของคุณ คือสิ่งสำคัญที่สุดสำหรับเรา",
        f"เปลี่ยนเรื่องยากให้เป็นเรื่องง่าย ด้วยบริการมาตรฐานจาก {b_name}\n\n{services_bullets}\nรวดเร็ว มืออาชีพ สบายใจในทุกขั้นตอน"
    ]

    price_str = f" ราคาเริ่มต้นเพียง {ctx['price_tag']}" if ctx.get("price_tag") else ""

    ctas = [
        f"👇 สนใจสอบถามรายละเอียดหรือปรึกษา ทักแชท Inbox เพจ {ctx['page_name']} หรือโทร {ctx['phone']} ได้เลยครับ!{price_str}",
        f"💬 ปรึกษาหรือนัดหมายบริการได้ทันที ทักข้อความหาเราได้ตลอดเวลา ทีมงาน {b_name} ยินดีให้คำแนะนำครับ!",
        f"📞 โทรจองคิวหรือสอบถามเพิ่มเติมได้ที่ {ctx['phone']} หรือทักแชท Inbox ได้เลยครับ"
    ]

    clean_tag = b_name.replace(" ", "").replace("-", "").replace(".", "")
    hashtags = [
        f"#{clean_tag} #{ctx['business_type'].replace(' ', '')} #บริการคุณภาพ #ดูแลครบวงจร",
        f"#{clean_tag} #บริการประทับใจ #รีวิวเพียบ #มั่นใจได้",
        f"#{clean_tag} #{clean_tag}Official #บริการถึงใจ"
    ]

    hook = random.choice(hooks)
    body = random.choice(bodies)
    cta = random.choice(ctas)
    tag = random.choice(hashtags)

    return f"{hook}\n\n{body}\n\n{cta}\n\n{tag}"


def create_facebook_post_content(
    topic: str = "",
    tone: Optional[str] = None,
    page_info: Optional[Dict[str, Any]] = None,
    product: Optional[str] = None
) -> str:
    """
    ฟังก์ชันหลักสำหรับสร้างเนื้อหาโพสต์ (เรียก Gemini AI ตาม Brand DNA ก่อน หากไม่มี Key ให้ใช้ Dynamic Template)
    """
    if not topic:
        ctx = _resolve_brand_context(page_info=page_info, product_or_service=product)
        topic = f"บริการแนะนำจาก {ctx['brand_name']}"

    # 1. ลองใช้ Gemini AI
    ai_content = generate_post_with_ai(topic=topic, tone=tone, page_info=page_info, product_or_service=product)
    if ai_content:
        return ai_content

    # 2. Fallback Template
    return generate_post_from_template(topic=topic, page_info=page_info, product=product)


def generate_brand_topics(page_info: Optional[Dict[str, Any]] = None, days: int = 7) -> List[Dict[str, str]]:
    """
    สร้างแผนหัวข้อคอนเทนต์ตาม Brand DNA สำหรับ N วัน
    """
    ctx = _resolve_brand_context(page_info=page_info)
    days = min(max(days, 3), 30)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
คุณเป็นผู้เชี่ยวชาญการวางแผนคอนเทนต์ Facebook สำหรับแบรนด์ "{ctx['brand_name']}"
- ประเภทธุรกิจ: {ctx['business_type']}
- สโลแกน: {ctx['tagline']}
- กลุ่มลูกค้าเป้าหมาย: {ctx['target_audience']}
- บริการหรือสินค้าหลัก: {ctx['core_services_str']}
- จุดขาย: {ctx['selling_points_str']}
- โทนเสียง: {ctx['tone_of_voice']}

กรุณาวางแผนหัวข้อโพสต์จำนวน {days} วัน ในรูปแบบ JSON Array:
[
  {{"topic": "ชื่อหัวข้อโพสต์ที่น่าสนใจและหยุดนิ้วโป้ง", "brief": "แนวทางการเล่าสั้นๆ 1 บรรทัด", "category": "หมวดหมู่เนื้อหา"}}
]
ตอบกลับเฉพาะโค้ด JSON เท่านั้น ห้ามมีคำอธิบายอื่น
"""
            resp = client.models.generate_content(model="gemini-3.1-flash-lite", contents=prompt)
            if resp and resp.text:
                clean_json = resp.text.strip().replace("```json", "").replace("```", "").strip()
                match = re.search(r"\[.*\]", clean_json, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except Exception as e:
            print(f"⚠️ Error in generate_brand_topics: {e}")

    # Fallback topics from Brand DNA
    fallback = []
    base_services = ctx.get("core_services") or [ctx["business_type"]]
    for i in range(days):
        srv = base_services[i % len(base_services)] if base_services else ctx["business_type"]
        fallback.append({
            "topic": f"หมดกังวลเรื่อง {srv} ให้ {ctx['brand_name']} ดูแล",
            "brief": f"นำเสนอจุดเด่นของบริการ {srv} พร้อมคำแนะนำและโปรโมชั่นพิเศษ",
            "category": srv if isinstance(srv, str) else "บริการเด่น"
        })
    return fallback

# ================= THAI HOLIDAYS POST GENERATOR =================

def generate_holiday_post(
    holiday: Dict[str, Any],
    page_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    สร้างเนื้อหาโพสต์วันสำคัญ Facebook ที่เชื่อมโยงความหมายของวันสำคัญเข้ากับ Brand DNA
    โดยใช้ Google Gemini AI และมี Rich Professional Fallback Template คุณภาพสูงกรณีไม่มี API Key
    
    คืนค่าเป็น:
    {
        "topic": topic,
        "content": content,
        "hashtags": hashtags,
        "visual_concept": visual_concept
    }
    """
    ctx = _resolve_brand_context(page_info=page_info)
    b_name = ctx["brand_name"]
    b_biz = ctx["business_type"]
    b_tagline = ctx["tagline"]
    b_phone = ctx["phone"]
    b_services = ctx["core_services_str"]
    b_selling = ctx["selling_points_str"]
    b_tone = ctx["tone_of_voice"]
    
    h_name = holiday.get("name", "วันสำคัญ")
    h_category = holiday.get("category", "วันสำคัญ")
    h_desc = holiday.get("description", "")
    h_greeting = holiday.get("greeting", "")
    h_visual_theme = holiday.get("visual_theme", "Professional photography")
    h_tags = holiday.get("suggested_hashtags", [])

    clean_brand = b_name.replace(" ", "").replace("-", "").replace(".", "")
    base_hashtags = list(h_tags)
    if f"#{clean_brand}" not in base_hashtags:
        base_hashtags.append(f"#{clean_brand}")
    if ctx.get("business_type") and f"#{ctx['business_type'].replace(' ', '')}" not in base_hashtags:
        base_hashtags.append(f"#{ctx['business_type'].replace(' ', '')}")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้าน Copywriting และการตลาดบน Social Media ภาษาไทย
แบรนด์: "{b_name}" ({b_biz})
สโลแกน: {b_tagline}
จุดเด่นของแบรนด์: {b_selling}
บริการหลัก: {b_services}
ช่องทางติดต่อ: โทร {b_phone} หรือ Inbox เพจ {ctx['page_name']}

โจทย์: เขียนโพสต์ Facebook อวยพรและระลึกถึงเนื่องใน "{h_name}" ({holiday.get('date', '')})
ข้อมูลวันสำคัญ: {h_desc}
แนวทางการอวยพร/ความหมาย: {h_greeting}

ข้อกำหนดเนื้อหา:
1. ข้อความอวยพร/น้อมรำลึกที่เหมาะสมอย่างยิ่งตามกาลเทศะและประเภท ({h_category}):
   - วันสำคัญทางศาสนาให้สงบ ปิติ มีสติ
   - วันรำลึกราชการให้น้อมรำลึกสำนึกในพระมหากรุณาธิคุณอย่างสุภาพสง่างาม
   - วันเทศกาลให้ร่าเริง สดใส อบอุ่น สนุกสนาน
   - วันสากล/ครอบครัวให้อบอุ่นหัวใจ ซาบซึ้ง
2. เชื่อมโยงความหมายของวันสำคัญเข้ากับคุณค่าและการดูแลลูกค้าของแบรนด์ "{b_name}" อย่างแนบเนียน อบอุ่น และเป็นธรรมชาติ (ไม่ขายของยัดเยียดแบบฮาร์ดเซลล์ แต่สร้างความผูกพัน ความเชื่อมั่น และความประทับใจ)
3. มี Call to Action หรือคำเชิญชวนอย่างสุภาพ หากต้องการคำปรึกษาหรือบริการจากทางแบรนด์ (โทร {b_phone} หรือทัก Inbox)
4. แฮชแท็กที่เหมาะสม 4-6 แท็ก
5. สรุปแนวคิดรูปภาพ (visual_concept) เป็นภาษาอังกฤษสั้นๆ เพื่อนำไปสั่ง AI สต็อกภาพต่อ

ให้ตอบกลับเฉพาะ JSON รูปแบบนี้เท่านั้น ห้ามมี markdown อื่น:
{{
  "topic": "หัวข้อโพสต์สั้นๆ ที่ประทับใจ ไม่เกิน 40 ตัวอักษร",
  "content": "เนื้อหาแคปชั่นฉบับเต็มพร้อมอีโมจิและการจัดบรรทัดอ่านง่ายบนมือถือ...",
  "hashtags": ["#แท็ก1", "#แท็ก2"],
  "visual_concept": "Creative visual prompt in English..."
}}
"""
            models = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
            for m in models:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp and resp.text:
                        raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
                        match = re.search(r"\{.*\}", raw, re.DOTALL)
                        if match:
                            data = json.loads(match.group(0))
                            return {
                                "topic": data.get("topic", f"สุขสันต์{h_name} จากใจ {b_name}"),
                                "content": data.get("content", "").strip(),
                                "hashtags": data.get("hashtags", base_hashtags),
                                "visual_concept": data.get("visual_concept", h_visual_theme)
                            }
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ Gemini AI Error on holiday post: {e}")

    # ================= RICH FALLBACK TEMPLATE =================
    topic = f"สุขสันต์{h_name} ✨ ความปรารถนาดีจาก {b_name}"
    h_type = holiday.get("type", "")

    if h_type == "buddhist":
        hook = f"🪷 เนื่องใน{h_name} ขอร่วมอนุโมทนาบุญและส่งมอบความสุขสงบสู่ทุกท่าน 🙏✨"
        body = (
            f"{h_greeting}\n\n"
            f"ในวันพระใหญ่อันเป็นมงคลนี้ ทีมงาน {b_name} ขอร่วมเป็นส่วนหนึ่งในการส่งมอบความปรารถนาดี "
            f"ขอให้ทุกท่านและครอบครัวประสบแต่ความสุข ความเจริญ มีสุขภาพพลานามัยที่สมบูรณ์แข็งแรง "
            f"และมีจิตใจที่ผ่องใสในทุกๆ วันครับ\n\n"
            f"สำหรับทุกความต้องการด้าน {b_biz} พวกเราพร้อมดูแลเคียงข้างคุณเสมอด้วยความซื่อสัตย์และจริงใจ"
        )
    elif h_type == "national_holiday" and ("นวมินทร" in h_name or "ปิยมหาราช" in h_name or "จักรี" in h_name or "รัฐธรรมนูญ" in h_name):
        topic = f"น้อมรำลึกในพระมหากรุณาธิคุณ เนื่องใน{h_name}"
        hook = f"💛 น้อมรำลึกในพระมหากรุณาธิคุณอันหาที่สุดมิได้ เนื่องใน{h_name}"
        body = (
            f"{h_greeting}\n\n"
            f"ข้าพระพุทธเจ้า ผู้บริหารและทีมงาน {b_name} ขอน้อมรำลึกและสืบสานพระราชปณิธาน "
            f"มุ่งมั่นพัฒนาคุณภาพการบริการและความซื่อสัตย์ เพื่อส่งต่อประโยชน์สุขและความอุ่นใจให้แก่สังคมและลูกค้าทุกท่านสืบไป"
        )
    elif "เฉลิมพระชนมพรรษา" in h_name or "ฉัตรมงคล" in h_name:
        topic = f"เนื่องในโอกาส{h_name}"
        hook = f"👑 ขอพระองค์ทรงพระเจริญยิ่งยืนนาน เนื่องในโอกาส{h_name}"
        body = (
            f"{h_greeting}\n\n"
            f"ด้วยเกล้าด้วยกระหม่อม ขอเดชะ\n"
            f"ข้าพระพุทธเจ้า ผู้บริหารและพนักงาน {b_name}"
        )
    elif h_type == "festival" or "สงกรานต์" in h_name or "ลอยกระทง" in h_name or "ปีใหม่" in h_name:
        hook = f"🎉 สุขสันต์{h_name}! ขอให้เทศกาลนี้เต็มไปด้วยรอยยิ้ม ความอบอุ่น และความสุขล้นใจ 🌟💖"
        body = (
            f"{h_greeting}\n\n"
            f"ในโอกาสแห่งความสุขและเทศกาลพิเศษนี้ ทีมงาน {b_name} ขอขอบพระคุณลูกค้าทุกท่านจากใจจริง "
            f"ที่ให้ความไว้วางใจให้เราเป็นผู้ช่วยดูแล {b_biz} มาโดยตลอด\n\n"
            f"ไม่ว่าเทศกาลไหนๆ เรื่อง {b_services} วางใจให้ {b_name} คอยดูแลเคียงข้างคุณได้เสมอครับ!"
        )
    elif "แม่" in h_name or "พ่อ" in h_name or "เด็ก" in h_name:
        hook = f"💙 สุขสันต์{h_name} ร่วมส่งต่อความรักและความห่วงใยให้คนสำคัญในครอบครัว 👨‍👩‍👧‍👦✨"
        body = (
            f"{h_greeting}\n\n"
            f"เพราะ 'บ้านและครอบครัว' คือสิ่งที่สำคัญที่สุด ทีมงาน {b_name} จึงมุ่งมั่นส่งมอบบริการ "
            f"ที่สะดวก ปลอดภัย และได้มาตรฐาน เพื่อให้ทุกคนในบ้านใช้ชีวิตได้อย่างสบายใจในทุกวันครับ"
        )
    else:
        hook = f"✨ สุขสันต์{h_name} ความสุขและความปรารถนาดีจากใจ {b_name} 🌟"
        body = (
            f"{h_greeting}\n\n"
            f"ทีมงาน {b_name} ขอร่วมส่งมอบกำลังใจและรอยยิ้มให้ทุกท่านในวันพิเศษนี้\n"
            f"สำหรับเรื่อง {b_biz} ให้เราช่วยดูแลคุณได้ทุกเวลาครับ"
        )

    cta = f"💬 สนใจสอบถามหรือนัดหมายบริการ ทักแชท Inbox เพจ {ctx['page_name']} หรือโทร {b_phone} ได้ตลอดเวลาครับ"
    tag_str = " ".join(base_hashtags[:6])
    full_content = f"{hook}\n\n{body}\n\n{cta}\n\n{tag_str}"

    return {
        "topic": topic,
        "content": full_content,
        "hashtags": base_hashtags,
        "visual_concept": h_visual_theme
    }
