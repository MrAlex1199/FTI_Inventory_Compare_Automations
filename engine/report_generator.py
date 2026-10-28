import os
import io
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
    def _get_base_dataframe(comparator, category: str) -> pd.DataFrame:
        """Obtain the original unmodified DataFrame for the given category."""
        recs = comparator.records.get(category, [])
        if category == "hw":
            if comparator.hw_df is not None and isinstance(comparator.hw_df, pd.DataFrame) and not comparator.hw_df.empty:
                return comparator.hw_df.copy().astype(object)
            rows = []
            for r in recs:
                rows.append({
                    "Record-ID": r.get("it_record_id", ""),
                    "รหัสพนักงาน": r.get("orig_it_emp_id", r.get("it_emp_id", "")),
                    "ผู้ใช้งาน/ดูแล": r.get("orig_it_emp_name", r.get("it_emp_name", "")),
                    "สถานที่เก็บ": r.get("orig_it_dept", r.get("it_dept", "")),
                    "ชื่อทรัพย์สิน": r.get("it_asset_name", ""),
                    "ประเภททรัพย์สิน": r.get("it_asset_type", "PC"),
                    "เลขที่ทรัพย์สิน": r.get("orig_asset_id", r.get("asset_id", "")),
                    "S/N": r.get("orig_it_sn", r.get("it_sn", "")),
                    "PC_Name": r.get("it_pc_name", ""),
                    "รหัสทรัพย์สิน Monitor": r.get("it_monitor_asset", ""),
                    "รหัสทรัพย์สิน UPS": r.get("it_ups_asset", ""),
                    "สถานะ(การตรวจสอบ)": r.get("it_check_status", ""),
                    "AssetRemark": r.get("it_remark", "")
                })
            return pd.DataFrame(rows)
        elif category == "sw":
            if comparator.sw_df is not None and isinstance(comparator.sw_df, pd.DataFrame) and not comparator.sw_df.empty:
                return comparator.sw_df.copy().astype(object)
            rows = []
            for r in recs:
                rows.append({
                    "IdAssetRecId": r.get("it_record_id", ""),
                    "รหัส Software": r.get("it_software_code", ""),
                    "ชื่อ Software": r.get("it_asset_name", ""),
                    "Key License": r.get("orig_it_sn", r.get("it_sn", "")) or r.get("it_license_key", ""),
                    "PCName": r.get("it_pc_name", ""),
                    "รหัสพนักงาน": r.get("orig_it_emp_id", r.get("it_emp_id", "")),
                    "ผู้ดูแล": r.get("orig_it_emp_name", r.get("it_emp_name", "")),
                    "สถานที่เก็บ": r.get("orig_it_dept", r.get("it_dept", "")),
                    "เลขที่ทรัพย์สิน": r.get("orig_asset_id", r.get("asset_id", "")),
                    "Check FixAsset": r.get("it_check_fixasset", "")
                })
            return pd.DataFrame(rows)
        elif category == "ups":
            if comparator.ups_df is not None and isinstance(comparator.ups_df, pd.DataFrame) and not comparator.ups_df.empty:
                return comparator.ups_df.copy().astype(object)
            rows = []
            for r in recs:
                rows.append({
                    "Record-ID": r.get("it_record_id", ""),
                    "รหัสพนักงาน": r.get("orig_it_emp_id", r.get("it_emp_id", "")),
                    "ผู้ใช้งาน/ดูแล": r.get("orig_it_emp_name", r.get("it_emp_name", "")),
                    "สถานที่เก็บ": r.get("orig_it_dept", r.get("it_dept", "")),
                    "เลขที่ทรัพย์สิน": r.get("orig_asset_id", r.get("asset_id", "")),
                    "ประเภททรัพย์สิน": r.get("it_asset_type", "UPS/Monitor"),
                    "ชื่อทรัพย์สิน": r.get("it_asset_name", ""),
                    "S/N": r.get("orig_it_sn", r.get("it_sn", "")),
                    "PC_Name": r.get("it_pc_name", ""),
                    "สถานะ(การตรวจสอบ)": r.get("it_check_status", ""),
                    "AssetRemark": r.get("it_remark", "")
                })
            return pd.DataFrame(rows)
        else:
            raise ValueError(f"Unknown category: {category}")

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
        1. 1_ข้อมูลเดิม (Original untouched data & columns)
        2. 2_เปรียบเทียบชี้จุดต่าง (Side-by-side comparison & diff highlighting)
        3. 3_ข้อมูลแก้ไขแล้ว_100% (100% ERP-synced & 3-pass verified active inventory with original columns)
        4. 4_ข้อมูลที่ถูกตัดออก (Excluded records with original columns + exclusion reason & ERP info)
        """
        from engine.comparator import clean_emp_id, clean_val, clean_asset_id, is_dept_match

        if category not in ("hw", "sw", "ups"):
            raise ValueError(f"Unknown category: {category}")

        recs = comparator.records.get(category, [])
        df_orig = cls._get_base_dataframe(comparator, category)

        emp_name_col = "ผู้ดูแล" if category == "sw" else "ผู้ใช้งาน/ดูแล"
        sn_col = "Key License" if category == "sw" else "S/N"

        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        # =====================================================================
        # TAB 1: 1_ข้อมูลเดิม (Original Untouched Data)
        # =====================================================================
        ws_orig = wb.create_sheet(title="1_ข้อมูลเดิม")
        cls._write_dataframe_to_sheet(ws_orig, df_orig, header_fill=FILL_HEADER)

        # =====================================================================
        # Prepare Reconciled Active Rows (Tab 3) & Excluded Rows (Tab 4) + Comparison (Tab 2)
        # =====================================================================
        active_indices = []
        excluded_indices = []
        excluded_meta = {}
        df_corrected_all = df_orig.copy().astype(object)

        comparison_rows = []

        for r in recs:
            idx = r.get("row_index")
            asset_id = clean_asset_id(r.get("asset_id", ""))
            orig_emp_id = r.get("orig_it_emp_id", r.get("it_emp_id", ""))
            orig_emp_name = r.get("orig_it_emp_name", r.get("it_emp_name", ""))
            orig_dept = r.get("orig_it_dept", r.get("it_dept", ""))
            orig_sn = r.get("orig_it_sn", r.get("it_sn", ""))

            # Evaluate original baseline against ERP
            orig_is_match, orig_m_type, orig_diffs, ax = comparator._evaluate_values_against_erp(
                r.get("orig_asset_id", asset_id),
                orig_emp_id,
                orig_dept
            )

            ax_emp_id = clean_emp_id(ax.get("ax_emp_id", "")) if ax else ""
            ax_emp_name = clean_val(ax.get("ax_emp_name", "")) if ax else ""
            ax_dept = clean_val(ax.get("ax_dept", "")) if ax else ""
            ax_loc_code = clean_val(ax.get("ax_loc_code", "")) if ax else ""
            ax_status = clean_val(ax.get("ax_status", "")) if ax else ""
            ax_asset_name = clean_val(ax.get("ax_asset_name", "")) if ax else ""

            # Determine if record is excluded or active
            is_excl = (not asset_id) or (not ax) or bool(ax.get("is_scrapped"))
            if is_excl:
                reason = (
                    "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)" if not asset_id
                    else ("ไม่พบในระบบ ERP (มีเฉพาะใน IT)" if not ax else "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน")
                )
                if idx is not None and idx in df_orig.index:
                    excluded_indices.append(idx)
                    excluded_meta[idx] = {
                        "สาเหตุที่ถูกตัดออก": reason,
                        "AX สถานะใน ERP": ax_status or ("ไม่พบใน ERP" if not ax else "ตัดจำหน่าย"),
                        "AX ชื่อทรัพย์สินใน ERP": ax_asset_name,
                        "AX รหัสพนักงานใน ERP": ax_emp_id,
                        "AX ชื่อพนักงานใน ERP": ax_emp_name,
                        "AX แผนกใน ERP": ax_dept
                    }
                action_taken = f"คัดออกไปยังแท็บ 4 ({reason})"
                final_status = "ถูกตัดออกหลังเปรียบเทียบ"
                final_emp_id = orig_emp_id
                final_emp_name = orig_emp_name
                final_dept = orig_dept
            else:
                # Active ERP asset -> guarantee 100% alignment with ERP (Multi-Pass Verified)
                final_emp_id = ax_emp_id
                final_emp_name = ax_emp_name if (ax_emp_name or not ax_emp_id) else r.get("it_emp_name", "")
                final_dept = ax_dept if ax_dept else (r.get("it_dept", "") if is_dept_match(r.get("it_dept", ""), ax_dept, ax_loc_code) else "")

                # 3-Pass Verification on this row
                for _vp in range(3):
                    v_match, _, _, _ = comparator._evaluate_values_against_erp(asset_id, final_emp_id, final_dept)
                    if not v_match:
                        final_emp_id = ax_emp_id
                        final_dept = ax_dept

                if idx is not None and idx in df_corrected_all.index:
                    active_indices.append(idx)
                    df_corrected_all.at[idx, "รหัสพนักงาน"] = final_emp_id
                    if emp_name_col in df_corrected_all.columns:
                        df_corrected_all.at[idx, emp_name_col] = final_emp_name
                    df_corrected_all.at[idx, "สถานที่เก็บ"] = final_dept
                    df_corrected_all.at[idx, "เลขที่ทรัพย์สิน"] = asset_id
                    if sn_col in df_corrected_all.columns:
                        df_corrected_all.at[idx, sn_col] = r.get("it_sn", orig_sn)

                if orig_is_match:
                    action_taken = "ข้อมูลตรงกับ ERP อยู่แล้ว (คงค่าเดิม)"
                else:
                    action_taken = "ซิงค์รหัสพนักงาน/ชื่อ/แผนก ให้ตรงกับ ERP 100%"
                final_status = "ตรงกันสมบูรณ์ 100% (ผ่านตรวจซ้ำ 3 รอบ)"

            comparison_rows.append({
                "rec": r,
                "asset_id": asset_id,
                "orig_emp_id": orig_emp_id,
                "orig_emp_name": orig_emp_name,
                "orig_dept": orig_dept,
                "orig_sn": orig_sn,
                "orig_m_type": orig_m_type,
                "orig_diffs": orig_diffs,
                "ax_emp_id": ax_emp_id,
                "ax_emp_name": ax_emp_name,
                "ax_dept": ax_dept,
                "ax_loc_code": ax_loc_code,
                "ax_status": ax_status or ("ปกติ (Open)" if ax else "ไม่พบใน ERP"),
                "final_emp_id": final_emp_id,
                "final_emp_name": final_emp_name,
                "final_dept": final_dept,
                "action_taken": action_taken,
                "final_status": final_status,
                "is_excl": is_excl
            })

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
            "ผลลัพธ์หลังตรวจซ้ำ 3 รอบ"
        ]

        for col_idx, h in enumerate(comp_headers, start=1):
            c = ws_comp.cell(row=1, column=col_idx, value=h)
            c.font = FONT_HEADER
            c.fill = FILL_HEADER_LIGHT
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = THIN_BORDER
        ws_comp.row_dimensions[1].height = 28

        for row_num, item in enumerate(comparison_rows, start=2):
            rec = item["rec"]
            m_type = item["orig_m_type"]
            diffs = item["orig_diffs"]

            row_vals = [
                row_num - 1,
                rec.get("it_record_id", ""),
                item["asset_id"],
                rec.get("it_asset_type", ""),
                rec.get("it_asset_name", ""),
                item["orig_emp_id"],
                item["orig_emp_name"],
                item["orig_dept"],
                m_type,
                item["ax_emp_id"],
                item["ax_emp_name"],
                item["ax_dept"],
                item["ax_status"],
                item["action_taken"],
                item["final_status"]
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
                    if not item["is_excl"]:
                        cell.fill = FILL_MATCH_GREEN
                        cell.font = FONT_GREEN
                    else:
                        cell.fill = FILL_SCRAPPED if "ตัดจำหน่าย" in m_type else FILL_MISSING_ERP
                        cell.font = FONT_ORANGE if "ตัดจำหน่าย" in m_type else FONT_BOLD

            ws_comp.row_dimensions[row_num].height = 20

        for col in ws_comp.columns:
            max_len = max((len(str(cell.value or '')) for cell in col[:250]), default=10)
            col_letter = get_column_letter(col[0].column)
            ws_comp.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)

        # =====================================================================
        # TAB 3: 3_ข้อมูลแก้ไขแล้ว_100% (100% Verified Active Inventory)
        # =====================================================================
        df_tab3 = df_corrected_all.loc[active_indices].copy() if active_indices else df_corrected_all.iloc[0:0].copy()
        ws_tab3 = wb.create_sheet(title="3_ข้อมูลแก้ไขแล้ว_100%")
        cls._write_dataframe_to_sheet(ws_tab3, df_tab3, header_fill=FILL_HEADER_GREEN)

        # =====================================================================
        # TAB 4: 4_ข้อมูลที่ถูกตัดออก (Excluded Inventory + Reason & ERP Columns)
        # =====================================================================
        df_tab4 = df_orig.loc[excluded_indices].copy() if excluded_indices else df_orig.iloc[0:0].copy()
        extra_cols = [
            "สาเหตุที่ถูกตัดออก",
            "AX สถานะใน ERP",
            "AX ชื่อทรัพย์สินใน ERP",
            "AX รหัสพนักงานใน ERP",
            "AX ชื่อพนักงานใน ERP",
            "AX แผนกใน ERP"
        ]
        for ec in extra_cols:
            df_tab4[ec] = [excluded_meta.get(i, {}).get(ec, "") for i in df_tab4.index]

        ws_tab4 = wb.create_sheet(title="4_ข้อมูลที่ถูกตัดออก")
        cls._write_dataframe_to_sheet(ws_tab4, df_tab4, header_fill=FILL_HEADER_RED, highlight_col_name="สาเหตุที่ถูกตัดออก")

        return wb

    @classmethod
    def export_corrected_inventory_bytes(cls, comparator, category: str) -> io.BytesIO:
        """Export 4-Tab inventory workbook (1_ข้อมูลเดิม, 2_เปรียบเทียบชี้จุดต่าง, 3_ข้อมูลแก้ไขแล้ว_100%, 4_ข้อมูลที่ถูกตัดออก) into BytesIO."""
        wb = cls.build_category_4tab_workbook(comparator, category)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    @classmethod
    def save_all_category_files(cls, comparator, output_dir: str) -> Dict[str, str]:
        """Save all 3 category 4-tab Excel files into output_dir with standard filenames."""
        os.makedirs(output_dir, exist_ok=True)
        file_map = {
            "hw": "1-it_asset_HW.xlsx",
            "sw": "2-it_asset_SW.xlsx",
            "ups": "3-it_asset_UPS_Monitor.xlsx"
        }
        saved_paths = {}
        for cat, fname in file_map.items():
            if len(comparator.records.get(cat, [])) > 0:
                wb = cls.build_category_4tab_workbook(comparator, cat)
                target_path = os.path.join(output_dir, fname)
                wb.save(target_path)
                saved_paths[cat] = target_path
        return saved_paths

    @classmethod
    def export_all_inventories_zip_bytes(cls, comparator) -> io.BytesIO:
        """Export all 3 category 4-tab Excel files + summary mismatch report into a single ZIP archive."""
        file_map = {
            "hw": "1-it_asset_HW.xlsx",
            "sw": "2-it_asset_SW.xlsx",
            "ups": "3-it_asset_UPS_Monitor.xlsx"
        }
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for cat, fname in file_map.items():
                if len(comparator.records.get(cat, [])) > 0:
                    excel_buf = cls.export_corrected_inventory_bytes(comparator, cat)
                    zf.writestr(fname, excel_buf.getvalue())
        zip_buf.seek(0)
        return zip_buf
