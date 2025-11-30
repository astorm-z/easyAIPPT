// Toast 提示组件 - 自动消失的轻量级提示

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {string} type - 类型：'success', 'error', 'info', 'warning'
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建 toast 容器（如果不存在）
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // 根据类型选择图标
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    const icon = icons[type] || icons.info;

    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    // 添加到容器
    container.appendChild(toast);

    // 触发动画
    requestAnimationFrame(() => {
        toast.classList.add('toast-show');
    });

    // 自动移除
    setTimeout(() => {
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');

        // 动画结束后移除元素
        setTimeout(() => {
            if (toast.parentNode) {
                container.removeChild(toast);
            }

            // 如果容器为空，移除容器
            if (container.children.length === 0) {
                document.body.removeChild(container);
            }
        }, 300);
    }, duration);
}

/**
 * 显示成功 Toast
 * @param {string} message - 提示消息
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showSuccessToast(message, duration = 3000) {
    showToast(message, 'success', duration);
}

/**
 * 显示错误 Toast
 * @param {string} message - 提示消息
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showErrorToast(message, duration = 3000) {
    showToast(message, 'error', duration);
}

/**
 * 显示警告 Toast
 * @param {string} message - 提示消息
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showWarningToast(message, duration = 3000) {
    showToast(message, 'warning', duration);
}

/**
 * 显示信息 Toast
 * @param {string} message - 提示消息
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showInfoToast(message, duration = 3000) {
    showToast(message, 'info', duration);
}

// 导出到全局
window.showToast = showToast;
window.showSuccessToast = showSuccessToast;
window.showErrorToast = showErrorToast;
window.showWarningToast = showWarningToast;
window.showInfoToast = showInfoToast;
