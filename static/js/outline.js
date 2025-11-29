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
            <h3 class="card-title">${page.title}</h3>
            <p class="card-content">${page.content}</p>
            ${page.image_prompt ? `<p class="text-muted text-sm mt-sm">图片提示: ${page.image_prompt}</p>` : ''}
            <div class="mt-md">
                <button class="btn btn-sm" onclick="editOutlinePage(${page.page_number}, '${escapeHtml(page.title)}', '${escapeHtml(page.content)}', '${escapeHtml(page.image_prompt || '')}')">编辑</button>
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

// 生成大纲
async function generateOutline() {
    showLoading('loading');
    try {
        await apiRequest(`/api/ppt/${projectId}/outline/generate`, {
            method: 'POST'
        });
        showSuccess('大纲生成成功');
        await loadOutline(projectId);
    } catch (error) {
        showError('大纲生成失败: ' + error.message);
    } finally {
        hideLoading('loading');
    }
}

// 重新生成大纲
async function regenerateOutline() {
    if (!confirm('确定要重新生成整个大纲吗？')) return;
    await generateOutline();
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

// 重新生成单页大纲
async function regenerateOutlinePage(pageNumber) {
    if (!confirm(`确定要重新生成第 ${pageNumber} 页吗？`)) return;

    try {
        await apiRequest(`/api/ppt/${projectId}/outline/${pageNumber}/regenerate`, {
            method: 'POST'
        });
        showSuccess('重新生成成功');
        await loadOutline(projectId);
    } catch (error) {
        showError('重新生成失败: ' + error.message);
    }
}

// 确认大纲
async function confirmOutline() {
    if (!confirm('确认大纲后将进入样式选择和PPT生成阶段，确定吗？')) return;

    try {
        // 更新项目状态
        await apiRequest(`/api/ppt/${projectId}/outline/generate`, {
            method: 'POST'
        });
        showSuccess('大纲已确认');
        window.location.href = `/ppt/${projectId}`;
    } catch (error) {
        showError('确认失败: ' + error.message);
    }
}
