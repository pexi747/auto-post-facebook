import os
import sys
import json
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv(override=True)

def fetch_facebook_page_details(page_id: str, access_token: str) -> dict:
    """ดึงข้อมูลเชิงลึกของเพจจาก Facebook Graph API"""
    url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "fields": "about,description,bio,category,phone,website,single_line_address,emails",
        "access_token": access_token
    }
    details = {}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            details = r.json()
    except Exception as e:
        print(f"Error fetching profile for {page_id}: {e}")

    # ดึงตัวอย่างโพสต์ล่าสุด 3-5 โพสต์
    feed_url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    feed_params = {
        "fields": "message,created_time",
        "limit": 5,
        "access_token": access_token
    }
    posts = []
    try:
        r_feed = requests.get(feed_url, params=feed_params, timeout=10)
        if r_feed.status_code == 200:
            items = r_feed.json().get("data", [])
            for item in items:
                msg = item.get("message", "").strip()
                if msg:
                    posts.append(msg)
    except Exception as e:
        print(f"Error fetching feed for {page_id}: {e}")

    details["recent_posts"] = posts[:3]
    return details

if __name__ == "__main__":
    data = json.load(open("managed_pages.json", encoding="utf-8"))
    for p in data["pages"]:
        info = fetch_facebook_page_details(p["id"], p["access_token"])
        print(f"=== {p['name']} ({p['id']}) ===")
        print("Category:", info.get("category"))
        print("About:", info.get("about"))
        print("Desc:", info.get("description"))
        print("Phone:", info.get("phone"))
        print("Website:", info.get("website"))
        print("Recent Posts Count:", len(info.get("recent_posts", [])))
        print("-" * 50)
