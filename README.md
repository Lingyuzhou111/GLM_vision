# GLM_vision

GLM_vision 是一款适用于 chatgpt-on-wechat 的图像和视频分析插件，基于智谱GLM-4V视觉模型，支持通过URL链接分析图片和视频内容。

智谱的多模态模型GLM-4V-FLASH最近全面免费开放。同时本人跟着WaytoAGI的共学教程也申请到了智谱AI平台的多个模型免费资源包，内含charglm-3、glm-4-air、glm-4-plus、glm-4v-plus等多个高智能对话模型和多模态模型的token 300万至5000万不等，有效期一个月。

本着不浪费资源的原则，于是就有了这个基于智谱多模态模型识别图片和视频的插件。

智谱GLM-4V-PLUS体验地址: https://open.bigmodel.cn/console/trialcenter?modelCode=glm-4v-plus

该插件使用起来非常简单，只需按以下步骤操作即可。

### 一. 获取API密钥
1. 注册并登录智谱AI开放平台 https://open.bigmodel.cn/
2. 在控制台创建API密钥并复制备用

### 二. 安装插件和配置config文件
1. 在微信机器人聊天窗口输入命令安装插件：
   ```
   #installp https://github.com/Lingyuzhou111/GLM_vision.git
   ```
2. 安装依赖：在插件目录打开终端，输入指令pip install -r requirements.txt，等待安装完成

3. 配置 config.json 文件，需要设置以下参数：
   ```json
   {
     "api": {
       "base_url": "https://open.bigmodel.cn/api/paas/v4",
       "model": "glm-4v-plus",
       "timeout": 60,
       "key": "YOUR_API_KEY",
       "temperature": 0.8
     },
     "image": {
       "max_size": 5,
       "max_pixels": 6000
     },
     "video": {
       "max_size": 20,
       "max_duration": 30
     }
   }
   ```

4. 重启 chatgpt-on-wechat 项目

5. 在微信机器人聊天窗口输入 #scanp 命令扫描新插件

6. 输入 #help GLM_vision 查看帮助信息，确认插件安装成功

### 三. 使用说明
1. 分析图片：
   - 发送"智谱识图 [图片URL]"或"分析图片 [图片URL]"或"看图 [图片URL]"
   - 支持的图片格式：jpg, jpeg, png, webp
   - 图片大小限制：5MB
   - 最大像素：6000px

2. 分析视频：
   - 发送"智谱识视频 [视频URL]"或"分析视频 [视频URL]"或"看视频 [视频URL]"
   - 支持的视频格式：mp4
   - 视频大小限制：20MB
   - 视频时长限制：30秒

### 四. 常见问题
1. 如果分析失败，请检查：
   - API Key 是否正确配置
   - 网络连接是否正常
   - URL是否可以直接访问媒体文件
   - 媒体文件是否符合大小和格式要求

2. 如遇到其他问题，请在 GitHub 仓库提交 Issue

### 五. 版本信息
- 版本：1.0
- 作者：Lingyuzhou
- 最后更新：2024-12-10
- Github个人主页https://github.com/Lingyuzhou111
