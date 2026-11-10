const ApiService = {
	routes: {
		login: 'https://api.libra.example.com/v1/auth/login',
		register: 'https://api.libra.example.com/v1/auth/register',
		resetPassword: 'https://api.libra.example.com/v1/auth/reset'
	},

	async call(apiName, payload = {}) {
		const targetUrl = this.routes[apiName];

		if (!targetUrl) {
			console.error(`[API ERROR] - Không tìm thấy route cho key: '${apiName}'`);
			throw new Error(`Route '${apiName}' is not defined.`);
		}

		console.group(`📡 [DEBUG API CALL] - ${apiName.toUpperCase()}`);
		console.log(`🔗 URL:`, targetUrl);
		console.log(`📦 Payload Data:`, payload);
		console.groupEnd();

		return new Promise((resolve) => {
			setTimeout(() => {
				resolve({
					status: 200,
					success: true,
					message: `Đăng nhập thành công vào endpoint ${targetUrl}`,
					data: {
						accessToken: "eyJhbGciOiJIUzI1NiIsInR...",
						userRole: payload.role
					}
				});
			}, 1200);
		});
	}
};

let currentRole = 'librarian';
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

togglePasswordBtn.addEventListener('click', () => {
	const isPassword = passwordInput.getAttribute('type') === 'password';
	passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

	const icon = togglePasswordBtn.querySelector('i');
	if (isPassword) {
		icon.classList.replace('fa-eye', 'fa-eye-slash');
		togglePasswordBtn.classList.replace('text-slate-400', 'text-blue-600');
	} else {
		icon.classList.replace('fa-eye-slash', 'fa-eye');
		togglePasswordBtn.classList.replace('text-blue-600', 'text-slate-400');
	}
});

const loginForm = document.getElementById('loginForm');

loginForm.addEventListener('submit', async (e) => {
	e.preventDefault();

	const payloadData = {
		role: currentRole,
		username: document.getElementById('username').value,
		password: passwordInput.value,
		rememberMe: document.getElementById('remember').checked
	};

	const submitBtn = loginForm.querySelector('button[type="submit"]');
	const originalContent = submitBtn.innerHTML;
	submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> <span>Đang xử lý...</span>';
	submitBtn.disabled = true;
	submitBtn.classList.add('opacity-75', 'cursor-not-allowed');

	try {
		const response = await ApiService.call('login', payloadData);

		if (response.success) {
			console.log('✅ [API RESPONSE]:', response);
			alert(`Đăng nhập thành công!\n(Hãy mở Console/F12 để xem cấu trúc gọi API Debug)`);
		}
	} catch (error) {
		console.error("Lỗi đăng nhập:", error);
		alert("Đã xảy ra lỗi hệ thống!");
	} finally {
		submitBtn.innerHTML = originalContent;
		submitBtn.disabled = false;
		submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
	}
});

// --- XỬ LÝ CUSTOM ALERT ---
const customAlert = document.getElementById('customAlert');
const customAlertBox = document.getElementById('customAlertBox');

function showCustomAlert() {
    // Xóa class hidden để hiển thị DOM
    customAlert.classList.remove('hidden');
    customAlert.classList.add('flex');
    
    // Tạo một chút delay nhỏ (reflow) để animation chạy mượt
    setTimeout(() => {
        customAlert.classList.remove('opacity-0');
        customAlertBox.classList.remove('scale-95');
        customAlertBox.classList.add('scale-100');
    }, 10);
}

function closeCustomAlert() {
    customAlert.classList.add('opacity-0');
    customAlertBox.classList.remove('scale-100');
    customAlertBox.classList.add('scale-95');
    
    setTimeout(() => {
        customAlert.classList.add('hidden');
        customAlert.classList.remove('flex');
    }, 300);
}

customAlert.addEventListener('click', (e) => {
    if (e.target === customAlert) {
        closeCustomAlert();
    }
});