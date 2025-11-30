// 大纲编辑

// 加载项目信息
async function loadProjectInfo(projectId) {
    try {
        const project = await apiRequest(`/api/ppt/${projectId}`);
        document.getElementById('ppt-title').textContent = project.title;
        document.getElementById('ppt-prompt').textContent = project.user_prompt;
    } catch (error) {
        console.error('加载项目信息失败:', error);
    }
}

// 加载大纲
async function loadOutline(projectId) {
    try {
        const pages = await apiRequest(`/api/ppt/${projectId}/outline`);
        if (pages.length === 0) {
            // 如果没有大纲，自动生成
            await generateOutline();
        } else {
            displayOutline(pages);
        }
    } catch (error) {
        console.error('加载大纲失败:', error);
    }
}

// 显示大纲
function displayOutline(pages) {
    const list = document.getElementById('outline-list');
    if (!list) return;

    list.innerHTML = pages.map(page => `
        <div class="card">
            <div class="mb-sm">
                <span class="text-muted">第 ${page.page_number} 页</span>
            </div>
            <h3 class="card-title">${escapeHtml(page.title)}</h3>
            <p class="card-content">${escapeHtml(page.content)}</p>
            ${page.image_prompt ? `<p class="text-muted text-sm mt-sm">图片提示: ${escapeHtml(page.image_prompt)}</p>` : ''}
            <div class="mt-md">
                <button class="btn btn-sm"
                    data-page-number="${page.page_number}"
                    data-title="${escapeHtml(page.title)}"
                    data-content="${escapeHtml(page.content)}"
                    data-image-prompt="${escapeHtml(page.image_prompt || '')}"
                    onclick="editOutlinePageFromButton(this)">编辑</button>
                <button class="btn btn-sm" onclick="regenerateOutlinePage(${page.page_number})">重新生成</button>
            </div>
        </div>
    `).join('');
}

// 转义HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// 反转义HTML
function unescapeHtml(text) {
    const div = document.createElement('div');
    div.innerHTML = text;
    return div.textContent;
}

// 生成大纲（先显示提示词）
async function generateOutline() {
    try {
        // 获取提示词
        const promptData = await apiRequest(`/api/ppt/${projectId}/outline/prompt`);

        // 显示提示词编辑模态框
        document.getElementById('generate-prompt-text').value = promptData.prompt;
        showModal('generate-prompt-modal');
    } catch (error) {
        showError('获取提示词失败: ' + error.message);
    }
}

// 确认生成大纲
async function confirmGenerateOutline(event) {
    event.preventDefault();

    const customPrompt = document.getElementById('generate-prompt-text').value;

    // 隐藏模态框
    hideGeneratePromptModal();

    // 显示加载状态
    showLoading('loading');

    try {
        await apiRequest(`/api/ppt/${projectId}/outline/generate`, {
            method: 'POST',
            body: JSON.stringify({ custom_prompt: customPrompt })
        });
        showSuccess('大纲生成成功');
        await loadOutline(projectId);
    } catch (error) {
        showError('大纲生成失败: ' + error.message);
    } finally {
        hideLoading('loading');
    }
}

// 隐藏生成提示词模态框
function hideGeneratePromptModal() {
    hideModal('generate-prompt-modal');
}

// 重新生成大纲
async function regenerateOutline() {
    const confirmed = await showConfirm('确定要重新生成整个大纲吗？', '重新生成大纲');
    if (!confirmed) return;
    await generateOutline();
}

// 从按钮元素读取数据并编辑大纲页
function editOutlinePageFromButton(button) {
    const pageNumber = button.dataset.pageNumber;
    const title = unescapeHtml(button.dataset.title);
    const content = unescapeHtml(button.dataset.content);
    const imagePrompt = unescapeHtml(button.dataset.imagePrompt);
    editOutlinePage(pageNumber, title, content, imagePrompt);
}

// 编辑大纲页
function editOutlinePage(pageNumber, title, content, imagePrompt) {
    document.getElementById('edit-page-number').value = pageNumber;
    document.getElementById('edit-title').value = title;
    document.getElementById('edit-content').value = content;
    document.getElementById('edit-prompt').value = imagePrompt;
    showModal('edit-modal');
}

// 隐藏编辑模态框
function hideEditModal() {
    hideModal('edit-modal');
    document.getElementById('edit-form').reset();
}

// 保存大纲页
async function saveOutlinePage(event) {
    event.preventDefault();
    const form = event.target;
    const pageNumber = document.getElementById('edit-page-number').value;

    try {
        await apiRequest(`/api/ppt/${projectId}/outline/${pageNumber}`, {
            method: 'PUT',
            body: JSON.stringify({
                title: document.getElementById('edit-title').value,
                content: document.getElementById('edit-content').value,
                image_prompt: document.getElementById('edit-prompt').value
            })
        });

        showSuccess('保存成功');
        hideEditModal();
        await loadOutline(projectId);
    } catch (error) {
        showError('保存失败: ' + error.message);
    }
}

// 重新生成单页大纲（显示额外提示词输入框）
async function regenerateOutlinePage(pageNumber) {
    // 显示重新生成提示词模态框
    document.getElementById('regenerate-page-number').value = pageNumber;
    document.getElementById('regenerate-extra-prompt').value = '';
    showModal('regenerate-prompt-modal');
}

// 确认重新生成单页大纲
async function confirmRegenerateOutlinePage(event) {
    event.preventDefault();

    const pageNumber = document.getElementById('regenerate-page-number').value;
    const extraPrompt = document.getElementById('regenerate-extra-prompt').value.trim();

    // 隐藏模态框
    hideRegeneratePromptModal();

    try {
        const body = extraPrompt ? { extra_prompt: extraPrompt } : {};
        await apiRequest(`/api/ppt/${projectId}/outline/${pageNumber}/regenerate`, {
            method: 'POST',
            body: JSON.stringify(body)
        });
        showSuccess('重新生成成功');
        await loadOutline(projectId);
    } catch (error) {
        showError('重新生成失败: ' + error.message);
    }
}

// 隐藏重新生成提示词模态框
function hideRegeneratePromptModal() {
    hideModal('regenerate-prompt-modal');
}

// 确认大纲
async function confirmOutline() {
    const confirmed = await showConfirm('确认大纲后将进入样式选择和PPT生成阶段，确定吗？', '确认大纲');
    if (!confirmed) return;

    try {
        // 调用确认大纲接口（不会重新生成，只更新状态）
        await apiRequest(`/api/ppt/${projectId}/outline/confirm`, {
            method: 'POST'
        });
        showSuccess('大纲已确认');
        window.location.href = `/ppt/${projectId}`;
    } catch (error) {
        showError('确认失败: ' + error.message);
    }
}
