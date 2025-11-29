"""Gemini API调用服务"""
import os
import json
import time
import google.generativeai as genai


class GeminiService:
    """Gemini服务"""

    def __init__(self, config):
        self.config = config
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    def load_prompt(self, prompt_file):
        """加载提示词文件"""
        prompt_path = os.path.join('prompts', prompt_file)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def retry_api_call(self, func, max_retries=None):
        """API调用重试机制"""
        if max_retries is None:
            max_retries = self.config.MAX_API_RETRIES

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f'API调用失败，已重试{max_retries}次: {str(e)}')
                # 指数退避
                wait_time = self.config.RETRY_DELAY_BASE ** attempt
                time.sleep(wait_time)

    def generate_outline(self, knowledge_text, user_prompt, expected_pages):
        """生成PPT大纲"""
        # 加载提示词模板
        prompt_template = self.load_prompt('outline_generation.txt')

        # 构建完整提示词
        full_prompt = prompt_template.format(
            knowledge_text=knowledge_text[:10000],  # 限制知识库文本长度
            user_prompt=user_prompt,
            expected_pages=expected_pages
        )

        def api_call():
            response = self.model.generate_content(full_prompt)
            # 解析JSON响应
            text = response.text.strip()
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            return json.loads(text.strip())

        return self.retry_api_call(api_call)

    def regenerate_outline_page(self, knowledge_text, user_prompt, page_number, existing_pages):
        """重新生成单页大纲"""
        # 加载提示词模板
        prompt_template = self.load_prompt('outline_generation.txt')

        # 构建上下文
        context = f"现有大纲:\n"
        for page in existing_pages:
            context += f"第{page['page_number']}页: {page['title']}\n"

        # 构建完整提示词
        full_prompt = f"""{prompt_template}

{context}

请重新生成第{page_number}页的内容，要求与其他页面保持连贯性。

知识库内容:
{knowledge_text[:5000]}

用户需求: {user_prompt}

请只返回第{page_number}页的JSON格式数据，格式如下:
{{
    "page_number": {page_number},
    "title": "页面标题",
    "content": "页面内容描述",
    "image_prompt": "图片生成提示词"
}}
"""

        def api_call():
            response = self.model.generate_content(full_prompt)
            text = response.text.strip()
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            return json.loads(text.strip())

        return self.retry_api_call(api_call)
