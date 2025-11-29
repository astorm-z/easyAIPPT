"""Gemini图片生成API调用服务"""
import os
import time
import logging
import google.generativeai as genai
from PIL import Image
import io

logger = logging.getLogger(__name__)


class BananaService:
    """Gemini图片生成服务（原Banana服务）"""

    def __init__(self, config):
        self.config = config
        # 使用Gemini API密钥
        genai.configure(api_key=config.GEMINI_API_KEY)
        # 使用Gemini的图片生成模型
        self.model_name = 'gemini-2.0-flash-exp'  # Gemini 2.0支持图片生成
        logger.info(f"BananaService初始化完成 - 使用Gemini模型: {self.model_name}")

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
        """使用Gemini生成图片"""
        logger.info(f"开始生成图片: {output_path}")
        logger.debug(f"提示词: {prompt[:100]}...")

        def api_call():
            try:
                # 使用Gemini 2.0的图片生成功能
                model = genai.GenerativeModel(self.model_name)

                logger.info(f"调用Gemini API生成图片")

                # 构建完整的提示词，要求生成图片
                full_prompt = f"""请生成一张PPT页面图片。要求：
{prompt}

请直接生成图片，不要返回文字描述。"""

                response = model.generate_content(full_prompt)
                logger.info("Gemini API调用成功")

                # 检查响应中是否有图片
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        if hasattr(part, 'inline_data'):
                            # 获取图片数据
                            image_data = part.inline_data.data
                            logger.info("从响应中提取图片数据")

                            # 保存图片
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                            logger.info(f"图片已保存: {output_path}")
                            return output_path

                # 如果没有图片，创建一个占位图片
                logger.warning("Gemini未返回图片，创建占位图片")
                self._create_placeholder_image(output_path, prompt)
                return output_path

            except Exception as e:
                logger.error(f"Gemini图片生成失败: {str(e)}")
                # 创建占位图片
                logger.info("创建占位图片")
                self._create_placeholder_image(output_path, prompt)
                return output_path

        return self.retry_api_call(api_call)

    def _create_placeholder_image(self, output_path, prompt):
        """创建占位图片（当API不可用时）"""
        from PIL import Image, ImageDraw, ImageFont

        # 创建1920x1080的白色背景图片
        img = Image.new('RGB', (1920, 1080), color='white')
        draw = ImageDraw.Draw(img)

        # 绘制边框
        draw.rectangle([(50, 50), (1870, 1030)], outline='#E0E0E0', width=2)

        # 添加文字说明
        try:
            # 尝试使用系统字体
            font_title = ImageFont.truetype("arial.ttf", 48)
            font_text = ImageFont.truetype("arial.ttf", 24)
        except:
            # 如果没有字体文件，使用默认字体
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        # 绘制标题
        title = "PPT页面占位图"
        draw.text((960, 400), title, fill='#333333', font=font_title, anchor='mm')

        # 绘制提示词（截取前100字符）
        prompt_text = prompt[:100] + "..." if len(prompt) > 100 else prompt
        draw.text((960, 500), prompt_text, fill='#666666', font=font_text, anchor='mm')

        # 绘制说明
        note = "（这是占位图片，请配置正确的Gemini API以生成真实图片）"
        draw.text((960, 600), note, fill='#999999', font=font_text, anchor='mm')

        # 保存图片
        img.save(output_path)
        logger.info(f"占位图片已创建: {output_path}")

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
