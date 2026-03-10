## 项目架构
email-reimbursement-fetcher/
├── Dockerfile          # Docker 构建文件
├── requirements.txt    # 依赖清单
├── config.py           # 配置文件（邮箱/推送/定时）
└── main.py             # 核心脚本（收邮件+定时+日志+推送）