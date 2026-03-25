/**
 * OrderPulse — Core Application Module
 * Handles sidebar, dark mode, toasts, and global utilities.
 */

window.OrderPulse = window.OrderPulse || {};
const OrderPulse = window.OrderPulse;

OrderPulse.initDashboard = function () {
    console.log('Dashboard initialized.');

    // Date picker validation
    const fromDateObj = document.getElementById('fromDate');
    const toDateObj = document.getElementById('toDate');
    
    // Error elements
    const fromError = document.getElementById('fromDateError');
    const toError = document.getElementById('toDateError');
    const globalError = document.getElementById('dateGlobalError');

    if (fromDateObj && toDateObj) {
        const today = new Date().toISOString().split('T')[0];
        fromDateObj.setAttribute('max', today);
        toDateObj.setAttribute('max', today);

        // Set default values to today if empty
        if (!fromDateObj.value) fromDateObj.value = today;
        if (!toDateObj.value) toDateObj.value = today;
        toDateObj.setAttribute('min', fromDateObj.value);

        // Utility to hide errors
        const hideErrors = () => {
            fromDateObj.classList.remove('is-invalid');
            toDateObj.classList.remove('is-invalid');
            fromError.style.display = 'none';
            toError.style.display = 'none';
            if (globalError) globalError.style.display = 'none';
            fromDateObj.style.borderColor = '';
            toDateObj.style.borderColor = '';
        };

        // When start date changes, set min of end date
        fromDateObj.addEventListener('change', function () {
            hideErrors();
            const startVal = this.value;

            if (startVal) {
                toDateObj.setAttribute('min', startVal);
                const endVal = toDateObj.value;
                if (endVal && endVal < startVal) {
                    toDateObj.value = '';
                    toDateObj.style.borderColor = 'var(--danger-color)';
                    toError.innerText = 'End date must be after start date';
                    toError.style.display = 'block';
                }
            } else {
                toDateObj.removeAttribute('min');
            }
        });

        // When end date changes, set max of start date
        toDateObj.addEventListener('change', function () {
            hideErrors();
            const endVal = this.value;

            if (endVal) {
                fromDateObj.setAttribute('max', endVal);
                const startVal = fromDateObj.value;
                if (startVal && startVal > endVal) {
                    fromDateObj.value = '';
                    fromDateObj.style.borderColor = 'var(--danger-color)';
                    fromError.innerText = 'Start date must be before end date';
                    fromError.style.display = 'block';
                }
            } else {
                fromDateObj.setAttribute('max', today);
            }
        });
    }
};

// ============= Sidebar =============
OrderPulse.initSidebar = function () {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar_collapsed', sidebar.classList.contains('collapsed'));
        });

        // Restore state
        if (localStorage.getItem('sidebar_collapsed') === 'true') {
            sidebar.classList.add('collapsed');
        }
    }
};

// ============= Dark Mode =============
OrderPulse.initDarkMode = function () {
    const btn = document.getElementById('darkModeToggle');
    if (btn) {
        btn.addEventListener('click', () => {
            // Already dark by default; this toggle is a placeholder
            OrderPulse.showToast('Dark mode is the default theme.', 'info');
        });
    }
};

// ============= Toast Notifications =============
OrderPulse.showToast = function (message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="material-icons-round">${icons[type] || 'info'}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <span class="material-icons-round" style="font-size:16px;">close</span>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(16px)';
            toast.style.transition = '300ms ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
};

// ============= Password Toggle =============
OrderPulse.togglePassword = function () {
    const input = document.getElementById('apiPassword');
    const icon = document.getElementById('passwordToggleIcon');
    if (input && icon) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.textContent = 'visibility_off';
        } else {
            input.type = 'password';
            icon.textContent = 'visibility';
        }
    }
};

// ============= Table State =============
OrderPulse._tableData = [];
OrderPulse._currentPage = 1;
OrderPulse._pageSize = 10;
OrderPulse._sortField = '';
OrderPulse._sortDir = 'asc';
OrderPulse._currentTaskId = null;

// ============= Table Rendering =============
OrderPulse.renderTable = function (data) {
    OrderPulse._tableData = data || [];
    OrderPulse._currentPage = 1;
    OrderPulse.filterTable();
};

OrderPulse.filterTable = function () {
    const search = (document.getElementById('tableSearch')?.value || '').toLowerCase();
    const storeFilter = document.getElementById('storeFilter')?.value || '';

    let filtered = OrderPulse._tableData.filter(row => {
        const matchSearch = !search ||
            (row.code || '').toLowerCase().includes(search) ||
            (row.awb || '').toLowerCase().includes(search) ||
            (row.status || '').toLowerCase().includes(search);
        const matchStore = !storeFilter || row.store_type === storeFilter;
        return matchSearch && matchStore;
    });

    // Sort
    if (OrderPulse._sortField) {
        filtered.sort((a, b) => {
            let va = a[OrderPulse._sortField] ?? '';
            let vb = b[OrderPulse._sortField] ?? '';
            if (typeof va === 'number' && typeof vb === 'number') {
                return OrderPulse._sortDir === 'asc' ? va - vb : vb - va;
            }
            va = String(va).toLowerCase();
            vb = String(vb).toLowerCase();
            return OrderPulse._sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
        });
    }

    OrderPulse._renderPage(filtered);
};

OrderPulse._renderPage = function (data) {
    const tbody = document.getElementById('ordersTableBody');
    const info = document.getElementById('tableInfo');
    const pagination = document.getElementById('pagination');
    if (!tbody) return;

    const start = (OrderPulse._currentPage - 1) * OrderPulse._pageSize;
    const end = start + OrderPulse._pageSize;
    const pageData = data.slice(start, end);
    const totalPages = Math.ceil(data.length / OrderPulse._pageSize);

    if (pageData.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="6">
                    <div class="empty-state">
                        <span class="material-icons-round">inbox</span>
                        <p>No orders found.</p>
                    </div>
                </td>
            </tr>`;
    } else {
        tbody.innerHTML = pageData.map(row => {
            const dtClass = row.dispatch_time === null ? '' :
                row.dispatch_time <= 24 ? 'dispatch-within' :
                    row.dispatch_time <= 48 ? 'dispatch-beyond' : 'dispatch-critical';
            const dtText = row.dispatch_time !== null ? row.dispatch_time : '—';
            const statusClass = (row.status || '').toLowerCase().replace(/[^a-z]/g, '');

            return `<tr>
                <td><code style="color:var(--primary);font-size:0.8rem;">${row.code || '—'}</code></td>
                <td><span class="store-badge ${row.store_type}">${row.store_type || '—'}</span></td>
                <td style="font-size:0.8rem;">${row.awb || '—'}</td>
                <td class="${dtClass}" style="font-weight:600;">${dtText}</td>
                <td><span class="status-badge ${statusClass}">${row.status || '—'}</span></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="OrderPulse.viewDetail('${row.code}')">
                        <span class="material-icons-round" style="font-size:14px;">visibility</span>
                        View
                    </button>
                </td>
            </tr>`;
        }).join('');
    }

    if (info) {
        info.textContent = `Showing ${Math.min(start + 1, data.length)}–${Math.min(end, data.length)} of ${data.length} orders`;
    }

    if (pagination) {
        let pHtml = '';
        for (let p = 1; p <= totalPages; p++) {
            pHtml += `<button class="page-btn ${p === OrderPulse._currentPage ? 'active' : ''}"
                        onclick="OrderPulse.goToPage(${p})">${p}</button>`;
        }
        pagination.innerHTML = pHtml;
    }
};

OrderPulse.goToPage = function (page) {
    OrderPulse._currentPage = page;
    OrderPulse.filterTable();
};

OrderPulse.sortTable = function (field) {
    if (OrderPulse._sortField === field) {
        OrderPulse._sortDir = OrderPulse._sortDir === 'asc' ? 'desc' : 'asc';
    } else {
        OrderPulse._sortField = field;
        OrderPulse._sortDir = 'asc';
    }
    OrderPulse.filterTable();
};

// ============= Modal =============
OrderPulse.viewDetail = function (code) {
    const modal = document.getElementById('orderModal');
    const loading = document.getElementById('modalLoading');
    const content = document.getElementById('modalContent');
    const codeEl = document.getElementById('modalOrderCode');

    if (modal) modal.style.display = 'flex';
    if (loading) loading.style.display = 'flex';
    if (content) content.style.display = 'none';
    if (codeEl) codeEl.textContent = code;

    OrderPulse.Ajax.getOrderDetail(code);
};

OrderPulse.closeModal = function () {
    const modal = document.getElementById('orderModal');
    if (modal) modal.style.display = 'none';
};

OrderPulse.populateModal = function (data) {
    const loading = document.getElementById('modalLoading');
    const content = document.getElementById('modalContent');
    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';

    // Populate fields
    const set = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '—';
    };

    const code = data.code || data.displayOrderCode || '';
    let storeType = '';
    ['PA', 'PI', 'MA', 'BL'].forEach(p => {
        if (code.toUpperCase().startsWith(p)) storeType = p;
    });

    set('modalStoreType', storeType ? `<span class="store-badge ${storeType}">${storeType}</span>` : '—');
    const storeEl = document.getElementById('modalStoreType');
    if (storeEl && storeType) {
        storeEl.innerHTML = `<span class="store-badge ${storeType}">${storeType}</span>`;
    }

    set('modalOrderDate', data.created || data.displayOrderDateTime || '—');
    set('modalStatus', data.status || data.statusCode || '—');
    set('modalCustomer', data.customerName || data.notificationEmail || '—');

    // Packages
    const packagesEl = document.getElementById('modalPackages');
    const packages = data.shippingPackages || [];
    if (packagesEl) {
        if (packages.length > 0) {
            packagesEl.innerHTML = packages.map((pkg, i) => `
                <div class="package-card">
                    <div class="package-field">
                        <span class="package-field-label">Package ID</span>
                        <span class="package-field-value">${pkg.code || `PKG-${i + 1}`}</span>
                    </div>
                    <div class="package-field">
                        <span class="package-field-label">AWB Number</span>
                        <span class="package-field-value">${pkg.trackingNumber || pkg.awbNumber || '—'}</span>
                    </div>
                    <div class="package-field">
                        <span class="package-field-label">Carrier</span>
                        <span class="package-field-value">${pkg.shippingProvider || '—'}</span>
                    </div>
                </div>
            `).join('');
        } else {
            packagesEl.innerHTML = '<p class="text-muted">No package information available.</p>';
        }
    }
};

// ============= Init =============
document.addEventListener('DOMContentLoaded', () => {
    OrderPulse.initSidebar();
    OrderPulse.initDarkMode();

    // Close modal on overlay click
    const modal = document.getElementById('orderModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) OrderPulse.closeModal();
        });
    }

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') OrderPulse.closeModal();
    });
});

