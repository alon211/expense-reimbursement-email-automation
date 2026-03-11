FROM python:3.9-slim

# 安装系统依赖（压缩文件解压工具）
RUN apt-get update && apt-get install -y \
    p7zip-full \
    unrar-free \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY config/ ./config/
COPY core/ ./core/
COPY utils/ ./utils/
COPY rules/ ./rules/
COPY main.py .

# 创建必要的目录
RUN mkdir -p /app/logs /app/extracted_mails

# 复制启动脚本
COPY .entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 设置环境变量
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 健康检查（每30秒检查一次进程）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

# 使用启动脚本
ENTRYPOINT ["/app/entrypoint.sh"]
