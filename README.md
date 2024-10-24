# Scrapping Best Daily Bet

Ce script effectue le scraping de données de paris sportifs depuis **Coteur.com**, en se connectant avec des identifiants fournis, et extrait les informations des matchs de football et de tennis.

## Fonctionnalités

- Se connecte automatiquement à Coteur.com.
- Scrape les informations des matchs de football et de tennis.
- Trie les matchs par taux de retour et enregistre les résultats dans des fichiers texte.

## Prérequis

- **Python 3.x**
- **Packages requis** : installez-les avec :
- ```bash
  pip install -r requirements.txt
   ```
  
##  Détails du script

- Login : Se connecte à Coteur.com avec les informations d'identification fournies.
- Scraping : Extrait les informations des matchs de football et de tennis.
- Résultats : Trie les matchs par taux de retour et enregistre les résultats dans le dossier results.

##  Utilisation

1. Créez un fichier .env à la racine du projet avec vos identifiants coteur.com :
```bash
USERNAME=VotreNomUtilisateur
PASSWORD=VotreMotDePasse
```
2. Exécutez le script en double cliquant sur le fichier start.bat, ou faites la commande suivante:
```bash
python script.py
```
