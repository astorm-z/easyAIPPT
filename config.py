"""配置文件加载模块"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Gemini API配置
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_API_BASE_URL = os.getenv('GEMINI_API_BASE_URL', 'https://generativelanguage.googleapis.com')

    # Banana (图片生成) API配置
    # 图片生成也使用Gemini API（gemini-3-pro-image-preview模型）
    BANANA_API_KEY = os.getenv('BANANA_API_KEY') or os.getenv('GEMINI_API_KEY')  # 优先使用独立key，否则使用Gemini key
    BANANA_API_BASE_URL = os.getenv('BANANA_API_BASE_URL', 'https://generativelanguage.googleapis.com')
    BANANA_MODEL = os.getenv('BANANA_MODEL', 'gemini-3-pro-image-preview')

    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', './database/easyaippt.db')

    # 文件存储配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    GENERATED_FOLDER = os.getenv('GENERATED_FOLDER', './generated')
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '50')) * 1024 * 1024  # 转换为字节

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx',
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'
    }

    # API重试配置
    MAX_API_RETRIES = 10
    RETRY_DELAY_BASE = 2  # 指数退避的基数（秒）
    API_TIMEOUT = 60  # API调用超时时间（秒）

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.GENERATED_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
