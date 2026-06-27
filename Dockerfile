FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt /app/
#install cpu only torch as nvidia wheel bloats size
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \ 
    torch

RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]