import logging
import os
from playwright.sync_api import sync_playwright

# Configuration de base pour le logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)


def log_message(message):
    """
    Enregistre un message avec la date et l'heure actuelles au format français.

    Args:
        message (str): Le message à afficher avec l'horodatage.

    Returns:
        None
    """
    logging.info(f"{message}")


def load_env_variables(file_path=".env"):
    """
    Charge les variables d'environnement à partir d'un fichier .env.

    Args:
        file_path (str): Le chemin vers le fichier .env.

    Returns:
        dict: Un dictionnaire contenant les variables d'environnement.
    """
    env_vars = {}
    with open(file_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars


def login_to_coteur(page, username, password):
    """
    Se connecte à Coteur.com avec les informations d'identification fournies.

    Args:
        page: Instance de la page Playwright.
        username (str): Le nom d'utilisateur pour la connexion.
        password (str): Le mot de passe pour la connexion.

    Returns:
        None
    """
    # Aller sur la page de connexion
    page.goto("https://www.coteur.com/login")

    # Remplir les champs de connexion
    page.fill('input[name="username"]', username)  # Le champ username est "username"
    page.fill('input[name="password"]', password)  # Le champ password est "password"

    # (Optionnel) Coche la case "Se rappeler de moi" si nécessaire
    page.check('input[name="_remember_me"]')

    # Soumettre le formulaire de connexion
    page.click('button[type="submit"]')

    # Attendre que la page de membre soit complètement chargée
    page.wait_for_load_state('networkidle')

    # Aller sur la page membre
    page.goto("https://www.coteur.com/comparateur-de-cotes")

    # Attendre le chargement complet de la page
    page.wait_for_load_state('networkidle')


def extract_match_info(page):
    """
    Extrait les informations des matchs et les affiche dans la console.

    Args:
        page: Instance de la page Playwright.

    Returns:
        list: Liste contenant les informations des matchs.
    """
    matches = []

    # Sélectionner tous les blocs de matchs (chaque match est un div avec la classe "events")
    match_elements = page.query_selector_all('div.events')

    for match_element in match_elements:
        # Extraire l'heure du match
        match_time = match_element.query_selector('div.event-time').inner_text().strip()

        # Extraire les noms des équipes
        teams = match_element.query_selector_all('div.event-team')
        team_1 = teams[0].inner_text().strip()
        team_2 = teams[1].inner_text().strip()

        # Extraire le taux de retour
        return_element = match_element.query_selector('div.event-return span')
        match_return = return_element.inner_text().strip()

        # Extraire les cotes
        odds_elements = match_element.query_selector_all('strong[data-odd-target="odds"]')
        odd_1 = odds_elements[0].inner_text().strip()
        odd_2 = odds_elements[1].inner_text().strip()

        # Ajouter les informations du match à la liste
        match_info = {
            "time": match_time,
            "team_1": team_1,
            "team_2": team_2,
            "return": match_return,
            "odds": {
                "team_1": odd_1,
                "team_2": odd_2
            }
        }
        matches.append(match_info)

    return matches


def create_playwright_browser():
    """
    Crée et lance une instance de navigateur Playwright en mode headless (sans interface graphique).

    Returns:
        browser, page: L'instance du navigateur et de la page Playwright.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)  # Lancer en mode headless
    page = browser.new_page()
    return browser, page


def main():
    # Charger les variables d'environnement à partir du fichier .env
    env_vars = load_env_variables()

    # Récupérer les identifiants
    username = env_vars.get('USERNAME')
    password = env_vars.get('PASSWORD')

    # Vérifier que les identifiants sont bien chargés
    if not username or not password:
        log_message("Les identifiants ne sont pas définis dans le fichier .env.")
        return

    # Créer une instance de Playwright et se connecter
    browser, page = create_playwright_browser()

    try:
        # Se connecter à Coteur
        login_to_coteur(page, username, password)

        # Extraire les informations des matchs
        matches = extract_match_info(page)

        # Afficher les informations des matchs dans la console
        for match in matches:
            print(f"Match: {match['team_1']} vs {match['team_2']}")
            print(f"Heure: {match['time']}")
            print(f"Retour: {match['return']}")
            print(f"Cote {match['team_1']}: {match['odds']['team_1']}")
            print(f"Cote {match['team_2']}: {match['odds']['team_2']}")
            print("-" * 30)

    finally:
        # Fermer le navigateur
        browser.close()

    # Enregistrer un message de fin dans le log
    log_message("Fin de l'exécution du script.")


if __name__ == "__main__":
    main()
