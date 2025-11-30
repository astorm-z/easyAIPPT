// PPT生成和进度管理

// 加载项目信息
// 全局变量存储项目信息
let currentProject = null;

async function loadProjectInfo(projectId) {
    try {
        const project = await apiRequest(`/api/ppt/${projectId}`);
        currentProject = project;
        document.getElementById('ppt-title').textContent = project.title;
    } catch (error) {
        console.error('加载项目信息失败:', error);
    }
}

// 加载样式模板
async function loadStyles(projectId, silent = false) {
    try {
        // 如果是静默模式（轮询调用），使用静默版本的API请求
        const styles = silent
            ? await apiRequestSilent(`/api/ppt/${projectId}/styles`)
            : await apiRequest(`/api/ppt/${projectId}/styles`);
        displayStyles(styles);
    } catch (error) {
        console.error('加载样式模板失败:', error);
        // 静默模式下不需要额外处理，因为 apiRequest 已经会显示错误
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

    // 获取当前选中的样式索引
    const selectedIndex = currentProject?.selected_style_index;

    grid.innerHTML = styles.map(style => {
        // 转换文件路径为URL路径
        const imageUrl = convertPathToUrl(style.image_path);
        const isSelected = selectedIndex === style.template_index;

        return `
            <div class="card ${isSelected ? 'card-selected' : ''}" data-style-index="${style.template_index}">
                <img src="${imageUrl}"
                     alt="样式 ${style.template_index + 1}"
                     style="width: 100%; height: auto; cursor: pointer;"
                     onclick="viewStyleImage('${imageUrl}', ${style.template_index})"
                     title="点击查看大图">
                <div class="mt-sm text-center">
                    <button class="btn btn-sm ${isSelected ? 'btn-primary' : ''}"
                            onclick="selectStyle(${style.template_index})">
                        ${isSelected ? '✓ 已选择' : '选择此样式'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// 查看样式大图
function viewStyleImage(imageUrl, styleIndex) {
    const modal = document.getElementById('style-image-modal');
    const img = document.getElementById('style-image-large');
    const title = document.getElementById('style-image-title');

    if (modal && img && title) {
        img.src = imageUrl;
        title.textContent = `样式 ${styleIndex + 1}`;
        showModal('style-image-modal');
    }
}

// 关闭样式大图模态框
function closeStyleImageModal() {
    hideModal('style-image-modal');
}

// 转换文件系统路径为URL路径
function convertPathToUrl(filePath) {
    // 移除开头的 ./ 并确保使用正斜杠
    return '/' + filePath.replace(/^\.\//, '').replace(/\\/g, '/');
}

// 生成样式模板
async function generateStyles() {
    // 弹出对话框让用户输入自定义提示词
    const customPrompt = await showPrompt('可选：输入自定义提示词来影响样式生成（留空则使用默认样式）', '', '自定义样式提示词');

    // 用户点击取消则不继续
    if (customPrompt === null) return;

    try {
        // 启动生成任务
        const body = customPrompt.trim() ? { custom_prompt: customPrompt.trim() } : {};
        await apiRequest(`/api/ppt/${projectId}/styles/generate`, {
            method: 'POST',
            body: JSON.stringify(body)
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
    let lastLoadedCount = 0; // 记录上次加载的数量

    const poll = async () => {
        try {
            // 使用静默版本的API请求，避免网络波动时弹窗提示
            const status = await apiRequestSilent(`/api/ppt/${projectId}/styles/status`);

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

            // 实时加载已生成的样式（当有新样式生成时）
            if (status.current > lastLoadedCount && status.status === 'generating') {
                await loadStyles(projectId, true); // 静默模式
                lastLoadedCount = status.current;
            }

            // 检查状态
            if (status.status === 'completed') {
                showSuccess('样式模板生成完成！');
                hideStyleProgress();
                await loadStyles(projectId); // 完成时正常加载
                return;
            } else if (status.status === 'failed') {
                showAlert(`样式模板生成失败: ${status.message}\n\n请点击"生成样式模板"按钮重新生成`, '生成失败');
                hideStyleProgress();
                // 清空样式网格，避免显示旧的样式
                const grid = document.getElementById('styles-grid');
                if (grid) {
                    grid.innerHTML = '<div class="alert alert-warning"><strong>生成失败</strong><p class="mt-sm">样式模板生成失败，请点击上方"生成样式模板"按钮重试</p></div>';
                }
                return;
            }

            // 继续轮询
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 1000); // 每秒轮询一次
            } else {
                showAlert('样式生成超时，请刷新页面查看结果', '超时提示');
                hideStyleProgress();
            }
        } catch (error) {
            // 静默处理错误，只在控制台记录，继续轮询
            console.warn('轮询进度失败（静默处理）:', error);
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 1000);
            } else {
                // 只有在达到最大重试次数后才提示
                showAlert('轮询超时，请刷新页面查看结果', '超时提示');
                hideStyleProgress();
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

        // 更新当前项目的选中样式索引
        if (currentProject) {
            currentProject.selected_style_index = styleIndex;
        }

        // 重新加载样式以更新UI
        await loadStyles(projectId, true);

        // 启用生成按钮
        document.getElementById('generate-btn').disabled = false;
    } catch (error) {
        showError('选择样式失败: ' + error.message);
    }
}

// 加载PPT页面
async function loadPages(projectId, silent = false) {
    try {
        // 如果是静默模式（SSE推送调用），使用静默版本的API请求
        const pages = silent
            ? await apiRequestSilent(`/api/ppt/${projectId}/pages`)
            : await apiRequest(`/api/ppt/${projectId}/pages`);
        displayPages(pages);

        // 检查是否有未完成的页面
        const hasIncomplete = pages.some(p => p.status === 'pending' || p.status === 'failed');
        const hasCompleted = pages.some(p => p.status === 'completed');

        // 如果有已完成的页面但还有未完成的，显示"继续生成"按钮
        if (hasIncomplete && hasCompleted) {
            document.getElementById('resume-btn').style.display = 'inline-block';
            document.getElementById('generate-btn').style.display = 'none';
        }
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

    grid.innerHTML = pages.map(page => {
        // 转换文件路径为URL路径
        const imageUrl = page.image_path ? convertPathToUrl(page.image_path) : null;
        return `
            <div class="card">
                <div class="mb-sm text-muted text-sm">第 ${page.page_number} 页</div>
                ${imageUrl ?
                    `<img src="${imageUrl}"
                          alt="第 ${page.page_number} 页"
                          style="width: 100%; height: auto; cursor: pointer;"
                          onclick="viewPageImage('${imageUrl}', ${page.page_number})"
                          title="点击查看大图">` :
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
        `;
    }).join('');

    // 检查是否全部完成
    const allCompleted = pages.every(p => p.status === 'completed');
    if (allCompleted) {
        document.getElementById('download-btn').disabled = false;
    }
}

// 查看PPT页面大图
function viewPageImage(imageUrl, pageNumber) {
    const modal = document.getElementById('page-image-modal');
    const img = document.getElementById('page-image-large');
    const title = document.getElementById('page-image-title');

    if (modal && img && title) {
        img.src = imageUrl;
        title.textContent = `第 ${pageNumber} 页`;
        showModal('page-image-modal');
    }
}

// 关闭PPT页面大图模态框
function closePageImageModal() {
    hideModal('page-image-modal');
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

// 显示生成提示词
async function showGeneratePrompt() {
    try {
        // 获取所有页面的提示词
        const promptsData = await apiRequest(`/api/ppt/${projectId}/pages/prompts`);

        // 显示提示词列表
        const container = document.getElementById('ppt-prompts-container');
        container.innerHTML = promptsData.map(item => `
            <div class="mb-lg" style="border: 1px solid var(--color-gray-200); border-radius: 4px; padding: var(--spacing-md);">
                <h4 class="mb-sm">第 ${item.page_number} 页: ${escapeHtml(item.title)}</h4>
                <textarea
                    id="prompt-${item.page_number}"
                    data-page-number="${item.page_number}"
                    style="width: 100%; min-height: 200px; font-family: monospace; font-size: 0.85em;"
                >${escapeHtml(item.prompt)}</textarea>
            </div>
        `).join('');

        // 显示模态框
        showModal('generate-ppt-prompt-modal');
    } catch (error) {
        showError('获取提示词失败: ' + error.message);
    }
}

// 隐藏生成PPT提示词模态框
function hideGeneratePPTPromptModal() {
    hideModal('generate-ppt-prompt-modal');
}

// 确认开始生成
async function confirmStartGeneration() {
    // 收集所有修改后的提示词
    const container = document.getElementById('ppt-prompts-container');
    const textareas = container.querySelectorAll('textarea[data-page-number]');

    const customPrompts = Array.from(textareas).map(textarea => ({
        page_number: parseInt(textarea.dataset.pageNumber),
        prompt: textarea.value
    }));

    // 隐藏模态框
    hideGeneratePPTPromptModal();

    try {
        // 启动生成任务
        await apiRequest(`/api/ppt/${projectId}/pages/generate`, {
            method: 'POST',
            body: JSON.stringify({ custom_prompts: customPrompts })
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

// 转义HTML（如果main.js中没有定义）
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 开始生成PPT（保留旧函数名以兼容）
async function startGeneration() {
    await showGeneratePrompt();
}

// 监听生成进度（SSE）
function listenProgress() {
    const eventSource = new EventSource(`/api/ppt/${projectId}/pages/status`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
            showAlert('生成过程出错: ' + data.error, '生成错误');
            eventSource.close();
            return;
        }

        // 更新进度条
        const progress = (data.current_page / data.total_pages) * 100;
        document.getElementById('progress-bar').style.width = progress + '%';
        document.getElementById('progress-text').textContent =
            `正在生成第 ${data.current_page} / ${data.total_pages} 页`;

        // 刷新页面显示（静默模式，避免网络波动时弹窗）
        loadPages(projectId, true);

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
    // 弹出对话框让用户输入自定义提示词
    const customPrompt = await showPrompt(`可选：输入自定义提示词来影响第 ${pageNumber} 页的生成（留空则使用默认提示词）`, '', `自定义第 ${pageNumber} 页提示词`);

    // 用户点击取消则不继续
    if (customPrompt === null) return;

    try {
        const body = customPrompt.trim() ? { custom_prompt: customPrompt.trim() } : {};
        await apiRequest(`/api/ppt/${projectId}/pages/${pageNumber}/regenerate`, {
            method: 'POST',
            body: JSON.stringify(body)
        });
        showSuccess('重新生成成功');
        await loadPages(projectId);
    } catch (error) {
        showError('重新生成失败: ' + error.message);
    }
}

// 恢复生成
async function resumeGeneration() {
    const confirmed = await showConfirm('继续生成未完成的PPT页面？', '继续生成');
    if (!confirmed) return;

    try {
        await apiRequest(`/api/ppt/${projectId}/pages/resume`, {
            method: 'POST'
        });

        // 显示进度区域
        document.getElementById('progress-section').classList.remove('hidden');
        document.getElementById('resume-btn').style.display = 'none';

        // 开始监听进度
        listenProgress();
    } catch (error) {
        showError('恢复生成失败: ' + error.message);
    }
}

// 下载PPT
function downloadPPT() {
    window.location.href = `/api/ppt/${projectId}/pages/download`;
}
