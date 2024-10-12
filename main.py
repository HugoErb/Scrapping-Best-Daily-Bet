import logging
import os
from dotenv import load_dotenv
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


def login_to_coteur(page, username, password):
    """
    Se connecte à Coteur.com avec les informations d'identification fournies.

    Args:
        page: Instance de la page Playwright.
        username (str): Le nom d'utilisateur pour la connexion.
        password (str): Le mot de passe pour la connexion.

    Returns:
        str: Le contenu HTML de la page après connexion.
    """
    # Aller sur la page de connexion
    page.goto("https://www.coteur.com/login")

    # Remplir les champs de connexion
    page.fill('input[name="pseudo"]', username)
    page.fill('input[name="pass"]', password)

    # Soumettre le formulaire de connexion
    page.click('input[type="submit"]')

    # Attendre que la page se charge après la connexion
    page.wait_for_load_state('networkidle')

    # Vérifier si la connexion a réussi en allant sur une page réservée aux membres
    page.goto("https://www.coteur.com/espace-membre.html")
    return page.content()


def create_playwright_browser():
    """
    Crée et lance une instance de navigateur Playwright (Chromium).

    Returns:
        browser, page: L'instance du navigateur et de la page Playwright.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    return browser, page


def main():
    # Charger les variables d'environnement depuis le fichier .env
    load_dotenv()

    # Récupérer les identifiants
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')

    # Vérifier que les identifiants sont bien chargés
    if not username or not password:
        log_message("Les identifiants ne sont pas définis dans le fichier .env.")
        return

    # Créer une instance de Playwright et se connecter
    browser, page = create_playwright_browser()

    # Se connecter à Coteur et récupérer le contenu
    try:
        content = login_to_coteur(page, username, password)
        print(content)
    finally:
        # Fermer le navigateur
        browser.close()

    # Enregistrer un message de fin dans le log
    log_message("Fin de l'exécution du script.")


if __name__ == "__main__":
    main()
