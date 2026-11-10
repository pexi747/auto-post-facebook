"""
โมดูล Universal AI Client Resolver สำหรับ FixPack Facebook Auto-Pilot
รองรับ 2 โหมดหลัก:
1. Free Tier: Google Gemini 1.5 Flash (100% ฟรี out of the box ผ่านระบบ GEMINI_API_KEY)
2. Customer Mode (Bring Your Own AI - BYO AI):
   - Google Gemini: gemini-1.5-flash, gemini-1.5-pro, gemini-2.5-flash, gemini-3.5-flash, gemini-3.8-flash
   - OpenAI: gpt-4o, gpt-4o-mini, o1-mini
   - Anthropic Claude: claude-3-7-sonnet, claude-3-5-haiku
   - DeepSeek: deepseek-chat (V3), deepseek-reasoner (R1)
   - Custom: OpenAI-compatible endpoints (OpenRouter, Groq, Together AI, Ollama, etc.)
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

USERS_FILE = "users.json"

PROVIDER_MODELS = {
    "gemini": [
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash (รวดเร็ว ประหยัด)", "default": True},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro (ฉลาด ละเอียด)"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash (ความเร็วสูง)"},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash"},
        {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash"},
        {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite"}
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (โมเดลเรือธง ฉลาดรอบด้าน)", "default": True},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (ไว คุ้มค่า ประหยัดต้นทุน)"},
        {"id": "o1-mini", "name": "o1-mini (Reasoning Model)"}
    ],
    "claude": [
        {"id": "claude-3-7-sonnet", "name": "Claude 3.7 Sonnet (เขียนสำนวนสละสลวย)", "default": True},
        {"id": "claude-3-5-haiku", "name": "Claude 3.5 Haiku (รวดเร็ว ทันใจ)"}
    ],
    "deepseek": [
        {"id": "deepseek-chat", "name": "DeepSeek-V3 (Chat) - ฉลาด คุ้มราคา", "default": True},
        {"id": "deepseek-reasoner", "name": "DeepSeek-R1 (Reasoner) - คิดวิเคราะห์ลึกซึ้ง"}
    ],
    "custom": [
        {"id": "custom-model", "name": "โมเดลตามที่ Base URL กำหนด", "default": True}
    ]
}

def mask_api_key(api_key: Optional[str]) -> str:
    """ซ่อนรหัส API Key บางส่วนเพื่อความปลอดภัย เช่น sk-••••••1234"""
    if not api_key:
        return ""
    key = str(api_key).strip()
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:4]}••••••••{key[-4:]}"

def get_user_ai_config(username: str) -> Dict[str, Any]:
    """
    อ่านค่าการตั้งค่า AI ของผู้ใช้จาก users.json
    ค่าเริ่มต้น: โหมดฟรี gemini-1.5-flash
    """
    default_config = {
        "mode": "free",
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "api_key": "",
        "base_url": ""
    }
    if not os.path.exists(USERS_FILE):
        return default_config
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        for u in users:
            if u.get("username") == username:
                cfg = u.get("ai_config") or {}
                merged = dict(default_config)
                merged.update({k: v for k, v in cfg.items() if v is not None})
                return merged
    except Exception as e:
        print(f"⚠️ Error reading ai_config for {username}: {e}")
    return default_config

def save_user_ai_config(username: str, config: Dict[str, Any]) -> bool:
    """
    บันทึกการตั้งค่า AI ของผู้ใช้ลงใน users.json
    คงค่า api_key เดิมไว้หากส่งค่า mask เข้ามา
    """
    if not os.path.exists(USERS_FILE):
        return False
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        target = None
        for u in users:
            if u.get("username") == username:
                target = u
                break
        if not target:
            return False

        existing_cfg = target.get("ai_config") or {}
        new_api_key = (config.get("api_key") or "").strip()
        # ถ้าส่ง mask มา หรือไม่ได้ระบุ ให้ใช้ Key เดิมที่มีอยู่
        if ("••••" in new_api_key) or (not new_api_key and existing_cfg.get("api_key")):
            new_api_key = existing_cfg.get("api_key", "")

        target["ai_config"] = {
            "mode": config.get("mode", "free"),
            "provider": config.get("provider", "gemini"),
            "model": config.get("model", "gemini-1.5-flash"),
            "api_key": new_api_key,
            "base_url": (config.get("base_url") or "").strip(),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Error saving ai_config for {username}: {e}")
        return False

# ================= PROVIDER REST HANDLERS =================

def _call_gemini(prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> str:
    """เรียกใช้ Google Gemini ผ่าน google.genai SDK หรือ REST API พร้อม Fast Fallback"""
    # จัดลำดับโมเดล: หากเป็น gemini-1.5-flash ให้ใช้โมเดลกลุ่ม Flash ที่กำลังให้บริการเป็นแกนนำ
    if model in ["gemini-1.5-flash", "gemini-2.5-flash"]:
        candidate_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash", model]
    else:
        candidate_models = [model, "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]

    # 1. ลองผ่าน google.genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for m in candidate_models:
            try:
                resp = client.models.generate_content(model=m, contents=prompt)
                if resp and resp.text:
                    return resp.text.strip()
            except Exception:
                continue
    except Exception:
        pass

    # 2. Fallback to Google Gemini REST API v1beta
    for m in candidate_models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            body = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            data_bytes = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            continue
    return ""

def _call_openai(prompt: str, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None) -> str:
    """เรียกใช้ OpenAI /chat/completions"""
    endpoint = f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "model": model or "gpt-4o",
        "messages": [{"role": "user", "content": prompt}]
    }
    if not str(model).startswith("o1"):
        payload["temperature"] = 0.7

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        choices = res_data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
    return ""

def _call_claude(prompt: str, api_key: str, model: str = "claude-3-7-sonnet") -> str:
    """เรียกใช้ Anthropic Claude /v1/messages"""
    endpoint = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": model or "claude-3-7-sonnet",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        content_list = res_data.get("content", [])
        if content_list:
            return content_list[0].get("text", "").strip()
    return ""

def _call_deepseek(prompt: str, api_key: str, model: str = "deepseek-chat", base_url: Optional[str] = None) -> str:
    """เรียกใช้ DeepSeek REST API"""
    endpoint = f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model or "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        choices = res_data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
    return ""

def _call_custom(prompt: str, api_key: str, model: str = "default", base_url: str = "") -> str:
    """เรียกใช้ Custom OpenAI-Compatible Base URL (Groq, Together, Ollama, OpenRouter)"""
    url = (base_url or "").strip().rstrip("/")
    if not url:
        raise ValueError("กรุณาระบุ Base URL สำหรับ Custom Provider")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model or "default",
        "messages": [{"role": "user", "content": prompt}]
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=45) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        choices = res_data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
    return ""

# ================= PUBLIC AI DISPATCHER =================

def call_ai_completion(
    prompt: str,
    user_config: Optional[Dict[str, Any]] = None,
    system_free: bool = True
) -> str:
    """
    ฟังก์ชันแกนกลางสำหรับการเรียก AI สร้างข้อความ:
    - หาก user_config เป็น mode == 'custom': จะยิงตาม Provider, Model, API Key ของลูกค้า
    - หากเป็น mode == 'free' หรือ Custom ล้มเหลวและ system_free == True: ใช้ Gemini 1.5 Flash ฟรีของระบบ
    """
    mode = (user_config or {}).get("mode", "free")
    
    if mode == "custom" and user_config:
        provider = user_config.get("provider", "gemini").lower()
        api_key = (user_config.get("api_key") or "").strip()
        model = user_config.get("model") or "gemini-1.5-flash"
        base_url = (user_config.get("base_url") or "").strip()

        try:
            if provider == "gemini" and api_key:
                res = _call_gemini(prompt, api_key=api_key, model=model)
                if res:
                    return res
            elif provider == "openai" and api_key:
                res = _call_openai(prompt, api_key=api_key, model=model, base_url=base_url)
                if res:
                    return res
            elif provider == "claude" and api_key:
                res = _call_claude(prompt, api_key=api_key, model=model)
                if res:
                    return res
            elif provider == "deepseek" and api_key:
                res = _call_deepseek(prompt, api_key=api_key, model=model, base_url=base_url)
                if res:
                    return res
            elif provider == "custom":
                res = _call_custom(prompt, api_key=api_key, model=model, base_url=base_url)
                if res:
                    return res
        except Exception as e:
            print(f"⚠️ BYO AI error ({provider}/{model}): {e}. Falling back to System Free Gemini.")

    if not system_free:
        return ""

    # ================= SYSTEM FREE TIER (Gemini 1.5 Flash) =================
    sys_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not sys_key:
        return ""

    return _call_gemini(prompt, api_key=sys_key, model="gemini-1.5-flash")

def test_ai_connection(
    provider: str,
    api_key: str,
    model: str,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    ทดสอบการเชื่อมต่อ API ของผู้ใช้ และจับเวลา Latency (ms)
    """
    prov = (provider or "gemini").lower().strip()
    key = (api_key or "").strip()
    mdl = (model or "").strip()
    b_url = (base_url or "").strip() or None

    test_prompt = "ทดสอบการเชื่อมต่อระบบ FixPack AI กรุณาตอบกลับเฉพาะคำว่า 'เชื่อมต่อสำเร็จ' สั้นๆ"
    t0 = time.time()

    try:
        reply = ""
        if prov == "gemini":
            if not key:
                return {"success": False, "error": "กรุณาระบุ Google Gemini API Key"}
            reply = _call_gemini(test_prompt, api_key=key, model=mdl or "gemini-1.5-flash")
        elif prov == "openai":
            if not key:
                return {"success": False, "error": "กรุณาระบุ OpenAI API Key"}
            reply = _call_openai(test_prompt, api_key=key, model=mdl or "gpt-4o-mini", base_url=b_url)
        elif prov == "claude":
            if not key:
                return {"success": False, "error": "กรุณาระบุ Anthropic API Key"}
            reply = _call_claude(test_prompt, api_key=key, model=mdl or "claude-3-5-haiku")
        elif prov == "deepseek":
            if not key:
                return {"success": False, "error": "กรุณาระบุ DeepSeek API Key"}
            reply = _call_deepseek(test_prompt, api_key=key, model=mdl or "deepseek-chat", base_url=b_url)
        elif prov == "custom":
            if not b_url:
                return {"success": False, "error": "กรุณาระบุ Base URL สำหรับ Custom Endpoint"}
            reply = _call_custom(test_prompt, api_key=key, model=mdl or "default", base_url=b_url)
        else:
            return {"success": False, "error": f"ไม่รองรับ Provider '{prov}'"}

        latency_ms = round((time.time() - t0) * 1000, 1)

        if reply:
            return {
                "success": True,
                "provider": prov,
                "model": mdl,
                "latency_ms": latency_ms,
                "reply": reply[:100]
            }
        else:
            return {
                "success": False,
                "error": "AI ไม่ส่งข้อความตอบกลับ กรุณาตรวจสอบสิทธิ์ของ Key หรือ Model ID",
                "latency_ms": latency_ms
            }

    except urllib.error.HTTPError as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        err_msg = f"HTTP Error {e.code}: {e.reason}"
        try:
            detail = json.loads(e.read().decode("utf-8"))
            if "error" in detail:
                err_msg = f"{err_msg} ({detail['error'].get('message') or detail['error']})"
        except Exception:
            pass
        return {"success": False, "error": err_msg, "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {"success": False, "error": str(e), "latency_ms": latency_ms}

