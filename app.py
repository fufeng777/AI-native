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

# 数据存储路径 - 使用绝对路径确保数据持久化
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CANDIDATES_FILE = DATA_DIR / "candidates.json"
RESUMES_DIR = DATA_DIR / "resumes"
RESUMES_DIR.mkdir(exist_ok=True)

# 快速判断清单
QUICK_CHECKLIST = [
    "候选人第一反应是'AI'而不是'人'（接到新任务时的本能指向）",
    "候选人是否有系统化的提示词库（对Prompt有设计、有优化）",
    "候选人是否拥有'自己的方法论'（对AI的使用有提炼、有优化）",
    "候选人是否改造过自己的工作流（用AI改变了做法）",
    "候选人对AI的吐槽是否具体（能精准指出不靠谱之处）",
    "候选人是否有事实核查习惯（不盲目相信AI输出）",
    "候选人有没有'AI焦虑'（积极意义上怕掉队，持续关注前沿）"
]

# 预设职位类别
JOB_CATEGORIES = [
    "产品", "运营", "算法", "工程", "设计", "市场", "销售", "人力资源", "财务", "其他"
]

# AI Native人才画像模板 - 针对不同岗位的评估侧重点
TALENT_PROFILES = {
    "产品": {
        "name": "AI产品经理",
        "description": "能将AI能力转化为产品价值，具备AI-First思维和用户洞察",
        "key_dimensions": ["ai_first_mindset", "problem_reframing", "deep_collaboration"],
        "dimension_weights": {
            "ai_first_mindset": 1.2,
            "prompt_engineering": 0.8,
            "deep_collaboration": 1.0,
            "problem_reframing": 1.2,
            "learning_mode": 0.8,
            "iteration_agility": 0.8,
            "boundary_awareness": 0.9,
            "critical_validation": 1.0
        },
        "ideal_tools": ["ChatGPT", "Claude", "Notion AI", "Figma AI"],
        "interview_focus": ["如何用AI发现用户需求", "AI功能设计案例", "AI产品落地经验"]
    },
    "运营": {
        "name": "AI运营专家",
        "description": "用AI提升运营效率，擅长内容生成、数据分析和自动化流程",
        "key_dimensions": ["prompt_engineering", "iteration_agility", "learning_mode"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.2,
            "deep_collaboration": 0.9,
            "problem_reframing": 0.8,
            "learning_mode": 1.0,
            "iteration_agility": 1.2,
            "boundary_awareness": 0.7,
            "critical_validation": 0.9
        },
        "ideal_tools": ["ChatGPT", "Midjourney", "剪映AI", "Coze"],
        "interview_focus": ["AI内容生产案例", "自动化运营流程", "提示词优化经验"]
    },
    "算法": {
        "name": "AI算法工程师",
        "description": "深入理解AI原理，能优化模型、设计智能体、解决技术难题",
        "key_dimensions": ["deep_collaboration", "boundary_awareness", "critical_validation"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.1,
            "deep_collaboration": 1.2,
            "problem_reframing": 1.0,
            "learning_mode": 1.0,
            "iteration_agility": 0.9,
            "boundary_awareness": 1.2,
            "critical_validation": 1.2
        },
        "ideal_tools": ["Claude", "GitHub Copilot", "Cursor", "HuggingFace"],
        "interview_focus": ["模型优化经验", "智能体设计案例", "AI技术边界认知"]
    },
    "工程": {
        "name": "AI原生工程师",
        "description": "用AI辅助编程，快速交付高质量代码，持续迭代技术栈",
        "key_dimensions": ["prompt_engineering", "iteration_agility", "learning_mode"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.2,
            "deep_collaboration": 1.0,
            "problem_reframing": 0.9,
            "learning_mode": 1.1,
            "iteration_agility": 1.1,
            "boundary_awareness": 1.0,
            "critical_validation": 1.0
        },
        "ideal_tools": ["GitHub Copilot", "Cursor", "ChatGPT", "Claude"],
        "interview_focus": ["AI辅助编程效率", "代码审查AI使用", "技术栈快速迭代"]
    },
    "设计": {
        "name": "AI创意设计师",
        "description": "融合AI工具进行创意设计，人机协作产出高质量作品",
        "key_dimensions": ["prompt_engineering", "deep_collaboration", "problem_reframing"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.3,
            "deep_collaboration": 1.1,
            "problem_reframing": 1.0,
            "learning_mode": 0.9,
            "iteration_agility": 1.0,
            "boundary_awareness": 0.8,
            "critical_validation": 0.9
        },
        "ideal_tools": ["Midjourney", "Stable Diffusion", "DALL-E", "Figma AI"],
        "interview_focus": ["AI设计工作流", "提示词创作技巧", "人机协作设计案例"]
    },
    "市场": {
        "name": "AI营销专家",
        "description": "用AI赋能营销全链路，从创意到数据分析全面提效",
        "key_dimensions": ["prompt_engineering", "ai_first_mindset", "iteration_agility"],
        "dimension_weights": {
            "ai_first_mindset": 1.1,
            "prompt_engineering": 1.2,
            "deep_collaboration": 0.9,
            "problem_reframing": 1.0,
            "learning_mode": 0.9,
            "iteration_agility": 1.1,
            "boundary_awareness": 0.8,
            "critical_validation": 0.9
        },
        "ideal_tools": ["ChatGPT", "Midjourney", "Jasper", "HeyGen"],
        "interview_focus": ["AI营销案例", "内容生产效率提升", "AI创意方法论"]
    },
    "销售": {
        "name": "AI赋能销售",
        "description": "用AI提升销售效率，客户洞察、话术优化、数据分析",
        "key_dimensions": ["learning_mode", "deep_collaboration", "ai_first_mindset"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 0.9,
            "deep_collaboration": 1.1,
            "problem_reframing": 0.9,
            "learning_mode": 1.1,
            "iteration_agility": 1.0,
            "boundary_awareness": 0.8,
            "critical_validation": 0.9
        },
        "ideal_tools": ["ChatGPT", "Kimi", "Notion AI", "飞书AI"],
        "interview_focus": ["AI辅助客户分析", "销售话术优化", "CRM智能化使用"]
    },
    "人力资源": {
        "name": "AI HR专家",
        "description": "用AI革新招聘培训，人才画像、面试辅助、员工发展",
        "key_dimensions": ["critical_validation", "deep_collaboration", "problem_reframing"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.0,
            "deep_collaboration": 1.1,
            "problem_reframing": 1.0,
            "learning_mode": 1.0,
            "iteration_agility": 0.9,
            "boundary_awareness": 1.0,
            "critical_validation": 1.2
        },
        "ideal_tools": ["ChatGPT", "Claude", "Kimi", "飞书AI"],
        "interview_focus": ["AI招聘实践", "人才评估AI化", "培训内容AI生成"]
    },
    "财务": {
        "name": "AI财务分析师",
        "description": "用AI处理财务数据，报表分析、风险识别、决策支持",
        "key_dimensions": ["critical_validation", "boundary_awareness", "deep_collaboration"],
        "dimension_weights": {
            "ai_first_mindset": 0.9,
            "prompt_engineering": 1.0,
            "deep_collaboration": 1.0,
            "problem_reframing": 0.9,
            "learning_mode": 0.9,
            "iteration_agility": 0.9,
            "boundary_awareness": 1.2,
            "critical_validation": 1.3
        },
        "ideal_tools": ["ChatGPT", "Excel AI", "Kimi", "Claude"],
        "interview_focus": ["AI财务分析案例", "数据准确性验证", "风险识别AI应用"]
    },
    "其他": {
        "name": "AI通用人才",
        "description": "具备AI Native基础能力，能快速适应不同岗位需求",
        "key_dimensions": ["ai_first_mindset", "learning_mode", "iteration_agility"],
        "dimension_weights": {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.0,
            "deep_collaboration": 1.0,
            "problem_reframing": 1.0,
            "learning_mode": 1.0,
            "iteration_agility": 1.0,
            "boundary_awareness": 1.0,
            "critical_validation": 1.0
        },
        "ideal_tools": ["ChatGPT", "Claude", "Kimi"],
        "interview_focus": ["AI使用习惯", "学习能力", "AI工具探索"]
    }
}

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

# 16种AI人格画像（四维度MBTI风格）
AI_PERSONALITIES = {
    # === 四大维度 ===
    # I=内向型/独立型  E=外向型/社交型
    # T=技术型/工具型  F=创意型/表达型
    # P=实践型/效率型  J=战略型/规划型
    # A=分析型/理性型  S=感性型/体验型

    # ---- IT型：内向·技术·实践·分析 ----
    "ITPA": {"name": "独狼极客", "emoji": "🐺", "desc": "独自钻研AI技术，追求极致效率。深夜独自调试代码，用AI构建自动化系统，不社交但实力恐怖。", "trait": "独立 | 技术驱动 | 效率至上", "color": "#1E40AF", "tools": ["Cursor", "GitHub Copilot", "DeepSeek", "n8n"], "scene": "凌晨3点，你独自用AI重构了整个后端系统，第二天同事以为系统被黑了"},
    "ITPS": {"name": "效率机器", "emoji": "⚡", "desc": "把AI当效率工具用到极致。每个工作流程都自动化，每天省出4小时摸鱼时间。", "trait": "高效 | 流程化 | 实用主义", "color": "#0369A1", "tools": ["Zapier", "Make", "Notion AI", "飞书AI"], "scene": "你用AI把周报自动生成了，同事还在手动写"},
    "ITJA": {"name": "架构大师", "emoji": "🏗️", "desc": "擅长用AI设计和构建复杂系统。先规划再执行，代码架构清晰如画。", "trait": "系统思维 | 规划能力强 | 严谨", "color": "#1E3A8A", "tools": ["LangChain", "Dify", "Coze", "Trae"], "scene": "你用AI设计了一套完整的Agent架构图，比架构师画的还清楚"},
    "ITJS": {"name": "数据先知", "emoji": "🔮", "desc": "用AI洞察数据背后的规律。看一眼数据就能预测趋势，决策靠数据不靠直觉。", "trait": "数据敏感 | 洞察力强 | 理性", "color": "#312E81", "tools": ["Perplexity", "NotebookLM", "ChatGPT数据分析", "Elicit"], "scene": "你用AI分析了竞品数据，发现了对手都没注意到的市场机会"},

    # ---- IF型：内向·技术·实践·感性 ----
    "IFPA": {"name": "AI艺术家", "emoji": "🎨", "desc": "用AI释放无限创意，作品令人惊叹。把AI当画笔，创作出超越想象的作品。", "trait": "创意无限 | 审美在线 | 表达欲强", "color": "#7C3AED", "tools": ["Midjourney", "Suno", "Runway", "DALL-E 3"], "scene": "你用AI生成的插画被误认为是专业设计师的作品"},
    "IFPS": {"name": "内容创客", "emoji": "✍️", "desc": "用AI高效产出内容，从文案到视频全覆盖。一个人就是一支内容团队。", "trait": "高产 | 多面手 | 快速迭代", "color": "#6D28D9", "tools": ["ChatGPT", "Gamma", "剪映AI", "Canva AI"], "scene": "你一个人用AI完成了品牌全套视觉物料，设计师以为你请了外包团队"},
    "IFJA": {"name": "产品幻视者", "emoji": "💡", "desc": "用AI快速验证产品想法，从概念到原型只需一天。脑中的产品总能变成现实。", "trait": "产品思维 | 快速验证 | 用户导向", "color": "#5B21B6", "tools": ["v0.dev", "Figma AI", "ChatGPT", "Claude"], "scene": "你用AI在一天内做出了产品MVP，投资人以为你有一个10人团队"},
    "IFJS": {"name": "学习黑客", "emoji": "🧠", "desc": "用AI破解学习难题，任何新领域都能快速上手。知识面广得像个行走的百科全书。", "trait": "好奇心强 | 快速学习 | 知识面广", "color": "#4C1D95", "tools": ["Khanmigo", "Duolingo Max", "Perplexity", "Consensus"], "scene": "你用AI在一周内学会了新编程语言，然后做出了一个完整项目"},

    # ---- ET型：外向·技术·效率·分析 ----
    "ETPA": {"name": "AI布道师", "emoji": "📣", "desc": "逢人就安利AI工具，朋友圈全是AI相关内容。公司里第一个用AI的人，也是最后一个放弃的人。", "trait": "热情 | 分享欲强 | 影响力大", "color": "#DC2626", "tools": ["ChatGPT", "Kimi", "豆包", "通义千问"], "scene": "你成功让全公司都用上了AI，老板给你加了薪"},
    "ETPS": {"name": "流程终结者", "emoji": "⚙️", "desc": "看到重复劳动就手痒，用AI自动化一切。你的口头禅是'这个可以自动化'。", "trait": "自动化狂 | 懒得聪明 | 流程优化", "color": "#B91C1C", "tools": ["Zapier", "Make", "Coze", "n8n"], "scene": "你用AI自动化了80%的日常工作，现在每天下午3点就下班了"},
    "ETJA": {"name": "战略指挥官", "emoji": "🎯", "desc": "善于用AI制定战略和规划。不是在用工具，而是在指挥一支AI军队。", "trait": "全局视角 | 战略思维 | 领导力", "color": "#991B1B", "tools": ["Claude", "ChatGPT", "Coze", "Dify"], "scene": "你用AI帮CEO制定了年度战略规划，董事会以为请了咨询公司"},
    "ETJS": {"name": "AI科学家", "emoji": "🔬", "desc": "用AI进行深度研究和分析，追求AI能力的边界。不是在使用AI，而是在研究AI。", "trait": "研究型 | 追求极致 | 学术精神", "color": "#7F1D1D", "tools": ["NotebookLM", "Elicit", "Consensus", "Scholarcy"], "scene": "你用AI写了一篇论文，被顶级会议收录了"},

    # ---- EF型：外向·技术·效率·感性 ----
    "EFPA": {"name": "AI社交家", "emoji": "🤝", "desc": "把AI当朋友和搭档，和AI的对话记录比和朋友的还长。擅长用AI提升沟通效率。", "trait": "善于沟通 | 人际导向 | AI知己", "color": "#059669", "tools": ["ChatGPT", "Pi", "Claude", "豆包"], "scene": "你用AI帮忙写了给客户的道歉信，客户感动得哭了"},
    "EFPS": {"name": "创意总监", "emoji": "🎭", "desc": "用AI激发团队创意，擅长把AI生成的灵感转化为落地方案。一个人带动整个团队的AI化。", "trait": "领导力 | 创意驱动 | 落地能力", "color": "#047857", "tools": ["Midjourney", "Gamma", "Canva AI", "Runway"], "scene": "你用AI带领团队在48小时内完成了一个品牌全案"},
    "EFJA": {"name": "AI产品经理", "emoji": "📱", "desc": "用AI理解用户需求，快速迭代产品。PRD、竞品分析、用户画像，AI全包了。", "trait": "产品感强 | 用户导向 | 数据驱动", "color": "#065F46", "tools": ["ChatGPT", "Claude", "Notion AI", "Perplexity"], "scene": "你用AI分析用户反馈，发现了产品经理都没注意到的痛点"},
    "EFJS": {"name": "体验设计师", "emoji": "✨", "desc": "用AI设计极致用户体验，从交互到视觉都追求完美。每个像素都有它的意义。", "trait": "审美极致 | 用户体验 | 细节控", "color": "#064E3B", "tools": ["Figma AI", "Adobe Firefly", "v0.dev", "Canva AI"], "scene": "你用AI设计的界面，用户留存率提升了40%"}
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

# 人才库标签预设
TALENT_TAGS = [
    "AI高手", "潜力股", "技术专家", "产品思维", "沟通能力强",
    "学习能力强", "经验丰富", "创新思维", "团队协作", "独立工作",
    "紧急招聘", "高优先级", "已联系", "待跟进", "已拒绝", "已录用"
]

# 面试阶段定义
INTERVIEW_STAGES = [
    {"id": "new", "name": "新简历", "color": "#9CA3AF"},
    {"id": "screening", "name": "初筛中", "color": "#60A5FA"},
    {"id": "interview1", "name": "一面", "color": "#34D399"},
    {"id": "interview2", "name": "二面", "color": "#10B981"},
    {"id": "interview3", "name": "三面", "color": "#059669"},
    {"id": "offer", "name": "Offer", "color": "#FBBF24"},
    {"id": "hired", "name": "已录用", "color": "#10B981"},
    {"id": "rejected", "name": "已拒绝", "color": "#EF4444"},
    {"id": "archived", "name": "已归档", "color": "#6B7280"}
]

# AI工具列表（60+工具，包含公司和功能介绍）
AI_TOOLS_LIST = [
    # === 对话大模型 ===
    {"name": "ChatGPT", "category": "对话大模型", "icon": "static/icons/openai.png",
     "company": "OpenAI", "desc": "全球最流行的AI对话助手，支持文本、图像、语音多模态交互，具备强大的推理和创作能力"},
    {"name": "Claude", "category": "对话大模型", "icon": "static/icons/anthropic.svg",
     "company": "Anthropic", "desc": "以安全性和长文本处理能力著称，擅长代码生成、文档分析和深度推理"},
    {"name": "Gemini", "category": "对话大模型", "icon": "static/icons/google.svg",
     "company": "Google", "desc": "谷歌旗舰AI模型，原生多模态，支持超长上下文，与Google生态深度整合"},
    {"name": "GPT-4o", "category": "对话大模型", "icon": "static/icons/openai.png",
     "company": "OpenAI", "desc": "OpenAI最新旗舰模型，支持实时语音对话、图像理解，响应速度极快"},
    {"name": "o1/o3", "category": "对话大模型", "icon": "static/icons/openai.png",
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
    {"name": "DALL-E 3", "category": "AI绘画", "icon": "static/icons/openai.png",
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
    {"name": "Sora", "category": "AI视频", "icon": "static/icons/openai.png",
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
         {"text": "先百度/Google搜一下看看", "score": {"ie": 20, "tf": 30, "pj": 40, "as": 50}, "tag": "传统搜索派"},
         {"text": "问ChatGPT这个领域是什么、该怎么做", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "AI咨询派"},
         {"text": "让AI帮我制定一个完整的执行方案", "score": {"ie": 50, "tf": 60, "pj": 60, "as": 60}, "tag": "AI规划派"},
         {"text": "直接让AI Agent帮我搭建框架，我负责审核", "score": {"ie": 60, "tf": 80, "pj": 70, "as": 70}, "tag": "AI代管派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q2", "dimension": "deep_collaboration", "category": "AI本能反应",
     "question": "你写Prompt的习惯是？",
     "options": [
         {"text": "就写几个关键词，比如'帮我写个方案'", "score": {"ie": 30, "tf": 20, "pj": 30, "as": 30}, "tag": "佛系Prompt"},
         {"text": "会写清楚背景、需求、格式要求", "score": {"ie": 40, "tf": 50, "pj": 50, "as": 50}, "tag": "结构化Prompt"},
         {"text": "会设定角色、提供示例、多轮迭代优化", "score": {"ie": 50, "tf": 70, "pj": 60, "as": 60}, "tag": "高级Prompt"},
         {"text": "我有自己的Prompt模板库，随时复用", "score": {"ie": 40, "tf": 90, "pj": 70, "as": 70}, "tag": "Prompt工程师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q3", "dimension": "problem_reframing", "category": "AI本能反应",
     "question": "遇到一个棘手的工作问题，你会？",
     "options": [
         {"text": "自己苦思冥想，实在不行问同事", "score": {"ie": 10, "tf": 30, "pj": 40, "as": 40}, "tag": "独立思考派"},
         {"text": "把问题描述给AI，看看它有什么建议", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "AI顾问派"},
         {"text": "让AI帮我重新定义问题，找到更好的切入点", "score": {"ie": 50, "tf": 60, "pj": 70, "as": 70}, "tag": "问题重构派"},
         {"text": "和AI来一场头脑风暴，碰撞出全新思路", "score": {"ie": 70, "tf": 50, "pj": 60, "as": 50}, "tag": "共创派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q4", "dimension": "learning_mode", "category": "AI本能反应",
     "question": "老板让你一周内学会一个你完全不懂的新技能，你会？",
     "options": [
         {"text": "买本书/找课程，从零开始系统学习", "score": {"ie": 20, "tf": 40, "pj": 50, "as": 50}, "tag": "传统学习派"},
         {"text": "让AI帮我制定学习计划，推荐学习资源", "score": {"ie": 40, "tf": 50, "pj": 60, "as": 60}, "tag": "AI辅助学习"},
         {"text": "直接用AI边做边学，遇到问题就问", "score": {"ie": 50, "tf": 60, "pj": 80, "as": 50}, "tag": "实战派"},
         {"text": "让AI帮我快速搭建原型，在实践中掌握", "score": {"ie": 60, "tf": 80, "pj": 90, "as": 60}, "tag": "极速上手派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q5", "dimension": "iteration_agility", "category": "AI本能反应",
     "question": "你手机里装了几个AI相关的App？",
     "options": [
         {"text": "0-1个，就一个ChatGPT", "score": {"ie": 20, "tf": 30, "pj": 30, "as": 40}, "tag": "专一派"},
         {"text": "2-4个，常用的那几个", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "实用派"},
         {"text": "5-9个，看到新的就想试试", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 50}, "tag": "尝鲜派"},
         {"text": "10个以上，手机内存都被AI占满了", "score": {"ie": 80, "tf": 60, "pj": 70, "as": 50}, "tag": "AI收藏家"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第二部分：AI社交风格 ===
    {"id": "q6", "dimension": "boundary_awareness", "category": "AI社交风格",
     "question": "AI给你一个看起来很专业但你不确定的答案，你会？",
     "options": [
         {"text": "直接用，AI说的应该没错", "score": {"ie": 30, "tf": 20, "pj": 30, "as": 10}, "tag": "信任派"},
         {"text": "大概看一下，没问题就用", "score": {"ie": 40, "tf": 40, "pj": 40, "as": 40}, "tag": "粗略检查派"},
         {"text": "交叉验证一下，用另一个AI或搜索引擎确认", "score": {"ie": 50, "tf": 60, "pj": 60, "as": 80}, "tag": "验证派"},
         {"text": "让AI自己批判自己的答案，找出漏洞", "score": {"ie": 50, "tf": 80, "pj": 70, "as": 90}, "tag": "批判大师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q7", "dimension": "ai_first_mindset", "category": "AI社交风格",
     "question": "你怎么形容你和AI的关系？",
     "options": [
         {"text": "就是个工具，用完就关", "score": {"ie": 10, "tf": 40, "pj": 40, "as": 40}, "tag": "工具关系"},
         {"text": "像个助手，帮我处理杂活", "score": {"ie": 40, "tf": 50, "pj": 50, "as": 50}, "tag": "助手关系"},
         {"text": "像个搭档，一起讨论解决问题", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 60}, "tag": "搭档关系"},
         {"text": "像个导师/朋友，有时候还会跟它聊天", "score": {"ie": 80, "tf": 40, "pj": 50, "as": 70}, "tag": "灵魂伴侣"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q8", "dimension": "deep_collaboration", "category": "AI社交风格",
     "question": "你用AI做过最让你自豪的事情是？",
     "options": [
         {"text": "写过邮件、翻译过文档", "score": {"ie": 30, "tf": 30, "pj": 30, "as": 30}, "tag": "基础应用"},
         {"text": "用AI写过代码、做过数据分析", "score": {"ie": 40, "tf": 70, "pj": 60, "as": 70}, "tag": "进阶应用"},
         {"text": "用AI完成了一个完整的项目", "score": {"ie": 50, "tf": 60, "pj": 70, "as": 60}, "tag": "项目级应用"},
         {"text": "搭建了AI自动化工作流，持续节省时间", "score": {"ie": 50, "tf": 80, "pj": 80, "as": 70}, "tag": "系统级应用"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q9", "dimension": "deep_collaboration", "category": "AI社交风格",
     "question": "你和朋友聊天时，提到AI的频率是？",
     "options": [
         {"text": "很少提，觉得没什么好说的", "score": {"ie": 10, "tf": 30, "pj": 30, "as": 30}, "tag": "低调派"},
         {"text": "偶尔分享一些好用的AI技巧", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "分享派"},
         {"text": "经常安利，朋友都说我被AI洗脑了", "score": {"ie": 70, "tf": 40, "pj": 60, "as": 50}, "tag": "布道派"},
         {"text": "三句话不离AI，朋友都开始用了", "score": {"ie": 90, "tf": 40, "pj": 70, "as": 40}, "tag": "AI传教士"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q10", "dimension": "learning_mode", "category": "AI社交风格",
     "question": "你有没有给AI取过名字或者设定过人设？",
     "options": [
         {"text": "没有，就叫ChatGPT", "score": {"ie": 10, "tf": 30, "pj": 30, "as": 20}, "tag": "务实派"},
         {"text": "想过但没做过", "score": {"ie": 30, "tf": 30, "pj": 40, "as": 40}, "tag": "犹豫派"},
         {"text": "设定过角色，比如'你是一个资深产品经理'", "score": {"ie": 50, "tf": 50, "pj": 50, "as": 60}, "tag": "角色扮演派"},
         {"text": "取了名字，还设定了性格、背景故事", "score": {"ie": 70, "tf": 40, "pj": 60, "as": 80}, "tag": "AI养成派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第三部分：AI生活场景 ===
    {"id": "q11", "dimension": "ai_first_mindset", "category": "AI生活场景",
     "question": "周末朋友聚餐，需要选餐厅，你会？",
     "options": [
         {"text": "打开大众点评自己翻", "score": {"ie": 20, "tf": 30, "pj": 30, "as": 40}, "tag": "传统派"},
         {"text": "问AI推荐附近有什么好吃的", "score": {"ie": 50, "tf": 40, "pj": 50, "as": 50}, "tag": "AI推荐派"},
         {"text": "让AI根据大家的口味偏好来推荐", "score": {"ie": 50, "tf": 50, "pj": 60, "as": 60}, "tag": "AI管家派"},
         {"text": "让AI做一个餐厅对比分析表格", "score": {"ie": 40, "tf": 70, "pj": 70, "as": 90}, "tag": "AI分析师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q12", "dimension": "iteration_agility", "category": "AI生活场景",
     "question": "看到一个新AI工具发布，你的反应是？",
     "options": [
         {"text": "哦，又出新了，跟我没关系", "score": {"ie": 10, "tf": 20, "pj": 20, "as": 30}, "tag": "佛系派"},
         {"text": "看看介绍，有意思就试试", "score": {"ie": 40, "tf": 40, "pj": 40, "as": 40}, "tag": "观望派"},
         {"text": "立刻注册试用，测评一下好不好用", "score": {"ie": 60, "tf": 50, "pj": 70, "as": 50}, "tag": "尝鲜派"},
         {"text": "不仅试用，还要写一篇测评发朋友圈", "score": {"ie": 80, "tf": 40, "pj": 80, "as": 40}, "tag": "测评博主"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q13", "dimension": "problem_reframing", "category": "AI生活场景",
     "question": "你用AI做过最有创意的事情是？",
     "options": [
         {"text": "没做过什么特别的", "score": {"ie": 20, "tf": 20, "pj": 20, "as": 30}, "tag": "待开发"},
         {"text": "用AI生成过图片/音乐/视频", "score": {"ie": 50, "tf": 40, "pj": 50, "as": 60}, "tag": "创作入门"},
         {"text": "用AI帮朋友做过生日礼物/表白文案", "score": {"ie": 60, "tf": 30, "pj": 60, "as": 70}, "tag": "创意生活家"},
         {"text": "用AI做了一个让所有人都惊艳的作品", "score": {"ie": 70, "tf": 40, "pj": 80, "as": 80}, "tag": "创意大师"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q14", "dimension": "boundary_awareness", "category": "AI生活场景",
     "question": "你有没有发现过AI'一本正经胡说八道'（幻觉）？",
     "options": [
         {"text": "没有，AI说的我都信", "score": {"ie": 30, "tf": 10, "pj": 20, "as": 10}, "tag": "信任者"},
         {"text": "好像有过，但不确定", "score": {"ie": 40, "tf": 30, "pj": 40, "as": 40}, "tag": "模糊感知"},
         {"text": "发现过好几次，现在都会验证一下", "score": {"ie": 50, "tf": 60, "pj": 60, "as": 70}, "tag": "警惕派"},
         {"text": "经常发现，还能故意引导AI犯错来测试它", "score": {"ie": 50, "tf": 90, "pj": 70, "as": 90}, "tag": "幻觉猎人"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    # === 第四部分：AI哲学思考 ===
    {"id": "q15", "dimension": "ai_first_mindset", "category": "AI哲学思考",
     "question": "如果AI能完美替代你80%的工作，你会？",
     "options": [
         {"text": "有点慌，开始担心失业", "score": {"ie": 20, "tf": 30, "pj": 30, "as": 30}, "tag": "焦虑派"},
         {"text": "无所谓，AI替代不了那20%", "score": {"ie": 30, "tf": 40, "pj": 40, "as": 40}, "tag": "淡定派"},
         {"text": "太好了，终于有时间做想做的事", "score": {"ie": 50, "tf": 40, "pj": 50, "as": 50}, "tag": "乐观派"},
         {"text": "主动学习驾驭AI，让自己不可替代", "score": {"ie": 60, "tf": 70, "pj": 70, "as": 70}, "tag": "进化派"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q16", "dimension": "iteration_agility", "category": "AI哲学思考",
     "question": "你通常在什么时间段使用AI？",
     "options": [
         {"text": "只在工作时间用", "score": {"ie": 10, "tf": 40, "pj": 30, "as": 40}, "tag": "上班族"},
         {"text": "工作+偶尔下班后", "score": {"ie": 30, "tf": 50, "pj": 50, "as": 50}, "tag": "加班族"},
         {"text": "随时随地，有需求就用", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 50}, "tag": "全天候"},
         {"text": "凌晨2点还在和AI讨论人生哲学", "score": {"ie": 70, "tf": 40, "pj": 50, "as": 80}, "tag": "深夜AI玩家"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q17", "dimension": "deep_collaboration", "category": "AI哲学思考",
     "question": "你觉得5年后AI会变成什么样？",
     "options": [
         {"text": "跟现在差不多吧", "score": {"ie": 10, "tf": 20, "pj": 20, "as": 30}, "tag": "保守派"},
         {"text": "会比现在好用很多", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "谨慎乐观"},
         {"text": "会深刻改变每个人的工作和生活", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 60}, "tag": "变革派"},
         {"text": "AI将无处不在，人类与AI深度融合", "score": {"ie": 70, "tf": 60, "pj": 70, "as": 70}, "tag": "未来主义者"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q18", "dimension": "boundary_awareness", "category": "AI哲学思考",
     "question": "你有没有因为使用AI而产生过'原来还可以这样'的顿悟时刻？",
     "options": [
         {"text": "没有过", "score": {"ie": 10, "tf": 20, "pj": 20, "as": 20}, "tag": "未觉醒"},
         {"text": "有过一两次", "score": {"ie": 40, "tf": 40, "pj": 40, "as": 50}, "tag": "初步觉醒"},
         {"text": "有很多次，每次都让我对AI有了新认识", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 70}, "tag": "持续觉醒"},
         {"text": "经常有，我已经习惯了被AI惊艳", "score": {"ie": 60, "tf": 50, "pj": 70, "as": 80}, "tag": "见怪不怪"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q19", "dimension": "problem_reframing", "category": "AI哲学思考",
     "question": "如果让你用一句话描述AI对你的影响，你会说？",
     "options": [
         {"text": "AI就是一个好用的工具", "score": {"ie": 20, "tf": 30, "pj": 30, "as": 30}, "tag": "工具论"},
         {"text": "AI让我的工作效率提升了不少", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "效率论"},
         {"text": "AI改变了我思考问题的方式", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 70}, "tag": "思维变革论"},
         {"text": "AI重新定义了我对'能力'的理解", "score": {"ie": 70, "tf": 60, "pj": 70, "as": 80}, "tag": "认知革命论"},
         {"text": "其他", "score": 0, "tag": "自定义"}]},
    {"id": "q20", "dimension": "learning_mode", "category": "AI哲学思考",
     "question": "如果给AI打分（满分10分），你会打几分？",
     "options": [
         {"text": "5分以下，还有很多不足", "score": {"ie": 20, "tf": 30, "pj": 30, "as": 40}, "tag": "严格评委"},
         {"text": "6-7分，还不错但需要改进", "score": {"ie": 40, "tf": 40, "pj": 50, "as": 50}, "tag": "客观评委"},
         {"text": "8-9分，已经非常强大了", "score": {"ie": 60, "tf": 50, "pj": 60, "as": 60}, "tag": "粉丝评委"},
         {"text": "10分满分！AI是人类的未来", "score": {"ie": 70, "tf": 40, "pj": 70, "as": 50}, "tag": "超级粉丝"},
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
    # 8维度权重：ai_first_mindset, prompt_engineering, deep_collaboration, problem_reframing, learning_mode, iteration_agility, boundary_awareness, critical_validation
    weights = [1.0, 1.0, 1.0, 1.0, 0.8, 0.8, 0.8, 0.9]
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
            
        weight = weights[i] if i < len(weights) else 1.0
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
            "score": {"ie": 40, "tf": 40, "pj": 40, "as": 40},  # 默认中等偏低的分数
            "analysis": "无法进行AI分析，采用默认评分"
        }
    
    # 构建分析prompt
    prompt = f"""
请分析用户对以下问题的回答，评估其AI使用能力和意识：

问题：{question_text}
用户回答：{user_answer}

请从以下四个维度评估（每项0-100分）：
1. ie（内向/外向）：AI使用的社交性和分享程度，高分偏E外向
2. tf（技术/创意）：AI使用的技术深度，高分偏T技术
3. pj（实践/战略）：AI使用的行动力，高分偏J战略
4. as（分析/感性）：AI使用的理性程度，高分偏A分析

请以JSON格式返回：
{{"ie": 分数, "tf": 分数, "pj": 分数, "as": 分数, "analysis": "简短分析说明"}}
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
            ie_score = min(100, max(0, int(result.get("ie", 40))))
            tf_score = min(100, max(0, int(result.get("tf", 40))))
            pj_score = min(100, max(0, int(result.get("pj", 40))))
            as_score = min(100, max(0, int(result.get("as", 40))))
            return {
                "score": {"ie": ie_score, "tf": tf_score, "pj": pj_score, "as": as_score},
                "analysis": result.get("analysis", "")
            }
    except Exception as e:
        pass
    
    return {
        "score": {"ie": 40, "tf": 40, "pj": 40, "as": 40},
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
    /* Fun/Personal version styles - 极简奢华风格 */
    .fun-header { display:none; } /* 不再使用 */
    .quiz-card { background:transparent; box-shadow:none; border:none; padding:0; }
    .result-hero { text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #1d1d1f 0%, #424245 100%); border-radius: 24px; color: white; margin: 2rem 0; }
    .result-emoji { font-size: 5rem; margin-bottom: 1rem; }
    .result-title { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.5rem; }
    .result-score { font-size: 4rem; font-weight: 700; margin: 1.5rem 0; letter-spacing: -0.02em; }
    .dimension-bar { height: 6px; background: #e5e5e7; border-radius: 3px; overflow: hidden; margin: 0.5rem 0; }
    .dimension-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
    .share-card { background: #ffffff; border-radius: 16px; padding: 2rem; text-align: center; border: 1px solid #e5e5e7; }
    .mode-card { background: white; border-radius: 16px; padding: 2rem; text-align: center; border: 1px solid #e5e5e7; cursor: pointer; transition: all 0.3s; }
    .mode-card:hover { border-color: #007AFF; transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.08); }
    .mode-card.active { border-color: #007AFF; background: #f5f5f7; }
    /* 极简风格滚动条 */
    .minimal-scroll::-webkit-scrollbar { height: 4px; }
    .minimal-scroll::-webkit-scrollbar-track { background: #f5f5f7; }
    .minimal-scroll::-webkit-scrollbar-thumb { background: #d2d2d7; border-radius: 2px; }
    /* 极简按钮样式 */
    .minimal-btn { background: #007AFF; color: white; border: none; border-radius: 12px; padding: 1rem 2rem; font-size: 1rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
    .minimal-btn:hover { background: #0056CC; transform: translateY(-1px); }
    /* 极简选项卡片 */
    .minimal-option { padding: 1rem 1.25rem; background: #f5f5f7; border-radius: 12px; margin: 0.5rem 0; border: 2px solid transparent; transition: all 0.2s; cursor: pointer; }
    .minimal-option:hover { background: #e8e8ed; }
    .minimal-option.selected { background: #e8f2ff; border-color: #007AFF; }
    /* 极简问题卡片 */
    .minimal-question { background: #ffffff; border-radius: 20px; padding: 2rem; margin: 1.5rem 0; border: 1px solid #e5e5e7; }
    /* 极简人格卡片 */
    .minimal-personality { flex: 0 0 auto; width: 120px; padding: 1.5rem 1rem; background: #ffffff; border-radius: 20px; border: 1px solid #e5e5e7; text-align: center; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; }
    .minimal-personality:hover { border-color: #007AFF; box-shadow: 0 4px 20px rgba(0, 122, 255, 0.15); transform: translateY(-4px); }
    /* 极简进度条 */
    .minimal-progress { margin: 2rem 0 3rem; }
    .minimal-progress-label { display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; color: #86868b; margin-bottom: 0.75rem; }
    .minimal-progress-bar { height: 2px; background: #e5e5e7; border-radius: 1px; overflow: hidden; }
    .minimal-progress-fill { height: 100%; background: #007AFF; border-radius: 1px; transition: width 0.3s; }
</style>""", unsafe_allow_html=True)

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
        
        # 候选人列表 - 人才库管理
        st.subheader("📚 人才库管理")
        
        # 搜索和筛选区域
        with st.expander("🔍 搜索与筛选", expanded=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                search = st.text_input("搜索姓名/职位/邮箱", "")
            with col2:
                level_filter = st.multiselect("等级筛选", ["L0", "L1", "L2", "L3"], default=[])
            with col3:
                stage_filter = st.multiselect("面试阶段", [s["name"] for s in INTERVIEW_STAGES], default=[])
            with col4:
                tag_filter = st.multiselect("标签筛选", TALENT_TAGS, default=[])
        
        # 统计信息
        total_count = len(candidates)
        st.caption(f"共 {total_count} 位候选人")
        
        # 筛选逻辑
        filtered_candidates = {}
        for cid, candidate in candidates.items():
            # 姓名搜索
            if search and search.lower() not in candidate.get("name", "").lower():
                # 也搜索职位和邮箱
                if search.lower() not in candidate.get("position", "").lower():
                    if search.lower() not in candidate.get("email", "").lower():
                        continue
            # 等级筛选
            if level_filter and candidate.get("level") not in level_filter:
                continue
            # 面试阶段筛选
            if stage_filter:
                candidate_stage = candidate.get("interview_stage", "新简历")
                if candidate_stage not in stage_filter:
                    continue
            # 标签筛选
            if tag_filter:
                candidate_tags = candidate.get("tags", [])
                if not any(tag in candidate_tags for tag in tag_filter):
                    continue
            filtered_candidates[cid] = candidate
        
        # 显示筛选结果数量
        if len(filtered_candidates) != total_count:
            st.caption(f"筛选结果: {len(filtered_candidates)} 位候选人")
        
        # 候选人列表展示
        for cid, candidate in filtered_candidates.items():
            with st.container():
                # 第一行：主要信息
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1.5, 1])
                
                with col1:
                    st.write(f"**{candidate.get('name', '未命名')}**")
                    st.caption(f"📧 {candidate.get('email', '无邮箱')} | 📅 {candidate.get('eval_date', '未知')}")
                
                with col2:
                    level = candidate.get("level", "L0")
                    color = get_level_color(level)
                    st.markdown(f'<span class="level-badge" style="background-color: {color}">{LEVEL_DEFINITIONS[level]["name"]}</span>', unsafe_allow_html=True)
                
                with col3:
                    st.write(f"**{candidate.get('total_score', 0)}分**")
                
                with col4:
                    # 面试阶段选择
                    current_stage = candidate.get("interview_stage", "新简历")
                    stage_names = [s["name"] for s in INTERVIEW_STAGES]
                    new_stage = st.selectbox(
                        "阶段",
                        stage_names,
                        index=stage_names.index(current_stage) if current_stage in stage_names else 0,
                        key=f"stage_{cid}",
                        label_visibility="collapsed"
                    )
                    if new_stage != current_stage:
                        st.session_state.candidates[cid]["interview_stage"] = new_stage
                        save_candidates(st.session_state.candidates)
                        st.rerun()
                
                with col5:
                    if st.button("查看详情", key=f"view_{cid}", type="primary"):
                        st.session_state.current_candidate = cid
                        st.rerun()
                
                # 第二行：职位和标签
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.caption(f"💼 {candidate.get('position', '未指定职位')}")
                with col2:
                    # 显示已有标签
                    current_tags = candidate.get("tags", [])
                    if current_tags:
                        tags_html = " ".join([f'<span style="background:#E8F4FD;color:#007AFF;padding:2px 8px;border-radius:12px;font-size:0.7rem;margin-right:4px;">{tag}</span>' for tag in current_tags])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    # 添加标签按钮
                    remaining_tags = [t for t in TALENT_TAGS if t not in current_tags]
                    if remaining_tags:
                        new_tag = st.selectbox(
                            "+ 标签",
                            [""] + remaining_tags,
                            key=f"tag_select_{cid}",
                            label_visibility="collapsed"
                        )
                        if new_tag:
                            if "tags" not in st.session_state.candidates[cid]:
                                st.session_state.candidates[cid]["tags"] = []
                            st.session_state.candidates[cid]["tags"].append(new_tag)
                            save_candidates(st.session_state.candidates)
                            st.rerun()
                
                st.divider()
    
    # 候选人详情弹窗
    if st.session_state.current_candidate:
        cid = st.session_state.current_candidate
        if cid in st.session_state.candidates:
            c = st.session_state.candidates[cid]
            
            # 数据兼容性处理：确保旧数据（6维度）也能显示8维度
            if 'dimensions' in c:
                dims = c['dimensions']
                # 如果缺少新维度，添加默认值
                if 'prompt_engineering' not in dims:
                    dims['prompt_engineering'] = {"score": 50, "notes": "（此维度为新增，原数据未包含）"}
                if 'critical_validation' not in dims:
                    dims['critical_validation'] = {"score": 50, "notes": "（此维度为新增，原数据未包含）"}
                c['dimensions'] = dims
            
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
            
            # 雷达图 - 使用8维度
            import plotly.graph_objects as go
            categories = [info['name'] for info in AI_NATIVE_DIMENSIONS.values()]
            values = [c.get('dimensions', {}).get(dim_key, {}).get('score', 0) for dim_key in AI_NATIVE_DIMENSIONS.keys()]
            values.append(values[0])
            fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories + [categories[0]], fill='toself', name=c['name']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 岗位匹配度分析
            st.subheader("🎯 岗位匹配度分析")
            candidate_position = c.get('position', '其他')
            
            # 找到最匹配的岗位画像
            matched_profile = TALENT_PROFILES.get(candidate_position, TALENT_PROFILES.get('其他'))
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.info(f"**岗位画像:** {matched_profile['name']}\n\n{matched_profile['description']}")
            
            with col2:
                # 计算加权匹配分数
                dimension_scores = c.get('dimensions', {})
                weights = matched_profile['dimension_weights']
                weighted_sum = 0
                total_weight = 0
                for dim_key, weight in weights.items():
                    score = dimension_scores.get(dim_key, {}).get('score', 50)
                    weighted_sum += score * weight
                    total_weight += weight
                match_score = round(weighted_sum / total_weight, 1)
                
                # 匹配度评级
                if match_score >= 80:
                    match_level = "🌟 优秀匹配"
                    match_color = "#10B981"
                elif match_score >= 60:
                    match_level = "✅ 良好匹配"
                    match_color = "#3B82F6"
                elif match_score >= 40:
                    match_level = "⚠️ 基本匹配"
                    match_color = "#F59E0B"
                else:
                    match_level = "❌ 匹配度较低"
                    match_color = "#EF4444"
                
                st.markdown(f"""
                <div style="text-align:center;padding:1rem;background:{match_color}20;border-radius:12px;border:2px solid {match_color}">
                    <div style="font-size:2.5rem;font-weight:bold;color:{match_color}">{match_score}分</div>
                    <div style="font-size:1rem;color:{match_color}">{match_level}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 关键维度分析
            st.write("**关键维度表现:**")
            key_dims = matched_profile['key_dimensions']
            for dim_key in key_dims:
                dim_info = AI_NATIVE_DIMENSIONS.get(dim_key, {})
                score = dimension_scores.get(dim_key, {}).get('score', 0)
                # 进度条样式
                bar_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
                st.markdown(f"""
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="font-weight:500;">{dim_info.get('name', dim_key)}</span>
                        <span style="color:{bar_color};font-weight:bold;">{score}分</span>
                    </div>
                    <div style="background:#E5E7EB;border-radius:4px;height:8px;overflow:hidden;">
                        <div style="background:{bar_color};height:100%;width:{score}%;transition:width 0.3s;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 面试建议
            st.write("**面试重点:**")
            for focus in matched_profile['interview_focus']:
                st.caption(f"• {focus}")
            
            # 简历预览
            resume_path = c.get('resume_path', '')
            resume_mime = c.get('resume_mime', '')
            if resume_path and os.path.exists(resume_path):
                st.markdown("---")
                st.subheader("📄 简历预览")
                try:
                    if resume_mime and resume_mime.startswith('image/'):
                        st.image(resume_path, caption=c.get('resume_filename', '简历'), use_container_width=True)
                    elif resume_mime == 'application/pdf':
                        # PDF渲染为图片预览
                        try:
                            import fitz
                            pdf_doc = fitz.open(resume_path)
                            
                            for page_num in range(len(pdf_doc)):
                                page = pdf_doc[page_num]
                                mat = fitz.Matrix(2, 2)
                                pix = page.get_pixmap(matrix=mat)
                                img_bytes = pix.tobytes("png")
                                st.image(img_bytes, caption=f"第 {page_num + 1} / {len(pdf_doc)} 页", use_container_width=True)
                            
                            pdf_doc.close()
                        except ImportError:
                            st.warning("请安装 PyMuPDF 来预览PDF: pip install PyMuPDF")
                        
                        with open(resume_path, 'rb') as f:
                            st.download_button(
                                "下载简历",
                                data=f.read(),
                                file_name=c.get('resume_filename', 'resume.pdf'),
                                mime='application/pdf'
                            )
                except Exception as e:
                    st.warning(f"简历预览失败: {e}")
            
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
            
            # 协作备注区域
            st.markdown("---")
            st.subheader("💬 协作备注")
            
            # 显示历史备注
            comments = c.get('comments', [])
            if comments:
                for i, comment in enumerate(comments):
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            st.caption(f"{comment.get('time', '未知时间')}")
                            st.caption(f"👤 {comment.get('author', '匿名')}")
                        with col2:
                            st.info(comment.get('content', ''))
                        # 删除备注按钮
                        if st.button("🗑️", key=f"del_comment_{cid}_{i}"):
                            st.session_state.candidates[cid]['comments'].pop(i)
                            save_candidates(st.session_state.candidates)
                            st.rerun()
            else:
                st.caption("暂无备注，添加第一条协作备注吧~")
            
            # 添加新备注
            with st.expander("➕ 添加备注"):
                author = st.text_input("您的姓名", value="HR", key=f"comment_author_{cid}")
                new_comment = st.text_area("备注内容", placeholder="输入您的评价或面试反馈...", key=f"comment_content_{cid}")
                if st.button("提交备注", key=f"submit_comment_{cid}"):
                    if new_comment.strip():
                        from datetime import datetime
                        comment_data = {
                            "author": author,
                            "content": new_comment.strip(),
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        if "comments" not in st.session_state.candidates[cid]:
                            st.session_state.candidates[cid]["comments"] = []
                        st.session_state.candidates[cid]["comments"].append(comment_data)
                        save_candidates(st.session_state.candidates)
                        st.success("备注添加成功！")
                        st.rerun()
            
            # 操作按钮
            st.markdown("---")
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
            
            # 数据兼容性处理：确保旧数据（6维度）也能编辑8维度
            if 'dimensions' in c:
                dims = c['dimensions']
                if 'prompt_engineering' not in dims:
                    dims['prompt_engineering'] = {"score": 50, "notes": ""}
                if 'critical_validation' not in dims:
                    dims['critical_validation'] = {"score": 50, "notes": ""}
                c['dimensions'] = dims
            
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
            
            # 八维评分编辑
            st.write("**AI Native 八维评分**")
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
    
    # 上传区域 - 支持PDF、图片、DOCX、TXT
    resume_file = st.file_uploader(
        "上传简历 (PDF / 图片 / DOCX / TXT)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="resume_upload"
    )
    
    resume_bytes = None
    resume_filename = None
    resume_mime = None
    
    if resume_file:
        st.success(f"已上传: {resume_file.name}")
        resume_bytes = resume_file.getvalue()
        resume_filename = resume_file.name
        resume_mime = resume_file.type
        
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
            elif resume_file.type and resume_file.type.startswith("image/"):
                # 图片简历 - 提取不到文字，但可以预览
                resume_text = "[图片简历 - 请查看预览]"
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
    
    # 简历预览 - 支持PDF和图片
    if resume_file:
        st.markdown("---")
        st.subheader("📄 简历预览")
        
        if resume_mime and resume_mime.startswith("image/"):
            # 图片简历直接显示
            st.image(resume_bytes, caption=resume_filename, use_container_width=True)
        elif resume_mime == "application/pdf":
            # PDF简历 - 渲染为图片预览（更兼容）
            try:
                import fitz  # PyMuPDF
                from io import BytesIO
                
                pdf_doc = fitz.open(stream=resume_bytes, filetype="pdf")
                
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    # 渲染为图片 (2x分辨率更清晰)
                    mat = fitz.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=mat)
                    img_bytes = pix.tobytes("png")
                    st.image(img_bytes, caption=f"第 {page_num + 1} / {len(pdf_doc)} 页", use_container_width=True)
                
                pdf_doc.close()
            except ImportError:
                st.warning("请安装 PyMuPDF 来预览PDF: pip install PyMuPDF")
                st.info("暂时无法预览PDF，但可以下载后查看")
            
            # 下载按钮
            st.download_button(
                "下载简历 PDF",
                data=resume_bytes,
                file_name=resume_filename,
                mime="application/pdf"
            )
        elif resume_text and resume_text not in ["[PDF文件内容]", "[文档内容]", "[图片简历 - 请查看预览]"]:
            # 纯文本简历
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
    checklist_items_keys = ["ai_first_response", "own_prompt_library", "own_methodology", "workflow_reformed", "specific_complaints", "fact_checking_habit", "ai_anxiety"]
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
            
            # 保存简历原文件到磁盘
            resume_path = ""
            if resume_bytes and resume_filename:
                resume_path = str(RESUMES_DIR / f"{candidate_id}_{resume_filename}")
                with open(resume_path, "wb") as f:
                    f.write(resume_bytes)
            
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
                "ai_analysis": ai_analysis_to_save,
                "resume_path": resume_path,
                "resume_filename": resume_filename or "",
                "resume_mime": resume_mime or ""
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
    """根据各维度分数判定16种AI人格画像
    
    avg_scores 包含4个维度: {"ie": x, "tf": x, "pj": x, "as": x}
    每个维度 0-100 分，>= 50 为高方向，< 50 为低方向
    """
    # 直接从 avg_scores 读取4个维度分数
    ie_score = avg_scores.get("ie", 50)
    tf_score = avg_scores.get("tf", 50)
    pj_score = avg_scores.get("pj", 50)
    as_score = avg_scores.get("as", 50)
    
    # 判定每个维度
    ie = "E" if ie_score >= 50 else "I"
    tf = "T" if tf_score >= 50 else "F"
    pj = "J" if pj_score >= 50 else "P"
    a_s = "A" if as_score >= 50 else "S"
    
    personality_code = f"{ie}{tf}{pj}{a_s}"
    
    # 确保是有效的16种画像之一
    valid_types = [
        "ITPA", "ITPS", "ITJA", "ITJS",
        "IFPA", "IFPS", "IFJA", "IFJS",
        "ETPA", "ETPS", "ETJA", "ETJS",
        "EFPA", "EFPS", "EFJA", "EFJS"
    ]
    
    if personality_code in valid_types:
        return personality_code
    
    # fallback
    return "ITPA"


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
        
        # 极简奢华风格欢迎页面
        st.markdown('''
        <div style="text-align:center;padding:6rem 2rem;min-height:80vh;display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:1.5rem;">AI Personality Assessment</div>
            <h1 style="font-size:3.5rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.03em;line-height:1.1;margin-bottom:1rem;">AI 人格进化论</h1>
            <p style="font-size:1.125rem;color:#86868b;max-width:500px;margin:0 auto 3rem;">20道趣味场景题，发现你的AI使用风格</p>
            <div style="display:flex;gap:2rem;justify-content:center;margin-bottom:4rem;font-size:0.875rem;color:#86868b;">
                <span>20题趣味测试</span>
                <span style="width:1px;background:#d2d2d7;"></span>
                <span>16种人格类型</span>
                <span style="width:1px;background:#d2d2d7;"></span>
                <span>约5分钟</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 16种人格预览 - 一行4个网格
        personalities = list(AI_PERSONALITIES.items())
        for i in range(0, len(personalities), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(personalities):
                    key, p = personalities[i + j]
                    # 读取专业SVG图标
                    icon_path = f"static/personality_icons/{key}.svg"
                    icon_html = ""
                    try:
                        with open(icon_path, 'r', encoding='utf-8') as f:
                            svg_content = f.read()
                        svg_content = svg_content.replace('<svg', '<svg width="36" height="36" style="display:block;margin:0 auto;"')
                        icon_html = svg_content
                    except:
                        icon_html = f'<div style="font-size:1.5rem;text-align:center;">{p.get("emoji", "🤖")}</div>'
                    
                    with cols[j]:
                        # 构建hover提示内容
                        tooltip_content = p.get('desc', '')
                        tooltip_tools = ' · '.join(p.get('tools', [])[:4])
                        card_id = f"personality_card_{key}"
                        
                        # 使用纯CSS实现hover效果（更可靠）
                        st.markdown(f'''
                        <style>
                        #{card_id} {{
                            text-align: center;
                            padding: 1.25rem 0.5rem;
                            background: #ffffff;
                            border-radius: 16px;
                            border: 1px solid #e5e5e7;
                            transition: all 0.3s;
                            position: relative;
                            cursor: help;
                        }}
                        #{card_id}:hover {{
                            border-color: #007AFF;
                            box-shadow: 0 4px 20px rgba(0,122,255,0.15);
                        }}
                        #{card_id} .tooltip {{
                            display: none;
                            position: absolute;
                            bottom: calc(100% + 8px);
                            left: 50%;
                            transform: translateX(-50%);
                            width: 240px;
                            background: rgba(29,29,31,0.98);
                            color: #ffffff;
                            padding: 14px;
                            border-radius: 12px;
                            font-size: 0.75rem;
                            line-height: 1.5;
                            z-index: 1000;
                            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                            text-align: left;
                        }}
                        #{card_id}:hover .tooltip {{
                            display: block;
                        }}
                        #{card_id} .tooltip::after {{
                            content: '';
                            position: absolute;
                            top: 100%;
                            left: 50%;
                            transform: translateX(-50%);
                            border: 8px solid transparent;
                            border-top-color: rgba(29,29,31,0.98);
                        }}
                        #{card_id} .tooltip-trait {{
                            font-weight: 600;
                            margin-bottom: 8px;
                            color: #007AFF;
                            font-size: 0.8rem;
                        }}
                        #{card_id} .tooltip-desc {{
                            margin-bottom: 10px;
                            opacity: 0.95;
                        }}
                        #{card_id} .tooltip-tools {{
                            border-top: 1px solid rgba(255,255,255,0.2);
                            padding-top: 8px;
                            font-size: 0.7rem;
                            opacity: 0.8;
                        }}
                        </style>
                        <div id="{card_id}">
                            <div style="margin-bottom:0.5rem;">{icon_html}</div>
                            <div style="font-size:0.8rem;font-weight:600;color:#1d1d1f;">{p["name"]}</div>
                            <div class="tooltip">
                                <div class="tooltip-trait">{p.get('trait', '')}</div>
                                <div class="tooltip-desc">{tooltip_content}</div>
                                <div class="tooltip-tools">常用: {tooltip_tools}</div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
        
        st.markdown('<div style="height:3rem;"></div>', unsafe_allow_html=True)

        # 极简开始按钮
        if st.button("开始测试 →", type="primary", use_container_width=True):
            st.session_state.personal_step = 1
            st.rerun()
    
    # ===== 测试阶段 =====
    elif st.session_state.personal_step in [1, 2, 3, 4]:
        step = st.session_state.personal_step
        categories = ["AI本能反应", "AI社交风格", "AI生活场景", "AI哲学思考"]
        category = categories[step - 1]
        
        # 添加锚点用于滚动定位
        st.markdown(f'<div id="part_{step}_start"></div>', unsafe_allow_html=True)
        
        # 检查是否需要滚动到该部分顶部
        if st.session_state.get('scroll_to_part_top', False):
            st.session_state.scroll_to_part_top = False
            st.markdown(f"""
            <script>
                document.getElementById('part_{step}_start').scrollIntoView({{behavior: 'smooth', block: 'start'}});
            </script>
            """, unsafe_allow_html=True)
        
        # 极简进度条
        progress = step / 5
        st.markdown(f'''
        <div class="minimal-progress">
            <div class="minimal-progress-label">
                <span>第{step}/4部分 · {category}</span>
                <span>{progress*100:.0f}%</span>
            </div>
            <div class="minimal-progress-bar">
                <div class="minimal-progress-fill" style="width:{progress*100}%;"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 当前阶段的题目
        step_questions = [q for q in FUN_QUESTIONS if q.get("category") == category]
        
        # 添加全局样式
        st.markdown("""
        <style>
        /* 简洁问题卡片 */
        .simple-question-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #f0f0f0;
        }
        .simple-question-text {
            font-size: 1.1rem;
            font-weight: 500;
            color: #1d1d1f;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        /* 选项按钮组 */
        .option-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .option-btn {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid #e5e5e7;
            border-radius: 12px;
            background: #ffffff;
            font-size: 0.95rem;
            color: #333333;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }
        .option-btn:hover {
            border-color: #999999;
            background: #fafafa;
        }
        .option-btn.selected {
            border-color: #1d1d1f;
            background: #1d1d1f;
            color: #ffffff;
        }
        /* 选项内文字 */
        .option-label {
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        .option-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #d1d1d6;
            flex-shrink: 0;
            margin-top: 6px;
            transition: all 0.2s ease;
        }
        .option-btn.selected .option-dot {
            background: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for q in step_questions:
            # 获取当前保存的答案
            current_answer = st.session_state.personal_answers.get(q["id"])
            current_selected = current_answer.get("text") if current_answer else None
            
            # 极简问题卡片
            st.markdown(f'''
            <div class="simple-question-card">
                <div class="simple-question-text">{q["question"]}</div>
                <div class="option-group">
            ''', unsafe_allow_html=True)
            
            # 使用columns让选项水平排列（两列）
            options = q["options"]
            option_cols = st.columns(len(options))
            
            for idx, (col, o) in enumerate(zip(option_cols, options)):
                with col:
                    is_selected = current_selected == o["text"]
                    
                    # 自定义选项按钮
                    btn_style = "option-btn selected" if is_selected else "option-btn"
                    btn_id = f"opt_{q['id']}_{idx}"
                    
                    st.markdown(f'''
                    <div class="{btn_style}" id="{btn_id}" onclick="this.classList.toggle('selected'); window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{o["text"]}', key: '{q["id"]}'}}, '*');">
                        <div class="option-label">
                            <div class="option-dot"></div>
                            <div>{o["text"]}</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
            
            # 隐藏的radio用于实际状态管理
            radio_options = [o["text"] for o in q["options"]]
            current_index = None
            if current_answer:
                for idx, o in enumerate(q["options"]):
                    if o["text"] == current_answer.get("text"):
                        current_index = idx
                        break
            
            selected = st.radio(
                " ",
                options=radio_options,
                key=f"q_{q['id']}",
                index=current_index,
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
                        
                        if other_text:
                            st.session_state.personal_other_answers[q["id"]] = other_text
                        elif other_text == "" and q["id"] in st.session_state.personal_other_answers:
                            del st.session_state.personal_other_answers[q["id"]]
                    break
        
        # 极简导航按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 上一部分"):
                st.session_state.personal_step = max(0, step - 1)
                st.rerun()
        with col2:
            btn_text = "下一部分 →" if step < 4 else "选择工具 →"
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
                    # 标记需要滚动到下一部分的第一题
                    st.session_state.scroll_to_part_top = True
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
                        # 读取图标（支持SVG和PNG）
                        icon_path = tool.get('icon', '')
                        icon_html = ""
                        if icon_path:
                            try:
                                if icon_path.endswith('.svg'):
                                    with open(icon_path, 'r', encoding='utf-8') as f:
                                        svg_content = f.read()
                                    svg_content = svg_content.replace('<svg', '<svg width="32" height="32" style="filter:drop-shadow(0 2px 4px rgba(0,0,0,0.1))"')
                                    icon_html = svg_content
                                elif icon_path.endswith('.png'):
                                    import base64
                                    with open(icon_path, 'rb') as f:
                                        img_data = base64.b64encode(f.read()).decode()
                                    icon_html = f'<img src="data:image/png;base64,{img_data}" width="32" height="32" style="filter:drop-shadow(0 2px 4px rgba(0,0,0,0.1))"/>'
                            except Exception as e:
                                icon_html = f'<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🤖</div>'
                        else:
                            icon_html = f'<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🤖</div>'
                        
                        # 检查是否已选择
                        is_checked = tool['name'] in st.session_state.personal_tools
                        
                        # 生成唯一key
                        tool_key = f"tool_{tool['name']}"
                        
                        # 卡片样式 - 选中时边框变蓝，显示勾选标记
                        card_style = '''
                            background: #ffffff;
                            border-radius: 16px;
                            padding: 1.25rem;
                            margin: 0.5rem 0;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                            border: 2px solid ''' + ('#007AFF' if is_checked else '#e5e5e7') + ''';
                            transition: all 0.3s ease;
                            position: relative;
                            min-height: 90px;
                        '''
                        
                        # 勾选标记（选中时显示在左下角）
                        checkmark_html = '''
                        <div style="position:absolute;bottom:10px;left:10px;width:22px;height:22px;background:#007AFF;border-radius:6px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,122,255,0.4);">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                <path d="M3 7L6 10L11 4" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        ''' if is_checked else ''
                        
                        # 渲染卡片（可点击）
                        st.markdown(f'''
                        <div style="{card_style}" onclick="document.querySelector('input[data-testid=\\'stCheckbox\\'][name=\\'{tool_key}\\']').click();">
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                                {icon_html}
                                <div style="font-size:1rem;font-weight:600;color:#1d1d1f;line-height:1.2;">{tool["name"]}</div>
                            </div>
                            <div style="font-size:0.75rem;color:#86868b;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;padding-right:30px;">{tool.get('desc', '')}</div>
                            <div style="font-size:0.7rem;color:#86868b;margin-top:6px;opacity:0.8;">{tool.get('company', '')}</div>
                            {checkmark_html}
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # 隐藏的checkbox用于状态管理
                        checked = st.checkbox(
                            "✓",
                            value=is_checked,
                            key=tool_key,
                            label_visibility="collapsed"
                        )
                        
                        # 更新选择状态
                        if checked != is_checked:
                            if checked:
                                st.session_state.personal_tools.append(tool['name'])
                            else:
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
        # 极简风格标题
        st.markdown('''
        <div style="text-align:center;padding:3rem 2rem;margin-bottom:2rem;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">Step 5</div>
            <h2 style="font-size:2rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;margin-bottom:0.5rem;">Prompt挑战</h2>
            <p style="font-size:1rem;color:#86868b;max-width:500px;margin:0 auto;">测试你的Prompt Engineering技能</p>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化Prompt挑战分数
        if 'prompt_challenge_score' not in st.session_state:
            st.session_state.prompt_challenge_score = 0

        for challenge in PROMPT_CHALLENGES:
            # 极简风格挑战卡片
            st.markdown(f'''
            <div class="minimal-question">
                <div style="font-size:1rem;font-weight:600;color:#1d1d1f;margin-bottom:0.5rem;">{challenge["title"]} <span style="color:#007AFF;font-weight:500;">+{challenge["points"]}分</span></div>
                <div style="font-size:0.875rem;color:#86868b;margin-bottom:1rem;">{challenge["desc"]}</div>
                <div style="font-size:0.9375rem;color:#1d1d1f;margin-bottom:1.5rem;">{challenge["task"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 用户输入自己的Prompt
            user_prompt = st.text_area(
                "写下你的Prompt：",
                key=f"prompt_input_{challenge['id']}",
                placeholder="发挥你的创意，写下你的Prompt..."
            )

            if user_prompt:
                # 根据Prompt长度和质量给予反馈
                word_count = len(user_prompt)
                if word_count >= 30:
                    st.success(f"不错！你的Prompt很详细，可以获得+{challenge['points']}分！")
                    if f"completed_{challenge['id']}" not in st.session_state:
                        st.session_state.prompt_challenge_score += challenge['points']
                        st.session_state[f"completed_{challenge['id']}"] = True
                elif word_count >= 15:
                    st.info("不错的开始！试着添加更多细节和约束条件~")
                else:
                    st.warning("试着写得更详细一些，比如加入背景、角色、输出格式等~")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 返回工具选择"):
                st.session_state.personal_step = 5
                st.rerun()
        with col2:
            if st.button("继续 →", type="primary"):
                st.session_state.personal_step = 7
                st.rerun()

    # ===== Step 7: AI对话模拟 =====
    elif st.session_state.personal_step == 7:
        # 极简风格标题
        st.markdown('''
        <div style="text-align:center;padding:3rem 2rem;margin-bottom:2rem;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">Step 6</div>
            <h2 style="font-size:2rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;margin-bottom:0.5rem;">AI对话模拟</h2>
            <p style="font-size:1rem;color:#86868b;max-width:500px;margin:0 auto;">选择最佳策略，学习如何与AI高效协作</p>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化对话模拟分数
        if 'chat_scenario_score' not in st.session_state:
            st.session_state.chat_scenario_score = 0
        if 'chat_scenario_count' not in st.session_state:
            st.session_state.chat_scenario_count = 0

        for scenario in AI_CHAT_SCENARIOS:
            # 极简场景卡片
            st.markdown(f'''
            <div class="minimal-question">
                <div style="font-size:1rem;font-weight:600;color:#1d1d1f;margin-bottom:0.5rem;">场景</div>
                <div style="font-size:1.125rem;color:#1d1d1f;">{scenario['scenario']}</div>
            </div>
            ''', unsafe_allow_html=True)

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

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 返回Prompt挑战"):
                st.session_state.personal_step = 6
                st.rerun()
        with col2:
            if st.button("继续 →", type="primary"):
                st.session_state.personal_step = 8
                st.rerun()

    # ===== Step 8: AI知识问答 =====
    elif st.session_state.personal_step == 8:
        # 极简风格标题
        st.markdown('''
        <div style="text-align:center;padding:3rem 2rem;margin-bottom:2rem;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">Step 7</div>
            <h2 style="font-size:2rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;margin-bottom:0.5rem;">AI知识问答</h2>
            <p style="font-size:1rem;color:#86868b;max-width:500px;margin:0 auto;">测试你的AI知识储备</p>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化知识问答分数
        if 'quiz_score' not in st.session_state:
            st.session_state.quiz_score = 0
        if 'quiz_count' not in st.session_state:
            st.session_state.quiz_count = 0

        for i, quiz in enumerate(AI_KNOWLEDGE_QUIZ):
            # 极简问题卡片
            st.markdown(f'''
            <div class="minimal-question">
                <div style="font-size:0.75rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.75rem;">问题 {i+1}/4</div>
                <div style="font-size:1.125rem;color:#1d1d1f;">{quiz['question']}</div>
            </div>
            ''', unsafe_allow_html=True)

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

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 返回AI对话模拟"):
                st.session_state.personal_step = 7
                st.rerun()
        with col2:
            if st.button("继续 →", type="primary"):
                st.session_state.personal_step = 9
                st.rerun()

    # ===== Step 9: 每日AI使用习惯测试 =====
    elif st.session_state.personal_step == 9:
        # 极简风格标题
        st.markdown('''
        <div style="text-align:center;padding:3rem 2rem;margin-bottom:2rem;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">Step 8</div>
            <h2 style="font-size:2rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;margin-bottom:0.5rem;">每日习惯测试</h2>
            <p style="font-size:1rem;color:#86868b;max-width:500px;margin:0 auto;">测测你的生活有多AI Native</p>
        </div>
        ''', unsafe_allow_html=True)

        # 初始化习惯测试答案
        if 'habit_answers' not in st.session_state:
            st.session_state.habit_answers = {}

        for habit in DAILY_AI_HABITS:
            # 极简问题卡片
            st.markdown(f'''
            <div class="minimal-question">
                <div style="font-size:1.125rem;color:#1d1d1f;">{habit["question"]}</div>
            </div>
            ''', unsafe_allow_html=True)

            selected = st.radio(
                "选择：",
                habit['options'],
                key=f"habit_{habit['id']}",
                label_visibility="collapsed"
            )

            st.session_state.habit_answers[habit['id']] = selected

        # 计算AI习惯得分
        ai_habit_count = sum(1 for ans in st.session_state.habit_answers.values()
                            if "AI" in ans or "问AI" in ans or "让AI" in ans)

        # 极简统计卡片
        st.markdown(f'''
        <div style="margin:2rem 0;padding:1.5rem;background:#f5f5f7;border-radius:16px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#1d1d1f;">{ai_habit_count}<span style="font-size:1rem;font-weight:400;">/{len(DAILY_AI_HABITS)}</span></div>
            <div style="font-size:0.875rem;color:#86868b;">个场景使用AI</div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← 返回知识问答"):
                st.session_state.personal_step = 8
                st.rerun()
        with col2:
            if st.button("查看结果 →", type="primary"):
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
        
        # 计算4个MBTI维度的分数
        dimension_scores_ie = []
        dimension_scores_tf = []
        dimension_scores_pj = []
        dimension_scores_as = []

        for q_id, ans in answers.items():
            score = ans.get("score", 0)
            if isinstance(score, dict):
                dimension_scores_ie.append(score.get("ie", 50))
                dimension_scores_tf.append(score.get("tf", 50))
                dimension_scores_pj.append(score.get("pj", 50))
                dimension_scores_as.append(score.get("as", 50))
            elif isinstance(score, (int, float)):
                # 兼容旧的数字格式
                dimension_scores_ie.append(score)
                dimension_scores_tf.append(score)
                dimension_scores_pj.append(score)
                dimension_scores_as.append(score)

        avg_ie = sum(dimension_scores_ie) / len(dimension_scores_ie) if dimension_scores_ie else 50
        avg_tf = sum(dimension_scores_tf) / len(dimension_scores_tf) if dimension_scores_tf else 50
        avg_pj = sum(dimension_scores_pj) / len(dimension_scores_pj) if dimension_scores_pj else 50
        avg_as = sum(dimension_scores_as) / len(dimension_scores_as) if dimension_scores_as else 50

        avg_scores = {
            "ie": avg_ie, "tf": avg_tf, "pj": avg_pj, "as": avg_as
        }

        # 总分 = 4个维度的加权平均
        total_score = round((avg_ie + avg_tf + avg_pj + avg_as) / 4, 1)
        level = calculate_level(total_score)
        fun_info = FUN_TITLES[level]

        # 判定AI人格画像
        personality = determine_ai_personality(avg_scores, answers)
        
        # 计算成就
        achievement_data = {
            "total_score": total_score,
            "tool_count": len(st.session_state.personal_tools),
        }
        for q_id, ans in answers.items():
            score_val = ans["score"]
            if isinstance(score_val, dict):
                avg_val = sum(score_val.values()) / len(score_val)
            else:
                avg_val = float(score_val) if isinstance(score_val, (int, float)) else 0
            achievement_data[f"{q_id}_score"] = avg_val
        
        unlocked = []
        for ach in ACHIEVEMENTS:
            try:
                if ach["condition"](achievement_data):
                    unlocked.append(ach)
            except:
                pass
        
        # ===== 结果展示 =====
        # 极简主结果卡片 - 深色背景突出主题
        st.markdown(f'''
        <div class="result-hero">
            <div class="result-emoji">{fun_info["emoji"]}</div>
            <h1 style="font-size:2.5rem;font-weight:700;margin-bottom:0.5rem;">{fun_info["title"]}</h1>
            <div style="font-size:1rem;opacity:0.8;margin:0.5rem 0 1.5rem;">{fun_info["tagline"]}</div>
            <div class="result-score">{total_score}<span style="font-size:1.5rem;font-weight:400;">分</span></div>
        </div>
        ''', unsafe_allow_html=True)
        
        # AI人格类型 - 极简玻璃质感卡片
        st.markdown('''
        <div style="margin:3rem 0;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">你的AI人格类型</div>
        ''', unsafe_allow_html=True)
        p = AI_PERSONALITIES[personality]
        # 读取专业SVG图标
        icon_path = f"static/personality_icons/{personality}.svg"
        try:
            with open(icon_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            svg_content = svg_content.replace('<svg', '<svg width="64" height="64" style="display:block;margin:0 auto;filter:drop-shadow(0 4px 8px rgba(0,0,0,0.2))"')
            icon_html = svg_content
        except:
            icon_html = f'<div style="font-size:4rem;text-align:center;">{p.get("emoji", "🤖")}</div>'
        
        st.markdown(f'''
        <div style="background:rgba(255,255,255,0.1);border-radius:20px;padding:2rem;margin:1rem 0;text-align:center;border:1px solid rgba(255,255,255,0.2);">
            <div style="margin-bottom:1rem;">{icon_html}</div>
            <div style="font-size:1.5rem;font-weight:600;color:#ffffff;">{personality} · {p['name']}</div>
            <div style="font-size:0.875rem;color:rgba(255,255,255,0.7);margin-top:0.5rem;">{p['trait']}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 人格描述
        st.markdown(f'''
        <div style="background:#ffffff;border-radius:20px;padding:2rem;margin:2rem 0;border:1px solid #e5e5e7;">
            <p style="font-size:1rem;color:#1d1d1f;line-height:1.8;margin-bottom:1.5rem;">{p['desc']}</p>
            <div style="background:#f5f5f7;padding:1rem;border-radius:12px;margin-bottom:1rem;">
                <div style="font-size:0.75rem;color:#86868b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">经典场景</div>
                <div style="font-size:0.9375rem;color:#1d1d1f;">{p['scene']}</div>
            </div>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
                <div style="font-size:0.75rem;color:#86868b;text-transform:uppercase;letter-spacing:0.1em;width:100%;margin-bottom:0.25rem;">常用工具</div>
                {''.join([f'<span style="background:#f5f5f7;padding:0.5rem 1rem;border-radius:8px;font-size:0.875rem;color:#1d1d1f;">{t}</span>' for t in p['tools']])}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 雷达图 - 透明背景适配深色区域
        import plotly.graph_objects as go
        dimension_labels = {
            "ie": "I内向 ← → E外向",
            "tf": "T技术 ← → F创意",
            "pj": "P实践 ← → J战略",
            "as": "A分析 ← → S感性"
        }
        categories = [dimension_labels[k] for k in ["ie", "tf", "pj", "as"]]
        values = [avg_scores.get(k, 50) for k in ["ie", "tf", "pj", "as"]]
        values.append(values[0])
        fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories + [categories[0]], fill='toself',
                                              fillcolor='rgba(0, 122, 255, 0.3)',
                                              line=dict(color='#007AFF')))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickcolor='rgba(255,255,255,0.3)', tickfont=dict(color='rgba(255,255,255,0.6)'))),
            showlegend=False, 
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 各维度进度条 - 极简风格
        st.markdown('''
        <div style="margin:2rem 0;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1.5rem;">各维度得分</div>
        ''', unsafe_allow_html=True)
        # 极简蓝调配色
        dimension_colors = ['#007AFF', '#7C3AED', '#059669', '#DC2626']
        dimension_names = {
            "ie": ("I内向", "E外向"),
            "tf": ("T技术", "F创意"),
            "pj": ("P实践", "J战略"),
            "as": ("A分析", "S感性")
        }
        for i, (dim_key, score) in enumerate(avg_scores.items()):
            color = dimension_colors[i]
            left_label, right_label = dimension_names[dim_key]
            st.markdown(f'''
            <div style="margin:0.75rem 0;">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
                    <span style="font-size:0.8rem;color:#86868b;">{left_label}</span>
                    <span style="font-size:0.8rem;color:#86868b;">{right_label}</span>
                </div>
                <div style="height:6px;background:#e5e5e7;border-radius:3px;position:relative;">
                    <div style="height:100%;width:50%;background:#e5e5e7;border-radius:3px;"></div>
                    <div style="position:absolute;top:-4px;left:{score}%;transform:translateX(-50%);width:14px;height:14px;background:{color};border-radius:50%;border:2px solid #ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.2);"></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # 成就解锁 - 极简风格
        st.markdown(f'''
        <div style="margin:3rem 0;">
            <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1.5rem;">成就解锁 ({len(unlocked)}/{len(ACHIEVEMENTS)})</div>
        </div>
        ''', unsafe_allow_html=True)
        if unlocked:
            ach_cols = st.columns(4)
            for i, ach in enumerate(unlocked):
                with ach_cols[i % 4]:
                    st.markdown(f'''
                    <div style="text-align:center;padding:1rem;background:#ffffff;border-radius:16px;border:1px solid #e5e5e7;margin:0.5rem 0;">
                        <div style="font-size:2rem;margin-bottom:0.5rem;">{ach["icon"]}</div>
                        <div style="font-weight:600;font-size:0.875rem;color:#1d1d1f;">{ach["name"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # 未解锁的成就
        locked = [a for a in ACHIEVEMENTS if a not in unlocked]
        if locked:
            with st.expander(f"未解锁的成就 ({len(locked)}个)"):
                for ach in locked:
                    st.markdown(f'''
                    <div style="display:flex;align-items:center;gap:0.75rem;padding:0.75rem;opacity:0.4;">
                        <div style="font-size:1.5rem;">{ach["icon"]}</div>
                        <div>
                            <div style="font-weight:500;font-size:0.875rem;">{ach["name"]}</div>
                            <div style="font-size:0.75rem;color:#86868b;">{ach["desc"]}</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # AI给你的寄语 - 极简深色卡片
        st.markdown(f'''
        <div style="background:linear-gradient(135deg, #1d1d1f 0%, #424245 100%);border-radius:20px;padding:2rem;margin:2rem 0;">
            <div style="font-size:0.75rem;font-weight:500;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1rem;">AI给你的寄语</div>
            <p style="font-size:1.125rem;line-height:1.8;color:#ffffff;">{fun_info["advice"]}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # 使用的工具统计 - 极简风格
        if st.session_state.personal_tools:
            st.markdown(f'''
            <div style="margin:2rem 0;">
                <div style="font-size:0.875rem;font-weight:500;color:#86868b;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:1.5rem;">你的AI工具箱 ({len(st.session_state.personal_tools)}个)</div>
            </div>
            ''', unsafe_allow_html=True)
            tool_cols = st.columns(5)
            for i, tool_name in enumerate(st.session_state.personal_tools):
                tool = next((t for t in AI_TOOLS_LIST if t["name"] == tool_name), None)
                icon = tool["icon"] if tool else "🤖"
                with tool_cols[i % 5]:
                    st.markdown(f'''
                    <div style="text-align:center;padding:1rem;background:#ffffff;border-radius:12px;border:1px solid #e5e5e7;">
                        <div style="font-size:1.5rem;margin-bottom:0.5rem;">{icon}</div>
                        <div style="font-size:0.75rem;color:#1d1d1f;">{tool_name}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # 分享卡片 - 极简风格
        st.markdown('''
        <div style="margin:3rem 0;">
        ''', unsafe_allow_html=True)
        share_text = f"我是{p['emoji']}{p['name']}，{fun_info['emoji']}{fun_info['title']}({total_score}分)"
        st.markdown(f'''
        <div class="share-card">
            <div style="font-size:3rem;margin-bottom:1rem;">{p["emoji"]} {fun_info["emoji"]}</div>
            <div style="font-size:1.25rem;font-weight:600;color:#1d1d1f;margin-bottom:0.5rem;">{share_text}</div>
            <div style="color:#86868b;font-size:0.875rem;">来测测你的AI人格吧！</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 重新测试 - 极简风格
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
# 侧边栏 - Edge风格标签页切换
with st.sidebar:
    st.markdown("""
    <style>
    .mode-tabs {
        display: flex;
        background: #f1f5f9;
        border-radius: 12px;
        padding: 4px;
        margin-bottom: 20px;
    }
    .mode-tab {
        flex: 1;
        text-align: center;
        padding: 10px 8px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 14px;
        font-weight: 500;
    }
    .mode-tab:hover {
        background: rgba(255,255,255,0.5);
    }
    .mode-tab.active {
        background: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .mode-tab.active .tab-icon {
        color: #6366f1;
    }
    .mode-tab.active .tab-text {
        color: #1e293b;
    }
    .tab-icon {
        font-size: 18px;
        margin-bottom: 4px;
        display: block;
    }
    .tab-text {
        font-size: 12px;
        color: #64748b;
    }
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Edge风格标签页 - 大按钮 + 图标 + 居中
    is_hr = st.session_state.app_mode in ["hr", "hr_add"]
    
    # 自定义样式 - 大按钮、居中、图标+文字
    st.markdown("""
    <style>
    /* 侧边栏居中容器 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        align-items: center;
    }
    
    /* 模式切换按钮容器 */
    .mode-switch-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        width: 100%;
        max-width: 200px;
        margin: 0 auto 20px auto;
    }
    
    /* 大按钮样式 */
    .mode-switch-container button {
        width: 100% !important;
        height: auto !important;
        padding: 16px 20px !important;
        border-radius: 14px !important;
        border: 2px solid transparent !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
    }
    
    /* 未选中状态 */
    .mode-switch-container button[kind="secondary"] {
        background: #f1f5f9 !important;
        color: #64748b !important;
        border-color: #e2e8f0 !important;
    }
    
    .mode-switch-container button[kind="secondary"]:hover {
        background: #e2e8f0 !important;
        border-color: #cbd5e1 !important;
        transform: translateY(-2px);
    }
    
    /* 选中状态 */
    .mode-switch-container button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border-color: #4f46e5 !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    }
    
    .mode-switch-container button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45) !important;
    }
    
    /* 图标样式 */
    .mode-icon {
        font-size: 20px;
        line-height: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 创建居中容器
    st.markdown('<div class="mode-switch-container">', unsafe_allow_html=True)
    
    # 简约按钮样式
    st.markdown("""
    <style>
    /* 简约按钮样式 */
    div[data-testid="stHorizontalBlock"]:has(button) {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 3px;
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button) button {
        border: none !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 14px 16px !important;
        transition: all 0.2s ease !important;
    }
    /* 未选中状态 */
    div[data-testid="stHorizontalBlock"]:has(button) button[kind="secondary"] {
        background: transparent !important;
        color: #666666 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button) button[kind="secondary"]:hover {
        background: #e9ecef !important;
    }
    /* 选中状态 - 灰白渐变 */
    div[data-testid="stHorizontalBlock"]:has(button) button[kind="primary"] {
        background: linear-gradient(135deg, #e8e8e8 0%, #d4d4d4 100%) !important;
        color: #333333 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button) button[kind="primary"]:hover {
        background: linear-gradient(135deg, #dcdcdc 0%, #c8c8c8 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 两列按钮
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("HR招聘", key="btn_hr", use_container_width=True,
                     type="primary" if is_hr else "secondary"):
            st.session_state.app_mode = "hr"
            st.rerun()
    with btn_col2:
        if st.button("个人测评", key="btn_personal", use_container_width=True,
                     type="primary" if not is_hr else "secondary"):
            st.session_state.app_mode = "personal"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # 快捷操作区
    if is_hr:
        st.markdown("### ⚡ 快捷操作")
        if st.button("➕ 新增候选人评估", use_container_width=True, type="secondary"):
            st.session_state.app_mode = "hr_add"
            st.rerun()

# 根据模式渲染不同页面
if st.session_state.app_mode == "hr":
    render_hr_version()
elif st.session_state.app_mode == "hr_add":
    render_hr_add_page()
elif st.session_state.app_mode == "personal":
    render_personal_version()
