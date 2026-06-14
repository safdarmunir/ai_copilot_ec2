FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.2
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY data ./data

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
