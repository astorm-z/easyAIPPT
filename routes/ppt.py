"""PPT生成相关路由"""
from flask import Blueprint, request, jsonify, render_template, Response, send_file
import json
import os
import zipfile
import io
from database.db_manager import DBManager
from services.banana_service import BananaService
from services.ppt_generator import PPTGenerator

ppt_bp = Blueprint('ppt', __name__)


def init_routes(db_manager: DBManager, banana_service: BananaService, ppt_generator: PPTGenerator):
    """初始化路由"""

    @ppt_bp.route('/api/workspaces/<int:workspace_id>/ppt', methods=['GET'])
    def get_workspace_ppt_projects(workspace_id):
        """获取工作空间的所有PPT项目"""
        try:
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            projects = db_manager.get_ppt_projects(workspace_id)
            return jsonify({'success': True, 'data': projects})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/workspaces/<int:workspace_id>/ppt/create', methods=['POST'])
    def create_ppt_project(workspace_id):
        """创建PPT项目"""
        try:
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            data = request.get_json()
            title = data.get('title', '').strip()
            user_prompt = data.get('user_prompt', '').strip()
            expected_pages = data.get('expected_pages', 10)

            if not title or not user_prompt:
                return jsonify({'success': False, 'error': '标题和提示词不能为空'}), 400

            project_id = db_manager.create_ppt_project(workspace_id, title, user_prompt, expected_pages)
            return jsonify({'success': True, 'data': {'id': project_id}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>', methods=['GET'])
    def get_ppt_project(project_id):
        """获取PPT项目详情"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            return jsonify({'success': True, 'data': project})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>', methods=['DELETE'])
    def delete_ppt_project(project_id):
        """删除PPT项目"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            db_manager.delete_ppt_project(project_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/styles/generate', methods=['POST'])
    def generate_styles(project_id):
        """生成样式模板（异步）"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"收到生成样式模板请求: project_id={project_id}")
            project = db_manager.get_ppt_project(project_id)
            if not project:
                logger.warning(f"项目不存在: project_id={project_id}")
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取自定义提示词（可选）
            data = request.get_json() or {}
            custom_prompt = data.get('custom_prompt', '').strip()

            # 在新线程中异步生成样式模板
            def generate_async():
                try:
                    logger.info(f"开始异步生成样式模板: project_id={project_id}, custom_prompt={custom_prompt}")
                    ppt_generator.generate_style_templates(project_id, project, custom_prompt=custom_prompt)
                    logger.info(f"样式模板生成完成: project_id={project_id}")
                except Exception as e:
                    logger.error(f"样式模板生成失败: project_id={project_id}, error={str(e)}")

            import threading
            thread = threading.Thread(target=generate_async)
            thread.daemon = True
            thread.start()
            logger.info(f"样式生成线程已启动: project_id={project_id}")

            return jsonify({'success': True, 'message': '样式生成任务已启动'})
        except Exception as e:
            logger.error(f"启动样式生成失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/styles/status', methods=['GET'])
    def get_styles_status(project_id):
        """获取样式生成进度"""
        try:
            status = ppt_generator.style_generation_status.get(project_id, {
                'current': 0,
                'total': 3,
                'status': 'idle',
                'message': '未开始'
            })
            return jsonify({'success': True, 'data': status})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/styles', methods=['GET'])
    def get_styles(project_id):
        """获取样式模板列表"""
        try:
            styles = db_manager.get_style_templates(project_id)
            return jsonify({'success': True, 'data': styles})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/styles/select', methods=['POST'])
    def select_style(project_id):
        """选择样式模板"""
        try:
            data = request.get_json()
            style_index = data.get('style_index')

            if style_index is None or style_index not in [0, 1, 2]:
                return jsonify({'success': False, 'error': '无效的样式索引'}), 400

            db_manager.update_ppt_project_style(project_id, style_index)
            db_manager.update_ppt_project_status(project_id, 'style_selected')

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/pages', methods=['GET'])
    def get_pages(project_id):
        """获取PPT页面列表"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            pages = db_manager.get_ppt_pages(project_id)
            return jsonify({'success': True, 'data': pages})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @ppt_bp.route('/api/ppt/<int:project_id>/pages/prompts', methods=['GET'])
    def get_pages_prompts(project_id):
        """获取所有页面的生成提示词"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取大纲
            outline_pages = db_manager.get_outline_pages(project_id)
            if not outline_pages:
                return jsonify({'success': False, 'error': '大纲不存在'}), 404

            # 获取选中的样式模板
            styles = db_manager.get_style_templates(project_id)
            selected_style = None
            if project['selected_style_index'] is not None:
                selected_style = next(
                    (s for s in styles if s['template_index'] == project['selected_style_index']),
                    None
                )

            # 构建每一页的提示词
            prompts = ppt_generator.build_page_prompts(outline_pages, selected_style)

            return jsonify({'success': True, 'data': prompts})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/pages/generate', methods=['POST'])
    def generate_pages(project_id):
        """开始生成所有页面"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"收到生成页面请求: project_id={project_id}")
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取请求数据
            data = request.get_json() or {}
            custom_prompts = data.get('custom_prompts')  # 自定义提示词列表（可选）

            # 检查是否需要恢复
            if project['status'] == 'generating':
                logger.info("项目正在生成中，尝试恢复")
                resumed = ppt_generator.resume_generation(project_id)
                if resumed:
                    return jsonify({'success': True, 'message': '已恢复生成任务'})

            # 启动生成任务（异步）
            ppt_generator.start_generation(project_id, custom_prompts)

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"启动生成失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/pages/resume', methods=['POST'])
    def resume_pages(project_id):
        """恢复未完成的生成任务"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"收到恢复生成请求: project_id={project_id}")
            resumed = ppt_generator.resume_generation(project_id)

            if resumed:
                return jsonify({'success': True, 'message': '已恢复生成任务'})
            else:
                return jsonify({'success': False, 'message': '无需恢复或任务已完成'})
        except Exception as e:
            logger.error(f"恢复生成失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/pages/status')
    def get_pages_status(project_id):
        """获取生成进度（SSE）"""
        def generate():
            try:
                for progress in ppt_generator.get_generation_progress(project_id):
                    yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    @ppt_bp.route('/api/ppt/<int:project_id>/pages/<int:page_number>/regenerate', methods=['POST'])
    def regenerate_page(project_id, page_number):
        """重新生成单页"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            # 获取自定义提示词（可选）
            data = request.get_json() or {}
            custom_prompt = data.get('custom_prompt', '').strip()

            result = ppt_generator.regenerate_single_page(project_id, page_number, custom_prompt=custom_prompt)

            return jsonify({'success': True, 'data': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/api/ppt/<int:project_id>/pages/download')
    def download_pages(project_id):
        """下载所有PPT图片（ZIP）"""
        try:
            project = db_manager.get_ppt_project(project_id)
            if not project:
                return jsonify({'success': False, 'error': 'PPT项目不存在'}), 404

            pages = db_manager.get_ppt_pages(project_id)

            # 创建ZIP文件
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for page in pages:
                    if page['image_path'] and os.path.exists(page['image_path']):
                        filename = f"page_{page['page_number']:03d}.png"
                        zf.write(page['image_path'], filename)

            memory_file.seek(0)
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{project['title']}_ppt.zip"
            )
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @ppt_bp.route('/ppt/<int:project_id>')
    def ppt_preview(project_id):
        """PPT预览页"""
        return render_template('ppt_preview.html', project_id=project_id)

    return ppt_bp
