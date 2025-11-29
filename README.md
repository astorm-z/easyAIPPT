# EasyAIPPT - AI驱动的PPT生成网站

通过AI自动生成专业PPT的Web应用，支持上传文档构建知识库，自动生成大纲，并逐页生成精美的PPT图片。

## 功能特性

- **工作空间管理**：创建多个独立的工作空间，互不干扰
- **知识库构建**：支持上传txt、pdf、doc、docx文档和常见图片格式
- **智能大纲生成**：基于Gemini 3 Pro模型，根据知识库和用户需求自动生成PPT大纲
- **大纲编辑**：支持手动编辑、单页重新生成或全部重新生成
- **样式模板选择**：自动生成3种PPT样式模板供用户选择
- **逐页生成PPT**：使用Nano Banana Pro模型逐页生成PPT图片，实时显示进度
- **灵活管理**：支持单页重新生成、一键下载所有PPT图片
- **极简UI设计**：采用极简主义设计风格，界面优雅纯粹

## 技术栈

- **后端**：Flask (Python 3.13)
- **前端**：纯HTML + CSS + JavaScript
- **数据库**：SQLite
- **文件存储**：本地文件系统
- **AI模型**：
  - Gemini 1.5 Pro（大纲生成）
  - Gemini 2.0 Flash（图片生成）

## 项目结构

```
easyAIPPT/
├── app.py                      # Flask主应用入口
├── config.py                   # 配置文件加载
├── .env                        # 环境变量（需自行创建）
├── requirements.txt            # Python依赖
├── database/                   # 数据库模块
│   ├── models.py              # 数据库模型定义
│   └── db_manager.py          # 数据库操作封装
├── services/                   # 服务层
│   ├── file_processor.py      # 文件处理服务
│   ├── gemini_service.py      # Gemini API调用
│   ├── banana_service.py      # Banana API调用
│   └── ppt_generator.py       # PPT生成流程控制
├── routes/                     # 路由模块
│   ├── workspace.py           # 工作空间路由
│   ├── knowledge.py           # 知识库路由
│   ├── outline.py             # 大纲路由
│   └── ppt.py                 # PPT生成路由
├── prompts/                    # AI提示词
│   ├── outline_generation.txt # 大纲生成提示词
│   ├── style_template.txt     # 样式模板提示词
│   └── page_generation.txt    # 页面生成提示词
├── static/                     # 静态资源
│   ├── css/style.css          # 极简风格样式
│   └── js/                    # JavaScript文件
├── templates/                  # HTML模板
└── uploads/                    # 用户上传文件（自动创建）
```

## 安装步骤

### 1. 克隆项目

```bash
cd /mnt/c/E/git/easyAIPPT
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写API密钥：

```env
# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# 注意：图片生成也使用Gemini API（gemini-2.0-flash-exp模型）
# 只需要配置一个Gemini API密钥即可

# Flask应用配置
FLASK_SECRET_KEY=your_secret_key_here
FLASK_DEBUG=True

# 数据库配置
DATABASE_PATH=./database/easyaippt.db

# 文件存储配置
UPLOAD_FOLDER=./uploads
GENERATED_FOLDER=./generated
MAX_UPLOAD_SIZE=50
```

### 5. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 使用流程

1. **创建工作空间**
   - 访问首页，点击"创建工作空间"
   - 输入工作空间名称和描述

2. **构建知识库**
   - 进入工作空间
   - 上传txt、pdf、doc、docx文档或图片
   - 系统会自动提取文本内容

3. **创建PPT项目**
   - 点击"创建PPT"
   - 输入PPT标题、内容描述和预期页数
   - 系统会自动跳转到大纲编辑页

4. **编辑大纲**
   - 查看AI生成的PPT大纲
   - 可以手动编辑每一页
   - 可以重新生成单页或全部大纲
   - 确认大纲后进入下一步

5. **选择样式**
   - 点击"生成样式模板"
   - 从3个样式模板中选择一个
   - 点击"开始生成"

6. **生成PPT**
   - 系统会逐页生成PPT图片
   - 实时显示生成进度
   - 可以重新生成任意一页
   - 全部完成后点击"下载PPT"

## 注意事项

1. **API密钥**：请确保正确配置Gemini和Banana的API密钥
2. **文件大小**：默认最大上传文件大小为50MB，可在.env中调整
3. **生成时间**：PPT生成需要较长时间，请耐心等待
4. **错误重试**：API调用失败会自动重试最多10次
5. **提示词调整**：可以根据需要修改prompts目录下的提示词文件

## 提示词说明

项目中的所有AI提示词都存储在 `prompts/` 目录下的txt文件中：

- `outline_generation.txt`：控制PPT大纲的生成逻辑
- `style_template.txt`：控制样式模板的生成风格
- `page_generation.txt`：控制单页PPT的生成效果

您可以根据实际需求修改这些提示词，以获得更符合期望的生成结果。

## API说明

### Gemini API集成

项目使用Google Gemini API进行AI功能：

- **大纲生成**：使用 `gemini-1.5-pro` 模型
- **图片生成**：使用 `gemini-2.0-flash-exp` 模型

如果Gemini图片生成功能不可用，系统会自动创建占位图片，确保流程可以正常测试。

配置方法：
1. 获取Gemini API密钥：https://makersuite.google.com/app/apikey
2. 在 `.env` 文件中配置 `GEMINI_API_KEY`

## 开发说明

### 添加新功能

1. 在对应的模块中添加代码
2. 更新路由和API端点
3. 更新前端页面和JavaScript
4. 测试功能是否正常

### 数据库修改

如需修改数据库结构：

1. 编辑 `database/models.py` 中的表定义
2. 删除现有数据库文件
3. 重新运行应用，数据库会自动重建

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
