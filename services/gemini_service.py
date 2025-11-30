"""Gemini API调用服务"""
import os
import json
import time
import requests


class GeminiService:
    """Gemini服务"""

    def __init__(self, config):
        self.config = config
        self.api_key = config.GEMINI_API_KEY
        self.api_base_url = config.GEMINI_API_BASE_URL
        self.model = config.GEMINI_MODEL

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
                print(f"[Gemini] 尝试第 {attempt + 1}/{max_retries} 次调用")
                return func()
            except Exception as e:
                print(f"[Gemini] 第 {attempt + 1} 次调用失败: {str(e)}")
                if attempt == max_retries - 1:
                    print(f"[Gemini] 已达到最大重试次数，放弃")
                    raise Exception(f'API调用失败，已重试{max_retries}次: {str(e)}')
                # 指数退避
                wait_time = self.config.RETRY_DELAY_BASE ** attempt
                print(f"[Gemini] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

    def generate_outline(self, knowledge_text, user_prompt, expected_pages):
        """生成PPT大纲"""
        print(f"[Gemini] 开始生成大纲，期望页数: {expected_pages}")
        # 加载提示词模板
        prompt_template = self.load_prompt('outline_generation.txt')
        print(f"[Gemini] 已加载提示词模板")

        # 构建完整提示词
        full_prompt = prompt_template.format(
            knowledge_text=knowledge_text[:10000],  # 限制知识库文本长度
            user_prompt=user_prompt,
            expected_pages=expected_pages
        )
        print(f"[Gemini] 提示词长度: {len(full_prompt)} 字符")

        def api_call():
            import requests
            import sys
            
            # 构建API URL
            api_url = f"{self.api_base_url}/v1beta/models/{self.model}:generateContent"
            print(f"[Gemini] API URL: {api_url}")
            print(f"[Gemini] 调用 Gemini API，超时时间: {self.config.API_TIMEOUT}秒")
            sys.stdout.flush()  # 强制刷新输出
            
            # 构建请求体
            request_body = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 8192,
                }
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
                
                print(f"[Gemini] API 返回，状态码: {response.status_code}")
                
                # 检查响应状态
                if response.status_code != 200:
                    print(f"[Gemini] API 返回错误: {response.text}")
                    raise Exception(f"API返回错误状态码 {response.status_code}: {response.text}")
                
                # 解析响应
                response_data = response.json()
                
                # 提取生成的文本
                if 'candidates' not in response_data or len(response_data['candidates']) == 0:
                    print(f"[Gemini] API 响应中没有candidates: {response_data}")
                    raise Exception("API响应格式错误：没有candidates")
                
                candidate = response_data['candidates'][0]
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    print(f"[Gemini] API 响应格式错误: {candidate}")
                    raise Exception("API响应格式错误：没有content或parts")
                
                text = candidate['content']['parts'][0]['text'].strip()
                print(f"[Gemini] API 返回成功")
                print(f"[Gemini] 响应文本长度: {len(text)} 字符")
                print(f"[Gemini] 响应文本前200字符: {text[:200]}")
                
            except requests.exceptions.Timeout:
                print(f"[Gemini] API 调用超时")
                raise Exception(f"API调用超时（{self.config.API_TIMEOUT}秒）")
            except requests.exceptions.RequestException as e:
                print(f"[Gemini] 请求异常: {type(e).__name__}: {str(e)}")
                raise
            except Exception as e:
                print(f"[Gemini] API 调用异常: {type(e).__name__}: {str(e)}")
                raise
            
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            try:
                result = json.loads(text.strip())
                print(f"[Gemini] JSON 解析成功")
                return result
            except json.JSONDecodeError as e:
                print(f"[Gemini] JSON 解析失败: {str(e)}")
                print(f"[Gemini] 尝试解析的文本: {text[:500]}")
                raise

        return self.retry_api_call(api_call)

    def build_outline_prompt(self, knowledge_text, user_prompt, expected_pages):
        """构建大纲生成提示词"""
        # 加载提示词模板
        prompt_template = self.load_prompt('outline_generation.txt')

        # 构建完整提示词
        full_prompt = prompt_template.format(
            knowledge_text=knowledge_text[:10000],  # 限制知识库文本长度
            user_prompt=user_prompt,
            expected_pages=expected_pages
        )

        return full_prompt

    def generate_outline_with_custom_prompt(self, custom_prompt):
        """使用自定义提示词生成大纲"""
        def api_call():
            import requests
            import sys
            
            # 构建API URL
            api_url = f"{self.api_base_url}/v1beta/models/{self.model}:generateContent"
            print(f"[Gemini] API URL: {api_url}")
            print(f"[Gemini] 使用自定义提示词调用 Gemini API，超时时间: {self.config.API_TIMEOUT}秒")
            sys.stdout.flush()
            
            # 构建请求体
            request_body = {
                "contents": [{
                    "parts": [{
                        "text": custom_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 8192,
                }
            }
            
            # 设置请求头和参数
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}
            
            try:
                # 发送请求
                response = requests.post(
                    api_url,
                    json=request_body,
                    headers=headers,
                    params=params,
                    timeout=self.config.API_TIMEOUT
                )
                
                print(f"[Gemini] API 返回，状态码: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[Gemini] API 返回错误: {response.text}")
                    raise Exception(f"API返回错误状态码 {response.status_code}: {response.text}")
                
                # 解析响应
                response_data = response.json()
                text = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                print(f"[Gemini] API 返回成功，响应文本长度: {len(text)} 字符")
                
            except requests.exceptions.Timeout:
                print(f"[Gemini] API 调用超时")
                raise Exception(f"API调用超时（{self.config.API_TIMEOUT}秒）")
            except Exception as e:
                print(f"[Gemini] API 调用异常: {type(e).__name__}: {str(e)}")
                raise
            
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            try:
                result = json.loads(text.strip())
                print(f"[Gemini] JSON 解析成功")
                return result
            except json.JSONDecodeError as e:
                print(f"[Gemini] JSON 解析失败: {str(e)}")
                print(f"[Gemini] 尝试解析的文本: {text[:500]}")
                raise

        return self.retry_api_call(api_call)

    def regenerate_outline_page(self, knowledge_text, user_prompt, page_number, existing_pages, extra_prompt=''):
        """重新生成单页大纲"""
        import requests
        
        # 加载提示词模板
        prompt_template = self.load_prompt('outline_generation.txt')

        # 构建上下文
        context = f"现有大纲:\n"
        for page in existing_pages:
            context += f"第{page['page_number']}页: {page['title']}\n"

        # 构建完整提示词
        extra_instruction = f"\n\n额外要求：{extra_prompt}" if extra_prompt else ""
        
        full_prompt = f"""{prompt_template}

{context}

请重新生成第{page_number}页的内容，要求与其他页面保持连贯性。{extra_instruction}

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
            # 构建API URL
            api_url = f"{self.api_base_url}/v1beta/models/{self.model}:generateContent"
            
            # 构建请求体
            request_body = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 8192,
                }
            }
            
            # 设置请求头和参数
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}
            
            # 发送请求
            response = requests.post(
                api_url,
                json=request_body,
                headers=headers,
                params=params,
                timeout=self.config.API_TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"API返回错误状态码 {response.status_code}: {response.text}")
            
            # 解析响应
            response_data = response.json()
            text = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # 移除可能的markdown代码块标记
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            return json.loads(text.strip())

        return self.retry_api_call(api_call)
