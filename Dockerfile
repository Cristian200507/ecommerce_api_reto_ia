# Imagen base oficial de Python ligera
FROM python:3.11-slim

# Prevenir generación de archivos .pyc y habilitar logs sin buffer en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias mínimas del sistema operativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero el manifiesto de dependencias para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY . .

# Exponer el puerto predeterminado de FastAPI / Uvicorn
EXPOSE 8000

# Comando de inicio del servidor en 0.0.0.0 para aceptar conexiones externas al contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
