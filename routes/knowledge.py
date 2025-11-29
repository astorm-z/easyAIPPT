"""知识库相关路由"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from database.db_manager import DBManager
from services.file_processor import FileProcessor
from config import Config

knowledge_bp = Blueprint('knowledge', __name__)


def init_routes(db_manager: DBManager, file_processor: FileProcessor):
    """初始化路由"""

    @knowledge_bp.route('/api/workspaces/<int:workspace_id>/knowledge/upload', methods=['POST'])
    def upload_knowledge_file(workspace_id):
        """上传文件到知识库"""
        try:
            # 检查工作空间是否存在
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            # 检查是否有文件
            if 'files' not in request.files:
                return jsonify({'success': False, 'error': '没有上传文件'}), 400

            files = request.files.getlist('files')
            if not files or files[0].filename == '':
                return jsonify({'success': False, 'error': '没有选择文件'}), 400

            uploaded_files = []
            for file in files:
                if file and file.filename:
                    # 保存文件并提取文本
                    result = file_processor.process_uploaded_file(
                        file, workspace_id, db_manager
                    )
                    if result['success']:
                        uploaded_files.append(result['data'])
                    else:
                        return jsonify(result), 400

            return jsonify({'success': True, 'data': uploaded_files})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @knowledge_bp.route('/api/workspaces/<int:workspace_id>/knowledge', methods=['GET'])
    def get_knowledge_files(workspace_id):
        """获取知识库文件列表"""
        try:
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            files = db_manager.get_knowledge_files(workspace_id)
            return jsonify({'success': True, 'data': files})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @knowledge_bp.route('/api/knowledge/<int:file_id>/preview', methods=['GET'])
    def preview_knowledge_file(file_id):
        """预览知识库文件"""
        try:
            file_info = db_manager.get_knowledge_file(file_id)
            if not file_info:
                return jsonify({'success': False, 'error': '文件不存在'}), 404

            # 检查文件是否存在
            if not os.path.exists(file_info['file_path']):
                return jsonify({'success': False, 'error': '文件已丢失'}), 404

            # 对于图片文件，直接返回文件
            if file_info['file_type'] == 'image':
                return send_file(file_info['file_path'])

            # 对于其他文件，返回提取的文本内容
            return jsonify({
                'success': True,
                'data': {
                    'filename': file_info.get('original_filename') or file_info['filename'],
                    'file_type': file_info['file_type'],
                    'content': file_info.get('extracted_text', ''),
                    'file_size': file_info['file_size']
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @knowledge_bp.route('/api/knowledge/<int:file_id>/download', methods=['GET'])
    def download_knowledge_file(file_id):
        """下载知识库文件"""
        try:
            file_info = db_manager.get_knowledge_file(file_id)
            if not file_info:
                return jsonify({'success': False, 'error': '文件不存在'}), 404

            # 检查文件是否存在
            if not os.path.exists(file_info['file_path']):
                return jsonify({'success': False, 'error': '文件已丢失'}), 404

            # 使用原始文件名作为下载文件名
            download_name = file_info.get('original_filename') or file_info['filename']

            return send_file(
                file_info['file_path'],
                as_attachment=True,
                download_name=download_name
            )
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @knowledge_bp.route('/api/knowledge/<int:file_id>', methods=['DELETE'])
    def delete_knowledge_file(file_id):
        """删除知识库文件"""
        try:
            file_info = db_manager.get_knowledge_file(file_id)
            if not file_info:
                return jsonify({'success': False, 'error': '文件不存在'}), 404

            # 删除物理文件
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])

            # 删除数据库记录
            db_manager.delete_knowledge_file(file_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return knowledge_bp
