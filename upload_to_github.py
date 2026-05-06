"""
GitHub 上传助手
用于将项目上传到 GitHub 仓库
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_git():
    """检查 Git 是否安装"""
    returncode, stdout, stderr = run_command("git --version")
    if returncode == 0:
        print(f"✅ Git 已安装: {stdout.strip()}")
        return True
    else:
        print("❌ Git 未安装")
        print("请访问 https://git-scm.com/download/win 下载并安装 Git")
        return False

def init_repo(project_dir):
    """初始化 Git 仓库"""
    print("\n📁 初始化 Git 仓库...")
    returncode, stdout, stderr = run_command("git init", cwd=project_dir)
    if returncode == 0:
        print("✅ Git 仓库初始化成功")
        return True
    else:
        print(f"❌ 初始化失败: {stderr}")
        return False

def config_git(project_dir, name="AI Native Analyzer", email="analyzer@example.com"):
    """配置 Git 用户信息"""
    print("\n⚙️ 配置 Git 用户信息...")
    run_command(f'git config user.name "{name}"', cwd=project_dir)
    run_command(f'git config user.email "{email}"', cwd=project_dir)
    print("✅ Git 用户配置完成")

def add_files(project_dir):
    """添加文件到暂存区"""
    print("\n📤 添加文件到暂存区...")
    returncode, stdout, stderr = run_command("git add .", cwd=project_dir)
    if returncode == 0:
        print("✅ 文件添加成功")
        return True
    else:
        print(f"❌ 添加失败: {stderr}")
        return False

def commit(project_dir, message="Initial commit"):
    """提交更改"""
    print(f"\n💾 提交更改: {message}")
    returncode, stdout, stderr = run_command(f'git commit -m "{message}"', cwd=project_dir)
    if returncode == 0:
        print("✅ 提交成功")
        return True
    else:
        print(f"❌ 提交失败: {stderr}")
        return False

def add_remote(project_dir, repo_url):
    """添加远程仓库"""
    print(f"\n🔗 添加远程仓库: {repo_url}")
    
    # 先检查是否已有远程仓库
    returncode, stdout, stderr = run_command("git remote -v", cwd=project_dir)
    if "origin" in stdout:
        print("远程仓库已存在，更新 URL...")
        returncode, stdout, stderr = run_command(f"git remote set-url origin {repo_url}", cwd=project_dir)
    else:
        returncode, stdout, stderr = run_command(f"git remote add origin {repo_url}", cwd=project_dir)
    
    if returncode == 0:
        print("✅ 远程仓库配置成功")
        return True
    else:
        print(f"❌ 配置失败: {stderr}")
        return False

def push(project_dir, branch="main"):
    """推送到远程仓库"""
    print(f"\n🚀 推送到远程仓库 ({branch})...")
    
    # 先检查分支名称
    returncode, stdout, stderr = run_command("git branch", cwd=project_dir)
    current_branch = stdout.strip().replace('* ', '')
    
    if current_branch != branch:
        # 重命名分支
        run_command(f"git branch -M {branch}", cwd=project_dir)
    
    returncode, stdout, stderr = run_command(f"git push -u origin {branch}", cwd=project_dir)
    if returncode == 0:
        print("✅ 推送成功！")
        print(f"\n🌐 仓库地址: https://github.com/fufeng777/AI-naitve-")
        return True
    else:
        print(f"❌ 推送失败: {stderr}")
        if "Authentication failed" in stderr or "403" in stderr:
            print("\n💡 提示: 需要配置 GitHub 身份验证")
            print("   方式1: 使用 Personal Access Token")
            print("   方式2: 配置 SSH 密钥")
            print("   方式3: 使用 GitHub Desktop 登录")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI Native 简历分析看板 - GitHub 上传工具")
    print("=" * 60)
    
    # 项目目录
    project_dir = Path(__file__).parent.absolute()
    print(f"\n📂 项目目录: {project_dir}")
    
    # 检查 Git
    if not check_git():
        print("\n❌ 请先安装 Git")
        input("按回车键退出...")
        return
    
    # 仓库地址
    repo_url = "https://github.com/fufeng777/AI-naitve-.git"
    
    # 初始化仓库
    if not init_repo(project_dir):
        # 可能已经初始化过了
        print("仓库可能已存在，继续...")
    
    # 配置 Git
    config_git(project_dir)
    
    # 添加文件
    if not add_files(project_dir):
        print("❌ 添加文件失败")
        input("按回车键退出...")
        return
    
    # 提交
    if not commit(project_dir, "Initial commit: AI Native 简历分析看板"):
        print("❌ 提交失败，可能没有变更")
    
    # 添加远程仓库
    if not add_remote(project_dir, repo_url):
        print("❌ 添加远程仓库失败")
        input("按回车键退出...")
        return
    
    # 推送
    if push(project_dir):
        print("\n" + "=" * 60)
        print("🎉 上传成功！")
        print("=" * 60)
        print(f"\n仓库地址: {repo_url}")
        print("\n下一步:")
        print("1. 访问 https://share.streamlit.io")
        print("2. 登录并选择这个仓库")
        print("3. 点击 Deploy 部署到云端")
    else:
        print("\n" + "=" * 60)
        print("❌ 上传失败")
        print("=" * 60)
        print("\n可能的原因:")
        print("1. GitHub 账号未登录")
        print("2. 需要配置 Personal Access Token")
        print("3. 网络连接问题")
        print("\n解决方案:")
        print("1. 使用 GitHub Desktop 登录")
        print("2. 或手动上传文件到 GitHub 网站")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
