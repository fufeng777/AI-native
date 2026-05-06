@echo off
chcp 65001 >nul
echo ==========================================
echo   AI Native 人才简历分析看板
echo ==========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 正在检查依赖...

REM 安装依赖
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [2/3] 依赖安装完成
echo [3/3] 正在启动看板...
echo.
echo ==========================================
echo   看板启动中，请稍候...
echo   浏览器将自动打开
echo ==========================================
echo.

REM 启动 Streamlit
streamlit run app.py

pause
