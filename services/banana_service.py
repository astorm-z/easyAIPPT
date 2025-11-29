"""Gemini图片生成API调用服务"""
import os
import time
import logging
from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)


class BananaService:
    """Gemini图片生成服务（Nano Banana Pro）"""

    def __init__(self, config):
        self.config = config
        # 初始化Gemini客户端
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        # 使用Gemini 3 Pro Image Preview模型（Nano Banana Pro）
        self.model_name = 'gemini-3-pro-image-preview'
        logger.info(f"BananaService初始化完成 - 使用模型: {self.model_name}")

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

    def generate_image(self, prompt, output_path, aspect_ratio="16:9", image_size="2K"):
        """使用Gemini生成图片"""
        logger.info(f"开始生成图片: {output_path}")
        logger.debug(f"提示词: {prompt[:100]}...")
        logger.info(f"图片配置: 比例={aspect_ratio}, 尺寸={image_size}")

        def api_call():
            try:
                logger.info(f"调用Gemini {self.model_name} 生成图片")

                # 使用新的Gemini API调用图片生成
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE'],  # 只生成图片
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio,  # 16:9适合PPT
                            image_size=image_size  # 2K分辨率
                        ),
                    )
                )
                logger.info("Gemini API调用成功")

                # 提取并保存图片
                for part in response.parts:
                    if part.inline_data is not None:
                        logger.info("从响应中提取图片数据")
                        # 使用as_image()方法获取PIL Image对象
                        image = part.as_image()
                        # 保存图片
                        image.save(output_path)
                        logger.info(f"图片已保存: {output_path}")
                        return output_path

                # 如果没有图片，创建占位图片
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
        """生成PPT页面（基于样式模板）"""
        logger.info(f"生成PPT页面，样式参考: {style_reference}")

        # 加载提示词模板
        prompt_template = self.load_prompt('page_generation.txt')
        full_prompt = prompt_template.format(
            page_content=page_content,
            style_reference="参考提供的样式模板图片" if style_reference else "无样式参考"
        )

        # 如果有样式模板，将其作为参考图片传入
        if style_reference and os.path.exists(style_reference):
            logger.info(f"使用样式模板图片: {style_reference}")
            return self.generate_image_with_reference(full_prompt, style_reference, output_path)
        else:
            logger.warning("没有样式模板参考，直接生成")
            return self.generate_image(full_prompt, output_path)

    def generate_image_with_reference(self, prompt, reference_image_path, output_path, aspect_ratio="16:9", image_size="2K"):
        """使用参考图片生成新图片（图片编辑功能）"""
        logger.info(f"开始生成图片（带参考图片）: {output_path}")
        logger.debug(f"提示词: {prompt[:100]}...")
        logger.info(f"参考图片: {reference_image_path}")
        logger.info(f"图片配置: 比例={aspect_ratio}, 尺寸={image_size}")

        def api_call():
            try:
                logger.info(f"调用Gemini {self.model_name} 生成图片（带参考）")

                # 加载参考图片
                reference_image = Image.open(reference_image_path)
                logger.info(f"参考图片已加载: {reference_image.size}")

                # 使用Gemini API调用图片生成（文字+图片转图片）
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt, reference_image],  # 同时传入文字和图片
                    config=types.GenerateContentConfig(
                        response_modalities=['IMAGE'],
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio,
                            image_size=image_size
                        ),
                    )
                )
                logger.info("Gemini API调用成功")

                # 提取并保存图片
                for part in response.parts:
                    if part.inline_data is not None:
                        logger.info("从响应中提取图片数据")
                        image = part.as_image()
                        image.save(output_path)
                        logger.info(f"图片已保存: {output_path}")
                        return output_path

                # 如果没有图片，创建占位图片
                logger.warning("Gemini未返回图片，创建占位图片")
                self._create_placeholder_image(output_path, prompt)
                return output_path

            except Exception as e:
                logger.error(f"Gemini图片生成失败: {str(e)}")
                logger.info("创建占位图片")
                self._create_placeholder_image(output_path, prompt)
                return output_path

        return self.retry_api_call(api_call)
