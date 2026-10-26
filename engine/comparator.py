import re
import os
import json
import uuid
import copy
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Department prefix to AX Location code & keyword mappings
DEPT_CODE_MAP = {
    "1001": {"codes": ["ADM"], "keywords": ["บริหาร", "สนง.บริหาร", "สำนักงานบริหาร", "สำนักงานเลขานุการบริษัท", "สำนักงานเลขา", "เลขา"]},
    "1001.1": {"codes": ["ADM"], "keywords": ["บริหาร", "สนง.บริหาร", "สำนักงานบริหาร"]},
    "1001.2": {"codes": ["ADT"], "keywords": ["ตรวจสอบภายใน", "ฝ่ายตรวจสอบภายใน", "ตรวจ"]},
    "1002": {"codes": ["ACC", "FIN", "CCD"], "keywords": ["บัญชี", "การเงิน", "บัญชีการเงิน", "ฝ่ายบัญชี", "ฝ่ายการเงิน"]},
    "1003": {"codes": ["RAD"], "keywords": ["วิจัย", "พัฒนา", "วิจัยและพัฒนา", "ฝ่ายพัฒนาธุรกิจผลิตภัณฑ์", "r&d"]},
    "1004": {"codes": ["ITD"], "keywords": ["สารสนเทศ", "เทคโนโลยี", "เทคโนโลยีและสารสนเทศ", "it"]},
    "1005": {"codes": ["SUP"], "keywords": ["ธุรการ", "ซ่อมบำรุง", "ธุรการซ่อมบำรุง", "ฝ่ายธุรการและซ่อมบำรุง"]},
    "1006": {"codes": ["HRD"], "keywords": ["บุคคล", "ทรัพยากรบุคคล", "จป", "ฝ่ายบริหารทรัพยากรบุคคล"]},
    "1007": {"codes": ["SAL", "AQK", "PUM"], "keywords": ["ขาย", "ฝ่ายขาย", "aquatek", "ปั๊ม", "วาล์ว", "sal"]},
    "1008": {"codes": ["SAL"], "keywords": ["ขาย", "ฝ่ายขาย", "support", "sale"]},
    "1009": {"codes": ["PRD", "PRO"], "keywords": ["ผลิต", "ฝ่ายผลิต", "ผลิตและบริการ"]},
    "1010": {"codes": ["LOG"], "keywords": ["คลัง", "จัดส่ง", "คลังสินค้า", "ฝ่ายคลังสินค้าและจัดส่ง"]},
    "1011": {"codes": ["LOG"], "keywords": ["จัดส่ง", "คลัง", "ฝ่ายคลังสินค้าและจัดส่ง"]},
    "1012": {"codes": ["PRI"], "keywords": ["จัดซื้อ", "จัดซื้อต่างประเทศ", "ฝ่ายจัดซื้อ"]},
    "1013": {"codes": ["PRL"], "keywords": ["จัดซื้อ", "จัดซื้อในประเทศ", "ฝ่ายจัดซื้อ"]},
    "1015": {"codes": ["ACC"], "keywords": ["เปิดบิล", "บัญชี", "ฝ่ายบัญชี"]},
    "1016": {"codes": ["MKT"], "keywords": ["ตลาด", "การตลาด", "ฝ่ายการตลาดและประชาสัมพันธ์"]},
    "9999": {"codes": ["JVC"], "keywords": ["ร่วมทุน", "บจ.ร่วมทุน"]},
}

def clean_val(val: Any) -> str:
    """Normalize general value to clean string."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", "<na>"):
        return ""
    return s

def clean_emp_id(val: Any) -> str:
    """Normalize employee ID (e.g. 16701002.0 -> '16701002')."""
    s = clean_val(val)
    if not s:
        return ""
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except (ValueError, TypeError):
        pass
    return s

def clean_asset_id(val: Any) -> str:
    """Normalize asset id by removing leading/trailing spaces and upper-casing."""
    s = clean_val(val)
    return s.upper()

def clean_dept_name(val: Any) -> str:
    """Clean department name removing slashes, prefixes and lowercase."""
    s = clean_val(val)
    if not s:
        return ""
    s = re.sub(r'^[0-9.]+\s*/\s*', '', s)
    s = re.sub(r'^(ฝ่าย|สำนักงาน|แผนก)\s*', '', s)
    s = s.replace(" ", "").lower()
    return s

def is_dept_match(it_dept_raw: Any, ax_dept_raw: Any, ax_loc_code: Any) -> bool:
    """
    Intelligent department comparison:
    1. If both are empty -> Match
    2. If one is empty and other isn't -> Mismatch
    3. Exact text match
    4. Code prefix mapping (e.g. '1004' in IT matches 'ITD' or 'เทคโนโลยีและสารสนเทศ' in AX)
    5. Substring inclusion
    """
    it_raw = clean_val(it_dept_raw)
    ax_raw = clean_val(ax_dept_raw)
    ax_code = clean_val(ax_loc_code).upper()

    if not it_raw and not ax_raw:
        return True
    if not it_raw or not ax_raw:
        return False

    it_clean = clean_dept_name(it_raw)
    ax_clean = clean_dept_name(ax_raw)

    if it_clean == ax_clean:
        return True

    # Check prefix code from IT e.g. 1004 from 1004/สารสนเทศ
    m = re.match(r'^([0-9.]+)', it_raw)
    if m:
        prefix = m.group(1)
        # Check specific prefix or base prefix (1001 from 1001.1)
        base_prefix = prefix.split('.')[0] if '.' in prefix else prefix
        rule = DEPT_CODE_MAP.get(prefix) or DEPT_CODE_MAP.get(base_prefix)
        if rule:
            # Check AX location code
            if ax_code and ax_code in rule["codes"]:
                return True
            # Check AX department keywords
            for kw in rule["keywords"]:
                if kw in ax_clean or ax_clean in kw:
                    return True

    # Cross keyword check
    if len(it_clean) >= 3 and len(ax_clean) >= 3:
        if it_clean in ax_clean or ax_clean in it_clean:
            return True

    return False

def is_scrapped(status_val: Any, search_name_val: Any) -> bool:
    """Check if asset is scrapped or sold in AX."""
    status_str = clean_val(status_val).lower()
    search_str = clean_val(search_name_val).lower()
    if status_str in ("scrapped", "closed", "ตัดจำหน่าย"):
        return True
    if "จำหน่าย" in search_str or "scrapped" in search_str:
        return True
    return False


class InventoryComparator:
    """Main comparison engine for ERP Master vs IT Inventory files."""

    def __init__(self):
        self.master_df: Optional[pd.DataFrame] = None
        self.master_dict: Dict[str, Dict[str, Any]] = {}
        
        # Raw Dataframes
        self.hw_df: Optional[pd.DataFrame] = None
        self.sw_df: Optional[pd.DataFrame] = None
        self.ups_df: Optional[pd.DataFrame] = None
        
        # Working editable records: Dict of category -> List of dicts
        self.records: Dict[str, List[Dict[str, Any]]] = {
            "hw": [],
            "sw": [],
            "ups": []
        }
        
        # Summary results cached
        self.summary: Dict[str, Any] = {}
        self.changelog: List[Dict[str, Any]] = []

        # Google Workspace-style Undo/Redo & Rollback stacks
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.autosave_path: Optional[str] = None
        self.sources_dir: Optional[str] = None

        # Filename tracking
        self.master_filename: Optional[str] = None
        self.hw_filename: Optional[str] = None
        self.sw_filename: Optional[str] = None
        self.ups_filename: Optional[str] = None

    def load_master(self, filepath_or_df) -> int:
        """Load and index the master ERP file."""
        if isinstance(filepath_or_df, pd.DataFrame):
            df = filepath_or_df.copy()
        else:
            df = pd.read_excel(filepath_or_df)
            
        self.master_df = df
        self.master_dict.clear()

        for idx, row in df.iterrows():
            asset_no = clean_asset_id(row.get("Fixed asset number"))
            if not asset_no:
                continue

            # AX Columns:
            # WorkName = AX Employee Name
            # Name2 = AX Department Name
            # Location = AX Location Code (e.g. ITD, HRD)
            # Responsible = AX Employee ID
            # Name = AX Asset Name
            # Serial number = AX S/N
            # Status = AX Status
            # Search name = AX Search Name
            self.master_dict[asset_no] = {
                "asset_id": asset_no,
                "ax_emp_name": clean_val(row.get("WorkName")),
                "ax_emp_id": clean_emp_id(row.get("Responsible")),
                "ax_dept": clean_val(row.get("Name2")),
                "ax_loc_code": clean_val(row.get("Location")),
                "ax_asset_name": clean_val(row.get("Name")),
                "ax_sn": clean_val(row.get("Serial number")),
                "ax_status": clean_val(row.get("Status")),
                "ax_search_name": clean_val(row.get("Search name")),
                "ax_group": clean_val(row.get("Fixed asset group")),
                "is_scrapped": is_scrapped(row.get("Status"), row.get("Search name")),
                "master_row_idx": idx
            }
        return len(self.master_dict)

    def load_inventory_files(self, hw_source, sw_source, ups_source) -> Dict[str, int]:
        """Load the three inventory files into internal records."""
        counts = {}

        # 1. Hardware
        if hw_source is not None:
            self.hw_df = hw_source if isinstance(hw_source, pd.DataFrame) else pd.read_excel(hw_source)
            self.records["hw"] = self._parse_hw_df(self.hw_df)
            counts["hw"] = len(self.records["hw"])

        # 2. Software
        if sw_source is not None:
            self.sw_df = sw_source if isinstance(sw_source, pd.DataFrame) else pd.read_excel(sw_source)
            self.records["sw"] = self._parse_sw_df(self.sw_df)
            counts["sw"] = len(self.records["sw"])

        # 3. UPS & Monitor
        if ups_source is not None:
            self.ups_df = ups_source if isinstance(ups_source, pd.DataFrame) else pd.read_excel(ups_source)
            self.records["ups"] = self._parse_ups_df(self.ups_df)
            counts["ups"] = len(self.records["ups"])

        # Run initial comparison
        self.recompare()
        self.autosave()
        return counts

    def _parse_hw_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records = []
        for idx, row in df.iterrows():
            asset_id = clean_asset_id(row.get("เลขที่ทรัพย์สิน"))
            asset_type = clean_val(row.get("ประเภททรัพย์สิน")) or "PC"
            records.append({
                "uid": f"hw_{idx}",
                "category": "hw",
                "row_index": idx,
                "asset_id": asset_id,
                "it_record_id": clean_val(row.get("Record-ID")),
                "it_emp_id": clean_emp_id(row.get("รหัสพนักงาน")),
                "it_emp_name": clean_val(row.get("ผู้ใช้งาน/ดูแล")),
                "it_dept": clean_val(row.get("สถานที่เก็บ")),
                "it_asset_name": clean_val(row.get("ชื่อทรัพย์สิน")),
                "it_asset_type": asset_type,
                "it_sn": clean_val(row.get("S/N")),
                "it_pc_name": clean_val(row.get("PC_Name")),
                "it_monitor_asset": clean_val(row.get("รหัสทรัพย์สิน Monitor")),
                "it_ups_asset": clean_val(row.get("รหัสทรัพย์สิน UPS")),
                "it_check_status": clean_val(row.get("สถานะ(การตรวจสอบ)")),
                "it_remark": clean_val(row.get("AssetRemark")),
                # Will be populated by comparison
                "is_match": True,
                "mismatch_type": "",
                "diff_fields": [],
                "ax_data": {}
            })
        return records

    def _parse_sw_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records = []
        for idx, row in df.iterrows():
            asset_id = clean_asset_id(row.get("เลขที่ทรัพย์สิน"))
            records.append({
                "uid": f"sw_{idx}",
                "category": "sw",
                "row_index": idx,
                "asset_id": asset_id,
                "it_record_id": clean_val(row.get("IdAssetRecId")),
                "it_emp_id": clean_emp_id(row.get("รหัสพนักงาน")),
                "it_emp_name": clean_val(row.get("ผู้ดูแล")),
                "it_dept": clean_val(row.get("สถานที่เก็บ")),
                "it_asset_name": clean_val(row.get("ชื่อ Software")),
                "it_asset_type": "Software",
                "it_sn": clean_val(row.get("Key License")),
                "it_pc_name": clean_val(row.get("PCName")),
                "it_license_key": clean_val(row.get("Key License")),
                "it_software_code": clean_val(row.get("รหัส Software")),
                "it_check_fixasset": clean_val(row.get("Check FixAsset")),
                "is_match": True,
                "mismatch_type": "",
                "diff_fields": [],
                "ax_data": {}
            })
        return records

    def _parse_ups_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records = []
        for idx, row in df.iterrows():
            asset_id = clean_asset_id(row.get("เลขที่ทรัพย์สิน"))
            asset_type = clean_val(row.get("ประเภททรัพย์สิน")) or "UPS/Monitor"
            records.append({
                "uid": f"ups_{idx}",
                "category": "ups",
                "row_index": idx,
                "asset_id": asset_id,
                "it_record_id": clean_val(row.get("Record-ID")),
                "it_emp_id": clean_emp_id(row.get("รหัสพนักงาน")),
                "it_emp_name": clean_val(row.get("ผู้ใช้งาน/ดูแล")),
                "it_dept": clean_val(row.get("สถานที่เก็บ")),
                "it_asset_name": clean_val(row.get("ชื่อทรัพย์สิน")),
                "it_asset_type": asset_type,
                "it_sn": clean_val(row.get("S/N")),
                "it_pc_name": clean_val(row.get("PC_Name")),
                "it_check_status": clean_val(row.get("สถานะ(การตรวจสอบ)")),
                "it_remark": clean_val(row.get("AssetRemark")),
                "is_match": True,
                "mismatch_type": "",
                "diff_fields": [],
                "ax_data": {}
            })
        return records

    def compare_single_record(self, rec: Dict[str, Any]) -> None:
        """Compare a single inventory record with ERP master data."""
        asset_id = rec["asset_id"]
        diff_fields = []

        if not asset_id:
            rec["is_match"] = False
            rec["mismatch_type"] = "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)"
            rec["diff_fields"] = ["asset_id"]
            rec["ax_data"] = {}
            return

        ax_record = self.master_dict.get(asset_id)
        if not ax_record:
            rec["is_match"] = False
            rec["mismatch_type"] = "ไม่พบในระบบ ERP (มีเฉพาะใน IT)"
            rec["diff_fields"] = ["asset_id"]
            rec["ax_data"] = {}
            return

        rec["ax_data"] = copy.deepcopy(ax_record)

        # Check Scrapped status in AX
        if ax_record["is_scrapped"]:
            rec["is_match"] = False
            rec["mismatch_type"] = "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน"
            rec["diff_fields"] = ["status", "dept", "emp_id"]
            return

        # Check Employee ID
        emp_match = True
        it_emp = rec["it_emp_id"]
        ax_emp = ax_record["ax_emp_id"]
        if it_emp != ax_emp:
            # If both are empty, consider match
            if it_emp or ax_emp:
                emp_match = False
                diff_fields.append("emp_id")

        # Check Department
        dept_match = is_dept_match(rec["it_dept"], ax_record["ax_dept"], ax_record["ax_loc_code"])
        if not dept_match:
            diff_fields.append("dept")

        # Classify mismatch
        if not emp_match and not dept_match:
            rec["is_match"] = False
            rec["mismatch_type"] = "รหัสพนักงาน + แผนกไม่ตรง"
        elif not emp_match:
            rec["is_match"] = False
            rec["mismatch_type"] = "รหัสพนักงานไม่ตรง"
        elif not dept_match:
            rec["is_match"] = False
            rec["mismatch_type"] = "แผนกไม่ตรง"
        else:
            rec["is_match"] = True
            rec["mismatch_type"] = "ตรงกันสมบูรณ์"

        rec["diff_fields"] = diff_fields

    def recompare(self) -> Dict[str, Any]:
        """Re-run comparison across all records and recalculate statistics."""
        summary = {
            "overall": {
                "total_records": 0,
                "matched_records": 0,
                "mismatched_records": 0,
                "match_rate": 0.0,
            },
            "by_category": {},
            "mismatch_breakdown": {
                "รหัสพนักงาน + แผนกไม่ตรง": 0,
                "รหัสพนักงานไม่ตรง": 0,
                "แผนกไม่ตรง": 0,
                "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน": 0,
                "ไม่พบในระบบ ERP (มีเฉพาะใน IT)": 0,
                "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)": 0,
                "อื่นๆ": 0
            },
            "asset_type_breakdown": {}
        }

        total_all = 0
        matched_all = 0

        for cat_key, cat_name in [("hw", "Hardware"), ("sw", "Software"), ("ups", "UPS & Monitor")]:
            recs = self.records.get(cat_key, [])
            cat_total = len(recs)
            cat_matched = 0

            for r in recs:
                self.compare_single_record(r)
                if r["is_match"]:
                    cat_matched += 1
                else:
                    m_type = r["mismatch_type"]
                    if m_type in summary["mismatch_breakdown"]:
                        summary["mismatch_breakdown"][m_type] += 1
                    else:
                        summary["mismatch_breakdown"]["อื่นๆ"] += 1

                # Asset type breakdown for mismatches
                if not r["is_match"]:
                    atype = r.get("it_asset_type") or "Unknown"
                    summary["asset_type_breakdown"][atype] = summary["asset_type_breakdown"].get(atype, 0) + 1

            cat_mismatched = cat_total - cat_matched
            cat_rate = round((cat_matched / cat_total * 100), 1) if cat_total > 0 else 0.0

            summary["by_category"][cat_key] = {
                "name": cat_name,
                "total": cat_total,
                "matched": cat_matched,
                "mismatched": cat_mismatched,
                "match_rate": cat_rate
            }

            total_all += cat_total
            matched_all += cat_matched

        summary["overall"]["total_records"] = total_all
        summary["overall"]["matched_records"] = matched_all
        summary["overall"]["mismatched_records"] = total_all - matched_all
        summary["overall"]["match_rate"] = round((matched_all / total_all * 100), 1) if total_all > 0 else 0.0

        self.summary = summary
        return summary

    def update_record(self, uid: str, updated_fields: Dict[str, Any], user: str = "IT Staff") -> Optional[Dict[str, Any]]:
        """Update fields of a record, log changelog, and recompare."""
        cat = uid.split("_")[0]
        if cat not in self.records:
            return None

        target_rec = None
        for r in self.records[cat]:
            if r["uid"] == uid:
                target_rec = r
                break

        if not target_rec:
            return None

        changes = {}
        for k, new_v in updated_fields.items():
            if k in target_rec:
                old_v = target_rec[k]
                if str(old_v) != str(new_v):
                    target_rec[k] = new_v
                    changes[k] = {"old": old_v, "new": new_v}

        if changes:
            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            self.changelog.append({
                "uid": uid,
                "asset_id": target_rec["asset_id"],
                "category": cat,
                "user": user,
                "timestamp": timestamp,
                "changes": changes
            })
            self.push_undo_action({
                "id": str(uuid.uuid4())[:8],
                "type": "single_edit",
                "description": f"แก้ไขข้อมูล {target_rec.get('asset_id')}",
                "timestamp": timestamp,
                "uid": uid,
                "changes": changes,
                "user": user
            })
            # Recompare single record and recalculate summary
            self.recompare()
            self.autosave()

        return target_rec

    def batch_quick_fix(self, category: str = "all", user: str = "IT Staff") -> Dict[str, Any]:
        """
        Automatically align IT records with ERP (AX) for all records where:
        - Asset ID exists in ERP
        - Record is currently a mismatch
        - ERP has valid employee and/or department data
        Returns summary of updated records.
        """
        categories = [category] if category and category != "all" else ["hw", "sw", "ups"]
        updated_count = 0
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_items = []

        for cat in categories:
            for r in self.records.get(cat, []):
                if r.get("is_match"):
                    continue

                ax = r.get("ax_data")
                if not ax or not ax.get("asset_id"):
                    continue

                changes = {}
                # Update Employee ID & Name if available in ERP
                ax_emp_id = ax.get("ax_emp_id")
                ax_emp_name = ax.get("ax_emp_name")
                if ax_emp_id and str(r.get("it_emp_id", "")).strip() != str(ax_emp_id).strip():
                    changes["it_emp_id"] = {"old": r.get("it_emp_id"), "new": ax_emp_id}
                    r["it_emp_id"] = ax_emp_id

                if ax_emp_name and str(r.get("it_emp_name", "")).strip() != str(ax_emp_name).strip():
                    changes["it_emp_name"] = {"old": r.get("it_emp_name"), "new": ax_emp_name}
                    r["it_emp_name"] = ax_emp_name

                # Update Department if available in ERP
                ax_dept = ax.get("ax_dept")
                if ax_dept and str(r.get("it_dept", "")).strip() != str(ax_dept).strip():
                    changes["it_dept"] = {"old": r.get("it_dept"), "new": ax_dept}
                    r["it_dept"] = ax_dept

                if changes:
                    updated_count += 1
                    batch_items.append({
                        "uid": r.get("uid"),
                        "asset_id": r.get("asset_id"),
                        "category": cat,
                        "changes": changes
                    })
                    self.changelog.append({
                        "uid": r.get("uid"),
                        "asset_id": r.get("asset_id"),
                        "category": cat,
                        "user": user,
                        "timestamp": timestamp,
                        "changes": changes,
                        "type": "batch_auto_fix"
                    })

        if updated_count > 0:
            self.push_undo_action({
                "id": str(uuid.uuid4())[:8],
                "type": "batch_quick_fix",
                "description": f"อัปเดตตรง ERP ทั้งหมด ({updated_count} รายการ)",
                "timestamp": timestamp,
                "items": batch_items,
                "user": user
            })
            self.recompare()
            self.autosave()

        return {
            "success": True,
            "updated_count": updated_count,
            "new_match_rate": self.summary.get("overall", {}).get("match_rate", 0) if self.summary else 0,
            "overall": self.summary.get("overall", {}) if self.summary else {}
        }


    def get_records(self, category: Optional[str] = None, mismatch_only: bool = True, search: str = "", limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """Fetch records with filtering and pagination."""
        all_recs = []
        categories = [category] if category and category != "all" else ["hw", "sw", "ups"]

        for c in categories:
            all_recs.extend(self.records.get(c, []))

        # Filter mismatch_only
        if mismatch_only:
            filtered = [r for r in all_recs if not r["is_match"]]
        else:
            filtered = all_recs

        # Search filter
        if search:
            q = search.lower().strip()
            def matches_query(r):
                fields = [
                    r.get("asset_id", ""),
                    r.get("it_record_id", ""),
                    r.get("it_emp_id", ""),
                    r.get("it_emp_name", ""),
                    r.get("it_dept", ""),
                    r.get("it_asset_name", ""),
                    r.get("mismatch_type", ""),
                    r.get("ax_data", {}).get("ax_emp_name", ""),
                    r.get("ax_data", {}).get("ax_emp_id", ""),
                    r.get("ax_data", {}).get("ax_dept", "")
                ]
                return any(q in str(f).lower() for f in fields)
            filtered = [r for r in filtered if matches_query(r)]

        total_count = len(filtered)
        paginated = filtered[offset: offset + limit]
        return paginated, total_count

    # =========================================================================
    # Google Workspace-Style Undo, Redo, Version History & AutoSave
    # =========================================================================
    def push_undo_action(self, action: Dict[str, Any]):
        """Push an action to undo stack, cap at 50, and clear redo stack."""
        self.undo_stack.append(action)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.autosave()

    def undo(self) -> Dict[str, Any]:
        """Rollback the last action like Google Workspace Ctrl+Z."""
        if not self.undo_stack:
            return {
                "success": False,
                "message": "ไม่มีประวัติการกระทำที่จะเลิกทำ (Undo stack is empty)",
                "can_undo": False,
                "can_redo": len(self.redo_stack) > 0
            }

        action = self.undo_stack.pop()
        action_type = action.get("type")

        if action_type in ("single_edit", "quick_fix"):
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    for field, change in action.get("changes", {}).items():
                        r[field] = change.get("old")
                    break
        elif action_type == "batch_quick_fix":
            for item in action.get("items", []):
                uid = item.get("uid")
                cat = uid.split("_")[0]
                for r in self.records.get(cat, []):
                    if r["uid"] == uid:
                        for field, change in item.get("changes", {}).items():
                            r[field] = change.get("old")
                        break

        # Push to redo stack
        self.redo_stack.append(action)
        self.recompare()
        self.autosave()

        return {
            "success": True,
            "message": f"เลิกทำสำเร็จ: {action.get('description', '')}",
            "action": action,
            "can_undo": len(self.undo_stack) > 0,
            "can_redo": True,
            "summary": self.summary
        }

    def redo(self) -> Dict[str, Any]:
        """Re-apply the undone action (Ctrl+Y)."""
        if not self.redo_stack:
            return {
                "success": False,
                "message": "ไม่มีประวัติที่จะทำซ้ำ (Redo stack is empty)",
                "can_undo": len(self.undo_stack) > 0,
                "can_redo": False
            }

        action = self.redo_stack.pop()
        action_type = action.get("type")

        if action_type in ("single_edit", "quick_fix"):
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    for field, change in action.get("changes", {}).items():
                        r[field] = change.get("new")
                    break
        elif action_type == "batch_quick_fix":
            for item in action.get("items", []):
                uid = item.get("uid")
                cat = uid.split("_")[0]
                for r in self.records.get(cat, []):
                    if r["uid"] == uid:
                        for field, change in item.get("changes", {}).items():
                            r[field] = change.get("new")
                        break

        self.undo_stack.append(action)
        self.recompare()
        self.autosave()

        return {
            "success": True,
            "message": f"ทำซ้ำสำเร็จ: {action.get('description', '')}",
            "action": action,
            "can_undo": True,
            "can_redo": len(self.redo_stack) > 0,
            "summary": self.summary
        }

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Return history timeline for Version History UI."""
        history = []
        for idx, act in enumerate(self.undo_stack):
            history.append({
                "index": idx,
                "id": act.get("id"),
                "type": act.get("type"),
                "description": act.get("description"),
                "timestamp": act.get("timestamp"),
                "user": act.get("user", "IT Officer"),
                "count": len(act.get("items", [])) if act.get("type") == "batch_quick_fix" else 1
            })
        return list(reversed(history))

    def rollback_to_index(self, target_index: int) -> Dict[str, Any]:
        """Rollback back to a specific revision index."""
        if target_index < 0 or target_index >= len(self.undo_stack):
            return {"success": False, "message": "ไม่พบเวอร์ชันที่ระบุ"}

        steps_to_undo = len(self.undo_stack) - 1 - target_index
        for _ in range(steps_to_undo):
            self.undo()

        return {
            "success": True,
            "message": f"ย้อนกลับสถานะสำเร็จ ({steps_to_undo} ขั้นตอน)",
            "can_undo": len(self.undo_stack) > 0,
            "can_redo": len(self.redo_stack) > 0,
            "summary": self.summary
        }

    def autosave(self, path: Optional[str] = None):
        """Persist current session state to disk atomically."""
        if path:
            self.autosave_path = path
        if not self.autosave_path:
            return
        try:
            filenames = {
                "master": getattr(self, "master_filename", None),
                "hw": getattr(self, "hw_filename", None),
                "sw": getattr(self, "sw_filename", None),
                "ups": getattr(self, "ups_filename", None)
            }
            data = {
                "records": self.records,
                "master_dict": self.master_dict,
                "summary": self.summary,
                "changelog": self.changelog[-200:],
                "undo_stack": self.undo_stack,
                "redo_stack": self.redo_stack,
                "filenames": filenames,
                "saved_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            dirname = os.path.dirname(os.path.abspath(self.autosave_path))
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            tmp_path = self.autosave_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.autosave_path)
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Autosave failed: {e}", component="AUTOSAVE", exc_info=True)
            except Exception:
                pass

    def load_autosave(self, path: str) -> bool:
        """Restore session from autosave file if exists."""
        self.autosave_path = path
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.records = data.get("records", {"hw": [], "sw": [], "ups": []})
            self.master_dict = data.get("master_dict", {})
            self.summary = data.get("summary", {})
            self.changelog = data.get("changelog", [])
            self.undo_stack = data.get("undo_stack", [])
            self.redo_stack = data.get("redo_stack", [])

            filenames = data.get("filenames", {})
            if filenames.get("master"): self.master_filename = filenames["master"]
            if filenames.get("hw"): self.hw_filename = filenames["hw"]
            if filenames.get("sw"): self.sw_filename = filenames["sw"]
            if filenames.get("ups"): self.ups_filename = filenames["ups"]

            # Load DataFrames from sources_dir if present
            if self.sources_dir and os.path.exists(self.sources_dir):
                for cat, attr in [("master", "master_df"), ("hw", "hw_df"), ("sw", "sw_df"), ("ups", "ups_df")]:
                    src_file = os.path.join(self.sources_dir, f"source_{cat}.xlsx")
                    if os.path.exists(src_file) and getattr(self, attr) is None:
                        try:
                            setattr(self, attr, pd.read_excel(src_file))
                        except Exception:
                            pass

            return bool(self.master_dict or any(len(v) > 0 for v in self.records.values()))
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Failed to load autosave from {path}: {e}", component="AUTOSAVE", exc_info=True)
            except Exception:
                pass
            return False

    def reset_session(self) -> bool:
        """Clear all in-memory data, wipe autosave file, and clean sources directory."""
        self.master_df = None
        self.master_dict = {}
        self.hw_df = None
        self.sw_df = None
        self.ups_df = None
        self.records = {"hw": [], "sw": [], "ups": []}
        self.summary = {}
        self.changelog = []
        self.undo_stack = []
        self.redo_stack = []
        self.master_filename = None
        self.hw_filename = None
        self.sw_filename = None
        self.ups_filename = None

        if self.autosave_path:
            for p in (self.autosave_path, self.autosave_path + ".tmp"):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

        if self.sources_dir and os.path.exists(self.sources_dir):
            for fname in os.listdir(self.sources_dir):
                fpath = os.path.join(self.sources_dir, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                except Exception:
                    pass
        return True

