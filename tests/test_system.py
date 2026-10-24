import sys
import os
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

    print("\n[SUCCESS] Clean business flow verification complete and all tests passed!")

if __name__ == "__main__":
    test_clean_business_flow()
