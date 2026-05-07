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
    "L0": {"title": "AI 小白", "description": "还在用传统方式工作的你，AI的世界等待探索", "emoji": "🌱", "color": "#9CA3AF"},
    "L1": {"title": "AI 玩家", "description": "偶尔玩玩AI工具，已经尝到甜头了", "emoji": "🎮", "color": "#60A5FA"},
    "L2": {"title": "AI 高手", "description": "AI已经是你的得力助手，工作效率起飞", "emoji": "🚀", "color": "#34D399"},
    "L3": {"title": "AI 大师", "description": "AI已经融入你的血液，你就是prompt大师", "emoji": "⚡", "color": "#FBBF24"}
}

# 个人版趣味问题
FUN_QUESTIONS = [
    {"id": "q1", "dimension": "ai_first_mindset", "question": "接到新任务时，你的第一个念头是？", "options": [
        {"text": "先想以前怎么做", "score": 0}, {"text": "看看有没有现成的AI工具能用", "score": 40}, 
        {"text": "思考如何用AI来重构这个问题", "score": 80}, {"text": "这能不能用AI做成一个自动化流程", "score": 100}]},
    {"id": "q2", "dimension": "deep_collaboration", "question": "你通常怎么和AI对话？", "options": [
        {"text": "问一个问题，等答案", "score": 0}, {"text": "多轮对话，迭代优化结果", "score": 60}, {"text": "像和一个专家讨论，有来有回", "score": 100}]},
    {"id": "q3", "dimension": "problem_reframing", "question": "遇到复杂问题时，你会？", "options": [
        {"text": "按部就班一步步解决", "score": 0}, {"text": "问问AI有没有更好的方法", "score": 40},
        {"text": "让AI帮我重新定义这个问题", "score": 80}, {"text": "和AI一起头脑风暴，找出最优解", "score": 100}]},
    {"id": "q4", "dimension": "learning_mode", "question": "需要学习一项新技能时，你会？", "options": [
        {"text": "找教程视频慢慢学", "score": 0}, {"text": "让AI给我制定学习计划", "score": 50}, {"text": "用AI快速搭建脚手架，边做边学", "score": 100}]},
    {"id": "q5", "dimension": "iteration_agility", "question": "你多久会尝试一次新的AI工具？", "options": [
        {"text": "基本上不换，用习惯的就行", "score": 0}, {"text": "偶尔会尝试新的", "score": 40},
        {"text": "经常关注AI动态，会主动尝试", "score": 80}, {"text": "AI新工具发布，我都是第一批用户", "score": 100}]},
    {"id": "q6", "dimension": "boundary_awareness", "question": "你如何看待AI的局限性？", "options": [
        {"text": "AI说的就是对的", "score": 0}, {"text": "知道AI有时候会出错", "score": 30},
        {"text": "能识别AI的幻觉，会批判性使用", "score": 70}, {"text": "清楚AI的能力边界，能精准指出问题", "score": 100}]},
    {"id": "q7", "dimension": "ai_first_mindset", "question": "你会用什么词形容自己使用AI的频率？", "options": [
        {"text": "偶尔", "score": 10}, {"text": "经常", "score": 50}, {"text": "日常", "score": 80}, {"text": "离不开", "score": 100}]},
    {"id": "q8", "dimension": "deep_collaboration", "question": "你用AI做过最复杂的事情是？", "options": [
        {"text": "回答问题、写文案", "score": 20}, {"text": "写代码、调试程序", "score": 50},
        {"text": "完成一个完整的项目", "score": 80}, {"text": "构建自动化工作流，节省大量时间", "score": 100}]}
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

# CSS 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
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
def render_personal_version():
    """个人测评版本主页面"""
    
    # 欢迎页面
    if not st.session_state.personal_completed:
        st.markdown('<div class="fun-header"><div class="fun-title">AI Native 能力测试</div><div class="fun-subtitle">测测你是AI小白还是AI大师？</div></div>', unsafe_allow_html=True)
        
        # 介绍
        st.markdown("""
        <div class="info-card">
        <h3>关于这个测试</h3>
        <p>AI Native 是指把 AI 作为默认工作方式来思考和行动的能力。这个测试会从6个维度评估你在工作中使用AI的水平。</p>
        <p><strong>测试时间：</strong>约3-5分钟</p>
        <p><strong>题目数量：</strong>8道选择题</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 开始测试")
        
        # 显示问题
        answers = {}
        for q in FUN_QUESTIONS:
            st.markdown(f'<div class="quiz-card"><h4>{q["question"]}</h4></div>', unsafe_allow_html=True)
            selected = st.radio("选择你的答案", 
                               options=[o["text"] for o in q["options"]], 
                               key=f"q_{q['id']}",
                               format_func=lambda x: x)
            # 找到对应的分数
            for o in q["options"]:
                if o["text"] == selected:
                    answers[q["id"]] = {"dimension": q["dimension"], "score": o["score"]}
                    break
        
        if st.button("查看我的结果", type="primary", use_container_width=True):
            # 计算各维度分数
            dimension_scores = {}
            for q_id, ans in answers.items():
                dim = ans["dimension"]
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                dimension_scores[dim].append(ans["score"])
            
            # 平均分数
            avg_scores = {}
            for dim, scores in dimension_scores.items():
                avg_scores[dim] = sum(scores) / len(scores)
            
            # 计算总分
            total_score = calculate_score(avg_scores)
            level = calculate_level(total_score)
            
            # 保存结果
            st.session_state.personal_answers = answers
            st.session_state.personal_dimension_scores = avg_scores
            st.session_state.personal_total_score = total_score
            st.session_state.personal_level = level
            st.session_state.personal_completed = True
            st.rerun()
    
    # 结果页面
    else:
        level = st.session_state.personal_level
        total_score = st.session_state.personal_total_score
        dimension_scores = st.session_state.personal_dimension_scores
        fun_info = FUN_TITLES[level]
        
        # 结果展示
        st.markdown(f'''
        <div class="result-hero">
            <div class="result-emoji">{fun_info["emoji"]}</div>
            <div class="result-title">{fun_info["title"]}</div>
            <div class="result-score">{total_score}分</div>
            <p>{fun_info["description"]}</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # 等级说明
        st.subheader("等级说明")
        for lvl, info in FUN_TITLES.items():
            color = info["color"]
            is_current = lvl == level
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f'<div class="level-badge" style="background-color: {color}">{info["emoji"]} {info["title"]}</div>', unsafe_allow_html=True)
                with col2:
                    if is_current:
                        st.success(info["description"])
                    else:
                        st.write(info["description"])
        
        # 雷达图
        st.subheader("你的AI能力雷达图")
        import plotly.graph_objects as go
        categories = [AI_NATIVE_DIMENSIONS[dim]["name"] for dim in AI_NATIVE_DIMENSIONS.keys()]
        values = [dimension_scores.get(dim, 0) for dim in AI_NATIVE_DIMENSIONS.keys()]
        values.append(values[0])
        fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories + [categories[0]], fill='toself', 
                                              fillcolor='rgba(102, 126, 234, 0.3)',
                                              line=dict(color='rgba(102, 126, 234, 1)')))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickcolor='white'), 
                                    bgcolor='rgba(0,0,0,0)'),
                         paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(0,0,0,0)',
                         showlegend=False, height=400, font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)
        
        # 各维度详情
        st.subheader("各维度详细分析")
        dimension_colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        for i, (dim_key, dim_info) in enumerate(AI_NATIVE_DIMENSIONS.items()):
            score = dimension_scores.get(dim_key, 0)
            color = dimension_colors[i % len(dimension_colors)]
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{dim_info['name']}**")
                    st.write(f"{score}分")
                with col2:
                    st.markdown(f'<div class="dimension-bar"><div class="dimension-fill" style="width: {score}%; background: {color}"></div></div>', unsafe_allow_html=True)
                    st.caption(dim_info['description'])
        
        # 分享卡片
        st.markdown("---")
        st.markdown('<div class="share-card"><h3>分享你的结果</h3><p>我刚刚测试了 AI Native 能力，获得了 {level} 等级 ({total_score}分)！{emoji}</p></div>'.format(
            level=fun_info["title"], total_score=total_score, emoji=fun_info["emoji"]), unsafe_allow_html=True)
        
        # 重新测试按钮
        st.markdown("---")
        if st.button("重新测试", use_container_width=True):
            st.session_state.personal_answers = {}
            st.session_state.personal_completed = False
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
