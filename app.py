"""Flask主应用入口"""
import logging
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

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    logger.info("正在初始化Flask应用...")

    # 初始化配置
    Config.init_app(app)
    logger.info("配置初始化完成")

    # 初始化数据库
    db = Database(Config.DATABASE_PATH)
    db_manager = DBManager(db)
    logger.info("数据库初始化完成")

    # 初始化服务
    file_processor = FileProcessor(Config)
    gemini_service = GeminiService(Config)
    banana_service = BananaService(Config)
    ppt_generator = PPTGenerator(Config, db_manager, banana_service)
    logger.info("服务层初始化完成")

    # 恢复未完成的生成任务
    logger.info("检查是否有未完成的生成任务...")
    try:
        # 查找所有状态为generating的项目
        all_workspaces = db_manager.get_all_workspaces()
        for workspace in all_workspaces:
            projects = db_manager.get_ppt_projects(workspace['id'])
            for project in projects:
                if project['status'] == 'generating':
                    logger.info(f"发现未完成的项目: {project['id']} - {project['title']}")
                    ppt_generator.resume_generation(project['id'])
    except Exception as e:
        logger.error(f"恢复生成任务失败: {str(e)}")

    # 注册路由蓝图
    workspace_bp = init_workspace_routes(db_manager)
    app.register_blueprint(workspace_bp)

    knowledge_bp = init_knowledge_routes(db_manager, file_processor)
    app.register_blueprint(knowledge_bp)

    outline_bp = init_outline_routes(db_manager, gemini_service)
    app.register_blueprint(outline_bp)

    ppt_bp_instance = init_ppt_routes(db_manager, banana_service, ppt_generator)
    app.register_blueprint(ppt_bp_instance)
    logger.info("路由注册完成")

    # 设置最大上传文件大小
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE

    # 添加静态文件路由，用于访问生成的图片
    from flask import send_from_directory

    @app.route('/generated/<path:filename>')
    def serve_generated_file(filename):
        """提供生成的文件访问"""
        return send_from_directory(Config.GENERATED_FOLDER, filename)

    @app.route('/uploads/<path:filename>')
    def serve_upload_file(filename):
        """提供上传的文件访问"""
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    logger.info("Flask应用初始化完成")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"启动Flask应用 - Debug模式: {Config.DEBUG}")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
