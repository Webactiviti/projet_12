# Utilisation d'une image Python légère et officielle
FROM python:3.11-slim

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Installation des dépendances système de base si nécessaire
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des bibliothèques Python (nous y reviendrons à l'étape 2)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de vos scripts Python dans le conteneur (étape 3)
COPY . /app/

# Exposition du port FastAPI
EXPOSE 8000

# Commande de lancement de l'application via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8021"]
