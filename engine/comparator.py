import re
import os
import json
import sqlite3
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

COLUMN_MAP = {
    "hw": {
        "asset_id": "เลขที่ทรัพย์สิน",
        "emp_id": "รหัสพนักงาน",
        "emp_name": "ผู้ใช้งาน/ดูแล",
        "dept": "สถานที่เก็บ",
        "sn": "S/N"
    },
    "sw": {
        "asset_id": "เลขที่ทรัพย์สิน",
        "emp_id": "รหัสพนักงาน",
        "emp_name": "ผู้ดูแล",
        "dept": "สถานที่เก็บ",
        "sn": "Key License"
    },
    "ups": {
        "asset_id": "เลขที่ทรัพย์สิน",
        "emp_id": "รหัสพนักงาน",
        "emp_name": "ผู้ใช้งาน/ดูแล",
        "dept": "สถานที่เก็บ",
        "sn": "S/N"
    }
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
    4. Code prefix mapping
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
        base_prefix = prefix.split('.')[0] if '.' in prefix else prefix
        rule = DEPT_CODE_MAP.get(prefix) or DEPT_CODE_MAP.get(base_prefix)
        if rule:
            if ax_code and ax_code in rule["codes"]:
                return True
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
    """Enhanced Multi-Category Comparison Engine with Per-Category Lifecycle & Spreadsheet Cell Editing."""

    def __init__(self):
        self.master_df: Optional[pd.DataFrame] = None
        self.master_dict: Dict[str, Dict[str, Any]] = {}

        # Raw DataFrames & Columns per category
        self.hw_df: Optional[pd.DataFrame] = None
        self.sw_df: Optional[pd.DataFrame] = None
        self.ups_df: Optional[pd.DataFrame] = None
        
        self.columns: Dict[str, List[str]] = {
            "hw": [],
            "sw": [],
            "ups": []
        }

        # Category status: 'empty' | 'loaded' | 'stale' | 'compared'
        self.category_states: Dict[str, str] = {
            "hw": "empty",
            "sw": "empty",
            "ups": "empty"
        }

        # Working editable records: Dict of category -> List of dicts
        self.records: Dict[str, List[Dict[str, Any]]] = {
            "hw": [],
            "sw": [],
            "ups": []
        }

        # Summary results cached per category and overall
        self.summary: Dict[str, Any] = {}
        self.changelog: List[Dict[str, Any]] = []

        # Undo/Redo & Rollback stacks
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.autosave_path: Optional[str] = None
        self.sources_dir: Optional[str] = None
        self.db_path: Optional[str] = None

        # Filename tracking
        self.master_filename: Optional[str] = None
        self.hw_filename: Optional[str] = None
        self.sw_filename: Optional[str] = None
        self.ups_filename: Optional[str] = None

    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Obtain connection to local SQLite database, creating schema if needed."""
        target_path = self.db_path
        if not target_path and self.autosave_path:
            dir_name = os.path.dirname(os.path.abspath(self.autosave_path))
            target_path = os.path.join(dir_name, ".fti_inventory_database.db")
            self.db_path = target_path

        if not target_path:
            return None

        try:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            conn = sqlite3.connect(target_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS erp_master_assets (
                        asset_id TEXT PRIMARY KEY,
                        ax_emp_id TEXT,
                        ax_emp_name TEXT,
                        ax_dept TEXT,
                        ax_loc_code TEXT,
                        ax_asset_name TEXT,
                        ax_sn TEXT,
                        ax_status TEXT,
                        ax_search_name TEXT,
                        ax_group TEXT,
                        is_scrapped INTEGER,
                        updated_at TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS inventory_db_records (
                        uid TEXT PRIMARY KEY,
                        category TEXT,
                        row_index INTEGER,
                        asset_id TEXT,
                        it_emp_id TEXT,
                        it_emp_name TEXT,
                        it_dept TEXT,
                        it_sn TEXT,
                        is_match INTEGER,
                        is_excluded INTEGER,
                        exclude_reason TEXT,
                        mismatch_type TEXT,
                        user_edited_cols TEXT,
                        cells_json TEXT,
                        ax_data_json TEXT,
                        updated_at TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_time TEXT,
                        category TEXT,
                        total_records INTEGER,
                        matched_records INTEGER,
                        mismatched_records INTEGER,
                        excluded_records INTEGER,
                        match_rate REAL,
                        summary_json TEXT
                    )
                """)
            return conn
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Failed to open SQLite database: {e}", component="SQLITE")
            except Exception:
                pass
            return None

    def sync_to_sqlite(self, category: Optional[str] = None):
        """Sync working memory state (ERP master & category records) into SQLite tables."""
        conn = self._get_db_connection()
        if not conn:
            return

        now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with conn:
                # Sync Master Assets if loaded
                if self.master_dict:
                    master_rows = []
                    for aid, m in self.master_dict.items():
                        master_rows.append((
                            aid,
                            m.get("ax_emp_id", ""),
                            m.get("ax_emp_name", ""),
                            m.get("ax_dept", ""),
                            m.get("ax_loc_code", ""),
                            m.get("ax_asset_name", ""),
                            m.get("ax_sn", ""),
                            m.get("ax_status", ""),
                            m.get("ax_search_name", ""),
                            m.get("ax_group", ""),
                            1 if m.get("is_scrapped") else 0,
                            now_str
                        ))
                    conn.executemany("""
                        INSERT OR REPLACE INTO erp_master_assets (
                            asset_id, ax_emp_id, ax_emp_name, ax_dept, ax_loc_code,
                            ax_asset_name, ax_sn, ax_status, ax_search_name, ax_group,
                            is_scrapped, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, master_rows)

                # Sync Category Records
                cats = [category] if category else ["hw", "sw", "ups"]
                for cat in cats:
                    recs = self.records.get(cat, [])
                    if not recs:
                        continue
                    db_rows = []
                    for r in recs:
                        cells = r.get("cells", {})
                        aid, it_emp, it_name, it_dept, it_sn = self._get_key_fields(cat, cells)
                        db_rows.append((
                            r.get("uid"),
                            cat,
                            r.get("row_index", 0),
                            aid,
                            it_emp,
                            it_name,
                            it_dept,
                            it_sn,
                            1 if r.get("is_match") is True else (0 if r.get("is_match") is False else None),
                            1 if r.get("is_excluded") else 0,
                            r.get("exclude_reason", ""),
                            r.get("mismatch_type", ""),
                            json.dumps(r.get("user_edited_cols", []), ensure_ascii=False),
                            json.dumps(cells, ensure_ascii=False),
                            json.dumps(r.get("ax_data", {}), ensure_ascii=False),
                            now_str
                        ))
                    conn.executemany("""
                        INSERT OR REPLACE INTO inventory_db_records (
                            uid, category, row_index, asset_id, it_emp_id, it_emp_name,
                            it_dept, it_sn, is_match, is_excluded, exclude_reason,
                            mismatch_type, user_edited_cols, cells_json, ax_data_json, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, db_rows)

                    # Record snapshot into scan_history_snapshots
                    cat_sum = self.summary.get("by_category", {}).get(cat, {})
                    if cat_sum:
                        conn.execute("""
                            INSERT INTO scan_history_snapshots (
                                snapshot_time, category, total_records, matched_records,
                                mismatched_records, excluded_records, match_rate, summary_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            now_str,
                            cat,
                            cat_sum.get("total_records", len(recs)),
                            cat_sum.get("matched", 0),
                            cat_sum.get("mismatched", 0),
                            cat_sum.get("excluded", 0),
                            float(cat_sum.get("match_rate", 0.0)),
                            json.dumps(cat_sum, ensure_ascii=False)
                        ))
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Sync to SQLite failed: {e}", component="SQLITE", exc_info=True)
            except Exception:
                pass
        finally:
            conn.close()

    def get_db_records(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve stored records from SQLite database for the category."""
        conn = self._get_db_connection()
        if not conn:
            return []
        try:
            cur = conn.execute("""
                SELECT * FROM inventory_db_records
                WHERE category = ?
                ORDER BY row_index ASC
            """, (category,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                try:
                    cells = json.loads(row["cells_json"]) if row["cells_json"] else {}
                except Exception:
                    cells = {}
                try:
                    ax_data = json.loads(row["ax_data_json"]) if row["ax_data_json"] else {}
                except Exception:
                    ax_data = {}
                try:
                    user_edited = json.loads(row["user_edited_cols"]) if row["user_edited_cols"] else []
                except Exception:
                    user_edited = []

                is_match_val = None
                if row["is_match"] is not None:
                    is_match_val = bool(row["is_match"])

                results.append({
                    "uid": row["uid"],
                    "category": row["category"],
                    "row_index": row["row_index"],
                    "cells": cells,
                    "orig_cells": copy.deepcopy(cells),
                    "user_edited_cols": user_edited,
                    "manual_exclude": None,
                    "is_excluded": bool(row["is_excluded"]),
                    "exclude_reason": row["exclude_reason"] or "",
                    "is_match": is_match_val,
                    "mismatch_type": row["mismatch_type"] or "",
                    "diff_fields": [],
                    "ax_data": ax_data,
                    "asset_id": row["asset_id"] or "",
                    "it_emp_id": row["it_emp_id"] or "",
                    "it_emp_name": row["it_emp_name"] or "",
                    "it_dept": row["it_dept"] or "",
                    "it_sn": row["it_sn"] or "",
                    "db_updated_at": row["updated_at"]
                })
            return results
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Failed to fetch DB records: {e}", component="SQLITE")
            except Exception:
                pass
            return []
        finally:
            conn.close()

    def get_erp_master_records(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """Retrieve ERP Master Asset records from SQLite database."""
        conn = self._get_db_connection()
        if not conn:
            # Fallback to in-memory master_dict
            res = []
            for idx, (aid, m) in enumerate(list(self.master_dict.items())[:limit]):
                res.append({
                    "uid": f"erp_{aid}",
                    "category": "erp",
                    "row_index": idx,
                    "asset_id": aid,
                    "it_emp_id": m.get("ax_emp_id", ""),
                    "it_emp_name": m.get("ax_emp_name", ""),
                    "it_dept": m.get("ax_dept", ""),
                    "it_sn": m.get("ax_sn", ""),
                    "is_match": True if not m.get("is_scrapped") else False,
                    "is_excluded": bool(m.get("is_scrapped")),
                    "exclude_reason": "ตัดจำหน่ายใน ERP" if m.get("is_scrapped") else "",
                    "mismatch_type": "ตัดจำหน่ายใน ERP" if m.get("is_scrapped") else "ข้อมูล ERP Master",
                    "user_edited_cols": [],
                    "diff_fields": [],
                    "ax_data": copy.deepcopy(m),
                    "cells": {
                        "เลขที่ทรัพย์สิน": aid,
                        "ชื่อทรัพย์สิน": m.get("ax_asset_name", ""),
                        "รหัสพนักงาน": m.get("ax_emp_id", ""),
                        "ชื่อผู้รับผิดชอบ": m.get("ax_emp_name", ""),
                        "แผนก/สถานที่": m.get("ax_dept", ""),
                        "Location": m.get("ax_loc_code", ""),
                        "Serial Number": m.get("ax_sn", ""),
                        "สถานะ": m.get("ax_status", ""),
                        "กลุ่มทรัพย์สิน": m.get("ax_group", "")
                    }
                })
            return res

        try:
            cur = conn.execute("""
                SELECT * FROM erp_master_assets
                ORDER BY asset_id ASC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            results = []
            for idx, r in enumerate(rows):
                aid = r["asset_id"]
                is_scrapped = bool(r["is_scrapped"])
                ax_dict = {
                    "asset_id": aid,
                    "ax_emp_id": r["ax_emp_id"] or "",
                    "ax_emp_name": r["ax_emp_name"] or "",
                    "ax_dept": r["ax_dept"] or "",
                    "ax_loc_code": r["ax_loc_code"] or "",
                    "ax_asset_name": r["ax_asset_name"] or "",
                    "ax_sn": r["ax_sn"] or "",
                    "ax_status": r["ax_status"] or "",
                    "ax_search_name": r["ax_search_name"] or "",
                    "ax_group": r["ax_group"] or "",
                    "is_scrapped": is_scrapped
                }
                results.append({
                    "uid": f"erp_{aid}",
                    "category": "erp",
                    "row_index": idx,
                    "asset_id": aid,
                    "it_emp_id": r["ax_emp_id"] or "",
                    "it_emp_name": r["ax_emp_name"] or "",
                    "it_dept": r["ax_dept"] or "",
                    "it_sn": r["ax_sn"] or "",
                    "is_match": True if not is_scrapped else False,
                    "is_excluded": is_scrapped,
                    "exclude_reason": "ตัดจำหน่ายใน ERP" if is_scrapped else "",
                    "mismatch_type": "ตัดจำหน่ายใน ERP" if is_scrapped else "ปกติ (ERP Master)",
                    "user_edited_cols": [],
                    "diff_fields": [],
                    "ax_data": ax_dict,
                    "cells": {
                        "เลขที่ทรัพย์สิน": aid,
                        "ชื่อทรัพย์สิน": r["ax_asset_name"] or "",
                        "รหัสพนักงาน": r["ax_emp_id"] or "",
                        "ชื่อผู้รับผิดชอบ": r["ax_emp_name"] or "",
                        "แผนก/สถานที่": r["ax_dept"] or "",
                        "Location": r["ax_loc_code"] or "",
                        "Serial Number": r["ax_sn"] or "",
                        "สถานะ": r["ax_status"] or "",
                        "กลุ่มทรัพย์สิน": r["ax_group"] or ""
                    }
                })
            return results
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Failed to fetch ERP master assets from DB: {e}", component="SQLITE")
            except Exception:
                pass
            return []
        finally:
            conn.close()

    def get_chart_analytics(self) -> Dict[str, Any]:
        """Compute aggregated multi-chart analytics across categories and SQLite DB."""
        cats = ["hw", "sw", "ups"]
        cat_names = {"hw": "Hardware", "sw": "Software", "ups": "UPS & Monitor"}

        # 1. Status breakdown overall
        ov = self.summary.get("overall", {})
        matched_count = ov.get("matched_records", 0)
        mismatched_count = ov.get("mismatched_records", 0)
        excluded_count = ov.get("excluded_records", 0)
        total_active = ov.get("total_records", 0)
        total_initial = ov.get("total_initial_records", total_active + excluded_count)
        overall_match_rate = ov.get("match_rate", 0.0)

        user_edited_count = 0
        for c in cats:
            for r in self.records.get(c, []):
                if len(r.get("user_edited_cols", [])) > 0:
                    user_edited_count += 1

        donut_data = [
            {"label": "ตรงกันสมบูรณ์", "value": matched_count, "color": "#10b981", "key": "match"},
            {"label": "พบจุดต่าง (Mismatch)", "value": mismatched_count, "color": "#ef4444", "key": "mismatch"},
            {"label": "ตัดออก (Scrapped)", "value": excluded_count, "color": "#f59e0b", "key": "excluded"},
            {"label": "แก้ไขเอง", "value": user_edited_count, "color": "#06b6d4", "key": "user_edited"}
        ]

        # 2. Grouped Bar comparison per category
        grouped_bar_data = []
        for c in cats:
            csum = self.summary.get("by_category", {}).get(c, {})
            grouped_bar_data.append({
                "category": c,
                "category_name": cat_names.get(c, c.upper()),
                "matched": csum.get("matched", 0),
                "mismatched": csum.get("mismatched", 0),
                "excluded": csum.get("excluded", 0),
                "total": csum.get("total_records", 0),
                "match_rate": csum.get("match_rate", 0.0)
            })

        # 3. Stacked 100% Progress per category
        stacked_progress = []
        for c in cats:
            csum = self.summary.get("by_category", {}).get(c, {})
            tot = csum.get("total_initial_records", 0) or csum.get("total_records", 1) or 1
            m = csum.get("matched", 0)
            diff = csum.get("mismatched", 0)
            ex = csum.get("excluded", 0)
            stacked_progress.append({
                "category": c,
                "category_name": cat_names.get(c, c.upper()),
                "rate": csum.get("match_rate", 0.0),
                "matched_pct": round((m / tot) * 100, 1),
                "mismatch_pct": round((diff / tot) * 100, 1),
                "excluded_pct": round((ex / tot) * 100, 1)
            })

        # 4. Root cause mismatch breakdown
        reasons_counter = {}
        dept_counter = {}
        for c in cats:
            for r in self.records.get(c, []):
                if r.get("is_match") is False or r.get("is_excluded") is True:
                    mtype = r.get("mismatch_type") or r.get("exclude_reason") or "ไม่ระบุสาเหตุ"
                    reasons_counter[mtype] = reasons_counter.get(mtype, 0) + 1

                    dept = r.get("it_dept") or r.get("cells", {}).get("สถานที่เก็บ") or r.get("cells", {}).get("แผนก") or "ไม่ระบุแผนก"
                    dept_counter[dept] = dept_counter.get(dept, 0) + 1

        top_reasons = sorted([{"reason": k, "count": v} for k, v in reasons_counter.items()], key=lambda x: x["count"], reverse=True)[:6]
        top_depts = sorted([{"department": k, "count": v} for k, v in dept_counter.items()], key=lambda x: x["count"], reverse=True)[:6]

        # SQLite DB Stats
        db_stats = {"total_db_records": 0, "total_master_assets": len(self.master_dict), "db_exists": False}
        conn = self._get_db_connection()
        if conn:
            try:
                db_stats["db_exists"] = True
                c1 = conn.execute("SELECT COUNT(*) FROM inventory_db_records").fetchone()
                db_stats["total_db_records"] = c1[0] if c1 else 0
                c2 = conn.execute("SELECT COUNT(*) FROM erp_master_assets").fetchone()
                db_stats["total_master_assets"] = c2[0] if c2 else len(self.master_dict)
            except Exception:
                pass
            finally:
                conn.close()

        return {
            "summary": {
                "total_records": total_active,
                "total_initial_records": total_initial,
                "matched_records": matched_count,
                "mismatched_records": mismatched_count,
                "excluded_records": excluded_count,
                "user_edited_records": user_edited_count,
                "match_rate": overall_match_rate
            },
            "donut_chart": donut_data,
            "grouped_bar_chart": grouped_bar_data,
            "stacked_progress_chart": stacked_progress,
            "mismatch_breakdown": {
                "top_reasons": top_reasons,
                "top_departments": top_depts
            },
            "db_stats": db_stats
        }

    def load_master(self, filepath_or_df) -> int:
        """Load and index the master ERP file. Marks all loaded categories as 'stale'."""
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

        # When Master changes, any category already loaded or compared becomes stale
        for cat in ["hw", "sw", "ups"]:
            if self.category_states.get(cat) in ("loaded", "compared", "stale"):
                self.category_states[cat] = "stale"
                # Clear previous comparison results since master changed
                for r in self.records.get(cat, []):
                    r["is_match"] = None
                    r["mismatch_type"] = "รอเปรียบเทียบใหม่ (Master เปลี่ยน)"
                    r["diff_fields"] = []
                    r["ax_data"] = {}

        self.recompute_overall_summary()
        self.autosave()
        return len(self.master_dict)

    def load_category(self, category: str, filepath_or_df, filename: Optional[str] = None) -> int:
        """Load category Excel file without auto-comparing. Sets state to 'loaded'."""
        if category not in ("hw", "sw", "ups"):
            raise ValueError(f"Unknown category: {category}")

        if isinstance(filepath_or_df, pd.DataFrame):
            df = filepath_or_df.copy()
        else:
            df = pd.read_excel(filepath_or_df)

        setattr(self, f"{category}_df", df)
        if filename:
            setattr(self, f"{category}_filename", filename)

        self.columns[category] = list(df.columns)
        records = []

        for idx, row in df.iterrows():
            cells = {col: clean_val(row[col]) for col in df.columns}
            aid, emp_id, emp_name, dept, sn = self._get_key_fields(category, cells)
            records.append({
                "uid": f"{category}_{idx}",
                "category": category,
                "row_index": idx,
                "asset_id": aid,
                "it_emp_id": emp_id,
                "it_emp_name": emp_name,
                "it_dept": dept,
                "it_sn": sn,
                "cells": cells,
                "orig_cells": copy.deepcopy(cells),
                "user_edited_cols": [],
                "manual_exclude": None, # None = auto, True = user excluded, False = user included
                "is_excluded": False,
                "exclude_reason": "",
                "is_match": None,
                "mismatch_type": "ยังไม่ได้เปรียบเทียบ",
                "diff_fields": [],
                "ax_data": {}
            })

        self.records[category] = records
        self.category_states[category] = "loaded"
        self.recompute_overall_summary()
        self.autosave()
        return len(records)

    def load_inventory_files(self, hw_source, sw_source, ups_source) -> Dict[str, int]:
        """Load multiple files (compat helper). Does NOT auto-compare."""
        counts = {}
        if hw_source is not None:
            counts["hw"] = self.load_category("hw", hw_source)
        if sw_source is not None:
            counts["sw"] = self.load_category("sw", sw_source)
        if ups_source is not None:
            counts["ups"] = self.load_category("ups", ups_source)
        return counts

    def _get_key_fields(self, category: str, cells: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
        """Extract (asset_id, emp_id, emp_name, dept, sn) from cells using COLUMN_MAP and robust fallbacks."""
        cmap = COLUMN_MAP.get(category, {})

        # 1. Asset ID
        aid = clean_asset_id(cells.get(cmap.get("asset_id", ""), ""))
        if not aid:
            for alias in ["เลขที่ทรัพย์สิน", "รหัสทรัพย์สิน", "Fixed asset number", "Asset ID", "Asset_ID", "Asset Number", "Asset_Number", "AssetNo", "Asset_No", "เลขทรัพย์สิน"]:
                if alias in cells and clean_asset_id(cells[alias]):
                    aid = clean_asset_id(cells[alias])
                    break
        if not aid:
            for k, v in cells.items():
                k_clean = str(k).strip().lower()
                if k_clean in ("เลขที่ทรัพย์สิน", "รหัสทรัพย์สิน", "fixed asset number", "asset id", "asset_id", "asset number", "asset_number", "assetno"):
                    val = clean_asset_id(v)
                    if val:
                        aid = val
                        break

        # 2. Employee ID
        emp_id = clean_emp_id(cells.get(cmap.get("emp_id", ""), ""))
        if not emp_id:
            for alias in ["รหัสพนักงาน", "Responsible", "Employee ID", "Employee_ID", "Emp ID", "Emp_ID", "EmployeeID"]:
                if alias in cells and clean_emp_id(cells[alias]):
                    emp_id = clean_emp_id(cells[alias])
                    break
        if not emp_id:
            for k, v in cells.items():
                k_clean = str(k).strip().lower()
                if k_clean in ("รหัสพนักงาน", "responsible", "employee id", "employee_id", "emp id", "emp_id", "employeeid"):
                    val = clean_emp_id(v)
                    if val:
                        emp_id = val
                        break

        # 3. Employee Name
        emp_name = clean_val(cells.get(cmap.get("emp_name", ""), ""))
        if not emp_name:
            for alias in ["ผู้ใช้งาน/ดูแล", "ผู้ดูแล", "WorkName", "ชื่อผู้รับผิดชอบ", "ชื่อพนักงาน", "Employee Name", "User Name", "ผู้ใช้งาน"]:
                if alias in cells and clean_val(cells[alias]):
                    emp_name = clean_val(cells[alias])
                    break
        if not emp_name:
            for k, v in cells.items():
                k_clean = str(k).strip().lower()
                if k_clean in ("ผู้ใช้งาน/ดูแล", "ผู้ดูแล", "workname", "ชื่อผู้รับผิดชอบ", "ชื่อพนักงาน", "employee name", "user name", "ผู้ใช้งาน"):
                    val = clean_val(v)
                    if val:
                        emp_name = val
                        break

        # 4. Department / Location
        dept = clean_val(cells.get(cmap.get("dept", ""), ""))
        if not dept:
            for alias in ["สถานที่เก็บ", "Name2", "แผนก", "ฝ่าย", "Department", "Location", "แผนก/สถานที่", "ฝ่ายงานตามผังบัญชี"]:
                if alias in cells and clean_val(cells[alias]):
                    dept = clean_val(cells[alias])
                    break
        if not dept:
            for k, v in cells.items():
                k_clean = str(k).strip().lower()
                if k_clean in ("สถานที่เก็บ", "name2", "แผนก", "ฝ่าย", "department", "location", "แผนก/สถานที่", "ฝ่ายงานตามผังบัญชี"):
                    val = clean_val(v)
                    if val:
                        dept = val
                        break

        # 5. Serial Number / Key License
        sn = clean_val(cells.get(cmap.get("sn", ""), ""))
        if not sn:
            for alias in ["S/N", "Serial number", "Serial Number", "Serial", "Key License", "License Key", "Key_License"]:
                if alias in cells and clean_val(cells[alias]):
                    sn = clean_val(cells[alias])
                    break
        if not sn:
            for k, v in cells.items():
                k_clean = str(k).strip().lower()
                if k_clean in ("s/n", "serial number", "serial", "key license", "license key", "key_license"):
                    val = clean_val(v)
                    if val:
                        sn = val
                        break

        return aid, emp_id, emp_name, dept, sn

    def _evaluate_values_against_erp(self, asset_id: str, it_emp_id: str, it_dept: str) -> Tuple[bool, str, List[str], Dict[str, Any]]:
        """Evaluate specific IT values against ERP master_dict and return (is_match, mismatch_type, diff_fields, ax_data)."""
        diff_fields = []
        if not asset_id:
            return False, "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)", ["asset_id"], {}

        ax_record = self.master_dict.get(asset_id)
        if not ax_record:
            return False, "ไม่พบในระบบ ERP (มีเฉพาะใน IT)", ["asset_id"], {}

        ax_copy = copy.deepcopy(ax_record)

        if ax_record["is_scrapped"]:
            return False, "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน", ["status", "dept", "emp_id"], ax_copy

        emp_match = True
        ax_emp = ax_record["ax_emp_id"]
        if it_emp_id != ax_emp:
            if it_emp_id or ax_emp:
                emp_match = False
                diff_fields.append("emp_id")

        dept_match = is_dept_match(it_dept, ax_record["ax_dept"], ax_record["ax_loc_code"])
        if not dept_match:
            diff_fields.append("dept")

        if not emp_match and not dept_match:
            return False, "รหัสพนักงาน + แผนกไม่ตรง", diff_fields, ax_copy
        elif not emp_match:
            return False, "รหัสพนักงานไม่ตรง", diff_fields, ax_copy
        elif not dept_match:
            return False, "แผนกไม่ตรง", diff_fields, ax_copy
        else:
            return True, "ตรงกันสมบูรณ์", [], ax_copy

    def evaluate_single_record(self, rec: Dict[str, Any]) -> None:
        """Evaluate matching status for a single record based on its current cells and manual_exclude."""
        cat = rec["category"]
        cells = rec["cells"]
        aid, emp_id, emp_name, dept, sn = self._get_key_fields(cat, cells)
        rec["asset_id"] = aid
        rec["it_emp_id"] = emp_id
        rec["it_emp_name"] = emp_name
        rec["it_dept"] = dept
        rec["it_sn"] = sn

        # Baseline evaluation against ERP
        is_match, m_type, diff_fields, ax_copy = self._evaluate_values_against_erp(aid, emp_id, dept)
        rec["ax_data"] = ax_copy

        # Check exclusion rules
        if rec.get("manual_exclude") is True:
            rec["is_excluded"] = True
            rec["exclude_reason"] = "ผู้ใช้กำหนดให้ตัดออกเอง"
            rec["is_match"] = False
            rec["mismatch_type"] = "ตัดออกโดยผู้ใช้"
            rec["diff_fields"] = diff_fields
            return

        if rec.get("manual_exclude") is False:
            # Force include
            rec["is_excluded"] = False
            rec["exclude_reason"] = ""
            rec["is_match"] = is_match
            rec["mismatch_type"] = m_type
            rec["diff_fields"] = diff_fields
            return

        # Automatic exclusion
        if not aid or not ax_copy or ax_copy.get("is_scrapped"):
            rec["is_excluded"] = True
            rec["exclude_reason"] = (
                "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)" if not aid
                else ("ไม่พบในระบบ ERP (มีเฉพาะใน IT)" if not ax_copy else "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน")
            )
            rec["is_match"] = False
            rec["mismatch_type"] = rec["exclude_reason"]
            rec["diff_fields"] = diff_fields
        else:
            rec["is_excluded"] = False
            rec["exclude_reason"] = ""
            rec["is_match"] = is_match
            rec["mismatch_type"] = m_type
            rec["diff_fields"] = diff_fields

    def compare_category(self, category: str, reset_to_orig: bool = False) -> Dict[str, Any]:
        """Perform comparison on a single category, changing its state to 'compared'.
        If reset_to_orig is True, restores automatic cells to original file values (preserving user edits).
        """
        if category not in ("hw", "sw", "ups"):
            raise ValueError(f"Unknown category: {category}")

        recs = self.records.get(category, [])
        for r in recs:
            if reset_to_orig:
                user_cols = set(r.get("user_edited_cols", []))
                for col, orig_val in r.get("orig_cells", {}).items():
                    if col not in user_cols:
                        r["cells"][col] = orig_val
                if r.get("manual_exclude") is None:
                    r["is_excluded"] = False
                    r["exclude_reason"] = ""
            self.evaluate_single_record(r)

        self.category_states[category] = "compared"
        self.recompute_overall_summary()
        self.autosave()
        return self.summary.get("by_category", {}).get(category, {})

    def recompute_overall_summary(self) -> Dict[str, Any]:
        """Recalculate summary metrics per category and overall."""
        summary = {
            "overall": {
                "total_initial_records": 0,
                "total_records": 0,
                "matched_records": 0,
                "mismatched_records": 0,
                "excluded_records": 0,
                "user_edited_records": 0,
                "match_rate": 0.0,
                "verified_100_percent": False,
                "verification_passes": 0
            },
            "category_states": copy.deepcopy(self.category_states),
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
            "excluded_breakdown": {
                "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน": 0,
                "ไม่พบในระบบ ERP (มีเฉพาะใน IT)": 0,
                "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)": 0,
                "อื่นๆ": 0
            }
        }

        total_initial_all = 0
        total_active_all = 0
        matched_active_all = 0
        excluded_all = 0
        user_edited_all = 0

        for cat_key, cat_name in [("hw", "Hardware"), ("sw", "Software"), ("ups", "UPS & Monitor")]:
            recs = self.records.get(cat_key, [])
            c_state = self.category_states.get(cat_key, "empty")
            cat_initial_total = len(recs)
            cat_active_total = 0
            cat_matched = 0
            cat_excluded = 0
            cat_user_edited = 0

            if c_state == "compared":
                for r in recs:
                    if r.get("user_edited_cols"):
                        cat_user_edited += 1

                    if r.get("is_excluded"):
                        cat_excluded += 1
                        ex_reason = r.get("exclude_reason") or r.get("mismatch_type") or "อื่นๆ"
                        if ex_reason in summary["excluded_breakdown"]:
                            summary["excluded_breakdown"][ex_reason] += 1
                        else:
                            summary["excluded_breakdown"]["อื่นๆ"] += 1
                        continue

                    cat_active_total += 1
                    if r.get("is_match"):
                        cat_matched += 1
                    else:
                        m_type = r.get("mismatch_type", "อื่นๆ")
                        if m_type in summary["mismatch_breakdown"]:
                            summary["mismatch_breakdown"][m_type] += 1
                        else:
                            summary["mismatch_breakdown"]["อื่นๆ"] += 1

            cat_mismatched = cat_active_total - cat_matched
            cat_rate = round((cat_matched / cat_active_total * 100), 1) if cat_active_total > 0 else 0.0

            summary["by_category"][cat_key] = {
                "name": cat_name,
                "state": c_state,
                "initial_total": cat_initial_total,
                "total": cat_active_total,
                "matched": cat_matched,
                "mismatched": cat_mismatched,
                "excluded": cat_excluded,
                "user_edited": cat_user_edited,
                "match_rate": cat_rate,
                "verified_100_percent": (cat_active_total > 0 and cat_mismatched == 0 and cat_rate == 100.0)
            }

            if c_state == "compared":
                total_initial_all += cat_initial_total
                total_active_all += cat_active_total
                matched_active_all += cat_matched
                excluded_all += cat_excluded
                user_edited_all += cat_user_edited

        mismatched_active_all = total_active_all - matched_active_all
        overall_rate = round((matched_active_all / total_active_all * 100), 1) if total_active_all > 0 else 0.0
        is_verified_100 = (total_active_all > 0 and mismatched_active_all == 0 and overall_rate == 100.0)

        summary["overall"]["total_initial_records"] = total_initial_all
        summary["overall"]["total_records"] = total_active_all
        summary["overall"]["matched_records"] = matched_active_all
        summary["overall"]["mismatched_records"] = mismatched_active_all
        summary["overall"]["excluded_records"] = excluded_all
        summary["overall"]["user_edited_records"] = user_edited_all
        summary["overall"]["match_rate"] = overall_rate
        summary["overall"]["verified_100_percent"] = is_verified_100
        summary["overall"]["verification_passes"] = 3 if is_verified_100 else 0

        self.summary = summary
        return summary

    def recompare(self) -> Dict[str, Any]:
        """Re-run comparison across all categories that are in 'compared' state."""
        for cat in ["hw", "sw", "ups"]:
            if self.category_states.get(cat) == "compared":
                for r in self.records.get(cat, []):
                    self.evaluate_single_record(r)
        return self.recompute_overall_summary()

    def update_cell(self, uid: str, column: str, new_value: Any, user: str = "IT Staff") -> Optional[Dict[str, Any]]:
        """
        Update a single cell in a record:
        - Updates rec['cells'][column]
        - Marks column in rec['user_edited_cols']
        - If category is compared, re-evaluates row (auto-reinstates excluded if valid ERP asset)
        - Records undo action
        """
        cat = uid.split("_")[0]
        recs = self.records.get(cat, [])
        target_rec = next((r for r in recs if r["uid"] == uid), None)
        if not target_rec:
            return None

        old_val = target_rec["cells"].get(column, "")
        clean_new = clean_val(new_value)

        if str(old_val) == clean_new:
            return target_rec # No change

        old_user_edited = copy.deepcopy(target_rec["user_edited_cols"])
        old_is_excluded = target_rec.get("is_excluded")
        old_manual_exclude = target_rec.get("manual_exclude")
        old_match = target_rec.get("is_match")
        old_mtype = target_rec.get("mismatch_type")

        target_rec["cells"][column] = clean_new
        if column not in target_rec["user_edited_cols"]:
            target_rec["user_edited_cols"].append(column)

        # Check if asset_id was edited and now matches ERP
        cmap = COLUMN_MAP.get(cat, {})
        if column == cmap.get("asset_id") and target_rec.get("manual_exclude") is None:
            clean_aid = clean_asset_id(clean_new)
            ax = self.master_dict.get(clean_aid)
            if ax and not ax.get("is_scrapped"):
                target_rec["is_excluded"] = False
                target_rec["exclude_reason"] = ""

        if self.category_states.get(cat) == "compared":
            self.evaluate_single_record(target_rec)

        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        action = {
            "id": str(uuid.uuid4())[:8],
            "type": "cell_edit",
            "description": f"แก้ไข {cat.upper()} แถว {target_rec['row_index']+1} คอลัมน์ '{column}': {old_val} -> {clean_new}",
            "timestamp": timestamp,
            "uid": uid,
            "category": cat,
            "column": column,
            "old_value": old_val,
            "new_value": clean_new,
            "old_user_edited": old_user_edited,
            "old_manual_exclude": old_manual_exclude,
            "old_is_excluded": old_is_excluded,
            "user": user
        }
        self.push_undo_action(action)

        self.changelog.append({
            "uid": uid,
            "category": cat,
            "column": column,
            "old": old_val,
            "new": clean_new,
            "timestamp": timestamp,
            "user": user
        })

        self.recompute_overall_summary()
        self.autosave()
        return target_rec

    def set_row_exclusion(self, uid: str, exclude: bool, user: str = "IT Staff") -> Optional[Dict[str, Any]]:
        """Manually move row between active (Tab 3) and excluded (Tab 4)."""
        cat = uid.split("_")[0]
        recs = self.records.get(cat, [])
        target_rec = next((r for r in recs if r["uid"] == uid), None)
        if not target_rec:
            return None

        old_manual = target_rec.get("manual_exclude")
        old_is_excl = target_rec.get("is_excluded")

        target_rec["manual_exclude"] = exclude
        if exclude:
            target_rec["is_excluded"] = True
            target_rec["exclude_reason"] = "ผู้ใช้กำหนดให้ตัดออกเอง"
            target_rec["is_match"] = False
            target_rec["mismatch_type"] = "ตัดออกโดยผู้ใช้"
        else:
            target_rec["is_excluded"] = False
            target_rec["exclude_reason"] = ""
            if self.category_states.get(cat) == "compared":
                self.evaluate_single_record(target_rec)

        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        action = {
            "id": str(uuid.uuid4())[:8],
            "type": "row_exclusion",
            "description": f"{'ย้ายไปตัดออก' if exclude else 'คืนกลับเป็นใช้งาน'} {cat.upper()} แถว {target_rec['row_index']+1}",
            "timestamp": timestamp,
            "uid": uid,
            "category": cat,
            "old_manual_exclude": old_manual,
            "new_manual_exclude": exclude,
            "old_is_excluded": old_is_excl,
            "user": user
        }
        self.push_undo_action(action)
        self.recompute_overall_summary()
        self.autosave()
        return target_rec

    def batch_quick_fix(self, category: str = "all", user: str = "IT Staff") -> Dict[str, Any]:
        """
        Auto-Fix with User-Edit Precedence:
        - Syncs active ERP records with ERP AX values
        - SKIPS any column that is in rec['user_edited_cols']
        - SKIPS rows where manual_exclude is explicitly set
        - Separates unmatchable records into Tab 4
        - Verifies 3 passes
        """
        categories = [category] if category and category != "all" else ["hw", "sw", "ups"]
        updated_count = 0
        excluded_count = 0
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_items = []

        for cat in categories:
            cmap = COLUMN_MAP.get(cat, {})
            emp_id_col = cmap.get("emp_id")
            emp_name_col = cmap.get("emp_name")
            dept_col = cmap.get("dept")

            for r in self.records.get(cat, []):
                self.evaluate_single_record(r)
                aid, emp_id, emp_name, dept, sn = self._get_key_fields(cat, r["cells"])
                ax = self.master_dict.get(aid) if aid else None

                changes = {}
                old_cells = copy.deepcopy(r["cells"])
                old_user_edited = copy.deepcopy(r["user_edited_cols"])
                old_is_excl = r.get("is_excluded")

                if r.get("manual_exclude") is True:
                    continue # User manually excluded this row

                # Check unmatchable
                if not aid or not ax or ax.get("is_scrapped"):
                    reason = (
                        "ไม่มีรหัสทรัพย์สิน (Asset ID Missing)" if not aid
                        else ("ไม่พบในระบบ ERP (มีเฉพาะใน IT)" if not ax else "ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน")
                    )
                    if not r.get("is_excluded"):
                        r["is_excluded"] = True
                        r["exclude_reason"] = reason
                        excluded_count += 1
                        changes["is_excluded"] = {"old": False, "new": True}
                else:
                    if r.get("is_excluded") and r.get("manual_exclude") is None:
                        r["is_excluded"] = False
                        r["exclude_reason"] = ""
                        changes["is_excluded"] = {"old": True, "new": False}

                    ax_emp_id = clean_emp_id(ax.get("ax_emp_id", ""))
                    ax_emp_name = clean_val(ax.get("ax_emp_name", ""))
                    ax_dept = clean_val(ax.get("ax_dept", ""))

                    # Sync Employee ID (skip if user edited)
                    if emp_id_col and emp_id_col not in r["user_edited_cols"]:
                        if str(r["cells"].get(emp_id_col, "")).strip() != ax_emp_id:
                            changes[emp_id_col] = {"old": r["cells"].get(emp_id_col, ""), "new": ax_emp_id}
                            r["cells"][emp_id_col] = ax_emp_id

                    # Sync Employee Name (skip if user edited)
                    if emp_name_col and emp_name_col not in r["user_edited_cols"]:
                        if ax_emp_name and str(r["cells"].get(emp_name_col, "")).strip() != ax_emp_name:
                            changes[emp_name_col] = {"old": r["cells"].get(emp_name_col, ""), "new": ax_emp_name}
                            r["cells"][emp_name_col] = ax_emp_name
                        elif not ax_emp_id and not ax_emp_name and str(r["cells"].get(emp_name_col, "")).strip() != "":
                            changes[emp_name_col] = {"old": r["cells"].get(emp_name_col, ""), "new": ""}
                            r["cells"][emp_name_col] = ""

                    # Sync Dept (skip if user edited)
                    if dept_col and dept_col not in r["user_edited_cols"]:
                        if ax_dept and str(r["cells"].get(dept_col, "")).strip() != ax_dept:
                            changes[dept_col] = {"old": r["cells"].get(dept_col, ""), "new": ax_dept}
                            r["cells"][dept_col] = ax_dept
                        elif not ax_dept and not is_dept_match(r["cells"].get(dept_col, ""), ax_dept, ax.get("ax_loc_code", "")):
                            changes[dept_col] = {"old": r["cells"].get(dept_col, ""), "new": ""}
                            r["cells"][dept_col] = ""

                    if any(k != "is_excluded" for k in changes.keys()):
                        updated_count += 1

                if changes:
                    batch_items.append({
                        "uid": r["uid"],
                        "category": cat,
                        "old_cells": old_cells,
                        "new_cells": copy.deepcopy(r["cells"]),
                        "old_is_excluded": old_is_excl,
                        "new_is_excluded": r.get("is_excluded"),
                        "changes": changes
                    })

            # Verification passes (3 passes)
            for _vp in range(3):
                for r in self.records.get(cat, []):
                    self.evaluate_single_record(r)

            self.category_states[cat] = "compared"

        if batch_items:
            self.push_undo_action({
                "id": str(uuid.uuid4())[:8],
                "type": "batch_quick_fix",
                "description": f"Auto-Fix {category.upper()} ({updated_count} รายการ, ตัดออก {excluded_count} รายการ)",
                "timestamp": timestamp,
                "items": batch_items,
                "user": user
            })

        self.recompute_overall_summary()
        self.autosave()

        return {
            "success": True,
            "updated_count": updated_count,
            "excluded_count": excluded_count,
            "verification_passes": 3,
            "verified_100_percent": self.summary.get("overall", {}).get("verified_100_percent", False),
            "new_match_rate": self.summary.get("overall", {}).get("match_rate", 0),
            "overall": self.summary.get("overall", {})
        }

    def push_undo_action(self, action: Dict[str, Any]):
        """Push an action to undo stack, cap at 50, and clear redo stack."""
        self.undo_stack.append(action)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.autosave()

    def undo(self) -> Dict[str, Any]:
        """Undo last action."""
        if not self.undo_stack:
            return {"success": False, "message": "ไม่มีประวัติการกระทำที่จะเลิกทำ", "can_undo": False, "can_redo": len(self.redo_stack) > 0}

        action = self.undo_stack.pop()
        atype = action.get("type")

        if atype == "cell_edit":
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    r["cells"][action["column"]] = action["old_value"]
                    r["user_edited_cols"] = copy.deepcopy(action["old_user_edited"])
                    r["manual_exclude"] = action.get("old_manual_exclude")
                    r["is_excluded"] = action.get("old_is_excluded", False)
                    if self.category_states.get(cat) == "compared":
                        self.evaluate_single_record(r)
                    break
        elif atype == "row_exclusion":
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    r["manual_exclude"] = action.get("old_manual_exclude")
                    r["is_excluded"] = action.get("old_is_excluded", False)
                    if self.category_states.get(cat) == "compared":
                        self.evaluate_single_record(r)
                    break
        elif atype == "batch_quick_fix":
            for item in action.get("items", []):
                uid = item.get("uid")
                cat = uid.split("_")[0]
                for r in self.records.get(cat, []):
                    if r["uid"] == uid:
                        r["cells"] = copy.deepcopy(item["old_cells"])
                        r["is_excluded"] = item["old_is_excluded"]
                        if self.category_states.get(cat) == "compared":
                            self.evaluate_single_record(r)
                        break

        self.redo_stack.append(action)
        self.recompute_overall_summary()
        self.autosave()

        return {
            "success": True,
            "message": f"เลิกทำสำเร็จ: {action.get('description', '')}",
            "can_undo": len(self.undo_stack) > 0,
            "can_redo": True,
            "summary": self.summary
        }

    def redo(self) -> Dict[str, Any]:
        """Redo undone action."""
        if not self.redo_stack:
            return {"success": False, "message": "ไม่มีประวัติที่จะทำซ้ำ", "can_undo": len(self.undo_stack) > 0, "can_redo": False}

        action = self.redo_stack.pop()
        atype = action.get("type")

        if atype == "cell_edit":
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    r["cells"][action["column"]] = action["new_value"]
                    if action["column"] not in r["user_edited_cols"]:
                        r["user_edited_cols"].append(action["column"])
                    if self.category_states.get(cat) == "compared":
                        self.evaluate_single_record(r)
                    break
        elif atype == "row_exclusion":
            uid = action.get("uid")
            cat = uid.split("_")[0]
            for r in self.records.get(cat, []):
                if r["uid"] == uid:
                    r["manual_exclude"] = action.get("new_manual_exclude")
                    r["is_excluded"] = bool(action.get("new_manual_exclude"))
                    if self.category_states.get(cat) == "compared":
                        self.evaluate_single_record(r)
                    break
        elif atype == "batch_quick_fix":
            for item in action.get("items", []):
                uid = item.get("uid")
                cat = uid.split("_")[0]
                for r in self.records.get(cat, []):
                    if r["uid"] == uid:
                        r["cells"] = copy.deepcopy(item["new_cells"])
                        r["is_excluded"] = item["new_is_excluded"]
                        if self.category_states.get(cat) == "compared":
                            self.evaluate_single_record(r)
                        break

        self.undo_stack.append(action)
        self.recompute_overall_summary()
        self.autosave()

        return {
            "success": True,
            "message": f"ทำซ้ำสำเร็จ: {action.get('description', '')}",
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
                "user": act.get("user", "IT Officer")
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
        """Persist session state to disk atomically."""
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
                "version": "2.0",
                "category_states": self.category_states,
                "columns": self.columns,
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
            # Sync to SQLite DB automatically on autosave
            try:
                self.sync_to_sqlite()
            except Exception:
                pass
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Autosave failed: {e}", component="AUTOSAVE", exc_info=True)
            except Exception:
                pass

    def load_autosave(self, path: str) -> bool:
        """Restore session from autosave file if exists and is valid 2.0 structure."""
        self.autosave_path = path
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check version. If older legacy format without 'version': '2.0', discard
            if data.get("version") != "2.0":
                return False

            self.category_states = data.get("category_states", {"hw": "empty", "sw": "empty", "ups": "empty"})
            self.columns = data.get("columns", {"hw": [], "sw": [], "ups": []})
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

            self.recompute_overall_summary()
            return True
        except Exception as e:
            try:
                from logger_util import get_system_logger
                get_system_logger().error(f"Failed to load autosave from {path}: {e}", component="AUTOSAVE", exc_info=True)
            except Exception:
                pass
            return False

    def reset_session(self) -> bool:
        """Clear session back to empty state."""
        self.master_df = None
        self.master_dict = {}
        self.hw_df = None
        self.sw_df = None
        self.ups_df = None
        self.columns = {"hw": [], "sw": [], "ups": []}
        self.category_states = {"hw": "empty", "sw": "empty", "ups": "empty"}
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
