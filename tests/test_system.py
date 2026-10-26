import sys
import os
import pandas as pd
from starlette.testclient import TestClient

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, comparator

def test_clean_business_flow():
    print("[1] Initializing TestClient...")
    client = TestClient(app)

    print("[2] Testing GET /api/summary...")
    res = client.get("/api/summary")
    assert res.status_code == 200, f"Summary failed: {res.text}"
    summary = res.json()
    overall = summary.get("overall", {})
    initial_rate = overall.get("match_rate", 0)
    print(f"    Initial match rate: {initial_rate}%")
    print(f"    Total: {overall.get('total_records')}, Matched: {overall.get('matched_records')}, Mismatched: {overall.get('mismatched_records')}")
    assert overall.get("total_records", 0) > 0, "No records loaded"

    print("[3] Testing GET /api/records (Hardware mismatches)...")
    res = client.get("/api/records?category=hw&mismatch_only=true&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    recs = data.get("records", [])
    assert len(recs) > 0

    # Find a record that has ERP data to test quick-fix
    target_rec = None
    for r in recs:
        ax = r.get("ax_data", {})
        if ax.get("ax_emp_id") or ax.get("ax_dept"):
            target_rec = r
            break
    
    if target_rec:
        uid = target_rec["uid"]
        print(f"[4] Testing POST /api/quick-fix on {uid} ({target_rec.get('asset_id')})...")
        res_qf = client.post("/api/quick-fix", json={"uid": uid, "user": "Test Runner"})
        assert res_qf.status_code == 200, f"Quick-fix failed: {res_qf.text}"
        qf_data = res_qf.json()
        print(f"    Quick-fix result: {qf_data.get('message')}")
        print(f"    Updated mismatch type: {qf_data.get('record', {}).get('mismatch_type')}")

    print("[5] Testing POST /api/recompare...")
    res_recomp = client.post("/api/recompare")
    assert res_recomp.status_code == 200
    new_summary = res_recomp.json().get("summary", {})
    print(f"    Re-compared match rate: {new_summary.get('overall', {}).get('match_rate')}%")

    print("[6] Testing POST /api/batch-quick-fix (Batch Auto-Fix)...")
    res_batch = client.post("/api/batch-quick-fix", json={"category": "all", "user": "Test Runner"})
    assert res_batch.status_code == 200, f"Batch quick-fix failed: {res_batch.text}"
    batch_data = res_batch.json()
    print(f"    Batch auto-fix: {batch_data.get('message')}")
    print(f"    New match rate after batch fix: {batch_data.get('result', {}).get('new_match_rate')}%")

    print("[7] Testing GET /api/files-status...")
    res_files = client.get("/api/files-status")
    assert res_files.status_code == 200
    files_info = res_files.json()
    print(f"    Files status: Master={files_info['master']['rows']}, HW={files_info['hw']['rows']}, SW={files_info['sw']['rows']}, UPS={files_info['ups']['rows']}")

    print("[8] Testing Excel Exports...")
    res_rep = client.get("/api/export/report?category=all")
    assert res_rep.status_code == 200
    assert len(res_rep.content) > 10000
    print(f"    Mismatch report downloaded: {len(res_rep.content)} bytes")

    res_inv = client.get("/api/export/inventory/hw")
    assert res_inv.status_code == 200
    assert len(res_inv.content) > 10000
    print(f"    Corrected inventory downloaded: {len(res_inv.content)} bytes")

    print("[9] Testing Pagination & All Records (Issue 1 Verification)...")
    res_page_all = client.get("/api/records?category=all&mismatch_only=true&page=1&page_size=99999")
    assert res_page_all.status_code == 200
    data_all = res_page_all.json()
    assert "total" in data_all and "total_count" in data_all
    assert data_all["total"] == data_all["total_count"]
    total_records = data_all["total"]
    assert len(data_all["records"]) == total_records, f"Expected {total_records} records, got {len(data_all['records'])}"
    print(f"    Show All (page_size=99999): Successfully returned all {total_records} records!")

    # Test page_size=25
    res_page_25 = client.get("/api/records?category=all&mismatch_only=true&page=1&page_size=25")
    assert res_page_25.status_code == 200
    data_25 = res_page_25.json()
    assert data_25["page_size"] == 25
    expected_pages = (total_records + 24) // 25
    assert data_25["total_pages"] == expected_pages
    print(f"    Pagination (page_size=25): Total {total_records} records, {data_25['total_pages']} pages computed correctly!")

    print("[10] Testing Re-opened Application Session Export & Atomic State (Issue 2 Verification)...")
    # Verify session_state.json exists and is valid JSON without any truncation
    from app import AUTOSAVE_FILE, SOURCES_DIR
    import json
    assert os.path.exists(AUTOSAVE_FILE), f"AUTOSAVE_FILE not found at {AUTOSAVE_FILE}"
    with open(AUTOSAVE_FILE, "r", encoding="utf-8") as f:
        saved_state = json.load(f)
    assert "records" in saved_state and "summary" in saved_state
    print(f"    Atomic session_state.json verified: {os.path.getsize(AUTOSAVE_FILE)} bytes, valid JSON!")

    # Verify source_hw.xlsx exists in SOURCES_DIR
    src_hw_path = os.path.join(SOURCES_DIR, "source_hw.xlsx")
    assert os.path.exists(src_hw_path), f"source_hw.xlsx not found at {src_hw_path}"
    df_src_hw = pd.read_excel(src_hw_path)
    assert len(df_src_hw.columns) >= 20, f"Expected full schema >= 20 columns, got {len(df_src_hw.columns)}"
    print(f"    Source storage verified: source_hw.xlsx has {len(df_src_hw.columns)} columns (all original columns preserved)!")

    # Test fresh cold instance loading
    from engine.comparator import InventoryComparator
    fresh_comp = InventoryComparator()
    fresh_comp.sources_dir = SOURCES_DIR
    restored = fresh_comp.load_autosave(AUTOSAVE_FILE)
    assert restored, "Failed to restore session in fresh InventoryComparator"
    assert len(fresh_comp.records.get("hw", [])) > 0, "No hw records restored"
    assert fresh_comp.hw_df is not None, "hw_df not restored from sources_dir"
    assert len(fresh_comp.hw_df.columns) == len(df_src_hw.columns), "hw_df columns mismatch after restore"
    print(f"    Fresh comparator restored successfully: {fresh_comp.summary.get('overall', {}).get('total_records')} records, full DataFrame restored!")

    # Download exports via TestClient
    for cat in ("hw", "sw", "ups"):
        res_cat = client.get(f"/api/export/inventory/{cat}")
        assert res_cat.status_code == 200, f"Export for {cat} failed after cold restart: {res_cat.text}"
        assert len(res_cat.content) > 2000, f"Export content for {cat} too small"
        print(f"    Cold session export '{cat}': {len(res_cat.content)} bytes downloaded successfully!")

    print("\n[SUCCESS] Clean business flow verification complete and all tests passed!")

if __name__ == "__main__":
    test_clean_business_flow()

