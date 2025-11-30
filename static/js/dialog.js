// 自定义弹窗组件 - 替代原生 alert, confirm, prompt

/**
 * 显示确认对话框
 * @param {string} message - 提示消息
 * @param {string} title - 标题（可选）
 * @returns {Promise<boolean>} - 用户点击确认返回 true，取消返回 false
 */
function showConfirm(message, title = '确认') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';

        overlay.innerHTML = `
            <div class="dialog">
                <div class="dialog-header">
                    <h3 class="dialog-title">${title}</h3>
                </div>
                <div class="dialog-body">
                    ${message}
                </div>
                <div class="dialog-footer">
                    <button class="dialog-btn" data-action="cancel">取消</button>
                    <button class="dialog-btn dialog-btn-primary" data-action="confirm">确认</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // 触发动画
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        // 处理按钮点击
        const handleClick = (e) => {
            const action = e.target.dataset.action;
            if (action) {
                overlay.classList.remove('active');
                setTimeout(() => {
                    document.body.removeChild(overlay);
                    resolve(action === 'confirm');
                }, 300);
            }
        };

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                handleClick({ target: { dataset: { action: 'cancel' } } });
            }
        });

        overlay.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', handleClick);
        });

        // ESC 键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                handleClick({ target: { dataset: { action: 'cancel' } } });
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    });
}

/**
 * 显示提示对话框
 * @param {string} message - 提示消息
 * @param {string} title - 标题（可选）
 */
function showAlert(message, title = '提示') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';

        overlay.innerHTML = `
            <div class="dialog">
                <div class="dialog-header">
                    <h3 class="dialog-title">${title}</h3>
                </div>
                <div class="dialog-body">
                    ${message}
                </div>
                <div class="dialog-footer">
                    <button class="dialog-btn dialog-btn-primary" data-action="ok">确定</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // 触发动画
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        // 处理按钮点击
        const handleClick = () => {
            overlay.classList.remove('active');
            setTimeout(() => {
                document.body.removeChild(overlay);
                resolve();
            }, 300);
        };

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay || e.target.dataset.action === 'ok') {
                handleClick();
            }
        });

        // ESC 键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                handleClick();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    });
}

/**
 * 显示输入对话框
 * @param {string} message - 提示消息
 * @param {string} defaultValue - 默认值（可选）
 * @param {string} title - 标题（可选）
 * @returns {Promise<string|null>} - 用户输入的值，取消返回 null
 */
function showPrompt(message, defaultValue = '', title = '输入') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';

        overlay.innerHTML = `
            <div class="dialog">
                <div class="dialog-header">
                    <h3 class="dialog-title">${title}</h3>
                </div>
                <div class="dialog-body">
                    <div>${message}</div>
                    <input type="text" class="dialog-input" value="${defaultValue}" placeholder="请输入...">
                </div>
                <div class="dialog-footer">
                    <button class="dialog-btn" data-action="cancel">取消</button>
                    <button class="dialog-btn dialog-btn-primary" data-action="confirm">确认</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const input = overlay.querySelector('.dialog-input');

        // 触发动画
        requestAnimationFrame(() => {
            overlay.classList.add('active');
            input.focus();
            input.select();
        });

        // 处理按钮点击
        const handleClick = (e) => {
            const action = e.target.dataset.action;
            if (action) {
                overlay.classList.remove('active');
                setTimeout(() => {
                    document.body.removeChild(overlay);
                    resolve(action === 'confirm' ? input.value : null);
                }, 300);
            }
        };

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                handleClick({ target: { dataset: { action: 'cancel' } } });
            }
        });

        overlay.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', handleClick);
        });

        // Enter 键确认
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                handleClick({ target: { dataset: { action: 'confirm' } } });
            }
        });

        // ESC 键取消
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                handleClick({ target: { dataset: { action: 'cancel' } } });
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    });
}

// 导出到全局
window.showConfirm = showConfirm;
window.showAlert = showAlert;
window.showPrompt = showPrompt;
