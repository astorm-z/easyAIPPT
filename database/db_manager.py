"""数据库操作封装"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from database.models import Database


class DBManager:
    """数据库管理器"""

    def __init__(self, db: Database):
        self.db = db

    # ==================== 工作空间操作 ====================

    def create_workspace(self, name: str, description: str = '') -> int:
        """创建工作空间"""
        query = 'INSERT INTO workspaces (name, description) VALUES (?, ?)'
        return self.db.execute_update(query, (name, description))

    def get_all_workspaces(self) -> List[Dict[str, Any]]:
        """获取所有工作空间"""
        query = 'SELECT * FROM workspaces ORDER BY updated_at DESC'
        return self.db.execute_query(query)

    def get_workspace(self, workspace_id: int) -> Optional[Dict[str, Any]]:
        """获取单个工作空间"""
        query = 'SELECT * FROM workspaces WHERE id = ?'
        results = self.db.execute_query(query, (workspace_id,))
        return results[0] if results else None

    def update_workspace(self, workspace_id: int, name: str, description: str = '') -> None:
        """更新工作空间"""
        query = '''
            UPDATE workspaces
            SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        self.db.execute_update(query, (name, description, workspace_id))

    def delete_workspace(self, workspace_id: int) -> None:
        """删除工作空间"""
        query = 'DELETE FROM workspaces WHERE id = ?'
        self.db.execute_update(query, (workspace_id,))

    # ==================== 知识库文件操作 ====================

    def add_knowledge_file(self, workspace_id: int, filename: str, file_type: str,
                          file_path: str, file_size: int, extracted_text: str = '',
                          original_filename: str = '') -> int:
        """添加知识库文件"""
        query = '''
            INSERT INTO knowledge_files
            (workspace_id, filename, original_filename, file_type, file_path, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_update(query, (workspace_id, filename, original_filename or filename,
                                              file_type, file_path, file_size, extracted_text))

    def get_knowledge_files(self, workspace_id: int) -> List[Dict[str, Any]]:
        """获取工作空间的所有知识库文件"""
        query = 'SELECT * FROM knowledge_files WHERE workspace_id = ? ORDER BY uploaded_at DESC'
        return self.db.execute_query(query, (workspace_id,))

    def get_knowledge_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """获取单个知识库文件"""
        query = 'SELECT * FROM knowledge_files WHERE id = ?'
        results = self.db.execute_query(query, (file_id,))
        return results[0] if results else None

    def delete_knowledge_file(self, file_id: int) -> None:
        """删除知识库文件"""
        query = 'DELETE FROM knowledge_files WHERE id = ?'
        self.db.execute_update(query, (file_id,))

    def get_workspace_knowledge_text(self, workspace_id: int) -> str:
        """获取工作空间所有知识库文本内容"""
        query = 'SELECT extracted_text FROM knowledge_files WHERE workspace_id = ?'
        results = self.db.execute_query(query, (workspace_id,))
        return '\n\n'.join([r['extracted_text'] for r in results if r['extracted_text']])

    # ==================== PPT项目操作 ====================

    def create_ppt_project(self, workspace_id: int, title: str, user_prompt: str,
                          expected_pages: int) -> int:
        """创建PPT项目"""
        query = '''
            INSERT INTO ppt_projects (workspace_id, title, user_prompt, expected_pages)
            VALUES (?, ?, ?, ?)
        '''
        return self.db.execute_update(query, (workspace_id, title, user_prompt, expected_pages))

    def get_ppt_projects(self, workspace_id: int) -> List[Dict[str, Any]]:
        """获取工作空间的所有PPT项目"""
        query = 'SELECT * FROM ppt_projects WHERE workspace_id = ? ORDER BY updated_at DESC'
        return self.db.execute_query(query, (workspace_id,))

    def get_ppt_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取单个PPT项目"""
        query = 'SELECT * FROM ppt_projects WHERE id = ?'
        results = self.db.execute_query(query, (project_id,))
        return results[0] if results else None

    def update_ppt_project_status(self, project_id: int, status: str) -> None:
        """更新PPT项目状态"""
        query = 'UPDATE ppt_projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        self.db.execute_update(query, (status, project_id))

    def update_ppt_project_style(self, project_id: int, style_index: int) -> None:
        """更新PPT项目选中的样式"""
        query = '''
            UPDATE ppt_projects
            SET selected_style_index = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        self.db.execute_update(query, (style_index, project_id))

    def delete_ppt_project(self, project_id: int) -> None:
        """删除PPT项目"""
        query = 'DELETE FROM ppt_projects WHERE id = ?'
        self.db.execute_update(query, (project_id,))

    # ==================== PPT大纲操作 ====================

    def add_outline_page(self, project_id: int, page_number: int, title: str,
                        content: str, image_prompt: str = '') -> int:
        """添加大纲页"""
        query = '''
            INSERT INTO ppt_outlines (ppt_project_id, page_number, title, content, image_prompt)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db.execute_update(query, (project_id, page_number, title, content, image_prompt))

    def get_outline_pages(self, project_id: int) -> List[Dict[str, Any]]:
        """获取PPT项目的所有大纲页"""
        query = 'SELECT * FROM ppt_outlines WHERE ppt_project_id = ? ORDER BY page_number'
        return self.db.execute_query(query, (project_id,))

    def update_outline_page(self, project_id: int, page_number: int, title: str,
                           content: str, image_prompt: str = '') -> None:
        """更新大纲页"""
        query = '''
            UPDATE ppt_outlines
            SET title = ?, content = ?, image_prompt = ?
            WHERE ppt_project_id = ? AND page_number = ?
        '''
        self.db.execute_update(query, (title, content, image_prompt, project_id, page_number))

    def delete_outline_pages(self, project_id: int) -> None:
        """删除PPT项目的所有大纲页"""
        query = 'DELETE FROM ppt_outlines WHERE ppt_project_id = ?'
        self.db.execute_update(query, (project_id,))

    # ==================== 样式模板操作 ====================

    def add_style_template(self, project_id: int, template_index: int, image_path: str) -> int:
        """添加样式模板"""
        query = '''
            INSERT INTO style_templates (ppt_project_id, template_index, image_path)
            VALUES (?, ?, ?)
        '''
        return self.db.execute_update(query, (project_id, template_index, image_path))

    def get_style_templates(self, project_id: int) -> List[Dict[str, Any]]:
        """获取PPT项目的所有样式模板"""
        query = 'SELECT * FROM style_templates WHERE ppt_project_id = ? ORDER BY template_index'
        return self.db.execute_query(query, (project_id,))

    def delete_style_templates(self, project_id: int) -> None:
        """删除PPT项目的所有样式模板"""
        query = 'DELETE FROM style_templates WHERE ppt_project_id = ?'
        self.db.execute_update(query, (project_id,))

    # ==================== PPT页面操作 ====================

    def add_ppt_page(self, project_id: int, page_number: int) -> int:
        """添加PPT页面"""
        query = 'INSERT INTO ppt_pages (ppt_project_id, page_number) VALUES (?, ?)'
        return self.db.execute_update(query, (project_id, page_number))

    def get_ppt_pages(self, project_id: int) -> List[Dict[str, Any]]:
        """获取PPT项目的所有页面"""
        query = 'SELECT * FROM ppt_pages WHERE ppt_project_id = ? ORDER BY page_number'
        return self.db.execute_query(query, (project_id,))

    def update_ppt_page(self, project_id: int, page_number: int, image_path: str,
                       status: str, error_message: str = '') -> None:
        """更新PPT页面"""
        query = '''
            UPDATE ppt_pages
            SET image_path = ?, status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE ppt_project_id = ? AND page_number = ?
        '''
        self.db.execute_update(query, (image_path, status, error_message, project_id, page_number))

    def update_ppt_page_status(self, project_id: int, page_number: int, status: str) -> None:
        """更新PPT页面状态"""
        query = '''
            UPDATE ppt_pages
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE ppt_project_id = ? AND page_number = ?
        '''
        self.db.execute_update(query, (status, project_id, page_number))

    def increment_page_retry_count(self, project_id: int, page_number: int) -> None:
        """增加页面重试次数"""
        query = '''
            UPDATE ppt_pages
            SET retry_count = retry_count + 1
            WHERE ppt_project_id = ? AND page_number = ?
        '''
        self.db.execute_update(query, (project_id, page_number))

    def delete_ppt_pages(self, project_id: int) -> None:
        """删除PPT项目的所有页面"""
        query = 'DELETE FROM ppt_pages WHERE ppt_project_id = ?'
        self.db.execute_update(query, (project_id,))
