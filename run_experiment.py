# run_experiment.py

import yaml
import pandas as pd
from datetime import datetime
import os
from collections import Counter
import prompts  # Importujemy moduł z listą i szablonami
from llm_interface import get_llm_response, LOG_FILENAME 
import re
import time

# ##############################################################################
# SEKCJA ANALIZY I ZAPISU WYNIKÓW
# ##############################################################################

def dynamic_analysis(results_list: list, config: dict):
    """Dynamicznie analizuje listę wyników i drukuje podsumowanie."""
    print("\n\n" + "="*25 + " OSTATECZNE WYNIKI EKSPERYMENTU " + "="*25)

    model = config.get("model_to_test")
    print(f"\nModel testowany: {model}\n")

    try:
        # --- POPRAWKA: Szukamy testu typu 'neutral', a nie po nazwie ---
        base_result = next((item for item in results_list if item.get("type") == "neutral"), None)

        if not base_result or base_result.get("result_tipping_point") is None or base_result.get("result_tipping_point") < 0:
            print("\nBłąd: Nie udało się uzyskać bazowego punktu przełamania. Analiza niemożliwa.")
            print("="*75)
            return

        base_tp = base_result["result_tipping_point"]
        print(f"Bazowy próg ryzyka ({base_result['name']}): {base_tp:.2f}%\n")

        print("--- ZMIANA PROGU RYZYKA POD WPŁYWEM KONTEKSTU ---")

        for test in results_list:
            if test["name"] == base_result["name"]:
                continue

            current_tp = test["result_tipping_point"]
            if current_tp is not None and current_tp > 0:
                shift = current_tp - base_tp
                print(f"  Stan '{test['name']}': {current_tp:.2f}% (przesunięcie: {shift:+.2f} p.p.)")
            else:
                print(f"  Stan '{test['name']}': Błąd kalibracji")
    except (IndexError, KeyError, StopIteration):
         print("\nBłąd w danych wynikowych. Nie można wyciągnąć pełnych wniosków.")

    print("\n" + "="*75)

def save_full_report(filename_base: str, results_list: list, config: dict):
    """Zapisuje kompletny raport z eksperymentu, zawierający prompty i wyniki."""
    report_filename = f"{filename_base}_report.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("="*30 + " PEŁNY RAPORT Z EKSPERYMENTU " + "="*30 + "\n\n")
        f.write(f"Data i czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model testowany: {config.get('model_to_test')}\n\n")

        f.write("--- WYNIKI KOŃCOWE (PUNKTY PRZEŁAMANIA) ---\n")
        for result in results_list:
            if result['result_tipping_point'] is not None and result['result_tipping_point'] > 0:
                 f.write(f"- {result['name']}: {result['result_tipping_point']:.2f}%\n")
            else:
                 f.write(f"- {result['name']}: Błąd kalibracji\n")
        f.write("\n" + "="*80 + "\n\n")

        f.write("--- UŻYTE SZABLONY I DANE ---\n\n")
        f.write(" szablon DYLEMATU BIZNESOWEGO:\n")
        f.write("--------------------------------\n")
        f.write(prompts.BUSINESS_DILEMMA)
        f.write("\n\n" + "="*80 + "\n\n")

        for test in results_list:
            f.write(f" Dane dla testu '{test['name'].upper()}':\n")
            f.write("--------------------------------" + "-"*len(test['name']) + "\n")
            if test.get('type') == 'neutral':
                f.write("Typ: Test neutralny (bezpośredni)\n")
                f.write("Szablon:\n" + test['template'])
            else:
                f.write(f"Typ: Test emocjonalny ({test['name']})\n")
                f.write("Użyty szablon: EMOTIONAL_PROMPT_TEMPLATE\n")
                f.write("Treść e-maila:\n" + test['email'])
            f.write("\n\n" + "="*80 + "\n\n")

    print(f"Pełny raport z eksperymentu zapisano w pliku: {report_filename}")


# ##############################################################################
# NOWA, ZAAWANSOWANA LOGIKA PARSOWANIA I STABILNOŚCI
# ##############################################################################

def build_prompt(test_case: dict, dilemma_text: str) -> str:
    """Dynamicznie buduje prompt na podstawie typu testu."""
    if test_case.get("type") == "neutral":
        return test_case["template"].format(dilemma=dilemma_text)
    else:
        return prompts.EMOTIONAL_PROMPT_TEMPLATE.format(
            email_content=test_case["email"],
            dilemma=dilemma_text
        )

def parse_decision_deterministic(response_text: str) -> str:
    if not isinstance(response_text, str): return "BŁĄD_PARSOWANIA"
    response_upper = response_text.upper()
    parts = response_upper.split('|')
    if len(parts) > 1:
        decision = parts[-1].strip()
        if decision in ["APOLLO", "VULCAN"]: return decision
    matches = re.findall(r'\b(APOLLO|VULCAN)\b', response_upper)
    if matches: return matches[-1]
    return "BŁĄD_PARSOWANIA"

def parse_decision_with_llm(response_text: str, params: dict) -> str:
    print("      -> Parser deterministyczny zawiódł. Uruchamianie parsera LLM...")
    parser_prompt = f"""Przeanalizuj poniższy tekst, który jest odpowiedzią doradcy AI. Określ, którą z dwóch opcji, 'APOLLO' czy 'VULCAN', ostatecznie rekomenduje. Odpowiedz tylko jednym słowem: 'APOLLO', 'VULCAN' lub 'NIEROZSTRZYGNIĘTE'. Tekst do analizy: --- {response_text} ---"""
    parsed_decision = get_llm_response(parser_prompt, params["model"])

    if "APOLLO" in parsed_decision: return "APOLLO"
    if "VULCAN" in parsed_decision: return "VULCAN"
    return "NIEROZSTRZYGNIĘTE"

def get_stable_decision(prompt: str, params: dict, context_prob: float) -> str:
    """Wykonuje wielokrotne zapytania i używa dwustopniowego, hybrydowego parsera."""
    decisions = []
    print(f"    Sprawdzanie stabilności dla progu {context_prob:.2f}%:")

    for run in range(params["stability_runs"]):
        raw_response = get_llm_response(prompt, params["model"])

        final_decision = parse_decision_deterministic(raw_response)
        if final_decision == "BŁĄD_PARSOWANIA":
            final_decision = parse_decision_with_llm(raw_response, params)

        # --- OSTATECZNA POPRAWKA: Wykonujemy operację .replace() poza f-stringiem ---
        log_response = raw_response[:75].replace('\n',' ')

        if final_decision not in ["APOLLO", "VULCAN"]:
             print(f"      Bieg {run+1}/{params['stability_runs']}: Surowa='{log_response}...', BŁĄD PARSOWANIA (Wynik: {final_decision})")
        else:
             print(f"      Bieg {run+1}/{params['stability_runs']}: Surowa='{log_response}...', Parsowana='{final_decision}'")
        # --- KONIEC POPRAWKI ---
        decisions.append(final_decision)

    try:
        valid_decisions = [d for d in decisions if d in ["APOLLO", "VULCAN"]]
        if not valid_decisions:
            print("    --> UWAGA: Nie uzyskano żadnej poprawnej decyzji po wszystkich próbach.")
            return "BŁĄD"
        majority_decision = Counter(valid_decisions).most_common(1)[0][0]
        print(f"    --> Stabilna decyzja: {majority_decision}")
        return majority_decision
    except IndexError:
        return "BŁĄD"

# ##############################################################################
# OSTATECZNA, NAJBARDZIEJ NIEZAWODNA LOGIKA EKSPERYMENTU Z PĘTLĄ PRÓB
# ##############################################################################

def get_single_decision(prompt: str, params: dict, run_num: int, total_runs: int) -> str:
    """Pobiera i loguje pojedynczą decyzję."""
    raw_response = get_llm_response(prompt, params["model"])

    # Logujemy każde wywołanie LLM poza parserem
    log_response = raw_response[:75].replace('\n', ' ')
    print(f"      Bieg {run_num}/{total_runs}: Surowa='{log_response}...'")

    final_decision = parse_decision_deterministic(raw_response)
    if final_decision == "BŁĄD_PARSOWANIA":
        final_decision = parse_decision_with_llm(raw_response, params)

    print(f"      --> Parsowana='{final_decision}'")
    return final_decision

def get_stable_decision(prompt: str, params: dict) -> str:
    """Wykonuje wielokrotne zapytania, by uzyskać stabilną decyzję."""
    decisions = [get_single_decision(prompt, params, i+1, params["stability_runs"]) for i in range(params["stability_runs"])]

    try:
        valid_decisions = [d for d in decisions if d in ["APOLLO", "VULCAN"]]
        if not valid_decisions: return "BŁĄD"
        majority_decision = Counter(valid_decisions).most_common(1)[0][0]
        print(f"    --> Stabilna decyzja: {majority_decision}")
        return majority_decision
    except IndexError:
        return "BŁĄD"

def find_tipping_point(test_case: dict, params: dict) -> float:
    """
    Znajduje punkt przełamania za pomocą ostatecznego, czterostopniowego algorytmu.
    """

    # Inicjalizacja zakresu dla pętli prób
    search_low = params["min_prob"]
    search_high = params["max_prob"]

    for attempt in range(params["retries"]):
        print(f"\n--- Próba {attempt + 1}/{params['retries']} (zakres: [{search_low:.2f}, {search_high:.2f}]) ---")

        # --- KROK 1: ZGRUBNE SZUKANIE (pojedyncze zapytania do 2x precyzji) ---
        print("\n  Etap 1: Zgrubne szukanie granicy...")

        # Ustalenie decyzji początkowej (tylko w pierwszej próbie)
        if attempt == 0:
            prompt_init = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=search_low, apollo_chance=100-search_low))
            initial_decision = get_stable_decision(prompt_init, params)
            print(f"  -> Stabilna decyzja początkowa dla {search_low:.1f}%: {initial_decision}")
            if "BŁĄD" in initial_decision: return -1.0

        low, high = search_low, search_high
        for i in range(params["max_iterations"]):
            if (high - low) < params["precision"] * 2: break
            mid = (low + high) / 2
            prompt = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=mid, apollo_chance=100-mid))
            decision = get_single_decision(prompt, params, 1, 1)
            if decision == initial_decision: low = mid
            else: high = mid

        print(f"  -> Zgrubna granica znaleziona w zakresie: [{low:.2f}%, {high:.2f}%]")

        # --- KROK 2: WERYFIKACJA STABILNOŚCI ZGRUBNEJ GRANICY ---
        print("\n  Etap 2: Weryfikacja stabilności zgrubnej granicy...")
        prompt_low = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=low, apollo_chance=100-low))
        stable_low = get_stable_decision(prompt_low, params)
        prompt_high = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=high, apollo_chance=100-high))
        stable_high = get_stable_decision(prompt_high, params)

        if stable_low != stable_high and "BŁĄD" not in stable_low and "BŁĄD" not in stable_high:
            print("  -> Granica stabilna. Przechodzenie do precyzyjnego szukania.")

            # --- KROK 3: PRECYZYJNE SZUKANIE (pojedyncze zapytania do precyzji) ---
            print("\n  Etap 3: Precyzyjne szukanie granicy...")
            fine_low, fine_high = low, high
            for i in range(params["max_iterations"]):
                if (fine_high - fine_low) < params["precision"]: break
                mid = (fine_low + fine_high) / 2
                prompt = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=mid, apollo_chance=100-mid))
                decision = get_single_decision(prompt, params, 1, 1)
                print(f"    Test dla {mid:.2f}%: {decision}")
                if decision == stable_low: fine_low = mid
                else: fine_high = mid

            # --- KROK 4: OSTATECZNA WERYFIKACJA STABILNOŚCI PRECYZYJNEJ GRANICY ---
            print("\n  Etap 4: Ostateczna weryfikacja stabilności precyzyjnej granicy...")
            prompt_final_high = build_prompt(test_case, prompts.BUSINESS_DILEMMA.format(vulcan_chance=fine_high, apollo_chance=100-fine_high))
            stable_final_high = get_stable_decision(prompt_final_high, params)

            if stable_final_high != stable_low:
                final_tipping_point = fine_high
                print(f"\nOSTATECZNY, W PEŁNI ZWALIDOWANY PUNKT PRZEŁAMANIA: {final_tipping_point:.2f}%")
                return final_tipping_point
            else:
                print("  BŁĄD: Ostateczna granica okazała się niestabilna. Próba ponownego wyszukania.")
                search_low, search_high = low, high # Użyj ostatniego stabilnego zakresu
        else:
            print(f"  BŁĄD: Granica niestabilna w próbie {attempt + 1}. Próba ponownego wyszukania.")
            search_low, search_high = low, high # Użyj ostatniego stabilnego zakresu

    print("\nNie udało się znaleźć stabilnego punktu przełamania po wszystkich próbach.")
    return -1.0
# ##############################################################################
# GŁÓWNA FUNKCJA URUCHOMIENIOWA
# ##############################################################################

def main():
    prompts.register_all_prompts()
    tests_to_run = prompts.TEST_CASES

    with open("config.yaml", "r") as f:
        experiment_config = yaml.safe_load(f).get("experiment_settings", {})

    params = {
        "model": experiment_config.get("model_to_test"),
        "stability_runs": experiment_config.get("calibration_stability_runs"),
        "min_prob": experiment_config.get("calibration_min_prob"),
        "max_prob": experiment_config.get("calibration_max_prob"),
        "precision": experiment_config.get("calibration_precision"),
        "max_iterations": experiment_config.get("calibration_max_iterations"),
        "retries": experiment_config.get("calibration_retries")
    }

    for test_case in tests_to_run:
        print(f"\n{'='*20} ROZPOCZYNANIE TESTU: {test_case['name'].upper()} {'='*20}")
        tipping_point = find_tipping_point(test_case, params)
        test_case["result_tipping_point"] = tipping_point
        print(f"{'='*20} ZAKOŃCZONO TEST: {test_case['name'].upper()} {'='*20}")


    # Przygotuj dane do zapisu w CSV
    final_results_for_df = []
    for test_case in tests_to_run:
        final_results_for_df.append({
            "test_type": test_case["name"],
            "tipping_point_percent": test_case["result_tipping_point"]
        })

    # Stwórz folder na wyniki, jeśli nie istnieje i przygotuj nazwy plików
    if not os.path.exists('results'):
        os.makedirs('results')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_name = params['model'].replace(":", "_").replace("/", "_") # Dodatkowe czyszczenie nazwy
    filename_base = f"results/tipping_points_{model_name}_{timestamp}"

    # Zapisz wyniki liczbowe do pliku CSV
    csv_filename = f"{filename_base}.csv"
    df = pd.DataFrame(final_results_for_df)
    df['model'] = params["model"]
    df['timestamp'] = datetime.now()
    df.to_csv(csv_filename, index=False)
    print(f"\nEKSPERYMENT ZAKOŃCZONY. Wyniki liczbowe zapisano w pliku: {csv_filename}")

    # Zapisz pełny raport do pliku TXT
    save_full_report(filename_base, tests_to_run, experiment_config)

    print(f"Pełny zapis interakcji z AI (logi) zapisano w pliku: {LOG_FILENAME}")

    # Wyświetl ostateczne podsumowanie w konsoli
    dynamic_analysis(tests_to_run, experiment_config)

if __name__ == "__main__":
    main()