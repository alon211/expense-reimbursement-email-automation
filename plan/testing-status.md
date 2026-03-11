# 测试覆盖状态

**最后更新**: 2026-03-11

本文档记录项目的测试覆盖情况，包括现有测试脚本、测试覆盖分析和待测试项。

---

## 现有测试脚本（15+ 个）

### 数据库测试

#### test_database.py
**职责**: 数据库基础功能测试
**测试内容**:
- [x] 数据库初始化
- [x] 邮件记录 CRUD 操作
- [x] 提取历史记录
- [x] 去重功能

**运行方式**:
```bash
python test_database.py
```

---

#### test_db_main_integration.py
**职责**: 主程序与数据库集成测试
**测试内容**:
- [x] 邮件拉取与数据库记录集成
- [x] 完整工作流测试

**运行方式**:
```bash
python test_db_main_integration.py
```

---

#### test_database_cleanup.py
**职责**: 数据库清理功能测试
**测试内容**:
- [x] 场景 1: 正常清理（文件存在）
- [x] 场景 2: 清理无效记录（文件不存在）
- [x] 场景 3: 自动清理功能

**运行方式**:
```bash
python test_database_cleanup.py
```

---

### 规则引擎测试

#### test_rules.py
**职责**: 规则加载和匹配测试
**测试内容**:
- [x] 规则 JSON 加载
- [x] 规则启用/禁用
- [x] 发件人匹配
- [x] 主题匹配
- [x] 正文匹配

**运行方式**:
```bash
python test_rules.py
```

---

#### test_rule_002.py
**职责**: 特定规则（rule_002 - 12306）测试
**测试内容**:
- [x] 12306 邮件匹配
- [x] 附件提取

**运行方式**:
```bash
python test_rule_002.py
```

---

#### test_rule_debug.py
**职责**: 规则匹配调试工具
**功能**:
- [x] 实时调试规则匹配过程

**运行方式**:
```bash
python test_rule_debug.py
```

---

### 去重功能测试

#### test_enhanced_dedup.py
**职责**: 增强版去重逻辑测试
**测试内容**:
- [x] message_id 去重
- [x] 文件存在性验证
- [x] 数据库记录去重

**运行方式**:
```bash
python test_enhanced_dedup.py
```

---

#### test_mail_date_dedup.py
**职责**: 基于邮件发送时间的去重测试
**测试内容**:
- [x] mail_date 唯一标识
- [x] 预检查去重
- [x] 智能更新逻辑

**运行方式**:
```bash
python test_mail_date_dedup.py
```

---

### 提取功能测试

#### test_todo3_extraction.py
**职责**: 文件提取功能测试（TODO3）
**测试内容**:
- [x] 邮件正文提取
- [x] 附件提取
- [x] 结构化数据导出

**运行方式**:
```bash
python test_todo3_extraction.py
```

---

#### test_extract_options.py
**职责**: 提取选项配置测试
**测试内容**:
- [x] extract_attachments 开关
- [x] extract_body 开关
- [x] extract_headers 开关

**运行方式**:
```bash
python test_extract_options.py
```

---

#### test_archive_extraction.py
**职责**: 压缩文件解压测试
**测试内容**:
- [x] ZIP 解压
- [x] RAR 解压
- [x] 7Z 解压
- [x] TAR.GZ 解压
- [x] 密码保护压缩包

**运行方式**:
```bash
python test_archive_extraction.py
```

---

#### test_real_attachments.py
**职责**: 真实附件解压测试
**测试内容**:
- [x] 真实 ZIP 文件解压
- [x] 解压后文件验证

**运行方式**:
```bash
python test_real_attachments.py
```

---

### 集成和调试工具

#### test_db_with_real_mail.py
**职责**: 真实邮件集成测试
**测试内容**:
- [x] 真实邮箱连接
- [x] 邮件拉取
- [x] 数据库记录

**运行方式**:
```bash
python test_db_with_real_mail.py
```

---

#### test_directory_reuse.py
**职责**: 目录复用测试
**测试内容**:
- [x] 提取目录复用逻辑

**运行方式**:
```bash
python test_directory_reuse.py
```

---

#### test_logger_production.py
**职责**: 生产环境日志测试
**测试内容**:
- [x] 控制台日志禁用
- [x] 文件日志输出

**运行方式**:
```bash
python test_logger_production.py
```

---

#### test_file_cleanup.py
**职责**: 文件清理测试
**测试内容**:
- [x] 无效文件清理
- [x] 空目录清理

**运行方式**:
```bash
python test_file_cleanup.py
```

---

#### test_clear_db.py & test_clear_db_integration.py
**职责**: 数据库清空功能测试
**测试内容**:
- [x] 数据库清空配置
- [x] 集成测试

**运行方式**:
```bash
python test_clear_db.py
python test_clear_db_integration.py
```

---

### 调试脚本

以下脚本主要用于开发和调试，不是自动化测试：

- `check_database.py` - 检查数据库状态
- `check_db.py` - 查看数据库内容
- `clean_database.py` - 清理数据库
- `clean_invalid_records.py` - 清理无效记录
- `clear_database.py` - 清空数据库
- `debug_db_paths.py` - 调试数据库路径
- `debug_mail_matching.py` - 调试邮件匹配

---

## 测试覆盖分析

### 核心模块测试覆盖

| 模块 | 测试覆盖 | 测试脚本 | 状态 |
|------|---------|---------|------|
| **config/settings.py** | ⚠️ 部分覆盖 | - | 未独立测试 |
| **config/logger_config.py** | ✅ 已覆盖 | test_logger_production.py | 已测试 |
| **core/database.py** | ✅ 完全覆盖 | test_database.py<br>test_database_cleanup.py<br>test_enhanced_dedup.py<br>test_mail_date_dedup.py | 多维度测试 |
| **core/rule_loader.py** | ✅ 完全覆盖 | test_rules.py<br>test_rule_002.py<br>test_rule_debug.py | 多维度测试 |
| **core/email_fetcher.py** | ⚠️ 部分覆盖 | test_db_main_integration.py<br>test_db_with_real_mail.py | 集成测试 |
| **core/email_extractor.py** | ✅ 完全覆盖 | test_todo3_extraction.py<br>test_extract_options.py<br>test_archive_extraction.py<br>test_real_attachments.py | 多维度测试 |
| **core/dingtalk_notifier.py** | ❌ 未覆盖 | - | **待测试** |
| **utils/header_decoder.py** | ⚠️ 部分覆盖 | test_db_with_real_mail.py | 集成测试 |
| **utils/file_utils.py** | ⚠️ 部分覆盖 | test_enhanced_dedup.py | 集成测试 |
| **utils/archive_utils.py** | ✅ 完全覆盖 | test_archive_extraction.py<br>test_real_attachments.py | 专门测试 |

---

### 功能测试覆盖

| 功能 | 测试覆盖 | 测试脚本 | 状态 |
|------|---------|---------|------|
| **IMAP 连接** | ✅ 已覆盖 | test_db_with_real_mail.py | 真实环境测试 |
| **邮件解析** | ✅ 已覆盖 | test_db_main_integration.py | 集成测试 |
| **规则匹配** | ✅ 已覆盖 | test_rules.py, test_rule_002.py | 专门测试 |
| **内容提取** | ✅ 已覆盖 | test_todo3_extraction.py | 专门测试 |
| **附件解压** | ✅ 已覆盖 | test_archive_extraction.py | 多格式测试 |
| **去重机制** | ✅ 已覆盖 | test_enhanced_dedup.py<br>test_mail_date_dedup.py | 多维度测试 |
| **数据库记录** | ✅ 已覆盖 | test_database.py<br>test_db_main_integration.py | 多维度测试 |
| **数据库清理** | ✅ 已覆盖 | test_database_cleanup.py | 专门测试 |
| **日志系统** | ✅ 已覆盖 | test_logger_production.py | 专门测试 |
| **钉钉推送** | ❌ 未覆盖 | - | **待测试** |
| **Docker 部署** | ❌ 未覆盖 | - | **待测试** |

---

## 待测试项

### 高优先级（P0）

#### 1. 钉钉通知推送测试 🔔
**缺失测试**:
- [ ] 单元测试：Webhook 请求构造
- [ ] 单元测试：签名计算（HMAC-SHA256）
- [ ] 集成测试：真实发送钉钉消息
- [ ] 异常测试：网络错误处理
- [ ] 异常测试：签名错误处理
- [ ] 异常测试：推送限流处理

**建议测试脚本**: `test_dingtalk_notifier.py`

**预计工作量**: 1-2 天

---

#### 2. Docker 部署测试 🐳
**缺失测试**:
- [ ] Dockerfile 构建测试
- [ ] docker-compose 启动测试
- [ ] 数据持久化测试
- [ ] 环境变量注入测试
- [ ] 容器日志输出测试
- [ ] 容器重启测试

**建议测试脚本**: `test_docker_deployment.py`

**预计工作量**: 1-2 天

---

### 中优先级（P1）

#### 3. 配置管理模块单元测试 ⚙️
**缺失测试**:
- [ ] 环境变量读取测试
- [ ] 配置校验测试
- [ ] 邮箱格式校验测试
- [ ] 必填项检查测试

**建议测试脚本**: `test_settings.py`

**预计工作量**: 0.5-1 天

---

#### 4. 邮件拉取模块单元测试 📧
**缺失测试**:
- [ ] IMAP 连接测试（Mock）
- [ ] 邮件搜索测试（Mock）
- [ ] 邮件头解码测试
- [ ] 邮件正文提取测试

**建议测试脚本**: `test_email_fetcher.py`

**预计工作量**: 1-2 天

---

#### 5. 工具函数单元测试 🔧
**缺失测试**:
- [ ] header_decoder.py 单元测试
- [ ] file_utils.py 单元测试

**建议测试脚本**: `test_header_decoder.py`, `test_file_utils.py`

**预计工作量**: 0.5-1 天

---

## 测试覆盖率目标

### 当前状态估算

| 模块 | 估算覆盖率 | 目标覆盖率 | 差距 |
|------|-----------|-----------|------|
| config/ | ~30% | 80% | -50% |
| core/ | ~70% | 80% | -10% |
| utils/ | ~60% | 80% | -20% |
| **总体** | **~60%** | **80%** | **-20%** |

### 提升计划

1. **Q1 2026**: 提升至 70%
   - 完成钉钉推送测试
   - 完成配置管理测试
   - 添加邮件拉取单元测试

2. **Q2 2026**: 提升至 80%+
   - 完成工具函数测试
   - 添加 Docker 部署测试
   - 引入 pytest 和覆盖率报告

---

## 测试框架建议

### 当前测试方式
- 独立测试脚本（Python）
- 手动运行和验证
- 无自动化测试框架

### 建议升级方案

#### 方案 1: pytest（推荐）
**优势**:
- 简洁的测试语法
- 强大的 fixture 机制
- 丰富的插件生态
- 覆盖率报告支持

**安装**:
```bash
pip install pytest pytest-cov pytest-mock
```

**示例**:
```python
# test_database_pytest.py
import pytest
from core.database import DatabaseManager

@pytest.fixture
def db_manager():
    """测试用数据库管理器"""
    return DatabaseManager(":memory:")

def test_add_email(db_manager):
    """测试添加邮件记录"""
    # 测试代码
    pass
```

**运行**:
```bash
# 运行所有测试
pytest

# 运行特定文件
pytest test_database_pytest.py

# 生成覆盖率报告
pytest --cov=core --cov-report=html
```

---

#### 方案 2: unittest（备选）
**优势**:
- Python 标准库，无需安装
- 成熟稳定

**劣势**:
- 测试语法较繁琐
- Fixture 功能较弱

---

## 持续集成建议

### GitHub Actions 配置示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=core --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 测试最佳实践

### 1. 测试命名
- 使用描述性的测试名称
- 格式：`test_<功能>_<场景>_<预期结果>`

### 2. 测试结构（AAA 模式）
```python
def test_something():
    # Arrange - 准备测试数据
    data = prepare_data()

    # Act - 执行被测试的功能
    result = function_under_test(data)

    # Assert - 验证结果
    assert result == expected
```

### 3. Mock 外部依赖
```python
from unittest.mock import Mock, patch

def test_email_fetch():
    with patch('core.email_fetcher.imaplib') as mock_imap:
        # 设置 Mock 行为
        mock_imap.IMAP4_SSL.return_value = Mock()

        # 测试代码
        ...
```

### 4. 测试隔离
- 每个测试独立运行
- 不依赖测试执行顺序
- 使用临时数据库和文件

---

**相关文档**:
- [功能完成状态](feature-status.md)
- [开发路线图](development-roadmap.md)
- [CLAUDE.md](../CLAUDE.md) - 主项目文档
