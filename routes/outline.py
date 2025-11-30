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
            print(f"[大纲生成] 开始生成项目 {project_id} 的大纲")
            project = db_manager.get_ppt_project(project_id)
            if not project:
                print(f"[大纲生成] 项目 {project_id} 不存在")
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取请求数据
            data = request.get_json() or {}
            custom_prompt = data.get('custom_prompt')  # 自定义提示词（可选）

            print(f"[大纲生成] 获取知识库文本，工作区ID: {project['workspace_id']}")
            # 获取知识库文本
            knowledge_text = db_manager.get_workspace_knowledge_text(project['workspace_id'])
            print(f"[大纲生成] 知识库文本长度: {len(knowledge_text)} 字符")

            print(f"[大纲生成] 调用Gemini API生成大纲，期望页数: {project['expected_pages']}")
            # 调用Gemini生成大纲
            if custom_prompt:
                print(f"[大纲生成] 使用自定义提示词")
                outline_data = gemini_service.generate_outline_with_custom_prompt(custom_prompt)
            else:
                outline_data = gemini_service.generate_outline(
                    knowledge_text,
                    project['user_prompt'],
                    project['expected_pages']
                )
            print(f"[大纲生成] Gemini API返回成功，生成了 {len(outline_data.get('pages', []))} 页")

            # 删除旧大纲
            db_manager.delete_outline_pages(project_id)
            print(f"[大纲生成] 已删除旧大纲")

            # 保存新大纲
            for page in outline_data['pages']:
                db_manager.add_outline_page(
                    project_id,
                    page['page_number'],
                    page['title'],
                    page['content'],
                    page.get('image_prompt', '')
                )
            print(f"[大纲生成] 已保存新大纲到数据库")

            # 更新项目状态
            db_manager.update_ppt_project_status(project_id, 'outline_generated')
            print(f"[大纲生成] 项目状态已更新为 outline_generated")

            return jsonify({'success': True, 'data': outline_data})
        except Exception as e:
            print(f"[大纲生成] 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
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

    @outline_bp.route('/api/ppt/<int:project_id>/outline/prompt', methods=['GET'])
    def get_outline_prompt(project_id):
        """获取生成大纲的提示词"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取知识库文本
            knowledge_text = db_manager.get_workspace_knowledge_text(project['workspace_id'])

            # 构建提示词
            prompt = gemini_service.build_outline_prompt(
                knowledge_text,
                project['user_prompt'],
                project['expected_pages']
            )

            return jsonify({'success': True, 'data': {'prompt': prompt}})
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

            # 获取请求数据
            data = request.get_json() or {}
            extra_prompt = data.get('extra_prompt', '').strip()  # 额外提示词

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
                pages,
                extra_prompt
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
