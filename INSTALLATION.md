# WhatsApp 訂單機器人 - 完整安裝指南

## 📋 目錄
1. [系統需求](#系統需求)
2. [快速開始](#快速開始)
3. [後端設置](#後端設置)
4. [前端管理後台](#前端管理後台)
5. [環境配置](#環境配置)
6. [數據庫設置](#數據庫設置)
7. [本地開發](#本地開發)
8. [生產部署](#生產部署)
9. [測試驗證](#測試驗證)
10. [故障排除](#故障排除)
11. [更新維護](#更新維護)

---

## 🖥️ 系統需求

### 最低配置
- **操作系統**: Ubuntu 20.04+, macOS 10.15+, Windows 10+ (WSL2 推薦)
- **內存**: 4GB RAM
- **存儲**: 2GB 可用空間
- **網絡**: 穩定的互聯網連接

### 軟件需求
- **Python**: 3.11 或更高版本
- **Node.js**: 18.x 或更高版本
- **PostgreSQL**: 14.x 或更高版本
- **Git**: 2.30+ 版本
- **Docker** (可選): 20.10+ 版本 (用於容器化部署)
- **Redis** (可選): 6.x+ 版本 (用於緩存)

### 服務帳號
- [GitHub 帳號](https://github.com)
- [Twilio 帳號](https://twilio.com) (WhatsApp API)
- [Cloudinary 帳號](https://cloudinary.com) (圖片儲存)
- [Render 帳號](https://render.com) (部署平台，可選)

---

## 🚀 快速開始

### 方法 A：使用 Docker Compose (最簡單)
```bash
# 1. 克隆項目
git clone https://github.com/asiangrocerking-arch/whatsapp-order-bot.git
cd whatsapp-order-bot

# 2. 配置環境變量
cp .env.example .env
# 編輯 .env 文件，填入你的配置

# 3. 啟動所有服務
docker-compose up -d

# 4. 訪問應用
# 後端 API: http://localhost:8000
# API 文檔: http://localhost:8000/docs
# PostgreSQL: localhost:5432
```

### 方法 B：手動安裝 (全面控制)
繼續閱讀以下詳細指南。

---

## 🔧 後端設置

### 1. 獲取代碼
```bash
# 克隆項目
git clone https://github.com/asiangrocerking-arch/whatsapp-order-bot.git
cd whatsapp-order-bot

# 或下載 ZIP
# 訪問: https://github.com/asiangrocerking-arch/whatsapp-order-bot/archive/main.zip
```

### 2. 創建 Python 虛擬環境
```bash
# 創建虛擬環境
python -m venv venv

# 激活虛擬環境
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. 安裝 Python 依賴
```bash
# 升級 pip
pip install --upgrade pip

# 安裝核心依賴
pip install -r requirements.txt

# 安裝開發依賴 (可選)
pip install pytest pytest-asyncio black flake8
```

### 4. 配置環境變量
```bash
# 複製環境變量模板
cp .env.example .env

# 編輯 .env 文件
# 使用你喜歡的編輯器，如 nano、vim 或 VS Code
nano .env
```

**需要設置的關鍵變量**:
```env
# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost/whatsapp_order_bot

# Twilio WhatsApp API
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Cloudinary 圖片儲存
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# 應用安全
SECRET_KEY=your-secret-key-minimum-32-characters
ENVIRONMENT=development

# 管理員帳號
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong-password-here
ADMIN_EMAIL=admin@example.com
```

---

## 🖥️ 前端管理後台

### 1. 安裝 Node.js 依賴
```bash
# 創建前端目錄 (如果不存在)
mkdir -p admin-frontend
cd admin-frontend

# 初始化 package.json (如果不存在)
npm init -y

# 安裝核心依賴
npm install react react-dom typescript
npm install @mui/material @emotion/react @emotion/styled
npm install @tanstack/react-query axios
npm install react-hook-form react-router-dom
npm install react-dropzone cloudinary-react

# 安裝開發依賴
npm install -D vite @types/react @types/node
npm install -D eslint prettier
```

### 2. 配置 TypeScript
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3. 前端環境變量
```env
# .env
VITE_API_BASE_URL=http://localhost:8000
VITE_CLOUDINARY_CLOUD_NAME=your-cloud-name
VITE_CLOUDINARY_UPLOAD_PRESET=your-upload-preset
```

### 4. 啟動前端開發服務器
```bash
# 開發模式
npm run dev
# 訪問: http://localhost:5173

# 生產構建
npm run build

# 預覽生產版本
npm run preview
```

---

## ⚙️ 環境配置

### 獲取 Twilio 憑證
1. 註冊 [Twilio 帳號](https://twilio.com/try-twilio)
2. 進入 Console → Account → Account SID & Auth Token
3. 啟用 WhatsApp:
   - Messaging → WhatsApp → Sandbox
   - 記錄 Sandbox Phone Number 和 Join Code
   - 設置 Webhook URL: `http://你的域名/webhook/whatsapp`

### 獲取 Cloudinary 憑證
1. 註冊 [Cloudinary 帳號](https://cloudinary.com)
2. Dashboard → Account Details
3. 複製 Cloudinary URL:
   ```
   cloudinary://API_KEY:API_SECRET@CLOUD_NAME
   ```
4. 創建 Upload Preset:
   - Settings → Upload → Upload presets
   - 點擊「Add upload preset」
   - 設置: Signing mode: Unsigned

### 生成安全密鑰
```bash
# 生成安全的 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成安全的密碼
python -c "import secrets; import string; alphabet = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(alphabet) for i in range(16)))"
```

---

## 🗄️ 數據庫設置

### 1. 安裝 PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14

# Windows
# 下載安裝包: https://www.postgresql.org/download/windows/
```

### 2. 創建數據庫和用戶
```bash
# 登錄 PostgreSQL
sudo -u postgres psql

# 創建數據庫
CREATE DATABASE whatsapp_order_bot;

# 創建用戶
CREATE USER whatsapp_bot_user WITH PASSWORD 'your-strong-password';

# 授予權限
GRANT ALL PRIVILEGES ON DATABASE whatsapp_order_bot TO whatsapp_bot_user;

# 退出
\q
```

### 3. 初始化數據庫
```bash
# 激活 Python 虛擬環境
source venv/bin/activate

# 創建數據庫表
cd /home/bot/.openclaw/workspace/whatsapp-order-bot
python -c "
from app.database import engine
from app import models
models.Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# 創建初始管理員
python -c "
from app.database import SessionLocal
from app import models
db = SessionLocal()
# 檢查是否已有管理員
existing = db.query(models.AdminUser).filter(
    models.AdminUser.username == 'admin'
).first()
if not existing:
    import os
    admin = models.AdminUser(
        username=os.getenv('ADMIN_USERNAME', 'admin'),
        email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
        hashed_password='initial-password-hash-placeholder',
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('Admin user created')
else:
    print('Admin user already exists')
db.close()
"
```

---

## 💻 本地開發

### 1. 啟動後端服務器
```bash
# 開發模式 (自動重載)
cd /home/bot/.openclaw/workspace/whatsapp-order-bot
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生產模式
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. 啟動前端服務器
```bash
cd admin-frontend
npm run dev
```

### 3. 測試 API 端點
```bash
# 健康檢查
curl http://localhost:8000/health

# API 文檔
# 訪問: http://localhost:8000/docs

# 創建測試商品
curl -X POST "http://localhost:8000/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試商品",
    "price": 100.0,
    "delivery_methods": ["自取"],
    "stock": 10
  }'

# 管理員登錄
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-admin-password"
  }'
```

### 4. 測試 WhatsApp 集成
1. 加入 WhatsApp Sandbox:
   ```
   發送 "join [sandbox-code]" 到 Twilio Sandbox 號碼
   ```
2. 測試訂單流程:
   ```
   在群組發送: "我要落單"
   檢查是否收到私訊
   ```

---

## 🚀 生產部署

### 選項 A：部署到 Render.com

#### 1. 創建 PostgreSQL 數據庫
1. 登錄 [Render Dashboard](https://dashboard.render.com)
2. 「New +」 → 「PostgreSQL」
3. 配置:
   - Name: `whatsapp-order-bot-db`
   - Database: `whatsapp_order_bot`
   - User: `whatsapp_bot_user`
   - Region: Singapore (或離你近的)
   - Plan: Free
4. 點擊「Create Database」
5. 複製 Internal Database URL

#### 2. 創建 Web 服務
1. 「New +」 → 「Web Service」
2. 連接 GitHub 倉庫
3. 配置:
   - Name: `whatsapp-order-bot`
   - Environment: `Python 3`
   - Region: Singapore
   - Branch: `main`
4. Build & Start Commands:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. 設置環境變量 (參考上面的環境配置)

#### 3. 設置 Twilio Webhook
1. Twilio Console → WhatsApp → Sandbox
2. 「WHEN A MESSAGE COMES IN」:
   ```
   https://whatsapp-order-bot.onrender.com/webhook/whatsapp
   ```
3. 「HTTP Method」: `POST`
4. 「Save」

### 選項 B：部署到 Railway.app
```bash
# 安裝 Railway CLI
npm i -g @railway/cli

# 登錄 Railway
railway login

# 初始化項目
railway init

# 添加 PostgreSQL
railway add postgresql

# 設置環境變量
railway variables set TWILIO_ACCOUNT_SID=your_sid
railway variables set TWILIO_AUTH_TOKEN=your_token
railway variables set CLOUDINARY_URL=your_url

# 部署
railway up
```

### 選項 C：Docker 部署
```bash
# 構建 Docker 鏡像
docker build -t whatsapp-order-bot .

# 運行容器
docker run -d \
  --name whatsapp-order-bot \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e TWILIO_ACCOUNT_SID=your_sid \
  whatsapp-order-bot

# 使用 Docker Compose
docker-compose up -d --build
```

---

## 🧪 測試驗證

### 1. 單元測試
```bash
# 運行後端測試
cd /home/bot/.openclaw/workspace/whatsapp-order-bot
python -m pytest tests/ -v

# 運行前端測試
cd admin-frontend
npm test
```

### 2. API 測試
```bash
# 測試健康檢查
curl -s https://your-app.onrender.com/health | jq .status

# 測試商品 API
curl -s https://your-app.onrender.com/products/ | jq '. | length'

# 測試認證
curl -X POST https://your-app.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}' \
  | jq .access_token
```

### 3. 集成測試
```bash
# 完整訂單流程測試
./scripts/test-order-flow.sh

# WhatsApp Webhook 測試
curl -X POST https://your-app.onrender.com/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+85212345678&Body=我要落單"
```

### 4. 壓力測試
```bash
# 使用 Apache Bench
ab -n 1000 -c 10 https://your-app.onrender.com/health

# 使用 hey
hey -n 1000 -c 50 https://your-app.onrender.com/products/
```

---

## 🔧 故障排除

### 常見問題及解決方案

#### 1. 數據庫連接失敗
```bash
# 檢查連接
psql $DATABASE_URL -c "SELECT 1"

# 錯誤: "password authentication failed"
# 解決: 檢查密碼和用戶權限

# 錯誤: "connection refused"
# 解決: 確保 PostgreSQL 正在運行
sudo systemctl status postgresql
```

#### 2. Twilio Webhook 不響應
```bash
# 檢查 Webhook URL
curl -X POST https://your-app.onrender.com/webhook/whatsapp/test

# 檢查 Twilio 日誌
# Twilio Console → Monitor → Logs

# 檢查 Render 日誌
# Render Dashboard → Logs
```

#### 3. 圖片上傳失敗
```bash
# 檢查 Cloudinary 配置
curl "https://api.cloudinary.com/v1_1/your-cloud-name/resources/image"

# 檢查上傳預設
# Cloudinary Dashboard → Settings → Upload → Upload presets
```

#### 4. 內存不足
```bash
# 檢查內存使用
free -h

# 優化 PostgreSQL
# 編輯 postgresql.conf:
shared_buffers = 128MB
work_mem = 4MB
```

#### 5. 部署失敗
```bash
# 查看構建日誌
# Render Dashboard → Builds

# 常見錯誤: ModuleNotFoundError
# 解決: 確保 requirements.txt 完整

# 常見錯誤: Port already in use
# 解決: 檢查端口 8000 是否被佔用
lsof -i :8000
```

### 監控工具
```bash
# 實時日誌
tail -f /var/log/whatsapp-bot.log

# 監控 API 響應時間
curl -w "@curl-format.txt" -o /dev/null -s https://your-app.onrender.com/health

# 監控數據庫性能
pg_stat_statements
```

---

## 🔄 更新維護

### 1. 更新代碼
```bash
# 拉取最新代碼
git pull origin main

# 更新依賴
pip install -r requirements.txt --upgrade
npm update

# 重新啟動服務
docker-compose down && docker-compose up -d --build
```

### 2. 數據庫遷移
```bash
# 創建遷移腳本
alembic revision --autogenerate -m "description"

# 應用遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

### 3. 備份策略
```bash
# 數據庫備份
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 圖片備份
# Cloudinary → Media Library → Download backup

# 自動化備份 (cron)
0 2 * * * /path/to/backup-script.sh
```

### 4. 性能優化
```bash
# 清理舊日誌
find /var/log -name "*.log" -mtime +30 -delete

# 優化數據庫
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# 清理緩存
redis-cli FLUSHALL
```

---

## 📞 支持與幫助

### 官方文檔
- [FastAPI 文檔](https://fastapi.tiangolo.com)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [React 文檔](https://react.dev)
- [PostgreSQL 文檔](https://www.postgresql.org/docs)

### 社區支持
- [GitHub Issues](https://github.com/asiangrocerking-arch/whatsapp-order-bot/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/whatsapp-bot)
- [Discord](https://discord.gg/clawd)

### 緊急聯絡
- 技術問題: GitHub Issues
- Twilio 問題: help@twilio.com
- Render 問題: support@render.com
- Cloudinary 問題: support@cloudinary.com

---

## 🎉 安裝完成！

你的 WhatsApp 訂單機器人現在應該已經完全安裝並運行。如有任何問題，請參考以上故障排除部分或聯繫支持。

**下一步建議:**
1. 添加更多商品類別
2. 設置自動化通知
3. 創建銷售報表
4. 擴展支付方式

**祝你使用愉快！** 🚀