"""
โปรแกรมจัดการสร้างคอนเทนต์และโพสต์ Facebook อัตโนมัติ (FixPack Auto-Pilot System)
"""
import os
import sys
from datetime import datetime, timedelta

# บังคับให้ Console บน Windows รองรับภาษาไทยและ Emoji แบบ UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from dotenv import load_dotenv
from facebook_service import FacebookPoster
from content_generator import create_facebook_post_content
from create_ai_banner import create_ai_technician_banner
from scheduler_engine import (
    load_schedule,
    save_schedule,
    add_scheduled_post,
    run_autopilot_service,
    DEFAULT_DAILY_TIME,
    SCHEDULE_FILE
)
import webbrowser

import pages_manager

def sync_token_cli():
    print("\n🔑 ใส่ Access Token จาก Facebook Graph API Explorer")
    print("💡 สามารถวางได้ทั้ง User Token หรือ Page Token")
    print("   ระบบจะดึงรายชื่อเพจและ Page Token ของทุกเพจ บันทึกลงไฟล์ .env ให้อัตโนมัติทันที!")
    token = input("\n👉 วาง Token ที่นี่: ").strip()
    if not token:
        print("❌ ยกเลิก")
        return
    print("\n⏳ กำลังเชื่อมต่อ Facebook API และอัปเดต .env...")
    res = pages_manager.auto_setup_token(token)
    if res["success"]:
        print("------------------------------------------------------")
        print(f"🎉 ซิงค์สำเร็จ! พบทั้งหมด {res['count']} เพจ")
        print(f"🎯 เพจที่เปิดใช้งานอยู่: {res.get('active_page', {}).get('name')}")
        print("✅ ข้อมูล FACEBOOK_PAGE_ID และ FACEBOOK_PAGE_ACCESS_TOKEN ถูกบันทึกลง .env เรียบร้อยแล้ว!")
        print("------------------------------------------------------")
    else:
        print(f"❌ เกิดข้อผิดพลาด: {res.get('error')}")

def switch_page_cli():
    print("\n🔄 สลับเพจ Facebook ที่ต้องการจัดการ:")
    pages = pages_manager.get_all_pages()
    active = pages_manager.get_active_page()
    active_id = str(active.get("id")) if active else ""

    print("-" * 65)
    for idx, p in enumerate(pages, 1):
        is_cur = "⭐ (กำลังใช้งาน)" if str(p.get("id")) == active_id else ""
        print(f"[{idx}] {p.get('name')} {is_cur}")
        print(f"    หมวดหมู่: {p.get('category')} | Page ID: {p.get('id')}")
    print("-" * 65)

    sel = input("👉 เลือกหมายเลขเพจที่ต้องการสลับ (หรือกด Enter เพื่อยกเลิก): ").strip()
    if sel.isdigit():
        idx = int(sel) - 1
        if 0 <= idx < len(pages):
            chosen = pages[idx]
            pages_manager.set_active_page(chosen["id"])
            print(f"✅ สลับไปยังเพจ '{chosen['name']}' เรียบร้อยแล้ว!")
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง")
    print("\n🌐 กำลังเปิดเว็บแดชบอร์ด FixPack Auto-Pilot...")
    url = "http://127.0.0.1:5050"
    try:
        webbrowser.open(url)
    except Exception:
        pass
    from web_app import run_server
    run_server(port=5050)

load_dotenv()

def print_banner():
    print("""
======================================================
  📢 FIXPACK FACEBOOK AUTO-PILOT & CONTENT SYSTEM 🚀
======================================================
    """)

def check_connection():
    print("\n🔍 กำลังตรวจสอบการเชื่อมต่อกับ Facebook Page...")
    poster = FacebookPoster()
    res = poster.validate_credentials()
    if res["success"]:
        print("------------------------------------------------------")
        print(f"✅ เชื่อมต่อสำเร็จ!")
        print(f"📌 ชื่อเพจ: {res.get('page_name')}")
        print(f"🆔 Page ID: {res.get('page_id')}")
        print(f"📂 หมวดหมู่: {res.get('category')}")
        print("------------------------------------------------------")
        return True
    else:
        print("------------------------------------------------------")
        print(f"❌ เชื่อมต่อไม่สำเร็จ: {res.get('error')}")
        print("💡 โปรดตรวจสอบค่า FACEBOOK_PAGE_ID และ FACEBOOK_PAGE_ACCESS_TOKEN ในไฟล์ .env")
        print("------------------------------------------------------")
        return False

def view_schedule():
    print("\n📅 ตารางรายการโพสต์ล่วงหน้า (Content Calendar):")
    posts = load_schedule()
    if not posts:
        print("ℹ️ ยังไม่มีรายการโพสต์ที่ตั้งเวลาไว้ (ระบบจะใช้ AI คิดหัวข้อให้อัตโนมัติเมื่อถึงเวลา)")
        return

    print("-" * 75)
    print(f"{'วันที่':<12} {'เวลา':<8} {'สถานะ':<10} {'หัวข้อ / รายละเอียด'}")
    print("-" * 75)
    for idx, p in enumerate(posts, 1):
        d = p.get("date", "-")
        t = p.get("time", "-")
        st = p.get("status", "pending")
        topic = p.get("topic") or (p.get("content", "")[:35] + "..." if p.get("content") else "💡 ให้ AI คิดหัวข้อให้เอง")
        
        status_icon = "⏳ รอโพสต์" if st == "pending" else ("✅ โพสต์แล้ว" if st == "posted" else "❌ ผิดพลาด")
        print(f"[{idx}] {d:<10} {t:<8} {status_icon:<10} {topic}")
    print("-" * 75)

def add_schedule_interactive():
    print("\n➕ เพิ่มโพสต์ล่วงหน้าใหม่")
    
    # 1. วันที่
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"💡 ตัวอย่าง: วันนี้ ({today_str}), พรุ่งนี้ ({tomorrow_str}) หรือระบุ YYYY-MM-DD")
    date_input = input(f"👉 ระบุวันที่ (กด Enter เพื่อใช้วันพรุ่งนี้ {tomorrow_str}): ").strip()
    if not date_input:
        date_input = tomorrow_str

    # 2. เวลา
    time_input = input("👉 ระบุเวลาโพสต์ (HH:MM เช่น 09:30, 18:00) [ค่าเริ่มต้น: 09:30]: ").strip() or "09:30"

    # 3. รูปแบบเนื้อหา
    print("\nเลือกรูปแบบเนื้อหา:")
    print("1. พิมพ์ข้อความแคปชั่นเองทั้งหมด")
    print("2. ระบุหัวข้อ แล้วให้ AI แต่งโพสต์ให้")
    print("3. ไม่ระบุอะไรเลย ให้ AI สุ่มคิดหัวข้อและเขียนให้เองทั้งหมด")
    c_choice = input("👉 เลือกรูปแบบ (1, 2 หรือ 3): ").strip()

    custom_content = ""
    custom_topic = ""

    if c_choice == "1":
        print("👉 พิมพ์ข้อความแคปชั่นที่ต้องการ (เสร็จแล้วกด Enter):")
        custom_content = input().strip()
    elif c_choice == "2":
        custom_topic = input("👉 ระบุหัวข้อที่ต้องการให้ AI เขียน: ").strip()
    else:
        print("✨ ระบบจะสุ่มเลือกหัวข้องานช่าง FixPack และเขียนโพสต์ให้อัตโนมัติ")

    # 4. รูปภาพ
    img_choice = input("👉 ต้องการแนบรูปแบนเนอร์ช่าง AI FixPack หรือไม่? (y/n) [ค่าเริ่มต้น: y]: ").strip().lower()
    img_path = "fixpack_ai_banner.png" if img_choice != "n" else ""

    item = add_scheduled_post(
        date_str=date_input,
        time_str=time_input,
        content=custom_content,
        topic=custom_topic,
        image_path=img_path
    )
    print(f"\n✅ บันทึกโพสต์ล่วงหน้าเรียบร้อยแล้ว! (กำหนดโพสต์: {date_input} เวลา {time_input} น.)")

def delete_schedule_interactive():
    view_schedule()
    posts = load_schedule()
    if not posts:
        return
    
    del_idx = input("\n👉 ระบุหมายเลขข้อที่ต้องการลบ (หรือกด Enter เพื่อยกเลิก): ").strip()
    if del_idx.isdigit():
        idx = int(del_idx) - 1
        if 0 <= idx < len(posts):
            removed = posts.pop(idx)
            save_schedule(posts)
            print(f"🗑️ ลบรายการวันที่ {removed.get('date')} เวลา {removed.get('time')} เรียบร้อยแล้ว")
        else:
            print("❌ ไม่พบหมายเลขข้อดังกล่าว")

def preview_post():
    print("\n✍️ สร้างเนื้อหาโพสต์ตัวอย่าง (Preview)")
    topic = input("👉 ระบุหัวข้อที่ต้องการ (กด Enter เพื่อให้ AI เลือกหัวข้อแนะนำ): ").strip()
    if not topic:
        topic = "บริการช่างซ่อมแซมบ้าน FixPack"
    
    print("\n⏳ กำลังสร้างเนื้อหาโพสต์...")
    content = create_facebook_post_content(topic=topic, product="FixPack งานเล็กซ่อมครบจบในแพ็กเดียว")

    print("\n" + "="*50)
    print("📝 ตัวอย่างโพสต์ที่จะได้:")
    print("="*50)
    print(content)
    print("="*50)
    return content

def post_now():
    content = preview_post()
    attach_img = input("\n🎨 ต้องการแนบรูปภาพแบนเนอร์ช่าง AI ตาม CI แบรนด์ไปด้วยหรือไม่? (y/n) [ค่าเริ่มต้น: y]: ").strip().lower()
    if attach_img != "n":
        img_path = "fixpack_ai_banner.png"
        if not os.path.exists(img_path):
            print("\n⏳ กำลังสร้างรูปภาพแบนเนอร์ CI แบรนด์อัตโนมัติ...")
            create_ai_technician_banner()
    else:
        img_path = None

    confirm = input("\n🚀 ต้องการโพสต์ลงเพจ FixPack จริงทันทีหรือไม่? (y/n): ").strip().lower()
    if confirm == "y":
        poster = FacebookPoster()
        print("\n⏳ กำลังส่งข้อมูลไปยัง Facebook Page...")
        if img_path and os.path.exists(img_path):
            result = poster.post_image(img_path, caption=content)
        else:
            result = poster.post_text(content)

        if result["success"]:
            print(f"✅ โพสต์สำเร็จเรียบร้อยแล้ว!")
            print(f"🔗 ลิงก์โพสต์: {result['url']}")
        else:
            print(f"❌ เกิดข้อผิดพลาด: {result.get('error')}")
    else:
        print("🚫 ยกเลิกการโพสต์")

def generate_ci_banner_menu():
    print("\n🎨 สร้างรูปภาพประกอบโพสต์ตาม CI แบรนด์ FixPack")
    hl = input("👉 พาดหัวบนการ์ด (กด Enter เพื่อใช้ 'เลือกซ่อมได้เอง 3 งานในบ้าน'): ").strip() or "เลือกซ่อมได้เอง 3 งานในบ้าน"
    sub = input("👉 รายละเอียดย่อย (กด Enter เพื่อใช้ 'ไฟฟ้า • ประปา • ประตูหน้าต่าง • ติดตั้ง'): ").strip() or "ไฟฟ้า • ประปา • ประตูหน้าต่าง • ติดตั้ง"
    price = input("👉 ราคาโปรโมชั่น (กด Enter เพื่อใช้ 'เหมาจ่าย 1,500.-'): ").strip() or "เหมาจ่าย 1,500.-"
    
    print("\n⏳ กำลังสร้างรูปภาพแบนเนอร์ 1080x1080...")
    out = create_ai_technician_banner(headline=hl, subheadline=sub, price=price)
    if out:
        print(f"🎉 สร้างสำเร็จ! บันทึกไว้ที่ไฟล์: {out}")

def launch_web_app():
    print("\n🌐 กำลังเปิดเว็บแดชบอร์ด FixPack Auto-Pilot...")
    url = "http://127.0.0.1:5050"
    try:
        webbrowser.open(url)
    except Exception:
        pass
    from web_app import run_server
    run_server(port=5050)

def main():
    print_banner()

    # ตรวจสอบไฟล์ .env
    if not os.path.exists(".env"):
        print("⚠️ ไม่พบไฟล์ .env ระบบกำลังสร้างไฟล์ .env จาก .env.example ให้...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r", encoding="utf-8") as f_src:
                with open(".env", "w", encoding="utf-8") as f_dst:
                    f_dst.write(f_src.read())
            print("✅ สร้างไฟล์ .env เรียบร้อยแล้ว")

    while True:
        print("\nเมนูการใช้งาน:")
        print("1. 📅 ดูตารางโพสต์ล่วงหน้า (Content Calendar)")
        print("2. ➕ เพิ่มโพสต์ล่วงหน้า (กำหนดวัน, เวลา, ข้อความ หรือให้ AI ช่วย)")
        print("3. 🗑️ ลบโพสต์ล่วงหน้า")
        print("4. 🤖 เริ่มระบบโพสต์อัตโนมัติ (Auto-Pilot 24 ชม. - วันไหนไม่ใส่ AI คิดให้เอง)")
        print("5. 🚀 สร้างโพสต์ + แนบรูป AI และโพสต์ลงเพจทันที (Post Now)")
        print("6. 🎨 ปรับแต่งสร้างรูปภาพแบนเนอร์ช่าง AI ใหม่ (1080x1080)")
        print("7. 🔍 ตรวจสอบการเชื่อมต่อ Facebook Page")
        print("8. 🔄 สลับเพจที่กำลังจัดการ (Switch Active Page - อัปเดต .env อัตโนมัติ)")
        print("9. 🔑 ใส่ Facebook Token เพื่อตั้งค่า .env และซิงค์เพจทั้งหมดอัตโนมัติ")
        print("10. 🌐 เปิดเว็บแดชบอร์ด FixPack Web App (UI สวยงาม รองรับหลายผู้ใช้)")
        print("11. 🚪 ออกจากโปรแกรม")

        choice = input("\n👉 กรุณาเลือกตัวเลือก (1-11): ").strip()

        if choice == "1":
            view_schedule()
        elif choice == "2":
            add_schedule_interactive()
        elif choice == "3":
            delete_schedule_interactive()
        elif choice == "4":
            run_autopilot_service()
        elif choice == "5":
            post_now()
        elif choice == "6":
            generate_ci_banner_menu()
        elif choice == "7":
            check_connection()
        elif choice == "8":
            switch_page_cli()
        elif choice == "9":
            sync_token_cli()
        elif choice == "10":
            launch_web_app()
        elif choice == "11":
            print("\n👋 ขอบคุณที่ใช้งานครับ!")
            sys.exit(0)
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง กรุณาเลือก 1-11")

if __name__ == "__main__":
    main()
