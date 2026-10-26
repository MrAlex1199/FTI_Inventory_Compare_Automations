// FTI IT Asset Inventory Compare System - UI/UX Pro Max Frontend Engine

document.addEventListener("DOMContentLoaded", () => {
    // Application State
    const state = {
        category: "all",
        filterType: "all",
        mismatchOnly: true,
        searchQuery: "",
        page: 1,
        pageSize: 25,
        totalPages: 1,
        totalRecords: 0,
        currentRecord: null,
        summary: null,
        theme: localStorage.getItem("fti_theme") || "light"
    };

    // DOM Elements Cache
    const elements = {
        // Theme
        themeToggle: document.getElementById("btn-theme-toggle"),

        // Summary & Score
        kpiMatchPercent: document.getElementById("kpi-match-percent"),
        scoreBarFill: document.getElementById("score-bar-fill"),
        kpiMatchedCount: document.getElementById("kpi-matched-count"),
        kpiTotalRecords: document.getElementById("kpi-total-records"),
        kpiMatchedRecords: document.getElementById("kpi-matched-records"),
        kpiMismatchedRecords: document.getElementById("kpi-mismatched-records"),
        kpiScrappedRecords: document.getElementById("kpi-scrapped-records"),

        // Breakdown bars
        hwMatchPercent: document.getElementById("hw-match-percent"),
        hwProgressFill: document.getElementById("hw-progress-fill"),
        hwMatchedVal: document.getElementById("hw-matched-val"),
        hwMismatchedVal: document.getElementById("hw-mismatched-val"),

        swMatchPercent: document.getElementById("sw-match-percent"),
        swProgressFill: document.getElementById("sw-progress-fill"),
        swMatchedVal: document.getElementById("sw-matched-val"),
        swMismatchedVal: document.getElementById("sw-mismatched-val"),

        upsMatchPercent: document.getElementById("ups-match-percent"),
        upsProgressFill: document.getElementById("ups-progress-fill"),
        upsMatchedVal: document.getElementById("ups-matched-val"),
        upsMismatchedVal: document.getElementById("ups-mismatched-val"),

        // Tab counts
        tabCntAll: document.getElementById("tab-cnt-all"),
        tabCntHw: document.getElementById("tab-cnt-hw"),
        tabCntSw: document.getElementById("tab-cnt-sw"),
        tabCntUps: document.getElementById("tab-cnt-ups"),

        // Table & Search
        tableBody: document.getElementById("table-body"),
        searchInput: document.getElementById("search-input"),
        btnClearSearch: document.getElementById("btn-clear-search"),
        chkMismatchOnly: document.getElementById("chk-mismatch-only"),
        catTabs: document.querySelectorAll(".cat-tab"),
        filterPills: document.querySelectorAll(".filter-pill"),

        // Pagination
        pageStart: document.getElementById("page-start"),
        pageEnd: document.getElementById("page-end"),
        totalCount: document.getElementById("total-count"),
        pageCurrent: document.getElementById("page-current"),
        btnPrevPage: document.getElementById("btn-prev-page"),
        btnNextPage: document.getElementById("btn-next-page"),
        selectPageSize: document.getElementById("select-page-size"),

        // Actions
        btnBatchQuickFix: document.getElementById("btn-batch-quick-fix"),
        btnCardBatchTrigger: document.getElementById("btn-card-batch-trigger"),
        btnRecompare: document.getElementById("btn-recompare"),
        btnExportDropdown: document.getElementById("btn-export-dropdown"),
        dropdownWrapper: document.querySelector(".dropdown"),

        // Dropzones
        dropzoneMaster: document.getElementById("dropzone-master"),
        dropzoneHw: document.getElementById("dropzone-hw"),
        dropzoneSw: document.getElementById("dropzone-sw"),
        dropzoneUps: document.getElementById("dropzone-ups"),

        fileInputMaster: document.getElementById("file-input-master"),
        fileInputHw: document.getElementById("file-input-hw"),
        fileInputSw: document.getElementById("file-input-sw"),
        fileInputUps: document.getElementById("file-input-ups"),

        // Modal Edit
        modalEdit: document.getElementById("modal-edit"),
        btnCloseEdit: document.getElementById("btn-close-edit"),
        btnCancelEdit: document.getElementById("btn-cancel-edit"),
        btnSaveEdit: document.getElementById("btn-save-edit"),
        btnCopyAx: document.getElementById("btn-copy-ax"),
        editUid: document.getElementById("edit-uid"),
        editAssetIdDisplay: document.getElementById("edit-asset-id-display"),
        editTypeDisplay: document.getElementById("edit-type-display"),
        editMismatchText: document.getElementById("edit-mismatch-text"),
        refAxName: document.getElementById("ref-ax-name"),
        refAxEmp: document.getElementById("ref-ax-emp"),
        refAxDept: document.getElementById("ref-ax-dept"),
        refAxStatus: document.getElementById("ref-ax-status"),
        editItEmpId: document.getElementById("edit-it-emp-id"),
        editItEmpName: document.getElementById("edit-it-emp-name"),
        editItDept: document.getElementById("edit-it-dept"),
        editItSn: document.getElementById("edit-it-sn"),
        editItAssetId: document.getElementById("edit-it-asset-id"),

        // Toast
        toast: document.getElementById("toast"),
        toastMsg: document.getElementById("toast-msg"),
        toastIcon: document.getElementById("toast-icon"),

        // Log Modal Elements
        btnViewLogs: document.getElementById("btn-view-logs"),
        modalLogs: document.getElementById("modal-logs"),
        btnCloseLogs: document.getElementById("btn-close-logs"),
        btnDoneLogs: document.getElementById("btn-done-logs"),
        btnRefreshLogs: document.getElementById("btn-refresh-logs"),
        btnCopyLogs: document.getElementById("btn-copy-logs"),
        logContentArea: document.getElementById("log-content-area"),
        logFilePath: document.getElementById("log-file-path"),

        // Google Workspace-style MVP Tools
        btnUndo: document.getElementById("btn-undo"),
        btnRedo: document.getElementById("btn-redo"),
        btnHistory: document.getElementById("btn-history"),
        btnNewSession: document.getElementById("btn-new-session"),
        btnExitApp: document.getElementById("btn-exit-app"),
        autosaveStatus: document.getElementById("autosave-status"),
        autosaveText: document.getElementById("autosave-text"),
        modalHistory: document.getElementById("modal-history"),
        btnCloseHistory: document.getElementById("btn-close-history"),
        btnDoneHistory: document.getElementById("btn-done-history"),
        historyTimelineList: document.getElementById("history-timeline-list")
    };

    // =========================================================================
    // Theme Management (Light / Dark Mode)
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

    if (elements.themeToggle) {
        elements.themeToggle.addEventListener("click", () => {
            const nextTheme = state.theme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
            showToast(`สลับเป็น ${nextTheme === "dark" ? "Dark Mode" : "Light Mode"} เรียบร้อย`, "info");
        });
    }

    // =========================================================================
    // Toast Notification Utility
    // =========================================================================
    let toastTimeout = null;
    function showToast(msg, type = "success") {
        if (!elements.toast) return;
        clearTimeout(toastTimeout);

        elements.toastMsg.textContent = msg;
        const card = elements.toast.querySelector(".toast-card");
        card.className = `toast-card ${type}`;

        if (type === "success") {
            elements.toastIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
        } else if (type === "error") {
            elements.toastIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        } else if (type === "warning") {
            elements.toastIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
        } else {
            elements.toastIcon.innerHTML = '<i class="fa-solid fa-circle-info"></i>';
        }

        elements.toast.style.display = "block";
        toastTimeout = setTimeout(() => {
            elements.toast.style.display = "none";
        }, 3500);
    }

    // =========================================================================
    // Data Loading & API Calls
    // =========================================================================
    async function loadFilesStatus() {
        try {
            const res = await fetch("/api/files-status");
            if (!res.ok) return;
            const data = await res.json();

            const updateCard = (key, elName, elMeta, elBadge) => {
                const info = data[key];
                if (!info) return;
                const nameEl = document.getElementById(elName);
                const metaEl = document.getElementById(elMeta);
                const badgeEl = document.getElementById(elBadge);

                if (info.loaded && info.rows > 0) {
                    if (nameEl) nameEl.textContent = info.filename || "ไฟล์ที่เลือก";
                    if (metaEl) metaEl.textContent = `พบข้อมูลพร้อมใช้งาน: ${info.rows.toLocaleString()} รายการ`;
                    if (badgeEl) {
                        badgeEl.className = "file-status ready";
                        badgeEl.innerHTML = '<i class="fa-solid fa-circle-check"></i> พร้อมใช้งาน';
                    }
                } else {
                    if (metaEl) metaEl.textContent = "ยังไม่ได้ระบุไฟล์ (ลากไฟล์มาวางที่นี่ได้)";
                    if (badgeEl) {
                        badgeEl.className = "file-status empty";
                        badgeEl.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> รอไฟล์';
                    }
                }
            };

            updateCard("master", "filename-master", "filemeta-master", "status-badge-master");
            updateCard("hw", "filename-hw", "filemeta-hw", "status-badge-hw");
            updateCard("sw", "filename-sw", "filemeta-sw", "status-badge-sw");
            updateCard("ups", "filename-ups", "filemeta-ups", "status-badge-ups");
        } catch (e) {
            console.error("Load files status error:", e);
        }
    }

    async function loadSummary() {
        try {
            const res = await fetch("/api/summary");
            if (!res.ok) throw new Error("Could not fetch summary data");
            const data = await res.json();
            state.summary = data;

            const ov = data.overall || {};
            const rate = ov.match_rate || 0;
            const matched = ov.matched_records || 0;
            const total = ov.total_records || 0;
            const mismatched = ov.mismatched_records || 0;

            // Overall KPI
            elements.kpiMatchPercent.textContent = `${rate}%`;
            elements.scoreBarFill.style.width = `${Math.min(100, rate)}%`;
            elements.kpiMatchedCount.textContent = matched.toLocaleString();
            elements.kpiTotalRecords.textContent = total.toLocaleString();

            // Dynamic color for score
            if (rate >= 70) {
                elements.kpiMatchPercent.style.color = "var(--green-success)";
            } else if (rate >= 40) {
                elements.kpiMatchPercent.style.color = "var(--amber-warn)";
            } else {
                elements.kpiMatchPercent.style.color = "var(--blue-primary)";
            }

            elements.kpiMatchedRecords.textContent = matched.toLocaleString();
            elements.kpiMismatchedRecords.textContent = mismatched.toLocaleString();

            const scrapped = (data.mismatch_breakdown && data.mismatch_breakdown["ตัดจำหน่ายใน ERP แต่ IT ยังมีใช้งาน"]) || 0;
            elements.kpiScrappedRecords.textContent = scrapped.toLocaleString();

            // Categories
            const byCat = data.by_category || {};
            const updateCat = (catKey, elPct, elFill, elMatch, elMismatch, elTabCnt) => {
                const c = byCat[catKey] || { match_rate: 0, matched: 0, mismatched: 0, total: 0 };
                if (elPct) elPct.textContent = `${c.match_rate}%`;
                if (elFill) elFill.style.width = `${Math.min(100, c.match_rate)}%`;
                if (elMatch) elMatch.textContent = (c.matched || 0).toLocaleString();
                if (elMismatch) elMismatch.textContent = (c.mismatched || 0).toLocaleString();
                if (elTabCnt) elTabCnt.textContent = (c.total || 0).toLocaleString();
            };

            updateCat("hw", elements.kpiHwPct, elements.fillHw, elements.kpiHwMatched, elements.kpiHwMismatched, elements.tabCountHw);
            updateCat("sw", elements.kpiSwPct, elements.fillSw, elements.kpiSwMatched, elements.kpiSwMismatched, elements.tabCountSw);
            updateCat("ups", elements.kpiUpsPct, elements.fillUps, elements.kpiUpsMatched, elements.kpiUpsMismatched, elements.tabCountUps);

            await updateSessionStatus();

            updateCat("hw", elements.hwMatchPercent, elements.hwProgressFill, elements.hwMatchedVal, elements.hwMismatchedVal, elements.tabCntHw);
            updateCat("sw", elements.swMatchPercent, elements.swProgressFill, elements.swMatchedVal, elements.swMismatchedVal, elements.tabCntSw);
            updateCat("ups", elements.upsMatchPercent, elements.upsProgressFill, elements.upsMatchedVal, elements.upsMismatchedVal, elements.tabCntUps);

            if (elements.tabCntAll) elements.tabCntAll.textContent = total.toLocaleString();

            // Update files status row count
            await loadFilesStatus();
        } catch (err) {
            console.error("Load summary error:", err);
            showToast("ไม่สามารถโหลดสรุปข้อมูลได้", "error");
        }
    }

    async function loadRecords() {
        elements.tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-cell">
                    <i class="fa-solid fa-spinner fa-spin"></i> กำลังโหลดรายการ...
                </td>
            </tr>
        `;

        try {
            const params = new URLSearchParams({
                category: state.category,
                mismatch_only: state.mismatchOnly,
                filter_type: state.filterType,
                search: state.searchQuery,
                page: state.page,
                page_size: state.pageSize
            });

            const res = await fetch(`/api/records?${params.toString()}`);
            if (!res.ok) throw new Error("Could not fetch records");
            const data = await res.json();

            state.totalRecords = Number(data.total ?? data.total_count ?? 0);
            state.totalPages = Number(data.total_pages ?? Math.max(1, Math.ceil(state.totalRecords / state.pageSize)));

            renderTable(data.records || []);
            renderPagination();
        } catch (err) {
            console.error("Load records error:", err);
            elements.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="loading-cell text-red">
                        <i class="fa-solid fa-circle-exclamation"></i> เกิดข้อผิดพลาดในการโหลดข้อมูล
                    </td>
                </tr>
            `;
        }
    }

    // =========================================================================
    // Table Rendering
    // =========================================================================
    function getMismatchBadge(type) {
        if (!type || type === "ตรงกันสมบูรณ์") {
            return `<span class="badge-mismatch mismatch-match"><i class="fa-solid fa-circle-check"></i> ตรงกัน</span>`;
        }
        if (type.includes("รหัสพนักงาน + แผนก")) {
            return `<span class="badge-mismatch mismatch-both"><i class="fa-solid fa-triangle-exclamation"></i> ต่างพนักงาน+แผนก</span>`;
        }
        if (type.includes("รหัสพนักงาน")) {
            return `<span class="badge-mismatch mismatch-emp"><i class="fa-solid fa-user-xmark"></i> พนักงานไม่ตรง</span>`;
        }
        if (type.includes("แผนก")) {
            return `<span class="badge-mismatch mismatch-dept"><i class="fa-solid fa-building-circle-xmark"></i> แผนกไม่ตรง</span>`;
        }
        if (type.includes("ตัดจำหน่าย")) {
            return `<span class="badge-mismatch mismatch-scrapped"><i class="fa-solid fa-ban"></i> ตัดจำหน่ายใน ERP</span>`;
        }
        if (type.includes("ไม่พบ")) {
            return `<span class="badge-mismatch mismatch-missing"><i class="fa-solid fa-circle-question"></i> ไม่พบใน ERP</span>`;
        }
        return `<span class="badge-mismatch mismatch-both">${type}</span>`;
    }

    function renderTable(records) {
        if (records.length === 0) {
            elements.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="loading-cell">
                        <i class="fa-solid fa-magnifying-glass"></i> ไม่พบรายการที่ตรงกับเงื่อนไข
                    </td>
                </tr>
            `;
            return;
        }

        const startIdx = (state.page - 1) * state.pageSize;
        let html = "";

        records.forEach((r, idx) => {
            const rowNum = startIdx + idx + 1;
            const cat = r.category || "hw";
            const ax = r.ax_data || {};
            const diffs = r.diff_fields || [];

            // Highlight differences
            const empDiff = diffs.includes("emp_id") || diffs.includes("both");
            const deptDiff = diffs.includes("dept") || diffs.includes("both");

            const itEmpHtml = empDiff
                ? `<mark class="diff-highlight">${r.it_emp_name || r.it_emp_id || "-"}</mark>`
                : (r.it_emp_name || r.it_emp_id || "-");

            const itDeptHtml = deptDiff
                ? `<mark class="diff-highlight">${r.it_dept || "-"}</mark>`
                : (r.it_dept || "-");

            const axEmpHtml = empDiff
                ? `<mark class="diff-highlight">${ax.ax_emp_name || ax.ax_emp_id || "-"}</mark>`
                : (ax.ax_emp_name || ax.ax_emp_id || "-");

            const axDeptHtml = deptDiff
                ? `<mark class="diff-highlight">${ax.ax_dept || "-"}</mark>`
                : (ax.ax_dept || "-");

            const hasAxSync = ax.ax_emp_id || ax.ax_dept;
            const canQuickFix = Boolean(hasAxSync && !r.is_match && !ax.is_scrapped && ax.asset_id);

            html += `
                <tr data-uid="${r.uid}">
                    <td style="color: var(--text-muted); font-size: 11px;">${rowNum}</td>
                    <td><span class="badge-cat badge-cat-${cat}">${cat.toUpperCase()}</span></td>
                    <td style="font-weight: 600; font-family: monospace; color: var(--blue-primary);">${r.asset_id || "-"}</td>
                    <td>${getMismatchBadge(r.mismatch_type)}</td>
                    <td>
                        <div class="info-cell-block">
                            <div class="info-line"><span class="info-label">ผู้ใช้:</span><span class="info-val">${itEmpHtml}</span></div>
                            <div class="info-line"><span class="info-label">แผนก:</span><span class="info-val">${itDeptHtml}</span></div>
                            <div class="info-line"><span class="info-label">S/N:</span><span class="info-val" style="color: var(--text-muted); font-size: 11px;">${r.it_sn || "-"}</span></div>
                        </div>
                    </td>
                    <td>
                        <div class="info-cell-block">
                            <div class="info-line"><span class="info-label">ERP:</span><span class="info-val">${axEmpHtml}</span></div>
                            <div class="info-line"><span class="info-label">แผนก:</span><span class="info-val">${axDeptHtml}</span></div>
                            <div class="info-line"><span class="info-label">สถานะ:</span><span class="info-val" style="color: var(--text-muted); font-size: 11px;">${ax.ax_status || (ax.asset_id ? "ปกติ" : "ไม่พบใน ERP")}</span></div>
                        </div>
                    </td>
                    <td>
                        <div class="cell-actions">
                            ${canQuickFix ? `
                                <button class="btn-table-action btn-quick-fix" data-uid="${r.uid}" title="อัปเดตข้อมูลพนักงานและแผนกให้ตรงกับ ERP ทันที">
                                    <i class="fa-solid fa-bolt"></i> ตรง ERP
                                </button>
                            ` : ""}
                            <button class="btn-table-action btn-edit-manual" data-uid="${r.uid}" title="เปิดหน้าต่างแก้ไขข้อมูล">
                                <i class="fa-solid fa-pen"></i> แก้ไข
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        elements.tableBody.innerHTML = html;
        bindTableEvents(records);
    }

    function renderPagination() {
        const total = state.totalRecords;
        const start = total === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
        const end = Math.min(total, state.page * state.pageSize);

        if (elements.pageStart) elements.pageStart.textContent = start.toLocaleString();
        if (elements.pageEnd) elements.pageEnd.textContent = end.toLocaleString();
        if (elements.totalCount) elements.totalCount.textContent = total.toLocaleString();
        if (elements.pageCurrent) elements.pageCurrent.textContent = `หน้า ${state.page} / ${state.totalPages}`;

        if (elements.btnPrevPage) elements.btnPrevPage.disabled = state.page <= 1;
        if (elements.btnNextPage) elements.btnNextPage.disabled = state.page >= state.totalPages;
    }

    // =========================================================================
    // Table Action Handlers
    // =========================================================================
    function bindTableEvents(records) {
        // 1-Click Quick-Fix
        document.querySelectorAll(".btn-quick-fix").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const uid = btn.getAttribute("data-uid");
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

                try {
                    const res = await fetch("/api/quick-fix", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid, user: "IT Officer" })
                    });
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) {
                        throw new Error(data.detail || "การเชื่อมต่อกับระบบ Quick-Fix ขัดข้อง");
                    }
                    if (data.status === "warning") {
                        showToast(data.message || "รายการนี้ไม่สามารถซิงค์อัตโนมัติได้", "warning");
                    } else if (data.status === "info") {
                        showToast(data.message || "ข้อมูลตรงกันอยู่แล้ว ไม่มีการเปลี่ยนแปลง", "info");
                    } else {
                        showToast(data.message || "อัปเดตข้อมูลสำเร็จ", "success");
                        await loadSummary();
                        await loadRecords();
                    }
                } catch (err) {
                    console.error("Quick-fix error:", err);
                    showToast(err.message || "เกิดข้อผิดพลาดในการอัปเดตข้อมูล", "error");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-bolt"></i> ตรง ERP';
                }
            });
        });

        // Edit Modal Trigger
        document.querySelectorAll(".btn-edit-manual").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const uid = btn.getAttribute("data-uid");
                const rec = records.find(r => r.uid === uid);
                if (rec) openEditModal(rec);
            });
        });
    }

    // =========================================================================
    // Modal Edit Operations
    // =========================================================================
    function openEditModal(rec) {
        state.currentRecord = rec;
        const ax = rec.ax_data || {};

        elements.editUid.value = rec.uid;
        elements.editAssetIdDisplay.textContent = rec.asset_id || "-";
        elements.editTypeDisplay.textContent = (rec.category || "HW").toUpperCase();
        elements.editMismatchText.textContent = rec.mismatch_type || "-";

        elements.refAxName.textContent = ax.ax_asset_name || "-";
        elements.refAxEmp.textContent = ax.ax_emp_name ? `${ax.ax_emp_name} (${ax.ax_emp_id || ""})` : (ax.ax_emp_id || "-");
        elements.refAxDept.textContent = ax.ax_dept || "-";
        elements.refAxStatus.textContent = ax.ax_status || (ax.asset_id ? "ปกติ" : "ไม่พบใน ERP");

        elements.editItEmpId.value = rec.it_emp_id || "";
        elements.editItEmpName.value = rec.it_emp_name || "";
        elements.editItDept.value = rec.it_dept || "";
        elements.editItSn.value = rec.it_sn || "";
        elements.editItAssetId.value = rec.asset_id || "";

        elements.modalEdit.style.display = "flex";
    }

    function closeEditModal() {
        elements.modalEdit.style.display = "none";
        state.currentRecord = null;
    }

    elements.btnCopyAx.addEventListener("click", () => {
        if (!state.currentRecord || !state.currentRecord.ax_data) return;
        const ax = state.currentRecord.ax_data;
        if (ax.ax_emp_id) elements.editItEmpId.value = ax.ax_emp_id;
        if (ax.ax_emp_name) elements.editItEmpName.value = ax.ax_emp_name;
        if (ax.ax_dept) elements.editItDept.value = ax.ax_dept;
        showToast("คัดลอกข้อมูล ERP ลงฟอร์มเรียบร้อยแล้ว", "info");
    });

    elements.btnSaveEdit.addEventListener("click", async () => {
        const uid = elements.editUid.value;
        if (!uid) return;

        elements.btnSaveEdit.disabled = true;
        elements.btnSaveEdit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังบันทึก...';

        try {
            const payload = {
                uid: uid,
                it_emp_id: elements.editItEmpId.value,
                it_emp_name: elements.editItEmpName.value,
                it_dept: elements.editItDept.value,
                it_sn: elements.editItSn.value,
                asset_id: elements.editItAssetId.value,
                user: "IT Officer"
            };

            const res = await fetch("/api/correct", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Correction request failed");
            showToast(`บันทึกข้อมูล ${elements.editAssetIdDisplay.textContent} สำเร็จ`, "success");
            closeEditModal();
            await loadSummary();
            await loadRecords();
        } catch (err) {
            console.error("Save edit error:", err);
            showToast("เกิดข้อผิดพลาดในการบันทึกข้อมูล", "error");
        } finally {
            elements.btnSaveEdit.disabled = false;
            elements.btnSaveEdit.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> บันทึกข้อมูลและคำนวณใหม่';
        }
    });

    // =========================================================================
    // Batch Auto-Fix Handlers
    // =========================================================================
    async function triggerBatchAutoFix() {
        const btn = elements.btnCardBatchTrigger || elements.btnBatchQuickFix;
        const originalHtml = btn ? btn.innerHTML : "";
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังประมวลผล Auto-Fix...';
        }

        try {
            const res = await fetch("/api/batch-quick-fix", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ category: state.category, user: "IT Officer" })
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.detail || "การเชื่อมต่อกับระบบ Auto-Fix ขัดข้อง");
            }

            const count = data.result ? data.result.updated_count : 0;
            const newRate = data.result ? data.result.new_match_rate : 0;

            if (count > 0) {
                showToast(`อัปเดตข้อมูลตรง ERP สำเร็จ ${count.toLocaleString()} รายการ (ความตรงกัน: ${newRate}%)`, "success");
            } else {
                showToast(data.message || "ข้อมูลทั้งหมดตรงกับ ERP อยู่แล้ว หรือไม่พบข้อมูล ERP ที่จะซิงค์", "info");
            }
            await loadSummary();
            await loadRecords();
        } catch (err) {
            console.error("Batch fix error:", err);
            showToast(err.message || "เกิดข้อผิดพลาดในการประมวลผล Auto-Fix", "error");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        }
    }

    if (elements.btnBatchQuickFix) {
        elements.btnBatchQuickFix.addEventListener("click", triggerBatchAutoFix);
    }
    if (elements.btnCardBatchTrigger) {
        elements.btnCardBatchTrigger.addEventListener("click", triggerBatchAutoFix);
    }

    // Re-compare Action (if present)
    if (elements.btnRecompare) {
        elements.btnRecompare.addEventListener("click", async () => {
            const icon = elements.btnRecompare.querySelector("i");
            if (icon) icon.classList.add("fa-spin");
            elements.btnRecompare.disabled = true;

            try {
                const res = await fetch("/api/recompare", { method: "POST" });
                if (!res.ok) throw new Error("Recompare failed");
                await loadSummary();
                await loadRecords();
                showToast("ประมวลผลเปรียบเทียบใหม่เรียบร้อยแล้ว!", "success");
            } catch (err) {
                console.error("Recompare error:", err);
                showToast("เกิดข้อผิดพลาดในการคำนวณใหม่", "error");
            } finally {
                if (icon) icon.classList.remove("fa-spin");
                elements.btnRecompare.disabled = false;
            }
        });
    }

    // Export Dropdown
    elements.btnExportDropdown.addEventListener("click", (e) => {
        e.stopPropagation();
        elements.dropdownWrapper.classList.toggle("open");
    });

    document.addEventListener("click", () => {
        elements.dropdownWrapper.classList.remove("open");
    });

    // Category Tabs
    elements.catTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            elements.catTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            state.category = tab.getAttribute("data-category");
            state.page = 1;
            loadRecords();
        });
    });

    // Secondary Filter Pills
    elements.filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            elements.filterPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            state.filterType = pill.getAttribute("data-filter");
            state.page = 1;
            loadRecords();
        });
    });

    // Search Box with Debounce
    let searchTimer = null;
    elements.searchInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        elements.btnClearSearch.style.display = val ? "block" : "none";

        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            state.searchQuery = val;
            state.page = 1;
            loadRecords();
        }, 250);
    });

    elements.btnClearSearch.addEventListener("click", () => {
        elements.searchInput.value = "";
        elements.btnClearSearch.style.display = "none";
        state.searchQuery = "";
        state.page = 1;
        loadRecords();
    });

    // Mismatch only toggle
    elements.chkMismatchOnly.addEventListener("change", (e) => {
        state.mismatchOnly = e.target.checked;
        state.page = 1;
        loadRecords();
    });

    // Pagination Controls
    if (elements.btnPrevPage) {
        elements.btnPrevPage.addEventListener("click", () => {
            if (state.page > 1) {
                state.page--;
                loadRecords();
            }
        });
    }
    if (elements.btnNextPage) {
        elements.btnNextPage.addEventListener("click", () => {
            if (state.page < state.totalPages) {
                state.page++;
                loadRecords();
            }
        });
    }
    if (elements.selectPageSize) {
        elements.selectPageSize.addEventListener("change", (e) => {
            state.pageSize = parseInt(e.target.value, 10) || 25;
            state.page = 1;
            loadRecords();
        });
    }

    // Modal Close
    elements.btnCloseEdit.addEventListener("click", closeEditModal);
    elements.btnCancelEdit.addEventListener("click", closeEditModal);

    // =========================================================================
    // Drag-and-Drop & File Upload Handlers
    // =========================================================================
    async function uploadSelectedFile(fileType, file) {
        if (!file) return;
        if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
            showToast("รองรับเฉพาะไฟล์ Excel (.xlsx หรือ .xls) เท่านั้น", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file_type", fileType);
        formData.append("file", file);

        showToast(`กำลังอัปโหลดไฟล์ ${file.name}...`, "info");

        try {
            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });
            if (!res.ok) throw new Error("Upload failed");
            const data = await res.json();
            showToast(data.message || `อัปโหลดไฟล์ ${file.name} เรียบร้อย!`, "success");
            await loadSummary();
            await loadRecords();
        } catch (err) {
            console.error("Upload error:", err);
            showToast("เกิดข้อผิดพลาดในการอัปโหลดไฟล์", "error");
        }
    }

    function setupDropzone(dropzoneEl, inputEl, fileType) {
        if (!dropzoneEl || !inputEl) return;

        // Click to open file dialog
        dropzoneEl.addEventListener("click", (e) => {
            if (e.target !== inputEl) {
                inputEl.click();
            }
        });

        inputEl.addEventListener("change", () => {
            if (inputEl.files.length > 0) {
                uploadSelectedFile(fileType, inputEl.files[0]);
            }
        });

        // Drag & Drop events
        ["dragenter", "dragover"].forEach(eventName => {
            dropzoneEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneEl.classList.add("drag-over");
            });
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropzoneEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
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

    setupDropzone(elements.dropzoneMaster, elements.fileInputMaster, "master");
    setupDropzone(elements.dropzoneHw, elements.fileInputHw, "hw");
    setupDropzone(elements.dropzoneSw, elements.fileInputSw, "sw");
    setupDropzone(elements.dropzoneUps, elements.fileInputUps, "ups");

    // Initial Load
    loadSummary();
    loadRecords();

    // Heartbeat for connection health check
    setInterval(() => {
        fetch("/api/heartbeat").catch(() => {});
    }, 5000);

    // =========================================================================
    // System Log Modal Operations (Centered Pro Max Terminal)
    // =========================================================================
    let currentLogLines = [];

    function renderLogContent(filterText = "") {
        if (!elements.logContentArea) return;
        const q = filterText.toLowerCase().trim();
        const filtered = q
            ? currentLogLines.filter(line => line.toLowerCase().includes(q))
            : currentLogLines;

        if (filtered.length > 0) {
            elements.logContentArea.textContent = filtered.join("\n");
        } else if (currentLogLines.length > 0) {
            elements.logContentArea.textContent = `[ไม่พบ Log ที่ตรงกับคำค้นหา: "${filterText}"]`;
        } else {
            elements.logContentArea.textContent = "[ยังไม่มีบันทึกข้อมูลใน Log]";
        }
        elements.logContentArea.scrollTop = elements.logContentArea.scrollHeight;
    }

    async function fetchSystemLogs() {
        if (!elements.logContentArea) return;
        elements.logContentArea.textContent = "กำลังดึงข้อมูล Log ล่าสุด...";
        try {
            const res = await fetch("/api/logs?lines=300");
            if (!res.ok) throw new Error("Failed to fetch logs");
            const data = await res.json();
            if (elements.logFilePath && data.log_file) {
                elements.logFilePath.textContent = data.log_file;
            }
            currentLogLines = data.lines || [];
            const searchInput = document.getElementById("log-search-input");
            const filterVal = searchInput ? searchInput.value : "";
            renderLogContent(filterVal);

            const statusText = document.getElementById("log-status-text");
            if (statusText) {
                statusText.textContent = `อัปเดตแล้ว (${currentLogLines.length} บรรทัด)`;
            }
        } catch (e) {
            elements.logContentArea.textContent = `เกิดข้อผิดพลาดในการโหลด Log: ${e.message}`;
        }
    }

    // Live search inside logs
    const logSearchInput = document.getElementById("log-search-input");
    if (logSearchInput) {
        logSearchInput.addEventListener("input", (e) => {
            renderLogContent(e.target.value);
        });
    }

    // Maximize / Restore Log Modal
    const btnMaximizeLogs = document.getElementById("btn-maximize-logs");
    const btnMaximizeLogsDot = document.getElementById("btn-maximize-logs-dot");
    const iconMaximize = document.getElementById("icon-maximize");
    const modalTerminalBox = document.querySelector(".modal-terminal-box");

    function toggleMaximizeLogs() {
        if (!modalTerminalBox) return;
        modalTerminalBox.classList.toggle("is-maximized");
        const isMax = modalTerminalBox.classList.contains("is-maximized");
        if (iconMaximize) {
            iconMaximize.className = isMax ? "fa-solid fa-compress" : "fa-solid fa-expand";
        }
    }

    if (btnMaximizeLogs) btnMaximizeLogs.addEventListener("click", toggleMaximizeLogs);
    if (btnMaximizeLogsDot) btnMaximizeLogsDot.addEventListener("click", toggleMaximizeLogs);

    if (elements.btnViewLogs) {
        elements.btnViewLogs.addEventListener("click", () => {
            if (elements.modalLogs) {
                elements.modalLogs.style.display = "flex";
                fetchSystemLogs();
            }
        });
    }

    const closeLogModal = () => {
        if (elements.modalLogs) elements.modalLogs.style.display = "none";
    };

    if (elements.btnCloseLogs) elements.btnCloseLogs.addEventListener("click", closeLogModal);
    if (elements.btnDoneLogs) elements.btnDoneLogs.addEventListener("click", closeLogModal);
    const btnCloseLogsDot = document.getElementById("btn-close-logs-dot");
    if (btnCloseLogsDot) btnCloseLogsDot.addEventListener("click", closeLogModal);

    if (elements.modalLogs) {
        elements.modalLogs.addEventListener("click", (e) => {
            if (e.target === elements.modalLogs) closeLogModal();
        });
    }

    if (elements.btnRefreshLogs) {
        elements.btnRefreshLogs.addEventListener("click", fetchSystemLogs);
    }

    if (elements.btnCopyLogs) {
        elements.btnCopyLogs.addEventListener("click", async () => {
            const text = elements.logContentArea ? elements.logContentArea.textContent : "";
            try {
                await navigator.clipboard.writeText(text);
                showToast("คัดลอกข้อความ Log เรียบร้อยแล้ว", "success");
            } catch (err) {
                showToast("ไม่สามารถคัดลอกอัตโนมัติได้ กรุณาเลือกข้อความและกด Ctrl+C", "warning");
            }
        });
    }

    // Global Escape Key to close open modals
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeLogModal();
            closeEditModal();
            if (elements.modalHistory) elements.modalHistory.style.display = "none";
        }
    });

    // =========================================================================
    // Google Workspace-Style Undo, Redo, Version History & Session Management
    // =========================================================================
    async function updateSessionStatus() {
        try {
            const res = await fetch("/api/session/status");
            if (!res.ok) return;
            const data = await res.json();

            if (elements.btnUndo) elements.btnUndo.disabled = !data.can_undo;
            if (elements.btnRedo) elements.btnRedo.disabled = !data.can_redo;

            if (elements.autosaveStatus && elements.autosaveText) {
                if (data.has_data) {
                    elements.autosaveStatus.style.display = "inline-flex";
                    elements.autosaveText.textContent = "บันทึกอัตโนมัติแล้ว";
                    elements.autosaveStatus.className = "autosave-badge";
                } else {
                    elements.autosaveStatus.style.display = "none";
                }
            }
        } catch (e) {
            console.error("Update session status error:", e);
        }
    }

    async function triggerUndo() {
        if (elements.btnUndo && elements.btnUndo.disabled) return;
        try {
            const res = await fetch("/api/undo", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                showToast(data.message || "เลิกทำสำเร็จ", "info");
                await loadSummary();
                await loadRecords();
                await loadFilesStatus();
            } else {
                showToast(data.message || "ไม่มีรายการที่จะเลิกทำ", "warning");
            }
        } catch (err) {
            console.error("Undo error:", err);
            showToast("เกิดข้อผิดพลาดในการเลิกทำ", "error");
        }
    }

    async function triggerRedo() {
        if (elements.btnRedo && elements.btnRedo.disabled) return;
        try {
            const res = await fetch("/api/redo", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                showToast(data.message || "ทำซ้ำสำเร็จ", "info");
                await loadSummary();
                await loadRecords();
                await loadFilesStatus();
            } else {
                showToast(data.message || "ไม่มีรายการที่จะทำซ้ำ", "warning");
            }
        } catch (err) {
            console.error("Redo error:", err);
            showToast("เกิดข้อผิดพลาดในการทำซ้ำ", "error");
        }
    }

    async function openHistoryModal() {
        if (!elements.modalHistory) return;
        elements.modalHistory.style.display = "flex";
        if (elements.historyTimelineList) {
            elements.historyTimelineList.innerHTML = '<p style="color: var(--text-muted); font-size: 12px;">กำลังโหลดประวัติ...</p>';
        }

        try {
            const res = await fetch("/api/history");
            const data = await res.json();
            const history = data.history || [];

            if (history.length === 0) {
                elements.historyTimelineList.innerHTML = `
                    <div style="text-align: center; padding: 24px; color: var(--text-muted);">
                        <i class="fa-solid fa-clock-rotate-left" style="font-size: 28px; margin-bottom: 8px; opacity: 0.5;"></i>
                        <p>ยังไม่มีประวัติการแก้ไขในเซสชันนี้</p>
                    </div>
                `;
                return;
            }

            let html = "";
            history.forEach(item => {
                const badge = item.type === "batch_quick_fix" 
                    ? '<span class="badge-cat badge-cat-hw" style="background:#fef3c7; color:#b45309;">BATCH</span>' 
                    : '<span class="badge-cat badge-cat-sw" style="background:#e0f2fe; color:#0369a1;">EDIT</span>';

                html += `
                    <div class="timeline-card">
                        <div class="timeline-info">
                            <div style="display: flex; align-items: center; gap: 6px;">
                                ${badge}
                                <span class="timeline-title">${item.description}</span>
                            </div>
                            <div class="timeline-meta">
                                <span><i class="fa-regular fa-clock"></i> ${item.timestamp}</span>
                                <span><i class="fa-regular fa-user"></i> ${item.user}</span>
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-sm btn-rollback" data-index="${item.index}" title="ย้อนกลับสถานะไปยังจุดนี้">
                            <i class="fa-solid fa-rotate-left"></i> ย้อนกลับจุดนี้
                        </button>
                    </div>
                `;
            });

            elements.historyTimelineList.innerHTML = html;

            document.querySelectorAll(".btn-rollback").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const idx = parseInt(btn.getAttribute("data-index"), 10);
                    if (confirm(`คุณต้องการย้อนกลับสถานะไปยังเวอร์ชันนี้หรือไม่?`)) {
                        try {
                            const rbRes = await fetch("/api/rollback", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ index: idx })
                            });
                            const rbData = await rbRes.json();
                            showToast(rbData.message || "ย้อนกลับสถานะเรียบร้อย", "success");
                            closeHistoryModal();
                            await loadSummary();
                            await loadRecords();
                            await loadFilesStatus();
                        } catch (e) {
                            showToast("เกิดข้อผิดพลาดในการย้อนกลับ", "error");
                        }
                    }
                });
            });
        } catch (e) {
            elements.historyTimelineList.innerHTML = `<p style="color: red; font-size: 12px;">เกิดข้อผิดพลาดในการโหลดประวัติ: ${e.message}</p>`;
        }
    }

    const closeHistoryModal = () => {
        if (elements.modalHistory) elements.modalHistory.style.display = "none";
    };

    if (elements.btnUndo) elements.btnUndo.addEventListener("click", triggerUndo);
    if (elements.btnRedo) elements.btnRedo.addEventListener("click", triggerRedo);
    if (elements.btnHistory) elements.btnHistory.addEventListener("click", openHistoryModal);
    if (elements.btnCloseHistory) elements.btnCloseHistory.addEventListener("click", closeHistoryModal);
    if (elements.btnDoneHistory) elements.btnDoneHistory.addEventListener("click", closeHistoryModal);
    if (elements.modalHistory) {
        elements.modalHistory.addEventListener("click", (e) => {
            if (e.target === elements.modalHistory) closeHistoryModal();
        });
    }

    // New Session Trigger
    if (elements.btnNewSession) {
        elements.btnNewSession.addEventListener("click", async () => {
            if (confirm("คุณต้องการเริ่มเซสชันใหม่หรือไม่?\nการกระทำนี้จะล้างข้อมูลและประวัติที่บันทึกไว้ และให้คุณใส่ไฟล์ชุดใหม่")) {
                try {
                    const res = await fetch("/api/session/reset", { method: "POST" });
                    const data = await res.json();
                    showToast(data.message || "เริ่มเซสชันใหม่เรียบร้อย", "success");
                    await loadSummary();
                    await loadRecords();
                    await loadFilesStatus();
                    await updateSessionStatus();
                } catch (e) {
                    showToast("เกิดข้อผิดพลาดในการเริ่มเซสชันใหม่", "error");
                }
            }
        });
    }

    // Exit Application Trigger
    if (elements.btnExitApp) {
        elements.btnExitApp.addEventListener("click", async () => {
            if (confirm("คุณต้องการปิดและออกจากโปรแกรม FTI IT Asset Compare หรือไม่?")) {
                try {
                    await fetch("/api/shutdown?force=true", { method: "POST" });
                } catch (e) {}
                showToast("กำลังปิดโปรแกรม...", "info");
                setTimeout(() => {
                    window.close();
                }, 400);
            }
        });
    }

    // Keyboard Shortcuts (Google Workspace style: Ctrl+Z, Ctrl+Y)
    document.addEventListener("keydown", (e) => {
        // Ctrl+Z or Cmd+Z -> Undo
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z") {
            // Check if not typing inside an input/textarea
            if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
            e.preventDefault();
            triggerUndo();
        }
        // Ctrl+Y or Ctrl+Shift+Z -> Redo
        if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))) {
            if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
            e.preventDefault();
            triggerRedo();
        }
    });

    // Initial check of session
    updateSessionStatus();
    loadFilesStatus();
});
