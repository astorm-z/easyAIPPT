"""认证相关路由"""
from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for

auth_bp = Blueprint('auth', __name__)


def init_routes(config):
    """初始化认证路由"""

    @auth_bp.route('/login')
    def login():
        """登录页面"""
        # 如果未设置密码，直接跳转到首页
        if not config.LOGIN_PASSWORD:
            return redirect('/')

        # 如果已登录，跳转到首页或指定页面
        if session.get('logged_in'):
            next_url = request.args.get('next', '/')
            return redirect(next_url)

        return render_template('login.html')

    @auth_bp.route('/api/auth/login', methods=['POST'])
    def api_login():
        """登录API"""
        try:
            data = request.get_json()
            password = data.get('password', '')

            # 如果未设置密码，直接成功
            if not config.LOGIN_PASSWORD:
                session['logged_in'] = True
                return jsonify({'success': True})

            # 验证密码
            if password == config.LOGIN_PASSWORD:
                session['logged_in'] = True
                session.permanent = True  # 使session持久化
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': '密码错误'}), 401

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @auth_bp.route('/api/auth/logout', methods=['POST'])
    def api_logout():
        """登出API"""
        session.clear()
        return jsonify({'success': True})

    @auth_bp.route('/logout')
    def logout():
        """登出页面"""
        session.clear()
        return redirect(url_for('auth.login'))

    return auth_bp
