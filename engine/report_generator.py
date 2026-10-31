import os
import io
import copy
import zipfile
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
FILL_MATCH_GREEN = PatternFill(start_color="FFD1FAE5", end_color="FFD1FAE5", fill_type="solid")   # Soft emerald green
FILL_USER_EDITED = PatternFill(start_color="FFE0F2FE", end_color="FFE0F2FE", fill_type="solid")   # Soft sky blue
FILL_HEADER = PatternFill(start_color="FF1E293B", end_color="FF1E293B", fill_type="solid")        # Dark slate
FILL_HEADER_LIGHT = PatternFill(start_color="FF334155", end_color="FF334155", fill_type="solid")  # Slate
FILL_HEADER_GREEN = PatternFill(start_color="FF15803D", end_color="FF15803D", fill_type="solid")  # Forest green
FILL_HEADER_RED = PatternFill(start_color="FFB91C1C", end_color="FFB91C1C", fill_type="solid")    # Deep red

FONT_HEADER = Font(name="TH Sarabun New", size=13, bold=True, color="FFFFFFFF")
FONT_REGULAR = Font(name="TH Sarabun New", size=11, bold=False, color="FF000000")
FONT_BOLD = Font(name="TH Sarabun New", size=11, bold=True, color="FF000000")
FONT_TITLE = Font(name="TH Sarabun New", size=16, bold=True, color="FF0F172A")
FONT_SUBTITLE = Font(name="TH Sarabun New", size=13, bold=True, color="FF1E293B")
FONT_RED = Font(name="TH Sarabun New", size=11, bold=True, color="FFFF0000")
FONT_ORANGE = Font(name="TH Sarabun New", size=11, bold=True, color="FFD35400")
FONT_GREEN = Font(name="TH Sarabun New", size=11, bold=True, color="FF15803D")

THIN_BORDER = Border(
    left=Side(style='thin', color='FFCBD5E1'),
    right=Side(style='thin', color='FFCBD5E1'),
    top=Side(style='thin', color='FFCBD5E1'),
    bottom=Side(style='thin', color='FFCBD5E1')
)

def get_row_fill_and_font(mismatch_type: str) -> tuple:
    """Return background fill and font based on mismatch type."""
    if not mismatch_type or mismatch_type == "ตรงกันสมบูรณ์":
        return FILL_MATCH_GREEN, FONT_GREEN
    elif "รหัสพนักงาน + แผนก" in mismatch_type:
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
    """Generates 4-Tab category Excel files and ZIP bundles reflecting exact cell state."""

    @staticmethod
    def _write_dataframe_to_sheet(ws, df: pd.DataFrame, header_fill=FILL_HEADER, highlight_col_name: Optional[str] = None):
        """Write a pandas DataFrame into an openpyxl worksheet with clean styling."""
        ws.views.sheetView[0].showGridLines = True
        cols = list(df.columns)

        # Write headers
        for col_idx, col_name in enumerate(cols, start=1):
            c = ws.cell(row=1, column=col_idx, value=str(col_name))
            c.font = FONT_HEADER
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = THIN_BORDER
        ws.row_dimensions[1].height = 26

        highlight_col_idx = (cols.index(highlight_col_name) + 1) if (highlight_col_name and highlight_col_name in cols) else None

        # Write rows
        for r_pos, (_, row) in enumerate(df.iterrows(), start=2):
            for c_idx, col_name in enumerate(cols, start=1):
                val = row[col_name]
                if pd.isna(val):
                    val = ""
                cell = ws.cell(row=r_pos, column=c_idx, value=val)
                cell.font = FONT_REGULAR
                cell.border = THIN_BORDER
                cell.alignment = Alignment(vertical="center")

                if highlight_col_idx and c_idx == highlight_col_idx:
                    s_val = str(val)
                    fill, f_color = get_row_fill_and_font(s_val)
                    if fill:
                        cell.fill = fill
                    if f_color:
                        cell.font = f_color
            ws.row_dimensions[r_pos].height = 20

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max((len(str(cell.value or '')) for cell in col[:250]), default=10)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 48)

    @classmethod
    def build_category_4tab_workbook(cls, comparator, category: str) -> openpyxl.Workbook:
        """
        Build the 4-Tab Excel workbook for a specific category (hw, sw, ups):
        1. 1_ข้อมูลเดิม (Original untouched data & columns from orig_cells)
        2. 2_เปรียบเทียบชี้จุดต่าง (Side-by-side comparison & diff highlighting & user edit notes)
        3. 3_ข้อมูลแก้ไขแล้ว_100% (Latest cells of active inventory with exact original columns)
        4. 4_ข้อมูลที่ถูกตัดออก (Excluded records with exact original columns + exclusion reason & ERP info)
        """
        from engine.comparator import COLUMN_MAP

        if category not in ("hw", "sw", "ups"):
            raise ValueError(f"Unknown category: {category}")

        recs = comparator.records.get(category, [])
        cols = comparator.columns.get(category, [])
        if not cols and recs:
            cols = list(recs[0]["cells"].keys())

        cmap = COLUMN_MAP.get(category, {})

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        # =====================================================================
        # TAB 1: 1_ข้อมูลเดิม (Original Untouched Data)
        # =====================================================================
        ws_orig = wb.create_sheet(title="1_ข้อมูลเดิม")
        orig_rows = []
        for r in recs:
            orig_rows.append(r.get("orig_cells", r.get("cells", {})))
        df_orig = pd.DataFrame(orig_rows, columns=cols)
        cls._write_dataframe_to_sheet(ws_orig, df_orig, header_fill=FILL_HEADER)

        # =====================================================================
        # TAB 2: 2_เปรียบเทียบชี้จุดต่าง (Detailed Diff & Resolution Sheet)
        # =====================================================================
        ws_comp = wb.create_sheet(title="2_เปรียบเทียบชี้จุดต่าง")
        ws_comp.views.sheetView[0].showGridLines = True

        comp_headers = [
            "ลำดับ",
            "IT Record ID",
            "เลขที่ทรัพย์สิน",
            "ประเภท Asset",
            "ชื่อทรัพย์สิน / Software",
            "IT รหัสพนักงาน (เดิม)",
            "IT ชื่อผู้ใช้งาน (เดิม)",
            "IT สถานที่เก็บ/แผนก (เดิม)",
            "จุดต่างก่อนแก้ไข (Mismatch)",
            "ERP รหัสพนักงาน (AX)",
            "ERP ชื่อพนักงาน (AX)",
            "ERP แผนก (AX)",
            "ERP สถานะ (AX)",
            "การดำเนินการของระบบ",
            "ผลลัพธ์หลังตรวจซ้ำ",
            "คอลัมน์ที่ผู้ใช้แก้ไขเอง"
        ]

        for col_idx, h in enumerate(comp_headers, start=1):
            c = ws_comp.cell(row=1, column=col_idx, value=h)
            c.font = FONT_HEADER
            c.fill = FILL_HEADER_LIGHT
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = THIN_BORDER
        ws_comp.row_dimensions[1].height = 28

        active_rows = []
        excluded_rows = []

        for row_num, r in enumerate(recs, start=2):
            orig_cells = r.get("orig_cells", {})
            curr_cells = r.get("cells", {})
            ax = r.get("ax_data", {})
            m_type = r.get("mismatch_type", "")
            diffs = r.get("diff_fields", [])
            user_edited = r.get("user_edited_cols", [])

            orig_aid = orig_cells.get(cmap.get("asset_id", ""), "")
            orig_emp_id = orig_cells.get(cmap.get("emp_id", ""), "")
            orig_emp_name = orig_cells.get(cmap.get("emp_name", ""), "")
            orig_dept = orig_cells.get(cmap.get("dept", ""), "")

            action_taken = "คงค่าเดิม"
            if r.get("is_excluded"):
                action_taken = f"คัดออกไปยังแท็บ 4 ({r.get('exclude_reason', '')})"
                final_status = "ถูกตัดออกหลังเปรียบเทียบ"
            elif user_edited:
                action_taken = f"แก้ไขโดยผู้ใช้ ({', '.join(user_edited)})"
                final_status = "ตรงกันสมบูรณ์ 100%" if r.get("is_match") else "ผู้ใช้ปรับแต่งเอง (ต่างจาก ERP)"
            elif r.get("is_match"):
                action_taken = "ซิงค์ตรงกับ ERP 100%" if m_type != "ตรงกันสมบูรณ์" else "ข้อมูลตรงกับ ERP อยู่แล้ว"
                final_status = "ตรงกันสมบูรณ์ 100% (ผ่านตรวจซ้ำ 3 รอบ)"
            else:
                action_taken = "รอการแก้ไข"
                final_status = m_type

            row_vals = [
                row_num - 1,
                curr_cells.get("Record-ID") or curr_cells.get("IdAssetRecId") or "",
                orig_aid,
                curr_cells.get("ประเภททรัพย์สิน") or ("Software" if category == "sw" else "PC/Monitor"),
                curr_cells.get("ชื่อทรัพย์สิน") or curr_cells.get("ชื่อ Software") or "",
                orig_emp_id,
                orig_emp_name,
                orig_dept,
                m_type,
                ax.get("ax_emp_id", ""),
                ax.get("ax_emp_name", ""),
                ax.get("ax_dept", ""),
                ax.get("ax_status", ""),
                action_taken,
                final_status,
                ", ".join(user_edited) if user_edited else "-"
            ]

            fill_m, font_m = get_row_fill_and_font(m_type)

            for c_idx, val in enumerate(row_vals, start=1):
                cell = ws_comp.cell(row=row_num, column=c_idx, value=val)
                cell.font = FONT_REGULAR
                cell.border = THIN_BORDER
                cell.alignment = Alignment(vertical="center")

                # Highlight original mismatch badge column
                if c_idx == 9:
                    if m_type == "ตรงกันสมบูรณ์":
                        cell.fill = FILL_MATCH_GREEN
                        cell.font = FONT_GREEN
                    elif fill_m:
                        cell.fill = fill_m
                        cell.font = font_m

                # Highlight diff cells on IT side
                if c_idx in (6, 7) and "emp_id" in diffs:
                    cell.fill = FILL_EMP_MISMATCH
                    cell.font = FONT_RED
                if c_idx == 8 and "dept" in diffs:
                    cell.fill = FILL_DEPT_MISMATCH
                    cell.font = FONT_ORANGE

                # Highlight final status column
                if c_idx == 15:
                    if r.get("is_excluded"):
                        cell.fill = FILL_SCRAPPED if "ตัดจำหน่าย" in m_type else FILL_MISSING_ERP
                        cell.font = FONT_ORANGE if "ตัดจำหน่าย" in m_type else FONT_BOLD
                    elif r.get("is_match"):
                        cell.fill = FILL_MATCH_GREEN
                        cell.font = FONT_GREEN
                    elif user_edited:
                        cell.fill = FILL_USER_EDITED
                        cell.font = FONT_BOLD

                # User edited column
                if c_idx == 16 and user_edited:
                    cell.fill = FILL_USER_EDITED
                    cell.font = FONT_BOLD

            ws_comp.row_dimensions[row_num].height = 20

            # Partition for Tab 3 & Tab 4
            if r.get("is_excluded"):
                ex_row = copy.deepcopy(curr_cells)
                ex_row["สาเหตุที่ถูกตัดออก"] = r.get("exclude_reason") or m_type
                ex_row["AX สถานะใน ERP"] = ax.get("ax_status", "ไม่พบใน ERP" if not ax else "ตัดจำหน่าย")
                ex_row["AX ชื่อทรัพย์สินใน ERP"] = ax.get("ax_asset_name", "")
                ex_row["AX รหัสพนักงานใน ERP"] = ax.get("ax_emp_id", "")
                ex_row["AX ชื่อพนักงานใน ERP"] = ax.get("ax_emp_name", "")
                ex_row["AX แผนกใน ERP"] = ax.get("ax_dept", "")
                excluded_rows.append(ex_row)
            else:
                active_rows.append(copy.deepcopy(curr_cells))

        for col in ws_comp.columns:
            max_len = max((len(str(cell.value or '')) for cell in col[:250]), default=10)
            col_letter = get_column_letter(col[0].column)
            ws_comp.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)

        # =====================================================================
        # TAB 3: 3_ข้อมูลแก้ไขแล้ว_100% (Active Reconciled Inventory)
        # =====================================================================
        ws_tab3 = wb.create_sheet(title="3_ข้อมูลแก้ไขแล้ว_100%")
        df_tab3 = pd.DataFrame(active_rows, columns=cols)
        cls._write_dataframe_to_sheet(ws_tab3, df_tab3, header_fill=FILL_HEADER_GREEN)

        # =====================================================================
        # TAB 4: 4_ข้อมูลที่ถูกตัดออก (Excluded Inventory)
        # =====================================================================
        extra_cols = [
            "สาเหตุที่ถูกตัดออก",
            "AX สถานะใน ERP",
            "AX ชื่อทรัพย์สินใน ERP",
            "AX รหัสพนักงานใน ERP",
            "AX ชื่อพนักงานใน ERP",
            "AX แผนกใน ERP"
        ]
        ws_tab4 = wb.create_sheet(title="4_ข้อมูลที่ถูกตัดออก")
        df_tab4 = pd.DataFrame(excluded_rows, columns=cols + extra_cols)
        cls._write_dataframe_to_sheet(ws_tab4, df_tab4, header_fill=FILL_HEADER_RED, highlight_col_name="สาเหตุที่ถูกตัดออก")

        return wb

    @classmethod
    def export_corrected_inventory_bytes(cls, comparator, category: str) -> io.BytesIO:
        """Export 4-Tab inventory workbook into BytesIO."""
        wb = cls.build_category_4tab_workbook(comparator, category)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    @classmethod
    def save_all_category_files(cls, comparator, output_dir: str) -> Dict[str, str]:
        """Save all compared category 4-tab Excel files into output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        file_map = {
            "hw": "1-it_asset_HW.xlsx",
            "sw": "2-it_asset_SW.xlsx",
            "ups": "3-it_asset_UPS_Monitor.xlsx"
        }
        saved_paths = {}
        for cat, fname in file_map.items():
            if comparator.category_states.get(cat) == "compared" and len(comparator.records.get(cat, [])) > 0:
                wb = cls.build_category_4tab_workbook(comparator, cat)
                target_path = os.path.join(output_dir, fname)
                wb.save(target_path)
                saved_paths[cat] = target_path
        return saved_paths

    @classmethod
    def export_all_inventories_zip_bytes(cls, comparator) -> io.BytesIO:
        """Export all compared 4-tab Excel files into a single ZIP archive."""
        file_map = {
            "hw": "1-it_asset_HW.xlsx",
            "sw": "2-it_asset_SW.xlsx",
            "ups": "3-it_asset_UPS_Monitor.xlsx"
        }
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for cat, fname in file_map.items():
                if comparator.category_states.get(cat) == "compared" and len(comparator.records.get(cat, [])) > 0:
                    excel_buf = cls.export_corrected_inventory_bytes(comparator, cat)
                    zf.writestr(fname, excel_buf.getvalue())
        zip_buf.seek(0)
        return zip_buf
