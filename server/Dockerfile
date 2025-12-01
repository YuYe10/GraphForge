FROM python:3.11-slim

WORKDIR /app

# 设置国内 Debian 镜像源（仅在 sources.list 存在时替换）
RUN if [ -f /etc/apt/sources.list ]; then \
            sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
            sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list; \
        else \
            echo "/etc/apt/sources.list not found; skipping apt mirrors replacement"; \
        fi

# 设置国内 Python 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 分阶段安装依赖：先安装核心依赖
COPY requirements.txt .
# 先安装轻量级依赖
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    neo4j>=5.14.0 \
    pymupdf==1.23.8 \
    pydantic-settings==2.1.0 \
    python-multipart==0.0.6 \
    redis==5.0.1 \
    rq==1.15.1 \
    python-dotenv==1.0.0 \
    aiofiles==23.2.1 \
    httpx==0.25.2 \
    python-docx==1.1.0 \
    beautifulsoup4==4.12.2 \
    pyyaml>=6.0 \
    fuzzywuzzy>=0.18.0 \
    python-Levenshtein>=0.23.0

# 再安装重量级依赖（可选，如果不需要可以注释掉）
RUN pip install --no-cache-dir \
    openai==1.3.0 \
    anthropic==0.39.0 \
    neo4j-graphrag>=0.5.0 \
    graphdatascience>=1.9

# 安装可选的AI依赖（如果不需要可以注释掉）
# RUN pip install --no-cache-dir sentence-transformers>=2.2.0 spacy>=3.7.0

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]