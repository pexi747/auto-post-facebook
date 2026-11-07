@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo ======================================================
echo   FixPack Facebook Auto-Pilot Web Dashboard
echo ======================================================
echo.
echo กำลังเริ่มต้นเซิร์ฟเวอร์...
echo - เปิดใช้งานบนเครื่องนี้:             http://localhost:5050
echo - เปิดจากมือถือในวง Wi-Fi เดียวกัน:     http://192.168.1.163:5050
echo - หากต้องการเข้าจากเน็ตภายนอก (4G/5G): ให้เปิด start_internet_tunnel.bat
echo.
echo บัญชีสำหรับเข้าสู่ระบบ:
echo - admin (รหัส: admin123) - ผู้ดูแลระบบ กำหนดค่า CI และผู้ใช้
echo - owner (รหัส: owner123) - เจ้าของเพจ โพสต์คอนเทนต์และใช้ AI
echo - staff (รหัส: staff123) - ทีมงานร่างคอนเทนต์
echo.
echo กด Ctrl+C เพื่อหยุดการทำงาน
echo ======================================================
py web_app.py
pause
