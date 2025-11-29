// 工作空间管理

// 加载所有工作空间
async function loadWorkspaces() {
    showLoading('loading');
    try {
        const workspaces = await apiRequest('/api/workspaces');
        displayWorkspaces(workspaces);
    } catch (error) {
        console.error('加载工作空间失败:', error);
    } finally {
        hideLoading('loading');
    }
}

// 显示工作空间列表
function displayWorkspaces(workspaces) {
    const grid = document.getElementById('workspaces-grid');
    if (!grid) return;

    if (workspaces.length === 0) {
        grid.innerHTML = '<p class="text-center text-muted">暂无工作空间，点击上方按钮创建</p>';
        return;
    }

    grid.innerHTML = workspaces.map(ws => `
        <div class="card">
            <h3 class="card-title">${ws.name}</h3>
            <p class="card-content">${ws.description || '暂无描述'}</p>
            <div class="mt-md">
                <a href="/workspace/${ws.id}" class="btn">进入</a>
            </div>
        </div>
    `).join('');
}

// 显示创建工作空间模态框
function showCreateModal() {
    showModal('create-modal');
}

// 隐藏创建工作空间模态框
function hideCreateModal() {
    hideModal('create-modal');
    document.getElementById('create-form').reset();
}

// 创建工作空间
async function createWorkspace(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const data = await apiRequest('/api/workspaces', {
            method: 'POST',
            body: JSON.stringify({
                name: formData.get('name'),
                description: formData.get('description')
            })
        });

        showSuccess('工作空间创建成功');
        hideCreateModal();
        window.location.href = `/workspace/${data.id}`;
    } catch (error) {
        console.error('创建工作空间失败:', error);
    }
}

// 加载工作空间详情
async function loadWorkspaceDetail(workspaceId) {
    try {
        const workspace = await apiRequest(`/api/workspaces/${workspaceId}`);
        document.getElementById('workspace-title').textContent = workspace.name;
        document.getElementById('workspace-desc').textContent = workspace.description || '';
    } catch (error) {
        console.error('加载工作空间详情失败:', error);
    }
}

// 加载知识库文件
async function loadKnowledgeFiles(workspaceId) {
    try {
        const files = await apiRequest(`/api/workspaces/${workspaceId}/knowledge`);
        displayKnowledgeFiles(files);
    } catch (error) {
        console.error('加载知识库文件失败:', error);
    }
}

// 显示知识库文件列表
function displayKnowledgeFiles(files) {
    const list = document.getElementById('knowledge-list');
    if (!list) return;

    if (files.length === 0) {
        list.innerHTML = '<p class="text-muted text-sm">暂无文件</p>';
        return;
    }

    list.innerHTML = files.map(file => `
        <div class="list-item">
            <div>
                <div>${file.filename}</div>
                <div class="text-muted text-sm">${formatFileSize(file.file_size)}</div>
            </div>
            <button class="btn btn-sm" onclick="deleteKnowledgeFile(${file.id})">删除</button>
        </div>
    `).join('');
}

// 上传文件
async function uploadFiles() {
    const input = document.getElementById('file-input');
    const files = input.files;

    if (files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        await fetch(`/api/workspaces/${workspaceId}/knowledge/upload`, {
            method: 'POST',
            body: formData
        }).then(res => res.json()).then(data => {
            if (!data.success) throw new Error(data.error);
            showSuccess('文件上传成功');
            loadKnowledgeFiles(workspaceId);
            input.value = '';
        });
    } catch (error) {
        showError(error.message);
    }
}

// 删除知识库文件
async function deleteKnowledgeFile(fileId) {
    if (!confirm('确定要删除这个文件吗？')) return;

    try {
        await apiRequest(`/api/knowledge/${fileId}`, { method: 'DELETE' });
        showSuccess('文件删除成功');
        loadKnowledgeFiles(workspaceId);
    } catch (error) {
        console.error('删除文件失败:', error);
    }
}

// 加载PPT项目列表
async function loadPPTProjects(workspaceId) {
    try {
        const projects = await apiRequest(`/api/workspaces/${workspaceId}/ppt/create`.replace('/create', ''));
        // 注意：这里需要调整API路径
        displayPPTProjects(projects);
    } catch (error) {
        console.error('加载PPT项目失败:', error);
    }
}

// 显示PPT项目列表
function displayPPTProjects(projects) {
    const list = document.getElementById('ppt-list');
    if (!list) return;

    if (projects.length === 0) {
        list.innerHTML = '<p class="text-muted text-sm">暂无PPT项目</p>';
        return;
    }

    list.innerHTML = projects.map(project => `
        <div class="card">
            <h4 class="card-title">${project.title}</h4>
            <p class="text-muted text-sm">状态: ${getStatusText(project.status)}</p>
            <div class="mt-md">
                ${getProjectButtons(project)}
            </div>
        </div>
    `).join('');
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'draft': '草稿',
        'outline_generated': '大纲已生成',
        'style_selected': '样式已选择',
        'generating': '生成中',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

// 获取项目操作按钮
function getProjectButtons(project) {
    if (project.status === 'draft') {
        return `<a href="/outline/${project.id}" class="btn">编辑大纲</a>`;
    } else if (project.status === 'outline_generated' || project.status === 'style_selected' || project.status === 'generating' || project.status === 'completed') {
        return `<a href="/ppt/${project.id}" class="btn">查看PPT</a>`;
    }
    return '';
}

// 显示创建PPT模态框
function showCreatePPTModal() {
    showModal('create-ppt-modal');
}

// 隐藏创建PPT模态框
function hideCreatePPTModal() {
    hideModal('create-ppt-modal');
    document.getElementById('create-ppt-form').reset();
}

// 创建PPT项目
async function createPPT(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const data = await apiRequest(`/api/workspaces/${workspaceId}/ppt/create`, {
            method: 'POST',
            body: JSON.stringify({
                title: formData.get('title'),
                user_prompt: formData.get('user_prompt'),
                expected_pages: parseInt(formData.get('expected_pages'))
            })
        });

        showSuccess('PPT项目创建成功');
        hideCreatePPTModal();
        window.location.href = `/outline/${data.id}`;
    } catch (error) {
        console.error('创建PPT项目失败:', error);
    }
}
