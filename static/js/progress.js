// PPT生成和进度管理

// 加载项目信息
async function loadProjectInfo(projectId) {
    try {
        const project = await apiRequest(`/api/ppt/${projectId}`);
        document.getElementById('ppt-title').textContent = project.title;
    } catch (error) {
        console.error('加载项目信息失败:', error);
    }
}

// 加载样式模板
async function loadStyles(projectId) {
    try {
        const styles = await apiRequest(`/api/ppt/${projectId}/styles`);
        displayStyles(styles);
    } catch (error) {
        console.error('加载样式模板失败:', error);
    }
}

// 显示样式模板
function displayStyles(styles) {
    const grid = document.getElementById('styles-grid');
    if (!grid) return;

    if (styles.length === 0) {
        grid.innerHTML = '<p class="text-muted">点击上方按钮生成样式模板</p>';
        return;
    }

    grid.innerHTML = styles.map(style => `
        <div class="card" onclick="selectStyle(${style.template_index})">
            <img src="${style.image_path}" alt="样式 ${style.template_index + 1}" style="width: 100%; height: auto;">
            <div class="mt-sm text-center">
                <button class="btn btn-sm">选择此样式</button>
            </div>
        </div>
    `).join('');
}

// 生成样式模板
async function generateStyles() {
    if (!confirm('生成样式模板需要一些时间，确定吗？')) return;

    try {
        // 启动生成任务
        await apiRequest(`/api/ppt/${projectId}/styles/generate`, {
            method: 'POST'
        });

        // 显示进度区域
        showStyleProgress();

        // 开始轮询进度
        pollStyleProgress();
    } catch (error) {
        showError('启动样式生成失败: ' + error.message);
    }
}

// 显示样式生成进度
function showStyleProgress() {
    const section = document.getElementById('style-section');
    if (!section) return;

    // 添加进度显示区域
    let progressDiv = document.getElementById('style-progress');
    if (!progressDiv) {
        progressDiv = document.createElement('div');
        progressDiv.id = 'style-progress';
        progressDiv.className = 'mb-lg';
        progressDiv.innerHTML = `
            <div class="progress">
                <div id="style-progress-bar" class="progress-bar" style="width: 0%"></div>
            </div>
            <p id="style-progress-text" class="text-center text-muted mt-sm">准备中...</p>
        `;
        section.insertBefore(progressDiv, document.getElementById('styles-grid'));
    }
    progressDiv.classList.remove('hidden');
}

// 隐藏样式生成进度
function hideStyleProgress() {
    const progressDiv = document.getElementById('style-progress');
    if (progressDiv) {
        progressDiv.classList.add('hidden');
    }
}

// 轮询样式生成进度
async function pollStyleProgress() {
    const maxAttempts = 300; // 最多轮询5分钟（每秒一次）
    let attempts = 0;

    const poll = async () => {
        try {
            const status = await apiRequest(`/api/ppt/${projectId}/styles/status`);

            // 更新进度条
            const progress = (status.current / status.total) * 100;
            const progressBar = document.getElementById('style-progress-bar');
            const progressText = document.getElementById('style-progress-text');

            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
            if (progressText) {
                progressText.textContent = status.message || `正在生成 ${status.current}/${status.total}`;
            }

            // 检查状态
            if (status.status === 'completed') {
                showSuccess('样式模板生成完成！');
                hideStyleProgress();
                await loadStyles(projectId);
                return;
            } else if (status.status === 'failed') {
                showError('样式模板生成失败: ' + status.message);
                hideStyleProgress();
                return;
            }

            // 继续轮询
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 1000); // 每秒轮询一次
            } else {
                showError('样式生成超时，请刷新页面查看结果');
                hideStyleProgress();
            }
        } catch (error) {
            console.error('轮询进度失败:', error);
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 1000);
            }
        }
    };

    poll();
}

// 选择样式
async function selectStyle(styleIndex) {
    try {
        await apiRequest(`/api/ppt/${projectId}/styles/select`, {
            method: 'POST',
            body: JSON.stringify({ style_index: styleIndex })
        });
        showSuccess('样式已选择');
        // 启用生成按钮
        document.getElementById('generate-btn').disabled = false;
    } catch (error) {
        showError('选择样式失败: ' + error.message);
    }
}

// 加载PPT页面
async function loadPages(projectId) {
    try {
        const pages = await apiRequest(`/api/ppt/${projectId}/pages`);
        displayPages(pages);
    } catch (error) {
        console.error('加载PPT页面失败:', error);
    }
}

// 显示PPT页面
function displayPages(pages) {
    const grid = document.getElementById('pages-grid');
    if (!grid) return;

    if (pages.length === 0) {
        grid.innerHTML = '<p class="text-muted">选择样式后点击"开始生成"按钮</p>';
        return;
    }

    grid.innerHTML = pages.map(page => `
        <div class="card">
            <div class="mb-sm text-muted text-sm">第 ${page.page_number} 页</div>
            ${page.image_path ?
                `<img src="${page.image_path}" alt="第 ${page.page_number} 页" style="width: 100%; height: auto;">` :
                `<div style="width: 100%; height: 200px; background: var(--color-gray-50); display: flex; align-items: center; justify-content: center;">
                    <span class="text-muted">${getPageStatusText(page.status)}</span>
                </div>`
            }
            ${page.status === 'completed' ?
                `<div class="mt-sm">
                    <button class="btn btn-sm" onclick="regeneratePage(${page.page_number})">重新生成</button>
                </div>` : ''
            }
            ${page.status === 'failed' ?
                `<div class="mt-sm">
                    <p class="text-muted text-sm">错误: ${page.error_message}</p>
                    <button class="btn btn-sm" onclick="regeneratePage(${page.page_number})">重试</button>
                </div>` : ''
            }
        </div>
    `).join('');

    // 检查是否全部完成
    const allCompleted = pages.every(p => p.status === 'completed');
    if (allCompleted) {
        document.getElementById('download-btn').disabled = false;
    }
}

// 获取页面状态文本
function getPageStatusText(status) {
    const statusMap = {
        'pending': '等待生成',
        'generating': '生成中...',
        'completed': '已完成',
        'failed': '生成失败'
    };
    return statusMap[status] || status;
}

// 开始生成PPT
async function startGeneration() {
    if (!confirm('开始生成PPT页面，这可能需要较长时间，确定吗？')) return;

    try {
        // 启动生成任务
        await apiRequest(`/api/ppt/${projectId}/pages/generate`, {
            method: 'POST'
        });

        // 显示进度条
        document.getElementById('progress-section').classList.remove('hidden');
        document.getElementById('generate-btn').disabled = true;

        // 开始监听进度
        listenProgress();
    } catch (error) {
        showError('启动生成失败: ' + error.message);
    }
}

// 监听生成进度（SSE）
function listenProgress() {
    const eventSource = new EventSource(`/api/ppt/${projectId}/pages/status`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
            showError('生成过程出错: ' + data.error);
            eventSource.close();
            return;
        }

        // 更新进度条
        const progress = (data.current_page / data.total_pages) * 100;
        document.getElementById('progress-bar').style.width = progress + '%';
        document.getElementById('progress-text').textContent =
            `正在生成第 ${data.current_page} / ${data.total_pages} 页`;

        // 刷新页面显示
        loadPages(projectId);

        // 如果完成或失败，关闭连接
        if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close();
            document.getElementById('progress-text').textContent =
                data.status === 'completed' ? '生成完成！' : '生成失败';

            if (data.status === 'completed') {
                showSuccess('PPT生成完成！');
                document.getElementById('download-btn').disabled = false;
            }
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error);
        eventSource.close();
    };
}

// 重新生成单页
async function regeneratePage(pageNumber) {
    if (!confirm(`确定要重新生成第 ${pageNumber} 页吗？`)) return;

    try {
        await apiRequest(`/api/ppt/${projectId}/pages/${pageNumber}/regenerate`, {
            method: 'POST'
        });
        showSuccess('重新生成成功');
        await loadPages(projectId);
    } catch (error) {
        showError('重新生成失败: ' + error.message);
    }
}

// 下载PPT
function downloadPPT() {
    window.location.href = `/api/ppt/${projectId}/pages/download`;
}
