"""
AI Native 人才简历分析模块
支持通义千问(Qwen)、OpenAI 等模型
"""

import json
import os
from typing import Dict, Any, Optional
import streamlit as st

# AI Native 评分维度定义（用于提示词）
AI_NATIVE_DIMENSIONS = {
    "ai_first_mindset": {
        "name": "AI-First 思维",
        "description": "以AI为核心重新设计工作流程，而非在传统流程上叠加AI辅助。能识别AI可替代/增强的环节，主动重构工作方式",
        "signals": ["描述中频繁出现'用AI重建了...'", "提到自己搭建的提示词库、AI工作流", "有跨领域快速产出的案例", "能识别AI可替代/增强的环节"],
        "weight": 1.0
    },
    "prompt_engineering": {
        "name": "提示词工程能力",
        "description": "精准驱动AI产出的提问能力。能设计结构化提示、角色设定、约束条件，让AI输出质量最大化",
        "signals": ["有系统化的提示词设计案例", "提到提示词模板或框架", "能描述如何让AI输出更准确", "有优化提示词迭代过程"],
        "weight": 1.0
    },
    "deep_collaboration": {
        "name": "深度协作能力",
        "description": "将AI当成思维伙伴、执行团队，能进行多轮、分层、批判性的深度协作",
        "signals": ["多步骤、多工具的AI工作流", "有纠错回路和验证机制", "与AI进行批判性对话的案例"],
        "weight": 1.0
    },
    "problem_reframing": {
        "name": "问题重构能力",
        "description": "不仅用AI提效，更用AI重新定义'这个问题应该是什么'",
        "signals": ["质疑任务本身的案例", "用AI找到更优路径的经历", "重新定义工作流程"],
        "weight": 1.0
    },
    "learning_mode": {
        "name": "学习模式",
        "description": "'用中学、边跑边造'，面对新领域时本能地用AI搭建脚手架快速进入",
        "signals": ["用AI学习新领域的案例", "快速掌握新技能的经历", "持续迭代学习方法"],
        "weight": 0.8
    },
    "iteration_agility": {
        "name": "迭代敏捷度",
        "description": "每天用AI的习惯在持续进化，关注前沿并积极尝试",
        "signals": ["AI使用习惯有明显变化", "关注并尝试新工具", "主动分享AI方法论"],
        "weight": 0.8
    },
    "boundary_awareness": {
        "name": "边界认知",
        "description": "清楚AI的能力边界，能精准指出AI不靠谱之处",
        "signals": ["能具体指出AI的错误", "有修复AI错误的案例", "对AI能力有理性认知"],
        "weight": 0.8
    },
    "critical_validation": {
        "name": "批判性验证",
        "description": "评估AI输出质量，发现事实错误、逻辑漏洞和偏见。不盲目相信AI，具备独立判断能力",
        "signals": ["有验证AI输出的案例", "能指出AI的幻觉和错误", "有事实核查的习惯", "能识别AI的偏见"],
        "weight": 0.9
    }
}

LEVEL_DEFINITIONS = {
    "L0": {"name": "L0 - 偶尔使用者", "description": "仅停留在偶尔使用AI工具，没有系统性的AI工作方式", "score_range": (0, 40), "color": "#9E9E9E"},
    "L1": {"name": "L1 - 工具使用者", "description": "能熟练使用AI工具提效，但尚未形成系统性的AI Native 工作方式", "score_range": (40, 60), "color": "#4CAF50"},
    "L2": {"name": "L2 - 深度协作者", "description": "将AI作为默认操作系统，能进行深度协作，持续迭代自己的工作方式", "score_range": (60, 80), "color": "#2196F3"},
    "L3": {"name": "L3 - 模式重构者", "description": "能系统性重构工作流程，用AI改写工作边界，具备方法论输出能力", "score_range": (80, 100), "color": "#FF9800"}
}

class AIResumeAnalyzer:
    """AI简历分析器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-turbo"):
        """
        初始化分析器
        
        Args:
            api_key: API密钥，如果不提供则从环境变量获取
            model: 模型名称，默认使用通义千问-turbo
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                # 尝试使用 OpenAI 兼容接口
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
            except ImportError:
                st.error("请先安装 openai 包: pip install openai")
    
    def is_available(self) -> bool:
        """检查AI是否可用"""
        return self.client is not None and self.api_key is not None
    
    def _build_analysis_prompt(self, resume_text: str) -> str:
        """构建分析提示词"""
        
        dimensions_desc = "\n".join([
            f"{i+1}. {info['name']}: {info['description']}\n   关键信号: {', '.join(info['signals'])}"
            for i, (key, info) in enumerate(AI_NATIVE_DIMENSIONS.items())
        ])
        
        prompt = f"""你是一位专业的 AI Native 人才评估专家。请深度分析以下简历，重点识别候选人的AI项目经验和AI工具使用栈。

## AI Native 八维评分标准

{dimensions_desc}

## 等级定义

- L0 (0-40分): 偶尔使用者 - 仅停留在偶尔使用AI工具
- L1 (40-60分): 工具使用者 - 能熟练使用AI工具提效
- L2 (60-80分): 深度协作者 - 将AI作为默认操作系统
- L3 (80-100分): 模式重构者 - 能系统性重构工作流程

## AI工具识别指南

请识别以下类别的AI工具使用情况：
- 对话大模型: ChatGPT, Claude, Gemini, 文心一言, 通义千问, Kimi, DeepSeek等
- AI编程: GitHub Copilot, Cursor, Codeium, Tabnine等
- AI绘画: Midjourney, Stable Diffusion, DALL-E, 即梦, 可灵等
- AI视频: Sora, Runway, Pika, HeyGen, 剪映AI等
- AI写作: Jasper, Copy.ai, Notion AI, 讯飞听见等
- AI数据分析: ChatExcel, AI公式生成, 智能图表等
- 智能体/自动化: Coze, Dify, n8n, Make, Zapier等

## AI项目经验识别

请提取以下类型的AI相关项目：
- 使用AI完成的具体业务成果（如"用AI生成营销文案，提升转化率30%"）
- 搭建的AI工作流或自动化流程
- 开发的AI应用或智能体
- 用AI解决的具体技术难题
- 提示词工程优化案例

## 简历内容

{resume_text}

## 分析要求

请按以下 JSON 格式输出分析结果：

```json
{{
  "basic_info": {{
    "name": "姓名",
    "position": "应聘职位",
    "email": "邮箱地址",
    "phone": "电话号码"
  }},
  "ai_tools_analysis": {{
    "tools_by_category": {{
      "对话大模型": ["工具名"],
      "AI编程": ["工具名"],
      "AI绘画": ["工具名"],
      "AI视频": ["工具名"],
      "AI写作": ["工具名"],
      "AI数据分析": ["工具名"],
      "智能体自动化": ["工具名"]
    }},
    "tools_proficiency": "熟练/一般/了解",
    "total_tools_count": 数量
  }},
  "ai_projects": [
    {{
      "project_name": "项目名称",
      "description": "项目描述",
      "ai_tools_used": ["使用的AI工具"],
      "business_impact": "业务成果（量化数据优先）",
      "complexity": "高/中/低"
    }}
  ],
  "prompt_engineering_evidence": {{
    "has_prompt_library": true/false,
    "optimization_cases": ["优化案例描述"],
    "framework_used": ["使用的提示词框架"]
  }},
  "dimension_scores": {{
    "ai_first_mindset": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "prompt_engineering": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "deep_collaboration": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "problem_reframing": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "learning_mode": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "iteration_agility": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "boundary_awareness": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "critical_validation": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}}
  }},
  "total_score": 总分,
  "level": "L0/L1/L2/L3",
  "quick_checklist": {{
    "ai_first_response": true/false,
    "own_prompt_library": true/false,
    "own_methodology": true/false,
    "workflow_reformed": true/false,
    "specific_complaints": true/false,
    "fact_checking_habit": true/false,
    "ai_anxiety": true/false
  }},
  "overall_assessment": "综合评价",
  "strengths": ["优势1", "优势2"],
  "concerns": ["顾虑1", "顾虑2"],
  "interview_suggestions": ["面试建议1", "面试建议2"]
}}
```

注意：
1. 分数范围 0-100，必须是整数
2. 必须有具体的证据支持评分
3. 总分是八维分数的加权平均（权重：ai_first_mindset=1.0, prompt_engineering=1.0, deep_collaboration=1.0, problem_reframing=1.0, learning_mode=0.8, iteration_agility=0.8, boundary_awareness=0.8, critical_validation=0.9）
4. AI项目经验请尽可能提取具体、可量化的成果
5. 工具栈按类别整理，识别熟练程度
6. 必须严格按照 JSON 格式输出"""
        
        return prompt
    
    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        分析简历
        
        Args:
            resume_text: 简历文本内容
            
        Returns:
            分析结果字典
        """
        if not self.is_available():
            return {"error": "AI 分析器未配置，请先设置 API Key"}
        
        if not resume_text or len(resume_text.strip()) < 50:
            return {"error": "简历内容太短，无法分析"}
        
        try:
            prompt = self._build_analysis_prompt(resume_text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的 AI Native 人才评估专家，擅长从简历中识别候选人的AI使用能力和思维方式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # 提取 JSON 内容
            json_content = self._extract_json(content)
            result = json.loads(json_content)
            
            # 验证结果格式
            result = self._validate_result(result)
            
            return result
            
        except Exception as e:
            return {"error": f"分析失败: {str(e)}"}
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        # 尝试找到 JSON 代码块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        else:
            # 直接返回文本，假设它就是 JSON
            return text.strip()
    
    def _validate_result(self, result: Dict) -> Dict:
        """验证并补全结果"""
        # 确保所有必需的字段都存在
        required_dimensions = list(AI_NATIVE_DIMENSIONS.keys())
        
        if "dimension_scores" not in result:
            result["dimension_scores"] = {}
        
        for dim in required_dimensions:
            if dim not in result["dimension_scores"]:
                result["dimension_scores"][dim] = {"score": 50, "evidence": "", "reasoning": ""}
            else:
                # 确保分数在有效范围内
                score = result["dimension_scores"][dim].get("score", 50)
                result["dimension_scores"][dim]["score"] = max(0, min(100, int(score)))
        
        # 计算总分 - 8维度加权
        weights_map = {
            "ai_first_mindset": 1.0,
            "prompt_engineering": 1.0,
            "deep_collaboration": 1.0,
            "problem_reframing": 1.0,
            "learning_mode": 0.8,
            "iteration_agility": 0.8,
            "boundary_awareness": 0.8,
            "critical_validation": 0.9
        }
        weighted_sum = sum(result["dimension_scores"][dim]["score"] * weights_map.get(dim, 1.0) for dim in required_dimensions)
        total_weight = sum(weights_map.get(dim, 1.0) for dim in required_dimensions)
        result["total_score"] = round(weighted_sum / total_weight, 1)
        
        # 确定等级
        total = result["total_score"]
        if total >= 80:
            result["level"] = "L3"
        elif total >= 60:
            result["level"] = "L2"
        elif total >= 40:
            result["level"] = "L1"
        else:
            result["level"] = "L0"
        
        # 确保 quick_checklist 存在
        if "quick_checklist" not in result:
            result["quick_checklist"] = {
                "ai_first_response": False,
                "own_prompt_library": False,
                "own_methodology": False,
                "workflow_reformed": False,
                "specific_complaints": False,
                "fact_checking_habit": False,
                "ai_anxiety": False
            }
        
        # 确保新的分析字段存在
        if "ai_tools_analysis" not in result:
            result["ai_tools_analysis"] = {
                "tools_by_category": {},
                "tools_proficiency": "了解",
                "total_tools_count": 0
            }
        if "ai_projects" not in result:
            result["ai_projects"] = []
        if "prompt_engineering_evidence" not in result:
            result["prompt_engineering_evidence"] = {
                "has_prompt_library": False,
                "optimization_cases": [],
                "framework_used": []
            }
        
        return result


def get_analyzer(force_refresh: bool = False) -> AIResumeAnalyzer:
    """获取分析器实例（从 session state 或创建新的）
    
    Args:
        force_refresh: 是否强制重新创建实例（当配置可能已更改时使用）
    """
    api_key = st.session_state.get('dashscope_api_key', os.getenv('DASHSCOPE_API_KEY', ''))
    model = st.session_state.get('ai_model', 'qwen-turbo')
    
    # 检查是否需要重新创建分析器
    need_refresh = force_refresh or 'ai_analyzer' not in st.session_state
    
    if not need_refresh and 'ai_analyzer' in st.session_state:
        # 检查现有分析器的配置是否匹配当前设置
        existing = st.session_state.ai_analyzer
        if existing.api_key != api_key or existing.model != model:
            need_refresh = True
    
    if need_refresh:
        st.session_state.ai_analyzer = AIResumeAnalyzer(api_key=api_key, model=model)
    
    return st.session_state.ai_analyzer


def render_ai_settings():
    """渲染 AI 设置界面"""
    st.subheader("🤖 AI 分析设置")
    
    with st.expander("配置 AI API"):
        api_key = st.text_input(
            "DashScope API Key",
            value=st.session_state.get('dashscope_api_key', os.getenv('DASHSCOPE_API_KEY', '')),
            type="password",
            help="从阿里云 DashScope 控制台获取: https://dashscope.aliyun.com"
        )
        
        model = st.selectbox(
            "选择模型",
            ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext"],
            index=0,
            help="qwen-turbo: 速度快、成本低\nqwen-plus: 平衡性能\nqwen-max: 最强性能"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存设置"):
                st.session_state.dashscope_api_key = api_key
                st.session_state.ai_model = model
                # 重新创建分析器
                st.session_state.ai_analyzer = AIResumeAnalyzer(api_key=api_key, model=model)
                st.success("设置已保存！")
        
        with col2:
            if st.button("测试连接"):
                analyzer = AIResumeAnalyzer(api_key=api_key, model=model)
                if analyzer.is_available():
                    try:
                        # 简单测试
                        response = analyzer.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "你好"}],
                            max_tokens=10
                        )
                        st.success("连接成功！")
                    except Exception as e:
                        st.error(f"连接失败: {e}")
                else:
                    st.error("分析器初始化失败，请检查 API Key")
        
        st.info("""
        **如何获取 API Key：**
        1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com)
        2. 注册/登录阿里云账号
        3. 创建 API Key
        4. 新用户有免费额度（100万次调用）
        """)


def render_ai_analysis_result(result: Dict[str, Any], on_apply: callable = None):
    """渲染 AI 分析结果"""

    if "error" in result:
        st.error(f"{result['error']}")
        return

    st.success("AI 分析完成！")

    # 基本信息
    basic_info = result.get("basic_info", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**姓名:** {basic_info.get('name', '未识别')}")
    with col2:
        st.write(f"**职位:** {basic_info.get('position', '未识别')}")
    with col3:
        level = result.get("level", "L0")
        score = result.get("total_score", 0)
        st.write(f"**AI Native 等级:** {level} ({score}分)")

    st.divider()

    # AI工具栈分析
    ai_tools_analysis = result.get("ai_tools_analysis", {})
    if ai_tools_analysis.get("total_tools_count", 0) > 0:
        st.subheader("🛠️ AI工具栈分析")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("识别工具数", ai_tools_analysis.get("total_tools_count", 0))
            st.metric("熟练程度", ai_tools_analysis.get("tools_proficiency", "了解"))
        with col2:
            tools_by_category = ai_tools_analysis.get("tools_by_category", {})
            if tools_by_category:
                for category, tools in tools_by_category.items():
                    if tools:
                        st.write(f"**{category}:** {', '.join(tools)}")
        st.divider()

    # AI项目经验
    ai_projects = result.get("ai_projects", [])
    if ai_projects:
        st.subheader("📂 AI项目经验")
        for project in ai_projects:
            with st.expander(f"{project.get('project_name', '未命名项目')} - {project.get('complexity', '中')}复杂度"):
                st.write(f"**描述:** {project.get('description', '')}")
                st.write(f"**使用工具:** {', '.join(project.get('ai_tools_used', []))}")
                st.write(f"**业务成果:** {project.get('business_impact', '')}")
        st.divider()

    # 提示词工程证据
    prompt_evidence = result.get("prompt_engineering_evidence", {})
    if prompt_evidence.get("has_prompt_library") or prompt_evidence.get("optimization_cases"):
        st.subheader("📝 提示词工程能力")
        col1, col2 = st.columns(2)
        with col1:
            has_library = prompt_evidence.get("has_prompt_library", False)
            st.write(f"**系统化提示词库:** {'✅ 有' if has_library else '❌ 无'}")
            frameworks = prompt_evidence.get("framework_used", [])
            if frameworks:
                st.write(f"**使用框架:** {', '.join(frameworks)}")
        with col2:
            cases = prompt_evidence.get("optimization_cases", [])
            if cases:
                st.write("**优化案例:**")
                for case in cases[:3]:
                    st.caption(f"• {case}")
        st.divider()

    # 八维评分
    st.subheader("📊 AI Native 八维能力评估")

    dimension_scores = result.get("dimension_scores", {})

    # 添加评分解读说明
    with st.expander("评分标准说明"):
        st.write("""
        **评分等级说明：**
        - **0-20分**: 未表现出该特征 - 候选人在这方面没有明显表现
        - **21-40分**: 偶尔表现出该特征 - 有初步意识但不够系统
        - **41-60分**: 基本具备该特征 - 能够常规性地运用
        - **61-80分**: 深度具备该特征 - 形成了自己的工作方式
        - **81-100分**: 卓越表现 - 具备方法论输出能力，能指导他人
        """)

    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
        dim_data = dimension_scores.get(dim_key, {})
        score = dim_data.get("score", 0)
        evidence = dim_data.get("evidence", "")
        reasoning = dim_data.get("reasoning", "")

        # 根据分数生成评价等级
        if score >= 81:
            level_desc = "卓越"
            level_color = "#4CAF50"
        elif score >= 61:
            level_desc = "深度具备"
            level_color = "#2196F3"
        elif score >= 41:
            level_desc = "基本具备"
            level_color = "#FF9800"
        elif score >= 21:
            level_desc = "初步意识"
            level_color = "#9E9E9E"
        else:
            level_desc = "待发展"
            level_color = "#757575"

        with st.expander(f"{dim_info['name']}: {score}分 - {level_desc}"):
            st.markdown(f"**维度定义:** {dim_info['description']}")
            st.markdown(f"**关键信号:** {', '.join(dim_info['signals'])}")
            st.markdown(f"**评价等级:** <span style='color:{level_color};font-weight:bold'>{level_desc}</span>", unsafe_allow_html=True)
            st.markdown(f"**评分理由:** {reasoning}")
            if evidence:
                st.markdown(f"**具体证据:** {evidence}")

            # 添加改进建议
            if score < 40:
                st.info(f"**发展建议:** 建议候选人加强对「{dim_info['name']}」的关注，可以通过学习相关案例和实践来提升这方面的能力。")
            elif score < 70:
                st.info(f"**提升建议:** 候选人已具备基础，建议进一步系统化「{dim_info['name']}」的工作方法，形成可复用的经验。")
            else:
                st.success(f"**优势领域:** 「{dim_info['name']}」是候选人的强项，可以在面试中深入了解其方法论，并考虑如何发挥其优势。")

    # 雷达图
    import plotly.graph_objects as go

    categories = [info['name'] for info in AI_NATIVE_DIMENSIONS.values()]
    values = [dimension_scores.get(dim, {}).get("score", 0) for dim in AI_NATIVE_DIMENSIONS.keys()]
    values.append(values[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill='toself',
        name='AI分析结果'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400,
        title="AI Native 八维能力雷达图"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 快速判断清单
    st.subheader("✅ 快速判断清单")
    checklist = result.get("quick_checklist", {})
    checklist_items = [
        ("ai_first_response", "候选人第一反应是'AI'而不是'人'"),
        ("own_prompt_library", "候选人有系统化的提示词库"),
        ("own_methodology", "候选人拥有'自己的方法论'"),
        ("workflow_reformed", "候选人改造过自己的工作流"),
        ("specific_complaints", "候选人对AI的吐槽具体"),
        ("fact_checking_habit", "候选人有事实核查习惯"),
        ("ai_anxiety", "候选人有积极的'AI焦虑'")
    ]

    passed = 0
    for key, label in checklist_items:
        checked = checklist.get(key, False)
        if checked:
            passed += 1
            st.markdown(f"[是] {label}")
        else:
            st.markdown(f"[否] {label}")
    
    st.write(f"**通过项目: {passed}/5**")
    
    # 根据通过数量给出评价
    if passed >= 4:
        st.success("**快速判断结果:** 候选人展现出强烈的 AI Native 特征，建议优先考虑！")
    elif passed >= 2:
        st.info("**快速判断结果:** 候选人具备一定的 AI Native 基础，值得进一步深入了解。")
    else:
        st.warning("**快速判断结果:** 候选人在 AI Native 方面的表现较弱，需要谨慎评估。")
    
    # 综合评价
    st.subheader("AI 综合评价")
    overall = result.get("overall_assessment", "")
    if overall:
        st.markdown(f"**总体评价:** {overall}")
        
        # 添加等级解读
        level = result.get("level", "L0")
        total_score = result.get("total_score", 0)
        
        level_descriptions = {
            "L0": "偶尔使用者 - 仅停留在偶尔使用AI工具，没有系统性的AI工作方式",
            "L1": "工具使用者 - 能熟练使用AI工具提效，但尚未形成系统性的AI Native工作方式",
            "L2": "深度协作者 - 将AI作为默认操作系统，能进行深度协作，持续迭代自己的工作方式",
            "L3": "模式重构者 - 能系统性重构工作流程，用AI改写工作边界，具备方法论输出能力"
        }
        
        st.markdown(f"**等级解读 ({level} - {total_score}分):** {level_descriptions.get(level, '')}")
    else:
        st.write("暂无综合评价")
    
    # 优势和顾虑
    st.subheader("优劣势分析")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**核心优势:**")
        strengths = result.get("strengths", [])
        if strengths:
            for strength in strengths:
                st.markdown(f"- {strength}")
        else:
            st.write("未识别出明显优势")
    
    with col2:
        st.write("**需要关注的点:**")
        concerns = result.get("concerns", [])
        if concerns:
            for concern in concerns:
                st.markdown(f"- {concern}")
        else:
            st.write("未识别出明显顾虑")
    
    # 面试建议
    st.subheader("面试建议")
    suggestions = result.get("interview_suggestions", [])
    if suggestions:
        st.write("基于AI分析，建议在面试中重点关注以下方面：")
        for i, suggestion in enumerate(suggestions, 1):
            st.markdown(f"{i}. {suggestion}")
    else:
        st.write("建议从以下维度深入了解候选人：")
        st.markdown("1. 询问候选人使用AI解决复杂问题的具体案例")
        st.markdown("2. 了解候选人对AI能力边界的认知")
        st.markdown("3. 探讨候选人如何持续学习和迭代AI使用方法")
    
    # 应用按钮
    if on_apply:
        st.divider()
        if st.button("应用 AI 分析结果到表单", type="primary"):
            on_apply(result)
            st.success("已应用！请检查并调整评分。")
