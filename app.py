import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import base64

# 页面配置
st.set_page_config(
    page_title="AI Native 人才简历分析看板",
    page_icon="🎯",
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

def load_candidates():
    """加载候选人数据"""
    if CANDIDATES_FILE.exists():
        with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_candidates(candidates):
    """保存候选人数据"""
    with open(CANDIDATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

def calculate_level(total_score):
    """根据总分计算等级"""
    for level, info in LEVEL_DEFINITIONS.items():
        min_score, max_score = info["score_range"]
        if min_score <= total_score < max_score or (level == "L3" and total_score >= max_score):
            return level
    return "L0"

def calculate_score(dimension_scores):
    """计算加权总分"""
    total = 0
    max_total = 0
    weights = [1.0, 1.0, 1.0, 0.8, 0.8, 0.8]
    for i, dim_key in enumerate(AI_NATIVE_DIMENSIONS.keys()):
        score = dimension_scores.get(dim_key, 0)
        weight = weights[i]
        total += score * weight
        max_total += 100 * weight
    
    if max_total > 0:
        normalized_score = (total / max_total) * 100
    else:
        normalized_score = 0
    
    return round(normalized_score, 1)

def get_level_color(level):
    """获取等级对应的颜色"""
    return LEVEL_DEFINITIONS.get(level, {}).get("color", "#gray")

# 初始化 session state
if 'candidates' not in st.session_state:
    st.session_state.candidates = load_candidates()

if 'current_candidate' not in st.session_state:
    st.session_state.current_candidate = None

if 'ai_analysis_result' not in st.session_state:
    st.session_state.ai_analysis_result = None

# CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .score-value {
        font-size: 3rem;
        font-weight: bold;
    }
    .level-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        margin: 0.5rem 0;
    }
    .dimension-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .signal-item {
        background: #e9ecef;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin: 0.2rem;
        display: inline-block;
    }
    .checklist-item {
        padding: 0.8rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-radius: 8px;
        border-left: 3px solid #28a745;
    }
    .ai-analysis-section {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.title("🎯 导航菜单")
page = st.sidebar.radio("", ["📋 候选人列表", "➕ 新增评估", "📊 候选人对比", "📖 评分标准"])

# 主内容区
if page == "📋 候选人列表":
    st.markdown('<div class="main-header">AI Native 人才简历分析看板</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">基于 AI Native 人才标准的候选人评估系统（支持 AI 智能分析）</div>', unsafe_allow_html=True)
    
    # AI 状态指示
    analyzer = get_analyzer()
    if analyzer.is_available():
        st.success("🤖 AI 分析功能已启用 - 可使用 AI 辅助简历分析")
    else:
        st.info("💡 如需启用 AI 分析功能，请在「➕ 新增评估」页面配置 API Key")
    
    candidates = st.session_state.candidates
    
    if not candidates:
        st.info("👋 欢迎使用！目前还没有候选人数据，请点击左侧'➕ 新增评估'开始添加。")
    else:
        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        
        level_counts = {"L0": 0, "L1": 0, "L2": 0, "L3": 0}
        for candidate in candidates.values():
            level = candidate.get("level", "L0")
            level_counts[level] = level_counts.get(level, 0) + 1
        
        with col1:
            st.metric("总候选人", len(candidates))
        with col2:
            st.metric("L2/L3 人才", level_counts["L2"] + level_counts["L3"])
        with col3:
            st.metric("L2 深度协作者", level_counts["L2"])
        with col4:
            st.metric("L3 模式重构者", level_counts["L3"])
        
        st.divider()
        
        # 候选人列表
        st.subheader("📋 候选人列表")
        
        # 搜索和筛选
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 搜索候选人姓名", "")
        with col2:
            level_filter = st.multiselect("筛选等级", ["L0", "L1", "L2", "L3"], default=[])
        
        # 过滤候选人
        filtered_candidates = {}
        for cid, candidate in candidates.items():
            if search and search.lower() not in candidate.get("name", "").lower():
                continue
            if level_filter and candidate.get("level") not in level_filter:
                continue
            filtered_candidates[cid] = candidate
        
        # 显示候选人卡片
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

elif page == "➕ 新增评估":
    st.markdown('<div class="main-header">新增候选人评估</div>', unsafe_allow_html=True)
    
    # 初始化 AI 分析器
    analyzer = get_analyzer()
    
    # AI 设置
    render_ai_settings()
    
    st.divider()
    
    # 基本信息
    st.subheader("1️⃣ 基本信息")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("候选人姓名 *", key="input_name")
        position = st.text_input("应聘职位 *", key="input_position")
    with col2:
        email = st.text_input("邮箱", key="input_email")
        phone = st.text_input("电话", key="input_phone")
    
    # 简历上传和 AI 分析
    st.subheader("2️⃣ 简历上传与 AI 分析")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        resume_file = st.file_uploader("上传简历 (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="resume_upload")
        
        if resume_file:
            st.success(f"✅ 已上传: {resume_file.name}")
            # 尝试读取简历内容
            try:
                if resume_file.type == "text/plain":
                    resume_text = resume_file.getvalue().decode('utf-8', errors='ignore')
                elif resume_file.type == "application/pdf":
                    resume_text = "[PDF文件内容 - 请在右侧查看AI分析结果]"
                    # 尝试用 PyPDF2 读取
                    try:
                        import PyPDF2
                        from io import BytesIO
                        pdf_reader = PyPDF2.PdfReader(BytesIO(resume_file.getvalue()))
                        resume_text = ""
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text() + "\n"
                    except:
                        pass
                else:
                    resume_text = "[文档内容 - 请在右侧查看AI分析结果]"
            except:
                resume_text = ""
        else:
            resume_text = ""
    
    with col2:
        st.write("**🤖 AI 智能分析**")
        
        # AI 分析按钮
        if st.button("🔍 使用 AI 分析简历", type="primary", disabled=not analyzer.is_available()):
            if resume_file and resume_text:
                with st.spinner("🤖 AI 正在分析简历，请稍候..."):
                    result = analyzer.analyze_resume(resume_text)
                    st.session_state.ai_analysis_result = result
                    
                    # 如果 AI 识别出姓名和职位，自动填充
                    if "basic_info" in result:
                        basic_info = result.get("basic_info", {})
                        if basic_info.get("name"):
                            st.session_state.input_name = basic_info.get("name", "")
                        if basic_info.get("position"):
                            st.session_state.input_position = basic_info.get("position", "")
            else:
                st.warning("⚠️ 请先上传简历文件")
        
        # 显示 AI 分析结果
        if st.session_state.ai_analysis_result:
            render_ai_analysis_result(st.session_state.ai_analysis_result)
    
    # 简历内容（可编辑）
    if resume_text and resume_text != "[PDF文件内容]":
        with st.expander("📄 查看简历内容"):
            st.text_area("简历文本", value=resume_text, height=200, key="resume_text_display")
    
    # AI Native 六维评分（人工评分）
    st.divider()
    st.subheader("3️⃣ 人工评分（可参考 AI 分析结果）")
    st.caption("请根据候选人的简历和面试表现，对以下六个维度进行评分（0-100分）")
    
    dimension_scores = {}
    
    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
        with st.expander(f"📊 {dim_info['name']} (权重: {dim_info['weight']})"):
            st.write(f"**定义:** {dim_info['description']}")
            st.write("**关键信号:**")
            for signal in dim_info['signals']:
                st.markdown(f'<span class="signal-item">{signal}</span>', unsafe_allow_html=True)
            
            # 如果有 AI 分析结果，自动填充
            ai_result = st.session_state.ai_analysis_result
            default_score = 50
            default_notes = ""
            if ai_result and "dimension_scores" in ai_result:
                ai_scores = ai_result.get("dimension_scores", {})
                if dim_key in ai_scores:
                    ai_dim = ai_scores[dim_key]
                    default_score = ai_dim.get("score", 50)
                    default_notes = ai_dim.get("reasoning", "")
            
            score = st.slider(f"评分", 0, 100, default_score, key=f"score_{dim_key}")
            notes = st.text_area(f"评分说明", value=default_notes, key=f"notes_{dim_key}", placeholder="请记录该维度的具体表现和证据...")
            
            dimension_scores[dim_key] = {
                "score": score,
                "notes": notes
            }
    
    # 快速判断清单
    st.subheader("4️⃣ 快速判断清单")
    st.caption("面试结束后，回答以下5个问题")
    
    # 如果有 AI 分析结果，自动填充
    ai_result = st.session_state.ai_analysis_result
    checklist_results = {}
    
    for i, item in enumerate(QUICK_CHECKLIST, 1):
        default_checked = False
        if ai_result and "quick_checklist" in ai_result:
            checklist_mapping = {
                1: "ai_first_response",
                2: "own_methodology",
                3: "workflow_reformed",
                4: "specific_complaints",
                5: "ai_anxiety"
            }
            ai_check = ai_result["quick_checklist"].get(checklist_mapping.get(i), False)
            default_checked = ai_check
        
        result = st.checkbox(f"{i}. {item}", value=default_checked, key=f"check_{i}")
        checklist_results[f"check_{i}"] = result
    
    # 综合评价
    st.subheader("5️⃣ 综合评价")
    
    # 如果有 AI 分析结果，自动填充
    default_overall = ""
    if ai_result and "overall_assessment" in ai_result:
        default_overall = ai_result.get("overall_assessment", "")
    
    overall_notes = st.text_area("综合评价与建议", value=default_overall, placeholder="请记录对该候选人的整体评价、优势和顾虑...", key="overall_notes")
    
    # 计算并保存
    if st.button("💾 保存评估", type="primary"):
        name = st.session_state.get("input_name", name)
        position = st.session_state.get("input_position", position)
        
        if not name or not position:
            st.error("❌ 请填写候选人姓名和应聘职位")
        else:
            # 计算分数
            scores_only = {k: v["score"] for k, v in dimension_scores.items()}
            total_score = calculate_score(scores_only)
            level = calculate_level(total_score)
            
            # 保存简历文件
            resume_filename = None
            if resume_file:
                resume_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}_{resume_file.name}"
                with open(RESUMES_DIR / resume_filename, 'wb') as f:
                    f.write(resume_file.getvalue())
            
            # 创建候选人记录
            candidate_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}"
            candidate_data = {
                "id": candidate_id,
                "name": name,
                "position": position,
                "email": st.session_state.get("input_email", email),
                "phone": st.session_state.get("input_phone", phone),
                "resume_filename": resume_filename,
                "resume_text": resume_text if resume_text else "",
                "dimensions": dimension_scores,
                "checklist": checklist_results,
                "overall_notes": overall_notes,
                "total_score": total_score,
                "level": level,
                "ai_analysis": st.session_state.ai_analysis_result,  # 保存 AI 分析结果
                "eval_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "created_at": datetime.now().isoformat()
            }
            
            # 保存到 session state 和文件
            st.session_state.candidates[candidate_id] = candidate_data
            save_candidates(st.session_state.candidates)
            
            st.success(f"✅ 评估已保存！候选人 {name} 的 AI Native 等级为: {LEVEL_DEFINITIONS[level]['name']} ({total_score}分)")
            
            # 清除 AI 分析结果
            st.session_state.ai_analysis_result = None
            
            # 显示结果预览
            st.balloons()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="score-card"><div class="score-value">{total_score}</div><div>AI Native 综合得分</div></div>', unsafe_allow_html=True)
            with col2:
                color = get_level_color(level)
                st.markdown(f'<div class="score-card" style="background: {color}"><div class="score-value">{level}</div><div>{LEVEL_DEFINITIONS[level]["name"]}</div></div>', unsafe_allow_html=True)

elif page == "📊 候选人对比":
    st.markdown('<div class="main-header">候选人对比分析</div>', unsafe_allow_html=True)
    
    candidates = st.session_state.candidates
    
    if len(candidates) < 2:
        st.info("📊 请至少添加2个候选人后才能使用对比功能")
    else:
        # 选择要对比的候选人
        candidate_names = {cid: f"{c['name']} ({c.get('level', 'L0')})" for cid, c in candidates.items()}
        selected = st.multiselect("选择要对比的候选人（最多5人）", list(candidate_names.keys()), format_func=lambda x: candidate_names[x], max_selections=5)
        
        if len(selected) >= 2:
            # 对比表格
            st.subheader("📊 综合对比")
            
            comparison_data = []
            for cid in selected:
                c = candidates[cid]
                row = {
                    "候选人": c['name'],
                    "等级": c.get('level', 'L0'),
                    "总分": c.get('total_score', 0),
                    "职位": c.get('position', '-'),
                    "评估日期": c.get('eval_date', '-')
                }
                # 添加各维度分数
                for dim_key in AI_NATIVE_DIMENSIONS.keys():
                    dim_score = c.get('dimensions', {}).get(dim_key, {}).get('score', 0)
                    row[AI_NATIVE_DIMENSIONS[dim_key]['name']] = dim_score
                
                comparison_data.append(row)
            
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)
            
            # 雷达图对比
            st.subheader("🕸️ 六维能力雷达图对比")
            
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            colors = ['#667eea', '#11998e', '#fc466b', '#3f5aa6', '#f093fb']
            
            for idx, cid in enumerate(selected):
                c = candidates[cid]
                values = []
                for dim_key in AI_NATIVE_DIMENSIONS.keys():
                    score = c.get('dimensions', {}).get(dim_key, {}).get('score', 0)
                    values.append(score)
                values.append(values[0])  # 闭合图形
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=[info['name'] for info in AI_NATIVE_DIMENSIONS.values()] + [list(AI_NATIVE_DIMENSIONS.values())[0]['name']],
                    fill='toself',
                    name=c['name'],
                    line=dict(color=colors[idx % len(colors)])
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 详细对比
            st.subheader("📝 详细评估对比")
            
            for cid in selected:
                c = candidates[cid]
                with st.expander(f"📋 {c['name']} - {LEVEL_DEFINITIONS[c.get('level', 'L0')]['name']}"):
                    st.write(f"**总分:** {c.get('total_score', 0)}分")
                    st.write(f"**综合评价:** {c.get('overall_notes', '无')}")
                    
                    st.write("**各维度评分:**")
                    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
                        dim_data = c.get('dimensions', {}).get(dim_key, {})
                        score = dim_data.get('score', 0)
                        notes = dim_data.get('notes', '')
                        st.write(f"- {dim_info['name']}: {score}分 - {notes}")
        else:
            st.info("👆 请选择至少2个候选人进行对比")

elif page == "📖 评分标准":
    st.markdown('<div class="main-header">AI Native 人才评分标准</div>', unsafe_allow_html=True)
    
    # 等级定义
    st.subheader("🎯 等级定义")
    
    for level, info in LEVEL_DEFINITIONS.items():
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f'<div class="level-badge" style="background-color: {info["color"]}">{info["name"]}</div>', unsafe_allow_html=True)
                st.write(f"分数范围: {info['score_range'][0]}-{info['score_range'][1]}分")
            with col2:
                st.write(info['description'])
            st.divider()
    
    # 六维评分标准
    st.subheader("📊 六维评分标准")
    
    for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
        with st.expander(f"📈 {dim_info['name']} (权重: {dim_info['weight']})"):
            st.write(f"**定义:** {dim_info['description']}")
            st.write("**关键信号:**")
            for signal in dim_info['signals']:
                st.markdown(f'<span class="signal-item">{signal}</span>', unsafe_allow_html=True)
            
            st.write("**评分参考:**")
            st.write("- 0-20分: 未表现出该特征")
            st.write("- 21-40分: 偶尔表现出该特征")
            st.write("- 41-60分: 经常表现出该特征")
            st.write("- 61-80分: 系统性展现该特征")
            st.write("- 81-100分: 该特征的典范，能输出方法论")
    
    # 快速判断清单
    st.subheader("✅ 快速判断清单")
    st.write("面试结束后，回答以下5个问题，即可快速判定:")
    
    for i, item in enumerate(QUICK_CHECKLIST, 1):
        st.markdown(f'<div class="checklist-item">{i}. {item}</div>', unsafe_allow_html=True)
    
    st.write("**评分规则:**")
    st.write("- 5条全中 → 强烈的 L2/L3")
    st.write("- 中3-4条 → L1+，有潜力到L2")
    st.write("- 中1-2条 → L0，仅停留在偶尔使用")
    st.write("- 0条 → 未入门")

# 候选人详情弹窗
if st.session_state.current_candidate:
    cid = st.session_state.current_candidate
    if cid in st.session_state.candidates:
        c = st.session_state.candidates[cid]
        
        st.markdown("---")
        st.subheader(f"📋 {c['name']} - 详细评估报告")
        
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
        values = []
        for dim_key in AI_NATIVE_DIMENSIONS.keys():
            score = c.get('dimensions', {}).get(dim_key, {}).get('score', 0)
            values.append(score)
        values.append(values[0])
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=c['name']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # AI 分析结果（如果有）
        ai_analysis = c.get('ai_analysis')
        if ai_analysis:
            with st.expander("🤖 查看 AI 分析报告"):
                render_ai_analysis_result(ai_analysis)
        
        # 各维度详情
        st.subheader("📊 各维度评分详情")
        for dim_key, dim_info in AI_NATIVE_DIMENSIONS.items():
            dim_data = c.get('dimensions', {}).get(dim_key, {})
            score = dim_data.get('score', 0)
            notes = dim_data.get('notes', '')
            
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**{dim_info['name']}**")
                    st.write(f"{score}分")
                with col2:
                    st.write(notes if notes else "无评分说明")
                st.divider()
        
        # 快速判断清单结果
        st.subheader("✅ 快速判断清单")
        checklist = c.get('checklist', {})
        passed = sum(1 for v in checklist.values() if v)
        st.write(f"通过项目: {passed}/5")
        
        for i, item in enumerate(QUICK_CHECKLIST, 1):
            checked = checklist.get(f"check_{i}", False)
            icon = "✅" if checked else "❌"
            st.write(f"{icon} {item}")
        
        # 综合评价
        st.subheader("📝 综合评价")
        st.write(c.get('overall_notes', '无综合评价'))
        
        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("关闭详情"):
                st.session_state.current_candidate = None
                st.rerun()
        with col2:
            if st.button("🗑️ 删除此候选人", type="secondary"):
                del st.session_state.candidates[cid]
                save_candidates(st.session_state.candidates)
                st.session_state.current_candidate = None
                st.rerun()
    else:
        st.session_state.current_candidate = None
