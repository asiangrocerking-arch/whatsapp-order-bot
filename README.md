# WhatsApp 訂單機器人

一個經濟型的 WhatsApp 訂單處理系統，專為小型企業和團購設計。

## 🎯 功能特點

### 核心功能
- **商品管理**：添加、編輯、刪除商品（名稱、圖片、價格、交收方式）
- **群組監聽**：自動識別群組中的「我要落單」關鍵詞
- **自動私訊**：機器人主動聯繫客戶確認訂單
- **訂單處理**：記錄訂單、管理狀態、通知客戶
- **管理後台**：查看訂單、管理商品、手動操作

### 技術特色
- **低成本運行**：使用免費/低價雲服務
- **易於部署**：一鍵部署到 Render/Railway
- **可擴展架構**：模塊化設計，方便添加新功能
- **安全可靠**：JWT 認證、輸入驗證、錯誤處理

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────┐
│         前端管理介面 (React Admin)          │
├─────────────────────────────────────────────┤
│         FastAPI 後端 (Python 3.11+)         │
├─────────────────────────────────────────────┤
│     WhatsApp 集成層 (Twilio API)           │
├─────────────────────────────────────────────┤
│       數據庫層 (PostgreSQL)                 │
└─────────────────────────────────────────────┘
```

## 🚀 快速開始

### 前置要求
- Python 3.11+
- PostgreSQL 或 SQLite
- Twilio 帳號（WhatsApp Sandbox）
- Cloudinary 帳號（圖片儲存）

### 本地開發

1. **克隆項目**
```bash
git clone <repository-url>
cd whatsapp-order-bot
```

2. **設置虛擬環境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
```

4. **配置環境變量**
```bash
cp .env.example .env
# 編輯 .env 文件，填入你的配置
```

5. **初始化數據庫**
```bash
python -c "from app.database import engine; from app import models; models.Base.metadata.create_all(bind=engine)"
```

6. **啟動開發服務器**
```bash
uvicorn app.main:app --reload --port 8000
```

7. **訪問 API 文檔**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📱 WhatsApp 配置

### 1. 設置 Twilio WhatsApp Sandbox
1. 註冊 [Twilio 帳號](https://www.twilio.com/try-twilio)
2. 進入 WhatsApp Sandbox
3. 獲取 Account SID 和 Auth Token
4. 設置 Webhook URL: `https://your-app.onrender.com/webhook/whatsapp`

### 2. 測試 Sandbox
1. 發送 "join [sandbox-code]" 到指定的 WhatsApp 號碼
2. 在群組中測試「我要落單」關鍵詞
3. 查看私訊流程

## 🌐 部署指南

### 部署到 Render.com（推薦）

#### 1. 設置 PostgreSQL 數據庫
1. 在 Render Dashboard 創建 PostgreSQL 實例
2. 記下連接字符串

#### 2. 部署 Web 服務
1. 連接 GitHub 倉庫
2. 選擇 Blueprint: `render.yaml`
3. 設置環境變量
4. 部署

#### 3. 配置 Webhook
1. 在 Twilio Console 更新 Webhook URL
2. 使用你的 Render app URL

### 部署到 Railway.app
```bash
railway init
railway add postgresql
railway up
```

## 🔧 環境變量

| 變量 | 說明 | 默認值 |
|------|------|--------|
| `DATABASE_URL` | 數據庫連接字符串 | - |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | - |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | - |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp 號碼 | `whatsapp:+14155238886` |
| `CLOUDINARY_URL` | Cloudinary 連接字符串 | - |
| `SECRET_KEY` | JWT 加密密鑰 | - |
| `ENVIRONMENT` | 運行環境 | `development` |

## 📊 數據庫結構

### 主要表結構
- **products**：商品信息（名稱、價格、庫存、圖片等）
- **orders**：訂單記錄（客戶、商品、狀態、交收信息）
- **whatsapp_sessions**：WhatsApp 會話狀態
- **admin_users**：管理員用戶

### 數據遷移
```bash
# 生成遷移腳本
alembic revision --autogenerate -m "描述"

# 應用遷移
alembic upgrade head
```

## 🔐 安全注意

### 重要安全措施
1. **永遠不要**在代碼中硬編碼 API 密鑰
2. 生產環境使用強 SECRET_KEY
3. 啟用 HTTPS（Render 自動提供）
4. 限制管理員訪問
5. 驗證所有用戶輸入

### WhatsApp 政策遵守
1. 明確告知用戶這是機器人
2. 不發送垃圾訊息
3. 提供取消訂閱選項
4. 遵守 Twilio 使用條款

## 📈 監控與維護

### 日誌查看
```bash
# Render 日誌
render logs

# Railway 日誌
railway logs
```

### 健康檢查
- `GET /health`：服務健康狀態
- `GET /config`：配置查看（僅開發環境）

### 備份策略
1. 定期導出 PostgreSQL 數據
2. 備份商品圖片到本地
3. 導出訂單記錄為 CSV

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 創建 Pull Request

### 代碼規範
- 使用 Black 格式化代碼
- 遵循 PEP 8 規範
- 添加類型註解
- 編寫測試用例

## 📞 支持與聯繫

### 常見問題
1. **Twilio Sandbox 無法接收消息？**
   - 檢查 Webhook URL 是否正確
   - 確認 Sandbox 已加入

2. **圖片上傳失敗？**
   - 檢查 Cloudinary 配置
   - 確認圖片格式和大小

3. **訂單狀態不更新？**
   - 檢查數據庫連接
   - 查看應用日誌

### 緊急問題
- 查看應用日誌
- 檢查環境變量
- 重啟服務實例

## 📄 許可證

MIT License

## 🙏 致謝

- [FastAPI](https://fastapi.tiangolo.com/) - 現代化 Python Web 框架
- [Twilio](https://www.twilio.com/) - WhatsApp API 服務
- [Render](https://render.com/) - 雲部署平台
- [Cloudinary](https://cloudinary.com/) - 圖片管理服務