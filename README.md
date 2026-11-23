# Gérer un projet d'infrastructure

# Description 

Mise en place d'un pipeline

1. Récupération des données d'un fichier XDF

2. Mise en forme des data , filtrage , génération des graphes et du rapport

3. Envoie de la réponse sous forme d'un ZIP



## 📂 Structure du Répertoire

```text
projet_12
├── pyproject.toml                                  # Gestion des dépendances Python (uv)
├── app.py                                          # serveur
├── config.py                                       # fichier de config
├── courbe_eeg.py                                   # génération des graphes eeg
├── docker-compose.yaml                             # fichier pour Docker
├── Dockerfile                                      # fichier pour Docker
├── EEG_result.py                                   # Calcul sur le signal EEG
├── energy.py                                       # Graphes énergie
├── fft.py                                          # Graphes FFT
├── head.py                                         # Position capteur EEG
├── lib.py                                          # librairie pour le projet
├── main.py                                         # Génération graphes et rapport
└── pyproject.toml                                  # fichier pour Docker
├── sca.py                                          # Graphes scalogrammes
├── topomap.py                                      # Graphes topomap
└── README.md   




