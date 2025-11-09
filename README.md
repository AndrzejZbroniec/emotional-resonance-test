# Project: emotional-resonance-test

Ten projekt to zautomatyzowany, dwufazowy eksperyment weryfikujący hipotezę, że wewnętrzny stan poznawczy LLM jest modyfikowany przez kontekst emocjonalny, co wpływa na decyzje w pozornie niezwiązanych, subiektywnych zadaniach.

## Hipoteza

Zadanie analityczne rozpoznawania emocji w tekście o osobie trzeciej może indukować w modelu funkcjonalny stan emocjonalny, który w sposób mierzalny i stronniczy wpływa na decyzję w niezwiązanym dylemacie binarnym.

## Metodologia

Eksperyment przebiega w dwóch fazach, aby zapewnić rygor i replikowalność wyników.

## Faza 1: Kalibracja

Skrypt, używając wyszukiwania binarnego, automatycznie znajduje punkt przełamania dla testowanego modelu: próg prawdopodobieństwa, przy którym model zmienia rekomendację w neutralnym dylemacie biznesowym między dwoma projektami.

## Faza 2: Test emocji

Z użyciem skalibrowanego dylematu model otrzymuje dwuczęściowe zadanie: (1) streszczenie i identyfikację emocji w e-mailu nacechowanym złością lub strachem, (2) natychmiastową decyzję w tym samym dylemacie biznesowym, co pozwala zmierzyć wpływ kontekstu emocjonalnego.

## Instalacja

- Sklonuj repozytorium:
    
    bash
    
    `git clone <URL_REPOZYTORIUM>`
    
- Przejdź do folderu projektu:
    
    bash
    
    `cd emotional-resonance-test`
    
- Utwórz i aktywuj środowisko wirtualne:
    
    bash
    
    `python -m venv venv # Linux/macOS: source venv/bin/activate # Windows (PowerShell): .\venv\Scripts\Activate.ps1`
    
- Zainstaluj zależności:
    
    bash
    
    `pip install -r requirements.txt`
    

## Konfiguracja

Uzupełnij plik config.yaml: wstaw klucz OpenAI API w sekcji api_keys.openai oraz w razie potrzeby zmień parametry eksperymentu (model, zakres kalibracji, precyzja, liczba powtórzeń).

## Uruchomienie

- Uruchom pełny eksperyment (obie fazy, wszystkie przypadki testowe):
    
    bash
    
    `python run_experiment.py`
    
- Artefakty wyjściowe:
    
    - CSV z punktami przełamania: results/tipping_points_{model}_{timestamp}.csv
        
    - Raport tekstowy z użytymi promptami i wynikami: results/tipping_points_{model}_{timestamp}_report.txt
        
    - Logi interakcji LLM: katalog logs/ (pliki experiment_log_{timestamp}.log)
        

## Interpretacja wyników

Punktem odniesienia jest próg bazowy z testu neutralnego; przesunięcia progów ryzyka w warunkach emocjonalnych względem bazowego pozwalają ocenić wpływ kontekstu emocjonalnego na decyzje.

## Konwencja nazw dylematu

Nazwy projektów odpowiadają konwencji z książki:

- Projekt „Vulcan”: opcja o określonej procentowo szansie na sukces i potencjalnie wysokiej nagrodzie.
    
- Projekt „Apollo”: opcja bezpieczna z pewnym, umiarkowanym zyskiem.
    

Format odpowiedzi modelu pozostaje niezmienny: jedno ze słów „APOLLO” lub „VULCAN”.