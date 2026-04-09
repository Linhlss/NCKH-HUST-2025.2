FROM python:3.11-slim

ARG INSTALL_LORA=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_HEADLESS=true \
    OLLAMA_BASE_URL=http://host.docker.internal:11434

WORKDIR /app

COPY requirements ./requirements

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements/runtime.txt \
    && if [ "$INSTALL_LORA" = "true" ]; then pip install --no-cache-dir -r requirements/lora.txt; fi

COPY . .

EXPOSE 8000 8501

CMD ["python", "run_me.py", "all", "--setup", "none"]
