"""PPT生成流程控制"""
import os
import logging
import threading
from typing import Generator, Dict, Any

logger = logging.getLogger(__name__)


class PPTGenerator:
    """PPT生成器"""

    def __init__(self, config, db_manager, banana_service):
        self.config = config
        self.db_manager = db_manager
        self.banana_service = banana_service
        self.generation_status = {}  # 存储生成状态
        self.style_generation_status = {}  # 存储样式生成状态
        logger.info("PPTGenerator初始化完成")

    def generate_style_templates(self, project_id, project, custom_prompt=''):
        """生成3个样式模板"""
        logger.info(f"开始为项目 {project_id} 生成样式模板, custom_prompt={custom_prompt}")

        # 初始化状态
        self.style_generation_status[project_id] = {
            'current': 0,
            'total': 3,
            'status': 'generating',
            'message': '准备生成样式模板...'
        }

        # 删除旧的样式模板
        self.db_manager.delete_style_templates(project_id)
        logger.info(f"已删除项目 {project_id} 的旧样式模板")

        # 创建输出目录
        output_dir = os.path.join(
            self.config.GENERATED_FOLDER,
            f'workspace_{project["workspace_id"]}',
            f'ppt_{project_id}',
            'styles'
        )
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"创建输出目录: {output_dir}")

        styles = []
        style_descriptions = [
            "现代简约风格，使用大量留白和几何图形",
            "商务专业风格，使用深色背景和金色点缀",
            "创意活泼风格，使用明亮色彩和动态元素"
        ]

        for i, description in enumerate(style_descriptions):
            # 如果有自定义提示词，追加到描述后面
            final_description = description
            if custom_prompt:
                final_description = f"{description}。额外要求：{custom_prompt}"

            logger.info(f"正在生成样式模板 {i+1}/3: {final_description}")
            self.style_generation_status[project_id]['current'] = i + 1
            self.style_generation_status[project_id]['message'] = f'正在生成样式 {i+1}/3...'

            output_path = os.path.join(output_dir, f'style_{i}.png')
            try:
                self.banana_service.generate_style_template(final_description, output_path)
                logger.info(f"样式模板 {i+1} 生成成功: {output_path}")

                style_id = self.db_manager.add_style_template(project_id, i, output_path)
                styles.append({
                    'id': style_id,
                    'template_index': i,
                    'image_path': output_path
                })
            except Exception as e:
                logger.error(f"生成样式模板 {i+1} 失败: {str(e)}")
                self.style_generation_status[project_id]['status'] = 'failed'
                self.style_generation_status[project_id]['message'] = f'生成样式 {i+1} 失败: {str(e)}'
                raise Exception(f'生成样式模板{i}失败: {str(e)}')

        self.style_generation_status[project_id]['status'] = 'completed'
        self.style_generation_status[project_id]['message'] = '样式模板生成完成'
        logger.info(f"项目 {project_id} 的所有样式模板生成完成")
        return styles

    def start_generation(self, project_id):
        """启动PPT页面生成（异步）"""
        logger.info(f"启动PPT页面生成任务: project_id={project_id}")
        # 在新线程中执行生成任务
        thread = threading.Thread(target=self._generate_pages, args=(project_id,))
        thread.daemon = True
        thread.start()

    def resume_generation(self, project_id):
        """恢复未完成的生成任务"""
        logger.info(f"尝试恢复生成任务: project_id={project_id}")

        # 检查项目状态
        project = self.db_manager.get_ppt_project(project_id)
        if not project:
            logger.warning(f"项目不存在: project_id={project_id}")
            return False

        # 只恢复状态为generating的项目
        if project['status'] != 'generating':
            logger.info(f"项目状态不是generating，无需恢复: status={project['status']}")
            return False

        # 检查是否有未完成的页面
        pages = self.db_manager.get_ppt_pages(project_id)
        incomplete_pages = [p for p in pages if p['status'] in ['pending', 'failed']]

        if not incomplete_pages:
            logger.info(f"所有页面已完成，更新项目状态")
            self.db_manager.update_ppt_project_status(project_id, 'completed')
            return False

        logger.info(f"发现 {len(incomplete_pages)} 个未完成页面，恢复生成任务")
        # 启动生成任务
        self.start_generation(project_id)
        return True

    def _generate_pages(self, project_id):
        """生成所有PPT页面"""
        try:
            # 获取项目信息
            project = self.db_manager.get_ppt_project(project_id)
            if not project:
                return

            # 获取大纲
            outline_pages = self.db_manager.get_outline_pages(project_id)
            if not outline_pages:
                return

            # 获取选中的样式模板
            styles = self.db_manager.get_style_templates(project_id)
            selected_style = None
            if project['selected_style_index'] is not None:
                selected_style = next(
                    (s for s in styles if s['template_index'] == project['selected_style_index']),
                    None
                )

            # 创建输出目录
            output_dir = os.path.join(
                self.config.GENERATED_FOLDER,
                f'workspace_{project["workspace_id"]}',
                f'ppt_{project_id}',
                'pages'
            )
            os.makedirs(output_dir, exist_ok=True)

            # 检查是否已有页面记录（恢复场景）
            existing_pages = self.db_manager.get_ppt_pages(project_id)
            if not existing_pages:
                logger.info("首次生成，初始化页面记录")
                # 删除旧的页面记录
                self.db_manager.delete_ppt_pages(project_id)
                # 初始化页面记录
                for page in outline_pages:
                    self.db_manager.add_ppt_page(project_id, page['page_number'])
                existing_pages = self.db_manager.get_ppt_pages(project_id)
            else:
                logger.info(f"恢复生成，已有 {len(existing_pages)} 条页面记录")

            # 更新项目状态
            self.db_manager.update_ppt_project_status(project_id, 'generating')

            # 初始化生成状态
            completed_count = len([p for p in existing_pages if p['status'] == 'completed'])
            self.generation_status[project_id] = {
                'current_page': completed_count,
                'total_pages': len(outline_pages),
                'status': 'generating',
                'error': None
            }
            logger.info(f"生成状态初始化: 已完成 {completed_count}/{len(outline_pages)} 页")

            # 逐页生成
            for page in outline_pages:
                # 检查该页是否已完成
                existing_page = next((p for p in existing_pages if p['page_number'] == page['page_number']), None)
                if existing_page and existing_page['status'] == 'completed':
                    logger.info(f"第 {page['page_number']} 页已完成，跳过")
                    continue

                try:
                    logger.info(f"开始生成第 {page['page_number']}/{len(outline_pages)} 页")
                    self.generation_status[project_id]['current_page'] = page['page_number']

                    output_path = os.path.join(output_dir, f'page_{page["page_number"]:03d}.png')

                    # 构建页面内容描述
                    page_content = f"标题: {page['title']}\n内容: {page['content']}"
                    if page['image_prompt']:
                        page_content += f"\n图片提示: {page['image_prompt']}"

                    # 生成图片
                    style_ref = selected_style['image_path'] if selected_style else ''
                    self.banana_service.generate_ppt_page(page_content, style_ref, output_path)

                    # 更新页面状态
                    self.db_manager.update_ppt_page(
                        project_id,
                        page['page_number'],
                        output_path,
                        'completed'
                    )
                    logger.info(f"第 {page['page_number']} 页生成完成")

                except Exception as e:
                    # 记录错误
                    self.db_manager.update_ppt_page(
                        project_id,
                        page['page_number'],
                        '',
                        'failed',
                        str(e)
                    )

            # 更新项目状态
            self.db_manager.update_ppt_project_status(project_id, 'completed')
            self.generation_status[project_id]['status'] = 'completed'

        except Exception as e:
            # 更新项目状态为失败
            self.db_manager.update_ppt_project_status(project_id, 'failed')
            if project_id in self.generation_status:
                self.generation_status[project_id]['status'] = 'failed'
                self.generation_status[project_id]['error'] = str(e)

    def get_generation_progress(self, project_id) -> Generator[Dict[str, Any], None, None]:
        """获取生成进度（生成器，用于SSE）"""
        # 等待生成任务启动
        max_wait = 30  # 最多等待30秒
        wait_count = 0
        while project_id not in self.generation_status and wait_count < max_wait:
            import time
            time.sleep(1)
            wait_count += 1

        if project_id not in self.generation_status:
            yield {'error': '生成任务未启动'}
            return

        # 持续推送进度
        while True:
            status = self.generation_status[project_id]
            yield {
                'current_page': status['current_page'],
                'total_pages': status['total_pages'],
                'status': status['status'],
                'error': status['error']
            }

            # 如果已完成或失败，结束推送
            if status['status'] in ['completed', 'failed']:
                break

            import time
            time.sleep(2)  # 每2秒推送一次

    def regenerate_single_page(self, project_id, page_number, custom_prompt=''):
        """重新生成单页"""
        try:
            # 获取项目信息
            project = self.db_manager.get_ppt_project(project_id)
            if not project:
                raise Exception('PPT项目不存在')

            # 获取大纲
            outline_pages = self.db_manager.get_outline_pages(project_id)
            page = next((p for p in outline_pages if p['page_number'] == page_number), None)
            if not page:
                raise Exception('页面不存在')

            # 获取选中的样式模板
            styles = self.db_manager.get_style_templates(project_id)
            selected_style = None
            if project['selected_style_index'] is not None:
                selected_style = next(
                    (s for s in styles if s['template_index'] == project['selected_style_index']),
                    None
                )

            # 输出路径
            output_dir = os.path.join(
                self.config.GENERATED_FOLDER,
                f'workspace_{project["workspace_id"]}',
                f'ppt_{project_id}',
                'pages'
            )
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'page_{page_number:03d}.png')

            # 构建页面内容描述
            page_content = f"标题: {page['title']}\n内容: {page['content']}"
            if page['image_prompt']:
                page_content += f"\n图片提示: {page['image_prompt']}"

            # 如果有自定义提示词，追加到内容后面
            if custom_prompt:
                page_content += f"\n额外要求: {custom_prompt}"

            # 生成图片
            style_ref = selected_style['image_path'] if selected_style else ''
            self.banana_service.generate_ppt_page(page_content, style_ref, output_path)

            # 更新页面状态
            self.db_manager.update_ppt_page(
                project_id,
                page_number,
                output_path,
                'completed'
            )

            return {
                'page_number': page_number,
                'image_path': output_path,
                'status': 'completed'
            }

        except Exception as e:
            # 增加重试次数
            self.db_manager.increment_page_retry_count(project_id, page_number)

            # 更新页面状态
            self.db_manager.update_ppt_page(
                project_id,
                page_number,
                '',
                'failed',
                str(e)
            )

            raise Exception(f'重新生成页面失败: {str(e)}')
