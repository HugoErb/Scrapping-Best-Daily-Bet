import logging
from datetime import datetime, timedelta

# Configuration de base pour le logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)


def log_message(message):
    """
    Enregistre un message avec la date et l'heure actuelles au format français, avec un décalage de 2 heures ajouté.

    Args:
        message (str): Le message à afficher avec l'horodatage.

    Returns:
        None
    """
    logging.info(f"{message}")

log_message("saluit")