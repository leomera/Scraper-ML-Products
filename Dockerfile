# Usa a imagem oficial do Playwright na versão EXATA que o requirements instalou
FROM mcr.microsoft.com/playwright/python:v1.61.0-jammy

WORKDIR /app

# Instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da sua API para dentro do servidor
COPY . .

# Comando para rodar o FastAPI na porta definida pelo Render
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]