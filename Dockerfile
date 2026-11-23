# Utilisation d'une image Python légère et officielle
FROM python:3.13-slim

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Installation des dépendances système de base si nécessaire

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2 libglib2.0-0 shared-mime-info fonts-liberation && rm -rf /var/lib/apt/lists/*

# Copie et installation des bibliothèques Python 
COPY pyproject.toml .

RUN pip install --no-cache-dir .

# Copie de vos scripts Python dans le conteneur (étape 3)
COPY . /app/

# Exposition du port FastAPI
EXPOSE 8021

ENV OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1

# Commande de lancement de l'application 
#CMD ["sh", "-c", "gunicorn -w 1 -b 0.0.0.0:${PORT:-8021} --timeout 180 --max-requests 2 --max-requests-jitter 1 app:app"]
CMD ["python" , "app.py"]
