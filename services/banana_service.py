"""Gemini图片生成API调用服务"""
import os
import time
import logging
import requests
import base64
import json
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class BananaService:
    """Gemini图片生成服务（Nano Banana Pro）"""

    def __init__(self, config):
        self.config = config
        self.api_key = config.BANANA_API_KEY
        self.api_base_url = config.BANANA_API_BASE_URL
        self.model_name = config.BANANA_MODEL
        logger.info(f"BananaService初始化完成 - 使用模型: {self.model_name}, API URL: {self.api_base_url}")

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
            logger.info(f"调用Gemini {self.model_name} 生成图片")

            # 构建API URL
            api_url = f"{self.api_base_url}/v1beta/models/{self.model_name}:streamGenerateContent"

            # 构建generationConfig
            generation_config = {
                "responseModalities": ["IMAGE"]
            }

            # 只有 gemini-3.0 开头的模型才支持 imageConfig 参数
            if self.model_name.startswith("gemini-3.0"):
                generation_config["imageConfig"] = {
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size
                }
                logger.info(f"模型 {self.model_name} 支持 imageConfig，使用配置: aspect_ratio={aspect_ratio}, image_size={image_size}")
            else:
                logger.warning(f"模型 {self.model_name} 不支持 imageConfig 参数，将忽略 aspect_ratio 和 image_size 配置")

            # 构建请求体
            request_body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": generation_config
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 设置请求参数（API Key）
            params = {
                "key": self.api_key
            }
            
            try:
                # 发送请求
                response = requests.post(
                    api_url,
                    json=request_body,
                    headers=headers,
                    params=params,
                    timeout=self.config.API_TIMEOUT
                )
                
                logger.info(f"API 返回，状态码: {response.status_code}")
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"API 返回错误: {response.text}")
                    raise Exception(f"API返回错误状态码 {response.status_code}: {response.text}")
                
                # 解析响应（流式响应）
                response_text = response.text
                logger.debug(f"响应内容: {response_text[:500]}...")
                
                # 解析流式响应中的图片数据
                image_data = None
                for line in response_text.strip().split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # 去掉 "data: " 前缀
                            if 'candidates' in data:
                                for candidate in data['candidates']:
                                    if 'content' in candidate and 'parts' in candidate['content']:
                                        for part in candidate['content']['parts']:
                                            if 'inlineData' in part:
                                                image_data = part['inlineData']['data']
                                                logger.info("从响应中提取图片数据")
                                                break
                                    if image_data:
                                        break
                            if image_data:
                                break
                        except json.JSONDecodeError:
                            continue
                
                if not image_data:
                    raise Exception("Gemini未返回图片数据")
                
                # 解码base64图片数据
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
                
                # 保存图片
                image.save(output_path)
                logger.info(f"图片已保存: {output_path}")
                return output_path
                
            except requests.exceptions.Timeout:
                logger.error(f"API 调用超时")
                raise Exception(f"API调用超时（{self.config.API_TIMEOUT}秒）")
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {type(e).__name__}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"API 调用异常: {type(e).__name__}: {str(e)}")
                raise

        # 调用重试机制，失败时抛出异常
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
        # 使用配置的样式模板分辨率
        aspect_ratio = self.config.IMAGE_ASPECT_RATIO
        image_size = self.config.STYLE_TEMPLATE_IMAGE_SIZE
        return self.generate_image(full_prompt, output_path, aspect_ratio=aspect_ratio, image_size=image_size)

    def generate_ppt_page(self, page_content, style_reference, output_path):
        """生成PPT页面（基于样式模板）"""
        logger.info(f"生成PPT页面，样式参考: {style_reference}")

        # 加载提示词模板
        prompt_template = self.load_prompt('page_generation.txt')

        # 根据是否有样式模板，构建不同的样式参考说明
        if style_reference and os.path.exists(style_reference):
            style_desc = "我已提供一张样式模板图片作为参考，请严格参考该图片的配色方案、布局风格、字体设计和视觉元素，生成与之风格一致的PPT页面"
        else:
            style_desc = "使用现代简约的设计风格"

        full_prompt = prompt_template.format(
            page_content=page_content,
            style_reference=style_desc
        )

        # 使用配置的PPT页面分辨率
        aspect_ratio = self.config.IMAGE_ASPECT_RATIO
        image_size = self.config.PPT_PAGE_IMAGE_SIZE

        # 如果有样式模板，将其作为参考图片传入
        if style_reference and os.path.exists(style_reference):
            logger.info(f"使用样式模板图片: {style_reference}")
            return self.generate_image_with_reference(full_prompt, style_reference, output_path, aspect_ratio=aspect_ratio, image_size=image_size)
        else:
            logger.warning("没有样式模板参考，直接生成")
            return self.generate_image(full_prompt, output_path, aspect_ratio=aspect_ratio, image_size=image_size)

    def generate_image_with_reference(self, prompt, reference_image_path, output_path, aspect_ratio="16:9", image_size="2K"):
        """使用参考图片生成新图片（图片编辑功能）"""
        logger.info(f"开始生成图片（带参考图片）: {output_path}")
        logger.debug(f"提示词: {prompt[:100]}...")
        logger.info(f"参考图片: {reference_image_path}")
        logger.info(f"图片配置: 比例={aspect_ratio}, 尺寸={image_size}")

        def api_call():
            logger.info(f"调用Gemini {self.model_name} 生成图片（带参考）")

            # 加载参考图片并转换为base64
            reference_image = Image.open(reference_image_path)
            logger.info(f"参考图片已加载: {reference_image.size}")
            
            # 将图片转换为base64
            buffered = BytesIO()
            reference_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 构建API URL
            api_url = f"{self.api_base_url}/v1beta/models/{self.model_name}:streamGenerateContent"

            # 构建generationConfig
            generation_config = {
                "responseModalities": ["IMAGE"]
            }

            # 只有 gemini-3.0 开头的模型才支持 imageConfig 参数
            if self.model_name.startswith("gemini-3.0"):
                generation_config["imageConfig"] = {
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size
                }
                logger.info(f"模型 {self.model_name} 支持 imageConfig，使用配置: aspect_ratio={aspect_ratio}, image_size={image_size}")
            else:
                logger.warning(f"模型 {self.model_name} 不支持 imageConfig 参数，将忽略 aspect_ratio 和 image_size 配置")

            # 构建请求体（同时传入文字和图片）
            request_body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": img_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": generation_config
            }
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 设置请求参数（API Key）
            params = {
                "key": self.api_key
            }
            
            try:
                # 发送请求
                response = requests.post(
                    api_url,
                    json=request_body,
                    headers=headers,
                    params=params,
                    timeout=self.config.API_TIMEOUT
                )
                
                logger.info(f"API 返回，状态码: {response.status_code}")
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"API 返回错误: {response.text}")
                    raise Exception(f"API返回错误状态码 {response.status_code}: {response.text}")
                
                # 解析响应（流式响应）
                response_text = response.text
                logger.debug(f"响应内容: {response_text[:500]}...")
                
                # 解析流式响应中的图片数据
                image_data = None
                for line in response_text.strip().split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # 去掉 "data: " 前缀
                            if 'candidates' in data:
                                for candidate in data['candidates']:
                                    if 'content' in candidate and 'parts' in candidate['content']:
                                        for part in candidate['content']['parts']:
                                            if 'inlineData' in part:
                                                image_data = part['inlineData']['data']
                                                logger.info("从响应中提取图片数据")
                                                break
                                    if image_data:
                                        break
                            if image_data:
                                break
                        except json.JSONDecodeError:
                            continue
                
                if not image_data:
                    raise Exception("Gemini未返回图片数据")
                
                # 解码base64图片数据
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
                
                # 保存图片
                image.save(output_path)
                logger.info(f"图片已保存: {output_path}")
                return output_path
                
            except requests.exceptions.Timeout:
                logger.error(f"API 调用超时")
                raise Exception(f"API调用超时（{self.config.API_TIMEOUT}秒）")
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {type(e).__name__}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"API 调用异常: {type(e).__name__}: {str(e)}")
                raise

        # 调用重试机制，失败时抛出异常
        return self.retry_api_call(api_call)
