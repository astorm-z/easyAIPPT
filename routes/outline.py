"""大纲相关路由"""
from flask import Blueprint, request, jsonify, render_template
from database.db_manager import DBManager
from services.gemini_service import GeminiService

outline_bp = Blueprint('outline', __name__)


def init_routes(db_manager: DBManager, gemini_service: GeminiService):
    """初始化路由"""

    @outline_bp.route('/api/ppt/<int:project_id>/outline/generate', methods=['POST'])
    def generate_outline(project_id):
        """生成PPT大纲"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取知识库文本
            knowledge_text = db_manager.get_workspace_knowledge_text(project['workspace_id'])

            # 调用Gemini生成大纲
            outline_data = gemini_service.generate_outline(
                knowledge_text,
                project['user_prompt'],
                project['expected_pages']
            )

            # 删除旧大纲
            db_manager.delete_outline_pages(project_id)

            # 保存新大纲
            for page in outline_data['pages']:
                db_manager.add_outline_page(
                    project_id,
                    page['page_number'],
                    page['title'],
                    page['content'],
                    page.get('image_prompt', '')
                )

            # 更新项目状态
            db_manager.update_ppt_project_status(project_id, 'outline_generated')

            return jsonify({'success': True, 'data': outline_data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @outline_bp.route('/api/ppt/<int:project_id>/outline', methods=['GET'])
    def get_outline(project_id):
        """获取大纲"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            pages = db_manager.get_outline_pages(project_id)
            return jsonify({'success': True, 'data': pages})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @outline_bp.route('/api/ppt/<int:project_id>/outline/<int:page_number>', methods=['PUT'])
    def update_outline_page(project_id, page_number):
        """更新单页大纲"""
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            image_prompt = data.get('image_prompt', '').strip()

            if not title or not content:
                return jsonify({'success': False, 'error': '标题和内容不能为空'}), 400

            db_manager.update_outline_page(project_id, page_number, title, content, image_prompt)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @outline_bp.route('/api/ppt/<int:project_id>/outline/<int:page_number>/regenerate', methods=['POST'])
    def regenerate_outline_page(project_id, page_number):
        """重新生成单页大纲"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取知识库文本
            knowledge_text = db_manager.get_workspace_knowledge_text(project['workspace_id'])

            # 获取当前大纲
            pages = db_manager.get_outline_pages(project_id)
            current_page = next((p for p in pages if p['page_number'] == page_number), None)

            if not current_page:
                return jsonify({'success': False, 'error': '页面不存在'}), 404

            # 调用Gemini重新生成该页
            new_page_data = gemini_service.regenerate_outline_page(
                knowledge_text,
                project['user_prompt'],
                page_number,
                pages
            )

            # 更新大纲
            db_manager.update_outline_page(
                project_id,
                page_number,
                new_page_data['title'],
                new_page_data['content'],
                new_page_data.get('image_prompt', '')
            )

            return jsonify({'success': True, 'data': new_page_data})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @outline_bp.route('/outline/<int:project_id>')
    def outline_page(project_id):
        """大纲编辑页"""
        return render_template('outline.html', project_id=project_id)

    return outline_bp
