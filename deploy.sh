#!/bin/bash

# WhatsApp 訂單機器人 - 部署助手
# 這個腳本會指導你完成部署過程

set -e

echo "🚀 WhatsApp 訂單機器人部署助手"
echo "======================================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查函數
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}錯誤：未找到 $1 命令${NC}"
        echo "請先安裝 $1"
        exit 1
    fi
    echo -e "${GREEN}✓ 找到 $1${NC}"
}

# 步驟 1：檢查環境
echo ""
echo "📋 步驟 1：檢查環境"
echo "------------------"
check_command git
check_command python3
check_command docker
check_command curl

# 檢查 Python 版本
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$python_version >= 3.11" | bc -l) -eq 1 ]]; then
    echo -e "${GREEN}✓ Python 版本 $python_version（需要 3.11+）${NC}"
else
    echo -e "${YELLOW}⚠ Python 版本 $python_version（建議 3.11+）${NC}"
fi

# 步驟 2：檢查項目文件
echo ""
echo "📋 步驟 2：檢查項目文件"
echo "------------------"

required_files=(
    "app/main.py"
    "app/models.py"
    "app/database.py"
    "requirements.txt"
    "render.yaml"
    ".env.example"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ 缺少文件：$file${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo -e "${RED}錯誤：項目文件不完整${NC}"
    exit 1
fi

# 步驟 3：檢查環境變量配置
echo ""
echo "📋 步驟 3：檢查環境變量配置"
echo "------------------"
echo "請確保你已準備好以下服務的帳號和憑證："
echo "1. ${GREEN}Twilio${NC} (WhatsApp Business API)"
echo "2. ${GREEN}Render${NC} (應用部署平台)"
echo "3. ${GREEN}Cloudinary${NC} (圖片儲存服務)"
echo "4. ${GREEN}GitHub${NC} (代碼託管)"
echo ""
read -p "是否已準備好所有帳號？(y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}請先註冊所需服務：${NC}"
    echo "1. Twilio: https://twilio.com"
    echo "2. Render: https://render.com"
    echo "3. Cloudinary: https://cloudinary.com"
    echo "4. GitHub: https://github.com"
    exit 1
fi

# 步驟 4：選擇部署方式
echo ""
echo "📋 步驟 4：選擇部署方式"
echo "------------------"
echo "1) 完整部署（推送到 GitHub + 部署到 Render）"
echo "2) 僅本地測試（使用 Docker Compose）"
echo "3) 查看詳細部署指南"
read -p "請選擇 (1-3): " deploy_option

case $deploy_option in
    1)
        echo -e "${GREEN}選擇完整部署${NC}"
        
        # 檢查 Git 倉庫狀態
        if [ ! -d ".git" ]; then
            echo "初始化 Git 倉庫..."
            git init
            git add .
            git commit -m "初始提交：WhatsApp訂單機器人"
        fi
        
        echo ""
        echo "📤 請將代碼推送到 GitHub："
        echo "1. 在 GitHub 創建新倉庫：https://github.com/new"
        echo "2. 不要初始化 README、.gitignore 或 license"
        echo "3. 複製倉庫 URL（格式：https://github.com/你的用戶名/whatsapp-order-bot.git）"
        echo ""
        read -p "請輸入 GitHub 倉庫 URL: " github_url
        
        if [[ -n "$github_url" ]]; then
            echo "添加遠程倉庫..."
            git remote remove origin 2>/dev/null || true
            git remote add origin "$github_url"
            git branch -M main
            
            echo "推送代碼到 GitHub..."
            git push -u origin main
            
            echo -e "${GREEN}✓ 代碼已推送到 GitHub${NC}"
        else
            echo -e "${YELLOW}⚠ 跳過 GitHub 推送${NC}"
        fi
        
        echo ""
        echo "🚀 部署到 Render："
        echo "1. 登錄 Render：https://dashboard.render.com"
        echo "2. 點擊「New +」→「Blueprint」"
        echo "3. 連接你的 GitHub 倉庫"
        echo "4. 應用名稱：whatsapp-order-bot"
        echo "5. 點擊「Apply」開始部署"
        echo ""
        echo "部署完成後，請執行以下配置："
        echo "1. 在 Render 設置環境變量（TWILIO_ACCOUNT_SID、TWILIO_AUTH_TOKEN、CLOUDINARY_URL）"
        echo "2. 在 Twilio Console 設置 Webhook URL"
        echo ""
        echo "詳細步驟請參考 DEPLOYMENT.md 文件"
        ;;
    
    2)
        echo -e "${GREEN}選擇本地測試${NC}"
        
        # 檢查 Docker Compose
        if ! docker-compose version &> /dev/null; then
            echo -e "${YELLOW}警告：未找到 docker-compose，嘗試使用 docker compose${NC}"
            if ! docker compose version &> /dev/null; then
                echo -e "${RED}錯誤：未找到 Docker Compose${NC}"
                exit 1
            fi
            DOCKER_COMPOSE="docker compose"
        else
            DOCKER_COMPOSE="docker-compose"
        fi
        
        echo "創建環境變量文件..."
        if [ ! -f ".env" ]; then
            cp .env.example .env
            echo -e "${YELLOW}⚠ 請編輯 .env 文件，填入你的配置${NC}"
            echo "需要設置："
            echo "  - TWILIO_ACCOUNT_SID"
            echo "  - TWILIO_AUTH_TOKEN"
            echo "  - CLOUDINARY_URL"
            read -p "按 Enter 繼續..." </dev/tty
        fi
        
        echo "啟動 Docker 服務..."
        $DOCKER_COMPOSE up -d
        
        echo -e "${GREEN}✓ 本地服務已啟動${NC}"
        echo ""
        echo "可用服務："
        echo "1. 主應用：http://localhost:8000"
        echo "2. API 文檔：http://localhost:8000/docs"
        echo "3. PostgreSQL：localhost:5432"
        echo "4. pgAdmin（可選）：http://localhost:5050"
        echo ""
        echo "停止服務：docker-compose down"
        ;;
    
    3)
        echo -e "${GREEN}部署指南${NC}"
        echo ""
        echo "詳細部署步驟請查看："
        echo "1. DEPLOYMENT.md - 完整部署指南"
        echo "2. README.md - 項目文檔"
        echo ""
        echo "快速開始："
        echo "1. 推送代碼到 GitHub"
        echo "2. 在 Render 創建 Blueprint"
        echo "3. 配置環境變量"
        echo "4. 設置 Twilio Webhook"
        ;;
    
    *)
        echo -e "${RED}無效選擇${NC}"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "🎉 部署助手完成"
echo ""
echo "需要更多幫助？"
echo "1. 查看 DEPLOYMENT.md 獲取詳細指南"
echo "2. 運行測試：python -m pytest tests/（如果存在）"
echo "3. 檢查日誌：docker-compose logs -f app"
echo ""
echo "祝你部署順利！🚀"