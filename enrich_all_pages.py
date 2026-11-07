import os
import sys
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from brand_knowledge_engine import fetch_raw_facebook_page_data, synthesize_brand_dna_with_ai

def enrich_all():
    file_path = "managed_pages.json"
    if not os.path.exists(file_path):
        print("❌ ไม่พบไฟล์ managed_pages.json")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pages = data.get("pages", [])
        total = len(pages)
        print(f"🚀 เริ่มต้นการศึกษาข้อมูลแบรนด์ทั้ง {total} เพจด้วย AI...")

        for i, p in enumerate(pages, 1):
            try:
                pid = p.get("id")
                name = p.get("name")
                token = p.get("access_token")

                if not token:
                    continue

                if p.get("brand_dna") and p.get("brand_dna", {}).get("core_services"):
                    print(f"[{i}/{total}] ⏩ มีข้อมูลแล้ว: {p.get('brand_name') or name}")
                    continue

                print(f"[{i}/{total}] 🔍 กำลังดึงข้อมูลและศึกษาแบรนด์: '{name}'...")
                # ดึงข้อมูลดิบจาก Facebook
                raw = fetch_raw_facebook_page_data(pid, token)

                # ให้ Gemini สังเคราะห์ Brand DNA
                dna = synthesize_brand_dna_with_ai(name, raw, p)
                if dna:
                    p["brand_dna"] = dna
                    p["brand_name"] = dna.get("brand_name") or p.get("brand_name") or name
                    p["business_type"] = dna.get("business_type") or p.get("category")
                    p["tagline"] = dna.get("tagline") or p.get("tagline")
                    p["target_audience"] = dna.get("target_audience")
                    p["core_services"] = dna.get("core_services", [])
                    p["selling_points"] = dna.get("selling_points", [])
                    p["tone_of_voice"] = dna.get("tone_of_voice")
                    p["sample_hooks"] = dna.get("sample_hooks", [])
                    p["sample_hashtags"] = dna.get("hashtags", [])
                    if dna.get("price_tag"):
                        p["price_tag"] = dna.get("price_tag")
                    if dna.get("primary_color"):
                        p["primary_color"] = dna.get("primary_color")
                    if dna.get("accent_color"):
                        p["accent_color"] = dna.get("accent_color")
                    print(f"[{i}/{total}] ✅ สำเร็จ: {p['brand_name']}")
                else:
                    print(f"[{i}/{total}] ⚠️ สังเคราะห์ไม่สำเร็จ: {name}")

                # บันทึกลงไฟล์
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                time.sleep(1)
            except Exception as item_err:
                print(f"⚠️ Error on page {i}: {item_err}")
                continue
    except Exception as overall_err:
        print(f"❌ Overall error: {overall_err}")
        with open("enrich_error.log", "w", encoding="utf-8") as err_f:
            err_f.write(str(overall_err))

if __name__ == "__main__":
    enrich_all()
