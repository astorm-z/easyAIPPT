"""Nano Banana Pro API调用服务"""
import os
import time
import logging
import requests

logger = logging.getLogger(__name__)


class BananaService:
    """Banana服务"""

    def __init__(self, config):
        self.config = config
        self.api_key = config.BANANA_API_KEY
        self.model_key = config.BANANA_MODEL_KEY
        # 这里需要根据实际的Banana API文档调整
        self.api_url = "https://api.banana.dev/v1/generate"  # 示例URL
        logger.info(f"BananaService初始化完成 - API URL: {self.api_url}")

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
                logger.debug(f"API调用尝试 {attempt + 1}/{max_retries}")
                return func()
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f'API调用失败，已重试{max_retries}次: {str(e)}')
                    raise Exception(f'API调用失败，已重试{max_retries}次: {str(e)}')
                # 指数退避
                wait_time = self.config.RETRY_DELAY_BASE ** attempt
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

    def generate_image(self, prompt, output_path):
        """生成图片"""
        logger.info(f"开始生成图片: {output_path}")
        logger.debug(f"提示词: {prompt[:100]}...")

        def api_call():
            # 这里需要根据实际的Banana API调整请求格式
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model_key,
                'prompt': prompt,
                'width': 1920,
                'height': 1080
            }

            logger.info(f"发送API请求到: {self.api_url}")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            logger.info("API请求成功")

            # 保存图片
            # 这里需要根据实际API响应格式调整
            result = response.json()
            logger.debug(f"API响应: {result}")

            # 假设API返回图片URL或base64数据
            if 'image_url' in result:
                # 下载图片
                logger.info(f"从URL下载图片: {result['image_url']}")
                img_response = requests.get(result['image_url'], timeout=60)
                img_response.raise_for_status()
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                logger.info(f"图片已保存: {output_path}")
            elif 'image_data' in result:
                # 保存base64数据
                logger.info("保存base64图片数据")
                import base64
                img_data = base64.b64decode(result['image_data'])
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                logger.info(f"图片已保存: {output_path}")
            else:
                logger.error("API响应中没有图片数据")
                raise Exception('API响应中没有图片数据')

            return output_path

        return self.retry_api_call(api_call)

    def generate_style_template(self, style_description, output_path):
        """生成样式模板"""
        prompt_template = self.load_prompt('style_template.txt')
        full_prompt = prompt_template.format(style_description=style_description)
        return self.generate_image(full_prompt, output_path)

    def generate_ppt_page(self, page_content, style_reference, output_path):
        """生成PPT页面"""
        prompt_template = self.load_prompt('page_generation.txt')
        full_prompt = prompt_template.format(
            page_content=page_content,
            style_reference=style_reference
        )
        return self.generate_image(full_prompt, output_path)
