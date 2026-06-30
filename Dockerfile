FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-web.txt pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY data ./data
COPY web ./web

RUN pip install --no-cache-dir -r requirements-web.txt

EXPOSE 8501

CMD ["streamlit", "run", "web/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
