import os
import json
import requests
import plugins
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from config import conf
from plugins import Plugin, Event, EventContext, EventAction
from PIL import Image
from io import BytesIO
import urllib.request
import re
import cv2
import numpy as np
import tempfile

@plugins.register(name="GLM_vision", desc="GLM-4V视觉模型插件", version="1.0", author="Lingyuzhou")
class GLMVision(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 设置配置项
            self.config = {
                "api_base": config["api"]["base_url"],
                "model": config["api"]["model"],
                "timeout": config["api"]["timeout"],
                "api_key": config["api"]["key"],
                "temperature": config["api"].get("temperature", 0.8),  # 添加temperature配置，默认0.8
                "image_max_size": config["image"]["max_size"],
                "image_max_pixels": config["image"]["max_pixels"],
                "video_max_size": config["video"]["max_size"],
                "video_max_duration": config["video"]["max_duration"]
            }
            
            # 验证API密钥
            if not self.config["api_key"]:
                raise Exception("[GLM Vision] API key not found in config.json")
            
            # 关键词
            self.keywords = {
                "image": ["智谱识图", "分析图片", "看图"],
                "video": ["智谱识视频", "分析视频", "看视频"]
            }
            
            logger.info(f"[GLM Vision] Plugin initialized successfully with model: {self.config['model']}")
            
            # 注册事件处理器
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            
        except Exception as e:
            logger.error(f"[GLM Vision] Failed to initialize plugin: {e}")
            raise

    def on_handle_context(self, e_context: EventContext):
        """处理消息"""
        context = e_context['context']
        
        if context.type == ContextType.TEXT:
            # 处理文本消息，查找URL
            text = context.content.strip()
            
            # 检查是否包含关键词
            is_image = any(kw in text for kw in self.keywords["image"])
            is_video = any(kw in text for kw in self.keywords["video"])
            
            if not (is_image or is_video):
                return
            
            # 提取URL
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, text)
            
            if not urls:
                reply = Reply(ReplyType.TEXT, "请提供媒体文件的URL链接")
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            
            url = urls[0]  # 使用第一个URL
            logger.info(f"[GLM Vision] Processing URL: {url}")
            
            try:
                if is_image:
                    # 对于图片，下载并处理
                    media_data = self._download_media(url)
                    processed_data = self._process_image(media_data, url)
                    if processed_data:
                        content = [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": processed_data}
                                },
                                {
                                    "type": "text",
                                    "text": "请描述这张图片"
                                }
                            ]
                        }]
                else:  # is_video
                    # 对于视频，使用官方文档的格式
                    content = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": url
                                }
                            },
                            {
                                "type": "text",
                                "text": "请描述这个视频"
                            }
                        ]
                    }]
                
                # 调用API
                response = self._call_glm_api(content)
                
                if response and "choices" in response:
                    reply_text = response["choices"][0]["message"]["content"]
                else:
                    reply_text = "抱歉，处理失败"
                    
                reply = Reply(ReplyType.TEXT, reply_text)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                
            except Exception as e:
                logger.error(f"[GLM Vision] Error processing media: {str(e)}")
                reply = Reply(ReplyType.TEXT, f"处理失败: {str(e)}")
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS

    def _download_media(self, url):
        """下载媒体文件"""
        try:
            response = urllib.request.urlopen(url)
            return response.read()
        except Exception as e:
            logger.error(f"[GLM Vision] Failed to download media: {e}")
            raise

    def _process_image(self, image_content, original_url):
        """处理图片内容"""
        try:
            # 检查图片大小
            size_mb = len(image_content) / (1024 * 1024)
            if size_mb > self.config["image_max_size"]:
                raise Exception(f"图片大小超过限制 ({size_mb:.1f}MB > {self.config['image_max_size']}MB)")
            
            # 检查图片尺寸
            img = Image.open(BytesIO(image_content))
            if max(img.size) > self.config["image_max_pixels"]:
                raise Exception(f"图片尺寸超过限制 ({max(img.size)} > {self.config['image_max_pixels']})")
            
            # 直接返回原始URL
            return original_url
            
        except Exception as e:
            logger.error(f"[GLM Vision] Image processing error: {e}")
            raise

    def _call_glm_api(self, messages):
        """调用GLM-4V API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config["model"],
                "messages": messages,
                "stream": False,
                "temperature": self.config.get("temperature", 0.8),  # 使用配置文件中的temperature，默认值为0.8
                "top_p": 0.7
            }
            
            # 为日志创建一个副本，替换敏感信息
            log_data = {
                "model": data["model"],
                "messages": [],
                "stream": data["stream"],
                "temperature": data["temperature"],
                "top_p": data["top_p"]
            }
            
            # 复制消息内容，替换URL为占位符
            for msg in data["messages"]:
                log_msg = {"role": msg["role"], "content": []}
                for content in msg["content"]:
                    content_copy = content.copy()
                    if "video_url" in content:
                        content_copy["video_url"] = {"url": "[VIDEO_URL]"}
                    elif "image_url" in content:
                        content_copy["image_url"] = {"url": "[IMAGE_URL]"}
                    log_msg["content"].append(content_copy)
                log_data["messages"].append(log_msg)
            
            logger.info(f"[GLM Vision] Sending API request to {self.config['api_base']}")
            logger.debug(f"[GLM Vision] Request payload: {json.dumps(log_data, ensure_ascii=False)}")
            
            url = f"{self.config['api_base']}/chat/completions"
            response = requests.post(url, headers=headers, json=data, timeout=self.config["timeout"])
            
            if response.status_code == 200:
                result = response.json()
                logger.info("[GLM Vision] Received API response successfully")
                logger.debug("[GLM Vision] Response received")
                return result
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                logger.error(f"[GLM Vision] {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "API请求超时"
            logger.error(f"[GLM Vision] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"[GLM Vision] API call error: {e}")
            raise

    def get_help_text(self, **kwargs):
        help_text = """智谱AI视觉分析插件使用说明：

1. 分析图片：
   发送"智谱识图 [图片URL]"或"分析图片 [图片URL]"或"看图 [图片URL]"

2. 分析视频：
   发送"智谱识视频 [视频URL]"或"分析视频 [视频URL]"或"看视频 [视频URL]"

图片要求：
- 支持格式：jpg、png、jpeg
- 大小限制：{}MB
- 最大像素：{}像素

视频要求：
- 支持格式：mp4
- 大小限制：{}MB
- 时长限制：{}秒

注意：请确保提供的URL可以直接访问媒体文件""".format(
            self.config["image_max_size"],
            self.config["image_max_pixels"],
            self.config["video_max_size"],
            self.config["video_max_duration"]
        )
        return help_text
