# 数据库清空配置功能

## 功能说明

新增了 `CLEAR_DB_ON_STARTUP` 配置选项，控制程序启动时是否清空数据库。

### 适用场景

- ✅ **开发测试**：频繁需要重新验证邮件提取流程
- ✅ **规则调试**：修改规则后需要重新处理所有邮件
- ✅ **数据重置**：清空旧的提取记录，重新开始
- ❌ **生产环境**：不建议启用，会丢失历史数据

## 配置方法

### 在 [.env](.env) 文件中添加：

```env
# 是否在启动时清空数据库（True=清空，False=保留）
# 警告：设置为 True 会删除所有已提取的邮件记录，仅用于开发和测试
CLEAR_DB_ON_STARTUP=False
```

### 配置值说明

| 值 | 行为 | 使用场景 |
|---|------|---------|
| `False` | 保留数据库（默认） | 生产环境、正常运行 |
| `True` | 启动时清空所有数据 | 开发测试、规则调试 |

## 实现细节

### 修改的文件

1. **[.env](.env)** - 添加配置项
2. **[config/settings.py](config/settings.py)** - 读取配置
3. **[core/database.py](core/database.py)** - 新增 `clear_all_data()` 方法
4. **[main.py](main.py)** - 应用配置

### 清空内容

当 `CLEAR_DB_ON_STARTUP=True` 时，程序会：

1. **清空邮件记录表** (`extracted_emails`)
   - 删除所有邮件提取记录
   - 重置自增ID序列

2. **清空历史记录表** (`extraction_history`)
   - 删除所有操作历史
   - 重置自增ID序列

3. **记录日志**
   - 清空前显示统计信息
   - 清空后显示删除数量

### 日志示例

**启用清空时（CLEAR_DB_ON_STARTUP=True）：**
```
【系统日志】数据库初始化成功
⚠️  配置要求启动时清空数据库（CLEAR_DB_ON_STARTUP=True）
【系统日志】清空前统计：5 封邮件，8 条历史
【系统日志】已清空：5 封邮件，8 条历史
✅ 数据库已清空，将重新处理所有匹配的邮件
```

**保留数据时（CLEAR_DB_ON_STARTUP=False）：**
```
【系统日志】数据库初始化成功
【系统日志】保留数据库记录（CLEAR_DB_ON_STARTUP=False）
```

## 使用方法

### 场景 1：开发测试时频繁重置

1. 在 `.env` 中设置：
   ```env
   CLEAR_DB_ON_STARTUP=True
   ```

2. 每次运行 `python main.py` 时自动清空数据库

3. 测试完成后，恢复默认值：
   ```env
   CLEAR_DB_ON_STARTUP=False
   ```

### 场景 2：手动清空数据库

如果只想手动清空一次，而不修改配置，可以：

```python
# 在 Python 交互环境中
from core.database import DatabaseManager
from config.settings import EXTRACT_ROOT_DIR
from pathlib import Path

db_path = Path(EXTRACT_ROOT_DIR) / "data.db"
db = DatabaseManager(str(db_path))
db.clear_all_data()
```

或运行测试脚本：
```bash
python test_clear_db.py
```

## 测试验证

### 测试脚本

| 脚本 | 功能 | 命令 |
|------|------|------|
| test_clear_db.py | 测试清空功能 | `python test_clear_db.py` |
| test_clear_db_integration.py | 测试主程序集成 | `python test_clear_db_integration.py` |

### 验证步骤

1. **测试清空功能**
   ```bash
   python test_clear_db.py
   ```
   预期输出：清空 3 条邮件记录和 5 条历史记录

2. **测试主程序集成**
   ```bash
   # 修改 .env 中的 CLEAR_DB_ON_STARTUP=True
   python main.py
   ```
   预期日志：显示清空统计信息

3. **验证数据库状态**
   ```bash
   python check_db.py
   ```
   预期输出：邮件记录 0 条，历史记录 0 条

## 注意事项

⚠️ **警告**

1. **数据丢失风险**
   - 设置为 `True` 会永久删除所有记录
   - 删除前无法撤销
   - 建议清空前备份数据库文件

2. **去重失效**
   - 清空后，已提取的邮件会被重新处理
   - 可能导致重复的钉钉通知
   - 可能导致重复的文件提取（TODO 3）

3. **生产环境**
   - 生产环境应设置为 `False`
   - 或使用 `clear_old_records(days=30)` 定期清理旧数据

## 数据备份

### 备份数据库

```bash
# Windows
copy extracted_mails\data.db extracted_mails\data_backup_%date%.db

# Linux/Mac
cp extracted_mails/data.db extracted_mails/data_backup_$(date +%Y%m%d).db
```

### 恢复数据库

```bash
# Windows
copy extracted_mails\data_backup_20260311.db extracted_mails\data.db

# Linux/Mac
cp extracted_mails/data_backup_20260311.db extracted_mails/data.db
```

## 代码实现

### DatabaseManager.clear_all_data()

```python
def clear_all_data(self) -> dict:
    """清空所有数据（邮件记录和历史记录）

    Returns:
        dict: 清理统计信息
    """
    with self._get_connection() as conn:
        cursor = conn.cursor()

        # 获取清理前的统计
        cursor.execute("SELECT COUNT(*) as count FROM extracted_emails")
        emails_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM extraction_history")
        history_count = cursor.fetchone()['count']

        # 清空表
        cursor.execute("DELETE FROM extracted_emails")
        cursor.execute("DELETE FROM extraction_history")

        # 重置自增ID序列
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='extracted_emails'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='extraction_history'")

        logger.warning(f"已清空所有数据：{emails_count} 条邮件记录，{history_count} 条历史记录")

        return {
            'emails_deleted': emails_count,
            'history_deleted': history_count
        }
```

## 相关文件

- 配置文件：[.env](.env)
- 配置读取：[config/settings.py](config/settings.py)
- 数据库模块：[core/database.py](core/database.py)
- 主程序：[main.py](main.py)
- 测试脚本：[test_clear_db.py](test_clear_db.py)

---

**功能状态**：✅ 已完成并测试通过
**默认配置**：CLEAR_DB_ON_STARTUP=False（安全模式）
**建议用途**：仅在开发和测试时启用
