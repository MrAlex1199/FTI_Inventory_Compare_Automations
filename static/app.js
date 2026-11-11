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
        sortColumn: null, // Column name being sorted
        sortOrder: null,  // 'asc', 'desc', or null
        viewMode: localStorage.getItem("fti_view_mode") || "mismatch", // 'mismatch' (default) or 'spreadsheet'
        selectedRecord: null,
        systemState: null,
        theme: localStorage.getItem("fti_theme") || "light"
    };

    // DOM Elements Cache
    const elements = {
        // Sidebar & App Version
        appSidebar: document.getElementById("app-sidebar"),
        btnTopbarSidebarToggle: document.getElementById("btn-topbar-sidebar-toggle"),
        brandVersion: document.getElementById("brand-version"),
        settingsAppVersion: document.getElementById("settings-app-version"),
        settingsBuildNum: document.getElementById("settings-build-num"),
        settingsCompileTime: document.getElementById("settings-compile-time"),
        settingsStoragePath: document.getElementById("settings-storage-path"),
        settingsStorageSize: document.getElementById("settings-storage-size"),
        settingsStorageTime: document.getElementById("settings-storage-time"),
        settingsRuntimeEnv: document.getElementById("settings-runtime-env"),
        settingsOsInfo: document.getElementById("settings-os-info"),

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
        btnExportMismatch: document.getElementById("btn-export-mismatch"),
        btnExportCategory: document.getElementById("btn-export-category"),
        workspaceStatusBadge: document.getElementById("workspace-status-badge"),
        btnModeMismatch: document.getElementById("btn-mode-mismatch"),
        btnModeSpreadsheet: document.getElementById("btn-mode-spreadsheet"),
        categoryKpiBar: document.getElementById("category-kpi-bar"),
        btnToggleKpi: document.getElementById("btn-toggle-kpi"),
        bentoKpiGrid: document.getElementById("bento-kpi-grid"),
        catKpiMatchRate: document.getElementById("cat-kpi-match-rate"),
        catKpiProgress: document.getElementById("cat-kpi-progress"),
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
        const btnDark = document.getElementById("btn-theme-dark");
        const btnLight = document.getElementById("btn-theme-light");
        if (btnDark && btnLight) {
            btnDark.classList.toggle("active", theme === "dark");
            btnLight.classList.toggle("active", theme === "light");
        }
    }
    applyTheme(state.theme);

    elements.themeToggle.addEventListener("click", () => {
        applyTheme(state.theme === "dark" ? "light" : "dark");
    });

    document.getElementById("btn-theme-dark")?.addEventListener("click", () => applyTheme("dark"));
    document.getElementById("btn-theme-light")?.addEventListener("click", () => applyTheme("light"));

    // KPI Bar Collapse/Expand Toggle
    if (elements.btnToggleKpi && elements.bentoKpiGrid) {
        const isCollapsed = localStorage.getItem("fti_kpi_collapsed") === "true";
        if (isCollapsed) {
            elements.bentoKpiGrid.classList.add("collapsed");
            const txt = elements.btnToggleKpi.querySelector(".toggle-text");
            const icon = elements.btnToggleKpi.querySelector("i");
            if (txt) txt.textContent = "ขยาย";
            if (icon) icon.className = "fa-solid fa-chevron-down";
        }
        elements.btnToggleKpi.addEventListener("click", () => {
            const nowCollapsed = elements.bentoKpiGrid.classList.toggle("collapsed");
            localStorage.setItem("fti_kpi_collapsed", nowCollapsed);
            const txt = elements.btnToggleKpi.querySelector(".toggle-text");
            const icon = elements.btnToggleKpi.querySelector("i");
            if (txt) txt.textContent = nowCollapsed ? "ขยาย" : "พับเก็บ";
            if (icon) icon.className = nowCollapsed ? "fa-solid fa-chevron-down" : "fa-solid fa-chevron-up";
        });
    }

    // =========================================================================
    // Sidebar Collapse / Expand Management (Icon-Rail Mode)
    // =========================================================================
    function setSidebarCollapsed(collapsed) {
        if (!elements.appSidebar) return;
        if (collapsed) {
            elements.appSidebar.classList.add("collapsed");
        } else {
            elements.appSidebar.classList.remove("collapsed");
        }
        localStorage.setItem("fti_sidebar_collapsed", collapsed ? "true" : "false");
    }

    if (elements.btnTopbarSidebarToggle) {
        elements.btnTopbarSidebarToggle.addEventListener("click", () => {
            const isCollapsed = elements.appSidebar.classList.contains("collapsed");
            setSidebarCollapsed(!isCollapsed);
        });
    }

    // Restore saved sidebar state or responsive default for HD screens (<= 1366px)
    const storedSidebar = localStorage.getItem("fti_sidebar_collapsed");
    if (storedSidebar !== null) {
        setSidebarCollapsed(storedSidebar === "true");
    } else if (window.innerWidth <= 1366) {
        setSidebarCollapsed(true);
    }

    // =========================================================================
    // Dynamic Version & Build Info
    // =========================================================================
    async function fetchVersionInfo() {
        try {
            const res = await fetch("/api/version");
            if (res.ok) {
                const data = await res.json();
                if (elements.brandVersion) {
                    elements.brandVersion.textContent = data.display_version || "v2.1.0";
                }
                if (elements.settingsAppVersion) {
                    elements.settingsAppVersion.textContent = data.version || "-";
                }
                if (elements.settingsBuildNum) {
                    elements.settingsBuildNum.textContent = String(data.build_number || "-");
                }
                if (elements.settingsCompileTime) {
                    elements.settingsCompileTime.textContent = data.compiled_at || "-";
                }
            }
        } catch (e) {
            console.warn("Version fetch failed:", e);
        }
    }

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

    // Direct Compare Buttons on Cards
    document.querySelectorAll(".btn-card-compare").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const cat = btn.getAttribute("data-cat");
            if (!cat) return;
            btn.disabled = true;
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> เทียบ...';
            try {
                const res = await fetch(`/api/compare/${cat}`, { method: "POST" });
                const d = await res.json();
                if (!res.ok) throw new Error(d.detail || "การเปรียบเทียบล้มเหลว");
                showToast(`เปรียบเทียบหมวด ${cat.toUpperCase()} สำเร็จ (ตรงกัน ${d.match_rate}%)`, "success");
                await fetchSystemState();
            } catch (err) {
                showToast(`เกิดข้อผิดพลาด: ${err.message}`, "error");
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    });

    // Executive Dashboard Quick Action Buttons
    async function runCompareAll() {
        const btnBanner = document.getElementById("btn-banner-compare-all");
        const btnDeck = document.getElementById("btn-exec-compare-all");
        if (btnBanner) { btnBanner.disabled = true; btnBanner.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังเปรียบเทียบ...'; }
        if (btnDeck) { btnDeck.disabled = true; }

        showToast("กำลังเริ่มเปรียบเทียบข้อมูลทุกหมวดหมู่ (HW, SW, UPS)...", "info");

        try {
            const res = await fetch("/api/compare-all?reset_to_orig=true", { method: "POST" });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "การเปรียบเทียบล้มเหลว");

            const overall = (data.summary && data.summary.overall) || {};
            const rate = overall.match_rate || 0;
            const mismatches = overall.mismatched_records || 0;

            showToast(`เปรียบเทียบครบ 3 หมวดแล้ว! ตรงกัน ${rate}% (พบจุดต่างที่รอตรวจสอบ ${mismatches} รายการ)`, "info");
            await fetchSystemState();
        } catch (err) {
            showToast(`เกิดข้อผิดพลาดในการเปรียบเทียบ: ${err.message}`, "error");
        } finally {
            if (btnBanner) { btnBanner.disabled = false; btnBanner.innerHTML = '<i class="fa-solid fa-bolt"></i> เปรียบเทียบทุกหมวดหมู่อัตโนมัติ'; }
            if (btnDeck) { btnDeck.disabled = false; }
        }
    }

    const btnBannerCompareAll = document.getElementById("btn-banner-compare-all");
    if (btnBannerCompareAll) btnBannerCompareAll.addEventListener("click", runCompareAll);

    const btnExecCompareAll = document.getElementById("btn-exec-compare-all");
    if (btnExecCompareAll) btnExecCompareAll.addEventListener("click", runCompareAll);

    const btnExecAutoFixAll = document.getElementById("btn-exec-autofix-all");
    if (btnExecAutoFixAll) {
        btnExecAutoFixAll.addEventListener("click", async () => {
            btnExecAutoFixAll.disabled = true;
            showToast("กำลังประมวลผล 1-Click Auto-Fix ทุกหมวดหมู่...", "info");
            try {
                const res = await fetch("/api/auto-fix/all", { method: "POST" });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail);
                showToast("1-Click Auto-Fix สำเร็จสมบูรณ์ 100% ทุกหมวดหมู่!", "success");
                await fetchSystemState();
            } catch (err) {
                showToast(`Auto-Fix ล้มเหลว: ${err.message}`, "error");
            } finally {
                btnExecAutoFixAll.disabled = false;
            }
        });
    }

    const btnExecDownloadAll = document.getElementById("btn-exec-download-all");
    if (btnExecDownloadAll) {
        btnExecDownloadAll.addEventListener("click", () => {
            switchView("summary");
        });
    }

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

        // Update Card Row Counts and Metric Subtitles
        const rowsMaster = document.getElementById("file-rows-master");
        const rowsHw = document.getElementById("file-rows-hw");
        const rowsSw = document.getElementById("file-rows-sw");
        const rowsUps = document.getElementById("file-rows-ups");

        if (rowsMaster) rowsMaster.textContent = (files.master && files.master.rows ? files.master.rows.toLocaleString() : "0");
        if (rowsHw) rowsHw.textContent = (files.hw && files.hw.rows ? files.hw.rows.toLocaleString() : "0");
        if (rowsSw) rowsSw.textContent = (files.sw && files.sw.rows ? files.sw.rows.toLocaleString() : "0");
        if (rowsUps) rowsUps.textContent = (files.ups && files.ups.rows ? files.ups.rows.toLocaleString() : "0");

        const updateStatusDetail = (cat, elId) => {
            const el = document.getElementById(elId);
            if (!el) return;
            const st = states[cat];
            const byCat = (data.summary && data.summary.by_category) || {};
            const sum = byCat[cat] || (data.summary && data.summary[cat]) || {};
            if (st === "compared") {
                const rate = sum.match_rate || 0;
                const matched = sum.matched || 0;
                const mismatched = sum.mismatched !== undefined ? sum.mismatched : (sum.mismatches || 0);
                el.textContent = `เทียบแล้ว ${rate.toFixed(1)}% (ตรง ${matched.toLocaleString()} | ต่าง ${mismatched.toLocaleString()})`;
            } else if (st === "stale") {
                el.textContent = "ไฟล์ Master เปลี่ยน รอเทียบใหม่";
            } else if (files[cat] && files[cat].loaded) {
                el.textContent = "พร้อมเริ่มการเปรียบเทียบ";
            } else {
                el.textContent = "รอไฟล์ข้อมูล";
            }
        };
        updateStatusDetail("hw", "file-status-detail-hw");
        updateStatusDetail("sw", "file-status-detail-sw");
        updateStatusDetail("ups", "file-status-detail-ups");

        // Update Compact Control Strip Readiness Status
        const stripStatus = document.getElementById("strip-files-status");
        if (stripStatus) {
            const masterOk = files.master && files.master.loaded;
            const countLoaded = ["hw", "sw", "ups"].filter(c => files[c] && files[c].loaded).length;
            if (masterOk && countLoaded === 3) {
                stripStatus.innerHTML = '<span class="text-green"><i class="fa-solid fa-circle-check"></i> พร้อมเปรียบเทียบครบทั้ง 4 ไฟล์ (1 Master + 3 IT Targets)</span>';
            } else if (masterOk) {
                stripStatus.innerHTML = `<span class="text-blue"><i class="fa-solid fa-circle-info"></i> ไฟล์ Master พร้อมแล้ว และโหลดไฟล์ IT ได้ ${countLoaded}/3 หมวดหมู่</span>`;
            } else {
                stripStatus.innerHTML = '<span class="text-amber"><i class="fa-solid fa-triangle-exclamation"></i> กรุณาอัปโหลดไฟล์หลัก ERP Master ก่อนทำการเปรียบเทียบ</span>';
            }
        }

        // Executive Dashboard KPI & Stepper Calculation
        updateExecutiveDashboard(data);

        // Undo/Redo tools
        elements.btnUndo.disabled = !data.can_undo;
        elements.btnRedo.disabled = !data.can_redo;

        // If in category view, update action bar
        if (["hw", "sw", "ups"].includes(state.currentView)) {
            updateWorkspaceControls(state.activeCategory);
        }
    }

    // =========================================================================
    // Executive Dashboard (Bento KPIs & Workflow Stepper)
    // =========================================================================
    function updateExecutiveDashboard(data) {
        const summary = data.summary || {};
        const overall = summary.overall || {};
        const byCat = summary.by_category || {};
        const states = data.category_states || {};
        const files = data.files || {};

        let totalRecords = 0;
        let totalMatched = 0;
        let totalMismatches = 0;
        let totalExcluded = 0;
        let totalUserEdited = 0;
        let comparedCount = 0;

        ["hw", "sw", "ups"].forEach(cat => {
            const s = byCat[cat] || summary[cat];
            const isCompared = states[cat] === "compared";
            if (isCompared && s) {
                comparedCount++;
                totalRecords += (s.initial_total || (files[cat] ? files[cat].rows : 0) || 0);
                totalMatched += (s.matched || 0);
                totalMismatches += (s.mismatched !== undefined ? s.mismatched : (s.mismatches || 0));
                totalExcluded += (s.excluded || 0);
                totalUserEdited += (s.user_edited || 0);
            } else if (files[cat] && files[cat].rows) {
                totalRecords += files[cat].rows;
            }
        });

        // If backend already computed overall summary and categories were compared, use overall directly
        if (overall.total_initial_records && comparedCount > 0) {
            totalRecords = overall.total_initial_records;
            if (overall.matched_records !== undefined) totalMatched = overall.matched_records;
            if (overall.mismatched_records !== undefined) totalMismatches = overall.mismatched_records;
            if (overall.excluded_records !== undefined) totalExcluded = overall.excluded_records;
            if (overall.user_edited_records !== undefined) totalUserEdited = overall.user_edited_records;
        }

        const activeTotal = totalMatched + totalMismatches;
        const overallRate = activeTotal > 0 ? ((totalMatched / activeTotal) * 100) : (overall.match_rate || 0);

        const elTotal = document.getElementById("exec-kpi-total");
        const elRate = document.getElementById("exec-kpi-rate");
        const elBar = document.getElementById("exec-kpi-bar");
        const elMatchedCount = document.getElementById("exec-kpi-matched-count");
        const elMismatch = document.getElementById("exec-kpi-mismatch");
        const elFixed = document.getElementById("exec-kpi-fixed");

        if (elTotal) elTotal.textContent = totalRecords.toLocaleString();

        if (comparedCount === 0) {
            if (elRate) elRate.textContent = "รอเริ่มเทียบ";
            if (elBar) elBar.style.width = "0%";
            if (elMatchedCount) elMatchedCount.textContent = 'กดปุ่ม "⚡ เปรียบเทียบทั้งหมด" ด้านล่าง';
            if (elMismatch) elMismatch.textContent = "-";
            if (elFixed) elFixed.textContent = "-";
        } else {
            if (elRate) elRate.textContent = `${overallRate.toFixed(1)}%`;
            if (elBar) elBar.style.width = `${Math.min(100, Math.max(0, overallRate))}%`;
            if (elMatchedCount) {
                if (comparedCount === 3) {
                    elMatchedCount.textContent = `ตรงกัน ${totalMatched.toLocaleString()} จาก ${activeTotal.toLocaleString()} รายการ (ครบ 3 หมวด)`;
                } else {
                    elMatchedCount.textContent = `ตรงกัน ${totalMatched.toLocaleString()} จาก ${activeTotal.toLocaleString()} รายการ (${comparedCount}/3 หมวด)`;
                }
            }
            if (elMismatch) elMismatch.textContent = totalMismatches.toLocaleString();
            if (elFixed) elFixed.textContent = (totalExcluded + totalUserEdited).toLocaleString();
        }

        // Update Stepper Progress
        const isMasterLoaded = files.master && files.master.loaded;
        const isAllCatsLoaded = ["hw", "sw", "ups"].every(c => files[c] && files[c].loaded);
        const isAnyCompared = ["hw", "sw", "ups"].some(c => states[c] === "compared");
        const isAllCompared = ["hw", "sw", "ups"].every(c => states[c] === "compared");

        const step1 = document.getElementById("workflow-step-1");
        const step2 = document.getElementById("workflow-step-2");
        const step3 = document.getElementById("workflow-step-3");
        const chip1 = document.getElementById("step-1-chip");
        const chip2 = document.getElementById("step-2-chip");
        const chip3 = document.getElementById("step-3-chip");

        if (step1 && chip1) {
            if (isMasterLoaded && isAllCatsLoaded) {
                step1.className = "stepper-step completed";
                chip1.className = "step-status-chip chip-done";
                chip1.textContent = "เสร็จสิ้น";
            } else {
                step1.className = "stepper-step active";
                chip1.className = "step-status-chip chip-active";
                chip1.textContent = "กำลังโหลดไฟล์";
            }
        }

        if (step2 && chip2) {
            if (isAllCompared) {
                step2.className = "stepper-step completed";
                chip2.className = "step-status-chip chip-done";
                chip2.textContent = overallRate >= 99.9 ? "ตรงกัน 100%" : "เปรียบเทียบครบแล้ว";
            } else if (isAnyCompared) {
                step2.className = "stepper-step active";
                chip2.className = "step-status-chip chip-active";
                chip2.textContent = "เปรียบเทียบไปแล้วบางหมวด";
            } else {
                step2.className = "stepper-step";
                chip2.className = "step-status-chip chip-pending";
                chip2.textContent = "รอดำเนินการ";
            }
        }

        if (step3 && chip3) {
            if (isAllCompared) {
                step3.className = "stepper-step active";
                chip3.className = "step-status-chip chip-active";
                chip3.textContent = "พร้อมส่งออกผลลัพธ์";
            } else {
                step3.className = "stepper-step";
                chip3.className = "step-status-chip chip-pending";
                chip3.textContent = "รอขั้นตอนที่ 2";
            }
        }
    }

    function updateWorkspaceControls(cat) {
        const st = (state.systemState && state.systemState.category_states && state.systemState.category_states[cat]) || "empty";
        const badge = elements.workspaceStatusBadge;

        if (elements.btnExportCategory) elements.btnExportCategory.href = `/api/export/inventory/${cat}`;
        if (elements.btnExportMismatch) elements.btnExportMismatch.href = `/api/export/mismatch/${cat}`;

        // Sync view mode buttons
        if (elements.btnModeMismatch && elements.btnModeSpreadsheet) {
            elements.btnModeMismatch.classList.toggle("active", state.viewMode === "mismatch");
            elements.btnModeSpreadsheet.classList.toggle("active", state.viewMode === "spreadsheet");
        }

        if (st === "compared") {
            badge.className = "status-indicator-badge text-green";
            badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> เปรียบเทียบแล้ว';
            elements.categoryKpiBar.style.display = "inline-flex";
            if (elements.btnExportMismatch) elements.btnExportMismatch.style.display = "inline-flex";
            if (elements.btnExportCategory) elements.btnExportCategory.style.display = "inline-flex";
            elements.btnRunAutoFix.style.display = "inline-flex";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> เปรียบเทียบใหม่';
        } else if (st === "stale") {
            badge.className = "status-indicator-badge text-amber";
            badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ข้อมูลเปลี่ยน - รอเปรียบเทียบใหม่';
            elements.categoryKpiBar.style.display = "none";
            if (elements.btnExportMismatch) elements.btnExportMismatch.style.display = "none";
            if (elements.btnExportCategory) elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        } else if (st === "loaded") {
            badge.className = "status-indicator-badge text-blue";
            badge.innerHTML = '<i class="fa-solid fa-circle-info"></i> พร้อมให้กดเปรียบเทียบ';
            elements.categoryKpiBar.style.display = "none";
            if (elements.btnExportMismatch) elements.btnExportMismatch.style.display = "none";
            if (elements.btnExportCategory) elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        } else {
            badge.className = "status-indicator-badge";
            badge.innerHTML = 'ยังไม่มีไฟล์';
            elements.categoryKpiBar.style.display = "none";
            if (elements.btnExportMismatch) elements.btnExportMismatch.style.display = "none";
            if (elements.btnExportCategory) elements.btnExportCategory.style.display = "none";
            elements.btnRunAutoFix.style.display = "none";
            elements.btnRunCompare.innerHTML = '<i class="fa-solid fa-play"></i> เริ่มเปรียบเทียบ';
        }

        // Update KPI bar if compared
        if (st === "compared" && state.systemState && state.systemState.summary) {
            const catSum = (state.systemState.summary.by_category && state.systemState.summary.by_category[cat]) || {};
            const rate = catSum.match_rate || 0;
            elements.catKpiMatchRate.textContent = `${rate}%`;
            if (elements.catKpiProgress) {
                elements.catKpiProgress.style.width = `${rate}%`;
            }
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
    // Spreadsheet Grid Engine (Full Columns + In-Cell Edit + 3-State Sorting)
    // =========================================================================
    const COLUMN_MAP = {
        hw: { emp_id: "รหัสพนักงาน", emp_name: "ผู้ใช้งาน/ดูแล", dept: "สถานที่เก็บ", sn: "S/N" },
        sw: { emp_id: "รหัสพนักงาน", emp_name: "ผู้ดูแล", dept: "สถานที่เก็บ", sn: "Key License" },
        ups: { emp_id: "รหัสพนักงาน", emp_name: "ผู้ใช้งาน/ดูแล", dept: "สถานที่เก็บ", sn: "S/N" }
    };

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function highlightSearch(text, query) {
        if (!query || text === null || text === undefined || text === "") {
            return (text === 0 ? "0" : (text || ""));
        }
        const str = String(text);
        const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const re = new RegExp(`(${escaped})`, 'gi');
        return str.replace(re, '<mark class="search-match">$1</mark>');
    }

    async function loadCategoryWorkspace(cat) {
        if (state.currentCategory !== cat) {
            state.selectedRecord = null;
            if (elements.erpSidePanel) {
                elements.erpSidePanel.classList.add("collapsed");
            }
        }
        updateWorkspaceControls(cat);

        const params = new URLSearchParams({
            filter_type: state.gridFilter,
            search: state.gridSearch,
            page: state.gridPage,
            page_size: state.gridPageSize
        });
        if (state.sortColumn) {
            params.set("sort_by", state.sortColumn);
            params.set("sort_dir", state.sortOrder || "asc");
        }

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
        const isMismatchMode = (state.viewMode === "mismatch");

        function getSortIcon(col) {
            if (state.sortColumn !== col) return '<i class="fa-solid fa-sort sort-icon"></i>';
            if (state.sortOrder === "asc") return '<i class="fa-solid fa-sort-up sort-icon"></i>';
            return '<i class="fa-solid fa-sort-down sort-icon"></i>';
        }

        function getSortClass(col) {
            if (state.sortColumn !== col) return "";
            return state.sortOrder === "asc" ? "sorted-asc" : "sorted-desc";
        }

        // 1. Build Header
        if (isMismatchMode) {
            elements.spreadsheetThead.innerHTML = `
                <tr>
                    <th class="col-sticky-1" style="width: 45px; text-align: center;">#</th>
                    <th class="col-sticky-2 sortable-th ${getSortClass('status')}" data-sort="status" style="width: 135px;" title="คลิกเพื่อจัดเรียงตามสถานะ">สถานะ ${getSortIcon('status')}</th>
                    <th class="sortable-th ${getSortClass('asset_id')}" data-sort="asset_id" style="width: 150px;" title="คลิกเพื่อจัดเรียงตามรหัสทรัพย์สิน">รหัสทรัพย์สิน (Asset ID) ${getSortIcon('asset_id')}</th>
                    <th class="sortable-th ${getSortClass('mismatch_type')}" data-sort="mismatch_type" style="width: 190px;" title="คลิกเพื่อจัดเรียงตามประเภทจุดต่าง">ประเภทจุดต่าง (Mismatch) ${getSortIcon('mismatch_type')}</th>
                    <th class="sortable-th ${getSortClass('it_emp_name')}" data-sort="it_emp_name" style="min-width: 250px;" title="คลิกเพื่อจัดเรียงตามชื่อผู้ถือครอง IT">ข้อมูลใน IT Inventory (เดิม/ล่าสุด) ${getSortIcon('it_emp_name')}</th>
                    <th class="sortable-th ${getSortClass('ax_emp_name')}" data-sort="ax_emp_name" style="min-width: 250px;" title="คลิกเพื่อจัดเรียงตามชื่อ ERP AX">ข้อมูลในระบบ ERP (AX) ${getSortIcon('ax_emp_name')}</th>
                    <th style="width: 170px; text-align: center;">การจัดการ</th>
                </tr>
            `;
        } else {
            let thHtml = `
                <th class="col-sticky-1" style="width: 45px; text-align: center;">#</th>
                <th class="col-sticky-2 sortable-th ${getSortClass('status')}" data-sort="status" style="width: 140px;" title="คลิกเพื่อจัดเรียงตามสถานะ">สถานะ ${getSortIcon('status')}</th>
            `;
            cols.forEach(col => {
                thHtml += `<th class="sortable-th ${getSortClass(col)}" data-sort="${col}" title="คลิกเพื่อจัดเรียงตาม ${col}">${col} ${getSortIcon(col)}</th>`;
            });
            elements.spreadsheetThead.innerHTML = `<tr>${thHtml}</tr>`;
        }

        // Attach 3-State Column Sort Event Handlers
        elements.spreadsheetThead.querySelectorAll(".sortable-th").forEach(th => {
            th.addEventListener("click", () => {
                const col = th.getAttribute("data-sort");
                if (state.sortColumn === col) {
                    if (state.sortOrder === "asc") {
                        state.sortOrder = "desc";
                    } else if (state.sortOrder === "desc") {
                        state.sortColumn = null;
                        state.sortOrder = null;
                    }
                } else {
                    state.sortColumn = col;
                    state.sortOrder = "asc";
                }
                state.gridPage = 1;
                loadCategoryWorkspace(state.activeCategory);
            });
        });

        // 2. Build Rows
        if (records.length === 0) {
            elements.spreadsheetTbody.innerHTML = `
                <tr>
                    <td colspan="${isMismatchMode ? 7 : cols.length + 2}" style="padding: 38px 20px; text-align: center;">
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;">
                            <i class="fa-solid fa-circle-check text-green" style="font-size: 36px;"></i>
                            <h4 style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0;">ไม่พบรายการที่ตรงกับเงื่อนไข</h4>
                            <p style="font-size: 12.5px; color: var(--text-muted); margin: 0 0 10px 0;">ข้อมูลในหมวดนี้ไม่มีจุดต่างค้างอยู่ หรือรายการทั้งหมดตรงกับระบบ ERP แล้ว</p>
                            <button class="btn btn-secondary btn-sm" id="btn-empty-reset-filter"><i class="fa-solid fa-rotate-left"></i> แสดงรายการทั้งหมด</button>
                        </div>
                    </td>
                </tr>
            `;
            const btnReset = document.getElementById("btn-empty-reset-filter");
            if (btnReset) {
                btnReset.addEventListener("click", () => {
                    elements.gridFilterPills.forEach(p => p.classList.toggle("active", p.getAttribute("data-filter") === "all"));
                    state.gridFilter = "all";
                    state.gridPage = 1;
                    loadCategoryWorkspace(state.activeCategory);
                });
            }
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
            const ax = r.ax_data || {};
            const mType = r.mismatch_type || "ปกติ";

            let rowClass = "";
            if (isExcluded) rowClass += " row-excluded";
            if (state.selectedRecord && state.selectedRecord.uid === uid) rowClass += " selected";

            // Status Badge
            let statusBadge = "";
            if (isExcluded) {
                statusBadge = `<span class="grid-badge grid-badge-excluded"><i class="fa-solid fa-ban"></i> ตัดออก</span>`;
            } else if (isMatch === true) {
                if (userEdited.length > 0) {
                    statusBadge = `<span class="grid-badge" style="background: rgba(14, 165, 233, 0.16); color: #0284c7; border: 1px solid rgba(14, 165, 233, 0.3);"><i class="fa-solid fa-user-pen"></i> แก้ไขเอง 100%</span>`;
                } else {
                    statusBadge = `<span class="grid-badge grid-badge-match"><i class="fa-solid fa-circle-check"></i> ตรงกัน 100%</span>`;
                }
            } else if (isMatch === false) {
                statusBadge = `<span class="grid-badge grid-badge-mismatch"><i class="fa-solid fa-triangle-exclamation"></i> ไม่ตรง</span>`;
            } else {
                statusBadge = `<span class="grid-badge grid-badge-pending">รอเปรียบเทียบ</span>`;
            }

            if (isMismatchMode) {
                // Mismatch Inspector View: Clear Side-by-Side Comparison
                const aid = r.asset_id || (ax && ax.asset_id) || (r.cells && (r.cells["เลขที่ทรัพย์สิน"] || r.cells["รหัสทรัพย์สิน"] || r.cells["Fixed Asset Number"] || r.cells["Asset ID"] || r.cells["Asset_ID"] || r.cells["Asset Number"] || r.cells["Asset_Number"] || r.cells["License_Key"])) || "-";
                const itEmp = r.it_emp_id || "-";
                const itName = r.it_emp_name || "-";
                const itDept = r.it_dept || "-";

                const axEmp = ax.ax_emp_id || "-";
                const axName = ax.ax_emp_name || "-";
                const axDept = ax.ax_dept || "-";
                const axStatus = ax.ax_status || (ax.asset_id ? "ปกติ" : "ไม่พบใน ERP");

                let mTypeColor = "#dc2626";
                if (mType.includes("แผนก")) mTypeColor = "#d97706";
                if (mType.includes("ตัดจำหน่าย")) mTypeColor = "#ea580c";
                if (mType.includes("ตรงกัน")) mTypeColor = "#16a34a";

                const aidDisp = highlightSearch(aid, state.gridSearch);
                const itEmpDisp = highlightSearch(itEmp, state.gridSearch);
                const itNameDisp = highlightSearch(itName, state.gridSearch);
                const itDeptDisp = highlightSearch(itDept, state.gridSearch);
                const axEmpDisp = highlightSearch(axEmp, state.gridSearch);
                const axNameDisp = highlightSearch(axName, state.gridSearch);
                const axDeptDisp = highlightSearch(axDept, state.gridSearch);
                const mTypeDisp = highlightSearch(mType, state.gridSearch);

                tbodyHtml += `
                    <tr class="${rowClass}" data-uid="${uid}">
                        <td class="col-sticky-1" style="text-align: center; color: var(--text-muted);">${rowNum}</td>
                        <td class="col-sticky-2">${statusBadge}</td>
                        <td style="font-family: var(--font-mono); font-weight: 600; color: var(--blue-primary);">${aidDisp}</td>
                        <td style="font-weight: 600; color: ${mTypeColor};">${mTypeDisp}</td>
                        <td>
                            <div class="comp-box">
                                <div class="comp-row"><span class="comp-label">รหัส:</span> <span class="comp-val ${diffs.includes('emp_id') ? 'diff-emp' : ''}">${itEmpDisp}</span></div>
                                <div class="comp-row"><span class="comp-label">ชื่อ:</span> <span class="comp-val">${itNameDisp}</span></div>
                                <div class="comp-row"><span class="comp-label">แผนก:</span> <span class="comp-val ${diffs.includes('dept') ? 'diff-dept' : ''}">${itDeptDisp}</span></div>
                            </div>
                        </td>
                        <td>
                            <div class="comp-box">
                                <div class="comp-row"><span class="comp-label">รหัส:</span> <span class="comp-val">${axEmpDisp}</span></div>
                                <div class="comp-row"><span class="comp-label">ชื่อ:</span> <span class="comp-val">${axNameDisp}</span></div>
                                <div class="comp-row"><span class="comp-label">แผนก:</span> <span class="comp-val">${axDeptDisp}</span></div>
                                <div class="comp-row"><span class="comp-label">สถานะ:</span> <span class="comp-val" style="color: ${ax.is_scrapped ? '#ef4444' : 'inherit'}; font-weight: 600;">${axStatus}</span></div>
                            </div>
                        </td>
                        <td style="text-align: center;">
                            <div class="row-actions-group" style="justify-content: center;">
                                ${ax.asset_id && !ax.is_scrapped && !isMatch ? `
                                    <button class="btn btn-primary btn-sm btn-row-sync" data-uid="${uid}" title="ซิงค์ข้อมูลแถวนี้ให้ตรงกับ ERP ทันที">
                                        <i class="fa-solid fa-bolt"></i> ซิงค์ ERP
                                    </button>
                                ` : (isMatch ? `<span style="font-size: 11px; color: #10b981; font-weight: 600;"><i class="fa-solid fa-check-double"></i> ซิงค์ตรงแล้ว</span>` : '')}
                                <button class="btn btn-secondary btn-sm btn-row-toggle-excl" data-uid="${uid}" title="${isExcluded ? 'กู้คืนเป็นรายการใช้งาน' : 'ตัดรายการนี้ออก'}">
                                    <i class="fa-solid ${isExcluded ? 'fa-arrow-rotate-left text-green' : 'fa-ban text-amber'}"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                // Spreadsheet Full Column View
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

                    const valDisp = highlightSearch(val, state.gridSearch);
                    trHtml += `<td class="${cellClass}" data-col="${col}" title="ดับเบิลคลิกเพื่อแก้ไข">${valDisp}</td>`;
                });

                trHtml += `</tr>`;
                tbodyHtml += trHtml;
            }
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

        // Quick-Fix Sync ERP button in Mismatch Inspector table
        document.querySelectorAll(".btn-row-sync").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const uid = btn.getAttribute("data-uid");
                const rec = records.find(r => r.uid === uid);
                if (!rec) return;

                const ax = rec.ax_data || {};
                const cmap = COLUMN_MAP[rec.category] || COLUMN_MAP["hw"];

                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

                try {
                    if (ax.ax_emp_id) {
                        await fetch("/api/cell", {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ uid, column: cmap.emp_id, value: ax.ax_emp_id, user: "IT Officer" })
                        });
                    }
                    if (ax.ax_emp_name) {
                        await fetch("/api/cell", {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ uid, column: cmap.emp_name, value: ax.ax_emp_name, user: "IT Officer" })
                        });
                    }
                    if (ax.ax_dept) {
                        await fetch("/api/cell", {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ uid, column: cmap.dept, value: ax.ax_dept, user: "IT Officer" })
                        });
                    }
                    showToast(`ซิงค์ข้อมูล ${rec.asset_id || uid} ให้ตรงกับ ERP เรียบร้อย`, "success");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                } catch (err) {
                    showToast(`ซิงค์ล้มเหลว: ${err.message}`, "error");
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-bolt"></i> ซิงค์ ERP';
                }
            });
        });

        // Toggle Exclude in Mismatch Inspector table
        document.querySelectorAll(".btn-row-toggle-excl").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const uid = btn.getAttribute("data-uid");
                const rec = records.find(r => r.uid === uid);
                if (!rec) return;

                try {
                    const res = await fetch("/api/row/exclusion", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid, exclude: !rec.is_excluded, user: "IT Officer" })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail);

                    showToast(rec.is_excluded ? "คืนกลับเป็นรายการใช้งานแล้ว" : "ย้ายไปข้อมูลที่ถูกตัดออกแล้ว", "info");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                } catch (err) {
                    showToast(`ดำเนินการล้มเหลว: ${err.message}`, "error");
                }
            });
        });
    }

    // =========================================================================
    // Field-by-Field Diff Inspector (Side Panel Engine)
    // =========================================================================
    function renderSidePanel(rec) {
        if (!elements.erpSidePanel) return;
        elements.erpSidePanel.classList.remove("collapsed");

        const ax = rec.ax_data || {};
        const isExcl = rec.is_excluded;
        const cmap = COLUMN_MAP[rec.category] || COLUMN_MAP["hw"];
        const cells = rec.cells || {};

        const aid = rec.asset_id || (ax && ax.asset_id) || cells["เลขที่ทรัพย์สิน"] || cells["รหัสทรัพย์สิน"] || cells["Fixed Asset Number"] || cells["Asset ID"] || cells["Asset_ID"] || cells["Asset Number"] || cells["Asset_Number"] || cells["License_Key"] || "-";
        const axStatus = ax.ax_status || (ax.asset_id ? "ปกติ" : "ไม่พบใน ERP");

        // Helper to render one comparison card
        function renderDiffFieldCard(fieldTitle, itVal, axVal, colName) {
            const strIt = (itVal || "").trim();
            const strAx = (axVal || "").trim();
            const isMatch = Boolean(strIt && strAx && strIt.toLowerCase() === strAx.toLowerCase());
            const hasAxVal = Boolean(strAx && strAx !== "-");
            const canSync = hasAxVal && !isMatch && ax.asset_id && !ax.is_scrapped;

            return `
                <div class="field-diff-card ${isMatch ? 'diff-match' : 'diff-mismatch'}">
                    <div class="field-diff-header">
                        <span class="field-diff-title">${fieldTitle}</span>
                        <span class="diff-badge ${isMatch ? 'badge-match' : 'badge-mismatch'}">
                            <i class="fa-solid ${isMatch ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
                            ${isMatch ? 'ตรงกัน 100%' : 'ต่างกัน'}
                        </span>
                    </div>
                    <div class="field-diff-grid">
                        <div class="diff-val-row">
                            <span class="diff-source-label">ใน IT:</span>
                            <span class="diff-val-text">${escapeHtml(itVal) || '<span class="text-muted">(ว่าง)</span>'}</span>
                        </div>
                        <div class="diff-val-row">
                            <span class="diff-source-label">ใน ERP:</span>
                            <span class="diff-val-text text-erp">${escapeHtml(axVal) || '<span class="text-muted">(ไม่พบใน ERP)</span>'}</span>
                        </div>
                    </div>
                    ${canSync ? `
                        <button class="btn-field-sync" data-col="${escapeHtml(colName)}" data-val="${escapeHtml(axVal)}" title="ซิงค์เฉพาะฟิลด์นี้ให้ตรงกับ ERP">
                            <i class="fa-solid fa-bolt"></i> ซิงค์เฉพาะค่านี้
                        </button>
                    ` : ''}
                </div>
            `;
        }

        const itEmpId = rec.it_emp_id || cells[cmap.emp_id] || "";
        const itEmpName = rec.it_emp_name || cells[cmap.emp_name] || "";
        const itDept = rec.it_dept || cells[cmap.dept] || "";
        const itSn = rec.it_sn || cells[cmap.sn] || "";

        let html = `
            <div class="side-hero-banner">
                <div class="side-hero-top">
                    <span class="side-hero-id">${escapeHtml(aid)}</span>
                    <span class="diff-badge ${ax.is_scrapped ? 'badge-mismatch' : (ax.asset_id ? 'badge-match' : 'badge-mismatch')}">
                        ${axStatus}
                    </span>
                </div>
                <div style="font-size: 11.5px; color: var(--text-muted);">หมวดหมู่: <strong style="color: var(--text-primary);">${rec.category.toUpperCase()}</strong> | UID: ${rec.uid}</div>
            </div>

            <!-- Field 1: รหัสพนักงาน -->
            ${renderDiffFieldCard("รหัสพนักงาน (Employee ID)", itEmpId, ax.ax_emp_id || "", cmap.emp_id)}

            <!-- Field 2: ชื่อผู้ถือครอง / ผู้ดูแล -->
            ${renderDiffFieldCard("ชื่อผู้ถือครอง (Employee Name)", itEmpName, ax.ax_emp_name || "", cmap.emp_name)}

            <!-- Field 3: แผนก / สถานที่เก็บ -->
            ${renderDiffFieldCard("แผนก (Department / Location)", itDept, ax.ax_dept || "", cmap.dept)}

            <!-- Field 4: Serial Number -->
            ${renderDiffFieldCard("Serial Number / Key", itSn, ax.ax_sn || "", cmap.sn)}

            <div class="side-actions-row">
                ${ax.asset_id && !ax.is_scrapped ? `
                    <button class="btn btn-primary btn-sm" id="btn-side-sync-erp">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> ซิงค์ทุกฟิลด์ให้ตรงกับ ERP
                    </button>
                ` : ""}

                <button class="btn btn-secondary btn-sm" id="btn-side-toggle-excl">
                    <i class="fa-solid ${isExcl ? 'fa-arrow-rotate-left text-green' : 'fa-filter-circle-xmark text-amber'}"></i>
                    ${isExcl ? 'คืนกลับเป็นรายการใช้งาน (แท็บ 3)' : 'ย้ายไปข้อมูลที่ถูกตัดออก (แท็บ 4)'}
                </button>
            </div>
        `;

        elements.sidePanelBody.innerHTML = html;

        // Bind Per-Field Sync Buttons
        elements.sidePanelBody.querySelectorAll(".btn-field-sync").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const col = btn.getAttribute("data-col");
                const val = btn.getAttribute("data-val");
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังซิงค์...';
                try {
                    const res = await fetch("/api/cell", {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid: rec.uid, column: col, value: val, user: "IT Officer" })
                    });
                    const d = await res.json();
                    if (!res.ok) throw new Error(d.detail);
                    showToast(`ซิงค์ ${col} เป็น "${val}" สำเร็จ`, "success");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                    if (d.record) {
                        state.selectedRecord = d.record;
                        renderSidePanel(d.record);
                    }
                } catch (err) {
                    showToast(`ซิงค์ไม่สำเร็จ: ${err.message}`, "error");
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-bolt"></i> ซิงค์เฉพาะค่านี้';
                }
            });
        });

        // Bind Toggle Exclude
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

        // Bind Sync All ERP
        const btnSyncErp = document.getElementById("btn-side-sync-erp");
        if (btnSyncErp) {
            btnSyncErp.addEventListener("click", async () => {
                btnSyncErp.disabled = true;
                btnSyncErp.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังซิงค์ทุกฟิลด์...';
                try {
                    if (ax.ax_emp_id) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cmap.emp_id, value: ax.ax_emp_id, user: "IT Officer" }) });
                    if (ax.ax_emp_name) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cmap.emp_name, value: ax.ax_emp_name, user: "IT Officer" }) });
                    if (ax.ax_dept) await fetch("/api/cell", { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ uid: rec.uid, column: cmap.dept, value: ax.ax_dept, user: "IT Officer" }) });

                    showToast("ซิงค์ทุกฟิลด์ของแถวนี้ให้ตรงกับ ERP แล้ว", "success");
                    await fetchSystemState();
                    await loadCategoryWorkspace(rec.category);
                } catch (e) {
                    showToast(e.message, "error");
                    btnSyncErp.disabled = false;
                    btnSyncErp.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> ซิงค์ทุกฟิลด์ให้ตรงกับ ERP';
                }
            });
        }
    }

    elements.btnCloseSidepanel.addEventListener("click", () => {
        if (elements.erpSidePanel) {
            elements.erpSidePanel.classList.add("collapsed");
        }
        elements.sidePanelBody.innerHTML = '<p class="side-panel-empty">คลิกเลือกแถวในตารางเพื่อดูการเปรียบเทียบจุดต่างรายฟิลด์</p>';
    });

    // =========================================================================
    // Keyboard Navigation & Ergonomics (Arrow Up/Down, Enter/F2, Esc)
    // =========================================================================
    document.addEventListener("keydown", (e) => {
        if (state.currentView === "files" || state.currentView === "summary") return;
        if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;

        const rows = Array.from(elements.spreadsheetTbody.querySelectorAll("tr[data-uid]"));
        if (!rows.length) return;

        const curIdx = rows.findIndex(r => r.classList.contains("selected"));

        if (e.key === "ArrowDown") {
            e.preventDefault();
            const nextIdx = (curIdx < rows.length - 1) ? curIdx + 1 : 0;
            const targetRow = rows[nextIdx];
            targetRow.click();
            targetRow.scrollIntoView({ block: "nearest", behavior: "smooth" });
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            const prevIdx = (curIdx > 0) ? curIdx - 1 : rows.length - 1;
            const targetRow = rows[prevIdx];
            targetRow.click();
            targetRow.scrollIntoView({ block: "nearest", behavior: "smooth" });
        } else if (e.key === "Escape") {
            if (elements.erpSidePanel && !elements.erpSidePanel.classList.contains("collapsed")) {
                elements.erpSidePanel.classList.add("collapsed");
            }
        } else if (e.key === "Enter" || e.key === "F2") {
            if (curIdx >= 0) {
                const targetRow = rows[curIdx];
                const editableTd = targetRow.querySelector("td[data-col]");
                if (editableTd) {
                    editableTd.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
                }
            }
        }
    });

    // =========================================================================
    // Dual View Mode Switcher (Mismatch Inspector vs Spreadsheet Grid)
    // =========================================================================
    if (elements.btnModeMismatch) {
        elements.btnModeMismatch.addEventListener("click", () => {
            state.viewMode = "mismatch";
            localStorage.setItem("fti_view_mode", "mismatch");
            elements.btnModeMismatch.classList.add("active");
            elements.btnModeSpreadsheet.classList.remove("active");
            if (elements.erpSidePanel) {
                elements.erpSidePanel.classList.add("collapsed");
            }
            state.gridPage = 1;
            loadCategoryWorkspace(state.activeCategory);
        });
    }

    if (elements.btnModeSpreadsheet) {
        elements.btnModeSpreadsheet.addEventListener("click", () => {
            state.viewMode = "spreadsheet";
            localStorage.setItem("fti_view_mode", "spreadsheet");
            elements.btnModeSpreadsheet.classList.add("active");
            elements.btnModeMismatch.classList.remove("active");
            state.gridPage = 1;
            loadCategoryWorkspace(state.activeCategory);
        });
    }

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

    // Settings Modal (Bento Grid)
    async function loadSettingsModalData() {
        try {
            const [statusRes, verRes] = await Promise.all([
                fetch("/api/session/status"),
                fetch("/api/version")
            ]);
            const status = await statusRes.json();
            const ver = await verRes.json();

            if (elements.settingsStoragePath) {
                elements.settingsStoragePath.textContent = status.autosave_path || "ยังไม่มีการบันทึกไฟล์";
            }
            if (elements.settingsStorageSize) {
                elements.settingsStorageSize.textContent = `${status.autosave_size_kb || 0} KB`;
            }
            if (elements.settingsStorageTime) {
                elements.settingsStorageTime.textContent = status.autosave_last_saved || "-";
            }
            if (elements.settingsRuntimeEnv) {
                elements.settingsRuntimeEnv.textContent = `Python ${status.python_version || "3.13"} / FastAPI Desktop`;
            }
            if (elements.settingsOsInfo) {
                elements.settingsOsInfo.textContent = status.platform_system || "Windows";
            }
            if (elements.settingsAppVersion) {
                elements.settingsAppVersion.textContent = ver.display_version || ver.version || "v2.1.0";
            }
            if (elements.settingsBuildNum) {
                elements.settingsBuildNum.textContent = `Build ${ver.build_number || "-"}`;
            }
            if (elements.settingsCompileTime) {
                elements.settingsCompileTime.textContent = ver.compiled_at || "-";
            }

            state.diagnostics = {
                app_version: ver.version || "2.1.0",
                display_version: ver.display_version || "v2.1.0",
                build_number: ver.build_number || 1,
                compiled_at: ver.compiled_at || "-",
                python_version: status.python_version || "-",
                platform: status.platform_system || "-",
                autosave_path: status.autosave_path || "-",
                autosave_size_kb: status.autosave_size_kb || 0,
                total_records: status.total_records || 0,
                matched_records: status.matched_records || 0
            };
        } catch (e) {
            console.warn("Failed to load settings modal data:", e);
        }
    }

    elements.btnOpenSettings.addEventListener("click", () => {
        elements.modalSettings.style.display = "flex";
        applyTheme(state.theme);
        loadSettingsModalData();
    });
    elements.btnCloseSettings.addEventListener("click", () => { elements.modalSettings.style.display = "none"; });
    elements.btnDoneSettings.addEventListener("click", () => { elements.modalSettings.style.display = "none"; });

    // Copy Autosave Path
    const btnCopyPath = document.getElementById("btn-copy-autosave-path");
    if (btnCopyPath) {
        btnCopyPath.addEventListener("click", async () => {
            const p = elements.settingsStoragePath ? elements.settingsStoragePath.textContent : "";
            if (p && p !== "กำลังโหลดตำแหน่งไฟล์..." && p !== "ยังไม่มีการบันทึกไฟล์") {
                try {
                    await navigator.clipboard.writeText(p);
                    showToast("คัดลอกตำแหน่งไฟล์สำเร็จ", "success");
                } catch (e) {
                    showToast("คัดลอกไม่สำเร็จ", "warning");
                }
            } else {
                showToast("ไม่พบตำแหน่งไฟล์เซสชัน", "warning");
            }
        });
    }

    // Copy Diagnostics
    const btnCopyDiag = document.getElementById("btn-copy-diagnostics");
    if (btnCopyDiag) {
        btnCopyDiag.addEventListener("click", async () => {
            try {
                const diagData = state.diagnostics || {
                    version: elements.settingsAppVersion?.textContent || "v2.1.0",
                    build: elements.settingsBuildNum?.textContent || "Build 11",
                    compiled_at: elements.settingsCompileTime?.textContent || "-",
                    os: elements.settingsOsInfo?.textContent || "Windows",
                    runtime: elements.settingsRuntimeEnv?.textContent || "Python 3.13 / FastAPI"
                };
                await navigator.clipboard.writeText(JSON.stringify(diagData, null, 2));
                showToast("คัดลอกข้อมูลระบบ (Diagnostics) สำเร็จ", "success");
            } catch (e) {
                showToast("คัดลอกข้อมูลไม่สำเร็จ", "warning");
            }
        });
    }

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
    fetchVersionInfo();
    fetchSystemState();
});
