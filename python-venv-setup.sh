#!/bin/bash
# 完全关闭严格模式，适配Git Bash/MINGW64
set +euo pipefail

# 配置项（可自定义项目名称）
PROJECT_NAME="PyVenvKit"

# 颜色定义（美化输出）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 重置颜色

# 全局变量初始化
PYTHON_VERSIONS=()
PYTHON_PATHS=()

# 主菜单函数
show_main_menu() {
    clear
    echo -e "${BLUE}========================================"
    echo -e "      ${PROJECT_NAME} - Python环境脚手架"
    echo -e "========================================${NC}"
    echo "1. 列出并选择Python版本创建虚拟环境"
    echo "2. 安装requirements.txt依赖"
    echo "3. 初始化Git仓库（生成.gitignore）"
    echo "4. 自动创建并关联GitHub远程仓库"
    echo "5. 退出"
    echo -e "${YELLOW}请输入选项（1/2/3/4/5）：${NC}"
    read -r choice

    case $choice in
        1)
            create_venv
            ;;
        2)
            install_dependencies
            ;;
        3)
            init_git_repo
            ;;
        4)
            create_and_link_github_repo
            ;;
        5)
            echo -e "${GREEN}退出脚本，再见！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请输入1-5！${NC}"
            sleep 2
            show_main_menu
            ;;
    esac
}

# 1. 创建虚拟环境（保留原有逻辑）
create_venv() {
    clear
    echo -e "${BLUE}========== 检测本地Python版本 ==========${NC}"
    
    # 重置版本列表
    PYTHON_VERSIONS=()
    PYTHON_PATHS=()

    # 第一步：检测系统PATH中的python/python3命令（核心逻辑）
    for cmd in python python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            cmd_path=$(command -v "$cmd")
            # 捕获版本输出
            version_output=$("$cmd_path" --version 2>&1)
            if [[ $version_output =~ Python\ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
                full_version=${BASH_REMATCH[1]}
                # 手动去重（不用关联数组，兼容Git Bash）
                if ! [[ " ${PYTHON_PATHS[@]} " =~ " $cmd_path " ]]; then
                    PYTHON_VERSIONS+=("$cmd (路径: $cmd_path, 版本: $full_version)")
                    PYTHON_PATHS+=("$cmd_path")
                fi
            fi
        fi
    done

    # 第二步：扫描Windows常见Python路径（适配Git Bash）
    common_paths=(
        "/c/Program Files/Python*/python.exe"
        "/c/Program Files (x86)/Python*/python.exe"
        "/c/Python*/python.exe"
        "$HOME/AppData/Local/Programs/Python*/python.exe"
    )
    # 遍历路径，避免ls报错
    for path_pattern in "${common_paths[@]}"; do
        # 用通配符匹配文件，兼容Git Bash
        for file in $path_pattern; do
            if [ -x "$file" ] && [ -f "$file" ]; then
                version_output=$("$file" --version 2>&1)
                if [[ $version_output =~ Python\ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
                    full_version=${BASH_REMATCH[1]}
                    # 手动去重
                    if ! [[ " ${PYTHON_PATHS[@]} " =~ " $file " ]]; then
                        PYTHON_VERSIONS+=("$(basename "$file") (路径: $file, 版本: $full_version)")
                        PYTHON_PATHS+=("$file")
                    fi
                fi
            fi
        done
    done

    # 处理未找到Python的情况
    if [ ${#PYTHON_VERSIONS[@]} -eq 0 ]; then
        echo -e "${RED}错误：未检测到任何Python版本！${NC}"
        echo -e "${YELLOW}当前系统python命令检测结果：${NC}"
        python --version 2>&1 || echo "python命令不存在"
        python3 --version 2>&1 || echo "python3命令不存在"
        sleep 3
        show_main_menu
        return
    fi

    # 列出可用版本
    echo -e "${GREEN}已检测到以下Python版本：${NC}"
    for i in "${!PYTHON_VERSIONS[@]}"; do
        echo "$((i+1)). ${PYTHON_VERSIONS[$i]}"
    done

    # 选择Python版本
    echo -e "${YELLOW}请选择要使用的Python版本（输入数字）：${NC}"
    read -r version_choice

    # 验证输入
    if ! [[ $version_choice =~ ^[0-9]+$ ]] || [ "$version_choice" -lt 1 ] || [ "$version_choice" -gt ${#PYTHON_VERSIONS[@]} ]; then
        echo -e "${RED}无效选择，请输入正确的数字！${NC}"
        sleep 2
        create_venv
        return
    fi

    # 获取选中的Python路径
    selected_python=${PYTHON_PATHS[$((version_choice-1))]}
    echo -e "${BLUE}你选择了：${PYTHON_VERSIONS[$((version_choice-1))]}${NC}"

    # 创建虚拟环境（venv）
    echo -e "${BLUE}正在创建虚拟环境...${NC}"
    venv_output=$("$selected_python" -m venv venv 2>&1)
    if [ $? -ne 0 ]; then
        echo -e "${RED}创建虚拟环境失败！${NC}"
        echo -e "${YELLOW}错误详情：${venv_output}${NC}"
        echo -e "${BLUE}请检查：1. Python版本是否≥3.3 2. 是否安装了venv模块${NC}"
        sleep 3
        show_main_menu
        return
    fi

    # 创建requirements.txt（如果不存在）
    if [ ! -f "requirements.txt" ]; then
        touch requirements.txt
        echo -e "${GREEN}已创建空的requirements.txt文件，请先编辑依赖后再安装！${NC}"
    else
        echo -e "${YELLOW}requirements.txt已存在，跳过创建${NC}"
    fi

    # 自动将venv添加到.gitignore（无论是否已存在.gitignore）
    echo -e "${BLUE}正在将venv目录加入.gitignore...${NC}"
    if [ -f ".gitignore" ]; then
        # 检查是否已包含venv，未包含则追加
        if ! grep -q "^venv/" .gitignore; then
            echo -e "\n# Python虚拟环境" >> .gitignore
            echo "venv/" >> .gitignore
            echo -e "${GREEN}已将venv/追加到现有.gitignore文件！${NC}"
        else
            echo -e "${YELLOW}venv/已存在于.gitignore中，无需重复添加！${NC}"
        fi
    else
        # 无.gitignore则创建并添加venv规则
        cat > .gitignore << 'EOF'
# Python虚拟环境
venv/
env/
*.env

# 日志文件
logs/
*.log
*.log.*

# Python编译文件
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 操作系统文件
.DS_Store
Thumbs.db
*.swp
*.swo
EOF
        echo -e "${GREEN}已创建.gitignore并添加venv/忽略规则！${NC}"
    fi

    echo -e "${GREEN}✅ 虚拟环境创建完成！venv目录已生成${NC}"
    sleep 2
    show_main_menu
}

# 2. 安装requirements.txt依赖（无修改）
install_dependencies() {
    clear
    echo -e "${BLUE}========== 安装Python依赖 ==========${NC}"

    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}错误：当前目录未找到requirements.txt文件！${NC}"
        sleep 2
        show_main_menu
        return
    fi

    # 检查requirements.txt是否为空
    if [ ! -s "requirements.txt" ]; then
        echo -e "${YELLOW}警告：requirements.txt文件为空，无法安装依赖！${NC}"
        echo -e "${BLUE}请先编辑requirements.txt添加需要的依赖后重试${NC}"
        sleep 3
        show_main_menu
        return
    fi

    # 检查虚拟环境是否存在
    if [ ! -d "venv" ]; then
        echo -e "${RED}错误：未检测到虚拟环境（venv目录），请先创建虚拟环境！${NC}"
        sleep 2
        show_main_menu
        return
    fi

    # 激活虚拟环境并安装依赖（兼容Windows Git Bash）
    echo -e "${BLUE}正在激活虚拟环境并安装依赖...${NC}"
    activate_script=""
    if [ -f "venv/bin/activate" ]; then
        activate_script="venv/bin/activate"
    elif [ -f "venv/Scripts/activate" ]; then
        activate_script="venv/Scripts/activate"
    else
        echo -e "${RED}错误：未找到虚拟环境激活脚本！${NC}"
        sleep 2
        show_main_menu
        return
    fi

    # 激活并安装依赖
    source "$activate_script"
    # 强制指定pip路径，避免环境问题
    pip_path=$(command -v pip)
    $pip_path install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    $pip_path install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

    echo -e "${GREEN}✅ 依赖安装完成！${NC}"
    deactivate
    sleep 2
    show_main_menu
}

# 3. 初始化Git仓库（保留venv检查逻辑）
init_git_repo() {
    clear
    echo -e "${BLUE}========== 初始化Git仓库 ==========${NC}"

    # 检查是否已安装Git
    if ! command -v git >/dev/null 2>&1; then
        echo -e "${RED}错误：未检测到Git，请先安装Git！${NC}"
        sleep 3
        show_main_menu
        return
    fi

    # 检查当前目录是否已初始化Git
    if [ -d ".git" ]; then
        echo -e "${YELLOW}警告：当前目录已存在Git仓库，无需重复初始化！${NC}"
        
        # 检查现有.gitignore是否包含venv
        if [ -f ".gitignore" ]; then
            echo -e "${BLUE}正在检查.gitignore中是否包含venv规则...${NC}"
            if ! grep -q "^venv/" .gitignore; then
                echo -e "\n# Python虚拟环境" >> .gitignore
                echo "venv/" >> .gitignore
                echo -e "${GREEN}已将venv/追加到现有.gitignore文件！${NC}"
            else
                echo -e "${YELLOW}venv/已存在于.gitignore中，无需重复添加！${NC}"
            fi
        else
            # 无.gitignore则创建（包含venv）
            echo -e "${BLUE}未找到.gitignore文件，正在创建并添加venv规则...${NC}"
            cat > .gitignore << 'EOF'
# Python虚拟环境
venv/
env/
*.env

# 日志文件
logs/
*.log
*.log.*

# Python编译文件
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 操作系统文件
.DS_Store
Thumbs.db
*.swp
*.swo
EOF
            echo -e "${GREEN}已创建.gitignore并添加venv/忽略规则！${NC}"
        fi
        
        sleep 3
        show_main_menu
        return
    fi

    # 初始化Git仓库
    echo -e "${BLUE}正在初始化Git仓库...${NC}"
    git init >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Git仓库初始化失败！${NC}"
        sleep 2
        show_main_menu
        return
    fi

    # 处理.gitignore文件
    echo -e "${BLUE}正在生成/检查.gitignore文件...${NC}"
    if [ -f ".gitignore" ]; then
        # 若已有.gitignore，检查并补充venv规则
        echo -e "${YELLOW}检测到已有.gitignore文件，检查venv规则...${NC}"
        if ! grep -q "^venv/" .gitignore; then
            echo -e "\n# Python虚拟环境" >> .gitignore
            echo "venv/" >> .gitignore
            echo -e "${GREEN}已将venv/追加到现有.gitignore文件！${NC}"
        else
            echo -e "${YELLOW}venv/已存在于.gitignore中，无需重复添加！${NC}"
        fi
    else
        # 无.gitignore则创建完整规则（包含venv）
        cat > .gitignore << 'EOF'
# Python虚拟环境
venv/
env/
*.env

# 日志文件
logs/
*.log
*.log.*

# Python编译文件
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 操作系统文件
.DS_Store
Thumbs.db
*.swp
*.swo
EOF
        echo -e "${GREEN}已生成Python项目专用.gitignore文件！${NC}"
    fi

    echo -e "${GREEN}✅ Git仓库初始化完成！${NC}"
    echo -e "${BLUE}已确保.gitignore包含：${NC}"
    echo "  - 虚拟环境目录（venv/）"
    echo "  - 日志文件（logs/、*.log）"
    echo "  - Python编译文件（__pycache__/）"
    echo "  - 操作系统临时文件（.DS_Store/Thumbs.db）"
    sleep 3
    show_main_menu
}

# 4. 新增：自动创建并关联GitHub远程仓库
create_and_link_github_repo() {
    clear
    echo -e "${BLUE}========== 自动创建并关联GitHub仓库 ==========${NC}"

    # 前置校验1：检查Git是否安装
    if ! command -v git >/dev/null 2>&1; then
        echo -e "${RED}错误：未检测到Git，请先安装Git！${NC}"
        sleep 3
        show_main_menu
        return
    fi

    # 前置校验2：检查GitHub CLI（gh）是否安装
    if ! command -v gh >/dev/null 2>&1; then
        echo -e "${YELLOW}未检测到GitHub CLI（gh），正在提示安装步骤...${NC}"
        echo -e "${BLUE}安装指南：${NC}"
        echo "  1. Windows：winget install GitHub.cli"
        echo "  2. macOS：brew install gh"
        echo "  3. Linux：参考 https://github.com/cli/cli#installation"
        echo -e "${RED}安装完成后需执行：gh auth login 登录GitHub账号${NC}"
        sleep 5
        show_main_menu
        return
    fi

    # 前置校验3：检查gh是否已登录
    if ! gh auth status >/dev/null 2>&1; then
        echo -e "${RED}错误：GitHub CLI未登录！请先执行 gh auth login 完成登录${NC}"
        sleep 3
        show_main_menu
        return
    fi

    # 前置校验4：确保本地Git仓库已初始化
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}本地未初始化Git仓库，正在自动初始化...${NC}"
        git init >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo -e "${RED}Git仓库初始化失败，无法继续！${NC}"
            sleep 2
            show_main_menu
            return
        fi
        echo -e "${GREEN}本地Git仓库初始化完成！${NC}"
    fi

    # 步骤1：输入GitHub用户名
    echo -e "${YELLOW}请输入你的GitHub用户名：${NC}"
    read -r github_username
    if [ -z "$github_username" ]; then
        echo -e "${RED}错误：用户名不能为空！${NC}"
        sleep 2
        create_and_link_github_repo
        return
    fi

    # 步骤2：检查远程仓库是否已存在
    echo -e "${BLUE}正在检查GitHub仓库 ${github_username}/${PROJECT_NAME} 是否存在...${NC}"
    repo_exists=$(gh repo view "${github_username}/${PROJECT_NAME}" >/dev/null 2>&1; echo $?)

    if [ $repo_exists -eq 0 ]; then
        # 仓库已存在：直接关联
        echo -e "${YELLOW}仓库 ${github_username}/${PROJECT_NAME} 已存在，直接关联...${NC}"
        repo_url="https://github.com/${github_username}/${PROJECT_NAME}.git"
        
        # 关联远程仓库（已存在则更新地址）
        git remote add origin "$repo_url" >/dev/null 2>&1 || git remote set-url origin "$repo_url" >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 成功关联已存在的GitHub仓库：${repo_url}${NC}"
        else
            echo -e "${RED}关联失败：请手动检查仓库地址或网络！${NC}"
        fi
    else
        # 仓库不存在：创建后关联
        echo -e "${BLUE}仓库 ${github_username}/${PROJECT_NAME} 不存在，正在创建...${NC}"
        # 创建公共仓库（如需私有，添加 --private 参数）
        create_output=$(gh repo create "${PROJECT_NAME}" --public --description "Python virtual environment scaffold" --confirm)
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ GitHub仓库 ${github_username}/${PROJECT_NAME} 创建成功！${NC}"
            # 获取仓库地址并关联
            repo_url="https://github.com/${github_username}/${PROJECT_NAME}.git"
            git remote add origin "$repo_url" >/dev/null 2>&1
            echo -e "${GREEN}✅ 成功关联新建的GitHub仓库：${repo_url}${NC}"
        else
            echo -e "${RED}仓库创建失败！错误信息：${create_output}${NC}"
            sleep 3
            show_main_menu
            return
        fi
    fi

    # 验证最终关联结果
    echo -e "${BLUE}当前远程仓库配置：${NC}"
    git remote -v
    sleep 4
    show_main_menu
}

# 脚本入口
echo -e "${GREEN}欢迎使用${PROJECT_NAME}！${NC}"
sleep 1
show_main_menu