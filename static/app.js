// FTI IT Asset Inventory Compare System - UI/UX Pro Max Engine (v2.0)
// Complete Workspace Architecture: Dynamic Spreadsheet Inspector + Manual Compare

document.addEventListener("DOMContentLoaded", () => {
    // Application State
    const state = {
        currentView: "files", // 'files', 'hw', 'sw', 'ups', 'summary'
        activeCategory: "hw",
        gridFilter: "all",
        gridSearch: "",
        gridPage: 1,
        gridPageSize: 50,
        selectedRecord: null,
        systemState: null,
        theme: localStorage.getItem("fti_theme") || "light"
    };

    // DOM Elements Cache
    const elements = {
        // Theme & App Navigation
        themeToggle: document.getElementById("btn-theme-toggle"),
        navItems: document.querySelectorAll(".nav-item"),
        viewPanels: document.querySelectorAll(".view-panel"),
        currentViewTitle: document.getElementById("current-view-title"),
        currentViewDesc: document.getElementById("current-view-desc"),

        // Nav Status Dots
        dotHw: document.getElementById("dot-nav-hw"),
        dotSw: document.getElementById("dot-nav-sw"),
        dotUps: document.getElementById("dot-nav-ups"),

        // Autosave & Tools
        autosaveStatus: document.getElementById("autosave-status"),
        autosaveText: document.getElementById("autosave-text"),
        btnUndo: document.getElementById("btn-undo"),
        btnRedo: document.getElementById("btn-redo"),
        btnHistory: document.getElementById("btn-history"),
        btnExitApp: document.getElementById("btn-exit-app"),
        btnOpenSettings: document.getElementById("btn-open-settings"),

        // File Cards & Badges
        filebadgeMaster: document.getElementById("filebadge-master"),
        filebadgeHw: document.getElementById("filebadge-hw"),
        filebadgeSw: document.getElementById("filebadge-sw"),
        filebadgeUps: document.getElementById("filebadge-ups"),
        filenameMaster: document.getElementById("filename-master"),
        filenameHw: document.getElementById("filename-hw"),
        filenameSw: document.getElementById("filename-sw"),
        filenameUps: document.getElementById("filename-ups"),
        dropzoneMaster: document.getElementById("dropzone-master"),
        dropzoneHw: document.getElementById("dropzone-hw"),
        dropzoneSw: document.getElementById("dropzone-sw"),
        dropzoneUps: document.getElementById("dropzone-ups"),
        fileInputMaster: document.getElementById("file-input-master"),
        fileInputHw: document.getElementById("file-input-hw"),
        fileInputSw: document.getElementById("file-input-sw"),
        fileInputUps: document.getElementById("file-input-ups"),

        // Workspace Controls
        btnRunCompare: document.getElementById("btn-run-compare"),
        btnRunAutoFix: document.getElementById("btn-run-autofix"),
        btnExportCategory: document.getElementById("btn-export-category"),
        workspaceStatusBadge: document.getElementById("workspace-status-badge"),
        categoryKpiBar: document.getElementById("category-kpi-bar"),
        catKpiMatchRate: document.getElementById("cat-kpi-match-rate"),
        catKpiMatched: document.getElementById("cat-kpi-matched"),
        catKpiMismatched: document.getElementById("cat-kpi-mismatched"),
        catKpiExcluded: document.getElementById("cat-kpi-excluded"),
        catKpiUserEdited: document.getElementById("cat-kpi-user-edited"),

        // Spreadsheet Grid & Toolbar
        gridFilterPills: document.querySelectorAll(".grid-filter-pill"),
        gridSearchInput: document.getElementById("grid-search-input"),
        spreadsheetTable: document.getElementById("spreadsheet-table"),
        spreadsheetThead: document.getElementById("spreadsheet-thead"),
        spreadsheetTbody: document.getElementById("spreadsheet-tbody"),
        gridPaginationInfo: document.getElementById("grid-pagination-info"),
        gridPageSize: document.getElementById("grid-page-size"),
        btnGridPrev: document.getElementById("btn-grid-prev"),
        btnGridNext: document.getElementById("btn-grid-next"),
        gridPageCurrent: document.getElementById("grid-page-current"),

        // Side Panel
        erpSidePanel: document.getElementById("erp-side-panel"),
        sidePanelBody: document.getElementById("side-panel-body"),
        btnCloseSidepanel: document.getElementById("btn-close-sidepanel"),

        // Summary View Elements
        sumRateHw: document.getElementById("sum-rate-hw"),
        sumStateHw: document.getElementById("sum-state-hw"),
        sumMatchedHw: document.getElementById("sum-matched-hw"),
        sumMismatchedHw: document.getElementById("sum-mismatched-hw"),
        sumExcludedHw: document.getElementById("sum-excluded-hw"),

        sumRateSw: document.getElementById("sum-rate-sw"),
        sumStateSw: document.getElementById("sum-state-sw"),
        sumMatchedSw: document.getElementById("sum-matched-sw"),
        sumMismatchedSw: document.getElementById("sum-mismatched-sw"),
        sumExcludedSw: document.getElementById("sum-excluded-sw"),

        sumRateUps: document.getElementById("sum-rate-ups"),
        sumStateUps: document.getElementById("sum-state-ups"),
        sumMatchedUps: document.getElementById("sum-matched-ups"),
        sumMismatchedUps: document.getElementById("sum-mismatched-ups"),
        sumExcludedUps: document.getElementById("sum-excluded-ups"),

        // Modals & Toast
        modalSettings: document.getElementById("modal-settings"),
        btnCloseSettings: document.getElementById("btn-close-settings"),
        btnDoneSettings: document.getElementById("btn-done-settings"),
        btnSettingsNewSession: document.getElementById("btn-settings-new-session"),
        btnSettingsOpenLogs: document.getElementById("btn-settings-open-logs"),

        modalLogs: document.getElementById("modal-logs"),
        btnCloseLogs: document.getElementById("btn-close-logs"),
        btnDoneLogs: document.getElementById("btn-done-logs"),
        btnRefreshLogs: document.getElementById("btn-refresh-logs"),
        logContentArea: document.getElementById("log-content-area"),
        logSearchInput: document.getElementById("log-search-input"),

        modalHistory: document.getElementById("modal-history"),
        btnCloseHistory: document.getElementById("btn-close-history"),
        btnDoneHistory: document.getElementById("btn-done-history"),
        historyTimelineList: document.getElementById("history-timeline-list"),

        toast: document.getElementById("toast"),
        toastMsg: document.getElementById("toast-msg"),
        toastIcon: document.getElementById("toast-icon")
    };

    // =========================================================================
    // Theme Management
    // =========================================================================
    function applyTheme(theme) {
        state.theme = theme;
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("fti_theme", theme);
        if (elements.themeToggle) {
            elements.themeToggle.innerHTML = theme === "dark"
                ? '<i class="fa-solid fa-sun" style="color: #f59e0b;"></i>'
                : '<i class="fa-solid fa-moon"></i>';
        }
    }
    applyTheme(state.theme);

    elements.themeToggle.addEventListener("click", () => {
        applyTheme(state.theme === "dark" ? "light" : "dark");
    });

    // =========================================================================
    // Toast Notification
    // =========================================================================
    let toastTimer = null;
    function showToast(msg, type = "success") {
        if (!elements.toast) return;
        clearTimeout(toastTimer);
        elements.toastMsg.textContent = msg;
        const card = elements.toast.querySelector(".toast-card");
        card.className = `toast-card ${type}`;

        if (type === "success") elements.toastIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
        else if (type === "error") elements.toastIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        else elements.toastIcon.innerHTML = '<i class="fa-solid fa-circle-info"></i>';

        elements.toast.style.display = "block";
        toastTimer = setTimeout(() => { elements.toast.style.display = "none"; }, 3500);
    }

    // =========================================================================
    // Navigation & View Switching
    // =========================================================================
    function switchView(viewName) {
        state.currentView = viewName;
        elements.navItems.forEach(item => {
            item.classList.toggle("active", item.getAttribute("data-view") === viewName);
        });

        elements.viewPanels.forEach(p => p.classList.remove("active"));

        if (viewName === "files") {
            document.getElementById("view-files").classList.add("active");
            elements.currentViewTitle.textContent = "ไฟล์ข้อมูลที่ใช้งาน (Data Sources)";
            elements.currentViewDesc.textContent = "ตรวจสอบไฟล์ ERP Master และไฟล์ IT Inventory";
        } else if (viewName === "summary") {
            document.getElementById("view-summary").classList.add("active");
            elements.currentViewTitle.textContent = "สรุปภาพรวมและดาวน์โหลด (Summary & Export)";
            elements.currentViewDesc.textContent = "ภาพรวมผลการเปรียบเทียบและดาวน์โหลดผลลัพธ์แยกหมวดหรือรวม ZIP";
            renderSummaryView();
        } else if (["hw", "sw", "ups"].includes(viewName)) {
            state.activeCategory = viewName;
            document.getElementById("view-category").classList.add("active");
            const names = { hw: "Hardware", sw: "Software", ups: "UPS & Monitor" };
            elements.currentViewTitle.textContent = `Workspace: ${names[viewName]}`;
            elements.currentViewDesc.textContent = `ตาราง Spreadsheet สำหรับตรวจสอบจุดต่างและแก้ไขข้อมูล ${names[viewName]} ครบทุกคอลัมน์`;
            loadCategoryWorkspace(viewName);
        }
    }

    elements.navItems.forEach(item => {
        item.addEventListener("click", () => {
            const view = item.getAttribute("data-view");
            if (view) switchView(view);
        });
    });

    document.querySelectorAll(".btn-nav-to-cat").forEach(btn => {
        btn.addEventListener("click", () => {
            const goto = btn.getAttribute("data-goto");
            if (goto) switchView(goto);
        });
    });

    // =========================================================================
    // State Synchronization
    // =========================================================================
    async function fetchSystemState() {
        try {
            const res = await fetch("/api/state");
            if (!res.ok) return;
            const data = await res.json();
            state.systemState = data;
            renderSystemState(data);
        } catch (e) {
            console.error("Fetch state error:", e);
        }
    }

    function renderSystemState(data) {
        const files = data.files || {};
        const states = data.category_states || {};

        // Update Nav status dots
        const updateDot = (el, cat) => {
            const st = states[cat] || "empty";
            el.className = `nav-status-dot state-${st}`;
        };
        updateDot(elements.dotHw, "hw");
        updateDot(elements.dotSw, "sw");
        updateDot(elements.dotUps, "ups");

        // Update File Cards
        const updateCard = (cat, badgeEl, filenameEl) => {
            const info = files[cat];
            if (!info || !info.loaded) {
                badgeEl.className = "file-badge badge-empty";
                badgeEl.textContent = "รอไฟล์";
            } else {
                const st = states[cat];
                if (st === "compared") {
                    badgeEl.className = "file-badge badge-ready";
                    badgeEl.textContent = "เปรียบเทียบแล้ว";
                } else if (st === "stale") {
                    badgeEl.className = "file-badge badge-stale";
                    badgeEl.textContent = "รอเปรียบเทียบใหม่";
                } else {
                    badgeEl.className = "file-badge badge-ready";
                    badgeEl.textContent = "พร้อมเปรียบเทียบ";
                }
                if (info.filename) filenameEl.textContent = info.filename;
            }
        };
        updateCard("master", elements.filebadgeMaster, elements.filenameMaster);
        updateCard("hw", elements.filebadgeHw, elements.filenameHw);
        updateCard("sw", elements.filebadgeSw, elements.filenameSw);
        updateCard("ups", elements.filebadgeUps, elements.filenameUps);

        // Undo/Redo tools
        elements.btnUndo.disabled = !data.can_undo;
        elements.btnRedo.disabled = !data.can_redo;

        // If in category view, update action bar
        if (["hw", "sw", "ups"].includes(state.currentView)) {
            updateWorkspaceControls(state.activeCategory);
        }
    }

    function updateWorkspaceControls(cat) {
        const st = (state.systemState && state.systemState.category_states && state.systemState.category_states[cat]) || "empty";
        const badge = elements.workspaceStatusBadge;

        elements.btnExportCategory.href = `/api/export/inventory/${cat}`;

        if (st === "compared") {
            badge.className = "status-indicator-badge text-green";
            badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> เปรียบเทียบแล้ว';
            elements.categoryKpiBar.style.display = "flex";
            elements.btnExportCategory.style.display = "inline-flex";
            elements.btnRunAutoFix.style.display = "inline-flex";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> เปรียบเทียบใหม่';
        } else if (st === "stale") {
            badge.className = "status-indicator-badge text-amber";
            badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ข้อมูลเปลี่ยน - รอเปรียบเทียบใหม่';
            elements.categoryKpiBar.style.display = "none";
            elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        } else if (st === "loaded") {
            badge.className = "status-indicator-badge text-blue";
            badge.innerHTML = '<i class="fa-solid fa-circle-info"></i> พร้อมให้กดเปรียบเทียบ';
            elements.categoryKpiBar.style.display = "none";
            elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        } else {
            badge.className = "status-indicator-badge";
            badge.innerHTML = 'ยังไม่มีไฟล์';
            elements.categoryKpiBar.style.display = "none";
            elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        }

        // Update KPI bar if compared
        if (st === "compared" && state.systemState && state.systemState.summary) {
            const catSum = (state.systemState.summary.by_category && state.systemState.summary.by_category[cat]) || {};
            elements.catKpiMatchRate.textContent = `${catSum.match_rate || 0}%`;
            elements.catKpiMatched.textContent = (catSum.matched || 0).toLocaleString();
            elements.catKpiMismatched.textContent = (catSum.mismatched || 0).toLocaleString();
            elements.catKpiExcluded.textContent = (catSum.excluded || 0).toLocaleString();
            elements.catKpiUserEdited.textContent = (catSum.user_edited || 0).toLocaleString();
        }
    }

    // =========================================================================
    // Workspace Actions: Compare & Auto-Fix
    // =========================================================================
    elements.btnRunCompare.addEventListener("click", async () => {
        const cat = state.activeCategory;
        elements.btnRunCompare.disabled = true;
        elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังเปรียบเทียบ...';

        try {
            const res = await fetch(`/api/compare/${cat}`, { method: "POST" });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "การเปรียบเทียบล้มเหลว");

            showToast(`เปรียบเทียบหมวด ${cat.toUpperCase()} สำเร็จ! (ความตรงกัน: ${data.category_summary.match_rate}%)`, "success");
            await fetchSystemState();
            await loadCategoryWorkspace(cat);
        } catch (e) {
            showToast(e.message, "error");
        } finally {
            elements.btnRunCompare.disabled = false;
        }
    });

    elements.btnRunAutoFix.addEventListener("click", async () => {
        const cat = state.activeCategory;
        elements.btnRunAutoFix.disabled = true;
        elements.btnRunAutoFix.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังซิงค์...';

        try {
            const res = await fetch(`/api/auto-fix/${cat}`, { method: "POST" });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Auto-Fix ล้มเหลว");

            const upd = data.result ? data.result.updated_count : 0;
            const excl = data.result ? data.result.excluded_count : 0;
            showToast(`Auto-Fix สำเร็จ (ปรับปรุง ${upd} รายการ, คัดแยก ${excl} รายการ)`, "success");
            await fetchSystemState();
            await loadCategoryWorkspace(cat);
        } catch (e) {
            showToast(e.message, "error");
        } finally {
            elements.btnRunAutoFix.disabled = false;
            elements.btnRunAutoFix.innerHTML = '<i class="fa-solid fa-bolt"></i> 1-Click Auto-Fix';
        }
    });

    // =========================================================================
    // Spreadsheet Grid Engine (Full Columns + In-Cell Edit)
    // =========================================================================
    async function loadCategoryWorkspace(cat) {
        updateWorkspaceControls(cat);

        const params = new URLSearchParams({
            filter_type: state.gridFilter,
            search: state.gridSearch,
            page: state.gridPage,
            page_size: state.gridPageSize
        });

        elements.spreadsheetTbody.innerHTML = `<tr><td colspan="10" style="padding: 24px; text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i> กำลังโหลดตารางข้อมูล...</td></tr>`;

        try {
            const res = await fetch(`/api/grid/${cat}?${params.toString()}`);
            if (!res.ok) throw new Error("Could not load grid");
            const data = await res.json();
            renderSpreadsheetGrid(data);
        } catch (e) {
            elements.spreadsheetTbody.innerHTML = `<tr><td colspan="10" style="padding: 24px; text-align: center; color: red;">เกิดข้อผิดพลาดในการโหลดตาราง: ${e.message}</td></tr>`;
        }
    }

    function renderSpreadsheetGrid(data) {
        const cols = data.columns || [];
        const records = data.records || [];
        const cat = data.category;

        // 1. Build Header
        let thHtml = `
            <th class="col-sticky-1" style="width: 45px; text-align: center;">#</th>
            <th class="col-sticky-2" style="width: 140px;">สถานะ</th>
        `;
        cols.forEach(col => {
            thHtml += `<th>${col}</th>`;
        });
        elements.spreadsheetThead.innerHTML = `<tr>${thHtml}</tr>`;

        // 2. Build Rows
        if (records.length === 0) {
            elements.spreadsheetTbody.innerHTML = `<tr><td colspan="${cols.length + 2}" style="padding: 28px; text-align: center; color: var(--text-muted);">ไม่พบรายการที่ตรงกับเงื่อนไข</td></tr>`;
            updatePaginationInfo(0, 0, 0, 1, 1);
            return;
        }

        const startIdx = (data.page - 1) * data.page_size;
        let tbodyHtml = "";

        records.forEach((r, idx) => {
            const rowNum = startIdx + idx + 1;
            const uid = r.uid;
            const diffs = r.diff_fields || [];
            const userEdited = r.user_edited_cols || [];
            const isExcluded = r.is_excluded;
            const isMatch = r.is_match;

            let rowClass = "";
            if (isExcluded) rowClass += " row-excluded";
            if (state.selectedRecord && state.selectedRecord.uid === uid) rowClass += " selected";

            // Status Badge
            let statusBadge = "";
            if (isExcluded) {
                statusBadge = `<span class="tag-cat tag-ups" style="font-size: 11px;"><i class="fa-solid fa-filter-circle-xmark"></i> ตัดออก</span>`;
            } else if (isMatch === true) {
                statusBadge = `<span class="tag-cat tag-hw" style="color: #059669; background: #ecfdf5; font-size: 11px;"><i class="fa-solid fa-circle-check"></i> ตรงกัน 100%</span>`;
            } else if (isMatch === false) {
                statusBadge = `<span class="tag-cat" style="color: #dc2626; background: #fef2f2; font-size: 11px;"><i class="fa-solid fa-triangle-exclamation"></i> ไม่ตรง</span>`;
            } else {
                statusBadge = `<span class="file-badge badge-empty" style="font-size: 11px;">รอเปรียบเทียบ</span>`;
            }

            let trHtml = `
                <tr class="${rowClass}" data-uid="${uid}">
                    <td class="col-sticky-1" style="text-align: center; color: var(--text-muted);">${rowNum}</td>
                    <td class="col-sticky-2">${statusBadge}</td>
            `;

            cols.forEach(col => {
                const val = r.cells[col] || "";
                let cellClass = "";

                if (col.includes("รหัสพนักงาน") && diffs.includes("emp_id")) {
                    cellClass += " cell-diff-emp";
                }
                if ((col.includes("สถานที่เก็บ") || col.includes("แผนก")) && diffs.includes("dept")) {
                    cellClass += " cell-diff-dept";
                }
                if (userEdited.includes(col)) {
                    cellClass += " cell-user-edited";
                }

                trHtml += `<td class="${cellClass}" data-col="${col}" title="ดับเบิลคลิกเพื่อแก้ไข">${val}</td>`;
            });

            trHtml += `</tr>`;
            tbodyHtml += trHtml;
        });

        elements.spreadsheetTbody.innerHTML = tbodyHtml;
        bindSpreadsheetEvents(records);
        updatePaginationInfo(startIdx + 1, Math.min(data.total, startIdx + records.length), data.total, data.page, data.total_pages);
    }

    function updatePaginationInfo(start, end, total, page, totalPages) {
        elements.gridPaginationInfo.textContent = `แสดง ${start.toLocaleString()} - ${end.toLocaleString()} จากทั้งหมด ${total.toLocaleString()} รายการ`;
        elements.gridPageCurrent.textContent = `หน้า ${page} / ${totalPages}`;
        elements.btnGridPrev.disabled = page <= 1;
        elements.btnGridNext.disabled = page >= totalPages;
    }

    // =========================================================================
    // Grid Events: Cell Double-Click Editing & Side Panel Selection
    // =========================================================================
    function bindSpreadsheetEvents(records) {
        // Row Click: Select & Show ERP Side Panel
        document.querySelectorAll("#spreadsheet-tbody tr").forEach(tr => {
            tr.addEventListener("click", () => {
                const uid = tr.getAttribute("data-uid");
                const rec = records.find(r => r.uid === uid);
                if (!rec) return;

                document.querySelectorAll("#spreadsheet-tbody tr").forEach(r => r.classList.remove("selected"));
                tr.classList.add("selected");
                state.selectedRecord = rec;
                renderSidePanel(rec);
            });
        });

        // Double Click Cell: Edit
        document.querySelectorAll("#spreadsheet-tbody td[data-col]").forEach(td => {
            td.addEventListener("dblclick", (e) => {
                e.stopPropagation();
                if (td.querySelector("input")) return; // already editing

                const col = td.getAttribute("data-col");
                const tr = td.closest("tr");
                const uid = tr.getAttribute("data-uid");
                const currentText = td.textContent;

                const input = document.createElement("input");
                input.type = "text";
                input.className = "cell-edit-input";
                input.value = currentText;

                td.innerHTML = "";
                td.appendChild(input);
                input.focus();
                input.select();

                const saveCell = async () => {
                    const newVal = input.value.trim();
                    if (newVal === currentText) {
                        td.textContent = currentText;
                        return;
                    }

                    td.textContent = newVal;
                    td.classList.add("cell-user-edited");

                    try {
                        const res = await fetch("/api/cell", {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ uid, column: col, value: newVal, user: "IT Officer" })
                        });
                        const data = await res.json();
                        if (!res.ok) throw new Error(data.detail || "Update failed");

                        showToast(`แก้ไขเซลล์ ${col} สำเร็จ`, "success");
                        await fetchSystemState();
                        // Re-render side panel if this row is selected
                        if (state.selectedRecord && state.selectedRecord.uid === uid) {
                            state.selectedRecord = data.record;
                            renderSidePanel(data.record);
                        }
                    } catch (err) {
                        showToast(`เกิดข้อผิดพลาด: ${err.message}`, "error");
                        td.textContent = currentText;
                    }
                };

                input.addEventListener("blur", saveCell);
                input.addEventListener("keydown", (ev) => {
                    if (ev.key === "Enter") {
                        input.blur();
                    } else if (ev.key === "Escape") {
                        input.removeEventListener("blur", saveCell);
                        td.textContent = currentText;
                    }
                });
            });
        });
    }

    // =========================================================================
    // Side Panel Rendering & Row Actions
    // =========================================================================
    function renderSidePanel(rec) {
        const ax = rec.ax_data || {};
        const isExcl = rec.is_excluded;

        let html = `
            <div class="side-item-group">
                <div class="side-item-label">รหัสสินทรัพย์ (Asset ID):</div>
                <div class="side-item-val" style="color: var(--blue-primary); font-family: monospace;">${ax.asset_id || "-"}</div>
            </div>
            <div class="side-item-group">
                <div class="side-item-label">สถานะในระบบ ERP (AX):</div>
                <div class="side-item-val">${ax.ax_status || (ax.asset_id ? "ปกติ" : "ไม่พบใน ERP")}</div>
            </div>
            <div class="side-item-group">
                <div class="side-item-label">ผู้ถือครองใน ERP:</div>
                <div class="side-item-val">${ax.ax_emp_name ? `${ax.ax_emp_name} (${ax.ax_emp_id || ""})` : (ax.ax_emp_id || "-")}</div>
            </div>
            <div class="side-item-group">
                <div class="side-item-label">แผนกใน ERP:</div>
                <div class="side-item-val">${ax.ax_dept || "-"}</div>
            </div>
            <div class="side-item-group">
                <div class="side-item-label">Serial Number (ERP):</div>
                <div class="side-item-val">${ax.ax_sn || "-"}</div>
            </div>

            <div class="side-actions-row">
                ${ax.asset_id && !ax.is_scrapped ? `
                    <button class="btn btn-primary btn-sm" id="btn-side-sync-erp">
                        <i class="fa-solid fa-bolt"></i> ใช้ข้อมูล ERP กับแถวนี้
                    </button>
                ` : ""}

                <button class="btn btn-secondary btn-sm" id="btn-side-toggle-excl">
                    <i class="fa-solid ${isExcl ? 'fa-arrow-rotate-left text-green' : 'fa-filter-circle-xmark text-amber'}"></i>
                    ${isExcl ? 'คืนกลับเป็นรายการใช้งาน (แท็บ 3)' : 'ย้ายไปข้อมูลที่ถูกตัดออก (แท็บ 4)'}
                </button>
            </div>
        `;

        elements.sidePanelBody.innerHTML = html;

        // Bind Side Panel Action Buttons
        const btnToggleExcl = document.getElementById("btn-side-toggle-excl");
        if (btnToggleExcl) {
            btnToggleExcl.addEventListener("click", async () => {
                try {
                    const res = await fetch("/api/row/exclusion", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid: rec.uid, exclude: !isExcl, user: "IT Officer" })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail);

                    showToast(isExcl ? "คืนกลับเป็นรายการใช้งานแล้ว" : "ย้ายไปข้อมูลที่ถูกตัดออกแล้ว", "info");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                } catch (e) {
                    showToast(e.message, "error");
                }
            });
        }

        const btnSyncErp = document.getElementById("btn-side-sync-erp");
        if (btnSyncErp) {
            btnSyncErp.addEventListener("click", async () => {
                try {
                    const cmap = { hw: ["รหัสพนักงาน", "ผู้ใช้งาน/ดูแล", "สถานที่เก็บ"], sw: ["รหัสพนักงาน", "ผู้ดูแล", "สถานที่เก็บ"], ups: ["รหัสพนักงาน", "ผู้ใช้งาน/ดูแล", "สถานที่เก็บ"] };
                    const cols = cmap[rec.category];
                    if (ax.ax_emp_id) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cols[0], value: ax.ax_emp_id }) });
                    if (ax.ax_emp_name) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cols[1], value: ax.ax_emp_name }) });
                    if (ax.ax_dept) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cols[2], value: ax.ax_dept }) });

                    showToast("ซิงค์ข้อมูลแถวนี้ให้ตรงกับ ERP แล้ว", "success");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                } catch (e) {
                    showToast(e.message, "error");
                }
            });
        }
    }

    elements.btnCloseSidepanel.addEventListener("click", () => {
        elements.sidePanelBody.innerHTML = '<p class="side-panel-empty">คลิกเลือกแถวในตารางเพื่อดูข้อมูลเปรียบเทียบกับ ERP</p>';
    });

    // =========================================================================
    // Grid Filter Pills & Search
    // =========================================================================
    elements.gridFilterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            elements.gridFilterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.gridFilter = pill.getAttribute("data-filter");
            state.gridPage = 1;
            loadCategoryWorkspace(state.activeCategory);
        });
    });

    let searchTimer = null;
    elements.gridSearchInput.addEventListener("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            state.gridSearch = e.target.value.trim();
            state.gridPage = 1;
            loadCategoryWorkspace(state.activeCategory);
        }, 300);
    });

    elements.gridPageSize.addEventListener("change", (e) => {
        state.gridPageSize = parseInt(e.target.value, 10);
        state.gridPage = 1;
        loadCategoryWorkspace(state.activeCategory);
    });

    elements.btnGridPrev.addEventListener("click", () => {
        if (state.gridPage > 1) {
            state.gridPage--;
            loadCategoryWorkspace(state.activeCategory);
        }
    });

    elements.btnGridNext.addEventListener("click", () => {
        state.gridPage++;
        loadCategoryWorkspace(state.activeCategory);
    });

    // =========================================================================
    // Summary & Download View
    // =========================================================================
    function renderSummaryView() {
        if (!state.systemState || !state.systemState.summary) return;
        const byCat = state.systemState.summary.by_category || {};
        const states = state.systemState.category_states || {};

        const updateSum = (cat, rateEl, stateEl, matchedEl, mismEl, exclEl) => {
            const c = byCat[cat] || {};
            const st = states[cat] || "empty";
            rateEl.textContent = `${c.match_rate || 0}%`;
            stateEl.textContent = st === "compared" ? "เปรียบเทียบแล้ว" : (st === "stale" ? "รอเปรียบเทียบใหม่" : "พร้อมเปรียบเทียบ");
            matchedEl.textContent = (c.matched || 0).toLocaleString();
            mismEl.textContent = (c.mismatched || 0).toLocaleString();
            exclEl.textContent = (c.excluded || 0).toLocaleString();
        };

        updateSum("hw", elements.sumRateHw, elements.sumStateHw, elements.sumMatchedHw, elements.sumMismatchedHw, elements.sumExcludedHw);
        updateSum("sw", elements.sumRateSw, elements.sumStateSw, elements.sumMatchedSw, elements.sumMismatchedSw, elements.sumExcludedSw);
        updateSum("ups", elements.sumRateUps, elements.sumStateUps, elements.sumMatchedUps, elements.sumMismatchedUps, elements.sumExcludedUps);
    }

    // =========================================================================
    // Drag-and-Drop & File Upload
    // =========================================================================
    function setupDropzone(dropzoneEl, inputEl, fileType) {
        if (!dropzoneEl || !inputEl) return;

        dropzoneEl.addEventListener("click", (e) => {
            if (e.target !== inputEl) inputEl.click();
        });

        inputEl.addEventListener("change", () => {
            if (inputEl.files.length > 0) uploadSelectedFile(fileType, inputEl.files[0]);
        });

        ["dragenter", "dragover"].forEach(evt => {
            dropzoneEl.addEventListener(evt, (e) => {
                e.preventDefault(); e.stopPropagation();
                dropzoneEl.classList.add("drag-over");
            });
        });

        ["dragleave", "drop"].forEach(evt => {
            dropzoneEl.addEventListener(evt, (e) => {
                e.preventDefault(); e.stopPropagation();
                dropzoneEl.classList.remove("drag-over");
            });
        });

        dropzoneEl.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                uploadSelectedFile(fileType, dt.files[0]);
            }
        });
    }

    async function uploadSelectedFile(fileType, file) {
        if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
            showToast("รองรับเฉพาะไฟล์ Excel (.xlsx หรือ .xls) เท่านั้น", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file_type", fileType);
        formData.append("file", file);

        showToast(`กำลังอัปโหลดไฟล์ ${file.name}...`, "info");
        try {
            const res = await fetch("/api/upload", { method: "POST", body: formData });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);

            showToast(data.message, "success");
            await fetchSystemState();
        } catch (e) {
            showToast(`อัปโหลดล้มเหลว: ${e.message}`, "error");
        }
    }

    setupDropzone(elements.dropzoneMaster, elements.fileInputMaster, "master");
    setupDropzone(elements.dropzoneHw, elements.fileInputHw, "hw");
    setupDropzone(elements.dropzoneSw, elements.fileInputSw, "sw");
    setupDropzone(elements.dropzoneUps, elements.fileInputUps, "ups");

    // =========================================================================
    // Undo / Redo & Version History
    // =========================================================================
    async function triggerUndo() {
        if (elements.btnUndo.disabled) return;
        try {
            const res = await fetch("/api/undo", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, "info");
                await fetchSystemState();
                if (["hw", "sw", "ups"].includes(state.currentView)) {
                    await loadCategoryWorkspace(state.activeCategory);
                }
            }
        } catch (e) {
            showToast("เกิดข้อผิดพลาดในการเลิกทำ", "error");
        }
    }

    async function triggerRedo() {
        if (elements.btnRedo.disabled) return;
        try {
            const res = await fetch("/api/redo", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                showToast(data.message, "info");
                await fetchSystemState();
                if (["hw", "sw", "ups"].includes(state.currentView)) {
                    await loadCategoryWorkspace(state.activeCategory);
                }
            }
        } catch (e) {
            showToast("เกิดข้อผิดพลาดในการทำซ้ำ", "error");
        }
    }

    elements.btnUndo.addEventListener("click", triggerUndo);
    elements.btnRedo.addEventListener("click", triggerRedo);

    // Keyboard Shortcuts (Ctrl+Z / Ctrl+Y)
    document.addEventListener("keydown", (e) => {
        if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z") {
            e.preventDefault(); triggerUndo();
        }
        if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))) {
            e.preventDefault(); triggerRedo();
        }
    });

    // Version History Modal
    elements.btnHistory.addEventListener("click", async () => {
        elements.modalHistory.style.display = "flex";
        try {
            const res = await fetch("/api/history");
            const data = await res.json();
            const list = data.history || [];
            if (list.length === 0) {
                elements.historyTimelineList.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 20px;">ยังไม่มีประวัติการแก้ไขในเซสชันนี้</p>`;
                return;
            }

            let html = "";
            list.forEach(item => {
                html += `
                    <div class="timeline-card">
                        <div class="timeline-info">
                            <div><strong>${item.description}</strong></div>
                            <div class="timeline-time"><i class="fa-regular fa-clock"></i> ${item.timestamp} · ${item.user}</div>
                        </div>
                        <button class="btn btn-secondary btn-sm btn-rollback" data-idx="${item.index}">ย้อนกลับจุดนี้</button>
                    </div>
                `;
            });
            elements.historyTimelineList.innerHTML = html;

            document.querySelectorAll(".btn-rollback").forEach(b => {
                b.addEventListener("click", async () => {
                    const idx = parseInt(b.getAttribute("data-idx"), 10);
                    if (confirm("ต้องการย้อนกลับสถานะไปยังเวอร์ชันนี้หรือไม่?")) {
                        await fetch("/api/rollback", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ index: idx }) });
                        elements.modalHistory.style.display = "none";
                        await fetchSystemState();
                        if (["hw", "sw", "ups"].includes(state.currentView)) {
                            await loadCategoryWorkspace(state.activeCategory);
                        }
                    }
                });
            });
        } catch (e) {
            elements.historyTimelineList.innerHTML = `<p style="color: red;">โหลดประวัติล้มเหลว</p>`;
        }
    });

    elements.btnCloseHistory.addEventListener("click", () => { elements.modalHistory.style.display = "none"; });
    elements.btnDoneHistory.addEventListener("click", () => { elements.modalHistory.style.display = "none"; });

    // Settings Modal
    elements.btnOpenSettings.addEventListener("click", () => { elements.modalSettings.style.display = "flex"; });
    elements.btnCloseSettings.addEventListener("click", () => { elements.modalSettings.style.display = "none"; });
    elements.btnDoneSettings.addEventListener("click", () => { elements.modalSettings.style.display = "none"; });

    elements.btnSettingsNewSession.addEventListener("click", async () => {
        if (confirm("ต้องการเริ่มเซสชันใหม่หรือไม่? การกระทำนี้จะล้างข้อมูลและประวัติที่บันทึกไว้")) {
            await fetch("/api/session/reset", { method: "POST" });
            elements.modalSettings.style.display = "none";
            showToast("เริ่มเซสชันใหม่เรียบร้อย", "success");
            await fetchSystemState();
            switchView("files");
        }
    });

    elements.btnSettingsOpenLogs.addEventListener("click", () => {
        elements.modalSettings.style.display = "none";
        elements.modalLogs.style.display = "flex";
        fetchLogs();
    });

    // Logs Modal
    async function fetchLogs() {
        try {
            const res = await fetch("/api/logs?lines=200");
            const data = await res.json();
            elements.logContentArea.textContent = (data.lines || []).join("\n") || "ไม่มีข้อความ Log";
            elements.logContentArea.scrollTop = elements.logContentArea.scrollHeight;
        } catch (e) {
            elements.logContentArea.textContent = "โหลด Log ล้มเหลว";
        }
    }

    elements.btnRefreshLogs.addEventListener("click", fetchLogs);
    elements.btnCloseLogs.addEventListener("click", () => { elements.modalLogs.style.display = "none"; });
    elements.btnDoneLogs.addEventListener("click", () => { elements.modalLogs.style.display = "none"; });

    // Exit Application
    elements.btnExitApp.addEventListener("click", async () => {
        if (confirm("คุณต้องการปิดและออกจากโปรแกรมหรือไม่?")) {
            try { await fetch("/api/shutdown?force=true", { method: "POST" }); } catch (e) {}
            showToast("กำลังปิดโปรแกรม...", "info");
            setTimeout(() => { window.close(); }, 400);
        }
    });

    // Heartbeat & Unload
    setInterval(() => { fetch("/api/heartbeat").catch(() => {}); }, 3000);
    window.addEventListener("beforeunload", () => {
        if (navigator.sendBeacon) navigator.sendBeacon("/api/client_unloading");
    });

    // Initial Load
    fetchSystemState();
});
