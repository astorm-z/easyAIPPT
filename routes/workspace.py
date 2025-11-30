"""工作空间相关路由"""
from flask import Blueprint, request, jsonify, render_template
from database.db_manager import DBManager

workspace_bp = Blueprint('workspace', __name__)


def init_routes(db_manager: DBManager):
    """初始化路由"""

    @workspace_bp.route('/')
    def index():
        """首页 - 显示所有工作空间"""
        return render_template('index.html')

    @workspace_bp.route('/api/workspaces', methods=['GET'])
    def get_workspaces():
        """获取所有工作空间"""
        try:
            workspaces = db_manager.get_all_workspaces()
            return jsonify({'success': True, 'data': workspaces})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @workspace_bp.route('/api/workspaces', methods=['POST'])
    def create_workspace():
        """创建新工作空间"""
        try:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400

            name = data.get('name', '').strip()
            description = data.get('description', '').strip()

            if not name:
                return jsonify({'success': False, 'error': '工作空间名称不能为空'}), 400

            workspace_id = db_manager.create_workspace(name, description)
            return jsonify({'success': True, 'data': {'id': workspace_id}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @workspace_bp.route('/api/workspaces/<int:workspace_id>', methods=['GET'])
    def get_workspace(workspace_id):
        """获取工作空间详情"""
        try:
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            return jsonify({'success': True, 'data': workspace})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @workspace_bp.route('/api/workspaces/<int:workspace_id>', methods=['PUT'])
    def update_workspace(workspace_id):
        """更新工作空间"""
        try:
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'success': False, 'error': '请求数据为空'}), 400

            name = data.get('name', '').strip()
            description = data.get('description', '').strip()

            if not name:
                return jsonify({'success': False, 'error': '工作空间名称不能为空'}), 400

            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            db_manager.update_workspace(workspace_id, name, description)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @workspace_bp.route('/api/workspaces/<int:workspace_id>', methods=['DELETE'])
    def delete_workspace(workspace_id):
        """删除工作空间"""
        try:
            workspace = db_manager.get_workspace(workspace_id)
            if not workspace:
                return jsonify({'success': False, 'error': '工作空间不存在'}), 404

            db_manager.delete_workspace(workspace_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @workspace_bp.route('/workspace/<int:workspace_id>')
    def workspace_detail(workspace_id):
        """工作空间详情页"""
        return render_template('workspace.html', workspace_id=workspace_id)

    return workspace_bp
