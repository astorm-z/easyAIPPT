"""数据库模型定义"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    """数据库连接管理"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn

    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 创建工作空间表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建知识库文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                extracted_text TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        ''')

        # 添加 original_filename 字段（如果不存在）
        try:
            cursor.execute("SELECT original_filename FROM knowledge_files LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE knowledge_files ADD COLUMN original_filename TEXT")

        # 创建PPT项目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ppt_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                user_prompt TEXT NOT NULL,
                expected_pages INTEGER,
                status TEXT DEFAULT 'draft',
                selected_style_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        ''')

        # 创建PPT大纲表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ppt_outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppt_project_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                image_prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ppt_project_id) REFERENCES ppt_projects(id) ON DELETE CASCADE
            )
        ''')

        # 创建样式模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS style_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppt_project_id INTEGER NOT NULL,
                template_index INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ppt_project_id) REFERENCES ppt_projects(id) ON DELETE CASCADE
            )
        ''')

        # 创建PPT页面表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ppt_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ppt_project_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                image_path TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ppt_project_id) REFERENCES ppt_projects(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回受影响的行数或最后插入的ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id
