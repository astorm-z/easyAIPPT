"""文件处理服务"""
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import PyPDF2
import docx


class FileProcessor:
    """文件处理器"""

    def __init__(self, config):
        self.config = config

    def allowed_file(self, filename):
        """检查文件类型是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.ALLOWED_EXTENSIONS

    def get_file_type(self, filename):
        """获取文件类型"""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext in ['txt']:
            return 'txt'
        elif ext in ['pdf']:
            return 'pdf'
        elif ext in ['doc', 'docx']:
            return 'docx'
        elif ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
            return 'image'
        return 'unknown'

    def extract_text_from_txt(self, file_path):
        """从txt文件提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()

    def extract_text_from_pdf(self, file_path):
        """从PDF文件提取文本"""
        try:
            text = ''
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
            return text.strip()
        except Exception as e:
            return f'[PDF文本提取失败: {str(e)}]'

    def extract_text_from_docx(self, file_path):
        """从DOCX文件提取文本"""
        try:
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            return f'[DOCX文本提取失败: {str(e)}]'

    def process_image(self, file_path):
        """处理图片文件"""
        try:
            # 验证图片
            img = Image.open(file_path)
            img.verify()
            return f'[图片文件: {os.path.basename(file_path)}]'
        except Exception as e:
            return f'[图片处理失败: {str(e)}]'

    def extract_text(self, file_path, file_type):
        """根据文件类型提取文本"""
        if file_type == 'txt':
            return self.extract_text_from_txt(file_path)
        elif file_type == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            return self.extract_text_from_docx(file_path)
        elif file_type == 'image':
            return self.process_image(file_path)
        return ''

    def process_uploaded_file(self, file, workspace_id, db_manager):
        """处理上传的文件"""
        try:
            # 检查文件名
            if not file.filename:
                return {'success': False, 'error': '文件名为空'}

            # 检查文件类型
            if not self.allowed_file(file.filename):
                return {'success': False, 'error': f'不支持的文件类型: {file.filename}'}

            # 保存原始文件名
            original_filename = file.filename

            # 获取文件扩展名
            _, ext = os.path.splitext(original_filename)
            file_type = self.get_file_type(original_filename)

            # 使用UUID生成唯一文件名，避免冲突和中文问题
            unique_filename = f"{uuid.uuid4().hex}{ext}"

            # 创建工作空间目录
            workspace_dir = os.path.join(self.config.UPLOAD_FOLDER, f'workspace_{workspace_id}', 'knowledge')
            os.makedirs(workspace_dir, exist_ok=True)

            # 保存文件
            file_path = os.path.join(workspace_dir, unique_filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            # 提取文本
            extracted_text = self.extract_text(file_path, file_type)

            # 保存到数据库
            file_id = db_manager.add_knowledge_file(
                workspace_id,
                unique_filename,
                file_type,
                file_path,
                file_size,
                extracted_text,
                original_filename
            )

            return {
                'success': True,
                'data': {
                    'id': file_id,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_type': file_type,
                    'file_size': file_size
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
