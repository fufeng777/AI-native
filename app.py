import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import base64

# 页面配置
st.set_page_config(
    page_title="AI Native 能力评估平台",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入 AI 分析模块
from ai_analyzer import (
    AIResumeAnalyzer, 
    get_analyzer, 
    render_ai_settings, 
    render_ai_analysis_result,
    AI_NATIVE_DIMENSIONS,
    LEVEL_DEFINITIONS
)

# 数据存储路径
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CANDIDATES_FILE = DATA_DIR / "candidates.json"
RESUMES_DIR = DATA_DIR / "resumes"
RESUMES_DIR.mkdir(exist_ok=True)

# 快速判断清单
QUICK_CHECKLIST = [
    "候选人第一反应是'AI'而不是'人'（接到新任务时的本能指向）",
    "候选人是否拥有'自己的方法论'（对AI的使用有提炼、有优化）",
    "候选人是否改造过自己的工作流（用AI改变了做法）",
    "候选人对AI的吐槽是否具体（能精准指出不靠谱之处）",
    "候选人有没有'AI焦虑'（积极意义上怕掉队，持续关注前沿）"
]

# 预设职位类别
JOB_CATEGORIES = [
    "产品", "运营", "算法", "工程", "设计", "市场", "销售", "人力资源", "财务", "其他"
]

# 个人版趣味等级定义
FUN_TITLES = {
    "L0": {"title": "AI 原始人", "description": "你还在用石器时代的方式工作，AI对你来说就像外星科技", "emoji": "🦣", "color": "#9CA3AF",
           "tagline": "碳基生物最后的倔强", "advice": "别怕AI，它不会取代你...暂时不会"},
    "L1": {"title": "AI 玩家", "description": "你已经踏入AI世界的大门，偶尔玩玩ChatGPT写写邮件", "emoji": "🎮", "color": "#60A5FA",
           "tagline": "AI世界的观光客", "advice": "试着把AI用到更多场景，你会发现新大陆"},
    "L2": {"title": "AI 高手", "description": "AI已经是你的得力助手，工作效率比同事快3倍", "emoji": "🚀", "color": "#34D399",
           "tagline": "人机协作的典范", "advice": "你已经超越90%的人，继续探索更深层的AI用法"},
    "L3": {"title": "AI 大师", "description": "AI已经融入你的血液，你甚至开始用AI来管理你的AI", "emoji": "⚡", "color": "#FBBF24",
           "tagline": "碳硅融合体", "advice": "你就是未来的样子，请带我们飞"}
}

# 8种AI人格类型（类似MBTI）
AI_PERSONALITIES = {
    "PROMPT-A": {"name": "提示词建筑师", "emoji": "🏗️", "desc": "你擅长用精确的语言指挥AI，写出的Prompt堪比艺术品",
                  "trait": "逻辑缜密 | 追求精准 | 结构化思维", "color": "#3B82F6",
                  "tools": ["ChatGPT", "Claude", "Gemini"], "scene": "写Prompt像写代码，每个字都有意义"},
    "AGENT-C": {"name": "智能体指挥官", "emoji": "🎯", "desc": "你善于构建AI Agent工作流，让多个AI协同作战",
                "trait": "全局视角 | 系统思维 | 善于编排", "color": "#EF4444",
                "tools": ["Coze", "Dify", "LangChain"], "scene": "你的AI团队比你整个部门都忙"},
    "CREATE-X": {"name": "创意炼金师", "emoji": "🎨", "desc": "你用AI释放无限创意，从文字到图像到视频无所不能",
                  "trait": "天马行空 | 审美在线 | 善于表达", "color": "#A855F7",
                  "tools": ["Midjourney", "Suno", "Runway"], "scene": "你的创意产出速度让甲方怀疑人生"},
    "CODE-N": {"name": "代码忍者", "emoji": "💻", "desc": "AI编程是你的超能力，Cursor和Copilot是你的双刀",
               "trait": "技术驱动 | 效率至上 | 持续学习", "color": "#10B981",
               "tools": ["Cursor", "GitHub Copilot", "v0"], "scene": "你一个人就是一个开发团队"},
    "DATA-W": {"name": "数据巫师", "emoji": "🔮", "desc": "你善于用AI洞察数据背后的秘密，让数据说话",
               "trait": "分析思维 | 数据敏感 | 洞察力强", "color": "#F59E0B",
               "tools": ["ChatGPT数据分析", "NotebookLM", "Perplexity"], "scene": "你看到数据就能预测未来"},
    "AUTO-B": {"name": "自动化狂人", "emoji": "🤖", "desc": "能用AI自动化的绝不手动，你的工作流全是自动的",
               "trait": "效率极致 | 流程思维 | 懒得优雅", "color": "#EC4899",
               "tools": ["Zapier", "Make", "n8n"], "scene": "别人上班你在摸鱼，因为AI替你干了"},
    "CHAT-S": {"name": "AI知己", "emoji": "💬", "desc": "你和AI的关系超越了工具，更像是思维伙伴和灵魂伴侣",
               "trait": "善于沟通 | 思想开放 | 情感丰富", "color": "#06B6D4",
               "tools": ["ChatGPT", "Pi", "Character.AI"], "scene": "你跟AI聊天的记录比跟朋友的还长"},
    "LEARN-P": {"name": "学习狂魔", "emoji": "📚", "desc": "AI是你的私人导师，任何新领域都能快速入门",
                "trait": "好奇心强 | 快速学习 | 知识面广", "color": "#8B5CF6",
                "tools": ["Coursera AI", "Khan Academy", "Perplexity"], "scene": "你的学习速度让爱因斯坦都嫉妒"}
}

# 成就系统
ACHIEVEMENTS = [
    {"id": "first_chat", "name": "初次接触", "desc": "第一次和AI对话", "icon": "🌱", "condition": lambda s: True},
    {"id": "prompt_master", "name": "提示词大师", "desc": "能用精准的Prompt获得理想结果", "icon": "✍️", "condition": lambda s: s.get("q2_score", 0) >= 80},
    {"id": "tool_collector", "name": "工具收藏家", "desc": "使用过5种以上AI工具", "icon": "🔧", "condition": lambda s: s.get("tool_count", 0) >= 5},
    {"id": "auto_flow", "name": "流程自动化", "desc": "用AI构建过自动化工作流", "icon": "⚙️", "condition": lambda s: s.get("q8_score", 0) >= 80},
    {"id": "ai_friend", "name": "AI之友", "desc": "把AI当成朋友而不只是工具", "icon": "🤝", "condition": lambda s: s.get("q10_score", 0) >= 80},
    {"id": "speed_learner", "name": "速学达人", "desc": "用AI在1周内学会新技能", "icon": "⚡", "condition": lambda s: s.get("q4_score", 0) >= 80},
    {"id": "boundary_keeper", "name": "边界守卫", "desc": "能精准识别AI的错误和幻觉", "icon": "🛡️", "condition": lambda s: s.get("q6_score", 0) >= 70},
    {"id": "creative_mind", "name": "创意无限", "desc": "用AI创作过令人惊叹的作品", "icon": "🌈", "condition": lambda s: s.get("q13_score", 0) >= 80},
    {"id": "night_owl", "name": "深夜AI玩家", "desc": "凌晨还在和AI讨论人生", "icon": "🦉", "condition": lambda s: s.get("q16_score", 0) >= 60},
    {"id": "evangelist", "name": "AI布道者", "desc": "逢人就安利AI工具", "icon": "📣", "condition": lambda s: s.get("q17_score", 0) >= 80},
    {"id": "philosopher", "name": "AI哲学家", "desc": "思考过AI与人类的关系", "icon": "🧠", "condition": lambda s: s.get("q19_score", 0) >= 60},
    {"id": "master", "name": "AI大师", "desc": "综合评分达到L3级别", "icon": "👑", "condition": lambda s: s.get("total_score", 0) >= 80}
]

# AI工具列表（60+工具，包含公司和功能介绍）
AI_TOOLS_LIST = [
    # === 对话大模型 ===
    {"name": "ChatGPT", "category": "对话大模型", "icon": "static/icons/openai.svg",
     "company": "OpenAI", "desc": "全球最流行的AI对话助手，支持文本、图像、语音多模态交互，具备强大的推理和创作能力"},
    {"name": "Claude", "category": "对话大模型", "icon": "static/icons/anthropic.svg",
     "company": "Anthropic", "desc": "以安全性和长文本处理能力著称，擅长代码生成、文档分析和深度推理"},
    {"name": "Gemini", "category": "对话大模型", "icon": "static/icons/google.svg",
     "company": "Google", "desc": "谷歌旗舰AI模型，原生多模态，支持超长上下文，与Google生态深度整合"},
    {"name": "GPT-4o", "category": "对话大模型", "icon": "static/icons/openai.svg",
     "company": "OpenAI", "desc": "OpenAI最新旗舰模型，支持实时语音对话、图像理解，响应速度极快"},
    {"name": "o1/o3", "category": "对话大模型", "icon": "static/icons/openai.svg",
     "company": "OpenAI", "desc": "OpenAI推理模型系列，擅长数学、编程、科学等需要深度思考的复杂任务"},

    # === 国产大模型 ===
    {"name": "文心一言", "category": "国产大模型", "icon": "static/icons/baidu.svg",
     "company": "百度", "desc": "百度推出的知识增强大模型，在中文理解和知识问答方面表现出色"},
    {"name": "通义千问", "category": "国产大模型", "icon": "static/icons/alibabadotcom.svg",
     "company": "阿里云", "desc": "阿里达摩院研发，支持长文档处理，与阿里生态产品深度整合"},
    {"name": "豆包", "category": "国产大模型", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "字节跳动出品，语音交互体验优秀，适合日常对话和娱乐场景"},
    {"name": "Kimi", "category": "国产大模型", "icon": "static/icons/moon.svg",
     "company": "月之暗面", "desc": "以200万字超长上下文处理能力闻名，适合长文档阅读和总结"},
    {"name": "DeepSeek", "category": "国产大模型", "icon": "static/icons/deepseek.svg",
     "company": "深度求索", "desc": "开源大模型，推理能力强劲，性价比极高，深受开发者喜爱"},
    {"name": "智谱清言", "category": "国产大模型", "icon": "static/icons/zhipu.svg",
     "company": "智谱AI", "desc": "清华系AI公司出品，GLM架构，在学术和代码场景表现优秀"},
    {"name": "腾讯元宝", "category": "国产大模型", "icon": "static/icons/tencent.svg",
     "company": "腾讯", "desc": "腾讯混元大模型，与微信、QQ等腾讯产品生态打通"},
    {"name": "讯飞星火", "category": "国产大模型", "icon": "static/icons/iflytek.svg",
     "company": "科大讯飞", "desc": "语音识别技术领先，在语音交互和办公场景有独特优势"},
    {"name": "天工AI", "category": "国产大模型", "icon": "static/icons/kunlun.svg",
     "company": "昆仑万维", "desc": "支持AI搜索、AI音乐、AI绘画等多功能，娱乐属性强"},

    # === AI绘画 ===
    {"name": "Midjourney", "category": "AI绘画", "icon": "static/icons/midjourney.svg",
     "company": "Midjourney", "desc": "AI绘画领域标杆，画面质量极高，艺术风格独特，适合创意设计和艺术创作"},
    {"name": "Stable Diffusion", "category": "AI绘画", "icon": "static/icons/stability.svg",
     "company": "Stability AI", "desc": "开源AI绘画模型，可本地部署，社区生态丰富，支持大量自定义模型"},
    {"name": "DALL-E 3", "category": "AI绘画", "icon": "static/icons/openai.svg",
     "company": "OpenAI", "desc": "OpenAI出品，语义理解能力极强，能准确理解复杂描述生成图像"},
    {"name": "Adobe Firefly", "category": "AI绘画", "icon": "static/icons/adobe.svg",
     "company": "Adobe", "desc": "Adobe官方AI工具，与Photoshop等设计软件无缝集成，商用安全"},
    {"name": "即梦AI", "category": "AI绘画", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "字节旗下AI绘画工具，中文提示词理解好，适合国内用户"},
    {"name": "可灵AI", "category": "AI绘画", "icon": "static/icons/bytedance.svg",
     "company": "快手", "desc": "快手出品，支持图生视频，在视频生成领域表现突出"},
    {"name": "LiblibAI", "category": "AI绘画", "icon": "static/icons/liblib.svg",
     "company": "Liblib", "desc": "国内领先的AI绘画平台，汇聚大量优质模型，社区活跃"},
    {"name": "通义万相", "category": "AI绘画", "icon": "static/icons/alibabadotcom.svg",
     "company": "阿里云", "desc": "阿里出品，支持文生图、图生图，中文场景优化好"},

    # === AI视频 ===
    {"name": "Runway", "category": "AI视频", "icon": "static/icons/runway.svg",
     "company": "Runway", "desc": "AI视频生成先驱，Gen-3模型效果惊艳，支持文生视频、图生视频"},
    {"name": "Pika", "category": "AI视频", "icon": "static/icons/pika.svg",
     "company": "Pika Labs", "desc": "专注AI视频生成，操作简单，适合快速生成短视频内容"},
    {"name": "HeyGen", "category": "AI视频", "icon": "static/icons/heygen.svg",
     "company": "HeyGen", "desc": "AI数字人视频生成，支持多语言口型同步，适合营销视频制作"},
    {"name": "Sora", "category": "AI视频", "icon": "static/icons/openai.svg",
     "company": "OpenAI", "desc": "OpenAI视频生成模型，可生成60秒高质量视频，物理模拟能力强"},
    {"name": "剪映AI", "category": "AI视频", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "剪映内置AI功能，支持AI配音、AI字幕、AI剪辑，国内用户友好"},
    {"name": "快影AI", "category": "AI视频", "icon": "static/icons/bytedance.svg",
     "company": "快手", "desc": "快手官方剪辑工具，AI功能丰富，适合短视频创作者"},

    # === AI音乐 ===
    {"name": "Suno", "category": "AI音乐", "icon": "static/icons/suno.svg",
     "company": "Suno", "desc": "AI音乐生成神器，输入文字即可生成完整歌曲，支持多种风格"},
    {"name": "Udio", "category": "AI音乐", "icon": "static/icons/udio.svg",
     "company": "Udio", "desc": "高品质AI音乐生成，人声效果逼真，适合专业音乐创作"},
    {"name": "Mureka", "category": "AI音乐", "icon": "static/icons/mureka.svg",
     "company": "Mureka", "desc": "AI音乐生成平台，支持多种乐器和风格，操作简单"},
    {"name": "天工音乐", "category": "AI音乐", "icon": "static/icons/kunlun.svg",
     "company": "昆仑万维", "desc": "国内AI音乐生成工具，中文歌曲生成效果好"},

    # === AI编程 ===
    {"name": "Cursor", "category": "AI编程", "icon": "static/icons/cursor.svg",
     "company": "Cursor", "desc": "基于VSCode的AI代码编辑器，支持GPT-4和Claude，代码补全和重构能力极强"},
    {"name": "GitHub Copilot", "category": "AI编程", "icon": "static/icons/github.svg",
     "company": "GitHub/OpenAI", "desc": "GitHub官方AI编程助手，与IDE深度集成，代码建议准确率高"},
    {"name": "Trae", "category": "AI编程", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "字节推出的AI编程工具，对标Cursor，免费使用Claude模型"},
    {"name": "v0.dev", "category": "AI编程", "icon": "static/icons/vercel.svg",
     "company": "Vercel", "desc": "AI生成React组件和前端代码，输入描述即可生成可运行的UI代码"},
    {"name": "Windsurf", "category": "AI编程", "icon": "static/icons/codeium.svg",
     "company": "Codeium", "desc": "Codeium出品，支持AI代理模式，可自动执行多步骤编程任务"},
    {"name": "Replit Agent", "category": "AI编程", "icon": "static/icons/replit.svg",
     "company": "Replit", "desc": "Replit的AI编程助手，支持从自然语言描述生成完整应用"},
    {"name": "Codeium", "category": "AI编程", "icon": "static/icons/codeium.svg",
     "company": "Codeium", "desc": "免费的AI代码补全工具，支持70+编程语言，响应速度快"},
    {"name": "Tabnine", "category": "AI编程", "icon": "static/icons/tabnine.svg",
     "company": "Tabnine", "desc": "老牌AI代码补全工具，支持本地部署，隐私保护好"},
    {"name": "Amazon CodeWhisperer", "category": "AI编程", "icon": "static/icons/amazonaws.svg",
     "company": "AWS", "desc": "亚马逊AI编程助手，与AWS服务深度集成，适合云开发"},
    {"name": "JetBrains AI", "category": "AI编程", "icon": "static/icons/jetbrains.svg",
     "company": "JetBrains", "desc": "JetBrains IDE内置AI助手，支持IntelliJ、PyCharm等全系产品"},

    # === AI搜索 ===
    {"name": "Perplexity", "category": "AI搜索", "icon": "static/icons/perplexity.svg",
     "company": "Perplexity", "desc": "AI搜索引擎，直接给出带引用来源的答案，信息准确可靠"},
    {"name": "秘塔AI搜索", "category": "AI搜索", "icon": "static/icons/metaso.svg",
     "company": "秘塔科技", "desc": "国内AI搜索引擎，无广告，结构化展示搜索结果，学术搜索强"},
    {"name": "Devv.ai", "category": "AI搜索", "icon": "static/icons/devv.svg",
     "company": "Devv", "desc": "专为开发者设计的AI搜索，编程问题回答精准，支持GitHub搜索"},
    {"name": "You.com", "category": "AI搜索", "icon": "static/icons/you.svg",
     "company": "You.com", "desc": "AI搜索引擎，支持多种AI模式，隐私保护好，可定制搜索偏好"},
    {"name": "Bing Copilot", "category": "AI搜索", "icon": "static/icons/microsoft.svg",
     "company": "微软", "desc": "Bing搜索引擎内置AI助手，与Edge浏览器深度集成"},
    {"name": "Globe Explorer", "category": "AI搜索", "icon": "static/icons/globe.svg",
     "company": "Globe", "desc": "可视化AI搜索，以思维导图形式展示搜索结果，适合探索性学习"},

    # === AI办公/效率 ===
    {"name": "Notion AI", "category": "AI办公", "icon": "static/icons/notion.svg",
     "company": "Notion", "desc": "Notion内置AI助手，支持写作、总结、翻译，与笔记深度整合"},
    {"name": "Gamma", "category": "AI办公", "icon": "static/icons/gamma.svg",
     "company": "Gamma", "desc": "AI生成PPT工具，输入主题自动生成精美演示文稿，设计感强"},
    {"name": "Tome", "category": "AI办公", "icon": "static/icons/tome.svg",
     "company": "Tome", "desc": "AI叙事工具，生成故事性强的PPT，适合融资路演和创意展示"},
    {"name": "飞书AI", "category": "AI办公", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "飞书内置AI助手，支持会议纪要、文档写作、智能问答"},
    {"name": "WPS AI", "category": "AI办公", "icon": "static/icons/wps.svg",
     "company": "金山", "desc": "WPS内置AI功能，支持文档生成、PDF解析、表格分析"},
    {"name": "Microsoft 365 Copilot", "category": "AI办公", "icon": "static/icons/microsoft.svg",
     "company": "微软", "desc": "Office全家桶AI助手，Word、Excel、PPT全面智能化"},
    {"name": "NotebookLM", "category": "AI办公", "icon": "static/icons/google.svg",
     "company": "Google", "desc": "Google出品，上传文档即可生成播客、摘要、问答，学习神器"},
    {"name": "Otter.ai", "category": "AI办公", "icon": "static/icons/otter.svg",
     "company": "Otter", "desc": "AI会议记录工具，实时转录、自动生成会议纪要"},
    {"name": "Fireflies.ai", "category": "AI办公", "icon": "static/icons/otter.svg",
     "company": "Fireflies", "desc": "AI会议助手，自动记录、搜索会议内容，支持多平台"},
    {"name": "Grammarly", "category": "AI办公", "icon": "static/icons/grammarly.svg",
     "company": "Grammarly", "desc": "AI写作助手，语法检查、风格优化，英文写作必备"},
    {"name": "DeepL Write", "category": "AI办公", "icon": "static/icons/deepl.svg",
     "company": "DeepL", "desc": "DeepL出品AI写作工具，翻译和改写能力极强"},

    # === AI Agent/自动化 ===
    {"name": "Coze", "category": "AI Agent", "icon": "static/icons/bytedance.svg",
     "company": "字节跳动", "desc": "字节跳动AI Bot开发平台，零代码搭建AI应用，可发布到抖音飞书"},
    {"name": "Dify", "category": "AI Agent", "icon": "static/icons/dify.svg",
     "company": "Dify", "desc": "开源LLM应用开发平台，支持工作流编排、RAG、Agent开发"},
    {"name": "LangChain", "category": "AI Agent", "icon": "static/icons/langchain.svg",
     "company": "LangChain", "desc": "最流行的LLM开发框架，构建复杂AI应用的基础设施"},
    {"name": "AutoGPT", "category": "AI Agent", "icon": "static/icons/autogpt.svg",
     "company": "AutoGPT", "desc": "自主AI Agent，可设定目标后自动分解任务并执行"},
    {"name": "Zapier AI", "category": "AI Agent", "icon": "static/icons/zapier.svg",
     "company": "Zapier", "desc": "Zapier集成AI功能，连接5000+应用，自动化工作流程"},
    {"name": "Make", "category": "AI Agent", "icon": "static/icons/make.svg",
     "company": "Make", "desc": "可视化自动化平台，支持复杂逻辑，比Zapier更灵活"},
    {"name": "n8n", "category": "AI Agent", "icon": "static/icons/n8n.svg",
     "company": "n8n", "desc": "开源工作流自动化工具，可自托管，适合技术用户"},
    {"name": "Flowise", "category": "AI Agent", "icon": "static/icons/flowise.svg",
     "company": "Flowise", "desc": "开源可视化LLM工作流构建工具，拖拽式搭建AI应用"},

    # === AI学习/教育 ===
    {"name": "Khanmigo", "category": "AI学习", "icon": "static/icons/khanacademy.svg",
     "company": "Khan Academy", "desc": "可汗学院AI导师，个性化辅导数学、科学等学科"},
    {"name": "Duolingo Max", "category": "AI学习", "icon": "static/icons/duolingo.svg",
     "company": "Duolingo", "desc": "多邻国AI功能，AI对话练习、解释答案，语言学习神器"},
    {"name": "Synthesis", "category": "AI学习", "icon": "static/icons/synthesis.svg",
     "company": "Synthesis", "desc": "AI数学辅导，通过对话引导学生自己找到答案"},
    {"name": "Elicit", "category": "AI学习", "icon": "static/icons/academic.svg",
     "company": "Elicit", "desc": "AI科研助手，自动搜索、总结学术论文，研究者必备"},
    {"name": "Consensus", "category": "AI学习", "icon": "static/icons/academic.svg",
     "company": "Consensus", "desc": "AI学术搜索引擎，基于2亿+论文给出科学共识答案"},
    {"name": "Scholarcy", "category": "AI学习", "icon": "static/icons/academic.svg",
     "company": "Scholarcy", "desc": "AI文献阅读助手，自动生成摘要、提取关键信息"},

    # === AI设计 ===
    {"name": "Canva AI", "category": "AI设计", "icon": "static/icons/canva.svg",
     "company": "Canva", "desc": "Canva内置AI功能，Magic Design一键生成设计，简单易用"},
    {"name": "Figma AI", "category": "AI设计", "icon": "static/icons/figma.svg",
     "company": "Figma", "desc": "Figma内置AI助手，自动生成设计、写设计说明"},
    {"name": "Looka", "category": "AI设计", "icon": "static/icons/looka.svg",
     "company": "Looka", "desc": "AI Logo生成器，输入品牌名自动生成Logo设计方案"},
    {"name": "Remove.bg", "category": "AI设计", "icon": "static/icons/removebg.svg",
     "company": "Remove.bg", "desc": "AI自动抠图，一键去除背景，效果精准"},
    {"name": "Upscayl", "category": "AI设计", "icon": "static/icons/upscayl.svg",
     "company": "Upscayl", "desc": "开源AI图片放大工具，无损提升图片分辨率"},
    {"name": "Clipdrop", "category": "AI设计", "icon": "static/icons/clipdrop.svg",
     "company": "Stability AI", "desc": "Stability AI出品，AI修图工具集，抠图、打光、扩图一站式"}
]

# === 趣味互动环节 ===

# 1. Prompt挑战关卡
PROMPT_CHALLENGES = [
    {
        "id": "prompt_1",
        "title": "初级：让AI讲个笑话",
        "desc": "测试基础Prompt能力",
        "task": "写一个Prompt让AI给你讲一个关于程序员的笑话",
        "example_good": "你是一个幽默的喜剧演员，请给我讲一个程序员才能听懂的笑话，要求有反转",
        "example_bad": "讲个笑话",
        "points": 10
    },
    {
        "id": "prompt_2",
        "title": "中级：角色扮演",
        "desc": "测试角色设定能力",
        "task": "设定一个AI角色帮你解决工作问题",
        "example_good": "你是一位有10年经验的麦肯锡咨询顾问，擅长用结构化思维解决复杂商业问题。请用金字塔原理帮我分析以下问题...",
        "example_bad": "你帮我分析一下",
        "points": 20
    },
    {
        "id": "prompt_3",
        "title": "高级：Few-shot示例",
        "desc": "测试高级Prompt技巧",
        "task": "用Few-shot技巧让AI学习你的写作风格",
        "example_good": "请模仿以下写作风格：[示例1]...[示例2]... 现在请用同样的风格写一段关于AI的文字",
        "example_bad": "模仿我的风格写一段",
        "points": 30
    }
]

# 2. AI对话模拟场景
AI_CHAT_SCENARIOS = [
    {
        "id": "chat_1",
        "scenario": "你是产品经理，需要让AI帮你分析竞品数据",
        "options": [
            {"text": "直接问：帮我分析一下竞品", "score": 10, "feedback": "太笼统了，AI不知道你要分析什么"},
            {"text": "给AI一个表格，让它总结关键洞察", "score": 50, "feedback": "不错，但还可以更具体"},
            {"text": "设定角色+提供数据+明确输出格式", "score": 100, "feedback": "完美！角色+数据+格式，AI能给出最佳答案"}
        ]
    },
    {
        "id": "chat_2",
        "scenario": "AI给你的代码有bug，你会怎么反馈？",
        "options": [
            {"text": "直接说：这代码不对", "score": 10, "feedback": "AI不知道哪里不对"},
            {"text": "指出具体错误行", "score": 50, "feedback": "可以，但AI可能不知道为什么错"},
            {"text": "指出错误+提供错误信息+说明预期行为", "score": 100, "feedback": "完美！给AI足够信息才能修复"}
        ]
    },
    {
        "id": "chat_3",
        "scenario": "你想让AI帮你写一封辞职信",
        "options": [
            {"text": "写一封辞职信", "score": 20, "feedback": "太简单了，结果可能很模板化"},
            {"text": "说明原因和语气", "score": 60, "feedback": "好一些，但还可以更具体"},
            {"text": "说明原因+语气+字数+必须包含的要点", "score": 100, "feedback": "完美！约束条件越多，结果越符合预期"}
        ]
    }
]

# 3. AI知识问答
AI_KNOWLEDGE_QUIZ = [
    {
        "question": "以下哪个不是大语言模型的特点？",
        "options": [
            "能理解上下文语境",
            "可以生成人类般的文本",
            "拥有真实的情感和意识",
            "能进行多轮对话"
        ],
        "correct": 2,
        "explanation": "AI没有真实的情感和意识，它只是模拟人类的语言模式"
    },
    {
        "question": "Prompt Engineering（提示工程）的主要目的是？",
        "options": [
            "让AI运行得更快",
            "更好地引导AI生成期望的输出",
            "修复AI的bug",
            "训练新的AI模型"
        ],
        "correct": 1,
        "explanation": "提示工程是通过优化输入提示来获得更好的AI输出"
    },
    {
        "question": "什么是AI的'幻觉'(Hallucination)？",
        "options": [
            "AI看到了不存在的东西",
            "AI生成了看似合理但实际错误的信息",
            "AI运行速度变慢",
            "AI产生了自我意识"
        ],
        "correct": 1,
        "explanation": "AI幻觉是指AI生成听起来合理但实际上不正确或虚构的信息"
    },
    {
        "question": "RAG（检索增强生成）的主要作用是？",
        "options": [
            "让AI说话更流畅",
            "让AI能够访问外部知识库生成更准确的回答",
            "让AI运行更快",
            "让AI更省电"
        ],
        "correct": 1,
        "explanation": "RAG让AI在生成回答前先检索相关信息，提高准确性和时效性"
    }
]

# 4. 每日AI使用习惯测试
DAILY_AI_HABITS = [
    {"id": "morning", "question": "早上醒来第一件事是？",
     "options": ["看手机消息", "问AI今天天气和日程", "刷社交媒体", "直接起床"]},
    {"id": "work", "question": "工作中遇到不会的问题，你会？",
     "options": ["先自己查资料", "直接问AI", "问同事", "放着不管"]},
    {"id": "lunch", "question": "中午不知道吃什么，你会？",
     "options": ["随便吃", "问AI推荐", "看外卖APP", "问朋友"]},
    {"id": "write", "question": "需要写一封正式邮件，你会？",
     "options": ["自己写", "让AI起草再修改", "找模板", "不写"]},
    {"id": "learn", "question": "想学一个新技能，你会？",
     "options": ["买课程系统学", "让AI制定学习计划", "直接问AI边做边学", "放弃"]}
]

# 个人版趣味问题
FUN_QUESTIONS = [
    # === 第一部分：AI本能反应 ===
    {"id": "q1", "dimension": "ai_first_mindset", "category": "AI本能反应",
     "question": "老板突然给你一个全新领域的任务，你的第一反应是？",
     "options": [
         {"text": "先百度/Google搜一下看看", "score": 10, "tag": "传统搜索派"},
         {"text": "问ChatGPT这个领域是什么、该怎么做", "score": 50, "tag": "AI咨询派"},
         {"text": "让AI帮我制定一个完整的执行方案", "score": 80, "tag": "AI规划派"},
         {"text": "直接让AI Agent帮我搭建框架，我负责审核", "score": 100, "tag": "AI代管派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q2", "dimension": "deep_collaboration", "category": "AI本能反应",
     "question": "你写Prompt的习惯是？",
     "options": [
         {"text": "就写几个关键词，比如'帮我写个方案'", "score": 10, "tag": "佛系Prompt"},
         {"text": "会写清楚背景、需求、格式要求", "score": 50, "tag": "结构化Prompt"},
         {"text": "会设定角色、提供示例、多轮迭代优化", "score": 80, "tag": "高级Prompt"},
         {"text": "我有自己的Prompt模板库，随时复用", "score": 100, "tag": "Prompt工程师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q3", "dimension": "problem_reframing", "category": "AI本能反应",
     "question": "遇到一个棘手的工作问题，你会？",
     "options": [
         {"text": "自己苦思冥想，实在不行问同事", "score": 0, "tag": "独立思考派"},
         {"text": "把问题描述给AI，看看它有什么建议", "score": 40, "tag": "AI顾问派"},
         {"text": "让AI帮我重新定义问题，找到更好的切入点", "score": 75, "tag": "问题重构派"},
         {"text": "和AI来一场头脑风暴，碰撞出全新思路", "score": 100, "tag": "共创派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q4", "dimension": "learning_mode", "category": "AI本能反应",
     "question": "老板让你一周内学会一个你完全不懂的新技能，你会？",
     "options": [
         {"text": "买本书/找课程，从零开始系统学习", "score": 10, "tag": "传统学习派"},
         {"text": "让AI帮我制定学习计划，推荐学习资源", "score": 50, "tag": "AI辅助学习"},
         {"text": "直接用AI边做边学，遇到问题就问", "score": 85, "tag": "实战派"},
         {"text": "让AI帮我快速搭建原型，在实践中掌握", "score": 100, "tag": "极速上手派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q5", "dimension": "iteration_agility", "category": "AI本能反应",
     "question": "你手机里装了几个AI相关的App？",
     "options": [
         {"text": "0-1个，就一个ChatGPT", "score": 10, "tag": "专一派"},
         {"text": "2-4个，常用的那几个", "score": 40, "tag": "实用派"},
         {"text": "5-9个，看到新的就想试试", "score": 75, "tag": "尝鲜派"},
         {"text": "10个以上，手机内存都被AI占满了", "score": 100, "tag": "AI收藏家"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第二部分：AI社交风格 ===
    {"id": "q6", "dimension": "boundary_awareness", "category": "AI社交风格",
     "question": "AI给你一个看起来很专业但你不确定的答案，你会？",
     "options": [
         {"text": "直接用，AI说的应该没错", "score": 0, "tag": "信任派"},
         {"text": "大概看一下，没问题就用", "score": 30, "tag": "粗略检查派"},
         {"text": "交叉验证一下，用另一个AI或搜索引擎确认", "score": 70, "tag": "验证派"},
         {"text": "让AI自己批判自己的答案，找出漏洞", "score": 100, "tag": "批判大师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q7", "dimension": "ai_first_mindset", "category": "AI社交风格",
     "question": "你怎么形容你和AI的关系？",
     "options": [
         {"text": "就是个工具，用完就关", "score": 10, "tag": "工具关系"},
         {"text": "像个助手，帮我处理杂活", "score": 40, "tag": "助手关系"},
         {"text": "像个搭档，一起讨论解决问题", "score": 75, "tag": "搭档关系"},
         {"text": "像个导师/朋友，有时候还会跟它聊天", "score": 100, "tag": "灵魂伴侣"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q8", "dimension": "deep_collaboration", "category": "AI社交风格",
     "question": "你用AI做过最让你自豪的事情是？",
     "options": [
         {"text": "写过邮件、翻译过文档", "score": 15, "tag": "基础应用"},
         {"text": "用AI写过代码、做过数据分析", "score": 45, "tag": "进阶应用"},
         {"text": "用AI完成了一个完整的项目", "score": 75, "tag": "项目级应用"},
         {"text": "搭建了AI自动化工作流，持续节省时间", "score": 100, "tag": "系统级应用"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q9", "dimension": "deep_collaboration", "category": "AI社交风格",
     "question": "你和朋友聊天时，提到AI的频率是？",
     "options": [
         {"text": "很少提，觉得没什么好说的", "score": 10, "tag": "低调派"},
         {"text": "偶尔分享一些好用的AI技巧", "score": 40, "tag": "分享派"},
         {"text": "经常安利，朋友都说我被AI洗脑了", "score": 75, "tag": "布道派"},
         {"text": "三句话不离AI，朋友都开始用了", "score": 100, "tag": "AI传教士"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q10", "dimension": "learning_mode", "category": "AI社交风格",
     "question": "你有没有给AI取过名字或者设定过人设？",
     "options": [
         {"text": "没有，就叫ChatGPT", "score": 0, "tag": "务实派"},
         {"text": "想过但没做过", "score": 30, "tag": "犹豫派"},
         {"text": "设定过角色，比如'你是一个资深产品经理'", "score": 65, "tag": "角色扮演派"},
         {"text": "取了名字，还设定了性格、背景故事", "score": 100, "tag": "AI养成派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第三部分：AI生活场景 ===
    {"id": "q11", "dimension": "ai_first_mindset", "category": "AI生活场景",
     "question": "周末朋友聚餐，需要选餐厅，你会？",
     "options": [
         {"text": "打开大众点评自己翻", "score": 10, "tag": "传统派"},
         {"text": "问AI推荐附近有什么好吃的", "score": 50, "tag": "AI推荐派"},
         {"text": "让AI根据大家的口味偏好来推荐", "score": 80, "tag": "AI管家派"},
         {"text": "让AI做一个餐厅对比分析表格", "score": 100, "tag": "AI分析师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q12", "dimension": "iteration_agility", "category": "AI生活场景",
     "question": "看到一个新AI工具发布，你的反应是？",
     "options": [
         {"text": "哦，又出新了，跟我没关系", "score": 0, "tag": "佛系派"},
         {"text": "看看介绍，有意思就试试", "score": 40, "tag": "观望派"},
         {"text": "立刻注册试用，测评一下好不好用", "score": 75, "tag": "尝鲜派"},
         {"text": "不仅试用，还要写一篇测评发朋友圈", "score": 100, "tag": "测评博主"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q13", "dimension": "problem_reframing", "category": "AI生活场景",
     "question": "你用AI做过最有创意的事情是？",
     "options": [
         {"text": "没做过什么特别的", "score": 0, "tag": "待开发"},
         {"text": "用AI生成过图片/音乐/视频", "score": 50, "tag": "创作入门"},
         {"text": "用AI帮朋友做过生日礼物/表白文案", "score": 75, "tag": "创意生活家"},
         {"text": "用AI做了一个让所有人都惊艳的作品", "score": 100, "tag": "创意大师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q14", "dimension": "boundary_awareness", "category": "AI生活场景",
     "question": "你有没有发现过AI'一本正经胡说八道'（幻觉）？",
     "options": [
         {"text": "没有，AI说的我都信", "score": 0, "tag": "信任者"},
         {"text": "好像有过，但不确定", "score": 30, "tag": "模糊感知"},
         {"text": "发现过好几次，现在都会验证一下", "score": 70, "tag": "警惕派"},
         {"text": "经常发现，还能故意引导AI犯错来测试它", "score": 100, "tag": "幻觉猎人"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第四部分：AI哲学思考 ===
    {"id": "q15", "dimension": "ai_first_mindset", "category": "AI哲学思考",
     "question": "如果AI能完美替代你80%的工作，你会？",
     "options": [
         {"text": "有点慌，开始担心失业", "score": 10, "tag": "焦虑派"},
         {"text": "无所谓，AI替代不了那20%", "score": 40, "tag": "淡定派"},
         {"text": "太好了，终于有时间做想做的事", "score": 75, "tag": "乐观派"},
         {"text": "主动学习驾驭AI，让自己不可替代", "score": 100, "tag": "进化派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q16", "dimension": "iteration_agility", "category": "AI哲学思考",
     "question": "你通常在什么时间段使用AI？",
     "options": [
         {"text": "只在工作时间用", "score": 10, "tag": "上班族"},
         {"text": "工作+偶尔下班后", "score": 40, "tag": "加班族"},
         {"text": "随时随地，有需求就用", "score": 75, "tag": "全天候"},
         {"text": "凌晨2点还在和AI讨论人生哲学", "score": 100, "tag": "深夜AI玩家"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q17", "dimension": "deep_collaboration", "category": "AI哲学思考",
     "question": "你觉得5年后AI会变成什么样？",
     "options": [
         {"text": "跟现在差不多吧", "score": 10, "tag": "保守派"},
         {"text": "会比现在好用很多", "score": 40, "tag": "谨慎乐观"},
         {"text": "会深刻改变每个人的工作和生活", "score": 75, "tag": "变革派"},
         {"text": "AI将无处不在，人类与AI深度融合", "score": 100, "tag": "未来主义者"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q18", "dimension": "boundary_awareness", "category": "AI哲学思考",
     "question": "你有没有因为使用AI而产生过'原来还可以这样'的顿悟时刻？",
     "options": [
         {"text": "没有过", "score": 0, "tag": "未觉醒"},
         {"text": "有过一两次", "score": 40, "tag": "初步觉醒"},
         {"text": "有很多次，每次都让我对AI有了新认识", "score": 75, "tag": "持续觉醒"},
         {"text": "经常有，我已经习惯了被AI惊艳", "score": 100, "tag": "见怪不怪"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q19", "dimension": "problem_reframing", "category": "AI哲学思考",
     "question": "如果让你用一句话描述AI对你的影响，你会说？",
     "options": [
         {"text": "AI就是一个好用的工具", "score": 10, "tag": "工具论"},
         {"text": "AI让我的工作效率提升了不少", "score": 40, "tag": "效率论"},
         {"text": "AI改变了我思考问题的方式", "score": 75, "tag": "思维变革论"},
         {"text": "AI重新定义了我对'能力'的理解", "score": 100, "tag": "认知革命论"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q20", "dimension": "learning_mode", "category": "AI哲学思考",
     "question": "如果给AI打分（满分10分），你会打几分？",
     "options": [
         {"text": "5分以下，还有很多不足", "score": 10, "tag": "严格评委"},
         {"text": "6-7分，还不错但需要改进", "score": 40, "tag": "客观评委"},
         {"text": "8-9分，已经非常强大了", "score": 75, "tag": "粉丝评委"},
         {"text": "10分满分！AI是人类的未来", "score": 100, "tag": "超级粉丝"},
         {"text": "其他", "score": 0, "tag": "自定义"}]}
]

def load_candidates():
    if CANDIDATES_FILE.exists():
        with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_candidates(candidates):
    with open(CANDIDATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

def calculate_level(total_score):
    for level, info in LEVEL_DEFINITIONS.items():
        min_score, max_score = info["score_range"]
        if min_score <= total_score < max_score or (level == "L3" and total_score >= max_score):
            return level
    return "L0"

def calculate_score(dimension_scores):
    total = 0.0
    max_total = 0.0
    weights = [1.0, 1.0, 1.0, 0.8, 0.8, 0.8]
    for i, dim_key in enumerate(AI_NATIVE_DIMENSIONS.keys()):
        dim_data = dimension_scores.get(dim_key, {})
        # 支持两种格式：{"score": xxx} 或直接是数字
        if isinstance(dim_data, dict):
            score = dim_data.get("score", 0)
        else:
            score = dim_data if isinstance(dim_data, (int, float)) else 0
        
        # 确保 score 是数字类型
        try:
            score = float(score) if score is not None else 0.0
        except (TypeError, ValueError):
            score = 0.0
            
        weight = weights[i]
        total += score * weight
        max_total += 100 * weight
    if max_total > 0:
        return round((total / max_total) * 100, 1)
    return 0

def get_level_color(level):
    return LEVEL_DEFINITIONS.get(level, {}).get("color", "#gray")

def analyze_other_answer(question_text, user_answer, analyzer=None):
    """分析用户对'其他'选项的自定义回答，给出评分和建议"""
    
    # 如果没有AI分析器，返回默认分数
    if not analyzer or not analyzer.is_available():
        return {
            "score": 40,  # 默认中等偏低的分数
            "analysis": "无法进行AI分析，采用默认评分"
        }
    
    # 构建分析prompt
    prompt = f"""
请分析用户对以下问题的回答，评估其AI使用能力和意识：

问题：{question_text}
用户回答：{user_answer}

请从以下几个维度评估（每项0-100分）：
1. AI使用频率和深度
2. AI使用方法的合理性
3. 对AI能力边界的认知
4. 整体AI素养

请以JSON格式返回：
{{"score": 平均分数(0-100), "analysis": "简短分析说明"}}
"""
    
    try:
        response = analyzer.client.chat.completions.create(
            model=analyzer.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        result_text = response.choices[0].message.content
        
        # 尝试解析JSON
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "score": min(100, max(0, int(result.get("score", 40)))),
                "analysis": result.get("analysis", "")
            }
    except Exception as e:
        pass
    
    return {
        "score": 40,
        "analysis": "分析失败，采用默认评分"
    }

# 初始化 session state
if 'candidates' not in st.session_state:
    st.session_state.candidates = load_candidates()
if 'current_candidate' not in st.session_state:
    st.session_state.current_candidate = None
if 'editing_candidate' not in st.session_state:
    st.session_state.editing_candidate = None
if 'ai_analysis_result' not in st.session_state:
    st.session_state.ai_analysis_result = None
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "hr"
if 'personal_answers' not in st.session_state:
    st.session_state.personal_answers = {}
if 'personal_completed' not in st.session_state:
    st.session_state.personal_completed = False
if 'personal_step' not in st.session_state:
    st.session_state.personal_step = 0
if 'personal_tools' not in st.session_state:
    st.session_state.personal_tools = []
if 'personal_other_answers' not in st.session_state:
    st.session_state.personal_other_answers = {}

# CSS 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    html { scroll-behavior: smooth; }
    .main-header { font-size: 2.2rem; font-weight: 600; color: #1a1a2e; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; font-weight: 400; }
    .score-card { background: linear-gradient(135deg, #86efac 0%, #ffffff 100%); padding: 2rem; border-radius: 12px; color: #166534; text-align: center; margin: 1rem 0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #bbf7d0; }
    .score-value { font-size: 2.8rem; font-weight: 700; letter-spacing: -0.02em; }
    .level-badge { display: inline-block; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: 600; font-size: 0.9rem; color: white; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .dimension-card { background: #ffffff; padding: 1.25rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #1e3a5f; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    .checklist-item { padding: 1rem; margin: 0.75rem 0; background: #ffffff; border-radius: 8px; border-left: 3px solid #059669; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }
    .section-header { font-size: 1.25rem; font-weight: 600; color: #1a1a2e; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
    .info-card { background: #ffffff; padding: 1.5rem; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin: 1rem 0; }
    .metric-label { font-size: 0.875rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.5rem; font-weight: 600; color: #1a1a2e; }
    /* Fun/Personal version styles */
    .fun-header { text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 2rem; }
    .fun-title { font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .fun-subtitle { font-size: 1.1rem; opacity: 0.9; }
    .quiz-card { background: white; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; }
    .result-hero { text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; }
    .result-emoji { font-size: 5rem; margin-bottom: 1rem; }
    .result-title { font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
    .result-score { font-size: 4rem; font-weight: 700; margin: 1rem 0; }
    .dimension-bar { height: 24px; background: #e2e8f0; border-radius: 12px; overflow: hidden; margin: 0.5rem 0; }
    .dimension-fill { height: 100%; border-radius: 12px; transition: width 0.5s ease; }
    .share-card { background: white; border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid #e2e8f0; }
    .mode-card { background: white; border-radius: 12px; padding: 2rem; text-align: center; border: 2px solid #e2e8f0; cursor: pointer; transition: all 0.3s; }
    .mode-card:hover { border-color: #667eea; transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .mode-card.active { border-color: #667eea; background: #f8f4ff; }
</style>
""", unsafe_allow_html=True)

# ==================== HR招聘版本 ====================
def render_hr_version():
    """HR招聘版本主页面"""
    st.markdown('<div class="main-header">AI Native Talent Assessment Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">基于 AI Native 人才标准的候选人评估系统</div>', unsafe_allow_html=True)
    
    analyzer = get_analyzer()
    candidates = st.session_state.candidates
    
    # AI 状态指示
    if analyzer.is_available():
        st.success("AI 分析功能已启用 - 可使用 AI 辅助简历分析")
    else:
        st.info("如需启用 AI 分析功能，请在「新增评估」页面配置 API Key")
    
    if not candidates:
        st.info("欢迎使用！目前还没有候选人数据，请点击左侧「新增评估」开始添加。")
    else:
        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="score-card"><div class="metric-label">候选人总数</div><div class="metric-value">{len(candidates)}</div></div>', unsafe_allow_html=True)
        with col2:
            l3_count = sum(1 for c in candidates.values() if c.get('level') == 'L3')
            st.markdown(f'<div class="score-card"><div class="metric-label">L3 大师</div><div class="metric-value">{l3_count}</div></div>', unsafe_allow_html=True)
        with col3:
            l2_count = sum(1 for c in candidates.values() if c.get('level') == 'L2')
            st.markdown(f'<div class="score-card"><div class="metric-label">L2 高手</div><div class="metric-value">{l2_count}</div></div>', unsafe_allow_html=True)
        with col4:
            avg_score = sum(c.get('total_score', 0) for c in candidates.values()) / len(candidates) if candidates else 0
            st.markdown(f'<div class="score-card"><div class="metric-label">平均分</div><div class="metric-value">{avg_score:.1f}</div></div>', unsafe_allow_html=True)
        
        # 候选人列表
        st.subheader("候选人列表")
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("搜索候选人姓名", "")
        with col2:
            level_filter = st.multiselect("筛选等级", ["L0", "L1", "L2", "L3"], default=[])
        
        filtered_candidates = {}
        for cid, candidate in candidates.items():
            if search and search.lower() not in candidate.get("name", "").lower():
                continue
            if level_filter and candidate.get("level") not in level_filter:
                continue
            filtered_candidates[cid] = candidate
        
        for cid, candidate in filtered_candidates.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{candidate.get('name', '未命名')}**")
                    st.caption(f"职位: {candidate.get('position', '未指定')} | 评估日期: {candidate.get('eval_date', '未知')}")
                with col2:
                    level = candidate.get("level", "L0")
                    color = get_level_color(level)
                    st.markdown(f'<span class="level-badge" style="background-color: {color}">{LEVEL_DEFINITIONS[level]["name"]}</span>', unsafe_allow_html=True)
                with col3:
                    st.write(f"**{candidate.get('total_score', 0)}分**")
                with col4:
                    if st.button("查看详情", key=f"view_{cid}"):
                        st.session_state.current_candidate = cid
                        st.rerun()
                st.divider()
    
    # 候选人详情弹窗
    if st.session_state.current_candidate:
        cid = st.session_state.current_candidate
        if cid in st.session_state.candidates:
            c = st.session_state.candidates[cid]
            st.markdown("---")
            st.subheader(f"{c['name']} - 详细评估报告")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**职位:** {c.get('position', '-')}")
                st.write(f"**邮箱:** {c.get('email', '-')}")
            with col2:
                level = c.get('level', 'L0')
                color = get_level_color(level)
                st.markdown(f'<div class="level-badge" style="background-color: {color}">{LEVEL_DEFINITIONS[level]["name"]}</div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="font-size: 2rem; font-weight: bold; color: {color}">{c.get("total_score", 0)}分</div>', unsafe_allow_html=True)
            
            # 雷达图
            import plotly.graph_objects as go
            categories = [info['name'] for info in AI_NATIVE_DIMENSIONS.values()]
            values = [c.get('dimensions', {}).get(dim_key, {}).get('score', 0) for dim_key in AI_NATIVE_DIMENSIONS.keys()]
            values.append(values[0])
            fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories + [categories[0]], fill='toself', name=c['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # AI 分析结果
            ai_analysis = c.get('ai_analysis')
            if ai_analysis:
                with st.expander("查看 AI 分析报告"):
                    render_ai_analysis_result(ai_analysis)
            
            # 各维度详情
            st.subheader("各维度评分详情")
            ai_dimensions = c.get('ai_dimensions', {})
            manual_modified = c.get('manual_modified', {})
            
            for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
                dim_data = c.get('dimensions', {}).get(dim_key, {})
                score = dim_data.get('score', 0)
                notes = dim_data.get('notes', '')
                is_manual = manual_modified.get(dim_key, False)
                
                # 获取AI原始评分
                ai_dim_data = ai_dimensions.get(dim_key, {})
                ai_score = ai_dim_data.get("score", 0) if ai_dim_data else 0
                ai_reasoning = ai_dim_data.get("reasoning", "") if ai_dim_data else ""
                
                with st.container():
                    # 标题行：显示维度名称、分数、来源标签
                    header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
                    with header_col1:
                        st.write(f"**{dim_info['name']}**")
                    with header_col2:
                        st.write(f"**{score}分**")
                    with header_col3:
                        if is_manual:
                            st.markdown('<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-size:0.8rem;">人工调整</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:0.8rem;">AI 评分</span>', unsafe_allow_html=True)
                    
                    # 显示评分说明
                    st.write(notes if notes else "无评分说明")
                    
                    # 如果有人工修改，显示AI原始评分供对比
                    if is_manual and ai_reasoning:
                        with st.expander("查看 AI 原始评分"):
                            st.write(f"AI 评分: {ai_score}分")
                            st.write(f"AI 理由: {ai_reasoning}")
                    
                    st.divider()
            
            # 快速判断清单
            st.subheader("快速判断清单")
            checklist = c.get('checklist', {})
            passed = sum(1 for v in checklist.values() if v)
            st.write(f"通过项目: {passed}/5")
            for i, item in enumerate(QUICK_CHECKLIST, 1):
                checked = checklist.get(f"check_{i}", False)
                icon = "[是]" if checked else "[否]"
                st.write(f"{icon} {item}")
            
            # 综合评价
            st.subheader("综合评价")
            st.write(c.get('overall_notes', '无综合评价'))
            
            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("关闭详情"):
                    st.session_state.current_candidate = None
                    st.session_state.editing_candidate = None
                    st.rerun()
            with col2:
                if st.button("编辑评估"):
                    st.session_state.editing_candidate = cid
                    st.rerun()
            with col3:
                if st.button("删除此候选人", type="secondary"):
                    del st.session_state.candidates[cid]
                    save_candidates(st.session_state.candidates)
                    st.session_state.current_candidate = None
                    st.session_state.editing_candidate = None
                    st.rerun()
        else:
            st.session_state.current_candidate = None
    
    # 候选人编辑页面
    if st.session_state.editing_candidate:
        cid = st.session_state.editing_candidate
        if cid in st.session_state.candidates:
            c = st.session_state.candidates[cid]
            st.markdown("---")
            st.subheader(f"编辑候选人评估 - {c['name']}")
            
            # 基本信息编辑
            st.write("**基本信息**")
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("姓名", value=c.get('name', ''), key="edit_name")
                current_position = c.get('position', '')
                position_options = JOB_CATEGORIES.copy()
                if current_position and current_position not in position_options:
                    position_options.append(current_position)
                edit_position_category = st.selectbox("职位类别", options=position_options, 
                    index=position_options.index(current_position) if current_position in position_options else 0,
                    key="edit_position_category")
                if edit_position_category == "其他":
                    edit_position = st.text_input("自定义职位", value=current_position if current_position not in JOB_CATEGORIES else "", key="edit_position_custom")
                else:
                    edit_position = edit_position_category
            with col2:
                edit_email = st.text_input("邮箱", value=c.get('email', ''), key="edit_email")
                edit_phone = st.text_input("电话", value=c.get('phone', ''), key="edit_phone")
            
            st.divider()
            
            # 六维评分编辑
            st.write("**AI Native 六维评分**")
            edit_dimensions = {}
            ai_dimensions = c.get('ai_dimensions', {})
            manual_modified = c.get('manual_modified', {})
            
            for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
                dim_data = c.get('dimensions', {}).get(dim_key, {})
                current_score = dim_data.get('score', 50)
                current_notes = dim_data.get('notes', '')
                is_manual = manual_modified.get(dim_key, False)
                
                # 获取AI原始评分
                ai_dim_data = ai_dimensions.get(dim_key, {})
                ai_score = ai_dim_data.get("score", 0) if ai_dim_data else 0
                ai_reasoning = ai_dim_data.get("reasoning", "") if ai_dim_data else ""
                
                source_label = "人工调整" if is_manual else "AI 评分"
                with st.expander(f"{dim_info['name']} (当前: {current_score}分 - {source_label})"):
                    st.write(f"**定义:** {dim_info['description']}")
                    
                    # 如果有AI原始评分，显示对比
                    if ai_reasoning and is_manual:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.caption(f"AI 原始评分: {ai_score}分")
                        with col_b:
                            st.caption(f"当前评分: {current_score}分")
                    
                    new_score = st.slider("评分", 0, 100, current_score, key=f"edit_score_{dim_key}")
                    new_notes = st.text_area("评分说明", value=current_notes, key=f"edit_notes_{dim_key}", height=100)
                    edit_dimensions[dim_key] = {"score": new_score, "notes": new_notes}
            
            st.divider()
            
            # 快速判断清单编辑
            st.write("**快速判断清单**")
            edit_checklist = {}
            current_checklist = c.get('checklist', {})
            for i, item in enumerate(QUICK_CHECKLIST, 1):
                checked = current_checklist.get(f"check_{i}", False)
                edit_checklist[f"check_{i}"] = st.checkbox(item, value=checked, key=f"edit_check_{i}")
            
            st.divider()
            
            st.write("**综合评价**")
            edit_overall_notes = st.text_area("综合评价", value=c.get('overall_notes', ''), key="edit_overall_notes", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存修改", type="primary"):
                    total_score = calculate_score(edit_dimensions)
                    level = calculate_level(total_score)
                    st.session_state.candidates[cid].update({
                        "name": edit_name, "position": edit_position, "email": edit_email, "phone": edit_phone,
                        "dimensions": edit_dimensions, "checklist": edit_checklist, "overall_notes": edit_overall_notes,
                        "total_score": total_score, "level": level, "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_candidates(st.session_state.candidates)
                    st.success("评估已更新！")
                    st.session_state.editing_candidate = None
                    st.rerun()
            with col2:
                if st.button("取消编辑"):
                    st.session_state.editing_candidate = None
                    st.rerun()
        else:
            st.session_state.editing_candidate = None

# ==================== HR版本 - 新增候选人页面 ====================
def render_hr_add_page():
    """HR版本 - 新增候选人页面"""
    st.markdown('<div class="main-header">新增候选人评估</div>', unsafe_allow_html=True)
    
    analyzer = get_analyzer()
    render_ai_settings()
    analyzer = get_analyzer(force_refresh=True)
    
    st.divider()
    
    # 基本信息
    st.subheader("1. 基本信息")
    default_name = st.session_state.get("ai_detected_name", "")
    default_position = st.session_state.get("ai_detected_position", "")
    default_email = st.session_state.get("ai_detected_email", "")
    default_phone = st.session_state.get("ai_detected_phone", "")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("候选人姓名 *", value=default_name, key="input_name")
        
        st.write("**应聘职位 ***")
        position_col1, position_col2 = st.columns([1, 1])
        with position_col1:
            detected_position = default_position if default_position else ""
            position_options = JOB_CATEGORIES.copy()
            if detected_position and detected_position not in position_options:
                position_options.append(detected_position)
            selected_category = st.selectbox("选择类别", options=position_options,
                index=position_options.index(detected_position) if detected_position in position_options else 0,
                key="position_category", label_visibility="collapsed")
        with position_col2:
            if selected_category == "其他":
                custom_position = st.text_input("自定义职位", value=detected_position if detected_position not in JOB_CATEGORIES else "",
                    key="position_custom", label_visibility="collapsed")
                position = custom_position
            else:
                position = selected_category
                # 不显示禁用的输入框，只存储职位值
                st.session_state["position_custom"] = position
    with col2:
        email = st.text_input("邮箱", value=default_email, key="input_email")
        phone = st.text_input("电话", value=default_phone, key="input_phone")
    
    # 简历上传和 AI 分析
    st.subheader("2. 简历上传与 AI 分析")
    
    # 上传区域
    resume_file = st.file_uploader("上传简历 (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="resume_upload")
    
    if resume_file:
        st.success(f"已上传: {resume_file.name}")
        try:
            if resume_file.type == "text/plain":
                resume_text = resume_file.getvalue().decode('utf-8', errors='ignore')
            elif resume_file.type == "application/pdf":
                try:
                    import PyPDF2
                    from io import BytesIO
                    pdf_reader = PyPDF2.PdfReader(BytesIO(resume_file.getvalue()))
                    resume_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
                except:
                    resume_text = "[PDF文件内容]"
            else:
                resume_text = "[文档内容]"
        except:
            resume_text = ""
    else:
        resume_text = ""
    
    # AI 分析按钮
    st.markdown("---")
    st.write("**AI 智能分析**")
    
    if st.button("使用 AI 分析简历", type="primary", disabled=not analyzer.is_available()):
        if resume_file and resume_text:
            with st.spinner("AI 正在分析简历，请稍候..."):
                result = analyzer.analyze_resume(resume_text)
                st.session_state.ai_analysis_result = result
                # 重置AI评分初始化标志，确保表单能更新为AI评分
                st.session_state.ai_scores_initialized = False
                if "basic_info" in result:
                    basic_info = result.get("basic_info", {})
                    if basic_info.get("name"):
                        st.session_state["ai_detected_name"] = basic_info.get("name", "")
                    if basic_info.get("position"):
                        st.session_state["ai_detected_position"] = basic_info.get("position", "")
                    if basic_info.get("email"):
                        st.session_state["ai_detected_email"] = basic_info.get("email", "")
                    if basic_info.get("phone"):
                        st.session_state["ai_detected_phone"] = basic_info.get("phone", "")
                st.rerun()  # 重新渲染页面以应用AI评分
        else:
            st.warning("请先上传简历文件")
    
    # AI 分析结果
    if st.session_state.ai_analysis_result:
        st.markdown("---")
        render_ai_analysis_result(st.session_state.ai_analysis_result)
    
    # 简历内容
    if resume_text and resume_text != "[PDF文件内容]":
        with st.expander("查看简历内容"):
            st.text_area("简历文本", value=resume_text, height=200, key="resume_text_display")
    
    # 人工评分（可选，默认使用AI评分）
    st.divider()
    st.subheader("3. 评分调整（可选）")
    st.caption("AI 分析完成后已自动评分。如需调整，可在下方修改；不修改则默认使用 AI 评分结果。")
    
    # 获取AI评分作为默认值
    ai_result = st.session_state.ai_analysis_result or {}
    ai_dimension_scores = ai_result.get("dimension_scores", {})
    ai_overall = ai_result.get("overall_assessment", "")
    ai_checklist = ai_result.get("quick_checklist", {})
    
    # 初始化 session state 用于存储AI评分（确保AI分析后能正确更新默认值）
    if 'ai_scores_initialized' not in st.session_state:
        st.session_state.ai_scores_initialized = False
    
    # 如果AI分析结果更新了，重置初始化标志
    if ai_result and not st.session_state.ai_scores_initialized:
        for dim_key in AI_NATIVE_DIMENSIONS.keys():
            ai_dim_data = ai_dimension_scores.get(dim_key, {})
            ai_score = ai_dim_data.get("score", 50) if ai_dim_data else 50
            ai_reasoning = ai_dim_data.get("reasoning", "") if ai_dim_data else ""
            st.session_state[f"score_{dim_key}"] = int(ai_score)
            st.session_state[f"notes_{dim_key}"] = ai_reasoning
        st.session_state.ai_scores_initialized = True
    
    dimension_scores = {}
    manual_modified = {}
    
    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
        # AI 默认分数
        ai_dim_data = ai_dimension_scores.get(dim_key, {})
        ai_score = ai_dim_data.get("score", 50) if ai_dim_data else 50
        ai_reasoning = ai_dim_data.get("reasoning", "") if ai_dim_data else ""
        
        # 获取当前值（优先从session_state获取，确保AI分析后能更新）
        current_score = st.session_state.get(f"score_{dim_key}", int(ai_score))
        current_notes = st.session_state.get(f"notes_{dim_key}", ai_reasoning)
        
        with st.expander(f"{dim_info['name']} (AI评分: {ai_score}分)"):
            # 显示AI分析理由
            if ai_reasoning:
                st.info(f"AI 分析理由: {ai_reasoning}")
            
            st.write(f"**定义:** {dim_info['description']}")
            st.write("**关键信号:**")
            for signal in dim_info['signals']:
                st.markdown(f"- {signal}")
            
            score = st.slider("评分（调整后）", 0, 100, current_score, key=f"score_{dim_key}")
            notes = st.text_area("评分说明", value=current_notes, height=80, key=f"notes_{dim_key}")
            dimension_scores[dim_key] = {"score": score, "notes": notes}
            
            # 只比较分数是否被修改（不比较notes，因为text_area可能有格式差异）
            manual_modified[dim_key] = (score != int(ai_score))
    
    # 快速判断清单
    st.divider()
    st.subheader("4. 快速判断清单")
    st.write("面试结束后，回答以下5个问题，即可快速判定:")
    
    checklist = {}
    checklist_items_keys = ["ai_first_response", "own_methodology", "workflow_reformed", "specific_complaints", "ai_anxiety"]
    for i, item in enumerate(QUICK_CHECKLIST, 1):
        # 默认使用AI判断结果
        ai_checked = ai_checklist.get(checklist_items_keys[i-1], False) if ai_checklist else False
        checklist[f"check_{i}"] = st.checkbox(item, value=ai_checked, key=f"check_{i}")
    
    # 综合评价
    st.divider()
    st.subheader("5. 综合评价")
    overall_notes = st.text_area("请输入综合评价（默认为AI评价）", value=ai_overall, height=150, key="overall_notes")
    
    # 保存按钮
    st.divider()
    if st.button("保存评估", type="primary", use_container_width=True):
        name = st.session_state.get("input_name", name)
        position = st.session_state.get("input_position", position)
        
        if not name or not position:
            st.error("请填写候选人姓名和应聘职位")
        else:
            total_score = calculate_score(dimension_scores)
            level = calculate_level(total_score)
            
            # 保存AI分析结果（在清空session之前）
            ai_analysis_to_save = st.session_state.ai_analysis_result
            
            candidate_id = f"candidate_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.session_state.candidates[candidate_id] = {
                "name": name,
                "position": position,
                "email": st.session_state.get("input_email", ""),
                "phone": st.session_state.get("input_phone", ""),
                "dimensions": dimension_scores,
                "ai_dimensions": ai_dimension_scores,
                "manual_modified": manual_modified,
                "checklist": checklist,
                "overall_notes": overall_notes,
                "total_score": total_score,
                "level": level,
                "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ai_analysis": ai_analysis_to_save
            }
            
            save_candidates(st.session_state.candidates)
            st.success(f"评估已保存！候选人 {name} 的 AI Native 等级为: {LEVEL_DEFINITIONS[level]['name']} ({total_score}分)")
            
            # 清除状态
            st.session_state.ai_analysis_result = None
            st.session_state["ai_detected_name"] = ""
            st.session_state["ai_detected_position"] = ""
            st.session_state["ai_detected_email"] = ""
            st.session_state["ai_detected_phone"] = ""
            
            # 返回列表
            if st.button("返回候选人列表"):
                st.session_state.app_mode = "hr"
                st.rerun()

# ==================== 个人测评版本 ====================
def determine_ai_personality(avg_scores, answers):
    """根据各维度分数判定AI人格类型"""
    scores = {
        "prompt": avg_scores.get("deep_collaboration", 0),      # Prompt能力
        "agent": avg_scores.get("ai_first_mindset", 0),         # 系统思维
        "create": avg_scores.get("problem_reframing", 0),       # 创意能力
        "code": avg_scores.get("learning_mode", 0),             # 学习/技术
        "data": avg_scores.get("boundary_awareness", 0),        # 分析能力
        "auto": avg_scores.get("iteration_agility", 0),         # 效率/自动化
        "chat": avg_scores.get("deep_collaboration", 0) * 0.5 + avg_scores.get("ai_first_mindset", 0) * 0.5,  # 社交
        "learn": avg_scores.get("learning_mode", 0) * 0.7 + avg_scores.get("iteration_agility", 0) * 0.3  # 学习
    }
    
    # 找到最高分的维度
    max_dim = max(scores, key=scores.get)
    
    personality_map = {
        "prompt": "PROMPT-A",
        "agent": "AGENT-C",
        "create": "CREATE-X",
        "code": "CODE-N",
        "data": "DATA-W",
        "auto": "AUTO-B",
        "chat": "CHAT-S",
        "learn": "LEARN-P"
    }
    
    return personality_map.get(max_dim, "CHAT-S")


def render_personal_version():
    """个人测评版本 - AI人格进化论"""
    
    # 检查是否需要滚动到顶部
    if st.session_state.get('scroll_to_top', False):
        st.session_state.scroll_to_top = False
        # 使用HTML和JavaScript实现滚动到顶部
        st.markdown("""
        <script>
            window.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)
    
    # ===== 欢迎页面 =====
    if st.session_state.personal_step == 0:
        # 添加锚点
        st.markdown('<div id="quiz_start"></div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="fun-header">
            <div class="fun-title">AI 人格进化论</div>
            <div class="fun-subtitle">你是AI原始人，还是AI大师？20道题揭示你的AI人格</div>
            <div style="margin-top:1rem;opacity:0.8;font-size:0.95rem;">
                测试时间 约5分钟 | 20道趣味场景题 | 8种AI人格类型 | 12个成就解锁
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 8种人格预览
        st.markdown("### 你可能是什么AI人格？")
        personality_cols = st.columns(4)
        personalities = list(AI_PERSONALITIES.items())
        for i, (key, p) in enumerate(personalities):
            with personality_cols[i % 4]:
                st.markdown(f'''
                <div style="text-align:center;padding:1rem;background:white;border-radius:12px;
                     border:1px solid #e2e8f0;margin:0.5rem 0;">
                    <div style="font-size:2rem;">{p["emoji"]}</div>
                    <div style="font-weight:600;font-size:0.9rem;color:#1a1a2e;">{p["name"]}</div>
                    <div style="font-size:0.75rem;color:#64748b;">{p["trait"]}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 开始按钮
        if st.button("开始测试", type="primary", use_container_width=True):
            st.session_state.personal_step = 1
            st.rerun()
    
    # ===== 测试阶段 =====
    elif st.session_state.personal_step in [1, 2, 3, 4]:
        step = st.session_state.personal_step
        categories = ["AI本能反应", "AI社交风格", "AI生活场景", "AI哲学思考"]
        category = categories[step - 1]
        
        # 进度条
        progress = step / 5
        st.markdown(f'''
        <div style="margin-bottom:1.5rem;">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span style="font-weight:600;">第{step}/4部分：{category}</span>
                <span style="color:#64748b;">{progress*100:.0f}%</span>
            </div>
            <div style="height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;">
                <div style="height:100%;width:{progress*100}%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:4px;transition:width 0.3s;"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 当前阶段的题目
        step_questions = [q for q in FUN_QUESTIONS if q.get("category") == category]
        
        for q in step_questions:
            st.markdown(f'''
            <div class="quiz-card">
                <div style="font-weight:600;margin-bottom:0.75rem;">{q["question"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 获取radio的选项
            radio_options = [o["text"] for o in q["options"]]
            
            # 检查是否有已保存的答案
            current_answer = st.session_state.personal_answers.get(q["id"])
            current_index = None
            if current_answer:
                # 找到当前选择的索引
                for idx, o in enumerate(q["options"]):
                    if o["text"] == current_answer.get("text"):
                        current_index = idx
                        break
            
            # 使用radio显示选项，不设置默认值(index=None)
            selected = st.radio(
                "选择最接近你的答案", 
                options=radio_options, 
                key=f"q_{q['id']}",
                index=current_index,
                format_func=lambda x: x,
                label_visibility="collapsed"
            )
            
            # 处理答案选择
            for o in q["options"]:
                if o["text"] == selected:
                    st.session_state.personal_answers[q["id"]] = {
                        "dimension": q["dimension"], 
                        "score": o["score"],
                        "tag": o.get("tag", ""),
                        "text": o["text"]
                    }
                    
                    # 如果选择了"其他"选项，显示文本输入框
                    if o["text"] == "其他":
                        other_answer_key = f"other_{q['id']}"
                        current_other = st.session_state.personal_other_answers.get(q["id"], "")
                        
                        other_text = st.text_input(
                            "请描述你的回答：",
                            value=current_other,
                            key=other_answer_key,
                            placeholder="请输入你的回答..."
                        )
                        
                        # 保存其他答案到session_state
                        if other_text:
                            st.session_state.personal_other_answers[q["id"]] = other_text
                        elif other_text == "" and q["id"] in st.session_state.personal_other_answers:
                            # 如果用户清空了输入，也清空保存的值
                            del st.session_state.personal_other_answers[q["id"]]
                    break
        
        # 下一阶段按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("上一部分"):
                st.session_state.personal_step = max(0, step - 1)
                st.rerun()
        with col2:
            btn_text = "下一部分" if step < 4 else "进入工具选择"
            if st.button(btn_text, type="primary"):
                # 检查当前板块的所有题目是否都已选择
                unanswered = []
                for q in step_questions:
                    answer = st.session_state.personal_answers.get(q["id"])
                    if not answer:
                        # 没有选择任何答案
                        unanswered.append(q["id"])
                    elif answer.get("text") == "其他":
                        # 选择了"其他"，检查是否填写了具体内容
                        if not st.session_state.personal_other_answers.get(q["id"], "").strip():
                            unanswered.append(q["id"])
                
                if unanswered:
                    # 显示警告信息
                    unanswered_display = [f"第{step_questions.index(next((x for x in step_questions if x['id'] == uid), step_questions[0]))+1}题" for uid in unanswered]
                    st.warning(f"请回答以下问题后再继续：{', '.join(unanswered_display)}")
                else:
                    st.session_state.personal_step = step + 1
                    # 标记需要滚动到顶部
                    st.session_state.scroll_to_top = True
                    st.rerun()
    
    # ===== AI工具选择 =====
    elif st.session_state.personal_step == 5:
        # 苹果风格标题
        st.markdown('''
        <div style="text-align:center;padding:3rem 1.5rem;margin-bottom:2rem;">
            <div style="font-size:2.5rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;margin-bottom:0.5rem;">AI工具箱</div>
            <div style="font-size:1.1rem;color:#86868b;max-width:600px;margin:0 auto;">选择你使用过的AI工具，发现你的AI能力图谱</div>
        </div>
        ''', unsafe_allow_html=True)

        # 按类别分组显示
        tool_categories = {}
        for tool in AI_TOOLS_LIST:
            cat = tool["category"]
            if cat not in tool_categories:
                tool_categories[cat] = []
            tool_categories[cat].append(tool)

        for cat, tools in tool_categories.items():
            # 苹果风格分类标题
            st.markdown(f'''
            <div style="margin:2rem 0 1rem 0;">
                <div style="font-size:1.25rem;font-weight:600;color:#1d1d1f;">{cat}</div>
                <div style="height:1px;background:linear-gradient(90deg, #d2d2d7, transparent);margin-top:0.5rem;"></div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 苹果风格网格布局 - 每行3个，更大卡片
            for i in range(0, len(tools), 3):
                cols = st.columns(3)
                for j, tool in enumerate(tools[i:i+3]):
                    with cols[j]:
                        # 读取SVG图标
                        icon_path = tool.get('icon', '')
                        icon_html = ""
                        if icon_path and icon_path.endswith('.svg'):
                            try:
                                with open(icon_path, 'r', encoding='utf-8') as f:
                                    svg_content = f.read()
                                # 调整SVG样式 - 苹果风格大图标
                                svg_content = svg_content.replace('<svg', '<svg width="32" height="32" style="filter:drop-shadow(0 2px 4px rgba(0,0,0,0.1))"')
                                icon_html = svg_content
                            except Exception as e:
                                # 使用emoji作为fallback
                                icon_html = f'<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🤖</div>'
                        else:
                            icon_html = f'<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🤖</div>'
                        
                        # 检查是否已选择
                        is_checked = tool['name'] in st.session_state.personal_tools
                        
                        # 苹果风格卡片 - 圆角、阴影、悬停效果
                        card_style = '''
                            background: ''' + ('linear-gradient(135deg, #007AFF 0%, #5856D6 100%)' if is_checked else '#ffffff') + ''';
                            border-radius: 16px;
                            padding: 1.25rem;
                            margin: 0.5rem 0;
                            box-shadow: 0 4px 20px rgba(0,0,0,''' + ('0.15)' if is_checked else '0.08)') + ''';
                            border: 1px solid ''' + ('transparent' if is_checked else '#e5e5e7') + ''';
                            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                            cursor: pointer;
                        '''
                        
                        text_color = '#ffffff' if is_checked else '#1d1d1f'
                        desc_color = 'rgba(255,255,255,0.8)' if is_checked else '#86868b'
                        
                        # 渲染卡片
                        st.markdown(f'''
                        <div style="{card_style}">
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                                {icon_html}
                                <div style="font-size:1rem;font-weight:600;color:{text_color};line-height:1.2;">{tool["name"]}</div>
                            </div>
                            <div style="font-size:0.75rem;color:{desc_color};line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{tool.get('desc', '')}</div>
                            <div style="font-size:0.7rem;color:{desc_color};margin-top:6px;opacity:0.8;">{tool.get('company', '')}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # 隐藏checkbox，点击卡片即可选择
                        checked = st.checkbox(
                            f"选择{tool['name']}",
                            value=is_checked,
                            key=f"tool_{tool['name']}",
                            label_visibility="collapsed"
                        )
                        
                        # 更新选择状态
                        if checked and tool['name'] not in st.session_state.personal_tools:
                            st.session_state.personal_tools.append(tool['name'])
                            st.rerun()
                        elif not checked and tool['name'] in st.session_state.personal_tools:
                            st.session_state.personal_tools.remove(tool['name'])
                            st.rerun()

        # 苹果风格底部统计和按钮
        selected_count = len(st.session_state.personal_tools)
        st.markdown('''
        <div style="margin:3rem 0;padding:1.5rem;background:linear-gradient(135deg, #f5f5f7 0%, #ffffff 100%);border-radius:20px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#1d1d1f;">''' + str(selected_count) + '''</div>
            <div style="font-size:0.9rem;color:#86868b;">已选择工具</div>
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 返回测试", use_container_width=True):
                st.session_state.personal_step = 4
                st.rerun()
        with col2:
            if st.button("继续 →", type="primary", use_container_width=True):
                st.session_state.personal_step = 6
                st.rerun()

    # ===== Step 6: Prompt挑战 =====
    elif st.session_state.personal_step == 6:
        st.markdown('''
        <div style="text-align:center;padding:1.5rem;margin-bottom:1.5rem;">
            <div style="font-size:1.5rem;font-weight:700;">Prompt挑战关卡</div>
            <div style="color:#64748b;">测试你的Prompt Engineering技能，学习如何更好地与AI对话</div>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化Prompt挑战分数
        if 'prompt_challenge_score' not in st.session_state:
            st.session_state.prompt_challenge_score = 0

        for challenge in PROMPT_CHALLENGES:
            with st.expander(f"{challenge['title']} (+{challenge['points']}分)"):
                st.write(f"**任务：** {challenge['task']}")
                st.write(f"*{challenge['desc']}*")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**示例（差）**")
                    st.info(challenge['example_bad'])
                with col2:
                    st.markdown("**示例（好）**")
                    st.success(challenge['example_good'])

                # 用户输入自己的Prompt
                user_prompt = st.text_area(
                    "写下你的Prompt：",
                    key=f"prompt_input_{challenge['id']}",
                    placeholder=f"尝试写一个比'{challenge['example_bad']}'更好的Prompt..."
                )

                if user_prompt:
                    if len(user_prompt) > len(challenge['example_bad']) + 10:
                        st.success(f"不错！你的Prompt很详细，可以获得+{challenge['points']}分！")
                        if f"completed_{challenge['id']}" not in st.session_state:
                            st.session_state.prompt_challenge_score += challenge['points']
                            st.session_state[f"completed_{challenge['id']}"] = True
                    else:
                        st.warning("试着写得更详细一些，比如加入角色设定、背景信息或格式要求~")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("返回工具选择"):
                st.session_state.personal_step = 5
                st.rerun()
        with col2:
            if st.button("继续：AI对话模拟", type="primary"):
                st.session_state.personal_step = 7
                st.rerun()

    # ===== Step 7: AI对话模拟 =====
    elif st.session_state.personal_step == 7:
        st.markdown('''
        <div style="text-align:center;padding:1.5rem;margin-bottom:1.5rem;">
            <div style="font-size:1.5rem;font-weight:700;">AI对话模拟场景</div>
            <div style="color:#64748b;">选择最佳策略，学习如何与AI高效协作</div>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化对话模拟分数
        if 'chat_scenario_score' not in st.session_state:
            st.session_state.chat_scenario_score = 0
        if 'chat_scenario_count' not in st.session_state:
            st.session_state.chat_scenario_count = 0

        for scenario in AI_CHAT_SCENARIOS:
            st.markdown(f"**场景：** {scenario['scenario']}")

            # 使用radio让用户选择
            options_text = [opt['text'] for opt in scenario['options']]
            selected = st.radio(
                "你会怎么做？",
                options_text,
                key=f"scenario_{scenario['id']}",
                label_visibility="collapsed"
            )

            # 只记录分数和选择，不显示即时评分
            for opt in scenario['options']:
                if opt['text'] == selected:
                    # 记录分数和选择（只记录一次）
                    if f"scenario_completed_{scenario['id']}" not in st.session_state:
                        st.session_state.chat_scenario_score += opt['score']
                        st.session_state.chat_scenario_count += 1
                        st.session_state[f"scenario_completed_{scenario['id']}"] = True
                        st.session_state[f"scenario_choice_{scenario['id']}"] = opt['text']
                        st.session_state[f"scenario_feedback_{scenario['id']}"] = opt['feedback']
                    break

            st.divider()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("返回Prompt挑战"):
                st.session_state.personal_step = 6
                st.rerun()
        with col2:
            if st.button("继续：AI知识问答", type="primary"):
                st.session_state.personal_step = 8
                st.rerun()

    # ===== Step 8: AI知识问答 =====
    elif st.session_state.personal_step == 8:
        st.markdown('''
        <div style="text-align:center;padding:1.5rem;margin-bottom:1.5rem;">
            <div style="font-size:1.5rem;font-weight:700;">AI知识问答</div>
            <div style="color:#64748b;">测试你的AI知识储备</div>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化知识问答分数
        if 'quiz_score' not in st.session_state:
            st.session_state.quiz_score = 0
        if 'quiz_count' not in st.session_state:
            st.session_state.quiz_count = 0

        for i, quiz in enumerate(AI_KNOWLEDGE_QUIZ):
            st.markdown(f"**问题 {i+1}：** {quiz['question']}")

            # 使用radio让用户选择
            selected_idx = st.radio(
                "选择答案：",
                range(len(quiz['options'])),
                format_func=lambda x, quiz=quiz: quiz['options'][x],
                key=f"quiz_{i}",
                label_visibility="collapsed"
            )

            # 显示答案反馈
            if f"quiz_answered_{i}" not in st.session_state:
                if st.button("提交答案", key=f"submit_quiz_{i}"):
                    st.session_state[f"quiz_answered_{i}"] = True
                    st.session_state[f"quiz_selected_{i}"] = selected_idx
                    if selected_idx == quiz['correct']:
                        st.session_state.quiz_score += 25
                        st.session_state.quiz_count += 1
                    st.rerun()
            else:
                selected_idx = st.session_state.get(f"quiz_selected_{i}", selected_idx)
                if selected_idx == quiz['correct']:
                    st.success(f"回答正确！{quiz['explanation']}")
                else:
                    st.error(f"回答错误。{quiz['explanation']}")

            st.divider()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("返回AI对话模拟"):
                st.session_state.personal_step = 7
                st.rerun()
        with col2:
            if st.button("继续：每日习惯测试", type="primary"):
                st.session_state.personal_step = 9
                st.rerun()

    # ===== Step 9: 每日AI使用习惯测试 =====
    elif st.session_state.personal_step == 9:
        st.markdown('''
        <div style="text-align:center;padding:1.5rem;margin-bottom:1.5rem;">
            <div style="font-size:1.5rem;font-weight:700;">每日AI使用习惯测试</div>
            <div style="color:#64748b;">测测你的生活有多AI Native</div>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化习惯测试答案
        if 'habit_answers' not in st.session_state:
            st.session_state.habit_answers = {}

        for habit in DAILY_AI_HABITS:
            st.markdown(f"**{habit['question']}**")

            selected = st.radio(
                "选择：",
                habit['options'],
                key=f"habit_{habit['id']}",
                label_visibility="collapsed"
            )

            st.session_state.habit_answers[habit['id']] = selected

            # 显示AI指数
            if selected == habit['options'][1]:  # 问AI
                st.caption("AI指数：高")
            elif selected == habit['options'][2]:  # 其他AI相关选项
                st.caption("AI指数：中高")
            else:
                st.caption("AI指数：待提升")

            st.divider()

        # 计算AI习惯得分
        ai_habit_count = sum(1 for ans in st.session_state.habit_answers.values()
                            if "AI" in ans or "问AI" in ans or "让AI" in ans)

        st.info(f"你的AI习惯指数：{ai_habit_count}/{len(DAILY_AI_HABITS)} 个场景使用AI")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("返回知识问答"):
                st.session_state.personal_step = 8
                st.rerun()
        with col2:
            if st.button("查看我的AI人格", type="primary"):
                st.session_state.personal_step = 10
                st.rerun()

    # ===== Step 10: 结果页面 =====
    elif st.session_state.personal_step == 10:
        answers = st.session_state.personal_answers
        
        # 检查AI分析器是否可用
        analyzer_available = False
        analyzer = None
        try:
            analyzer = get_analyzer()
            if analyzer and analyzer.is_available():
                analyzer_available = True
        except:
            pass
        
        # 计算各维度分数
        dimension_scores = {}
        for q_id, ans in answers.items():
            dim = ans["dimension"]
            if dim not in dimension_scores:
                dimension_scores[dim] = []
            
            # 检查是否有"其他"选项被选择
            if ans.get("text") == "其他":
                custom_answer = st.session_state.personal_other_answers.get(q_id, "")
                if custom_answer:
                    # 使用AI分析自定义答案
                    analysis_result = analyze_other_answer(
                        next((q["question"] for q in FUN_QUESTIONS if q["id"] == q_id), ""),
                        custom_answer,
                        analyzer if analyzer_available else None
                    )
                    dimension_scores[dim].append(analysis_result["score"])
                else:
                    # 用户选择了"其他"但没有填写答案，给最低分
                    dimension_scores[dim].append(0)
            else:
                dimension_scores[dim].append(ans["score"])
        
        avg_scores = {}
        for dim, scores in dimension_scores.items():
            avg_scores[dim] = sum(scores) / len(scores)
        
        total_score = calculate_score(avg_scores)
        level = calculate_level(total_score)
        fun_info = FUN_TITLES[level]
        
        # 判定AI人格类型
        personality = determine_ai_personality(avg_scores, answers)
        
        # 计算成就
        achievement_data = {
            "total_score": total_score,
            "tool_count": len(st.session_state.personal_tools),
        }
        for q_id, ans in answers.items():
            achievement_data[f"{q_id}_score"] = ans["score"]
        
        unlocked = []
        for ach in ACHIEVEMENTS:
            try:
                if ach["condition"](achievement_data):
                    unlocked.append(ach)
            except:
                pass
        
        # ===== 结果展示 =====
        # 主结果卡片
        st.markdown(f'''
        <div class="result-hero">
            <div class="result-emoji">{fun_info["emoji"]}</div>
            <div class="result-title">{fun_info["title"]}</div>
            <div style="font-size:1.1rem;opacity:0.9;margin:0.5rem 0;">{fun_info["tagline"]}</div>
            <div class="result-score">{total_score}分</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # AI人格类型
        st.markdown("---")
        st.markdown("### 你的AI人格类型")
        p = AI_PERSONALITIES[personality]
        st.markdown(f'''
        <div style="background:white;border-radius:12px;padding:1.5rem;border:2px solid {p['color']};margin:1rem 0;">
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
                <div style="font-size:3rem;">{p["emoji"]}</div>
                <div>
                    <div style="font-size:1.5rem;font-weight:700;color:{p['color']};">{personality} - {p['name']}</div>
                    <div style="color:#64748b;">{p['trait']}</div>
                </div>
            </div>
            <p style="color:#475569;margin-bottom:0.75rem;">{p['desc']}</p>
            <div style="background:#f8fafc;padding:0.75rem;border-radius:8px;font-size:0.9rem;color:#64748b;">
                <strong>经典场景：</strong>{p['scene']}
            </div>
            <div style="margin-top:0.75rem;">
                <strong>常用工具：</strong>
                {" ".join([f'<span style="background:#e3f2fd;padding:2px 8px;border-radius:4px;margin:2px;display:inline-block;font-size:0.85rem;">{t}</span>' for t in p['tools']])}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 雷达图
        st.subheader("AI能力雷达图")
        import plotly.graph_objects as go
        categories = [AI_NATIVE_DIMENSIONS[dim]["name"] for dim in AI_NATIVE_DIMENSIONS.keys()]
        values = [avg_scores.get(dim, 0) for dim in AI_NATIVE_DIMENSIONS.keys()]
        values.append(values[0])
        fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories + [categories[0]], fill='toself',
                                              fillcolor='rgba(102, 126, 234, 0.3)',
                                              line=dict(color='rgba(102, 126, 234, 1)')))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                         showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # 各维度进度条
        st.subheader("各维度得分")
        dimension_colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        dim_names = {"ai_first_mindset": "AI优先思维", "deep_collaboration": "深度协作", 
                     "problem_reframing": "问题重构", "learning_mode": "学习模式",
                     "iteration_agility": "迭代敏捷", "boundary_awareness": "边界认知"}
        for i, (dim_key, score) in enumerate(avg_scores.items()):
            color = dimension_colors[i % len(dimension_colors)]
            name = dim_names.get(dim_key, dim_key)
            st.markdown(f'''
            <div style="margin:0.5rem 0;">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
                    <span style="font-weight:500;">{name}</span>
                    <span style="font-weight:600;color:{color};">{score:.0f}分</span>
                </div>
                <div class="dimension-bar">
                    <div class="dimension-fill" style="width:{score}%;background:{color};"></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 成就解锁
        st.markdown("---")
        st.subheader(f"成就解锁 ({len(unlocked)}/{len(ACHIEVEMENTS)})")
        ach_cols = st.columns(4)
        for i, ach in enumerate(unlocked):
            with ach_cols[i % 4]:
                st.markdown(f'''
                <div style="text-align:center;padding:0.75rem;background:linear-gradient(135deg,#fef3c7,#fde68a);
                     border-radius:8px;margin:0.25rem 0;">
                    <div style="font-size:1.5rem;">{ach["icon"]}</div>
                    <div style="font-weight:600;font-size:0.8rem;">{ach["name"]}</div>
                    <div style="font-size:0.7rem;color:#92400e;">{ach["desc"]}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        # 未解锁的成就
        locked = [a for a in ACHIEVEMENTS if a not in unlocked]
        if locked:
            with st.expander(f"未解锁的成就 ({len(locked)}个)"):
                for ach in locked:
                    st.markdown(f'''
                    <div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem;opacity:0.5;">
                        <div style="font-size:1.5rem;">{ach["icon"]}</div>
                        <div>
                            <div style="font-weight:500;">{ach["name"]}</div>
                            <div style="font-size:0.8rem;color:#64748b;">{ach["desc"]}</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # 对话模拟详细反馈
        if st.session_state.chat_scenario_count > 0:
            st.markdown("---")
            st.subheader("AI对话模拟反馈")
            st.write(f"你在对话模拟环节获得了 **{st.session_state.chat_scenario_score}** 分")
            
            for scenario in AI_CHAT_SCENARIOS:
                scenario_id = scenario['id']
                if f"scenario_completed_{scenario_id}" in st.session_state:
                    choice = st.session_state.get(f"scenario_choice_{scenario_id}", "")
                    feedback = st.session_state.get(f"scenario_feedback_{scenario_id}", "")
                    
                    with st.container():
                        st.markdown(f"**场景：** {scenario['scenario']}")
                        st.markdown(f"**你的选择：** {choice}")
                        st.markdown(f"**反馈：** {feedback}")
                        st.divider()
        
        # AI给你的寄语
        st.markdown("---")
        st.subheader("AI给你的寄语")
        st.markdown(f'''
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;padding:1.5rem;color:white;">
            <p style="font-size:1.1rem;line-height:1.8;">{fun_info["advice"]}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # 使用的工具统计
        if st.session_state.personal_tools:
            st.markdown("---")
            st.subheader(f"你的AI工具箱 ({len(st.session_state.personal_tools)}个)")
            tool_cols = st.columns(5)
            for i, tool_name in enumerate(st.session_state.personal_tools):
                tool = next((t for t in AI_TOOLS_LIST if t["name"] == tool_name), None)
                icon = tool["icon"] if tool else "🔧"
                with tool_cols[i % 5]:
                    st.markdown(f'''
                    <div style="text-align:center;padding:0.5rem;background:#f8fafc;border-radius:8px;margin:0.25rem 0;">
                        <div style="font-size:1.2rem;">{icon}</div>
                        <div style="font-size:0.75rem;">{tool_name}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # 分享卡片
        st.markdown("---")
        st.subheader("分享你的AI人格")
        share_text = f"我是{p['emoji']}{p['name']}，AI Native等级：{fun_info['emoji']}{fun_info['title']}({total_score}分)"
        st.markdown(f'''
        <div class="share-card">
            <div style="font-size:1.5rem;">{p["emoji"]} {fun_info["emoji"]}</div>
            <div style="font-size:1.1rem;font-weight:600;margin:0.5rem 0;">{share_text}</div>
            <div style="color:#64748b;font-size:0.85rem;">来测测你的AI人格吧！</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 重新测试
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("重新测试", use_container_width=True):
                st.session_state.personal_step = 0
                st.session_state.personal_answers = {}
                st.session_state.personal_tools = []
                st.rerun()
        with col2:
            if st.button("返回首页", use_container_width=True):
                st.session_state.app_mode = "hr"
                st.rerun()

# ==================== 主入口 ====================
# 侧边栏模式切换
st.sidebar.markdown("### 选择使用模式")

mode_col1, mode_col2 = st.columns(2)
with mode_col1:
    if st.sidebar.button("HR招聘版", use_container_width=True, 
                         type="primary" if st.session_state.app_mode == "hr" else "secondary"):
        st.session_state.app_mode = "hr"
        st.rerun()

with mode_col2:
    if st.sidebar.button("个人测评版", use_container_width=True,
                         type="primary" if st.session_state.app_mode == "personal" else "secondary"):
        st.session_state.app_mode = "personal"
        st.rerun()

st.sidebar.markdown("---")

# 新增评估页面入口（HR版本）
if st.session_state.app_mode == "hr":
    st.sidebar.markdown("### 快捷操作")
    if st.sidebar.button("+ 新增候选人评估", use_container_width=True):
        st.session_state.app_mode = "hr_add"
        st.rerun()

# 根据模式渲染不同页面
if st.session_state.app_mode == "hr":
    render_hr_version()
elif st.session_state.app_mode == "hr_add":
    render_hr_add_page()
elif st.session_state.app_mode == "personal":
    render_personal_version()
