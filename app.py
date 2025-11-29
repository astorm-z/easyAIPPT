"""Flask主应用入口"""
from flask import Flask
from config import Config
from database.models import Database
from database.db_manager import DBManager
from services.file_processor import FileProcessor
from services.gemini_service import GeminiService
from services.banana_service import BananaService
from services.ppt_generator import PPTGenerator

# 导入路由
from routes.workspace import init_routes as init_workspace_routes
from routes.knowledge import init_routes as init_knowledge_routes
from routes.outline import init_routes as init_outline_routes
from routes.ppt import init_routes as init_ppt_routes


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化配置
    Config.init_app(app)

    # 初始化数据库
    db = Database(Config.DATABASE_PATH)
    db_manager = DBManager(db)

    # 初始化服务
    file_processor = FileProcessor(Config)
    gemini_service = GeminiService(Config)
    banana_service = BananaService(Config)
    ppt_generator = PPTGenerator(Config, db_manager, banana_service)

    # 注册路由蓝图
    workspace_bp = init_workspace_routes(db_manager)
    app.register_blueprint(workspace_bp)

    knowledge_bp = init_knowledge_routes(db_manager, file_processor)
    app.register_blueprint(knowledge_bp)

    outline_bp = init_outline_routes(db_manager, gemini_service)
    app.register_blueprint(outline_bp)

    ppt_bp_instance = init_ppt_routes(db_manager, banana_service, ppt_generator)
    app.register_blueprint(ppt_bp_instance)

    # 设置最大上传文件大小
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
