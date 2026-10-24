import sys
import os
import io

# Safeguard sys.stdout and sys.stderr in --noconsole windowed mode
class SafeWriter:
    def write(self, s): pass
    def flush(self): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = SafeWriter()
elif not hasattr(sys.stdout, "isatty"):
    sys.stdout.isatty = lambda: False

if sys.stderr is None:
    sys.stderr = SafeWriter()
elif not hasattr(sys.stderr, "isatty"):
    sys.stderr.isatty = lambda: False

import time
import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd

from engine.comparator import InventoryComparator
from engine.report_generator import ReportGenerator
from logger_util import get_system_logger, PRIMARY_LOG_FILE

logger = get_system_logger()

app = FastAPI(title="FTI IT Asset Inventory Compare System", version="1.0.0")

# Request Logging Middleware (Full Debug)
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    is_heartbeat = path == "/api/heartbeat"
    client_ip = request.client.host if request.client else "127.0.0.1"

    try:
        response = await call_next(request)
        elapsed_ms = (time.time() - start_time) * 1000
        if not is_heartbeat:
            logger.info(f"{request.method:4} {path:22} -> {response.status_code} [{elapsed_ms:.1f}ms] (Client: {client_ip})", component="HTTP")
        return response
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"{request.method:4} {path:22} -> FAILED: {e} [{elapsed_ms:.1f}ms]", component="HTTP", exc_info=True)
        raise

# Multi-path search for base data directory
candidate_dirs = [
    os.getcwd(),
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)),
    r"E:\WEB\FTI_Inventory Compare Automations",
    os.path.dirname(os.path.abspath(__file__))
]

BASE_DIR = os.getcwd()
for cdir in candidate_dirs:
    if cdir and os.path.exists(os.path.join(cdir, "0-FTI_asset_HWSWOth.xlsx")):
        BASE_DIR = cdir
        break

if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
    STATIC_DIR = os.path.join(BUNDLE_DIR, "static") if os.path.exists(os.path.join(BUNDLE_DIR, "static")) else os.path.join(EXE_DIR, "static")
else:
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Mount static files
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global singleton comparator instance
comparator = InventoryComparator()

# Autosave session configuration
AUTOSAVE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", BASE_DIR), "FTI_Inventory_Compare")
os.makedirs(AUTOSAVE_DIR, exist_ok=True)
AUTOSAVE_FILE = os.path.join(AUTOSAVE_DIR, "session_autosave.json")
comparator.autosave_path = AUTOSAVE_FILE

def init_app_session():
    """Start with restored autosave if present; otherwise clean slate for MVP."""
    try:
        restored = comparator.load_autosave(AUTOSAVE_FILE)
        if restored:
            total = comparator.summary.get('overall', {}).get('total_records', 0)
            rate = comparator.summary.get('overall', {}).get('match_rate', 0)
            logger.info(f"Restored previous session from autosave: {total} records, {rate}% match rate", component="AUTOSAVE")
        else:
            logger.info("Clean session initialized. Ready for file upload.", component="SESSION")
    except Exception as e:
        logger.error(f"Error initializing session: {e}", component="SESSION", exc_info=True)

# Initialize on module load
init_app_session()


@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI application startup completed.", component="SYSTEM")


# Pydantic models
class EditRecordRequest(BaseModel):
    uid: str
    it_emp_id: Optional[str] = None
    it_emp_name: Optional[str] = None
    it_dept: Optional[str] = None
    asset_id: Optional[str] = None
    it_sn: Optional[str] = None
    user: Optional[str] = "IT Officer"

last_heartbeat_time = datetime.datetime.now().timestamp()
server_ref = None

def get_last_heartbeat() -> float:
    global last_heartbeat_time
    return last_heartbeat_time

def set_server_instance(srv):
    global server_ref
    server_ref = srv

@app.get("/api/heartbeat")
async def get_heartbeat():
    global last_heartbeat_time
    last_heartbeat_time = datetime.datetime.now().timestamp()
    return {"status": "ok", "time": last_heartbeat_time}

@app.post("/api/shutdown")
async def request_shutdown(force: bool = False):
    """Explicit shutdown initiated by user action."""
    global server_ref
    if force and server_ref is not None:
        logger.info("Explicit shutdown requested by user.", component="SYSTEM")
        server_ref.should_exit = True
        return {"status": "shutting down"}
    return {"status": "ignored"}

@app.get("/api/logs")
async def get_system_logs(lines: int = Query(default=150, ge=1, le=2000)):
    """Fetch live log content for UI diagnostic modal."""
    if not os.path.exists(PRIMARY_LOG_FILE):
        return JSONResponse({"log_file": PRIMARY_LOG_FILE, "lines": []})
    try:
        with open(PRIMARY_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            return JSONResponse({
                "log_file": PRIMARY_LOG_FILE,
                "total_lines": len(all_lines),
                "lines": [l.rstrip("\r\n") for l in all_lines[-lines:]]
            })
    except Exception as e:
        return JSONResponse({"log_file": PRIMARY_LOG_FILE, "error": str(e), "lines": []})

@app.get("/api/logs/download")
async def download_system_log():
    """Download the full fti_debug.log file."""
    if os.path.exists(PRIMARY_LOG_FILE):
        return FileResponse(PRIMARY_LOG_FILE, filename="fti_debug.log", media_type="text/plain")
    raise HTTPException(status_code=404, detail="Log file not found")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>FTI IT Asset Inventory Compare System</h1><p>UI loading...</p>")


@app.get("/api/summary")
async def get_summary():
    """Return overall and categorized match rate and metrics."""
    if not comparator.summary:
        comparator.recompare()
    return JSONResponse(comparator.summary)


@app.get("/api/records")
async def get_records(
    category: str = Query("all", description="all, hw, sw, ups"),
    mismatch_only: bool = Query(True),
    filter_type: str = Query("all", description="all, both, emp, dept, scrapped, missing"),
    search: str = Query("", description="search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=500)
):
    """Retrieve paginated records with filtering."""
    offset = (page - 1) * page_size
    
    # 1. Get raw records
    recs, _ = comparator.get_records(
        category=category,
        mismatch_only=mismatch_only,
        search=search,
        limit=999999,
        offset=0
    )

    # 2. Apply filter_type if specified
    if filter_type == "both":
        recs = [r for r in recs if "รหัสพนักงาน + แผนก" in r.get("mismatch_type", "")]
    elif filter_type == "emp":
        recs = [r for r in recs if r.get("mismatch_type") == "รหัสพนักงานไม่ตรง"]
    elif filter_type == "dept":
        recs = [r for r in recs if r.get("mismatch_type") == "แผนกไม่ตรง"]
    elif filter_type == "scrapped":
        recs = [r for r in recs if "ตัดจำหน่าย" in r.get("mismatch_type", "")]
    elif filter_type == "missing":
        recs = [r for r in recs if "ไม่พบ" in r.get("mismatch_type", "")]

    total_count = len(recs)
    paginated_recs = recs[offset: offset + page_size]

    return JSONResponse({
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
        "records": paginated_recs
    })


class QuickFixRequest(BaseModel):
    uid: str
    user: Optional[str] = "IT Officer"


@app.post("/api/quick-fix")
async def quick_fix_record(req: QuickFixRequest):
    """Automatically synchronize IT record fields to match ERP AX values."""
    cat = req.uid.split("_")[0]
    rec = None
    for r in comparator.records.get(cat, []):
        if r["uid"] == req.uid:
            rec = r
            break
    if not rec:
        raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลรหัส {req.uid}")

    ax = rec.get("ax_data", {})
    if not ax or not ax.get("asset_id"):
        return JSONResponse({
            "success": False,
            "status": "warning",
            "message": f"รหัส {rec.get('asset_id', req.uid)} ไม่มีข้อมูลในระบบ ERP สำหรับซิงค์",
            "summary": comparator.summary
        })

    fields_to_update = {}
    if ax.get("ax_emp_id"):
        fields_to_update["it_emp_id"] = str(ax["ax_emp_id"]).strip()
    if ax.get("ax_emp_name"):
        fields_to_update["it_emp_name"] = str(ax["ax_emp_name"]).strip()
    if ax.get("ax_dept"):
        fields_to_update["it_dept"] = str(ax["ax_dept"]).strip()

    if not fields_to_update:
        return JSONResponse({
            "success": False,
            "status": "info",
            "message": "ข้อมูลในระบบ ERP เป็นค่าว่าง ไม่มีการเปลี่ยนแปลง",
            "summary": comparator.summary
        })

    updated = comparator.update_record(req.uid, fields_to_update, user=req.user or "IT Officer")
    return JSONResponse({
        "success": True,
        "status": "success",
        "message": f"ปรับปรุงข้อมูล {rec.get('asset_id')} ให้ตรงกับ ERP แล้ว",
        "record": updated,
        "summary": comparator.summary
    })


class BatchQuickFixRequest(BaseModel):
    category: Optional[str] = "all"
    user: Optional[str] = "IT Officer"


@app.post("/api/batch-quick-fix")
async def batch_quick_fix(req: BatchQuickFixRequest = BatchQuickFixRequest()):
    """Automatically synchronize all mismatched IT records with ERP AX."""
    res = comparator.batch_quick_fix(category=req.category or "all", user=req.user or "IT Officer")
    count = res.get('updated_count', 0)
    if count > 0:
        msg = f"อัปเดตข้อมูลให้ตรงกับ ERP เรียบร้อยแล้ว {count:,} รายการ"
    else:
        msg = "ข้อมูลในระบบตรงกับ ERP อยู่แล้ว หรือไม่พบรายการที่มีข้อมูล ERP ให้ซิงค์"

    return JSONResponse({
        "status": "success",
        "message": msg,
        "result": res,
        "summary": comparator.summary,
        "can_undo": len(comparator.undo_stack) > 0,
        "can_redo": len(comparator.redo_stack) > 0
    })


# =========================================================================
# Google Workspace-style Undo, Redo, Version History & Session Reset
# =========================================================================
@app.post("/api/undo")
async def undo_action():
    """Rollback the last action like Google Workspace Ctrl+Z."""
    res = comparator.undo()
    logger.info(f"Undo action: {res.get('message')}", component="HISTORY")
    return JSONResponse(res)


@app.post("/api/redo")
async def redo_action():
    """Re-apply the undone action (Ctrl+Y)."""
    res = comparator.redo()
    logger.info(f"Redo action: {res.get('message')}", component="HISTORY")
    return JSONResponse(res)


@app.get("/api/history")
async def get_history_timeline():
    """Return version history timeline of all actions."""
    return JSONResponse({
        "history": comparator.get_version_history(),
        "can_undo": len(comparator.undo_stack) > 0,
        "can_redo": len(comparator.redo_stack) > 0
    })


class RollbackRequest(BaseModel):
    index: int


@app.post("/api/rollback")
async def rollback_to_version(req: RollbackRequest):
    """Rollback to a specific revision in history."""
    res = comparator.rollback_to_index(req.index)
    logger.info(f"Rollback to revision {req.index}: {res.get('message')}", component="HISTORY")
    return JSONResponse(res)


@app.post("/api/session/reset")
async def reset_current_session():
    """Reset session to clean slate, wiping autosave file."""
    comparator.reset_session()
    logger.info("Session reset to clean slate by user.", component="SESSION")
    return JSONResponse({
        "success": True,
        "status": "success",
        "message": "ล้างข้อมูลทั้งหมดเรียบร้อยแล้ว พร้อมเริ่มเซสชันใหม่",
        "summary": comparator.summary
    })


@app.get("/api/session/status")
async def get_session_status():
    """Get active session details and undo/redo capabilities."""
    total = comparator.summary.get('overall', {}).get('total_records', 0) if comparator.summary else 0
    return JSONResponse({
        "has_data": total > 0 or len(comparator.master_dict) > 0,
        "total_records": total,
        "can_undo": len(comparator.undo_stack) > 0,
        "can_redo": len(comparator.redo_stack) > 0,
        "history_count": len(comparator.undo_stack),
        "autosave_path": comparator.autosave_path
    })


@app.get("/api/files-status")
async def get_files_status():
    """Return status of all 4 loaded files."""
    return JSONResponse({
        "master": {
            "loaded": len(comparator.master_dict) > 0 or comparator.master_df is not None,
            "rows": len(comparator.master_dict) if len(comparator.master_dict) > 0 else (len(comparator.master_df) if comparator.master_df is not None else 0),
            "filename": getattr(comparator, "master_filename", "Master ERP AX Data" if len(comparator.master_dict) > 0 else None)
        },
        "hw": {
            "loaded": len(comparator.records.get("hw", [])) > 0,
            "rows": len(comparator.records.get("hw", [])),
            "filename": getattr(comparator, "hw_filename", "Hardware Inventory" if len(comparator.records.get("hw", [])) > 0 else None)
        },
        "sw": {
            "loaded": len(comparator.records.get("sw", [])) > 0,
            "rows": len(comparator.records.get("sw", [])),
            "filename": getattr(comparator, "sw_filename", "Software Inventory" if len(comparator.records.get("sw", [])) > 0 else None)
        },
        "ups": {
            "loaded": len(comparator.records.get("ups", [])) > 0,
            "rows": len(comparator.records.get("ups", [])),
            "filename": getattr(comparator, "ups_filename", "UPS & Monitor Inventory" if len(comparator.records.get("ups", [])) > 0 else None)
        }
    })


@app.post("/api/correct")
async def correct_record(req: EditRecordRequest):
    """Update fields of an in-memory inventory record."""
    fields_to_update = {}
    if req.it_emp_id is not None:
        fields_to_update["it_emp_id"] = req.it_emp_id.strip()
    if req.it_emp_name is not None:
        fields_to_update["it_emp_name"] = req.it_emp_name.strip()
    if req.it_dept is not None:
        fields_to_update["it_dept"] = req.it_dept.strip()
    if req.asset_id is not None:
        fields_to_update["asset_id"] = req.asset_id.strip().upper()
    if req.it_sn is not None:
        fields_to_update["it_sn"] = req.it_sn.strip()

    updated = comparator.update_record(req.uid, fields_to_update, user=req.user or "IT Officer")
    if not updated:
        raise HTTPException(status_code=404, detail=f"Record {req.uid} not found")

    return JSONResponse({
        "status": "success",
        "message": f"Updated record {req.uid}",
        "record": updated,
        "summary": comparator.summary
    })


@app.post("/api/recompare")
async def recompare_data():
    """Trigger complete re-comparison and refresh KPI statistics."""
    summary = comparator.recompare()
    return JSONResponse({
        "status": "success",
        "message": "Re-comparison complete",
        "summary": summary
    })


@app.post("/api/upload")
async def upload_files(
    file_type: str = Form(..., description="master, hw, sw, ups"),
    file: UploadFile = File(...)
):
    """Upload new Excel file dynamically."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are supported")

    content = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {str(e)}")

    if file_type == "master":
        comparator.master_filename = file.filename
        comparator.load_master(df)
        comparator.recompare()
        comparator.autosave()
        return JSONResponse({"status": "success", "message": f"โหลดไฟล์หลัก ERP สำเร็จ ({len(df):,} รายการ)", "filename": file.filename})
    elif file_type == "hw":
        comparator.hw_filename = file.filename
        comparator.hw_df = df
        comparator.records["hw"] = comparator._parse_hw_df(df)
    elif file_type == "sw":
        comparator.sw_filename = file.filename
        comparator.sw_df = df
        comparator.records["sw"] = comparator._parse_sw_df(df)
    elif file_type == "ups":
        comparator.ups_filename = file.filename
        comparator.ups_df = df
        comparator.records["ups"] = comparator._parse_ups_df(df)
    else:
        raise HTTPException(status_code=400, detail="Invalid file_type")

    comparator.recompare()
    comparator.autosave()
    return JSONResponse({
        "status": "success",
        "message": f"อัปโหลดไฟล์ {file_type.upper()} สำเร็จ ({len(df):,} รายการ)",
        "filename": file.filename,
        "summary": comparator.summary
    })


@app.post("/api/reset")
async def reset_data():
    """Reset all records and start clean session."""
    comparator.reset_session()
    return JSONResponse({
        "status": "success",
        "message": "ล้างข้อมูลทั้งหมดแล้ว พร้อมเริ่มเซสชันใหม่",
        "summary": comparator.summary
    })


@app.get("/api/changelog")
async def get_changelog():
    """Return list of edits made during the session."""
    return JSONResponse({
        "total_edits": len(comparator.changelog),
        "changelog": comparator.changelog
    })


@app.get("/api/export/report")
async def export_mismatch_report(category: Optional[str] = Query("all")):
    """Download styled Excel mismatch report directly."""
    buf = ReportGenerator.generate_mismatch_report_bytes(comparator, category=category)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = category.upper() if category and category != "all" else "ALL"
    filename = f"{prefix}_Mismatch_Report_{now_str}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/export/inventory/{category}")
async def export_inventory_file(category: str):
    """Download corrected inventory Excel file."""
    if category not in ("hw", "sw", "ups"):
        raise HTTPException(status_code=400, detail="Category must be hw, sw, or ups")

    buf = ReportGenerator.export_corrected_inventory_bytes(comparator, category)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name_map = {
        "hw": "1-it_asset_HW_Corrected",
        "sw": "2-it_asset_SW_Corrected",
        "ups": "3-it_asset_UPS_Monitor_Corrected"
    }
    filename = f"{name_map[category]}_{now_str}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
