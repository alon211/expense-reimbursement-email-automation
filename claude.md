## 项目架构
email-reimbursement-fetcher/
├── .env.example                          # 环境变量示例文件（提交到Git）
├── .env                                  # 实际环境变量（忽略Git，本地配置）
├── .gitignore                            # Git忽略规则
├── docker-compose.yml                    # Docker-compose部署配置
├── Dockerfile                            # Docker镜像构建文件
├── requirements.txt                      # 项目依赖
├── README.md                             # 项目说明文档
├── config/                               # 配置模块
│   ├── __init__.py                       # 配置包初始化
│   ├── settings.py                       # 配置读取核心逻辑（原config.py）
│   └── logger_config.py                  # 日志专属配置（抽离日志初始化）
├── core/                                 # 核心业务逻辑
│   ├── __init__.py
│   ├── email_fetcher.py                  # 邮件拉取/解析逻辑（原main.py核心）
│   └── dingtalk_notifier.py              # 钉钉推送逻辑（抽离解耦）
├── utils/                                # 工具函数
│   ├── __init__.py
│   ├── header_decoder.py                 # 邮件头解码工具
│   └── file_utils.py                     # 文件/路径工具（日志目录校验等）
├── logs/                                 # 日志目录（自动生成，忽略Git）
└── main.py                               # 程序入口（仅保留主循环，轻量化）


### 各目录/文件核心职责说明
#### 1. 根目录核心文件
| 文件                | 核心作用                                                                 |
|---------------------|--------------------------------------------------------------------------|
| `.env.example`      | 环境变量示例（如 `IMAP_HOST=xxx`、`LOG_LEVEL=DEBUG`），供团队参考配置     |
| `.env`              | 本地实际配置（不提交Git），包含敏感信息（邮箱密码、钉钉Webhook）          |
| `Dockerfile`/`docker-compose.yml` | Docker部署配置，一键构建/启动服务                          |
| `requirements.txt`  | 项目依赖（如 `requests==2.31.0`、`python-dotenv==1.0.0`）                |
| `README.md`         | 项目说明（部署步骤、配置说明、常见问题）                                  |

#### 2. 配置模块（`config/`）
抽离配置相关逻辑，解耦核心业务：
- `settings.py`：读取 `.env` 环境变量，统一导出所有配置（如 IMAP 信息、日志级别）；
- `logger_config.py`：日志专属配置（抽离原 `init_logger` 逻辑，专注日志初始化）。

#### 3. 核心业务模块（`core/`）
按功能拆分核心逻辑，便于维护：
- `email_fetcher.py`：邮件拉取、解析、标记已读等核心逻辑（原 `fetch_reimbursement_mails`/`parse_reimbursement_mail`）；
- `dingtalk_notifier.py`：钉钉推送专属逻辑（原 `send_dingtalk_message`）。

#### 4. 工具模块（`utils/`）
抽离通用工具函数，复用性强：
- `header_decoder.py`：邮件头解码（原 `decode_mail_header`）；
- `file_utils.py`：日志目录校验、文件刷盘、路径兼容等工具函数。

#### 5. 程序入口（`main.py`）
轻量化设计，仅负责：
- 初始化配置/日志；
- 启动定时任务主循环；
- 捕获全局异常。

### 关键文件示例（核心片段）
#### 1. `config/settings.py`（配置读取）
```python
# config/settings.py
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv(override=True)

# 邮箱配置
IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")
MAIL_CHECK_FOLDER = os.getenv("MAIL_CHECK_FOLDER", "INBOX")
MAIL_SEARCH_CRITERIA = os.getenv("MAIL_SEARCH_CRITERIA", "UNSEEN")

# 定时配置
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Shanghai")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# 钉钉配置
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
PUSH_SWITCH = os.getenv("PUSH_SWITCH", "True").lower() == "true"

# 其他配置
PARSE_RULES_JSON_PATH = os.getenv("PARSE_RULES_JSON_PATH", "./rules.json")
EXTRACT_ROOT_DIR = os.getenv("EXTRACT_ROOT_DIR", "./extracts")
```

#### 2. `config/logger_config.py`（日志配置）
```python
# config/logger_config.py
import logging
import os
import sys
import atexit
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_DIR

def init_logger():
    """初始化日志（抽离后的独立逻辑）"""
    # 日志目录校验
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.access(LOG_DIR, os.W_OK):
        raise PermissionError(f"日志目录 {LOG_DIR} 无写入权限！")
    
    # 日志文件名
    log_file = os.path.join(
        LOG_DIR,
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{LOG_LEVEL}.log"
    ).replace("\\", "/")
    
    # 日志格式
    fmt = '%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    
    # 控制台Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.flush = sys.stdout.flush

    # 文件Handler
    log_file_obj = open(log_file, mode='a', encoding='utf-8', buffering=1)
    file_handler = logging.StreamHandler(log_file_obj)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # 强制刷盘
    def force_flush():
        if log_file_obj and not log_file_obj.closed:
            log_file_obj.flush()
            os.fsync(log_file_obj.fileno())
    file_handler.flush = force_flush

    # 重写emit方法
    original_emit = file_handler.emit
    def emit_with_flush(record):
        original_emit(record)
        force_flush()
    file_handler.emit = emit_with_flush

    # 初始化Logger
    logger = logging.getLogger("ExpenseReimbursement")
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    # 退出钩子
    atexit.register(lambda: (force_flush(), log_file_obj.close()))

    # 测试写入
    logger.info(f"日志初始化完成，文件路径：{log_file}")
    return logger, log_file
```

#### 3. `main.py`（轻量化入口）
```python
# main.py
import time
import pytz
import sys
from config.settings import (
    CHECK_INTERVAL, TIME_ZONE, LOG_LEVEL
)
from config.logger_config import init_logger
from core.email_fetcher import fetch_reimbursement_mails
from utils.file_utils import check_file_exists

# 初始化日志
try:
    logger, log_file = init_logger()
except Exception as e:
    print(f"日志初始化失败：{e}")
    sys.exit(1)

def main():
    """主循环"""
    tz = pytz.timezone(TIME_ZONE)
    logger.info("\n===== 报销邮件自动化服务启动 =====")
    logger.info(f"Python版本：{sys.version} | 日志级别：{LOG_LEVEL}")
    logger.info(f"检查间隔：{CHECK_INTERVAL}s | 日志文件：{log_file}")
    logger.info("=================================\n")

    # 验证日志文件
    if check_file_exists(log_file):
        logger.info("✅ 日志文件写入正常")
    else:
        logger.error("❌ 日志文件写入异常，请检查权限！")

    # 定时任务
    while True:
        try:
            current_time = pytz.utc.localize(datetime.utcnow()).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"\n=== 开始邮件检查：{current_time} ===")
            fetch_reimbursement_mails(logger)  # 传入logger解耦
        except Exception as e:
            logger.error(f"主循环异常：{str(e)}")
        logger.info(f"等待{CHECK_INTERVAL}秒后再次检查...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户手动终止程序，正在退出...")
    except Exception as e:
        logger.error(f"程序异常退出：{str(e)}")
        sys.exit(1)
```

### 核心优势
1. **模块化解耦**：
   - 配置、日志、业务逻辑、工具函数完全拆分，便于单独维护/扩展；
   - 例如：后续新增企业微信推送，只需在 `core/` 下新增 `wechat_notifier.py`。
2. **环境隔离**：
   - `.env` 分离敏感配置，避免硬编码；
   - `.env.example` 便于团队协作，无需暴露敏感信息。
3. **部署友好**：
   - Dockerfile/docker-compose.yml 支持一键部署；
   - 日志目录独立，便于挂载宿主机卷。
4. **可维护性**：
   - 每个文件职责单一，符合“单一职责原则”；
   - 工具函数抽离，避免重复代码。

### `.gitignore` 示例（关键忽略项）
```
# 环境变量
.env
# 日志
logs/
# 缓存/编译文件
__pycache__/
*.pyc
# Docker构建缓存
.dockerignore
# 编辑器配置
.idea/
.vscode/
*.swp
```

### 扩展建议
- 若需新增功能（如邮件附件下载）：在 `core/` 下新增 `attachment_processor.py`；
- 若需配置多环境（测试/生产）：在 `config/` 下新增 `settings_dev.py`/`settings_prod.py`；
- 若需监控：在 `utils/` 下新增 `monitor_utils.py`（如日志大小监控、服务存活检测）。

