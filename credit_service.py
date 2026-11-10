"""
โมดูลจัดการระบบเครดิตผู้ใช้งาน (Credit & Top-up Service)
รองรับ:
1. ตรวจสอบยอดเครดิตของผู้ใช้แต่ละคน (get_user_credit)
2. หักเครดิตตามประเภทการใช้งาน (deduct_credit) พร้อมรองรับ Admin Bypass (สิทธิ์ไม่จำกัด)
3. เติมเครดิตผู้ใช้และบันทึกประวัติธุรกรรม (topup_credit, admin_adjust_credit)
4. แพ็กเกจราคาเครดิต (CREDIT_PACKAGES)
5. สร้างรหัส QR Code มาตรฐาน Thai PromptPay EMVCo Payload พร้อมคำนวณ CRC16
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

USERS_FILE = "users.json"
CREDIT_TRANSACTIONS_FILE = "credit_transactions.json"

# กำหนดอัตราค่าบริการเครดิต (Pricing Constants)
CREDIT_PRICING = {
    "caption": 1,        # ให้ AI คิดและแต่งแคปชั่น
    "image": 3,          # ให้ AI เจนเนอเรตรูปภาพโฆษณาคมชัดสูง
    "schedule": 1,       # บันทึกโพสต์ลงตารางล่วงหน้า
    "instant_post": 1,   # โพสต์ขึ้นเพจ Facebook ทันที
    "holiday_post": 2    # ให้ AI สร้างและตั้งเวลาโพสต์วันสำคัญ/เทศกาล
}

# รายการแพ็กเกจเติมเครดิต (Credit Packages)
CREDIT_PACKAGES = [
    {
        "id": "pkg_s",
        "name": "Starter Package (S)",
        "price_thb": 100,
        "credits": 100,
        "bonus": 0,
        "badge": "ทดลองใช้งาน",
        "description": "เหมาะสำหรับผู้เริ่มต้นใช้งาน โพสต์ได้ประมาณ 25-50 โพสต์",
        "popular": False
    },
    {
        "id": "pkg_m",
        "name": "Standard Package (M)",
        "price_thb": 300,
        "credits": 350,
        "bonus": 50,
        "badge": "ยอดนิยม คุ้มค่า",
        "description": "แถมฟรี +50 เครดิต! ดูแลเพจได้ต่อเนื่อง 2-4 สัปดาห์",
        "popular": True
    },
    {
        "id": "pkg_l",
        "name": "Pro Business Package (L)",
        "price_thb": 500,
        "credits": 650,
        "bonus": 150,
        "badge": "สุดคุ้ม +150 เครดิต",
        "description": "แถมฟรี +150 เครดิต! สำหรับธุรกิจที่โพสต์ทุกวันตลอดเดือน",
        "popular": False
    },
    {
        "id": "pkg_vip",
        "name": "VIP Enterprise Package",
        "price_thb": 1000,
        "credits": 1500,
        "bonus": 500,
        "badge": "VIP โบนัส 50%",
        "description": "แถมฟรี +500 เครดิตจุใจ! รองรับหลายเพจ และโพสต์วันสำคัญครบปี",
        "popular": False
    }
]

def load_users() -> List[Dict[str, Any]]:
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users: List[Dict[str, Any]]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_transactions() -> List[Dict[str, Any]]:
    if not os.path.exists(CREDIT_TRANSACTIONS_FILE):
        return []
    try:
        with open(CREDIT_TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_transactions(txs: List[Dict[str, Any]]):
    with open(CREDIT_TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, ensure_ascii=False, indent=2)

def get_user_credit(username: str) -> int:
    """ตรวจสอบยอดเครดิตปัจจุบันของผู้ใช้"""
    users = load_users()
    for u in users:
        if u.get("username") == username:
            if u.get("role") == "admin":
                return 999999
            return int(u.get("credits", 0))
    return 0

def record_transaction(
    username: str,
    tx_type: str,
    action: str,
    amount: int,
    balance_after: int,
    description: str = "",
    package_id: Optional[str] = None
) -> Dict[str, Any]:
    """บันทึกประวัติธุรกรรมเครดิตลงไฟล์ credit_transactions.json"""
    txs = load_transactions()
    tx = {
        "id": f"tx_{int(time.time()*1000)}_{username}",
        "username": username,
        "tx_type": tx_type,  # 'deduct', 'topup', 'welcome', 'admin_adjust'
        "action": action,
        "amount": amount,
        "balance_after": balance_after,
        "description": description,
        "package_id": package_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    txs.insert(0, tx)
    if len(txs) > 2000:
        txs = txs[:2000]
    save_transactions(txs)
    return tx

def deduct_credit(
    username: str,
    action: str,
    amount: Optional[int] = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    หักเครดิตผู้ใช้สำหรับการใช้งาน AI หรือการโพสต์
    - ถ้าเป็น admin จะ bypass การหัก (unlimited)
    - ถ้าเครดิตไม่พอจะคืน dict แจ้งเตือน code='insufficient_credits'
    """
    if amount is None:
        amount = CREDIT_PRICING.get(action, 1)

    users = load_users()
    user = next((u for u in users if u.get("username") == username), None)
    if not user:
        return {"success": False, "error": "ไม่พบบัญชีผู้ใช้งานในระบบ", "code": "user_not_found"}

    if user.get("role") == "admin":
        return {
            "success": True,
            "balance": 999999,
            "deducted": 0,
            "unlimited": True,
            "message": "Admin สิทธิ์ไม่จำกัด"
        }

    current_balance = int(user.get("credits", 0))
    if current_balance < amount:
        return {
            "success": False,
            "error": f"เครดิตไม่เพียงพอ (ต้องการ {amount} เครดิต แต่คงเหลือ {current_balance} เครดิต)",
            "code": "insufficient_credits",
            "balance": current_balance,
            "required": amount
        }

    new_balance = current_balance - amount
    user["credits"] = new_balance
    save_users(users)

    desc = description or f"ใช้งานระบบ {action} (-{amount} เครดิต)"
    record_transaction(
        username=username,
        tx_type="deduct",
        action=action,
        amount=-amount,
        balance_after=new_balance,
        description=desc
    )

    return {
        "success": True,
        "balance": new_balance,
        "deducted": amount
    }

def topup_credit(
    username: str,
    amount: int,
    package_id: str,
    note: str = ""
) -> Dict[str, Any]:
    """เติมเครดิตให้ผู้ใช้ตามแพ็กเกจที่ชำระเงิน"""
    users = load_users()
    user = next((u for u in users if u.get("username") == username), None)
    if not user:
        return {"success": False, "error": "ไม่พบบัญชีผู้ใช้งาน"}

    current_balance = int(user.get("credits", 0))
    new_balance = current_balance + amount
    user["credits"] = new_balance
    save_users(users)

    desc = note or f"เติมเครดิตแพ็กเกจ {package_id} (+{amount} เครดิต)"
    record_transaction(
        username=username,
        tx_type="topup",
        action="topup",
        amount=amount,
        balance_after=new_balance,
        description=desc,
        package_id=package_id
    )

    return {
        "success": True,
        "balance": new_balance,
        "added": amount,
        "package_id": package_id
    }

def admin_adjust_credit(
    target_username: str,
    amount: int,
    reason: str = ""
) -> Dict[str, Any]:
    """Admin ปรับยอดเครดิตให้ผู้ใช้โดยตรง"""
    users = load_users()
    user = next((u for u in users if u.get("username") == target_username), None)
    if not user:
        return {"success": False, "error": "ไม่พบผู้ใช้ที่ต้องการปรับยอด"}

    current_balance = int(user.get("credits", 0))
    new_balance = max(0, current_balance + amount)
    user["credits"] = new_balance
    save_users(users)

    desc = reason or f"ผู้ดูแลระบบปรับปรุงยอดเครดิต ({'+' if amount >= 0 else ''}{amount} เครดิต)"
    record_transaction(
        username=target_username,
        tx_type="admin_adjust",
        action="adjust",
        amount=amount,
        balance_after=new_balance,
        description=desc
    )

    return {
        "success": True,
        "username": target_username,
        "balance": new_balance,
        "adjusted": amount
    }

def get_user_transactions(username: str, limit: int = 50) -> List[Dict[str, Any]]:
    """ดึงประวัติธุรกรรมเครดิตของผู้ใช้คนนั้นๆ"""
    txs = load_transactions()
    user_txs = [t for t in txs if t.get("username") == username]
    return user_txs[:limit]

# ================= PROMPTPAY EMVCO QR PAYLOAD GENERATOR =================

def crc16_ccitt(data: str) -> str:
    """คำนวณ CRC16-CCITT (Polynomial 0x1021, Initial Value 0xFFFF) ตามมาตรฐาน EMVCo"""
    crc = 0xFFFF
    for byte in data.encode("utf-8"):
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def generate_promptpay_payload(promptpay_id: str, amount: float = 0.0) -> str:
    """
    สร้างมาตรฐานสตริง EMVCo Thai PromptPay QR Code
    - promptpay_id: เบอร์มือถือ 10 หลัก (เช่น 0660971257) หรือ เลขประจำตัวผู้เสียภาษี 13 หลัก
    - amount: ยอดเงินบาทที่ต้องการให้สแกน (ถ้ามี)
    """
    clean_id = "".join(c for c in promptpay_id if c.isdigit())
    
    # AID Thai PromptPay: A000000677010111
    subtag00 = "0016A000000677010111"
    
    if len(clean_id) == 10 and clean_id.startswith("0"):
        # เบอร์มือถือแปลงเป็น 0066 + 9 หลักหลัง
        formatted_mobile = f"0066{clean_id[1:]}"
        subtag_id = f"0113{formatted_mobile}"
    elif len(clean_id) == 13:
        # เลขประจำตัวผู้เสียภาษี / บัตรประชาชน 13 หลัก
        subtag_id = f"0213{clean_id}"
    else:
        subtag_id = f"01{len(clean_id):02d}{clean_id}"

    tag29_value = subtag00 + subtag_id
    tag29 = f"29{len(tag29_value):02d}{tag29_value}"
    
    # Payload Format Indicator (00) = 01
    tag00 = "000201"
    # Point of Initiation Method: 12 (Dynamic QR พร้อมยอดเงิน) หรือ 11 (Static QR)
    tag01 = "010212" if amount > 0 else "010211"
    # Currency: 764 (THB)
    tag53 = "5303764"
    # Country Code: TH
    tag58 = "5802TH"
    
    raw = tag00 + tag01 + tag29 + tag53
    if amount > 0:
        amt_str = f"{amount:.2f}"
        tag54 = f"54{len(amt_str):02d}{amt_str}"
        raw += tag54
        
    raw += tag58
    # Tag 63: Checksum Length = 04
    raw += "6304"
    
    checksum = crc16_ccitt(raw)
    return raw + checksum
