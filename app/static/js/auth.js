/**
 * Auth.js — AJAX handlers for Authentication, Profile, and Password management.
 */

// ─── Toast Helper ───
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="material-icons-round" style="font-size:18px;">
            ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
        </span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


// ─── Toggle Password Visibility ───
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('.material-icons-round');
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility';
    } else {
        input.type = 'password';
        icon.textContent = 'visibility_off';
    }
}


// ─── AJAX Helper ───
function authFetch(url, method, data) {
    return fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: data ? JSON.stringify(data) : undefined
    }).then(async res => {
        const json = await res.json();
        return { ok: res.ok, status: res.status, data: json };
    });
}


// ─── Login Form ───
(function() {
    const form = document.getElementById('loginForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('loginBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="material-icons-round">hourglass_empty</span> Signing in...';

        authFetch('/api/auth/login', 'POST', {
            email: document.getElementById('loginEmail').value,
            password: document.getElementById('loginPassword').value,
            remember: document.getElementById('rememberMe').checked
        }).then(res => {
            if (res.data.success) {
                showToast('Login successful! Redirecting...', 'success');
                setTimeout(() => { window.location.href = '/'; }, 800);
            } else {
                showToast(res.data.message || 'Login failed.', 'error');
                btn.disabled = false;
                btn.innerHTML = '<span class="material-icons-round">login</span> Sign In';
            }
        }).catch(() => {
            showToast('Network error. Please try again.', 'error');
            btn.disabled = false;
            btn.innerHTML = '<span class="material-icons-round">login</span> Sign In';
        });
    });
})();


// ─── Register Form ───
(function() {
    const form = document.getElementById('registerForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('registerBtn');

        const password = document.getElementById('regPassword').value;
        const confirm = document.getElementById('regConfirm').value;
        if (password !== confirm) {
            showToast('Passwords do not match.', 'error');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<span class="material-icons-round">hourglass_empty</span> Creating...';

        authFetch('/api/auth/register', 'POST', {
            name: document.getElementById('regName').value,
            email: document.getElementById('regEmail').value,
            password: password,
            confirm_password: confirm
        }).then(res => {
            if (res.data.success) {
                showToast('Account created! Redirecting to login...', 'success');
                setTimeout(() => { window.location.href = '/auth/login'; }, 1500);
            } else {
                showToast(res.data.message || 'Registration failed.', 'error');
                btn.disabled = false;
                btn.innerHTML = '<span class="material-icons-round">person_add</span> Create Account';
            }
        }).catch(() => {
            showToast('Network error.', 'error');
            btn.disabled = false;
            btn.innerHTML = '<span class="material-icons-round">person_add</span> Create Account';
        });
    });
})();


// ─── Forgot Password Form ───
(function() {
    const form = document.getElementById('forgotForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('forgotBtn');
        btn.disabled = true;

        authFetch('/api/auth/forgot-password', 'POST', {
            email: document.getElementById('forgotEmail').value
        }).then(res => {
            showToast(res.data.message || 'Check your email/console for the reset link.', res.data.success ? 'success' : 'error');
            btn.disabled = false;
        }).catch(() => {
            showToast('Network error.', 'error');
            btn.disabled = false;
        });
    });
})();


// ─── Reset Password Form ───
(function() {
    const form = document.getElementById('resetForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('resetBtn');
        const password = document.getElementById('resetPassword').value;
        const confirm = document.getElementById('resetConfirm').value;

        if (password !== confirm) {
            showToast('Passwords do not match.', 'error');
            return;
        }

        btn.disabled = true;

        authFetch('/api/auth/reset-password', 'POST', {
            token: document.getElementById('resetToken').value,
            new_password: password,
            confirm_password: confirm
        }).then(res => {
            if (res.data.success) {
                showToast('Password reset! Redirecting to login...', 'success');
                setTimeout(() => { window.location.href = '/auth/login'; }, 1500);
            } else {
                showToast(res.data.message || 'Reset failed.', 'error');
                btn.disabled = false;
            }
        }).catch(() => {
            showToast('Network error.', 'error');
            btn.disabled = false;
        });
    });
})();


// ─── Profile Form ───
(function() {
    const form = document.getElementById('profileForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('saveProfileBtn');
        btn.disabled = true;

        authFetch('/api/auth/profile', 'PUT', {
            name: document.getElementById('profileName').value,
            email: document.getElementById('profileEmail').value
        }).then(res => {
            if (res.data.success) {
                showToast('Profile updated!', 'success');
                // Update displayed name/email
                const dn = document.getElementById('profileDisplayName');
                const de = document.getElementById('profileDisplayEmail');
                if (dn) dn.textContent = res.data.user.name;
                if (de) de.textContent = res.data.user.email;
            } else {
                showToast(res.data.message || 'Update failed.', 'error');
            }
            btn.disabled = false;
        }).catch(() => {
            showToast('Network error.', 'error');
            btn.disabled = false;
        });
    });
})();


// ─── Change Password Form ───
(function() {
    const form = document.getElementById('changePasswordForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const btn = document.getElementById('changePassBtn');
        const newPw = document.getElementById('newPassword').value;
        const confirmPw = document.getElementById('confirmNewPassword').value;

        if (newPw !== confirmPw) {
            showToast('New passwords do not match.', 'error');
            return;
        }

        btn.disabled = true;

        authFetch('/api/auth/change-password', 'POST', {
            old_password: document.getElementById('oldPassword').value,
            new_password: newPw,
            confirm_password: confirmPw
        }).then(res => {
            if (res.data.success) {
                showToast('Password changed successfully!', 'success');
                form.reset();
            } else {
                showToast(res.data.message || 'Failed.', 'error');
            }
            btn.disabled = false;
        }).catch(() => {
            showToast('Network error.', 'error');
            btn.disabled = false;
        });
    });
})();


// ─── User Dropdown Menu Toggle ───
(function() {
    const avatarBtn = document.getElementById('userAvatarBtn');
    const dropdown = document.getElementById('userDropdown');
    if (!avatarBtn || !dropdown) return;

    avatarBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });

    // Close on outside click
    document.addEventListener('click', function() {
        dropdown.classList.remove('open');
    });

    dropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
})();


// ─── Logout Button ───
(function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;

    logoutBtn.addEventListener('click', function() {
        authFetch('/api/auth/logout', 'POST').then(res => {
            if (res.data.success) {
                window.location.href = '/auth/login';
            }
        }).catch(() => {
            window.location.href = '/auth/login';
        });
    });
})();
