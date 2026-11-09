"""
โมดูลจัดการเอกสารและฐานความรู้แบรนด์ (Brand Knowledge & Document Engine)
หน้าที่:
1. รองรับการแนบไฟล์ประกอบข้อมูลแบรนด์ (PDF, Word .docx, Text, CSV, Markdown, รูปภาพโบรชัวร์/เมนู)
2. สกัดเนื้อหาข้อความ (Text Extraction) จากไฟล์รูปแบบต่างๆ
3. ให้ AI (Gemini) สรุปและสกัดข้อมูลจากเอกสารเข้าสู่ Brand DNA (เรื่องราวแบรนด์, จุดขาย, สินค้า/บริการ, กลุ่มเป้าหมาย)
4. จัดเตรียมเนื้อหาความรู้ (Knowledge Context) เพื่อส่งต่อให้ AI ใช้ในการเขียนคอนเทนต์ Facebook
"""
import os
import sys
import json
import time
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

DOCUMENTS_BASE_DIR = "brand_documents"


def _get_page_docs_dir(page_id: str) -> str:
    """คืนค่า path โฟลเดอร์เก็บเอกสารของเพจนั้นๆ"""
    safe_page_id = str(page_id).strip() or "default"
    path = os.path.join(DOCUMENTS_BASE_DIR, safe_page_id)
    os.makedirs(path, exist_ok=True)
    return path


def _get_metadata_path(page_id: str) -> str:
    return os.path.join(_get_page_docs_dir(page_id), "metadata.json")


def load_documents_metadata(page_id: str) -> List[Dict[str, Any]]:
    """โหลดรายการเอกสารทั้งหมดของเพจ"""
    meta_path = _get_metadata_path(page_id)
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_documents_metadata(page_id: str, docs: List[Dict[str, Any]]):
    """บันทึกรายการเอกสารของเพจ"""
    meta_path = _get_metadata_path(page_id)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    สกัดข้อความจากไฟล์เอกสารหลากหลายฟอร์แมต
    รองรับ: PDF, DOCX, TXT, MD, CSV, JSON, PNG, JPG, JPEG, WEBP
    """
    ext = os.path.splitext(filename)[1].lower()
    text = ""

    # 1. Plain Text / Markdown / CSV / JSON
    if ext in [".txt", ".md", ".csv", ".json", ".log"]:
        for encoding in ["utf-8", "utf-8-sig", "cp874", "tis-620", "latin1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read()
                break
            except Exception:
                continue
        return text.strip()

    # 2. PDF Files (via pypdf)
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            extracted = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted.append(f"--- หน้า {i+1} ---\n{page_text.strip()}")
            text = "\n\n".join(extracted)
        except Exception as e:
            print(f"pypdf extraction error for {filename}: {e}")

        # หากเป็น PDF สแกน (ไม่มีข้อความตัวอักษร) ลองใช้ Gemini
        if not text.strip():
            text = _extract_with_gemini_multimodal(file_path, mime_type="application/pdf")
        return text.strip()

    # 3. Word Documents (.docx)
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        paras.append(" | ".join(cells))
            text = "\n".join(paras)
        except Exception as e:
            print(f"docx extraction error for {filename}: {e}")
        return text.strip()

    # 4. Images (JPG, PNG, WEBP) -> ใช้ Gemini Vision OCR
    elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
        text = _extract_with_gemini_multimodal(file_path, mime_type=f"image/{ext.replace('.', '')}")
        return text.strip()

    return text.strip()


def _extract_with_gemini_multimodal(file_path: str, mime_type: str = "image/jpeg") -> str:
    """ใช้ Gemini ดึงข้อความและสรุปข้อมูลจากไฟล์เอกสารหรือรูปภาพ"""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return ""

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = """
กรุณาถอดข้อความและสรุปข้อมูลสำคัญทั้งหมดจากไฟล์นี้:
- ข้อมูลชื่อแบรนด์/บริษัท/ร้าน
- เรื่องราว คอนเซ็ปต์ หรือความเป็นมา
- รายการสินค้า/บริการ พร้อมราคา (ถ้ามี)
- จุดเด่น โปรโมชั่น และเงื่อนไขการให้บริการ
- ช่องทางการติดต่อ เบอร์โทร ที่อยู่ โซเชียลมีเดีย
พิมพ์เนื้อหาเป็นภาษาไทยที่อ่านเข้าใจง่าย เป็นระเบียบ
"""
        # อัปโหลดไฟล์ชั่วคราวผ่าน Gemini Files API หรือส่ง Image
        if mime_type.startswith("image/"):
            from PIL import Image
            img = Image.open(file_path)
            resp = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[prompt, img]
            )
            if resp and resp.text:
                return resp.text.strip()
        else:
            # ใช้ Client Files API สำหรับ PDF
            uploaded = client.files.upload(file=file_path)
            resp = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[uploaded, prompt]
            )
            if resp and resp.text:
                return resp.text.strip()
    except Exception as e:
        print(f"Gemini multimodal extraction error: {e}")

    return ""


def add_document(page_id: str, original_filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """
    บันทึกไฟล์เอกสารลงโฟลเดอร์ของเพจ สกัดข้อความ และบันทึก Metadata
    """
    docs_dir = _get_page_docs_dir(page_id)
    doc_id = f"doc_{int(time.time())}_{os.urandom(3).hex()}"
    
    # ทำความสะอาดชื่อไฟล์
    safe_name = re.sub(r'[\\/*?:"<>|]', "", original_filename).strip()
    save_filename = f"{doc_id}_{safe_name}"
    save_path = os.path.join(docs_dir, save_filename)

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # สกัดข้อความ
    extracted_text = extract_text_from_file(save_path, original_filename)
    
    # สร้างสรุปสั้นๆ (Summary)
    summary = ""
    if extracted_text:
        first_lines = [l.strip() for l in extracted_text.split("\n") if l.strip()]
        summary = " ".join(first_lines[:3])[:200]
    else:
        summary = "ไม่พบข้อความที่สกัดได้ หรือเป็นไฟล์ที่ไม่รองรับ"

    # ขนาดไฟล์แบบอ่านง่าย
    size_bytes = len(file_bytes)
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

    doc_info = {
        "id": doc_id,
        "filename": original_filename,
        "saved_filename": save_filename,
        "file_path": save_path,
        "size": size_str,
        "size_bytes": size_bytes,
        "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "has_text": bool(extracted_text),
        "text_length": len(extracted_text),
        "summary": summary,
        "extracted_text": extracted_text[:10000] # เก็บข้อความสูงสุด 10,000 ตัวอักษร
    }

    docs = load_documents_metadata(page_id)
    docs.append(doc_info)
    save_documents_metadata(page_id, docs)

    return doc_info


def delete_document(page_id: str, doc_id: str) -> bool:
    """ลบเอกสารออกจากระบบ"""
    docs = load_documents_metadata(page_id)
    new_docs = []
    deleted = False

    for d in docs:
        if d.get("id") == doc_id:
            file_path = d.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            deleted = True
        else:
            new_docs.append(d)

    if deleted:
        save_documents_metadata(page_id, new_docs)
    return deleted


def get_all_documents_context(page_id: str, max_chars: int = 5000) -> str:
    """
    รวมเนื้อหาความรู้จากเอกสารที่แนบไว้ทั้งหมดของเพจ สำหรับส่งให้ AI ใช้งาน
    """
    docs = load_documents_metadata(page_id)
    if not docs:
        return ""

    snippets = []
    total_len = 0

    for d in docs:
        txt = d.get("extracted_text", "").strip()
        if txt:
            snippet = f"=== เอกสาร: {d.get('filename')} ===\n{txt}"
            if total_len + len(snippet) > max_chars:
                remaining = max_chars - total_len
                if remaining > 100:
                    snippets.append(snippet[:remaining] + "\n...(ตัดทอน)...")
                break
            snippets.append(snippet)
            total_len += len(snippet)

    return "\n\n".join(snippets)


def analyze_documents_and_extract_brand_dna(page_id: str, current_dna: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    ให้ AI สแกนเอกสารทั้งหมดที่แนบไว้ของแบรนด์นี้ แล้วสกัด/อัปเดตเป็น Brand DNA
    (เรื่องราวแบรนด์, สินค้าหลัก, จุดขาย, กลุ่มเป้าหมาย, โทนเสียง)
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"success": False, "error": "กรุณาระบุ GEMINI_API_KEY ในไฟล์ .env"}

    docs_text = get_all_documents_context(page_id, max_chars=8000)
    if not docs_text.strip():
        return {
            "success": False,
            "error": "ยังไม่มีไฟล์เอกสารที่มีข้อความ กรุณาอัปโหลดเอกสาร (PDF, DOCX, TXT, รูปภาพ) ก่อนสั่งให้ AI วิเคราะห์"
        }

    current_dna = current_dna or {}

    prompt = f"""
คุณเป็น Brand Strategist และ Creative Director ผู้เชี่ยวชาญการสร้างอัตลักษณ์แบรนด์ (Brand DNA)
ด้านล่างนี้คือข้อมูลและเอกสารอ้างอิงของธุรกิจ:

{docs_text}

ข้อมูลแบรนด์ปัจจุบัน (ถ้ามี):
- ชื่อแบรนด์: {current_dna.get('brand_name', '')}
- สโลแกน: {current_dna.get('tagline', '')}
- ประเภทธุรกิจ: {current_dna.get('business_type', '')}
- เรื่องราวแบรนด์เดิม: {current_dna.get('brand_story', '')}

คำสั่ง:
กรุณาวิเคราะห์เอกสารอ้างอิงข้างต้นอย่างละเอียด สกัดและสังเคราะห์ "ตัวตนของแบรนด์ (Brand Identity)" ให้ครบถ้วน ชัดเจน และน่าดึงดูด
โดยตอบกลับเฉพาะ JSON รูปแบบนี้เท่านั้น:

{{
  "brand_name": "ชื่อแบรนด์ที่ถูกต้อง สั้นกระชับ",
  "business_type": "ประเภทธุรกิจแบบชัดเจน (เช่น อาหารกล่องสุขภาพและจัดเลี้ยงสัมมนา)",
  "tagline": "สโลแกนหรือคำนิยามประจำแบรนด์ที่ติดหู",
  "brand_story": "เรื่องราวตัวตนของแบรนด์ (เล่าที่มา ความตั้งใจ ปรัชญา หรือจุดเด่นที่ทำให้แบรนด์นี้พิเศษ ความยาวประมาณ 2-4 บรรทัด)",
  "target_audience": "กลุ่มลูกค้าเป้าหมายที่แท้จริง (เช่น พนักงานออฟฟิศย่านใจกลางเมือง, บริษัทที่จัดสัมมนา, ครอบครัว)",
  "core_services": [
    "สินค้าหรือบริการเด่นที่ 1 (ระบุชื่อเมนู/แพ็กเกจ/ราคา ถ้าพบในเอกสาร)",
    "สินค้าหรือบริการเด่นที่ 2",
    "สินค้าหรือบริการเด่นที่ 3",
    "สินค้าหรือบริการเด่นที่ 4"
  ],
  "selling_points": [
    "จุดขายที่โดดเด่นที่ 1 เช่น วัตถุดิบสดใหม่ไม่ใส่ผงชูรส",
    "จุดขายที่ 2 เช่น ส่งตรงเวลา จัดส่งฟรีในพื้นที่",
    "จุดขายที่ 3 เช่น สั่งล่วงหน้าได้ไม่มีขั้นต่ำ"
  ],
  "tone_of_voice": "น้ำเสียงการสื่อสารที่เหมาะสมกับแบรนด์ (เช่น อบอุ่น เป็นกันเอง ชวนหิว หรือ น่าเชื่อถือ มืออาชีพ รวดเร็ว)",
  "negative_guidelines": "ข้อห้ามหรือสิ่งที่ไม่ควรใช้ในการสื่อสาร (เช่น ไม่โอ้อวดเกินจริง, หลีกเลี่ยงการลดราคาแข่ง)",
  "phone": "เบอร์โทรติดต่อ (ถ้าพบในเอกสาร ให้ดึงมาใส่)",
  "price_tag": "ราคาเริ่มต้นหรือโปรโมชั่นเด่น (ถ้าพบในเอกสาร)"
}}
ตอบเฉพาะ JSON เท่านั้น
"""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        for model_choice in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]:
            try:
                resp = client.models.generate_content(model=model_choice, contents=prompt)
                if resp and resp.text:
                    match = re.search(r"\{.*\}", resp.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        return {
                            "success": True,
                            "brand_dna": data,
                            "model": model_choice
                        }
            except Exception:
                continue

        return {"success": False, "error": "AI ไม่สามารถประมวลผลเอกสารได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง"}
    except Exception as e:
        return {"success": False, "error": str(e)}
