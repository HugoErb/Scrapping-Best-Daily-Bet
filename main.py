import logging
import os
import datetime
from playwright.sync_api import sync_playwright
from tqdm import tqdm
from constants import BOOKMAKERS


def setup_logger():
    """
    Configure le logger pour l'application.
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


def ask_user_for_bookmaker():
    """
    Demande à l'utilisateur quel bookmaker choisir.
    """
    print("Liste des bookmakers disponibles :")
    for i, bookmaker in enumerate(BOOKMAKERS, 1):
        print(f"{i}. {bookmaker['name']}")
    print(f"{len(BOOKMAKERS) + 1}. Tous les bookmakers")

    choice = int(input("\nEntrez le numéro du bookmaker à récupérer : "))

    if choice == len(BOOKMAKERS) + 1:
        return [b['id'] for b in BOOKMAKERS]
    elif 1 <= choice <= len(BOOKMAKERS):
        return [BOOKMAKERS[choice - 1]['id']]
    else:
        print("Choix invalide. Réessayez.")
        return ask_user_for_bookmaker()


def select_bookmakers(page, selected_bookmakers):
    """
    Sélectionne les bookmakers sur la page des paramètres et valide.
    """
    log_message("Navigation vers la page des sélections des bookmakers.")
    page.goto("https://www.coteur.com/bookmaker/selection")

    # Vérifiez que vous êtes bien sur la page attendue
    if "selection" not in page.url:
        log_message("Erreur : Vous n'êtes pas connecté. Impossible d'accéder à la page des sélections.")
        return

    log_message("Attente de la page.")
    page.wait_for_selector('form[action="?action=update"]')  # Attendre que le formulaire soit visible

    # Sélectionner uniquement les checkboxes dans la balise <form>
    checkboxes = page.query_selector_all('form[action="?action=update"] input.form-check-input[type="checkbox"]')

    # Décochez toutes les checkboxes trouvées
    for checkbox in checkboxes:
        if checkbox.is_checked():
            checkbox.click()

    # Cochez uniquement les bookmakers sélectionnés
    for bookmaker_id in selected_bookmakers:
        checkbox_selector = f'form[action="?action=update"] input.form-check-input[value="{bookmaker_id}"]'
        checkbox = page.query_selector(checkbox_selector)

        if checkbox:
            try:
                checkbox.scroll_into_view_if_needed()
                checkbox.click()
            except Exception as e:
                log_message(f"Erreur lors de la sélection du bookmaker ID {bookmaker_id} : {str(e)}")
        else:
            log_message(f"Checkbox introuvable pour le bookmaker ID {bookmaker_id}.")

    # Soumettez le formulaire
    page.click('form[action="?action=update"] button[type="submit"]')
    page.wait_for_load_state('networkidle')
    log_message("Validation du changement de bookmaker soumis avec succès.")


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


def extract_matches(page, sport="football"):
    """
    Extrait les informations des matchs de la page actuelle et ignore les matchs avec des cotes à 0.
    La vérification de la cote de match nul est ignorée pour les sports comme le tennis.

    Args:
        page: Instance de la page Playwright.
        sport (str): Le sport ("football" ou "tennis").

    Returns:
        list: Liste contenant les informations des matchs valides.
    """
    matches = []

    # Sélectionner tous les blocs de matchs (chaque match est un div avec la classe "events")
    match_elements = page.query_selector_all('div.events')

    for match_element in match_elements:
        # Extraire l'heure du match
        match_time = match_element.query_selector('div.event-time').inner_text().strip().replace("\n", " ")

        # Extraire les noms des équipes ou joueurs
        teams = match_element.query_selector_all('div.event-team')

        # Vérifier que nous avons bien deux équipes ou joueurs dans le bloc
        if len(teams) < 2:
            continue

        team_1 = teams[0].inner_text().strip()
        team_2 = teams[1].inner_text().strip()

        # Extraire le taux de retour
        return_element = match_element.query_selector('div.event-return span')
        match_return = return_element.inner_text().strip()

        # Extraire les cotes (victoire équipe 1, match nul, et victoire équipe 2)
        odds_elements = match_element.query_selector_all('strong[data-odd-target="odds"]')

        # Ajustement pour les cotes : 1ère équipe, match nul, 2ème équipe
        odd_1 = odds_elements[0].inner_text().strip()  # Cote pour la victoire de l'équipe 1
        odd_draw = None
        odd_2 = None

        if sport == "football" and len(odds_elements) == 3:
            odd_draw = odds_elements[1].inner_text().strip()  # Cote pour le match nul
            odd_2 = odds_elements[2].inner_text().strip()  # Cote pour la victoire de l'équipe 2
        else:
            odd_2 = odds_elements[1].inner_text().strip()  # Pas de cote de match nul dans le tennis

        # Vérifier que les cotes ne sont pas égales à 0 (ignorer les matchs avec des cotes à 0)
        if odd_1 == "0.00" or odd_2 == "0.00":
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
                "draw": odd_draw if odd_draw else ""
            }
        }
        matches.append(match_info)

    return matches


def paginate_and_extract_matches(page, url, sport="football"):
    """
    Parcourt les pages de la section fournie dans l'URL et extrait les informations des matchs.

    Args:
        page: Instance de la page Playwright.
        url: L'URL à scrapper (cotes foot ou cotes tennis).
        sport: Le type de sport ("football" ou "tennis").

    Returns:
        list: Liste contenant toutes les informations des matchs de toutes les pages.
    """
    all_matches = []

    # Aller à la première page de la section donnée
    page.goto(url)
    total_pages = get_total_pages(page)

    # Parcourir toutes les pages, de la page 1 à total_pages avec une barre de progression
    for current_page in tqdm(range(1, total_pages + 1), desc=f"Chargement des matchs de {sport}"):
        # Aller à la page avec le numéro de page
        page.goto(f"{url}?page={current_page}")

        # Attendre le chargement complet de la page
        page.wait_for_load_state('networkidle')

        # Extraire les informations des matchs sur la page actuelle
        matches = extract_matches(page, sport)
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


def save_match_info_to_file(matches, title, bookmaker_name):
    """
    Enregistre les informations des matchs dans un fichier texte dans le dossier 'results'.

    Args:
        matches (list): La liste contenant les informations des matchs.
        title (str): Le titre pour identifier les matchs (foot ou tennis).
        bookmaker_name (str): Le nom du bookmaker pour identifier la provenance des matchs.
    """
    # Créer le dossier 'results' s'il n'existe pas
    os.makedirs('results', exist_ok=True)

    # Définir le chemin du fichier
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    file_path = f"results/{title.lower()}_{bookmaker_name.lower()}_{date_str}.txt"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"--- {title.upper()} - {bookmaker_name.upper()} ---\n")
        for match in matches:
            f.write(f"Match: {match['team_1']} vs {match['team_2']}\n")
            f.write(f"Heure: {match['time']}\n")
            f.write(f"Retour: {match['return']}\n")
            f.write(f"Cote {match['team_1']}: {match['odds']['team_1']}\n")
            if match['odds']['draw']:
                f.write(f"Cote match nul: {match['odds']['draw']}\n")
            f.write(f"Cote {match['team_2']}: {match['odds']['team_2']}\n")
            f.write("-" * 30 + "\n")

    log_message(
        f"Les informations des matchs de {title} ({bookmaker_name}) ont été enregistrées dans '{file_path}'.")



def main():
    setup_logger()

    # Charger les variables d'environnement
    env_vars = load_env_variables()
    username = env_vars.get('USERNAME')
    password = env_vars.get('PASSWORD')

    if not username or not password:
        log_message("Identifiants non définis dans .env.")
        return

    # Créer une instance de Playwright
    browser, page = create_playwright_browser()

    try:
        # Étape 1 : Connexion au site
        log_message("Connexion au compte...")
        login_to_coteur(page, username, password)

        # Vérifier si la connexion a réussi
        if "login" in page.url:
            log_message("Erreur : Connexion échouée. Veuillez vérifier vos identifiants.")
            return
        log_message("Connexion réussie.")

        # Étape 2 : Demander le bookmaker à scrapper
        selected_bookmakers = ask_user_for_bookmaker()

        # Étape 3 : Gérer "Tous" les bookmakers
        if len(selected_bookmakers) > 1:  # Cas où "Tous" est sélectionné
            for bookmaker_id in selected_bookmakers:
                bookmaker_name = next(b['name'] for b in BOOKMAKERS if b['id'] == bookmaker_id)

                # Sélectionner uniquement le bookmaker actuel
                log_message(f"Sélection unique du bookmaker {bookmaker_name}.")
                select_bookmakers(page, [bookmaker_id])

                # Scrapper les matchs de football
                log_message(f"Scrapping des matchs de football pour {bookmaker_name}.")
                foot_matches = paginate_and_extract_matches(page, "https://www.coteur.com/cotes-foot", sport="football")
                sorted_foot_matches = sort_matches_by_return(foot_matches)
                save_match_info_to_file(sorted_foot_matches, "Foot", bookmaker_name)

                # Scrapper les matchs de tennis
                log_message(f"Scrapping des matchs de tennis pour {bookmaker_name}.")
                tennis_matches = paginate_and_extract_matches(page, "https://www.coteur.com/cotes-tennis", sport="tennis")
                sorted_tennis_matches = sort_matches_by_return(tennis_matches)
                save_match_info_to_file(sorted_tennis_matches, "Tennis", bookmaker_name)

                # Décocher le bookmaker actuel avant de passer au suivant
                log_message(f"Désélection du bookmaker {bookmaker_name}.")
                select_bookmakers(page, [])  # Désélectionner tous les bookmakers

        else:  # Cas où un seul bookmaker est sélectionné
            bookmaker_id = selected_bookmakers[0]
            bookmaker_name = next(b['name'] for b in BOOKMAKERS if b['id'] == bookmaker_id)

            # Sélectionner le bookmaker
            log_message(f"Sélection du bookmaker {bookmaker_name}.")
            select_bookmakers(page, [bookmaker_id])

            # Scrapper les matchs de football
            log_message(f"Scrapping des matchs de football pour {bookmaker_name}.")
            foot_matches = paginate_and_extract_matches(page, "https://www.coteur.com/cotes-foot", sport="football")
            sorted_foot_matches = sort_matches_by_return(foot_matches)
            save_match_info_to_file(sorted_foot_matches, "Foot", bookmaker_name)

            # Scrapper les matchs de tennis
            log_message(f"Scrapping des matchs de tennis pour {bookmaker_name}.")
            tennis_matches = paginate_and_extract_matches(page, "https://www.coteur.com/cotes-tennis", sport="tennis")
            sorted_tennis_matches = sort_matches_by_return(tennis_matches)
            save_match_info_to_file(sorted_tennis_matches, "Tennis", bookmaker_name)

    finally:
        browser.close()

    log_message("Fin de l'exécution du script.")


if __name__ == "__main__":
    main()
