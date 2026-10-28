# FTI IT Asset Inventory Compare System 📊

> **ระบบเปรียบเทียบและประสานข้อมูลทรัพย์สินไอทีระหว่างระบบ ERP (AX) กับ IT Inventory อัตโนมัติ**  
> พัฒนาด้วย FastAPI, Pandas, OpenPyXL และ Vanilla CSS/JS ในรูปแบบ **Standalone Windowed Desktop Application (UI/UX Pro Max)**

---

## 🌟 คุณสมบัติเด่น (Key Features)

- **🎯 100% Match Rate & Multi-Pass Audit**: ปรับปรุงข้อมูลใช้งานจริงให้ตรงกับ ERP AX สมบูรณ์ 100.0% พร้อมระบบตรวจซ้ำ 3 รอบ (3-Pass Verification) ป้องกันข้อผิดพลาด
- **📑 แยกผลลัพธ์ 4 แท็บสมบูรณ์แบบ**: แต่ละไฟล์หมวดหมู่ (`1-it_asset_HW.xlsx`, `2-it_asset_SW.xlsx`, `3-it_asset_UPS_Monitor.xlsx`) ประกอบด้วย:
  1. `1_ข้อมูลเดิม`: ข้อมูลต้นฉบับดั้งเดิมคงคอลัมน์ครบถ้วน
  2. `2_เปรียบเทียบชี้จุดต่าง`: ตารางเทียบเคียง IT vs ERP AX แบบเคียงข้าง ไฮไลต์สีจุดต่าง และระบุการดำเนินการ
  3. `3_ข้อมูลแก้ไขแล้ว_100%`: ข้อมูลทรัพย์สินใช้งานจริงที่ซิงค์ตรง ERP 100% คงคอลัมน์เดิม นำเข้าใช้งานต่อได้ทันที
  4. `4_ข้อมูลที่ถูกตัดออก`: รายการที่ตัดจำหน่ายใน ERP, ไม่พบใน ERP, หรือไม่มีรหัสทรัพย์สิน พร้อมระบุสาเหตุและข้อมูล ERP อ้างอิง
- **⚡ 1-Click Batch Auto-Fix 100%**: ซิงค์รหัสพนักงาน ชื่อพนักงาน และแผนกจาก ERP AX ไปยัง IT Inventory ทันทีในคลิกเดียว พร้อมคัดแยกแท็บ 4 อัตโนมัติ
- **💾 Google Workspace-Style Auto-Save**: บันทึกสถานะการเปรียบเทียบและการแก้ไขลงเครื่องอัตโนมัติ กู้คืนเซสชันเมื่อเปิดโปรแกรมใหม่
- **↩️ Undo / Redo & Version History**: รองรับคีย์ลัดสากล `Ctrl + Z` (เลิกทำ) และ `Ctrl + Y` (ทำซ้ำ) พร้อมหน้าต่างดูประวัติย้อนหลังและปุ่ม Rollback
- **🖥️ 100% Windowed Desktop App**: รันผ่านหน้าต่างโปรแกรม Windows แท้ๆ (App-Mode) ไร้หน้าต่าง Command Prompt ดำรบกวนสายตา
- **💻 Centered System Console & Live Logs**: หน้าต่างแสดง Log ระบบแบบ Real-time ลอยตรงกลางจอ สไตล์ macOS พร้อมระบบค้นหา/กรองข้อความสด และปุ่มขยายเต็มจอ
- **📁 Drag-and-Drop Ingestion**: รองรับการลากวางไฟล์ Excel ทั้ง 4 หมวด (Master ERP, Hardware, Software, UPS & Monitor) ได้อย่างอิสระ
- **📥 Comprehensive Excel & ZIP Export**: ส่งออกไฟล์ 4 แท็บแยกหมวดหมู่, ดาวน์โหลดรวม 3 ไฟล์เป็น ZIP ในคลิกเดียว และรายงานจุดต่าง (Mismatch Reports)
- **🌙 Dark / Light Mode**: สลับธีมกลางวันและกลางคืน ถนอมสายตา

---

## 🏗️ สถาปัตยกรรมระบบ (System Architecture)

```
FTI_Inventory Compare Automations/
│
├── app.py                     # FastAPI Backend Server & REST API Endpoints
├── run_desktop.py             # Desktop App Launcher (Edge App Mode, Free Port Finder, Window Lifecycle)
├── build_exe.py               # PyInstaller Automated Build Script (Single-File .EXE)
├── build_exe.bat              # สคริปต์คลิกเดียวสำหรับ Compile เป็น .EXE
├── start_app.bat              # สคริปต์เปิดรันแบบรวดเร็ว (Live Development Mode)
├── start_exe.bat              # สคริปต์เปิดไฟล์ Executable สำเร็จรูป
├── logger_util.py             # Safe Thread-Safe Logging Utility (Windowed Mode Compatible)
├── requirements.txt           # รายการ Python Dependencies
│
├── engine/
│   ├── comparator.py          # แกนประมวลผลเปรียบเทียบ, กฎ Fuzzy Matching, Auto-Save & Revision Stack
│   └── report_generator.py    # ตัวสร้างไฟล์รายงาน Excel ด้วย OpenPyXL
│
├── static/
│   ├── index.html             # โครงสร้างหน้าเว็บหลัก (Semantic HTML5, Accessibility)
│   ├── style.css              # ระบบดีไซน์ระดับองค์กร (Glassmorphism, Responsive Tokens)
│   └── app.js                 # Front-end Application Logic & Event Handlers
│
├── tests/
│   └── test_system.py         # Automated End-to-End Test Suite
└── output/                    # โฟลเดอร์จัดเก็บไฟล์ Export
```

---

## 🚀 วิธีการใช้งาน (Getting Started)

### วิธีที่ 1: รันในโหมดพัฒนา (Development / Live Preview)
1. ติดตั้งไลบรารีที่จำเป็น:
   ```bash
   pip install -r requirements.txt
   ```
2. เริ่มต้นรันโปรแกรม:
   ```bash
   python run_desktop.py
   # หรือดับเบิลคลิกที่ start_app.bat
   ```
3. เมื่อแก้ไขไฟล์ HTML/CSS/JS สามารถกด `Ctrl + F5` ในหน้าต่างโปรแกรมเพื่อดูผลการเปลี่ยนแปลงได้ทันที

---

### วิธีที่ 2: คอมไพล์เป็นไฟล์เดี่ยว .EXE (Production Standalone Build)
1. ดับเบิลคลิกที่ [build_exe.bat](file:///e:/WEB/FTI_Inventory%20Compare%20Automations/build_exe.bat) หรือรันคำสั่ง:
   ```bash
   python build_exe.py
   ```
2. ระบบจะทำการแพ็กโค้ดและ Assets ทั้งหมดเป็นไฟล์เดี่ยว:
   - `FTI_Inventory_Compare.exe`
3. สามารถคัดลอกไฟล์ `.exe` ไปเปิดใช้งานบนคอมพิวเตอร์เครื่องอื่นที่มี Windows 10/11 ได้ทันทีโดยไม่ต้องติดตั้ง Python!

---

## 📄 License
Internal Enterprise Automation System for FTI IT Operations.
