"""
โมดูลสำหรับตั้งเวลาโพสต์ Facebook อัตโนมัติ (Scheduler)
"""
import time
import os
import sys

# รองรับ UTF-8 สำหรับ Windows Console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import schedule
from dotenv import load_dotenv
from facebook_service import FacebookPoster
from content_generator import create_facebook_post_content

load_dotenv()

def scheduled_job():
    """งานที่จะถูกเรียกเมื่อถึงเวลาที่กำหนด"""
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⏰ เริ่มต้นกระบวนการสร้างและโพสต์อัตโนมัติ...")
    
    # ดึงหัวข้อที่เข้ากับบริการของ FixPack
    default_topics = [
        "แก้ปัญหาก๊อกน้ำรั่ว ท่อน้ำตัน ซ่อมจบไม่บานปลาย",
        "ตรวจเช็คระบบไฟในบ้าน ป้องกันไฟลัดวงจร",
        "รวมงานช่างเล็กๆ ในบ้านที่คุณไม่ต้องเหนื่อยทำเอง",
        "ข้อดีของการซ่อมบ้านแบบเหมาจบในแพ็กเดียว",
        "ดูแลบ้านรับหน้าฝน จุดไหนบ้างที่ควรตรวจเช็คด่วน"
    ]
    import random
    topic = random.choice(default_topics)
    
    print(f"📝 กำลังสร้างเนื้อหาสำหรับหัวข้อ: {topic}")
    content = create_facebook_post_content(topic=topic)
    
    print("-----------------------------------------")
    print(content)
    print("-----------------------------------------")
    
    poster = FacebookPoster()
    img_path = "fixpack_ai_banner.png"
    if os.path.exists(img_path):
        print(f"🖼️ แนบรูปภาพแบนเนอร์ CI แบรนด์: {img_path}")
        result = poster.post_image(img_path, caption=content)
    else:
        result = poster.post_text(content)
    
    if result["success"]:
        print(f"✅ โพสต์สำเร็จเรียบร้อย! ดูโพสต์ได้ที่: {result['url']}")
    else:
        print(f"❌ โพสต์ไม่สำเร็จ: {result.get('error')}")

def start_scheduler(schedule_time: str = "09:00", interval_hours: int = 0):
    """
    เริ่มต้นรัน Scheduler
    :param schedule_time: เวลาที่ต้องการโพสต์ทุกวัน เช่น "09:00" หรือ "18:30"
    :param interval_hours: ถ้ามากกว่า 0 จะโพสต์ทุกๆ N ชั่วโมง
    """
    if interval_hours > 0:
        print(f"🚀 ตั้งเวลาระบบ: จะโพสต์อัตโนมัติทุกๆ {interval_hours} ชั่วโมง")
        schedule.every(interval_hours).hours.do(scheduled_job)
    else:
        print(f"🚀 ตั้งเวลาระบบ: จะโพสต์อัตโนมัติทุกวันเวลา {schedule_time} น.")
        schedule.every().day.at(schedule_time).do(scheduled_job)

    print("ℹ️ กด Ctrl+C เพื่อหยุดการทำงานของระบบตั้งเวลา\n")
    
    # รันทันที 1 ครั้งเพื่อทดสอบ (ถ้าต้องการ สามารถเปิดได้)
    # scheduled_job()

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    start_scheduler(schedule_time="09:00")
