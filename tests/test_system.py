import sys
import os
import io
import json
import openpyxl
import pandas as pd
from starlette.testclient import TestClient

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app, comparator, AUTOSAVE_FILE, SOURCES_DIR
from engine.comparator import clean_emp_id, clean_val, clean_asset_id


def test_clean_business_flow():
    print("[1] Initializing TestClient and loading fresh baseline...")
    client = TestClient(app)

    # Ensure fresh baseline from original Excel files to test full lifecycle
    comparator.load_master(os.path.join(BASE_DIR, "0-FTI_asset_HWSWOth.xlsx"))
    comparator.load_inventory_files(
        os.path.join(BASE_DIR, "1-it_asset_HW.xlsx"),
        os.path.join(BASE_DIR, "2-it_asset_SW.xlsx"),
        os.path.join(BASE_DIR, "3-it_asset_UPS_Monitor.xlsx")
    )

    print("[2] Testing GET /api/summary (Initial State before Auto-Fix)...")
    res = client.get("/api/summary")
    assert res.status_code == 200, f"Summary failed: {res.text}"
    summary = res.json()
    overall = summary.get("overall", {})
    print(f"    Initial match rate: {overall.get('match_rate')}%")
    print(f"    Total: {overall.get('total_records')}, Matched: {overall.get('matched_records')}, Mismatched: {overall.get('mismatched_records')}")
    assert overall.get("total_initial_records") == 1516, f"Expected 1516 initial records, got {overall.get('total_initial_records')}"

    print("[3] Testing GET /api/records (Hardware mismatches)...")
    res = client.get("/api/records?category=hw&mismatch_only=true&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    recs = data.get("records", [])
    assert len(recs) > 0

    # Find an active ERP record to test single quick-fix
    target_rec = None
    for r in recs:
        ax = r.get("ax_data", {})
        if ax.get("asset_id") and not ax.get("is_scrapped"):
            target_rec = r
            break

    if target_rec:
        uid = target_rec["uid"]
        print(f"[4] Testing POST /api/quick-fix on {uid} ({target_rec.get('asset_id')})...")
        res_qf = client.post("/api/quick-fix", json={"uid": uid, "user": "Test Runner"})
        assert res_qf.status_code == 200, f"Quick-fix failed: {res_qf.text}"
        qf_data = res_qf.json()
        print(f"    Quick-fix result: {qf_data.get('message')}")
        assert qf_data.get("record", {}).get("is_match") is True

    print("[5] Testing POST /api/batch-quick-fix (100% Reconciliation + Multi-Pass Verification)...")
    res_batch = client.post("/api/batch-quick-fix", json={"category": "all", "user": "Test Runner"})
    assert res_batch.status_code == 200, f"Batch quick-fix failed: {res_batch.text}"
    batch_data = res_batch.json()
    b_res = batch_data.get("result", {})
    b_sum = batch_data.get("summary", {}).get("overall", {})
    print(f"    Batch message: {batch_data.get('message')}")
    print(f"    Active Matched: {b_sum.get('matched_records')} / {b_sum.get('total_records')} ({b_sum.get('match_rate')}%)")
    print(f"    Mismatched remaining: {b_sum.get('mismatched_records')}")
    print(f"    Excluded (Tab 4): {b_sum.get('excluded_records')}")
    print(f"    Verified 100% (3 passes): {b_sum.get('verified_100_percent')} (passes={b_sum.get('verification_passes')})")

    assert b_sum.get("match_rate") == 100.0, f"Expected 100.0% match rate, got {b_sum.get('match_rate')}"
    assert b_sum.get("mismatched_records") == 0, f"Expected 0 mismatched records, got {b_sum.get('mismatched_records')}"
    assert b_sum.get("matched_records") == 775, f"Expected 775 active matched records, got {b_sum.get('matched_records')}"
    assert b_sum.get("excluded_records") == 741, f"Expected 741 excluded records, got {b_sum.get('excluded_records')}"
    assert b_sum.get("verified_100_percent") is True, "Expected verified_100_percent to be True"
    assert b_sum.get("verification_passes") == 3, "Expected 3 verification passes"

    print("[6] Testing GET /api/records for Active 100% Matched vs Excluded (Tab 4)...")
    res_active = client.get("/api/records?category=all&mismatch_only=false&filter_type=all&page=1&page_size=99999")
    assert res_active.status_code == 200
    data_active = res_active.json()
    assert data_active["total"] == 775, f"Expected 775 active records, got {data_active['total']}"
    assert len(data_active["records"]) == 775

    res_excl = client.get("/api/records?category=all&filter_type=excluded&page=1&page_size=99999")
    assert res_excl.status_code == 200
    data_excl = res_excl.json()
    assert data_excl["total"] == 741, f"Expected 741 excluded records, got {data_excl['total']}"
    assert len(data_excl["records"]) == 741
    print(f"    Active records: {data_active['total']}, Excluded records: {data_excl['total']} (Sum = {data_active['total'] + data_excl['total']})")

    print("[7] Testing 4-Tab Excel Exports & Independent 3-Pass Audit on Tab 3...")
    expected_counts = {
        "hw": {"filename": "1-it_asset_HW.xlsx", "total": 235, "active": 93, "excluded": 142, "cols": 25},
        "sw": {"filename": "2-it_asset_SW.xlsx", "total": 899, "active": 504, "excluded": 395, "cols": 14},
        "ups": {"filename": "3-it_asset_UPS_Monitor.xlsx", "total": 382, "active": 178, "excluded": 204, "cols": 18},
    }
    expected_sheets = [
        "1_ข้อมูลเดิม",
        "2_เปรียบเทียบชี้จุดต่าง",
        "3_ข้อมูลแก้ไขแล้ว_100%",
        "4_ข้อมูลที่ถูกตัดออก"
    ]

    for cat, spec in expected_counts.items():
        res_inv = client.get(f"/api/export/inventory/{cat}")
        assert res_inv.status_code == 200, f"Export failed for {cat}: {res_inv.text}"
        wb = openpyxl.load_workbook(io.BytesIO(res_inv.content), data_only=True)
        assert wb.sheetnames == expected_sheets, f"Unexpected sheets for {cat}: {wb.sheetnames}"

        ws1 = wb["1_ข้อมูลเดิม"]
        ws2 = wb["2_เปรียบเทียบชี้จุดต่าง"]
        ws3 = wb["3_ข้อมูลแก้ไขแล้ว_100%"]
        ws4 = wb["4_ข้อมูลที่ถูกตัดออก"]

        rows_tab1 = ws1.max_row - 1
        rows_tab2 = ws2.max_row - 1
        rows_tab3 = ws3.max_row - 1
        rows_tab4 = ws4.max_row - 1

        assert rows_tab1 == spec["total"], f"{cat} Tab 1 rows: expected {spec['total']}, got {rows_tab1}"
        assert rows_tab2 == spec["total"], f"{cat} Tab 2 rows: expected {spec['total']}, got {rows_tab2}"
        assert rows_tab3 == spec["active"], f"{cat} Tab 3 rows: expected {spec['active']}, got {rows_tab3}"
        assert rows_tab4 == spec["excluded"], f"{cat} Tab 4 rows: expected {spec['excluded']}, got {rows_tab4}"
        assert rows_tab3 + rows_tab4 == rows_tab1, f"{cat} row conservation failed: {rows_tab3} + {rows_tab4} != {rows_tab1}"

        assert ws1.max_column == spec["cols"], f"{cat} Tab 1 cols: expected {spec['cols']}, got {ws1.max_column}"
        assert ws3.max_column == spec["cols"], f"{cat} Tab 3 cols: expected {spec['cols']}, got {ws3.max_column}"
        assert ws4.max_column == spec["cols"] + 6, f"{cat} Tab 4 cols: expected {spec['cols'] + 6}, got {ws4.max_column}"

        # Independent 3-Pass Verification directly on Tab 3 Excel cells against Master ERP
        df_tab3 = pd.read_excel(io.BytesIO(res_inv.content), sheet_name="3_ข้อมูลแก้ไขแล้ว_100%")
        assert len(df_tab3) == spec["active"]

        for p in range(1, 4):
            mismatch_in_pass = 0
            for idx, row in df_tab3.iterrows():
                aid = clean_asset_id(row.get("เลขที่ทรัพย์สิน", ""))
                emp = clean_emp_id(row.get("รหัสพนักงาน", ""))
                dept = clean_val(row.get("สถานที่เก็บ", ""))

                is_m, m_type, _, ax = comparator._evaluate_values_against_erp(aid, emp, dept)
                assert ax is not None and ax.get("asset_id"), f"Pass {p}: Asset {aid} in Tab 3 not found in Master ERP!"
                assert not ax.get("is_scrapped"), f"Pass {p}: Asset {aid} in Tab 3 is scrapped in Master ERP!"
                if not is_m or emp != clean_emp_id(ax.get("ax_emp_id", "")) or dept != clean_val(ax.get("ax_dept", "")):
                    mismatch_in_pass += 1
            assert mismatch_in_pass == 0, f"Pass {p} failed for {cat}: {mismatch_in_pass} mismatches found!"

        print(f"    Verified {spec['filename']}: Tab1={rows_tab1}, Tab2={rows_tab2}, Tab3={rows_tab3} (100% matched across 3 passes), Tab4={rows_tab4}")

    print("[8] Testing ZIP Export (/api/export/inventory-all) and Output Directory Files...")
    res_zip = client.get("/api/export/inventory-all")
    assert res_zip.status_code == 200
    assert len(res_zip.content) > 50000

    out_dir = os.path.join(BASE_DIR, "output")
    for cat, spec in expected_counts.items():
        fpath = os.path.join(out_dir, spec["filename"])
        assert os.path.exists(fpath), f"Output file missing: {fpath}"
        assert os.path.getsize(fpath) > 10000
    print(f"    All 3 files verified in {out_dir} and in ZIP bundle ({len(res_zip.content):,} bytes)!")

    print("[9] Testing Cold Session Restart & Persistence...")
    from engine.comparator import InventoryComparator
    fresh_comp = InventoryComparator()
    fresh_comp.sources_dir = SOURCES_DIR
    restored = fresh_comp.load_autosave(AUTOSAVE_FILE)
    assert restored, "Failed to restore session in fresh InventoryComparator"
    assert fresh_comp.summary["overall"]["match_rate"] == 100.0
    assert fresh_comp.summary["overall"]["matched_records"] == 775
    assert fresh_comp.summary["overall"]["excluded_records"] == 741
    print("    Cold session restore verified: 100.0% match rate, 775 matched, 741 excluded preserved!")

    print("\n[SUCCESS] All 100% Reconciliation, 4-Tab Excel Exports, and 3-Pass Audit tests passed!")


if __name__ == "__main__":
    test_clean_business_flow()
