/**
 * OrderPulse — AJAX Module
 * Handles all API calls using Fetch API.
 */

OrderPulse.Ajax = OrderPulse.Ajax || {};

// ============= Helper =============
OrderPulse.Ajax._fetch = async function (url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const config = { ...defaults, ...options };
    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
    }
    const response = await fetch(url, config);
    return response.json();
};

// ============= Settings =============
OrderPulse.testConnection = async function () {
    const btn = document.getElementById('testConnectionBtn');
    const panel = document.getElementById('connectionPanel');
    const icon = document.getElementById('connectionIcon');
    const msg = document.getElementById('connectionMessage');

    const data = {
        api_base_url: document.getElementById('apiBaseUrl')?.value || '',
        username: document.getElementById('apiUsername')?.value || '',
        password: document.getElementById('apiPassword')?.value || ''
    };

    if (!data.api_base_url || !data.username || !data.password) {
        OrderPulse.showToast('Please fill in all fields.', 'warning');
        return;
    }

    if (btn) btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Testing...';

    try {
        const result = await OrderPulse.Ajax._fetch('/api/test-connection', {
            method: 'POST',
            body: data
        });

        if (panel) panel.style.display = 'block';

        if (result.success) {
            if (icon) { icon.textContent = 'check_circle'; icon.className = 'material-icons-round connection-icon success'; }
            if (msg) msg.textContent = result.message;
            OrderPulse.showToast('Connection successful!', 'success');
        } else {
            if (icon) { icon.textContent = 'error'; icon.className = 'material-icons-round connection-icon error'; }
            if (msg) msg.textContent = result.message;
            OrderPulse.showToast('Connection failed.', 'error');
        }
    } catch (e) {
        OrderPulse.showToast('Network error: ' + e.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span class="material-icons-round">power</span><span>Test Connection</span>';
        }
    }
};

OrderPulse.saveSettings = async function () {
    const btn = document.getElementById('saveSettingsBtn');

    const data = {
        api_base_url: document.getElementById('apiBaseUrl')?.value || '',
        username: document.getElementById('apiUsername')?.value || '',
        password: document.getElementById('apiPassword')?.value || ''
    };

    if (!data.api_base_url || !data.username || !data.password) {
        OrderPulse.showToast('Please fill in all fields.', 'warning');
        return;
    }

    if (btn) btn.disabled = true;

    try {
        const result = await OrderPulse.Ajax._fetch('/api/save-settings', {
            method: 'POST',
            body: data
        });

        if (result.success) {
            OrderPulse.showToast('Settings saved successfully!', 'success');
            OrderPulse.loadSavedSettings();
        } else {
            OrderPulse.showToast(result.message || 'Failed to save.', 'error');
        }
    } catch (e) {
        OrderPulse.showToast('Network error: ' + e.message, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
};

OrderPulse.loadSavedSettings = async function () {
    try {
        const result = await OrderPulse.Ajax._fetch('/api/get-settings');
        const panel = document.getElementById('savedCredentials');

        if (result.exists && result.settings && panel) {
            panel.style.display = 'block';
            const s = result.settings;

            const set = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val || '—';
            };

            set('savedUrl', s.api_base_url);
            set('savedUsername', s.username_masked);
            set('savedDate', s.updated_at ? new Date(s.updated_at).toLocaleString() : '—');
            set('savedTestStatus', s.last_test_success ? '✓ Passed' : '✗ Not tested');
        }
    } catch (e) {
        // Settings not loaded, that's fine
    }
};

OrderPulse.clearSettings = async function () {
    if (!confirm('Are you sure you want to clear all saved credentials?')) return;

    try {
        const result = await OrderPulse.Ajax._fetch('/api/settings', { method: 'DELETE' });
        if (result.success) {
            OrderPulse.showToast('Credentials cleared.', 'info');
            const panel = document.getElementById('savedCredentials');
            if (panel) panel.style.display = 'none';
            const connPanel = document.getElementById('connectionPanel');
            if (connPanel) connPanel.style.display = 'none';
        }
    } catch (e) {
        OrderPulse.showToast('Error clearing credentials.', 'error');
    }
};

// ============= Orders =============
OrderPulse.loadOrders = async function () {
    const fromInput = document.getElementById('fromDate');
    const toInput = document.getElementById('toDate');
    
    // Extra validation check before submitting
    const fromDate = fromInput ? fromInput.value : '';
    const toDate = toInput ? toInput.value : '';
    const today = new Date().toISOString().split('T')[0];
    
    const fromError = document.getElementById('fromDateError');
    const toError = document.getElementById('toDateError');
    const globalError = document.getElementById('dateGlobalError');

    // Reset styles
    if (fromInput) fromInput.style.borderColor = '';
    if (toInput) toInput.style.borderColor = '';
    if (fromError) fromError.style.display = 'none';
    if (toError) toError.style.display = 'none';
    if (globalError) globalError.style.display = 'none';

    let hasError = false;

    if (!fromDate) {
        if (fromInput) fromInput.style.borderColor = 'var(--danger-color)';
        if (fromError) { fromError.innerText = 'Please select a start date.'; fromError.style.display = 'block'; }
        hasError = true;
    } else if (fromDate > today) {
        if (fromInput) fromInput.style.borderColor = 'var(--danger-color)';
        if (fromError) { fromError.innerText = 'Cannot select a future date.'; fromError.style.display = 'block'; }
        hasError = true;
    }

    if (!toDate) {
        if (toInput) toInput.style.borderColor = 'var(--danger-color)';
        if (toError) { toError.innerText = 'Please select an end date.'; toError.style.display = 'block'; }
        hasError = true;
    } else if (toDate > today) {
        if (toInput) toInput.style.borderColor = 'var(--danger-color)';
        if (toError) { toError.innerText = 'Cannot select a future date.'; fromError.style.display = 'block'; }
        hasError = true;
    }

    if (fromDate && toDate && toDate < fromDate) {
        if (globalError) { 
            globalError.innerText = 'End date cannot be before start date.'; 
            globalError.style.display = 'block';
        }
        if (toInput) toInput.style.borderColor = 'var(--danger-color)';
        hasError = true;
    }

    if (hasError) return;

    const loadBtn = document.getElementById('loadOrdersBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const exportBtn = document.getElementById('exportBtn');
    const progress = document.getElementById('progressContainer');

    if (loadBtn) loadBtn.disabled = true;
    if (cancelBtn) cancelBtn.style.display = 'inline-flex';
    if (exportBtn) exportBtn.disabled = true;
    if (progress) progress.style.display = 'block';

    OrderPulse._updateProgress(5, 'Submitting request...');

    try {
        const result = await OrderPulse.Ajax._fetch('/api/fetch-orders', {
            method: 'POST',
            body: { from_date: fromDate, to_date: toDate }
        });

        if (result.success) {
            OrderPulse._currentTaskId = result.task_id;
            OrderPulse.showToast('Order loading started.', 'info');
            // Start polling if WebSocket is not connected
            if (!OrderPulse.WS || !OrderPulse.WS.connected) {
                OrderPulse._pollStatus(result.task_id);
            }
        } else {
            OrderPulse.showToast(result.message || 'Failed to start.', 'error');
            OrderPulse._resetLoadUI();
        }
    } catch (e) {
        OrderPulse.showToast('Network error: ' + e.message, 'error');
        OrderPulse._resetLoadUI();
    }
};

OrderPulse.cancelTask = async function () {
    if (!OrderPulse._currentTaskId) return;

    try {
        await OrderPulse.Ajax._fetch('/api/orders/cancel', {
            method: 'POST',
            body: { task_id: OrderPulse._currentTaskId }
        });
        OrderPulse.showToast('Cancel signal sent.', 'warning');
    } catch (e) {
        OrderPulse.showToast('Error cancelling.', 'error');
    }
};

OrderPulse._pollStatus = async function (taskId) {
    const poll = async () => {
        try {
            const result = await OrderPulse.Ajax._fetch(`/api/orders/status?task_id=${taskId}`);

            if (result.status === 'running' || result.status === 'queued') {
                OrderPulse._updateProgress(result.progress || 10, 'Processing...');
                setTimeout(poll, 1500);
            } else if (result.status === 'completed') {
                OrderPulse._updateProgress(100, 'Completed!');
                OrderPulse.showToast('Orders loaded successfully!', 'success');
                OrderPulse._loadReport();
            } else if (result.status === 'cancelled') {
                OrderPulse.showToast('Task cancelled.', 'warning');
                OrderPulse._resetLoadUI();
            } else if (result.status === 'failed') {
                OrderPulse.showToast(`Error: ${result.error || 'Unknown'}`, 'error');
                OrderPulse._resetLoadUI();
            }
        } catch (e) {
            OrderPulse.showToast('Polling error: ' + e.message, 'error');
            OrderPulse._resetLoadUI();
        }
    };

    setTimeout(poll, 1500);
};

OrderPulse._loadReport = async function () {
    try {
        const result = await OrderPulse.Ajax._fetch('/api/report');
        if (result.success && result.data) {
            OrderPulse._updateDashboard(result.data);
        }
    } catch (e) {
        OrderPulse.showToast('Error loading report.', 'error');
    } finally {
        OrderPulse._resetLoadUI();
    }
};

OrderPulse._updateDashboard = function (data) {
    const summary = data.summary || {};

    // Update stat cards with animation
    OrderPulse._animateValue('totalOrdersValue', summary.total_orders || 0);
    OrderPulse._animateValue('awbCountValue', summary.awb_count || 0);

    const avgEl = document.getElementById('avgDispatchValue');
    if (avgEl) avgEl.textContent = summary.avg_dispatch_time || 0;

    const w24El = document.getElementById('within24hValue');
    if (w24El) w24El.textContent = (summary.within_24h_rate || 0) + '%';

    // Update badges
    const awbPct = summary.total_orders > 0 ? Math.round((summary.awb_count / summary.total_orders) * 100) : 0;
    const awbBadge = document.getElementById('statAwbBadge');
    if (awbBadge) awbBadge.textContent = awbPct + '%';

    const rateBadge = document.getElementById('stat24hBadge');
    if (rateBadge) {
        const rate = summary.within_24h_rate || 0;
        rateBadge.textContent = rate >= 75 ? 'Good' : rate >= 50 ? 'Fair' : 'Low';
    }

    // Update charts
    if (OrderPulse.Charts) {
        OrderPulse.Charts.updateBar(data.dispatch_analysis);
        OrderPulse.Charts.updateDonut(data.store_distribution);
        OrderPulse.Charts.updateLine(data.orders_over_time);
    }

    // Update table
    OrderPulse.renderTable(data.table_data || []);

    // Enable export
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) exportBtn.disabled = false;
};

OrderPulse._animateValue = function (elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;

    let current = 0;
    const step = Math.ceil(target / 30);
    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = current.toLocaleString();
    }, 30);
};

OrderPulse._updateProgress = function (progress, message) {
    const bar = document.getElementById('progressBar');
    const text = document.getElementById('progressText');
    if (bar) bar.style.width = Math.max(0, Math.min(100, progress)) + '%';
    if (text) text.textContent = message || '';
};

OrderPulse._resetLoadUI = function () {
    const loadBtn = document.getElementById('loadOrdersBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const progress = document.getElementById('progressContainer');

    if (loadBtn) loadBtn.disabled = false;
    if (cancelBtn) cancelBtn.style.display = 'none';

    setTimeout(() => {
        if (progress) progress.style.display = 'none';
        OrderPulse._updateProgress(0, '');
    }, 1000);

    OrderPulse._currentTaskId = null;
};

// ============= Order Detail =============
OrderPulse.Ajax.getOrderDetail = async function (code) {
    try {
        const result = await OrderPulse.Ajax._fetch(`/api/order/${encodeURIComponent(code)}`);
        if (result.success && result.data) {
            OrderPulse.populateModal(result.data);
        } else {
            OrderPulse.showToast(result.message || 'Failed to load detail.', 'error');
            OrderPulse.closeModal();
        }
    } catch (e) {
        OrderPulse.showToast('Error fetching order detail.', 'error');
        OrderPulse.closeModal();
    }
};

// ============= Export =============
OrderPulse.exportExcel = function () {
    window.location.href = '/api/export';
    OrderPulse.showToast('Downloading Excel report...', 'info');
};

