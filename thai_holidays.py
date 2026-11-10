"""
โมดูลปฏิทินวันสำคัญ เทศกาล และวันพระพุทธศาสนาของไทย (Thai Holidays & Festivals Registry)
รองรับการคำนวณวันหยุดราชการ วันพระใหญ่ วันประเพณีวัฒนธรรม และวันสำคัญสากล ปี 2025-2028
"""
import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

def format_thai_date(date_str: str, include_year: bool = True) -> str:
    """แปลงวันที่ YYYY-MM-DD ให้เป็นภาษาไทย เช่น 24 พฤศจิกายน 2569"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        d = dt.day
        m = THAI_MONTHS[dt.month]
        th_year = dt.year + 543
        if include_year:
            return f"{d} {m} {th_year}"
        return f"{d} {m}"
    except Exception:
        return date_str

@dataclass
class HolidayEvent:
    id: str
    name: str
    name_en: str
    date: str  # YYYY-MM-DD
    type: str  # national_holiday, buddhist, festival, cultural, observance
    category: str  # วันหยุดราชการ, วันสำคัญทางพระพุทธศาสนา, เทศกาลประเพณี, วันสำคัญสากล
    description: str
    greeting: str
    visual_theme: str
    suggested_hashtags: List[str]
    default_time: str = "08:30"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["formatted_date_th"] = format_thai_date(self.date)
        return data

# คลังข้อมูลวันสำคัญของไทยครอบคลุมปี 2025 - 2028
HOLIDAYS_DATABASE: List[Dict[str, Any]] = [
    # ================= 2025 =================
    {
        "id": "new_year_2025", "name": "วันขึ้นปีใหม่", "name_en": "New Year's Day", "date": "2025-01-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเริ่มต้นศักราชใหม่ วันแห่งความสุขและการเริ่มต้นสิ่งดีๆ ร่วมกับครอบครัว",
        "greeting": "สุขสันต์วันปีใหม่ ขออาราธนาคุณพระศรีรัตนตรัยและสิ่งศักดิ์สิทธิ์ดลบันดาลให้ทุกท่านมีความสุข สุขภาพแข็งแรง การงานเจริญก้าวหน้า",
        "visual_theme": "Modern celebratory Thai New Year scene, warm golden fireworks, family happiness, cozy ambiance, 8k commercial photography",
        "suggested_hashtags": ["#วันปีใหม่", "#สวัสดีปีใหม่", "#HappyNewYear2025", "#เริ่มต้นปีใหม่"]
    },
    {
        "id": "children_day_2025", "name": "วันเด็กแห่งชาติ", "name_en": "National Children's Day", "date": "2025-01-11",
        "type": "cultural", "category": "วันสำคัญ",
        "description": "วันเสาร์ที่สองของเดือนมกราคม วันแห่งการส่งเสริมและมอบความสุขให้เยาวชนไทย",
        "greeting": "สุขสันต์วันเด็กแห่งชาติ ขอให้น้องๆ ทุกคนเติบโตด้วยรอยยิ้ม สุขภาพแข็งแรง เปี่ยมด้วยความรู้และจินตนาการ",
        "visual_theme": "Cheerful Thai children smiling happily, creative learning environment, colorful vibrant modern style",
        "suggested_hashtags": ["#วันเด็กแห่งชาติ", "#วันเด็ก2025", "#คำขวัญวันเด็ก", "#ความสุขของเด็กๆ"]
    },
    {
        "id": "teachers_day_2025", "name": "วันครู", "name_en": "Teachers' Day", "date": "2025-01-16",
        "type": "observance", "category": "วันสำคัญ",
        "description": "วันรำลึกถึงพระคุณครูบาอาจารย์ผู้ประสิทธิ์ประสาทวิชาความรู้",
        "greeting": "น้อมกราบคารวะและรำลึกถึงพระคุณครู ผู้เป็นแสงสว่างนำทางชีวิตและมอบวิชาความรู้ด้วยความเสียสละ",
        "visual_theme": "Respectful Thai Teachers Day tribute, traditional phan phum flowers, warm gentle library morning light",
        "suggested_hashtags": ["#วันครู", "#วันครูแห่งชาติ", "#พระคุณครู", "#รำลึกพระคุณครู"]
    },
    {
        "id": "valentine_day_2025", "name": "วันวาเลนไทน์", "name_en": "Valentine's Day", "date": "2025-02-14",
        "type": "festival", "category": "วันสำคัญสากล",
        "description": "วันแห่งความรักสากล ร่วมส่งมอบความรัก ความอบอุ่น และความปรารถนาดี",
        "greeting": "สุขสันต์วันวาเลนไทน์ ขอให้หัวใจของทุกท่านอบอวลไปด้วยความรัก ความห่วงใย และรอยยิ้มในทุกวัน",
        "visual_theme": "Heartwarming Valentine celebration, gentle red roses, warm cozy romantic atmosphere, premium lifestyle photo",
        "suggested_hashtags": ["#วันวาเลนไทน์", "#ValentinesDay", "#ส่งต่อความรัก", "#สุขสันต์วันแห่งความรัก"]
    },
    {
        "id": "makha_bucha_2025", "name": "วันมาฆบูชา", "name_en": "Makha Bucha Day", "date": "2025-02-12",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 3 วันจาตุรงคสันนิบาต พระพุทธองค์แสดงโอวาทปาติโมกข์",
        "greeting": "เนื่องในวันมาฆบูชา ขอร่วมทำบุญตักบาตร รักษาศีล ฟังธรรม น้อมนำโอวาทปาติโมกข์มาเป็นหลักชัยในชีวิต",
        "visual_theme": "Serene Thai Buddhist temple evening, gentle candlelight procession wian tian, lotus flower, golden peaceful light",
        "suggested_hashtags": ["#วันมาฆบูชา", "#ทำบุญตักบาตร", "#เวียนเทียน", "#วันพระใหญ่"]
    },
    {
        "id": "womens_day_2025", "name": "วันสตรีสากล", "name_en": "International Women's Day", "date": "2025-03-08",
        "type": "observance", "category": "วันสำคัญสากล",
        "description": "วันเฉลิมฉลองพลัง ความมุ่งมั่น และความสำเร็จของผู้หญิงทั่วโลก",
        "greeting": "สุขสันต์วันสตรีสากล ร่วมยกย่องและส่งพลังใจแด่ผู้หญิงทุกคน ผู้เป็นเสาหลักแห่งความรักและความสำเร็จ",
        "visual_theme": "Empowered confident Asian woman professional, bright inspiring office lighting, purple ribbon aesthetic",
        "suggested_hashtags": ["#วันสตรีสากล", "#IWD2025", "#พลังหญิง", "#InternationalWomensDay"]
    },
    {
        "id": "chakri_day_2025", "name": "วันจักรี", "name_en": "Chakri Memorial Day", "date": "2025-04-06",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกการก่อตั้งราชวงศ์จักรีและกรุงเทพมหานคร",
        "greeting": "น้อมรำลึกในพระมหากรุณาธิคุณ พระบาทสมเด็จพระพุทธยอดฟ้าจุฬาโลกมหาราช และบูรพมหากษัตริย์แห่งพระบรมราชจักรีวงศ์",
        "visual_theme": "Majestic Grand Palace Bangkok panorama, traditional Thai architectural elegance, golden hour sky",
        "suggested_hashtags": ["#วันจักรี", "#ราชวงศ์จักรี", "#น้อมรำลึกในพระมหากรุณาธิคุณ"]
    },
    {
        "id": "songkran_2025", "name": "เทศกาลสงกรานต์ (วันปีใหม่ไทย)", "name_en": "Songkran Water Festival", "date": "2025-04-13",
        "type": "festival", "category": "เทศกาลประเพณี / วันหยุดราชการ",
        "description": "ประเพณีปีใหม่ไทย รดน้ำดำหัวผู้ใหญ่ สรงน้ำพระ และเล่นสาดน้ำชุ่มฉ่ำใจ",
        "greeting": "สุขสันต์วันสงกรานต์และวันปีใหม่ไทย ขอให้ทุกท่านเดินทางปลอดภัย ร่มเย็นเป็นสุข สุขภาพแข็งแรงตลอดปี",
        "visual_theme": "Joyful Songkran celebration, traditional Thai jasmine scented water bowl, cheerful family blessings, vibrant sunlight",
        "suggested_hashtags": ["#วันสงกรานต์", "#สงกรานต์2025", "#ปีใหม่ไทย", "#วันครอบครัว", "#SongkranFestival"]
    },
    {
        "id": "labor_day_2025", "name": "วันแรงงานแห่งชาติ", "name_en": "National Labour Day", "date": "2025-05-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเชิดชูเกียรติและขอบคุณหยาดเหงื่อแรงงานของผู้ขับเคลื่อนเศรษฐกิจ",
        "greeting": "สุขสันต์วันแรงงานแห่งชาติ ขอบคุณทุกความทุ่มเท หยาดเหงื่อ และความตั้งใจของคนทำงานทุกคน",
        "visual_theme": "Dedicated hardworking professionals and technicians in clean modern uniform, thumbs up, warm inspiring sunset",
        "suggested_hashtags": ["#วันแรงงานแห่งชาติ", "#วันแรงงาน", "#ขอบคุณคนทำงาน", "#LaborDay"]
    },
    {
        "id": "coronation_day_2025", "name": "วันฉัตรมงคล", "name_en": "Coronation Day", "date": "2025-05-04",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกพระราชพิธีบรมราชาภิเษก พระบาทสมเด็จพระวชิรเกล้าเจ้าอยู่หัว",
        "greeting": "เนื่องในวันฉัตรมงคล ขอน้อมรำลึกในพระราชพิธีบรมราชาภิเษก ขอพระองค์ทรงพระเจริญยิ่งยืนนาน",
        "visual_theme": "Royal coronation regalia backdrop, elegant yellow and gold Thai motifs, dignified patriotic atmosphere",
        "suggested_hashtags": ["#วันฉัตรมงคล", "#ทรงพระเจริญ", "#CoronationDay"]
    },
    {
        "id": "visakha_bucha_2025", "name": "วันวิสาขบูชา", "name_en": "Visakha Bucha Day", "date": "2025-05-11",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันสำคัญสากลของโลก วันคล้ายวันประสูติ ตรัสรู้ และปรินิพพานขององค์สมเด็จพระสัมมาสัมพุทธเจ้า",
        "greeting": "เนื่องในวันวิสาขบูชา ขอร่วมทำความดี รักษาศีล ปฏิบัติธรรม น้อมนำธรรมะมาเป็นแสงสว่างในการดำเนินชีวิต",
        "visual_theme": "Golden Buddha statue surrounded by lotus flowers, peaceful glowing full moon light, ethereal Thai temple serenity",
        "suggested_hashtags": ["#วันวิสาขบูชา", "#วันสำคัญสากลของโลก", "#ทำบุญรักษาศีล", "#วันพระใหญ่"]
    },
    {
        "id": "queen_suthida_bday_2025", "name": "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ พระบรมราชินี", "name_en": "HM Queen Suthida's Birthday", "date": "2025-06-03",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดา พัชรสุธาพิมลลักษณ พระบรมราชินี",
        "greeting": "เนื่องในโอกาสวันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ พระบรมราชินี ขอพระองค์ทรงพระเจริญ มีพระพลานามัยสมบูรณ์แข็งแรง",
        "visual_theme": "Royal purple and gold Thai ceremonial aesthetics, orchid decorations, elegant dignified setting",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#สมเด็จพระบรมราชินี", "#วันเฉลิมพระชนมพรรษา"]
    },
    {
        "id": "asalha_bucha_2025", "name": "วันอาสาฬหบูชา", "name_en": "Asalha Bucha Day", "date": "2025-07-10",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 8 พระพุทธองค์ทรงแสดงปฐมเทศนา ธัมมจักกัปปวัตตนสูตร เกิดพระรัตนตรัยครบองค์สาม",
        "greeting": "เนื่องในวันอาสาฬหบูชา น้อมรำลึกถึงพระรัตนตรัย ขอให้ชีวิตเปี่ยมด้วยแสงสว่างแห่งปัญญาและความสงบสุข",
        "visual_theme": "Dhammachakka wheel of Dhamma stone sculpture, warm candlelight, peaceful temple courtyard",
        "suggested_hashtags": ["#วันอาสาฬหบูชา", "#วันพระรัตนตรัย", "#ทำบุญตักบาตร", "#เวียนเทียน"]
    },
    {
        "id": "khao_phansa_2025", "name": "วันเข้าพรรษา", "name_en": "Buddhist Lent Day", "date": "2025-07-11",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเริ่มต้นเทศกาลเข้าพรรษา พระสงฆ์จำพรรษาตลอดไตรมาส 3 เดือน",
        "greeting": "เนื่องในเทศกาลเข้าพรรษา ขอเชิญชวนทุกท่านร่วมถวายเทียนพรรษา รักษาศีล ลดละเลิกอบายมุข สร้างมงคลให้ชีวิต",
        "visual_theme": "Carved traditional Thai Lent candle with intricate wax art, glowing flame, incense smoke, morning temple mist",
        "suggested_hashtags": ["#วันเข้าพรรษา", "#ถวายเทียนพรรษา", "#งดเหล้าเข้าพรรษา", "#รักษาศีล"]
    },
    {
        "id": "king_rama10_bday_2025", "name": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว ร.10", "name_en": "HM King Rama X's Birthday", "date": "2025-07-28",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระปรเมนทรรามาธิบดีศรีสินทรมหาวชิราลงกรณ พระวชิรเกล้าเจ้าอยู่หัว",
        "greeting": "เนื่องในโอกาสวันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว ขอพระองค์ทรงพระเจริญยิ่งยืนนาน ด้วยเกล้าด้วยกระหม่อม ขอเดชะ",
        "visual_theme": "Magnificent royal yellow ceremonial backdrop, blooming Ratchaphruek flowers, dignified grand illumination",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#วันเฉลิมพระชนมพรรษา", "#รัชกาลที่10", "#LongLiveTheKing"]
    },
    {
        "id": "mothers_day_2025", "name": "วันแม่แห่งชาติ", "name_en": "National Mother's Day", "date": "2025-08-12",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา สมเด็จพระพันปีหลวง และวันแม่แห่งชาติ ร่วมบอกรักและกตัญญูต่อคุณแม่",
        "greeting": "สุขสันต์วันแม่แห่งชาติ ขอส่งความรักและความอบอุ่นแด่คุณแม่ทุกท่าน ขอให้ท่านมีสุขภาพแข็งแรงและเปี่ยมสุขเสมอ",
        "visual_theme": "Warm hug between mother and adult child, fresh white jasmine garland malai, soft natural morning window light",
        "suggested_hashtags": ["#วันแม่แห่งชาติ", "#วันแม่2025", "#รักแม่", "#มะลิวันแม่", "#MothersDay"]
    },
    {
        "id": "awk_phansa_2025", "name": "วันออกพรรษา", "name_en": "End of Buddhist Lent", "date": "2025-10-07",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 11 สิ้นสุดการจำพรรษา 3 เดือน มีประเพณีตักบาตรเทโวโรหณะ",
        "greeting": "เนื่องในวันออกพรรษา ขออนุโมทนาบุญกับกุศลจิตทุกท่าน และร่วมตักบาตรเทโวเพื่อความเป็นสิริมงคล",
        "visual_theme": "Tak Bat Devo almsgiving procession descending temple stairs, golden morning sunlight, colorful lotus flowers",
        "suggested_hashtags": ["#วันออกพรรษา", "#ตักบาตรเทโว", "#ทำบุญออกพรรษา", "#วันพระใหญ่"]
    },
    {
        "id": "navamindra_day_2025", "name": "วันนวมินทรมหาราช", "name_en": "King Rama IX Memorial Day", "date": "2025-10-13",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันสวรรคต พระบาทสมเด็จพระบรมชนกาธิเบศร มหาภูมิพลอดุลยเดชมหาราช บรมนาถบพิตร",
        "greeting": "๑๓ ตุลาคม วันนวมินทรมหาราช น้อมรำลึกในพระมหากรุณาธิคุณอันหาที่สุดมิได้ แห่งในหลวงรัชกาลที่ ๙ สถิตในใจตราบนิรันดร์",
        "visual_theme": "Golden light shining over King Rama IX suffiency economy project field, peaceful yellow flowers, solemn tribute",
        "suggested_hashtags": ["#วันนวมินทรมหาราช", "#คิดถึงในหลวงรัชกาลที่9", "#สถิตในดวงใจตราบนิรันดร์"]
    },
    {
        "id": "chulalongkorn_day_2025", "name": "วันปิยมหาราช", "name_en": "Chulalongkorn Memorial Day", "date": "2025-10-23",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันสวรรคต พระบาทสมเด็จพระจุลจอมเกล้าเจ้าอยู่หัว (พระปิยมหาราช)",
        "greeting": "๒๓ ตุลาคม วันปิยมหาราช น้อมรำลึกในพระมหากรุณาธิคุณ พระบาทสมเด็จพระจุลจอมเกล้าเจ้าอยู่หัว ผู้ทรงวางรากฐานความเจริญให้แก่ชาติไทย",
        "visual_theme": "Royal Equestrian Statue Bangkok surrounded by pink roses, twilight royal illumination, dignified historical aesthetic",
        "suggested_hashtags": ["#วันปิยมหาราช", "#พระปิยมหาราช", "#น้อมรำลึกในพระมหากรุณาธิคุณ"]
    },
    {
        "id": "halloween_2025", "name": "วันฮาโลวีน", "name_en": "Halloween", "date": "2025-10-31",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "เทศกาลฮาโลวีน สนุกสนานกับการแต่งกายและบรรยากาศเฉลิมฉลอง",
        "greeting": "Happy Halloween! ขอให้ค่ำคืนนี้เต็มไปด้วยความสุข รอยยิ้ม และความสนุกสนาน ปลอดภัยไร้เรื่องชวนปวดหัว",
        "visual_theme": "Playful modern Halloween pumpkin lantern, cozy warm amber lights, stylish clean commercial photography",
        "suggested_hashtags": ["#HappyHalloween", "#ฮาโลวีน2025", "#เทศกาลฮาโลวีน", "#TrickOrTreat"]
    },
    {
        "id": "loy_krathong_2025", "name": "ประเพณีวันลอยกระทง", "name_en": "Loy Krathong Festival", "date": "2025-11-05",
        "type": "festival", "category": "เทศกาลประเพณี",
        "description": "วันเพ็ญเดือน 12 ลอยกระทงขอขมาพระแม่คงคาและอธิษฐานสิ่งดีๆ เข้ามาสู่ชีวิต",
        "greeting": "สุขสันต์วันลอยกระทง ขอให้สายน้ำพัดพาความทุกข์โศกออกไป และนำพาความสุข ความเจริญรุ่งเรืองมาสู่ทุกท่าน",
        "visual_theme": "Illuminated banana leaf Krathong with candle and flowers floating on calm river under luminous full moon, warm golden reflections",
        "suggested_hashtags": ["#วันลอยกระทง", "#ลอยกระทง2025", "#ขอขมาพระแม่คงคา", "#LoyKrathongFestival"]
    },
    {
        "id": "fathers_day_2025", "name": "วันพ่อแห่งชาติ / วันชาติ", "name_en": "National Father's Day & National Day", "date": "2025-12-05",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันพระบรมราชสมภพ รัชกาลที่ 9 วันชาติ และวันพ่อแห่งชาติ",
        "greeting": "๕ ธันวาคม วันพ่อแห่งชาติและวันชาติ น้อมรำลึกในพระมหากรุณาธิคุณในหลวง ร.๙ และขอส่งความสุขความอบอุ่นแด่คุณพ่อทุกท่าน",
        "visual_theme": "Heartwarming father and adult children happy moment, yellow canna flowers, warm sunlit home living room",
        "suggested_hashtags": ["#วันพ่อแห่งชาติ", "#วันพ่อ2025", "#รักพ่อ", "#วันชาติ", "#FathersDay"]
    },
    {
        "id": "constitution_day_2025", "name": "วันรัฐธรรมนูญ", "name_en": "Constitution Day", "date": "2025-12-10",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกการพระราชทานรัฐธรรมนูญฉบับแรกแห่งราชอาณาจักรไทย",
        "greeting": "๑๐ ธันวาคม วันรัฐธรรมนูญ น้อมรำลึกถึงพระมหากรุณาธิคุณที่พระราชทานรัฐธรรมนูญเพื่อการปกครองระบอบประชาธิปไตย",
        "visual_theme": "Democracy Monument Bangkok under dramatic sunset sky, golden illumination, historic national pride",
        "suggested_hashtags": ["#วันรัฐธรรมนูญ", "#ประชาธิปไตย", "#ConstitutionDay"]
    },
    {
        "id": "christmas_2025", "name": "วันคริสต์มาส", "name_en": "Christmas Day", "date": "2025-12-25",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "เทศกาลคริสต์มาสแห่งความรัก ความสุข และการเฉลิมฉลองของครอบครัว",
        "greeting": "Merry Christmas! ขอส่งมอบความสุข ความอบอุ่น และรอยยิ้ม ขอให้เทศกาลนี้เต็มไปด้วยช่วงเวลาดีๆ ร่วมกับคนที่คุณรัก",
        "visual_theme": "Festive modern Christmas tree with warm twinkling lights, red and gold ornaments, cozy premium living room",
        "suggested_hashtags": ["#MerryChristmas", "#คริสต์มาส2025", "#เทศกาลแห่งความสุข", "#ChristmasDay"]
    },
    {
        "id": "new_year_eve_2025", "name": "วันสิ้นปี", "name_en": "New Year's Eve", "date": "2025-12-31",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันส่งท้ายปีเก่า ต้อนรับปีใหม่ ทบทวนเรื่องราวดีๆ และพร้อมก้าวสู่ปีต่อไป",
        "greeting": "สุขสันต์วันส่งท้ายปีเก่า ขอบพระคุณทุกความไว้วางใจตลอดปีที่ผ่านมา ขอให้ทุกท่านก้าวสู่ปีใหม่อย่างสดใสและเปี่ยมด้วยพลัง",
        "visual_theme": "Dramatic New Year Eve celebration, cityscape with midnight fireworks, countdown joy, premium advertising style",
        "suggested_hashtags": ["#วันสิ้นปี", "#ส่งท้ายปีเก่า", "#Countdown2026", "#ขอบคุณตลอดปี"]
    },

    # ================= 2026 =================
    {
        "id": "new_year_2026", "name": "วันขึ้นปีใหม่", "name_en": "New Year's Day", "date": "2026-01-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเริ่มต้นศักราชใหม่ วันแห่งความสุขและการเริ่มต้นสิ่งดีๆ ร่วมกับครอบครัว",
        "greeting": "สุขสันต์วันปีใหม่ ขออาราธนาคุณพระศรีรัตนตรัยและสิ่งศักดิ์สิทธิ์ดลบันดาลให้ทุกท่านมีความสุข สุขภาพแข็งแรง การงานเจริญก้าวหน้า",
        "visual_theme": "Modern celebratory Thai New Year scene, warm golden fireworks, family happiness, cozy ambiance, 8k commercial photography",
        "suggested_hashtags": ["#วันปีใหม่", "#สวัสดีปีใหม่", "#HappyNewYear2026", "#เริ่มต้นปีใหม่"]
    },
    {
        "id": "children_day_2026", "name": "วันเด็กแห่งชาติ", "name_en": "National Children's Day", "date": "2026-01-10",
        "type": "cultural", "category": "วันสำคัญ",
        "description": "วันเสาร์ที่สองของเดือนมกราคม วันแห่งการส่งเสริมและมอบความสุขให้เยาวชนไทย",
        "greeting": "สุขสันต์วันเด็กแห่งชาติ ขอให้น้องๆ ทุกคนเติบโตด้วยรอยยิ้ม สุขภาพแข็งแรง เปี่ยมด้วยความรู้และจินตนาการ",
        "visual_theme": "Cheerful Thai children smiling happily, creative learning environment, colorful vibrant modern style",
        "suggested_hashtags": ["#วันเด็กแห่งชาติ", "#วันเด็ก2026", "#คำขวัญวันเด็ก", "#ความสุขของเด็กๆ"]
    },
    {
        "id": "teachers_day_2026", "name": "วันครู", "name_en": "Teachers' Day", "date": "2026-01-16",
        "type": "observance", "category": "วันสำคัญ",
        "description": "วันรำลึกถึงพระคุณครูบาอาจารย์ผู้ประสิทธิ์ประสาทวิชาความรู้",
        "greeting": "น้อมกราบคารวะและรำลึกถึงพระคุณครู ผู้เป็นแสงสว่างนำทางชีวิตและมอบวิชาความรู้ด้วยความเสียสละ",
        "visual_theme": "Respectful Thai Teachers Day tribute, traditional phan phum flowers, warm gentle library morning light",
        "suggested_hashtags": ["#วันครู", "#วันครูแห่งชาติ", "#พระคุณครู", "#รำลึกพระคุณครู"]
    },
    {
        "id": "valentine_day_2026", "name": "วันวาเลนไทน์", "name_en": "Valentine's Day", "date": "2026-02-14",
        "type": "festival", "category": "วันสำคัญสากล",
        "description": "วันแห่งความรักสากล ร่วมส่งมอบความรัก ความอบอุ่น และความปรารถนาดี",
        "greeting": "สุขสันต์วันวาเลนไทน์ ขอให้หัวใจของทุกท่านอบอวลไปด้วยความรัก ความห่วงใย และรอยยิ้มในทุกวัน",
        "visual_theme": "Heartwarming Valentine celebration, gentle red roses, warm cozy romantic atmosphere, premium lifestyle photo",
        "suggested_hashtags": ["#วันวาเลนไทน์", "#ValentinesDay", "#ส่งต่อความรัก", "#สุขสันต์วันแห่งความรัก"]
    },
    {
        "id": "makha_bucha_2026", "name": "วันมาฆบูชา", "name_en": "Makha Bucha Day", "date": "2026-03-03",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 3 (ปีอธิกมาส ขึ้น 15 ค่ำ เดือน 4) วันจาตุรงคสันนิบาต พระพุทธองค์แสดงโอวาทปาติโมกข์",
        "greeting": "เนื่องในวันมาฆบูชา ขอร่วมทำบุญตักบาตร รักษาศีล ฟังธรรม น้อมนำโอวาทปาติโมกข์มาเป็นหลักชัยในชีวิต",
        "visual_theme": "Serene Thai Buddhist temple evening, gentle candlelight procession wian tian, lotus flower, golden peaceful light",
        "suggested_hashtags": ["#วันมาฆบูชา", "#ทำบุญตักบาตร", "#เวียนเทียน", "#วันพระใหญ่"]
    },
    {
        "id": "womens_day_2026", "name": "วันสตรีสากล", "name_en": "International Women's Day", "date": "2026-03-08",
        "type": "observance", "category": "วันสำคัญสากล",
        "description": "วันเฉลิมฉลองพลัง ความมุ่งมั่น และความสำเร็จของผู้หญิงทั่วโลก",
        "greeting": "สุขสันต์วันสตรีสากล ร่วมยกย่องและส่งพลังใจแด่ผู้หญิงทุกคน ผู้เป็นเสาหลักแห่งความรักและความสำเร็จ",
        "visual_theme": "Empowered confident Asian woman professional, bright inspiring office lighting, purple ribbon aesthetic",
        "suggested_hashtags": ["#วันสตรีสากล", "#IWD2026", "#พลังหญิง", "#InternationalWomensDay"]
    },
    {
        "id": "chakri_day_2026", "name": "วันจักรี", "name_en": "Chakri Memorial Day", "date": "2026-04-06",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกการก่อตั้งราชวงศ์จักรีและกรุงเทพมหานคร",
        "greeting": "น้อมรำลึกในพระมหากรุณาธิคุณ พระบาทสมเด็จพระพุทธยอดฟ้าจุฬาโลกมหาราช และบูรพมหากษัตริย์แห่งพระบรมราชจักรีวงศ์",
        "visual_theme": "Majestic Grand Palace Bangkok panorama, traditional Thai architectural elegance, golden hour sky",
        "suggested_hashtags": ["#วันจักรี", "#ราชวงศ์จักรี", "#น้อมรำลึกในพระมหากรุณาธิคุณ"]
    },
    {
        "id": "songkran_2026", "name": "เทศกาลสงกรานต์ (วันปีใหม่ไทย)", "name_en": "Songkran Water Festival", "date": "2026-04-13",
        "type": "festival", "category": "เทศกาลประเพณี / วันหยุดราชการ",
        "description": "ประเพณีปีใหม่ไทย รดน้ำดำหัวผู้ใหญ่ สรงน้ำพระ และเล่นสาดน้ำชุ่มฉ่ำใจ",
        "greeting": "สุขสันต์วันสงกรานต์และวันปีใหม่ไทย ขอให้ทุกท่านเดินทางปลอดภัย ร่มเย็นเป็นสุข สุขภาพแข็งแรงตลอดปี",
        "visual_theme": "Joyful Songkran celebration, traditional Thai jasmine scented water bowl, cheerful family blessings, vibrant sunlight",
        "suggested_hashtags": ["#วันสงกรานต์", "#สงกรานต์2026", "#ปีใหม่ไทย", "#วันครอบครัว", "#SongkranFestival"]
    },
    {
        "id": "labor_day_2026", "name": "วันแรงงานแห่งชาติ", "name_en": "National Labour Day", "date": "2026-05-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเชิดชูเกียรติและขอบคุณหยาดเหงื่อแรงงานของผู้ขับเคลื่อนเศรษฐกิจ",
        "greeting": "สุขสันต์วันแรงงานแห่งชาติ ขอบคุณทุกความทุ่มเท หยาดเหงื่อ และความตั้งใจของคนทำงานทุกคน",
        "visual_theme": "Dedicated hardworking professionals and technicians in clean modern uniform, thumbs up, warm inspiring sunset",
        "suggested_hashtags": ["#วันแรงงานแห่งชาติ", "#วันแรงงาน", "#ขอบคุณคนทำงาน", "#LaborDay"]
    },
    {
        "id": "coronation_day_2026", "name": "วันฉัตรมงคล", "name_en": "Coronation Day", "date": "2026-05-04",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกพระราชพิธีบรมราชาภิเษก พระบาทสมเด็จพระวชิรเกล้าเจ้าอยู่หัว",
        "greeting": "เนื่องในวันฉัตรมงคล ขอน้อมรำลึกในพระราชพิธีบรมราชาภิเษก ขอพระองค์ทรงพระเจริญยิ่งยืนนาน",
        "visual_theme": "Royal coronation regalia backdrop, elegant yellow and gold Thai motifs, dignified patriotic atmosphere",
        "suggested_hashtags": ["#วันฉัตรมงคล", "#ทรงพระเจริญ", "#CoronationDay"]
    },
    {
        "id": "visakha_bucha_2026", "name": "วันวิสาขบูชา", "name_en": "Visakha Bucha Day", "date": "2026-05-31",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 6 วันสำคัญสากลของโลก คล้ายวันประสูติ ตรัสรู้ และปรินิพพาน",
        "greeting": "เนื่องในวันวิสาขบูชา ขอร่วมทำความดี รักษาศีล ปฏิบัติธรรม น้อมนำธรรมะมาเป็นแสงสว่างในการดำเนินชีวิต",
        "visual_theme": "Golden Buddha statue surrounded by lotus flowers, peaceful glowing full moon light, ethereal Thai temple serenity",
        "suggested_hashtags": ["#วันวิสาขบูชา", "#วันสำคัญสากลของโลก", "#ทำบุญรักษาศีล", "#วันพระใหญ่"]
    },
    {
        "id": "queen_suthida_bday_2026", "name": "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ พระบรมราชินี", "name_en": "HM Queen Suthida's Birthday", "date": "2026-06-03",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดา พัชรสุธาพิมลลักษณ พระบรมราชินี",
        "greeting": "เนื่องในโอกาสวันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ พระบรมราชินี ขอพระองค์ทรงพระเจริญ มีพระพลานามัยสมบูรณ์แข็งแรง",
        "visual_theme": "Royal purple and gold Thai ceremonial aesthetics, orchid decorations, elegant dignified setting",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#สมเด็จพระบรมราชินี", "#วันเฉลิมพระชนมพรรษา"]
    },
    {
        "id": "asalha_bucha_2026", "name": "วันอาสาฬหบูชา", "name_en": "Asalha Bucha Day", "date": "2026-07-29",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 8 พระพุทธองค์ทรงแสดงปฐมเทศนา เกิดพระรัตนตรัยครบองค์สาม",
        "greeting": "เนื่องในวันอาสาฬหบูชา น้อมรำลึกถึงพระรัตนตรัย ขอให้ชีวิตเปี่ยมด้วยแสงสว่างแห่งปัญญาและความสงบสุข",
        "visual_theme": "Dhammachakka wheel of Dhamma stone sculpture, warm candlelight, peaceful temple courtyard",
        "suggested_hashtags": ["#วันอาสาฬหบูชา", "#วันพระรัตนตรัย", "#ทำบุญตักบาตร", "#เวียนเทียน"]
    },
    {
        "id": "khao_phansa_2026", "name": "วันเข้าพรรษา", "name_en": "Buddhist Lent Day", "date": "2026-07-30",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเริ่มต้นเทศกาลเข้าพรรษา พระสงฆ์จำพรรษาตลอดไตรมาส 3 เดือน",
        "greeting": "เนื่องในเทศกาลเข้าพรรษา ขอเชิญชวนทุกท่านร่วมถวายเทียนพรรษา รักษาศีล ลดละเลิกอบายมุข สร้างมงคลให้ชีวิต",
        "visual_theme": "Carved traditional Thai Lent candle with intricate wax art, glowing flame, incense smoke, morning temple mist",
        "suggested_hashtags": ["#วันเข้าพรรษา", "#ถวายเทียนพรรษา", "#งดเหล้าเข้าพรรษา", "#รักษาศีล"]
    },
    {
        "id": "king_rama10_bday_2026", "name": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว ร.10", "name_en": "HM King Rama X's Birthday", "date": "2026-07-28",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระปรเมนทรรามาธิบดีศรีสินทรมหาวชิราลงกรณ พระวชิรเกล้าเจ้าอยู่หัว",
        "greeting": "เนื่องในโอกาสวันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว ขอพระองค์ทรงพระเจริญยิ่งยืนนาน ด้วยเกล้าด้วยกระหม่อม ขอเดชะ",
        "visual_theme": "Magnificent royal yellow ceremonial backdrop, blooming Ratchaphruek flowers, dignified grand illumination",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#วันเฉลิมพระชนมพรรษา", "#รัชกาลที่10", "#LongLiveTheKing"]
    },
    {
        "id": "mothers_day_2026", "name": "วันแม่แห่งชาติ", "name_en": "National Mother's Day", "date": "2026-08-12",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา สมเด็จพระพันปีหลวง และวันแม่แห่งชาติ ร่วมบอกรักและกตัญญูต่อคุณแม่",
        "greeting": "สุขสันต์วันแม่แห่งชาติ ขอส่งความรักและความอบอุ่นแด่คุณแม่ทุกท่าน ขอให้ท่านมีสุขภาพแข็งแรงและเปี่ยมสุขเสมอ",
        "visual_theme": "Warm hug between mother and adult child, fresh white jasmine garland malai, soft natural morning window light",
        "suggested_hashtags": ["#วันแม่แห่งชาติ", "#วันแม่2026", "#รักแม่", "#มะลิวันแม่", "#MothersDay"]
    },
    {
        "id": "awk_phansa_2026", "name": "วันออกพรรษา", "name_en": "End of Buddhist Lent", "date": "2026-10-26",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 11 สิ้นสุดการจำพรรษา 3 เดือน มีประเพณีตักบาตรเทโวโรหณะ",
        "greeting": "เนื่องในวันออกพรรษา ขออนุโมทนาบุญกับกุศลจิตทุกท่าน และร่วมตักบาตรเทโวเพื่อความเป็นสิริมงคล",
        "visual_theme": "Tak Bat Devo almsgiving procession descending temple stairs, golden morning sunlight, colorful lotus flowers",
        "suggested_hashtags": ["#วันออกพรรษา", "#ตักบาตรเทโว", "#ทำบุญออกพรรษา", "#วันพระใหญ่"]
    },
    {
        "id": "navamindra_day_2026", "name": "วันนวมินทรมหาราช", "name_en": "King Rama IX Memorial Day", "date": "2026-10-13",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันสวรรคต พระบาทสมเด็จพระบรมชนกาธิเบศร มหาภูมิพลอดุลยเดชมหาราช บรมนาถบพิตร",
        "greeting": "๑๓ ตุลาคม วันนวมินทรมหาราช น้อมรำลึกในพระมหากรุณาธิคุณอันหาที่สุดมิได้ แห่งในหลวงรัชกาลที่ ๙ สถิตในใจตราบนิรันดร์",
        "visual_theme": "Golden light shining over King Rama IX suffiency economy project field, peaceful yellow flowers, solemn tribute",
        "suggested_hashtags": ["#วันนวมินทรมหาราช", "#คิดถึงในหลวงรัชกาลที่9", "#สถิตในดวงใจตราบนิรันดร์"]
    },
    {
        "id": "chulalongkorn_day_2026", "name": "วันปิยมหาราช", "name_en": "Chulalongkorn Memorial Day", "date": "2026-10-23",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันสวรรคต พระบาทสมเด็จพระจุลจอมเกล้าเจ้าอยู่หัว (พระปิยมหาราช)",
        "greeting": "๒๓ ตุลาคม วันปิยมหาราช น้อมรำลึกในพระมหากรุณาธิคุณ พระบาทสมเด็จพระจุลจอมเกล้าเจ้าอยู่หัว ผู้ทรงวางรากฐานความเจริญให้แก่ชาติไทย",
        "visual_theme": "Royal Equestrian Statue Bangkok surrounded by pink roses, twilight royal illumination, dignified historical aesthetic",
        "suggested_hashtags": ["#วันปิยมหาราช", "#พระปิยมหาราช", "#น้อมรำลึกในพระมหากรุณาธิคุณ"]
    },
    {
        "id": "halloween_2026", "name": "วันฮาโลวีน", "name_en": "Halloween", "date": "2026-10-31",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "เทศกาลฮาโลวีน สนุกสนานกับการแต่งกายและบรรยากาศเฉลิมฉลอง",
        "greeting": "Happy Halloween! ขอให้ค่ำคืนนี้เต็มไปด้วยความสุข รอยยิ้ม และความสนุกสนาน ปลอดภัยไร้เรื่องชวนปวดหัว",
        "visual_theme": "Playful modern Halloween pumpkin lantern, cozy warm amber lights, stylish clean commercial photography",
        "suggested_hashtags": ["#HappyHalloween", "#ฮาโลวีน2026", "#เทศกาลฮาโลวีน", "#TrickOrTreat"]
    },
    {
        "id": "loy_krathong_2026", "name": "ประเพณีวันลอยกระทง", "name_en": "Loy Krathong Festival", "date": "2026-11-24",
        "type": "festival", "category": "เทศกาลประเพณี",
        "description": "วันเพ็ญเดือน 12 ลอยกระทงขอขมาพระแม่คงคาและอธิษฐานสิ่งดีๆ เข้ามาสู่ชีวิต",
        "greeting": "สุขสันต์วันลอยกระทง ขอให้สายน้ำพัดพาความทุกข์โศกออกไป และนำพาความสุข ความเจริญรุ่งเรืองมาสู่ทุกท่าน",
        "visual_theme": "Illuminated banana leaf Krathong with candle and flowers floating on calm river under luminous full moon, warm golden reflections",
        "suggested_hashtags": ["#วันลอยกระทง", "#ลอยกระทง2026", "#ขอขมาพระแม่คงคา", "#LoyKrathongFestival"]
    },
    {
        "id": "fathers_day_2026", "name": "วันพ่อแห่งชาติ / วันชาติ", "name_en": "National Father's Day & National Day", "date": "2026-12-05",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันคล้ายวันพระบรมราชสมภพ รัชกาลที่ 9 วันชาติ และวันพ่อแห่งชาติ",
        "greeting": "๕ ธันวาคม วันพ่อแห่งชาติและวันชาติ น้อมรำลึกในพระมหากรุณาธิคุณในหลวง ร.๙ และขอส่งความสุขความอบอุ่นแด่คุณพ่อทุกท่าน",
        "visual_theme": "Heartwarming father and adult children happy moment, yellow canna flowers, warm sunlit home living room",
        "suggested_hashtags": ["#วันพ่อแห่งชาติ", "#วันพ่อ2026", "#รักพ่อ", "#วันชาติ", "#FathersDay"]
    },
    {
        "id": "constitution_day_2026", "name": "วันรัฐธรรมนูญ", "name_en": "Constitution Day", "date": "2026-12-10",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรำลึกการพระราชทานรัฐธรรมนูญฉบับแรกแห่งราชอาณาจักรไทย",
        "greeting": "๑๐ ธันวาคม วันรัฐธรรมนูญ น้อมรำลึกถึงพระมหากรุณาธิคุณที่พระราชทานรัฐธรรมนูญเพื่อการปกครองระบอบประชาธิปไตย",
        "visual_theme": "Democracy Monument Bangkok under dramatic sunset sky, golden illumination, historic national pride",
        "suggested_hashtags": ["#วันรัฐธรรมนูญ", "#ประชาธิปไตย", "#ConstitutionDay"]
    },
    {
        "id": "christmas_2026", "name": "วันคริสต์มาส", "name_en": "Christmas Day", "date": "2026-12-25",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "เทศกาลคริสต์มาสแห่งความรัก ความสุข และการเฉลิมฉลองของครอบครัว",
        "greeting": "Merry Christmas! ขอส่งมอบความสุข ความอบอุ่น และรอยยิ้ม ขอให้เทศกาลนี้เต็มไปด้วยช่วงเวลาดีๆ ร่วมกับคนที่คุณรัก",
        "visual_theme": "Festive modern Christmas tree with warm twinkling lights, red and gold ornaments, cozy premium living room",
        "suggested_hashtags": ["#MerryChristmas", "#คริสต์มาส2026", "#เทศกาลแห่งความสุข", "#ChristmasDay"]
    },
    {
        "id": "new_year_eve_2026", "name": "วันสิ้นปี", "name_en": "New Year's Eve", "date": "2026-12-31",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันส่งท้ายปีเก่า ต้อนรับปีใหม่ ทบทวนเรื่องราวดีๆ และพร้อมก้าวสู่ปีต่อไป",
        "greeting": "สุขสันต์วันส่งท้ายปีเก่า ขอบพระคุณทุกความไว้วางใจตลอดปีที่ผ่านมา ขอให้ทุกท่านก้าวสู่ปีใหม่อย่างสดใสและเปี่ยมด้วยพลัง",
        "visual_theme": "Dramatic New Year Eve celebration, cityscape with midnight fireworks, countdown joy, premium advertising style",
        "suggested_hashtags": ["#วันสิ้นปี", "#ส่งท้ายปีเก่า", "#Countdown2027", "#ขอบคุณตลอดปี"]
    },

    # ================= 2027 =================
    {
        "id": "new_year_2027", "name": "วันขึ้นปีใหม่", "name_en": "New Year's Day", "date": "2027-01-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเริ่มต้นศักราชใหม่", "greeting": "สุขสันต์วันปีใหม่ ขอให้ทุกท่านมีความสุข สุขภาพแข็งแรง การงานรุ่งเรือง",
        "visual_theme": "Festive Thai New Year morning celebration, bright sunlight, hope and happiness",
        "suggested_hashtags": ["#วันปีใหม่", "#สวัสดีปีใหม่2027", "#HappyNewYear2027"]
    },
    {
        "id": "children_day_2027", "name": "วันเด็กแห่งชาติ", "name_en": "National Children's Day", "date": "2027-01-09",
        "type": "cultural", "category": "วันสำคัญ",
        "description": "วันเด็กแห่งชาติ เสาร์ที่ 2 ของมกราคม", "greeting": "สุขสันต์วันเด็กแห่งชาติ เติบโตอย่างมีคุณภาพและมีความสุข",
        "visual_theme": "Thai children learning with smiles, creative modern school environment",
        "suggested_hashtags": ["#วันเด็กแห่งชาติ", "#วันเด็ก2027"]
    },
    {
        "id": "teachers_day_2027", "name": "วันครู", "name_en": "Teachers' Day", "date": "2027-01-16",
        "type": "observance", "category": "วันสำคัญ",
        "description": "วันรำลึกถึงพระคุณครู", "greeting": "น้อมรำลึกพระคุณครู ผู้สร้างคนสร้างอนาคต",
        "visual_theme": "Thai Teachers Day jasmine and lotus homage, warm classic tone",
        "suggested_hashtags": ["#วันครู", "#วันครู2027"]
    },
    {
        "id": "valentine_day_2027", "name": "วันวาเลนไทน์", "name_en": "Valentine's Day", "date": "2027-02-14",
        "type": "festival", "category": "วันสำคัญสากล",
        "description": "วันแห่งความรักสากล", "greeting": "สุขสันต์วันแห่งความรัก ขอให้ความรักเบ่งบานในทุกครอบครัว",
        "visual_theme": "Modern Valentine roses, pastel red tones, heartwarming elegance",
        "suggested_hashtags": ["#วันวาเลนไทน์", "#ValentinesDay2027"]
    },
    {
        "id": "makha_bucha_2027", "name": "วันมาฆบูชา", "name_en": "Makha Bucha Day", "date": "2027-02-21",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเพ็ญเดือน 3 วันแสดงโอวาทปาติโมกข์", "greeting": "ร่วมทำบุญตักบาตร ละชั่ว ทำดี จิตใจผ่องใส",
        "visual_theme": "Temple candle walk at dusk, golden pagoda reflection",
        "suggested_hashtags": ["#วันมาฆบูชา", "#วันพระใหญ่"]
    },
    {
        "id": "womens_day_2027", "name": "วันสตรีสากล", "name_en": "International Women's Day", "date": "2027-03-08",
        "type": "observance", "category": "วันสำคัญสากล",
        "description": "วันสตรีสากล", "greeting": "สุขสันต์วันสตรีสากล ร่วมสนับสนุนพลังและความสามารถของสตรี",
        "visual_theme": "Inspirational professional Asian women leaders, bright lighting",
        "suggested_hashtags": ["#วันสตรีสากล", "#IWD2027"]
    },
    {
        "id": "chakri_day_2027", "name": "วันจักรี", "name_en": "Chakri Memorial Day", "date": "2027-04-06",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันพระบาทสมเด็จพระพุทธยอดฟ้าจุฬาโลกมหาราชและวันที่ระลึกมหาจักรีบรมราชวงศ์",
        "greeting": "น้อมรำลึกในพระมหากรุณาธิคุณบูรพกษัตริย์แห่งราชวงศ์จักรี",
        "visual_theme": "Royal Chakri dynasty memorial architecture, golden sunlight",
        "suggested_hashtags": ["#วันจักรี", "#ราชวงศ์จักรี"]
    },
    {
        "id": "songkran_2027", "name": "เทศกาลสงกรานต์ (วันปีใหม่ไทย)", "name_en": "Songkran Water Festival", "date": "2027-04-13",
        "type": "festival", "category": "เทศกาลประเพณี / วันหยุดราชการ",
        "description": "ประเพณีสงกรานต์ไทย รดน้ำดำหัวและเดินทางกลับบ้านอย่างปลอดภัย",
        "greeting": "สุขสันต์วันสงกรานต์ เย็นกาย เย็นใจ เดินทางปลอดภัยทุกเส้นทาง",
        "visual_theme": "Songkran water splashing joy, traditional Thai scented water flower garland",
        "suggested_hashtags": ["#วันสงกรานต์", "#สงกรานต์2027", "#ปีใหม่ไทย"]
    },
    {
        "id": "labor_day_2027", "name": "วันแรงงานแห่งชาติ", "name_en": "National Labour Day", "date": "2027-05-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันแรงงานแห่งชาติ", "greeting": "ขอบคุณทุกแรงกายแรงใจของผู้ใช้แรงงานและผู้ทำงานทุกคน",
        "visual_theme": "Skilled craftsmen and service specialists working safely, clean aesthetic",
        "suggested_hashtags": ["#วันแรงงานแห่งชาติ", "#LaborDay2027"]
    },
    {
        "id": "coronation_day_2027", "name": "วันฉัตรมงคล", "name_en": "Coronation Day", "date": "2027-05-04",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันฉัตรมงคล", "greeting": "เนื่องในวันฉัตรมงคล ขอพระองค์ทรงพระเจริญยิ่งยืนนาน",
        "visual_theme": "Royal Thai golden emblems and national flag, dignified atmosphere",
        "suggested_hashtags": ["#วันฉัตรมงคล", "#ทรงพระเจริญ"]
    },
    {
        "id": "visakha_bucha_2027", "name": "วันวิสาขบูชา", "name_en": "Visakha Bucha Day", "date": "2027-05-20",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันวิสาขบูชา วันเพ็ญเดือน 6 วันสำคัญสากลของโลก",
        "greeting": "เนื่องในวันวิสาขบูชา น้อมรำลึกถึงพระพุทธคุณ พระธรรมคุณ พระสังฆคุณ",
        "visual_theme": "Buddha statue under Bodhi tree with soft moonlight, tranquil temple scenery",
        "suggested_hashtags": ["#วันวิสาขบูชา", "#วันสำคัญสากลของโลก", "#วันพระใหญ่"]
    },
    {
        "id": "queen_suthida_bday_2027", "name": "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ พระบรมราชินี", "name_en": "HM Queen Suthida's Birthday", "date": "2027-06-03",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา สมเด็จพระบรมราชินี", "greeting": "ขอพระองค์ทรงพระเจริญ ทรงมีพระพลานามัยแข็งแรง",
        "visual_theme": "Purple Thai silk floral tributes, royal dignified ambiance",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#สมเด็จพระบรมราชินี"]
    },
    {
        "id": "asalha_bucha_2027", "name": "วันอาสาฬหบูชา", "name_en": "Asalha Bucha Day", "date": "2027-07-18",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันอาสาฬหบูชา วันปฐมเทศนา", "greeting": "ขอแสงสว่างแห่งธรรมคุ้มครองให้ทุกท่านสุขสงบ",
        "visual_theme": "Golden Dharmachakra and candle flame in quiet Buddhist temple",
        "suggested_hashtags": ["#วันอาสาฬหบูชา", "#เวียนเทียน"]
    },
    {
        "id": "khao_phansa_2027", "name": "วันเข้าพรรษา", "name_en": "Buddhist Lent Day", "date": "2027-07-19",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันเข้าพรรษา เริ่มต้นการจำพรรษา", "greeting": "ร่วมรักษาศีล ละเว้นอบายมุข สร้างบุญบารมีตลอดพรรษา",
        "visual_theme": "Traditional carved wax Lent candle, warm glow in monastery",
        "suggested_hashtags": ["#วันเข้าพรรษา", "#ถวายเทียนพรรษา"]
    },
    {
        "id": "king_rama10_bday_2027", "name": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว ร.10", "name_en": "HM King Rama X's Birthday", "date": "2027-07-28",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระเจ้าอยู่หัว", "greeting": "ขอพระองค์ทรงพระเจริญยิ่งยืนนาน ด้วยเกล้าด้วยกระหม่อม ขอเดชะ",
        "visual_theme": "Ceremonial royal yellow flowers and illumination, dignified grandeur",
        "suggested_hashtags": ["#ทรงพระเจริญ", "#รัชกาลที่10"]
    },
    {
        "id": "mothers_day_2027", "name": "วันแม่แห่งชาติ", "name_en": "National Mother's Day", "date": "2027-08-12",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันแม่แห่งชาติ", "greeting": "สุขสันต์วันแม่ ขอให้คุณแม่ทุกท่านมีสุขภาพแข็งแรงและมีความสุข",
        "visual_theme": "White jasmine flowers and happy Thai family smiling together",
        "suggested_hashtags": ["#วันแม่แห่งชาติ", "#รักแม่", "#MothersDay2027"]
    },
    {
        "id": "awk_phansa_2027", "name": "วันออกพรรษา", "name_en": "End of Buddhist Lent", "date": "2027-10-15",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันออกพรรษาและตักบาตรเทโว", "greeting": "ร่วมอนุโมทนาบุญวันออกพรรษา ขอความสุขสถิตในจิตใจ",
        "visual_theme": "Almsgiving procession with monks under golden morning sunlight",
        "suggested_hashtags": ["#วันออกพรรษา", "#ตักบาตรเทโว"]
    },
    {
        "id": "navamindra_day_2027", "name": "วันนวมินทรมหาราช", "name_en": "King Rama IX Memorial Day", "date": "2027-10-13",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันนวมินทรมหาราช น้อมรำลึกในหลวง ร.๙", "greeting": "น้อมรำลึกในพระมหากรุณาธิคุณอันหาที่สุดมิได้",
        "visual_theme": "King Rama IX memorial tribute, golden light on yellow blossoms",
        "suggested_hashtags": ["#วันนวมินทรมหาราช", "#ธสถิตในดวงใจไทยนิรันดร์"]
    },
    {
        "id": "chulalongkorn_day_2027", "name": "วันปิยมหาราช", "name_en": "Chulalongkorn Memorial Day", "date": "2027-10-23",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันปิยมหาราช", "greeting": "น้อมรำลึกในพระมหากรุณาธิคุณ พระปิยมหาราช",
        "visual_theme": "Equestrian statue in Bangkok with pink floral tribute",
        "suggested_hashtags": ["#วันปิยมหาราช", "#น้อมรำลึกในพระมหากรุณาธิคุณ"]
    },
    {
        "id": "halloween_2027", "name": "วันฮาโลวีน", "name_en": "Halloween", "date": "2027-10-31",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "วันฮาโลวีน", "greeting": "Happy Halloween! สนุกสนานและปลอดภัยในค่ำคืนนี้",
        "visual_theme": "Artistic modern jack-o-lantern with amber bokeh lights",
        "suggested_hashtags": ["#Halloween2027", "#HappyHalloween"]
    },
    {
        "id": "loy_krathong_2027", "name": "ประเพณีวันลอยกระทง", "name_en": "Loy Krathong Festival", "date": "2027-11-13",
        "type": "festival", "category": "เทศกาลประเพณี",
        "description": "ประเพณีลอยกระทง วันเพ็ญเดือน 12", "greeting": "สุขสันต์วันลอยกระทง ขอให้สายน้ำนำพาแต่สิ่งดีงามมาสู่ชีวิต",
        "visual_theme": "Krathong floating on moonlit Chao Phraya river with Wat Arun silhouette",
        "suggested_hashtags": ["#วันลอยกระทง", "#ลอยกระทง2027", "#LoyKrathong"]
    },
    {
        "id": "fathers_day_2027", "name": "วันพ่อแห่งชาติ / วันชาติ", "name_en": "National Father's Day & National Day", "date": "2027-12-05",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันพ่อแห่งชาติและวันชาติ", "greeting": "สุขสันต์วันพ่อแห่งชาติ ส่งมอบความรักและความอบอุ่นแด่คุณพ่อทุกท่าน",
        "visual_theme": "Father holding adult children hands, warm sunset glow",
        "suggested_hashtags": ["#วันพ่อแห่งชาติ", "#รักพ่อ", "#วันชาติ"]
    },
    {
        "id": "constitution_day_2027", "name": "วันรัฐธรรมนูญ", "name_en": "Constitution Day", "date": "2027-12-10",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันรัฐธรรมนูญ", "greeting": "๑๐ ธันวาคม วันรัฐธรรมนูญแห่งราชอาณาจักรไทย",
        "visual_theme": "Democracy monument silhouette with Thai national flag colors",
        "suggested_hashtags": ["#วันรัฐธรรมนูญ", "#ConstitutionDay"]
    },
    {
        "id": "christmas_2027", "name": "วันคริสต์มาส", "name_en": "Christmas Day", "date": "2027-12-25",
        "type": "festival", "category": "เทศกาลสากล",
        "description": "วันคริสต์มาส", "greeting": "Merry Christmas! สุขสันต์เทศกาลคริสต์มาส ขอให้มีความสุขสมหวัง",
        "visual_theme": "Christmas tree with sparkling warm decorations and presents",
        "suggested_hashtags": ["#MerryChristmas2027", "#Christmas"]
    },
    {
        "id": "new_year_eve_2027", "name": "วันสิ้นปี", "name_en": "New Year's Eve", "date": "2027-12-31",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันสิ้นปี ส่งท้ายปีเก่า", "greeting": "ส่งท้ายปีเก่า ต้อนรับปีใหม่ ขอให้ก้าวสู่อีกหนึ่งปีด้วยความสำเร็จ",
        "visual_theme": "City fireworks display welcoming the brand new year, vibrant colors",
        "suggested_hashtags": ["#วันสิ้นปี", "#Countdown2028"]
    },

    # ================= 2028 =================
    {
        "id": "new_year_2028", "name": "วันขึ้นปีใหม่", "name_en": "New Year's Day", "date": "2028-01-01",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันขึ้นปีใหม่", "greeting": "สุขสันต์วันปีใหม่ ขอให้มีสุขภาพแข็งแรง ร่ำรวย และมีความสุข",
        "visual_theme": "Bright sunrise over modern Bangkok skyline, celebratory feeling",
        "suggested_hashtags": ["#วันปีใหม่", "#HappyNewYear2028"]
    },
    {
        "id": "children_day_2028", "name": "วันเด็กแห่งชาติ", "name_en": "National Children's Day", "date": "2028-01-08",
        "type": "cultural", "category": "วันสำคัญ",
        "description": "วันเด็กแห่งชาติ เสาร์ที่ 2 ของมกราคม", "greeting": "สุขสันต์วันเด็กแห่งชาติ เป็นเด็กดี มีความสุข สนุกกับการเรียนรู้",
        "visual_theme": "Children laughing and playing in bright sunlit park",
        "suggested_hashtags": ["#วันเด็กแห่งชาติ", "#วันเด็ก2028"]
    },
    {
        "id": "teachers_day_2028", "name": "วันครู", "name_en": "Teachers' Day", "date": "2028-01-16",
        "type": "observance", "category": "วันสำคัญ",
        "description": "วันครูแห่งชาติ", "greeting": "น้อมจิตกตัญญู รำลึกพระคุณครู",
        "visual_theme": "Lotus bouquet and traditional Thai gratitude garland",
        "suggested_hashtags": ["#วันครู", "#วันครู2028"]
    },
    {
        "id": "valentine_day_2028", "name": "วันวาเลนไทน์", "name_en": "Valentine's Day", "date": "2028-02-14",
        "type": "festival", "category": "วันสำคัญสากล",
        "description": "วันวาเลนไทน์", "greeting": "Happy Valentine's Day ขอให้ความรักและความสุขรายล้อมเสมอ",
        "visual_theme": "Modern floral love arrangement, elegant warm photography",
        "suggested_hashtags": ["#Valentine2028", "#วันแห่งความรัก"]
    },
    {
        "id": "makha_bucha_2028", "name": "วันมาฆบูชา", "name_en": "Makha Bucha Day", "date": "2028-02-10",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันมาฆบูชา", "greeting": "ร่วมทำบุญตักบาตร ละเว้นบาปทั้งปวง ทำจิตใจให้บริสุทธิ์",
        "visual_theme": "Serene candlelight procession at golden Thai chedi",
        "suggested_hashtags": ["#วันมาฆบูชา", "#วันพระใหญ่"]
    },
    {
        "id": "songkran_2028", "name": "เทศกาลสงกรานต์ (วันปีใหม่ไทย)", "name_en": "Songkran Water Festival", "date": "2028-04-13",
        "type": "festival", "category": "เทศกาลประเพณี / วันหยุดราชการ",
        "description": "เทศกาลสงกรานต์ วันปีใหม่ไทย", "greeting": "สุขสันต์วันสงกรานต์ ขอให้เย็นชื่นใจ ครอบครัวอบอุ่น",
        "visual_theme": "Splashing crystal water in warm tropical Thai sunlight, cheerful smiles",
        "suggested_hashtags": ["#วันสงกรานต์", "#สงกรานต์2028", "#ปีใหม่ไทย"]
    },
    {
        "id": "visakha_bucha_2028", "name": "วันวิสาขบูชา", "name_en": "Visakha Bucha Day", "date": "2028-05-08",
        "type": "buddhist", "category": "วันสำคัญทางพระพุทธศาสนา",
        "description": "วันวิสาขบูชา", "greeting": "น้อมนำธรรมะสู่การดำเนินชีวิตด้วยความมีสติ",
        "visual_theme": "Golden Buddha statues illuminated by candles in quiet hall",
        "suggested_hashtags": ["#วันวิสาขบูชา", "#วันสำคัญสากลของโลก"]
    },
    {
        "id": "mothers_day_2028", "name": "วันแม่แห่งชาติ", "name_en": "National Mother's Day", "date": "2028-08-12",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันแม่แห่งชาติ", "greeting": "สุขสันต์วันแม่แห่งชาติ บอกรักและดูแลคุณแม่ทุกวัน",
        "visual_theme": "Pure white jasmine flower garland, morning sunlight in home",
        "suggested_hashtags": ["#วันแม่แห่งชาติ", "#MothersDay2028"]
    },
    {
        "id": "loy_krathong_2028", "name": "ประเพณีวันลอยกระทง", "name_en": "Loy Krathong Festival", "date": "2028-11-01",
        "type": "festival", "category": "เทศกาลประเพณี",
        "description": "วันลอยกระทง", "greeting": "สุขสันต์วันลอยกระทง ขอให้ทุกท่านมีความสุขสมหวังตลอดไป",
        "visual_theme": "Krathong gently floating on reflective water under soft full moon",
        "suggested_hashtags": ["#วันลอยกระทง", "#LoyKrathong2028"]
    },
    {
        "id": "fathers_day_2028", "name": "วันพ่อแห่งชาติ / วันชาติ", "name_en": "National Father's Day & National Day", "date": "2028-12-05",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันพ่อแห่งชาติและวันชาติ", "greeting": "สุขสันต์วันพ่อแห่งชาติ ขอให้คุณพ่อทุกท่านมีสุขภาพแข็งแรง",
        "visual_theme": "Warm family generation portrait with yellow blossoms",
        "suggested_hashtags": ["#วันพ่อแห่งชาติ", "#วันชาติ"]
    },
    {
        "id": "new_year_eve_2028", "name": "วันสิ้นปี", "name_en": "New Year's Eve", "date": "2028-12-31",
        "type": "national_holiday", "category": "วันหยุดราชการ",
        "description": "วันสิ้นปี", "greeting": "สุขสันต์วันสิ้นปี ขอบคุณทุกสิ่งดีๆ ตลอดปีที่ผ่านมา",
        "visual_theme": "Midnight fireworks and celebration champagne glasses",
        "suggested_hashtags": ["#วันสิ้นปี", "#Countdown2029"]
    }
]

def _build_registry() -> Dict[str, HolidayEvent]:
    reg = {}
    for item in HOLIDAYS_DATABASE:
        event = HolidayEvent(
            id=item["id"],
            name=item["name"],
            name_en=item["name_en"],
            date=item["date"],
            type=item["type"],
            category=item["category"],
            description=item["description"],
            greeting=item["greeting"],
            visual_theme=item["visual_theme"],
            suggested_hashtags=item["suggested_hashtags"],
            default_time=item.get("default_time", "08:30")
        )
        reg[item["id"]] = event
    return reg

HOLIDAYS_REGISTRY = _build_registry()

def get_upcoming_holidays(from_date: Optional[str] = None, days_ahead: int = 60) -> List[Dict[str, Any]]:
    """
    ดึงรายการวันสำคัญที่กำลังจะมาถึงในช่วงเวลาที่กำหนด (ค่าเริ่มต้น 60 วัน)
    """
    if from_date:
        try:
            start_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        except Exception:
            start_dt = date.today()
    else:
        start_dt = date.today()

    end_dt = start_dt + timedelta(days=days_ahead)

    results = []
    for h in HOLIDAYS_REGISTRY.values():
        try:
            h_date = datetime.strptime(h.date, "%Y-%m-%d").date()
        except Exception:
            continue

        if start_dt <= h_date <= end_dt:
            h_dict = h.to_dict()
            h_dict["days_until"] = (h_date - start_dt).days
            results.append(h_dict)

    results.sort(key=lambda x: x["date"])
    return results

def get_holiday_by_id(holiday_id: str) -> Optional[Dict[str, Any]]:
    """ดึงข้อมูลวันสำคัญตาม holiday_id"""
    ev = HOLIDAYS_REGISTRY.get(holiday_id)
    if ev:
        return ev.to_dict()
    return None

def get_all_holidays_for_year(year: int) -> List[Dict[str, Any]]:
    """ดึงรายการวันสำคัญทั้งหมดสำหรับปีที่ระบุ (เช่น 2026)"""
    year_prefix = f"{year}-"
    results = [ev.to_dict() for ev in HOLIDAYS_REGISTRY.values() if ev.date.startswith(year_prefix)]
    results.sort(key=lambda x: x["date"])
    return results

# Alias for convenience
get_all_holidays = get_all_holidays_for_year

