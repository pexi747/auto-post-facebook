@echo off
chcp 65001 > nul
echo ======================================================
echo   อัปโหลดโปรเจกต์ขึ้น GitHub (สำหรับต่อเข้า Cloud ฟรี)
echo ======================================================
echo.
echo 1. ไปที่ https://github.com/new แล้วกดสร้าง New Repository (ตั้งชื่ออะไรก็ได้ เช่น fixpack-bot)
echo 2. คัดลอกลิงก์ Repository มาวางที่นี่ (เช่น https://github.com/your-username/fixpack-bot.git)
echo.
set /p repo_url="👉 วางลิงก์ GitHub Repository: "

if "%repo_url%"=="" (
    echo ❌ ยกเลิก
    pause
    exit /b
)

git remote remove origin >nul 2>&1
git branch -M main
git remote add origin %repo_url%
echo.
echo ⏳ กำลังอัปโหลดโค้ดขึ้น GitHub...
git push -u origin main

echo.
echo ======================================================
echo ✅ อัปโหลดขึ้น GitHub เรียบร้อยแล้ว!
echo ขั้นต่อไป: ไปที่ https://render.com กด New Web Service แล้วเลือก Repo นี้ได้เลย
echo ======================================================
pause
