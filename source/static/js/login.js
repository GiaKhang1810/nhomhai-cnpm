const ApiService = {
    routes: {
        login: '/auth/login',
        logout: '/auth/logout'
    },

    async call(apiName, payload = {}) {
        const targetUrl = this.routes[apiName];
        try {
            const response = await fetch(targetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                return {
                    status: response.status,
                    success: response.ok && (data.success ?? true),
                    message: data.message || 'Thao tác thành công.',
                    redirect_url: data.redirect_url,
                    data: data.data || {}
                };
            } else {
                const text = await response.text();
                console.error("❌ [SERVER ERROR - HTML RESPONSE]:", text);
                return {
                    status: response.status,
                    success: false,
                    message: "Máy chủ trả về HTML thay vì JSON. Hãy kiểm tra terminal Python."
                };
            }
        } catch (error) {
            return {
                status: 500,
                success: false,
                message: 'Không thể kết nối đến máy chủ.'
            };
        }
    }
};

let currentRole = 'librarian';

document.addEventListener('DOMContentLoaded', () => {
    const roleButtons = document.querySelectorAll('[data-role]');
    
    roleButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            roleButtons.forEach(b => {
                b.className = 'flex-1 py-2 hover:bg-slate-200 rounded-md font-medium transition-all text-xs md:text-sm text-slate-500';
            });

            e.target.className = 'flex-1 py-2 bg-blue-600 text-white rounded-md font-semibold shadow-sm transition-all text-xs md:text-sm';
            
            currentRole = e.target.getAttribute('data-role');
        });
    });

    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if(togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', () => {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

            const icon = togglePasswordBtn.querySelector('i');
            if (icon) {
                if (isPassword) {
                    icon.classList.replace('fa-eye', 'fa-eye-slash');
                    togglePasswordBtn.classList.replace('text-slate-400', 'text-blue-600');
                } else {
                    icon.classList.replace('fa-eye-slash', 'fa-eye');
                    togglePasswordBtn.classList.replace('text-blue-600', 'text-slate-400');
                }
            }
        });
    }

    const loginForm = document.getElementById('loginForm');
    
    if(loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const roleMap = {
                'librarian': 'LIBRARIAN',
                'reader': 'READER',
                'admin': 'ADMIN'
            };

            const usernameElement = document.getElementById('username');
            const rememberElement = document.getElementById('remember');

            const payloadData = {
                role: roleMap[currentRole] || 'LIBRARIAN',
                username: usernameElement ? usernameElement.value.trim() : '',
                password: passwordInput ? passwordInput.value : '',
                rememberMe: rememberElement ? rememberElement.checked : false
            };

            if (!payloadData.username || !payloadData.password) {
                alert("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.");
                return;
            }

            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalContent = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> <span>Đang xử lý...</span>';
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-75', 'cursor-not-allowed');

            try {
                const response = await ApiService.call('login', payloadData);

                if (response.success) {
                    if (response.redirect_url) {
                        window.location.href = response.redirect_url;
                    } else {
                        alert(response.message || 'Đăng nhập thành công!');
                    }
                } else {
                    alert(response.message || 'Đăng nhập thất bại.');
                }
            } catch (error) {
                console.error("Lỗi đăng nhập:", error);
                alert("Đã xảy ra lỗi hệ thống! Vui lòng thử lại sau.");
            } finally {
                submitBtn.innerHTML = originalContent;
                submitBtn.disabled = false;
                submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
            }
        });
    }
});

const customAlert = document.getElementById('customAlert');
const customAlertBox = document.getElementById('customAlertBox');

function showCustomAlert() {
    if(!customAlert || !customAlertBox) return;
    customAlert.classList.remove('hidden');
    customAlert.classList.add('flex');
    
    setTimeout(() => {
        customAlert.classList.remove('opacity-0');
        customAlertBox.classList.remove('scale-95');
        customAlertBox.classList.add('scale-100');
    }, 10);
}

function closeCustomAlert() {
    if(!customAlert || !customAlertBox) return;
    customAlert.classList.add('opacity-0');
    customAlertBox.classList.remove('scale-100');
    customAlertBox.classList.add('scale-95');
    
    setTimeout(() => {
        customAlert.classList.add('hidden');
        customAlert.classList.remove('flex');
    }, 300);
}

if(customAlert) {
    customAlert.addEventListener('click', (e) => {
        if (e.target === customAlert) {
            closeCustomAlert();
        }
    });
}