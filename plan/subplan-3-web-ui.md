# 子计划3：本地Docker Web UI控制端

**目标**: 创建可视化的Web管理界面，支持配置管理、远程触发、结果查看和下载

**预计工期**: 7-10天

**技术栈**:
- 后端: FastAPI 0.104+ (Python异步框架)
- 前端: Vue.js 3 + Vite + Element Plus
- 数据库: SQLite (复用现有)

---

## 📋 执行步骤

### 阶段1：项目初始化（1天）

#### 步骤1.1：更新依赖

在 [requirements.txt](../requirements.txt) 中添加：

```txt
# 现有依赖...
pytz>=2024.1
requests>=2.31.0
imaplib2>=3.6
python-dotenv>=1.0.0
chardet>=5.2.0
pycryptodome>=3.20.0
py7zr>=0.20.0
rarfile>=4.0

# Web UI后端依赖
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6

# GitHub API客户端
PyGithub>=1.59.1
```

#### 步骤1.2：创建项目结构

```bash
# 创建后端目录结构
mkdir -p web_backend/api
mkdir -p web_backend/models
mkdir -p web_backend/services

# 创建前端目录
mkdir -p web_frontend/src/{views,components,api,stores}
```

#### 步骤1.3：创建requirements.txt（前端）

创建 [web_frontend/package.json](../web_frontend/package.json)（后面会创建）：

```json
{
  "name": "email-web-ui",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.0",
    "element-plus": "^2.5.0",
    "@element-plus/icons-vue": "^2.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

---

### 阶段2：后端API开发（3-4天）

#### 步骤2.1：创建FastAPI应用入口

创建 [web_backend/main.py](../web_backend/main.py)：

```python
"""
FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# 导入API路由
from api import extraction, rules, records, config, github

# 创建应用
app = FastAPI(
    title="邮件自动化服务API",
    description="本地Docker Web UI控制端",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(extraction.router, prefix="/api/extraction", tags=["提取"])
app.include_router(rules.router, prefix="/api/rules", tags=["规则"])
app.include_router(records.router, prefix="/api/records", tags=["记录"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])
app.include_router(github.router, prefix="/api/github", tags=["GitHub"])

# 根路径
@app.get("/")
async def root():
    return {
        "message": "邮件自动化服务API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 健康检查
@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 步骤2.2：创建数据模型

创建 [web_backend/models/schemas.py](../web_backend/models/schemas.py)：

```python
"""
Pydantic数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ConfigSchema(BaseModel):
    """系统配置"""
    local_save_path: str = Field(default="./extracted_mails", description="本地保存路径")
    github_token: str = Field(default="", description="GitHub Personal Access Token")
    github_repo: str = Field(default="", description="GitHub仓库 (username/repo)")
    execution_mode: str = Field(default="github", description="执行模式: github | local")

    class Config:
        json_schema_extra = {
            "example": {
                "local_save_path": "./extracted_mails",
                "github_token": "ghp_xxx",
                "github_repo": "username/repo",
                "execution_mode": "github"
            }
        }


class ExtractionRequest(BaseModel):
    """提取请求"""
    mode: str = Field(default="github", description="执行模式: github | local")
    time_range_days: int = Field(default=20, ge=1, le=365, description="搜索时间范围（天）")
    rule_filter: Optional[str] = Field(default=None, description="规则ID过滤器（逗号分隔）")

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "github",
                "time_range_days": 20,
                "rule_filter": "rule_002,rule_003"
            }
        }


class ExtractionResponse(BaseModel):
    """提取响应"""
    task_id: str = Field(description="任务ID")
    status: str = Field(description="状态: pending | running | success | failed")
    message: str = Field(description="消息")
    executed_at: Optional[str] = Field(default=None, description="执行时间")


class RuleSchema(BaseModel):
    """规则配置"""
    rule_id: str
    rule_name: str
    enabled: bool
    description: str
    match_conditions: dict
    extract_options: dict
    output_subdir: str


class MailRecordSchema(BaseModel):
    """邮件记录"""
    id: int
    message_id: str
    subject: str
    sender: str
    mail_date: str
    rule_id: str
    extracted_at: str
    attachment_count: int
```

#### 步骤2.3：创建配置管理API

创建 [web_backend/api/config.py](../web_backend/api/config.py)：

```python
"""
配置管理API
"""
from fastapi import APIRouter, HTTPException
from models.schemas import ConfigSchema
import sqlite3
import json
from pathlib import Path

router = APIRouter(prefix="/config", tags=["配置"])

CONFIG_DB = "extracted_mails/web_config.db"


def init_config_db():
    """初始化配置数据库"""
    Path(CONFIG_DB).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(CONFIG_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


@router.get("/", response_model=ConfigSchema)
async def get_config():
    """获取系统配置"""
    init_config_db()

    conn = sqlite3.connect(CONFIG_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT key, value FROM config")
    rows = cursor.fetchall()

    config = {
        "local_save_path": "./extracted_mails",
        "github_token": "",
        "github_repo": "",
        "execution_mode": "github"
    }

    for key, value in rows:
        config[key] = value

    conn.close()
    return config


@router.put("/", response_model=ConfigSchema)
async def update_config(config: ConfigSchema):
    """更新系统配置"""
    init_config_db()

    conn = sqlite3.connect(CONFIG_DB)
    cursor = conn.cursor()

    # 更新或插入配置
    for key, value in config.dict().items():
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value)
            VALUES (?, ?)
        """, (key, str(value)))

    conn.commit()
    conn.close()

    return config


@router.post("/validate-github-token")
async def validate_github_token(token: str):
    """验证GitHub Token有效性"""
    try:
        import requests

        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            return {
                "valid": True,
                "username": user_data.get("login")
            }
        else:
            return {"valid": False}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### 步骤2.4：创建提取API

创建 [web_backend/api/extraction.py](../web_backend/api/extraction.py)：

```python
"""
提取API
"""
from fastapi import APIRouter, BackgroundTasks
from models.schemas import ExtractionRequest, ExtractionResponse
import uuid
from services.extraction_service import ExtractionService

router = APIRouter(prefix="/extraction", tags=["提取"])

service = ExtractionService()


@router.post("/trigger", response_model=ExtractionResponse)
async def trigger_extraction(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """
    触发邮件提取

    mode: "github" | "local"
    - github: 远程执行（GitHub Actions）
    - local: 本地执行（备用）
    """
    task_id = str(uuid.uuid4())

    if request.mode == "github":
        # 触发GitHub Actions（后台执行）
        background_tasks.add_task(
            service.trigger_github_extraction,
            task_id,
            request.time_range_days,
            request.rule_filter
        )
    else:
        # 本地执行
        background_tasks.add_task(
            service.trigger_local_extraction,
            task_id,
            request.time_range_days,
            request.rule_filter
        )

    return ExtractionResponse(
        task_id=task_id,
        status="pending",
        message=f"提取任务已创建，模式: {request.mode}"
    )


@router.get("/status/{task_id}")
async def get_extraction_status(task_id: str):
    """查询提取任务状态"""
    return await service.get_task_status(task_id)


@router.get("/results/{task_id}")
async def get_extraction_results(task_id: str):
    """获取提取结果（JSON）"""
    return await service.get_task_results(task_id)
```

#### 步骤2.5：创建规则管理API

创建 [web_backend/api/rules.py](../web_backend/api/rules.py)：

```python
"""
规则管理API
"""
from fastapi import APIRouter
from models.schemas import RuleSchema
from core.rule_loader import RuleLoader
import json
from pathlib import Path

router = APIRouter(prefix="/rules", tags=["规则"])

RULES_FILE = "rules/parse_rules.json"


@router.get("/")
async def list_rules():
    """获取所有规则"""
    loader = RuleLoader(RULES_FILE)
    rules = loader.get_all_rules()
    return {"rules": rules}


@router.post("/")
async def create_rule(rule: RuleSchema):
    """创建新规则"""
    loader = RuleLoader(RULES_FILE)
    # TODO: 实现添加规则逻辑
    return {"message": "创建成功"}


@router.put("/{rule_id}")
async def update_rule(rule_id: str, rule: RuleSchema):
    """更新规则"""
    # TODO: 实现更新规则逻辑
    return {"message": "更新成功"}


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str):
    """删除规则"""
    # TODO: 实现删除规则逻辑
    return {"message": "删除成功"}


@router.post("/test")
async def test_rule(rule: RuleSchema, test_mail: dict):
    """测试规则匹配"""
    from core.rule_loader import Rule

    r = Rule(
        rule_id=rule.rule_id,
        rule_name=rule.rule_name,
        enabled=rule.enabled,
        description=rule.description,
        match_conditions=rule.match_conditions,
        extract_options=rule.extract_options,
        output_subdir=rule.output_subdir
    )

    matched = r.match(
        subject=test_mail.get("subject", ""),
        sender=test_mail.get("sender", ""),
        body=test_mail.get("body", "")
    )

    return {"matched": matched}
```

#### 步骤2.6：创建邮件记录API

创建 [web_backend/api/records.py](../web_backend/api/records.py)：

```python
"""
邮件记录API
"""
from fastapi import APIRouter
from core.database import DatabaseManager
from pathlib import Path

router = APIRouter(prefix="/records", tags=["记录"])

DB_PATH = "extracted_mails/data.db"


@router.get("/")
async def list_records(
    page: int = 1,
    page_size: int = 20,
    rule_id: str = None,
    keyword: str = None
):
    """分页查询邮件记录"""
    db = DatabaseManager(DB_PATH)

    # TODO: 实现分页查询逻辑
    stats = db.get_statistics()

    return {
        "total": stats["total_emails"],
        "page": page,
        "page_size": page_size,
        "records": []
    }


@router.get("/stats")
async def get_statistics():
    """获取统计信息"""
    db = DatabaseManager(DB_PATH)
    return db.get_statistics()
```

#### 步骤2.7：创建GitHub集成API

创建 [web_backend/api/github.py](../web_backend/api/github.py)：

```python
"""
GitHub集成API
"""
from fastapi import APIRouter, HTTPException
from core.github_client import GitHubWorkflowClient

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.post("/trigger")
async def trigger_github_workflow(
    time_range_days: int = 20,
    rule_filter: str = None
):
    """触发GitHub Actions工作流"""
    # TODO: 从配置数据库读取token和repo
    # client = GitHubWorkflowClient(token, repo)
    # run_id = client.trigger_workflow("email-extraction.yml", {...})
    return {"message": "触发成功", "run_id": "12345"}


@router.get("/status/{run_id}")
async def get_workflow_status(run_id: str):
    """查询工作流状态"""
    # TODO: 实现状态查询
    return {"status": "running"}
```

#### 步骤2.8：创建服务层

创建 [web_backend/services/extraction_service.py](../web_backend/services/extraction_service.py)：

```python
"""
提取服务
"""
import asyncio
from typing import Dict


class ExtractionService:
    """提取服务"""

    def __init__(self):
        self.tasks = {}  # 任务状态存储

    async def trigger_github_extraction(
        self,
        task_id: str,
        time_range_days: int,
        rule_filter: str
    ):
        """触发GitHub Actions执行"""
        # 更新任务状态
        self.tasks[task_id] = {
            "status": "running",
            "mode": "github",
            "progress": 0
        }

        try:
            # 调用GitHub API
            from core.github_client import GitHubWorkflowClient
            from api.config import get_config

            config = await get_config()

            client = GitHubWorkflowClient(
                token=config.github_token,
                repo=config.github_repo
            )

            run_id = client.trigger_workflow(
                workflow_file="email-extraction.yml",
                inputs={"time_range_days": str(time_range_days)}
            )

            # 等待完成
            outputs = client.get_workflow_outputs(run_id)

            # 更新任务状态
            self.tasks[task_id] = {
                "status": "success",
                "mode": "github",
                "result": outputs,
                "run_id": run_id
            }

        except Exception as e:
            self.tasks[task_id] = {
                "status": "failed",
                "error": str(e)
            }

    async def trigger_local_extraction(
        self,
        task_id: str,
        time_range_days: int,
        rule_filter: str
    ):
        """触发本地执行（备用）"""
        # TODO: 实现本地提取逻辑
        pass

    async def get_task_status(self, task_id: str) -> Dict:
        """查询任务状态"""
        return self.tasks.get(task_id, {"status": "not_found"})

    async def get_task_results(self, task_id: str) -> Dict:
        """获取任务结果"""
        task = self.tasks.get(task_id)
        if task and task.get("status") == "success":
            return task.get("result", {})
        return {}
```

---

### 阶段3：前端界面开发（3-4天）

#### 步骤3.1：初始化Vue项目

```bash
cd web_frontend

# 如果还没有初始化
npm create vite@latest . -- --template vue
npm install

# 安装依赖
npm install vue-router pinia axios element-plus @element-plus/icons-vue
```

#### 步骤3.2：创建Vite配置

创建 [web_frontend/vite.config.js](../web_frontend/vite.config.js)：

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

#### 步骤3.3：创建API请求封装

创建 [web_frontend/src/api/request.js](../web_frontend/src/api/request.js)：

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    ElMessage.error(error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default request
```

#### 步骤3.4：创建API模块

创建 [web_frontend/src/api/extraction.js](../web_frontend/src/api/extraction.js)：

```javascript
import request from './request'

export function triggerExtraction(data) {
  return request.post('/extraction/trigger', data)
}

export function getExtractionStatus(taskId) {
  return request.get(`/extraction/status/${taskId}`)
}

export function getExtractionResults(taskId) {
  return request.get(`/extraction/results/${taskId}`)
}
```

创建 [web_frontend/src/api/config.js](../web_frontend/src/api/config.js)：

```javascript
import request from './request'

export function getConfig() {
  return request.get('/config/')
}

export function updateConfig(config) {
  return request.put('/config/', config)
}

export function validateGitHubToken(token) {
  return request.post('/config/validate-github-token', { token })
}
```

创建 [web_frontend/src/api/rules.js](../web_frontend/src/api/rules.js)：

```javascript
import request from './request'

export function listRules() {
  return request.get('/rules/')
}

export function createRule(rule) {
  return request.post('/rules/', rule)
}

export function updateRule(ruleId, rule) {
  return request.put(`/rules/${ruleId}`, rule)
}

export function deleteRule(ruleId) {
  return request.delete(`/rules/${ruleId}`)
}

export function testRule(rule, testMail) {
  return request.post('/rules/test', { rule, test_mail: testMail })
}
```

#### 步骤3.5：创建主应用

创建 [web_frontend/src/main.js](../web_frontend/src/main.js)：

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

#### 步骤3.6：创建路由配置

创建 [web_frontend/src/router/index.js](../web_frontend/src/router/index.js)：

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/rules',
    name: 'RulesManager',
    component: () => import('../views/RulesManager.vue')
  },
  {
    path: '/records',
    name: 'MailRecords',
    component: () => import('../views/MailRecords.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

#### 步骤3.7：创建视图页面

创建 [web_frontend/src/views/Dashboard.vue](../web_frontend/src/views/Dashboard.vue)：

```vue
<template>
  <div class="dashboard">
    <h1>仪表板</h1>

    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <el-statistic title="总提取邮件" :value="stats.totalEmails" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="今日新增" :value="stats.todayNew" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="规则数量" :value="stats.ruleCount" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="存储空间" :value="stats.storageUsed" suffix="MB" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>快速操作</span>
      </template>
      <el-space>
        <el-button type="primary" @click="triggerExtraction('github')">
          立即提取（GitHub Actions）
        </el-button>
        <el-button @click="triggerExtraction('local')">
          本地提取（备用）
        </el-button>
      </el-space>
    </el-card>

    <!-- 最近记录 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>最近提取记录</span>
      </template>
      <el-table :data="recentRecords">
        <el-table-column prop="subject" label="主题" />
        <el-table-column prop="sender" label="发件人" />
        <el-table-column prop="extractedAt" label="提取时间" />
        <el-table-column prop="ruleId" label="匹配规则" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { triggerExtraction as apiTrigger } from '../api/extraction'
import { ElMessage } from 'element-plus'

const stats = ref({
  totalEmails: 0,
  todayNew: 0,
  ruleCount: 0,
  storageUsed: 0
})

const recentRecords = ref([])

const triggerExtraction = async (mode) => {
  try {
    const response = await apiTrigger({ mode, time_range_days: 20 })
    ElMessage.success(`提取任务已创建: ${response.task_id}`)
  } catch (error) {
    ElMessage.error('触发失败: ' + error.message)
  }
}

onMounted(() => {
  // 加载统计数据
})
</script>
```

创建 [web_frontend/src/views/Settings.vue](../web_frontend/src/views/Settings.vue)：

```vue
<template>
  <div class="settings">
    <h1>系统设置</h1>

    <el-card>
      <template #header>
        <span>系统配置</span>
      </template>

      <el-form :model="config" label-width="150px">
        <el-form-item label="本地保存路径">
          <el-input v-model="config.localSavePath" />
        </el-form-item>

        <el-form-item label="GitHub Token">
          <el-input v-model="config.githubToken" type="password" show-password />
          <el-button size="small" @click="validateToken">验证Token</el-button>
        </el-form-item>

        <el-form-item label="GitHub仓库">
          <el-input v-model="config.githubRepo" placeholder="username/repo" />
        </el-form-item>

        <el-form-item label="执行模式">
          <el-radio-group v-model="config.executionMode">
            <el-radio label="github">GitHub Actions（推荐）</el-radio>
            <el-radio label="local">本地执行（备用）</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateConfig, validateGitHubToken } from '../api/config'
import { ElMessage } from 'element-plus'

const config = ref({
  local_save_path: './extracted_mails',
  github_token: '',
  github_repo: '',
  execution_mode: 'github'
})

const loadConfig = async () => {
  try {
    const data = await getConfig()
    config.value = data
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

const saveConfig = async () => {
  try {
    await updateConfig(config.value)
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

const validateToken = async () => {
  try {
    const result = await validateGitHubToken(config.value.github_token)
    if (result.valid) {
      ElMessage.success(`Token有效，用户: ${result.username}`)
    } else {
      ElMessage.error('Token无效')
    }
  } catch (error) {
    ElMessage.error('验证失败: ' + error.message)
  }
}

onMounted(() => {
  loadConfig()
})
</script>
```

---

### 阶段4：Docker多容器编排（1-2天）

#### 步骤4.1：创建后端Dockerfile

创建 [Dockerfile.backend](../Dockerfile.backend)：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY core/ ./core/
COPY config/ ./config/
COPY utils/ ./utils/
COPY web_backend/ ./web_backend/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "web_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 步骤4.2：创建前端Dockerfile

创建 [Dockerfile.frontend](../Dockerfile.frontend)：

```dockerfile
# 构建阶段
FROM node:18-alpine as builder

WORKDIR /app
COPY web_frontend/package*.json ./
RUN npm install
COPY web_frontend/ ./
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 步骤4.3：创建nginx配置

创建 [nginx.conf](../nginx.conf)：

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://web-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 步骤4.4：更新docker-compose.yml

更新 [docker-compose.yml](../docker-compose.yml)（完整版）：

```yaml
version: '3.8'

services:
  # Web后端
  web-backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: email-web-backend
    ports:
      - "8000:8000"
    volumes:
      - ./core:/app/core
      - ./config:/app/config
      - ./utils:/app/utils
      - ./extracted_mails:/app/extracted_mails
      - ./rules:/app/rules
      - ./web_backend:/app/web_backend
    environment:
      - DATABASE_URL=sqlite:///extracted_mails/data.db
      - WEB_CONFIG_DB=sqlite:///extracted_mails/web_config.db
    restart: unless-stopped

  # Web前端
  web-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: email-web-frontend
    ports:
      - "80:80"
    depends_on:
      - web-backend
    restart: unless-stopped

  # 邮件提取服务（本地备用）
  email-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: email-service
    volumes:
      - ./extracted_mails:/app/extracted_mails
      - ./logs:/app/logs
      - ./rules:/app/rules
    environment:
      - IMAP_HOST=${IMAP_HOST}
      - IMAP_USER=${IMAP_USER}
      - IMAP_PASS=${IMAP_PASS}
      - DINGTALK_WEBHOOK=${DINGTALK_WEBHOOK}
      - DINGTALK_SECRET=${DINGTALK_SECRET}
      - CHECK_INTERVAL=${CHECK_INTERVAL:-60}
    restart: unless-stopped
    profiles:
      - local  # 仅在本地模式时启动
```

---

## 📊 完成标准

### 必须完成（P0）

- [ ] web_backend/ 后端API完整
- [ ] web_frontend/ 前端界面可访问
- [ ] Dockerfile.backend 和 Dockerfile.frontend
- [ ] docker-compose.yml 多容器编排
- [ ] nginx.conf 反向代理配置

### 推荐完成（P1）

- [ ] 仪表板页面（统计、快速操作）
- [ ] 规则管理页面（列表、编辑、测试）
- [ ] 系统设置页面（配置管理）
- [ ] 完整流程测试通过

### 可选完成（P2）

- [ ] 邮件记录页面
- [ ] WebSocket实时状态推送
- [ ] 主题切换
- [ ] 响应式设计

---

## 🧪 测试计划

### 后端API测试

```bash
# 启动后端
docker-compose up web-backend

# 测试API
curl http://localhost:8000/health
curl http://localhost:8000/api/config/
```

### 前端界面测试

```bash
# 开发模式
cd web_frontend
npm run dev

# 访问 http://localhost:3000
```

### 完整系统测试

```bash
# 启动所有服务
docker-compose up -d

# 访问 http://localhost
# 执行用户流程
```

---

## 🎯 最终目标

完成本计划后，整个混合架构系统将上线：

```
✅ 计划1: 本地Docker化 - 完成
✅ 计划2: GitHub Actions - 完成
✅ 计划3: Web UI控制端 - 完成
```

---

**相关文档**:
- [子计划1: 本地Docker化](./subplan-1-local-docker.md)
- [子计划2: GitHub Actions](./subplan-2-github-actions.md)
- [主计划文件](./bubbly-booping-rossum.md)
