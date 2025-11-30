// 通用工具函数

// API请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }

        return data.data;
    } catch (error) {
        console.error('API请求错误:', error);
        showError(error.message);
        throw error;
    }
}

// API请求封装（静默版本，用于轮询等场景，不显示错误弹窗）
async function apiRequestSilent(url, options = {}) {
    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    });

    const data = await response.json();

    if (!data.success) {
        throw new Error(data.error || '请求失败');
    }

    return data.data;
}

// 显示错误消息
function showError(message) {
    showAlert(message, '错误');
}

// 显示成功消息
function showSuccess(message) {
    showAlert(message, '成功');
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 显示加载状态
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('hidden');
    }
}

// 隐藏加载状态
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('hidden');
    }
}

// 模态框控制
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// 点击模态框背景关闭
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});
