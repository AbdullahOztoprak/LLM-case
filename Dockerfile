FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY sources.yaml ./

RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "devdocs_rag.api:app", "--host", "0.0.0.0", "--port", "8000"]
