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
        "name": "AI 优先思维",
        "description": "接到任务后，第一反应是'AI可以怎么帮我解'而不是'我以前怎么做'",
        "signals": ["描述中频繁出现'用AI重建了...'", "提到自己搭建的提示词库、AI工作流", "有跨领域快速产出的案例"]
    },
    "deep_collaboration": {
        "name": "深度协作能力",
        "description": "将AI当成思维伙伴、执行团队，能进行多轮、分层、批判性的深度协作",
        "signals": ["多步骤、多工具的AI工作流", "有纠错回路和验证机制", "与AI进行批判性对话的案例"]
    },
    "problem_reframing": {
        "name": "问题重构能力",
        "description": "不仅用AI提效，更用AI重新定义'这个问题应该是什么'",
        "signals": ["质疑任务本身的案例", "用AI找到更优路径的经历", "重新定义工作流程"]
    },
    "learning_mode": {
        "name": "学习模式",
        "description": "'用中学、边跑边造'，面对新领域时本能地用AI搭建脚手架快速进入",
        "signals": ["用AI学习新领域的案例", "快速掌握新技能的经历", "持续迭代学习方法"]
    },
    "iteration_agility": {
        "name": "迭代敏捷度",
        "description": "每天用AI的习惯在持续进化，关注前沿并积极尝试",
        "signals": ["AI使用习惯有明显变化", "关注并尝试新工具", "主动分享AI方法论"]
    },
    "boundary_awareness": {
        "name": "边界认知",
        "description": "清楚AI的能力边界，能精准指出AI不靠谱之处",
        "signals": ["能具体指出AI的错误", "有修复AI错误的案例", "对AI能力有理性认知"]
    }
}

LEVEL_DEFINITIONS = {
    "L0": {"name": "L0 - 偶尔使用者", "description": "仅停留在偶尔使用AI工具，没有系统性的AI工作方式", "score_range": (0, 40)},
    "L1": {"name": "L1 - 工具使用者", "description": "能熟练使用AI工具提效，但尚未形成系统性的AI Native 工作方式", "score_range": (40, 60)},
    "L2": {"name": "L2 - 深度协作者", "description": "将AI作为默认操作系统，能进行深度协作，持续迭代自己的工作方式", "score_range": (60, 80)},
    "L3": {"name": "L3 - 模式重构者", "description": "能系统性重构工作流程，用AI改写工作边界，具备方法论输出能力", "score_range": (80, 100)}
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
        
        prompt = f"""你是一位专业的 AI Native 人才评估专家。请分析以下简历，评估候选人在 AI Native 六个维度上的表现。

## AI Native 六维评分标准

{dimensions_desc}

## 等级定义

- L0 (0-40分): 偶尔使用者 - 仅停留在偶尔使用AI工具
- L1 (40-60分): 工具使用者 - 能熟练使用AI工具提效
- L2 (60-80分): 深度协作者 - 将AI作为默认操作系统
- L3 (80-100分): 模式重构者 - 能系统性重构工作流程

## 简历内容

{resume_text}

## 分析要求

请按以下 JSON 格式输出分析结果：

```json
{{
  "basic_info": {{
    "name": "姓名",
    "position": "应聘职位",
    "ai_tools": ["使用的AI工具列表"],
    "key_projects": ["关键项目经验"]
  }},
  "dimension_scores": {{
    "ai_first_mindset": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "deep_collaboration": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "problem_reframing": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "learning_mode": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "iteration_agility": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}},
    "boundary_awareness": {{"score": 分数, "evidence": "证据", "reasoning": "评分理由"}}
  }},
  "total_score": 总分,
  "level": "L0/L1/L2/L3",
  "quick_checklist": {{
    "ai_first_response": true/false,
    "own_methodology": true/false,
    "workflow_reformed": true/false,
    "specific_complaints": true/false,
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
3. 总分是六维分数的加权平均（前3维权重1.0，后3维权重0.8）
4. 必须严格按照 JSON 格式输出"""
        
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
        
        # 计算总分
        weights = [1.0, 1.0, 1.0, 0.8, 0.8, 0.8]
        scores = [result["dimension_scores"][dim]["score"] for dim in required_dimensions]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
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
                "own_methodology": False,
                "workflow_reformed": False,
                "specific_complaints": False,
                "ai_anxiety": False
            }
        
        return result


def get_analyzer() -> AIResumeAnalyzer:
    """获取分析器实例（从 session state 或创建新的）"""
    if 'ai_analyzer' not in st.session_state:
        api_key = st.session_state.get('dashscope_api_key', os.getenv('DASHSCOPE_API_KEY', ''))
        model = st.session_state.get('ai_model', 'qwen-turbo')
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
            if st.button("💾 保存设置"):
                st.session_state.dashscope_api_key = api_key
                st.session_state.ai_model = model
                # 重新创建分析器
                st.session_state.ai_analyzer = AIResumeAnalyzer(api_key=api_key, model=model)
                st.success("✅ 设置已保存！")
        
        with col2:
            if st.button("🧪 测试连接"):
                analyzer = AIResumeAnalyzer(api_key=api_key, model=model)
                if analyzer.is_available():
                    try:
                        # 简单测试
                        response = analyzer.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "你好"}],
                            max_tokens=10
                        )
                        st.success("✅ 连接成功！")
                    except Exception as e:
                        st.error(f"❌ 连接失败: {e}")
                else:
                    st.error("❌ 分析器初始化失败，请检查 API Key")
        
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
        st.error(f"❌ {result['error']}")
        return
    
    st.success("✅ AI 分析完成！")
    
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
    
    # AI 工具
    ai_tools = basic_info.get("ai_tools", [])
    if ai_tools:
        st.write("**识别的 AI 工具:**")
        for tool in ai_tools:
            st.markdown(f'<span style="background:#e3f2fd;padding:2px 8px;border-radius:4px;margin:2px;display:inline-block">{tool}</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # 六维评分
    st.subheader("📊 AI 评分结果")
    
    dimension_scores = result.get("dimension_scores", {})
    
    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
        dim_data = dimension_scores.get(dim_key, {})
        score = dim_data.get("score", 0)
        evidence = dim_data.get("evidence", "")
        reasoning = dim_data.get("reasoning", "")
        
        with st.expander(f"📈 {dim_info['name']}: {score}分"):
            st.write(f"**评分理由:** {reasoning}")
            if evidence:
                st.write(f"**证据:** {evidence}")
    
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
        title="AI Native 六维能力雷达图"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 快速判断清单
    st.subheader("✅ 快速判断清单")
    checklist = result.get("quick_checklist", {})
    checklist_items = [
        ("ai_first_response", "候选人第一反应是'AI'而不是'人'"),
        ("own_methodology", "候选人拥有'自己的方法论'"),
        ("workflow_reformed", "候选人改造过自己的工作流"),
        ("specific_complaints", "候选人对AI的吐槽具体"),
        ("ai_anxiety", "候选人有积极的'AI焦虑'")
    ]
    
    passed = 0
    for key, label in checklist_items:
        checked = checklist.get(key, False)
        if checked:
            passed += 1
            st.markdown(f"✅ {label}")
        else:
            st.markdown(f"❌ {label}")
    
    st.write(f"**通过项目: {passed}/5**")
    
    # 综合评价
    st.subheader("📝 AI 综合评价")
    st.write(result.get("overall_assessment", "无"))
    
    # 优势和顾虑
    col1, col2 = st.columns(2)
    with col1:
        st.write("**优势:**")
        for strength in result.get("strengths", []):
            st.markdown(f"✓ {strength}")
    
    with col2:
        st.write("**顾虑:**")
        for concern in result.get("concerns", []):
            st.markdown(f"⚠ {concern}")
    
    # 面试建议
    st.subheader("💡 面试建议")
    for suggestion in result.get("interview_suggestions", []):
        st.markdown(f"• {suggestion}")
    
    # 应用按钮
    if on_apply:
        st.divider()
        if st.button("✅ 应用 AI 分析结果到表单", type="primary"):
            on_apply(result)
            st.success("已应用！请检查并调整评分。")
