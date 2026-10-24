import os
import io
import tempfile
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd

# Color codes matching HW_Mismatch_Report.xlsx
FILL_BOTH_MISMATCH = PatternFill(start_color="FFFFCCCC", end_color="FFFFCCCC", fill_type="solid")  # Soft red
FILL_EMP_MISMATCH = PatternFill(start_color="FFFFFFCC", end_color="FFFFFFCC", fill_type="solid")   # Soft yellow
FILL_DEPT_MISMATCH = PatternFill(start_color="FFD6EAF8", end_color="FFD6EAF8", fill_type="solid") # Soft blue
FILL_SCRAPPED = PatternFill(start_color="FFFDEBD0", end_color="FFFDEBD0", fill_type="solid")      # Soft orange
FILL_MISSING_ERP = PatternFill(start_color="FFEAECEE", end_color="FFEAECEE", fill_type="solid")   # Soft gray
FILL_HEADER = PatternFill(start_color="FF1E293B", end_color="FF1E293B", fill_type="solid")        # Dark slate
FILL_HEADER_LIGHT = PatternFill(start_color="FF334155", end_color="FF334155", fill_type="solid")  # Slate

FONT_HEADER = Font(name="TH Sarabun New", size=13, bold=True, color="FFFFFFFF")
FONT_REGULAR = Font(name="TH Sarabun New", size=11, bold=False, color="FF000000")
FONT_BOLD = Font(name="TH Sarabun New", size=11, bold=True, color="FF000000")
FONT_TITLE = Font(name="TH Sarabun New", size=16, bold=True, color="FF0F172A")
FONT_SUBTITLE = Font(name="TH Sarabun New", size=13, bold=True, color="FF1E293B")
FONT_RED = Font(name="TH Sarabun New", size=11, bold=True, color="FFFF0000")
FONT_ORANGE = Font(name="TH Sarabun New", size=11, bold=True, color="FFD35400")

THIN_BORDER = Border(
    left=Side(style='thin', color='FFCBD5E1'),
    right=Side(style='thin', color='FFCBD5E1'),
    top=Side(style='thin', color='FFCBD5E1'),
    bottom=Side(style='thin', color='FFCBD5E1')
)

def get_row_fill_and_font(mismatch_type: str) -> tuple:
    """Return background fill and font based on mismatch type."""
    if "รหัสพนักงาน + แผนก" in mismatch_type:
        return FILL_BOTH_MISMATCH, FONT_RED
    elif "รหัสพนักงาน" in mismatch_type:
        return FILL_EMP_MISMATCH, FONT_RED
    elif "แผนก" in mismatch_type:
        return FILL_DEPT_MISMATCH, FONT_ORANGE
    elif "ตัดจำหน่าย" in mismatch_type:
        return FILL_SCRAPPED, FONT_BOLD
    elif "ไม่พบ" in mismatch_type:
        return FILL_MISSING_ERP, FONT_REGULAR
    return None, FONT_REGULAR


class ReportGenerator:
    """Generates styled Mismatch reports and corrected inventory files (files or in-memory BytesIO)."""

    @staticmethod
    def build_mismatch_workbook(comparator, category: Optional[str] = None) -> openpyxl.Workbook:
        """Create and populate openpyxl Workbook with summary and mismatch records."""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # 1. Filter records
        categories = [category] if category and category != "all" else ["hw", "sw", "ups"]
        all_mismatches = []
        for c in categories:
            all_mismatches.extend([r for r in comparator.records.get(c, []) if not r["is_match"]])

        summary_data = comparator.summary

        # -------------------------------------------------------------
        # Sheet 1: สรุป
        # -------------------------------------------------------------
        ws_summary = wb.create_sheet(title="สรุป")
        ws_summary.views.sheetView[0].showGridLines = True

        ws_summary.cell(row=1, column=1, value="รายงาน Mismatch IT Asset Inventory").font = FONT_TITLE
        ws_summary.cell(row=2, column=1, value=f"เวลาประมวลผล: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}").font = FONT_REGULAR

        # Summary Table by Mismatch Type
        headers_mtype = ["ประเภท Mismatch", "จำนวน (รายการ)", "สัดส่วน (%)"]
        start_row = 4
        for col_idx, h in enumerate(headers_mtype, start=1):
            c = ws_summary.cell(row=start_row, column=col_idx, value=h)
            c.font = FONT_HEADER
            c.fill = FILL_HEADER
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = THIN_BORDER

        curr_row = start_row + 1
        m_breakdown = summary_data.get("mismatch_breakdown", {})
        total_mismatches = len(all_mismatches)

        for m_name, count in m_breakdown.items():
            if count == 0:
                continue
            pct = f"{(count / total_mismatches * 100):.1f}%" if total_mismatches > 0 else "0.0%"
            c1 = ws_summary.cell(row=curr_row, column=1, value=m_name)
            c2 = ws_summary.cell(row=curr_row, column=2, value=count)
            c3 = ws_summary.cell(row=curr_row, column=3, value=pct)

            c2.alignment = Alignment(horizontal="right")
            c3.alignment = Alignment(horizontal="right")

            fill, _ = get_row_fill_and_font(m_name)
            for c in (c1, c2, c3):
                c.font = FONT_REGULAR
                c.border = THIN_BORDER
                if fill:
                    c.fill = fill
            curr_row += 1

        # Total Row
        ws_summary.cell(row=curr_row, column=1, value="รวมทั้งหมด").font = FONT_BOLD
        ws_summary.cell(row=curr_row, column=2, value=total_mismatches).font = FONT_BOLD
        ws_summary.cell(row=curr_row, column=3, value="100.0%").font = FONT_BOLD
        for col_idx in (1, 2, 3):
            ws_summary.cell(row=curr_row, column=col_idx).border = THIN_BORDER
        curr_row += 2

        # Asset Type Table
        ws_summary.cell(row=curr_row, column=1, value="จำแนกตามประเภท Asset").font = FONT_SUBTITLE
        curr_row += 1
        for col_idx, h in enumerate(["ประเภท Asset", "จำนวน (รายการ)", "สัดส่วน (%)"], start=1):
            c = ws_summary.cell(row=curr_row, column=col_idx, value=h)
            c.font = FONT_HEADER
            c.fill = FILL_HEADER_LIGHT
            c.alignment = Alignment(horizontal="center")
            c.border = THIN_BORDER
        curr_row += 1

        atype_breakdown = summary_data.get("asset_type_breakdown", {})
        for atype, count in atype_breakdown.items():
            pct = f"{(count / total_mismatches * 100):.1f}%" if total_mismatches > 0 else "0.0%"
            c1 = ws_summary.cell(row=curr_row, column=1, value=atype)
            c2 = ws_summary.cell(row=curr_row, column=2, value=count)
            c3 = ws_summary.cell(row=curr_row, column=3, value=pct)
            c2.alignment = Alignment(horizontal="right")
            c3.alignment = Alignment(horizontal="right")
            for c in (c1, c2, c3):
                c.font = FONT_REGULAR
                c.border = THIN_BORDER
            curr_row += 1

        curr_row += 2

        # Legend Table
        ws_summary.cell(row=curr_row, column=1, value="คำอธิบายสี (Color Legend)").font = FONT_SUBTITLE
        curr_row += 1
        legend_items = [
            ("รหัสพนักงาน + แผนกไม่ตรง", FILL_BOTH_MISMATCH, "รหัสพนักงานและแผนกใน IT ไม่ตรงกับ ERP AX"),
            ("รหัสพนักงานไม่ตรง", FILL_EMP_MISMATCH, "รหัสพนักงานไม่ตรงกัน แต่แผนกตรงกัน"),
            ("แผนกไม่ตรง", FILL_DEPT_MISMATCH, "แผนกไม่ตรงกัน หรือใน ERP ไม่มีแผนก/รออัปเดต"),
            ("ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน", FILL_SCRAPPED, "ใน ERP มีสถานะ Scrapped / ตัดจำหน่ายแล้ว"),
            ("ไม่พบในระบบ ERP (มีเฉพาะใน IT)", FILL_MISSING_ERP, "ไม่มีรหัสทรัพย์สินนี้ใน Master ERP")
        ]
        for l_title, l_fill, l_desc in legend_items:
            c1 = ws_summary.cell(row=curr_row, column=1, value=l_title)
            c2 = ws_summary.cell(row=curr_row, column=2, value=l_desc)
            c1.fill = l_fill
            c1.font = FONT_BOLD
            c2.font = FONT_REGULAR
            c1.border = THIN_BORDER
            c2.border = THIN_BORDER
            curr_row += 1

        # -------------------------------------------------------------
        # Helper: Create Record Table Sheet
        # -------------------------------------------------------------
        def write_record_sheet(sheet_title: str, records_list: List[Dict[str, Any]]):
            ws = wb.create_sheet(title=sheet_title)
            ws.views.sheetView[0].showGridLines = True

            headers = [
                "IT Record ID",
                "IT รหัสพนักงาน",
                "IT ชื่อพนักงาน",
                "IT สถานที่เก็บ (แผนก)",
                "รหัสทรัพย์สิน",
                "ประเภท Asset",
                "ประเภท Mismatch",
                "AX ชื่อพนักงาน",
                "AX รหัสพนักงาน",
                "AX แผนก",
                "AX ชื่อทรัพย์สิน",
                "AX สถานะ",
                "แนวทางแก้ไข (IT Action)"
            ]

            for col_idx, h in enumerate(headers, start=1):
                c = ws.cell(row=1, column=col_idx, value=h)
                c.font = FONT_HEADER
                c.fill = FILL_HEADER
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                c.border = THIN_BORDER
            ws.row_dimensions[1].height = 28

            for r_idx, rec in enumerate(records_list, start=2):
                ax = rec.get("ax_data", {})
                m_type = rec.get("mismatch_type", "")

                if "รหัสพนักงาน + แผนก" in m_type:
                    action = "ตรวจสอบการโอนย้ายทรัพย์สินและผู้ถือครองจริง"
                elif "รหัสพนักงาน" in m_type:
                    action = "ปรับรหัสพนักงานใน IT ให้ตรงกับ ERP หรือแจ้งย้ายสิทธิ์"
                elif "แผนก" in m_type:
                    action = "ปรับแผนกใน IT ให้ตรงกับ ERP หรือตรวจสอบหน่วยงาน"
                elif "ตัดจำหน่าย" in m_type:
                    action = "ตรวจสอบเพื่อตัดจำหน่ายออกจาก IT Inventory"
                elif "ไม่พบ" in m_type:
                    action = "ตรวจสอบเลขที่ทรัพย์สิน หรือลงทะเบียนเข้าระบบ ERP"
                else:
                    action = "ตรวจสอบข้อมูล"

                row_vals = [
                    rec.get("it_record_id", ""),
                    rec.get("it_emp_id", ""),
                    rec.get("it_emp_name", ""),
                    rec.get("it_dept", ""),
                    rec.get("asset_id", ""),
                    rec.get("it_asset_type", ""),
                    m_type,
                    ax.get("ax_emp_name", ""),
                    ax.get("ax_emp_id", ""),
                    ax.get("ax_dept", ""),
                    ax.get("ax_asset_name", ""),
                    ax.get("ax_status", ""),
                    action
                ]

                fill, font_color = get_row_fill_and_font(m_type)

                for c_idx, val in enumerate(row_vals, start=1):
                    cell = ws.cell(row=r_idx, column=c_idx, value=val)
                    cell.font = FONT_REGULAR
                    cell.border = THIN_BORDER
                    cell.alignment = Alignment(vertical="center")

                    if c_idx == 7 and fill:
                        cell.fill = fill
                        cell.font = font_color

                    if c_idx == 2 and "emp_id" in rec.get("diff_fields", []):
                        cell.font = FONT_RED
                    if c_idx == 4 and "dept" in rec.get("diff_fields", []):
                        cell.font = FONT_ORANGE

                ws.row_dimensions[r_idx].height = 20

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # -------------------------------------------------------------
        # Sheet 2: ทั้งหมด
        # -------------------------------------------------------------
        write_record_sheet(f"ทั้งหมด ({len(all_mismatches)})", all_mismatches)

        # -------------------------------------------------------------
        # Sub-sheets for specific mismatch categories
        # -------------------------------------------------------------
        cat_configs = [
            ("รหัสพนักงาน+แผนก", lambda r: "รหัสพนักงาน + แผนก" in r["mismatch_type"]),
            ("รหัสพนักงาน", lambda r: r["mismatch_type"] == "รหัสพนักงานไม่ตรง"),
            ("แผนก", lambda r: r["mismatch_type"] == "แผนกไม่ตรง"),
            ("ตัดจำหน่ายใน ERP", lambda r: "ตัดจำหน่าย" in r["mismatch_type"]),
            ("ไม่พบใน ERP", lambda r: "ไม่พบ" in r["mismatch_type"])
        ]

        for s_title, filter_fn in cat_configs:
            filtered_subset = [r for r in all_mismatches if filter_fn(r)]
            if filtered_subset:
                clean_title = f"{s_title} ({len(filtered_subset)})"[:31]
                write_record_sheet(clean_title, filtered_subset)

        for col in ws_summary.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_summary.column_dimensions[col_letter].width = max(max_len + 5, 14)

        return wb

    @classmethod
    def generate_mismatch_report_bytes(cls, comparator, category: Optional[str] = None) -> io.BytesIO:
        """Generate Excel mismatch report directly into in-memory BytesIO buffer."""
        wb = cls.build_mismatch_workbook(comparator, category)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    @classmethod
    def generate_mismatch_report_file(cls, comparator, output_path: str, category: Optional[str] = None) -> str:
        """Save report to file path with fallback to temp directory if write is restricted."""
        wb = cls.build_mismatch_workbook(comparator, category)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            wb.save(output_path)
            return output_path
        except Exception:
            fallback_dir = os.path.join(tempfile.gettempdir(), "fti_reports")
            os.makedirs(fallback_dir, exist_ok=True)
            fallback_path = os.path.join(fallback_dir, os.path.basename(output_path))
            wb.save(fallback_path)
            return fallback_path

    @staticmethod
    def export_corrected_inventory_bytes(comparator, category: str) -> io.BytesIO:
        """Export updated inventory dataframe directly into in-memory BytesIO buffer."""
        if category == "hw":
            df = comparator.hw_df.copy().astype(object)
            recs = comparator.records.get("hw", [])
            for r in recs:
                idx = r["row_index"]
                if idx in df.index:
                    df.at[idx, "รหัสพนักงาน"] = r["it_emp_id"]
                    df.at[idx, "ผู้ใช้งาน/ดูแล"] = r["it_emp_name"]
                    df.at[idx, "สถานที่เก็บ"] = r["it_dept"]
                    df.at[idx, "เลขที่ทรัพย์สิน"] = r["asset_id"]
                    df.at[idx, "S/N"] = r["it_sn"]
        elif category == "sw":
            df = comparator.sw_df.copy().astype(object)
            recs = comparator.records.get("sw", [])
            for r in recs:
                idx = r["row_index"]
                if idx in df.index:
                    df.at[idx, "รหัสพนักงาน"] = r["it_emp_id"]
                    df.at[idx, "ผู้ดูแล"] = r["it_emp_name"]
                    df.at[idx, "สถานที่เก็บ"] = r["it_dept"]
                    df.at[idx, "เลขที่ทรัพย์สิน"] = r["asset_id"]
                    df.at[idx, "Key License"] = r["it_sn"]
        elif category == "ups":
            df = comparator.ups_df.copy().astype(object)
            recs = comparator.records.get("ups", [])
            for r in recs:
                idx = r["row_index"]
                if idx in df.index:
                    df.at[idx, "รหัสพนักงาน"] = r["it_emp_id"]
                    df.at[idx, "ผู้ใช้งาน/ดูแล"] = r["it_emp_name"]
                    df.at[idx, "สถานที่เก็บ"] = r["it_dept"]
                    df.at[idx, "เลขที่ทรัพย์สิน"] = r["asset_id"]
                    df.at[idx, "S/N"] = r["it_sn"]
        else:
            raise ValueError(f"Unknown category: {category}")

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buf.seek(0)
        return buf
