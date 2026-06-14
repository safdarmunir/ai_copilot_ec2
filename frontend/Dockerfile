FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.2
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
