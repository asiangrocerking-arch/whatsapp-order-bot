# WhatsApp 訂單機器人 - 部署指南

## 📋 前置要求

### 已註冊服務
1. **Twilio 帳號** - WhatsApp Business API
2. **Render 帳號** - 應用部署平台
3. **Cloudinary 帳號** - 圖片儲存服務
4. **GitHub 帳號** - 代碼託管

### 環境準備
- Git 命令行工具
- Python 3.11+（本地測試用）
- 命令行終端

---

## 🚀 快速部署（5分鐘）

### 步驟 1：推送代碼到 GitHub

```bash
# 進入項目目錄
cd whatsapp-order-bot

# 初始化 Git（如果未初始化）
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "初始提交：WhatsApp訂單機器人"

# 在 GitHub 創建新倉庫（網頁操作）
# 獲取倉庫 URL，例如：https://github.com/你的用戶名/whatsapp-order-bot.git

# 添加遠程倉庫
git remote add origin https://github.com/你的用戶名/whatsapp-order-bot.git

# 推送代碼
git branch -M main
git push -u origin main
```

### 步驟 2：部署到 Render

1. **登錄 Render**：https://dashboard.render.com
2. **點擊「New +」** → **「Blueprint」**
3. **連接 GitHub 倉庫**：選擇你的 `whatsapp-order-bot` 倉庫
4. **應用名稱**：輸入 `whatsapp-order-bot`（或其他名稱）
5. **點擊「Apply」**：Render 會自動檢測 `render.yaml` 並部署

### 步驟 3：配置環境變量

部署完成後，在 Render Dashboard：

1. 進入你的 Web Service
2. 點擊「Environment」標籤
3. 添加以下環境變量：

| 變量名 | 值 | 獲取方式 |
|--------|-----|----------|
| `TWILIO_ACCOUNT_SID` | 你的 Twilio Account SID | Twilio Console → Account Info |
| `TWILIO_AUTH_TOKEN` | 你的 Twilio Auth Token | Twilio Console → Account Info |
| `CLOUDINARY_URL` | 你的 Cloudinary URL | Cloudinary Dashboard → Account Details |
| `SECRET_KEY` | 隨機字符串（用於 JWT） | 可以留空，Render 會自動生成 |
| `ENVIRONMENT` | `production` | |
| `PORT` | `8000` | |

4. 點擊「Save Changes」

### 步驟 4：設置 Twilio Webhook

1. **登錄 Twilio Console**：https://console.twilio.com
2. 進入 **WhatsApp** → **Sandbox**
3. 找到 **「WHEN A MESSAGE COMES IN」** 字段
4. 輸入你的 Webhook URL：
   ```
   https://你的應用名稱.onrender.com/webhook/whatsapp
   ```
   （將「你的應用名稱」替換為 Render 分配的域名）
5. 點擊 **「Save」**

### 步驟 5：測試部署

1. **訪問健康檢查**：
   ```
   https://你的應用名稱.onrender.com/health
   ```
   應該返回 `{"status":"healthy"}`

2. **訪問 API 文檔**：
   ```
   https://你的應用名稱.onrender.com/docs
   ```

3. **測試 WhatsApp**：
   - 發送 "join [sandbox-code]" 到你的 WhatsApp Sandbox 號碼
   - 在群組發送「我要落單」
   - 檢查是否收到私訊

---

## 🔧 詳細配置

### Twilio 配置詳解

1. **獲取 Sandbox 憑證**：
   - 登錄 Twilio Console
   - 進入「WhatsApp」→「Sandbox」
   - 記錄「Sandbox Phone Number」和「Join Code」

2. **測試 Sandbox**：
   ```
   發送 "join [Join Code]" 到 Sandbox Phone Number
   ```

3. **Webhook 驗證**：
   - 確保 Webhook URL 正確
   - 必須是 HTTPS
   - 無需身份驗證

### Cloudinary 配置

1. **獲取 Cloudinary URL**：
   ```
   cloudinary://API_KEY:API_SECRET@CLOUD_NAME
   ```

2. **圖片上傳限制**：
   - 最大文件大小：10MB
   - 支持格式：JPG、PNG、GIF
   - 免費層：每月 10GB 流量

### Render 配置

1. **免費層限制**：
   - Web Service：每月 750 小時
   - PostgreSQL：每月 100MB 儲存
   - 自動睡眠：15分鐘無流量後休眠

2. **升級建議**：
   - 如果需要 24/7 運行，升級到「Starter」計劃（$7/月）
   - 如果需要更多數據庫儲存，升級到「Standard」計劃

---

## 🧪 本地測試部署

### 使用 Docker Compose

```bash
# 複製環境變量文件
cp .env.example .env
# 編輯 .env 文件，填入你的配置

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f app

# 停止服務
docker-compose down
```

### 手動測試 API

```bash
# 添加測試商品
curl -X POST "http://localhost:8000/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試商品",
    "price": 100.0,
    "delivery_methods": ["自取"],
    "stock": 10
  }'

# 查看商品列表
curl "http://localhost:8000/products/"

# 測試管理員登錄
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

---

## 🚨 故障排除

### 常見問題

#### 1. Render 部署失敗
- **錯誤**：`ModuleNotFoundError: No module named 'fastapi'`
  - **解決**：確保 `requirements.txt` 文件存在且正確
- **錯誤**：`ImportError: cannot import name 'X' from 'Y'`
  - **解決**：檢查 Python 版本（需要 3.11+）

#### 2. Twilio Webhook 無響應
- **檢查**：Webhook URL 是否正確
- **檢查**：Render 應用是否正在運行
- **檢查**：`/webhook/whatsapp` 端點是否可訪問

#### 3. 數據庫連接失敗
- **檢查**：Render PostgreSQL 是否已創建
- **檢查**：`DATABASE_URL` 環境變量是否正確
- **檢查**：應用日誌中的數據庫錯誤

#### 4. 圖片上傳失敗
- **檢查**：`CLOUDINARY_URL` 是否正確
- **檢查**：Cloudinary 帳號是否激活
- **檢查**：圖片大小是否超過限制

### 日誌查看

```bash
# Render 日誌
# 在 Render Dashboard 點擊「Logs」標籤

# 本地日誌
docker-compose logs -f app

# 詳細日誌
uvicorn app.main:app --reload --log-level debug
```

### 健康檢查端點

- `GET /health` - 服務健康狀態
- `GET /config` - 配置查看（僅開發環境）
- `GET /webhook/whatsapp/test` - WhatsApp 集成測試

---

## 📈 監控與維護

### 日常檢查
1. **Render Dashboard**：查看服務狀態和資源使用
2. **Twilio Console**：查看訊息量和錯誤
3. **Cloudinary Dashboard**：查看圖片儲存和流量

### 數據備份
```bash
# 從 Render PostgreSQL 導出數據
render postgresql export --database whatsapp-order-bot-db

# 備份到本地
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 性能優化
1. **啟用緩存**：考慮添加 Redis
2. **圖片優化**：使用 Cloudinary 自動壓縮
3. **數據庫索引**：為常用查詢字段添加索引

---

## 🔒 安全建議

### 生產環境安全
1. **更改默認密碼**：
   - 修改 `ADMIN_PASSWORD` 環境變量
   - 使用強密碼（12+字符，包含大小寫、數字、符號）

2. **限制訪問**：
   - 使用 Render 的 IP 限制功能
   - 僅允許管理員 IP 訪問 `/admin` 端點

3. **定期更新**：
   - 定期更新 Python 依賴
   - 監控安全公告

### WhatsApp 政策遵守
1. **明確告知**：讓用戶知道這是機器人
2. **不發垃圾**：僅在用戶請求時發送消息
3. **提供退出**：允許用戶取消訂閱

---

## 📞 支持與幫助

### 官方文檔
- **FastAPI**：https://fastapi.tiangolo.com
- **Twilio WhatsApp**：https://www.twilio.com/docs/whatsapp
- **Render**：https://render.com/docs
- **Cloudinary**：https://cloudinary.com/documentation

### 故障報告
1. 檢查應用日誌
2. 提供錯誤訊息
3. 描述重現步驟

### 緊急聯絡
- Render 支持：support@render.com
- Twilio 支持：help@twilio.com
- 項目問題：GitHub Issues

---

## 🎉 部署成功！

部署完成後，你可以：

1. **訪問管理界面**：`https://你的應用名稱.onrender.com/docs`
2. **添加商品**：使用 `/products` API
3. **測試訂單流程**：在 WhatsApp 群組發送「我要落單」
4. **查看訂單**：使用 `/orders` API 或管理界面

**下一步建議**：
- 添加更多商品類別
- 設置自動化通知
- 創建簡單的前端管理界面
- 添加報表和分析功能

**祝你使用愉快！** 🚀