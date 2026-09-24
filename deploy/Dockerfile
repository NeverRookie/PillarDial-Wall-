FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统字体与必要依赖 (支持中文和无衬线字体)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fonts-dejavu-core \
    fontconfig \
    curl \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY app/ ./app/
COPY static/ ./static/

# 环境变量
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
