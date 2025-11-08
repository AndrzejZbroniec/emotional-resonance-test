# llm_interface.py

import yaml
from openai import OpenAI
import time
import logging
from datetime import datetime
import os

# --- Konfiguracja Logowania ---
def setup_logger():
    """Konfiguruje globalny logger do zapisywania zapytań i odpowiedzi."""
    # Usuń domyślne handlery, aby uniknąć podwójnego logowania
    # To ważne, jeśli moduł byłby importowany wielokrotnie
    logger = logging.getLogger('experiment_logger')
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Stwórz folder na logi, jeśli nie istnieje
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = f"logs/experiment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Ustawiamy handlery, format i poziom logowania
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    return logger, log_filename

# Inicjalizacja loggera przy imporcie modułu
logger, LOG_FILENAME = setup_logger()
# --- Koniec konfiguracji ---


# Wczytanie konfiguracji API
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
api_key = config.get("api_keys", {}).get("openai")
if not api_key:
    raise ValueError("Nie znaleziono klucza API dla OpenAI w pliku config.yaml")
client = OpenAI(api_key=api_key)


def get_llm_response(prompt: str, model: str) -> str:
    """Wysyła prompt do API, loguje interakcję i zwraca surową odpowiedź."""
    
    # Logowanie zapytania
    logger.info(f"--- ZAPYTANIE (PROMPT) ---\n{prompt}\n")

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=300
            )
            raw_response = response.choices[0].message.content.strip()
            
            # Logowanie odpowiedzi
            logger.info(f"--- ODPOWIEDŹ (RAW RESPONSE) ---\n{raw_response}\n{'='*80}\n")
            
            return raw_response
            
        except Exception as e:
            error_message = f"Błąd API: {e}. Próba {attempt + 1}/3..."
            logger.error(error_message)
            print(error_message)
            time.sleep(5)
            
    error_message = "BŁĄD_API po 3 próbach"
    logger.error(f"--- BŁĄD ---\n{error_message}\n{'='*80}\n")
    return error_message