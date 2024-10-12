import logging
import os
from playwright.sync_api import sync_playwright
from tqdm import tqdm  # Pour la barre de progression

# Configuration de base pour le logger
def setup_logger():
    """
    Configure le logger de base pour l'application.
    """
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
    """
    # Aller sur la page de connexion
    page.goto("https://www.coteur.com/login")

    # Remplir les champs de connexion
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)

    # (Optionnel) Coche la case "Se rappeler de moi" si nécessaire
    page.check('input[name="_remember_me"]')

    # Soumettre le formulaire de connexion
    page.click('button[type="submit"]')

    # Attendre que la page de membre soit complètement chargée
    page.wait_for_load_state('networkidle')


def get_total_pages(page):
    """
    Récupère le nombre total de pages dans la pagination.

    Args:
        page: Instance de la page Playwright.

    Returns:
        int: Le dernier numéro de page à parcourir.
    """
    pagination = page.query_selector('ul.pagination')

    if pagination:
        # Trouver tous les éléments <a> qui contiennent un numéro de page
        page_links = pagination.query_selector_all('li.page-item a.page-link')

        # Récupérer uniquement les numéros de pages (ignorer ">>", "<<" etc.)
        valid_page_numbers = [link.inner_text().strip() for link in page_links if link.inner_text().strip().isdigit()]

        # Obtenir le dernier numéro de page
        if valid_page_numbers:
            last_page = int(valid_page_numbers[-1])
            return last_page

    # Si la pagination n'existe pas ou est mal formée, on retourne 1 (au cas où il n'y aurait qu'une page)
    return 1


def extract_football_matches(page):
    """
    Extrait les informations des matchs de football de la page actuelle et ignore les matchs avec des cotes à 0.

    Args:
        page: Instance de la page Playwright.

    Returns:
        list: Liste contenant les informations des matchs valides.
    """
    matches = []

    # Sélectionner tous les blocs de matchs (chaque match est un div avec la classe "events")
    match_elements = page.query_selector_all('div.events')

    for match_element in match_elements:
        # Extraire l'heure du match
        match_time = match_element.query_selector('div.event-time').inner_text().strip().replace("\n", " ")

        # Extraire les noms des équipes
        teams = match_element.query_selector_all('div.event-team')

        # Vérifier que nous avons bien deux équipes dans le bloc
        if len(teams) < 2:
            continue

        team_1 = teams[0].inner_text().strip()
        team_2 = teams[1].inner_text().strip()

        # Extraire le taux de retour
        return_element = match_element.query_selector('div.event-return span')
        match_return = return_element.inner_text().strip()

        # Extraire les cotes (victoire équipe 1, nul, victoire équipe 2)
        odds_elements = match_element.query_selector_all('strong[data-odd-target="odds"]')
        odd_1 = odds_elements[0].inner_text().strip()  # Cote pour la victoire de l'équipe 1
        odd_2 = odds_elements[1].inner_text().strip()  # Cote pour la victoire de l'équipe 2

        # Vérifier si une cote pour le match nul est présente
        odd_draw = None
        if len(odds_elements) > 2:
            odd_draw = odds_elements[2].inner_text().strip()  # Cote pour le match nul
        else:
            odd_draw = "0.00"  # Si pas de cote pour le match nul, on considère qu'elle est à 0

        # Vérifier que toutes les cotes ne sont pas égales à 0
        if odd_1 == "0.00" or odd_2 == "0.00" or odd_draw == "0.00":
            continue  # Ignorer ce match et passer au suivant

        # Ajouter les informations du match à la liste
        match_info = {
            "time": match_time,
            "team_1": team_1,
            "team_2": team_2,
            "return": match_return,
            "odds": {
                "team_1": odd_1,
                "team_2": odd_2,
                "draw": odd_draw
            }
        }
        matches.append(match_info)

    return matches


def paginate_and_extract_matches(page):
    """
    Parcourt les pages de la section "Cotes Foot" et extrait les informations des matchs.

    Args:
        page: Instance de la page Playwright.

    Returns:
        list: Liste contenant toutes les informations des matchs de toutes les pages.
    """
    all_matches = []

    # D'abord, trouver le nombre total de pages
    page.goto("https://www.coteur.com/cotes-foot")
    total_pages = get_total_pages(page)

    # Parcourir toutes les pages, de la page 1 à total_pages avec une barre de progression
    for current_page in tqdm(range(1, total_pages + 1), desc="Chargement des pages de matchs"):
        # Aller à la page des cotes de foot avec le numéro de page
        page.goto(f"https://www.coteur.com/cotes-foot?page={current_page}")

        # Attendre le chargement complet de la page
        page.wait_for_load_state('networkidle')

        # Extraire les informations des matchs sur la page actuelle
        matches = extract_football_matches(page)
        all_matches.extend(matches)

    return all_matches


def sort_matches_by_return(matches):
    """
    Trie la liste des matchs par taux de retour décroissant.

    Args:
        matches (list): La liste des matchs à trier.

    Returns:
        list: La liste triée des matchs.
    """
    # Convertir le taux de retour en flottant et trier par ce taux
    return sorted(matches, key=lambda match: float(match['return'].replace('%', '')), reverse=True)


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


def display_match_info(matches):
    """
    Affiche les informations des matchs dans la console.

    Args:
        matches (list): La liste contenant les informations des matchs.
    """
    for match in matches:
        print(f"Match: {match['team_1']} vs {match['team_2']}")
        print(f"Heure: {match['time']}")
        print(f"Retour: {match['return']}")
        print(f"Cote {match['team_1']}: {match['odds']['team_1']}")
        if match['odds']['draw']:
            print(f"Cote match nul: {match['odds']['draw']}")
        print(f"Cote {match['team_2']}: {match['odds']['team_2']}")
        print("-" * 30)


def main():
    # Configurer le logger
    setup_logger()

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

        # Parcourir les pages et extraire les informations des matchs
        all_matches = paginate_and_extract_matches(page)

        # Trier les matchs par taux de retour décroissant
        sorted_matches = sort_matches_by_return(all_matches)

        # Afficher les informations des matchs
        display_match_info(sorted_matches)

    finally:
        # Fermer le navigateur
        browser.close()

    # Enregistrer un message de fin dans le log
    log_message("Fin de l'exécution du script.")


if __name__ == "__main__":
    main()
