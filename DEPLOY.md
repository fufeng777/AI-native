# 🚀 AI Native 人才简历分析看板 - 部署指南

本指南将帮助你将看板部署到 Streamlit Cloud，使其可以通过网页访问。

---

## 📋 部署前准备

### 1. 获取阿里云 DashScope API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.aliyun.com)
2. 注册/登录阿里云账号
3. 进入「API-KEY管理」，创建新的 API Key
4. 复制 API Key 并妥善保存

> 💡 **新手福利**: 新用户有 100万次免费调用额度

---

## 🖥️ 方案一：部署到 Streamlit Cloud（免费，推荐）

### 第一步：创建 GitHub 仓库

1. **登录 GitHub**
   - 访问 [github.com](https://github.com)
   - 登录你的账号（没有账号请先注册）

2. **创建新仓库**
   - 点击右上角「+」→「New repository」
   - 填写信息：
     - Repository name: `ai-native-resume-analyzer`
     - Description: `AI Native 人才简历分析看板`
     - 选择「Public」（Streamlit Cloud 需要公开仓库）
     - 勾选「Add a README file」
   - 点击「Create repository」

3. **上传代码**
   - 在仓库页面，点击「uploading an existing file」
   - 将项目中的所有文件拖拽上传：
     ```
     ai_native_resume_analyzer/
     ├── app.py
     ├── ai_analyzer.py
     ├── requirements.txt
     ├── .streamlit/
     │   └── config.toml
     └── README.md
     ```
   - 点击「Commit changes」

### 第二步：部署到 Streamlit Cloud

1. **访问 Streamlit Cloud**
   - 打开 [share.streamlit.io](https://share.streamlit.io)
   - 点击「Sign up」注册账号
   - 推荐使用 GitHub 账号登录

2. **关联 GitHub**
   - 首次使用需要授权 GitHub 访问
   - 选择刚才创建的仓库

3. **配置部署**
   - App file: `app.py`
   - Branch: `main`
   - 点击「Deploy!」

### 第三步：配置环境变量

1. **进入应用设置**
   - 部署完成后，点击应用右上角「Settings」

2. **添加 Secrets**
   - 在「Secrets」中添加：
   ```
   DASHSCOPE_API_KEY = "你的API Key"
   ```
   - 点击「Save」

3. **重新部署**
   - Streamlit Cloud 会自动检测更改并重新部署

### 第四步：访问应用

部署成功后，你会获得一个类似这样的链接：
```
https://your-app-name.streamlit.app
```

现在可以通过这个链接访问你的看板了！

---

## 🖥️ 方案二：本地运行

如果暂时不想部署，可以本地运行：

### 方式一：使用启动脚本（Windows）

1. 双击 `启动看板.bat`
2. 等待依赖安装完成
3. 浏览器自动打开 http://localhost:8501

### 方式二：命令行启动

```bash
# 进入项目目录
cd ai_native_resume_analyzer

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

### 配置本地 API Key

**方式 A: 环境变量**
```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="你的API Key"

# Windows CMD
set DASHSCOPE_API_KEY=你的API Key

# 启动
streamlit run app.py
```

**方式 B: 界面配置**
1. 打开应用
2. 进入「➕ 新增评估」页面
3. 找到「🤖 AI 分析设置」
4. 输入 API Key 并保存

---

## ⚙️ 功能说明

### AI 分析功能

看板已集成 AI 智能分析功能：

1. **上传简历**
   - 支持 PDF、DOCX、TXT 格式
   - PDF 文件会被自动提取文本

2. **AI 自动分析**
   - 点击「🔍 使用 AI 分析简历」按钮
   - AI 会自动分析简历，给出：
     - 六维评分（带权重计算）
     - 快速判断清单结果
     - 综合评价
     - 面试建议

3. **人工复核**
   - AI 分析结果会自动填充到评分表单
   - 招聘人员可以调整评分
   - 最终以人工评分结果为准

### 数据存储

- **本地运行**: 数据保存在 `data/candidates.json`
- **Streamlit Cloud**: 数据存储在浏览器的 Session 中（每次刷新会重置）
  - 💡 **重要**: 部署到云端后，建议定期导出数据

### 导出数据

如果需要保留数据，可以：

1. 打开应用，进入候选人详情
2. 手动复制评估结果
3. 或者修改代码添加导出功能

---

## 🔧 常见问题

### Q1: 部署失败怎么办？

**检查项：**
1. GitHub 仓库是否设置为 Public
2. requirements.txt 是否正确
3. .streamlit/config.toml 是否存在
4. 查看 Streamlit Cloud 的部署日志

### Q2: AI 分析功能无法使用？

**检查项：**
1. 是否正确配置了 `DASHSCOPE_API_KEY`
2. API Key 是否有效
3. 是否有免费额度

### Q3: 如何更新已部署的应用？

只需将新代码推送到 GitHub 仓库，Streamlit Cloud 会自动重新部署。

```bash
git add .
git commit -m "更新说明"
git push origin main
```

### Q4: 如何修改应用名称？

在 Streamlit Cloud 的应用设置中，可以修改 App URL 的前缀。

---

## 📊 项目结构

```
ai_native_resume_analyzer/
├── app.py                 # 主应用文件
├── ai_analyzer.py         # AI 分析模块
├── requirements.txt       # Python 依赖
├── .streamlit/
│   └── config.toml        # Streamlit 配置
├── data/                  # 数据存储（本地）
│   ├── candidates.json
│   └── resumes/
├── 启动看板.bat          # Windows 启动脚本
├── README.md             # 使用说明
└── DEPLOY.md             # 部署指南
```

---

## 🌐 其他部署选项

### Vercel（适合前端开发者）

如果熟悉 Next.js，可以将 Streamlit 应用包装成 API：
- 使用 `streamlit-api` 或类似工具
- Vercel 部署需要付费

### 云服务器（适合企业使用）

购买云服务器（阿里云/腾讯云等）：
- 完全自主控制
- 可以连接数据库
- 支持私有化部署
- 需要服务器费用

### Docker 容器

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

---

## 📞 获取帮助

如果部署过程中遇到问题：

1. 查看 [Streamlit 官方文档](https://docs.streamlit.io/)
2. 查看 [DashScope API 文档](https://help.aliyun.com/zh/dashscope/)
3. 提交 GitHub Issue

---

**祝你部署成功！🎉**
