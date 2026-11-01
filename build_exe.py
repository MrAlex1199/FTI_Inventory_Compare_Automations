import os
import sys
import json
import shutil
import datetime
import subprocess

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def bump_build_version(base_dir: str) -> dict:
    version_file = os.path.join(base_dir, "version.json")
    vdata = {
        "version": "2.1.0",
        "build_number": 1,
        "build_date": datetime.datetime.now().strftime("%Y.%m.%d"),
        "compiled_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "display_version": "v2.1.0 (Build 2026.11.01-01)"
    }
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                vdata = json.load(f)
        except Exception:
            pass

    today_str = datetime.datetime.now().strftime("%Y.%m.%d")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Increment build counter
    current_build = vdata.get("build_number", 0) + 1
    vdata["build_number"] = current_build
    vdata["build_date"] = today_str
    vdata["compiled_at"] = now_str
    vdata["display_version"] = f"v{vdata.get('version', '2.1.0')} (Build {today_str}-{current_build:02d})"

    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(vdata, f, indent=2, ensure_ascii=False)

    # Also sync into static directory for direct frontend loading
    static_version = os.path.join(base_dir, "static", "version.json")
    with open(static_version, "w", encoding="utf-8") as f_static:
        json.dump(vdata, f_static, indent=2, ensure_ascii=False)

    print(f"Stamping Version: {vdata['display_version']} | Compiled: {now_str}")
    return vdata

def build_single_exe():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vdata = bump_build_version(base_dir)
    temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'fti_inventory_compare_build')
    dist_dir = os.path.join(temp_dir, 'dist')
    work_dir = os.path.join(temp_dir, 'build')
    spec_dir = os.path.join(temp_dir, 'spec')

    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(spec_dir, exist_ok=True)

    print("=" * 65)
    print("   FTI IT Asset Inventory Compare - Building Single-File .EXE")
    print("=" * 65)
    print(f"Source Directory: {base_dir}")
    print(f"Build Temp Directory: {temp_dir}")

    # Terminate running instance if any, to avoid file lock on E:\FTI_Inventory_Compare.exe
    try:
        subprocess.run(["taskkill", "/F", "/IM", "FTI_Inventory_Compare.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    static_src = os.path.join(base_dir, "static")
    engine_src = os.path.join(base_dir, "engine")
    main_script = os.path.join(base_dir, "run_desktop.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "FTI_Inventory_Compare",
        "--onefile",
        "--noconsole",
        "--noconfirm",
        "--clean",
        "--specpath", spec_dir,
        "--distpath", dist_dir,
        "--workpath", work_dir,
        "--add-data", f"{static_src};static",
        "--add-data", f"{engine_src};engine",
        "--add-data", f"{os.path.join(base_dir, 'version.json')};.",
        "--hidden-import", "logger_util",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pandas",
        "--hidden-import", "jinja2",
        "--hidden-import", "python_multipart",
        "--hidden-import", "starlette",
        "--hidden-import", "engine.comparator",
        "--hidden-import", "engine.report_generator",
        main_script
    ]

    print("\nExecuting PyInstaller command...")
    print(" ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")
        return False

    built_exe = os.path.join(dist_dir, "FTI_Inventory_Compare.exe")
    if not os.path.exists(built_exe):
        print(f"\n[ERROR] Built executable not found at: {built_exe}")
        return False

    exe_size_mb = os.path.getsize(built_exe) / (1024 * 1024)
    print(f"\nBuilt executable successfully! Size: {exe_size_mb:.2f} MB")

    # Deploy executable to destinations
    destinations = [
        os.path.join(base_dir, "FTI_Inventory_Compare.exe"),
        "E:\\FTI_Inventory_Compare.exe"
    ]

    for dest in destinations:
        try:
            print(f"Deploying to: {dest}")
            shutil.copy2(built_exe, dest)
            print("  -> Deployed successfully!")
        except Exception as e:
            print(f"  -> Notice: Could not copy to {dest}: {e}")

    print("\n" + "=" * 65)
    print("   BUILD & DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print(f"   Single-File EXE: {destinations[0]}")
    if os.path.exists("E:\\FTI_Inventory_Compare.exe"):
        print(f"   Portable Copy: E:\\FTI_Inventory_Compare.exe")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = build_single_exe()
    if not success:
        sys.exit(1)
