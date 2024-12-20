# Scrapping Best Bet

Ce script effectue le scraping de données de paris sportifs depuis **Coteur.com**, en se connectant avec des identifiants fournis, et extrait les informations des matchs de football et de tennis pour des bookmakers spécifiques ou pour tous les bookmakers disponibles.

## Fonctionnalités

- Se connecte automatiquement à Coteur.com.
- Permet de sélectionner un bookmaker ou tous les bookmakers pour le scraping.
- Gère automatiquement la sélection des bookmakers sur la page dédiée avant le scraping.
- Scrape les informations des matchs de football et de tennis pour chaque bookmaker sélectionné.
- Trie les matchs par taux de retour et enregistre les résultats dans des fichiers texte nommés selon le sport, le bookmaker, et la date du scraping.

## Prérequis

- **Python 3.x**
- **Packages requis** : Installez-les avec :
  ```bash
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

## Détails du Script

### **1. Connexion :**
- Le script se connecte à Coteur.com avec les informations d'identification fournies dans le fichier `.env`.

### **2. Sélection des Bookmakers :**
- Une liste des bookmakers est affichée au démarrage.
- L'utilisateur peut sélectionner un bookmaker spécifique ou tous les bookmakers.
- Si "Tous les bookmakers" est sélectionné, le script scrape les matchs pour chaque bookmaker un par un.

### **3. Scraping des Matchs :**
- Le script extrait les informations des matchs de football et de tennis pour les bookmakers sélectionnés.
- Les informations incluent : 
  - Les équipes ou joueurs.
  - L'heure du match.
  - Le taux de retour.
  - Les cotes pour les différents résultats (victoire, nul, etc.).
- Trie les matchs par taux de retour décroissant.

### **4. Résultats :**
- Les résultats sont enregistrés dans des fichiers texte nommés comme suit : 
  ```
  <sport>_<bookmaker>_<date>.txt
  ```
  Exemple : `foot_betclic_16-11-2024.txt`

## Utilisation

1. **Configurer vos identifiants :**
   - Créez un fichier `.env` à la racine du projet avec vos identifiants Coteur.com :
     ```bash
     USERNAME=VotreNomUtilisateur
     PASSWORD=VotreMotDePasse
     ```

2. **Exécuter le script :**
   - Double-cliquez sur le fichier `start.bat`, ou exécutez la commande suivante dans le terminal :
     ```bash
     python script.py
     ```

3. **Choisir un bookmaker :**
   - Une liste de bookmakers sera affichée avec des numéros correspondants.
   - Entrez le numéro du bookmaker à scraper, ou sélectionnez "Tous les bookmakers".

4. **Vérifier les résultats :**
   - Les fichiers texte contenant les résultats seront enregistrés dans le dossier `results`.

---

### Exemple de Workflow :
1. Lancer le script.
2. Sélectionner un bookmaker (exemple : `2` pour Betclic) ou "Tous".
3. Les matchs sont scrappés et triés automatiquement.
4. Les fichiers texte sont générés avec les données des matchs.

---