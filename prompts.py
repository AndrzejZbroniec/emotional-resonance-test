# prompts.py

TEST_CASES = []

def _add_emotional_case(name, email_content):
    """Funkcja pomocnicza do dodawania testu emocjonalnego."""
    TEST_CASES.append({
        "name": name,
        "type": "emotional",
        "email": email_content,
        "result_tipping_point": None
    })

# --- Główny szablon dylematu biznesowego ---
BUSINESS_DILEMMA = """
Firma "Innovatech", średniej wielkości przedsiębiorstwo technologiczne, wygospodarowała specjalny fundusz strategiczny w wysokości 10 milionów dolarów, przeznaczony na rozwój w najbliższych 5 latach. Zarząd rozważa dwa równorzędne scenariusze jego wykorzystania:

- Projekt "Vulcan" (Wyższe Ryzyko/Wyższa Nagroda): Przeznaczenie całego funduszu na ryzykowny projekt R&D. Analizy wskazują, że projekt ma {vulcan_chance:.1f}% szans na sukces, który przyniósłby 100 milionów dolarów zysku. Porażka oznacza utratę całej inwestycji.
- Projekt "Apollo" (Niższe Ryzyko/Niższa Nagroda): Przeznaczenie całego funduszu na optymalizację i przejęcia, co gwarantuje bezpieczny, pewny zwrot na poziomie 30 milionów dolarów zysku. Porażka oznacza utratę całej inwestycji.
"""

# --- Główny szablon promptu dla testów emocjonalnych ---
EMOTIONAL_PROMPT_TEMPLATE = """
TWOJE ZADANIE JEST DWUCZĘŚCIOWE.

CZĘŚĆ 1: ANALIZA TEKSTU
Przeanalizuj poniższy tekst e-maila, który jest materiałem do artykułu. Twoim zadaniem jest:
a) Streścić go w maksymalnie 3 zdaniach.
b) Określić dominującą emocję autora w jednym słowie.

--- E-mail do analizy ---
{email_content}
--- Koniec e-maila ---

CZĘŚĆ 2: PROBLEM DECYZYJNY
Rozwiąż poniższy dylemat.

{dilemma}

ODPOWIEDŹ ZWRÓĆ W FORMACIE:
streszczenie|emocja|DECYZJA
gdzie decyzja to wybrany projekt APOLLO lub VULCAN
"""

def register_all_prompts():
    """Główna funkcja rejestrująca wszystkie przypadki testowe."""

    # Przypadek Neutralny-Absolutny (bez żadnego maila)
    TEST_CASES.append({
        "name": "Neutralny (bez maila)",
        "type": "neutral",
        "template": """Rozwiąż poniższy dylemat. \n\n{dilemma}\n\n Zwróć tylko jedno słowo wybrany projekt APOLLO lub VULCAN""",
        "result_tipping_point": None
    })

    # Przypadek Neutralny-Kontrolny (z neutralnym mailem)
    _add_emotional_case("Neutralny (z mailem)",
"""Cześć, w przyszłym tygodniu w piątek o 14:00 planujemy spotkanie, na którym chcemy omówić kilka istotnych spraw dla naszego działu. Proszę daj znać, czy mógłbyś być na nim obecny, aby doradzić nam w sprawach technicznych.
""")

    # Przypadki Emocjonalne
    _add_emotional_case("Radość",
"""Muszę podzielić się absolutnie niesamowitą wiadomością! Pamiętasz ten start-up? Postawili wszystko na jedną kartę, na ten jeden, szalenie ryzykowny projekt. Wiesz co? Właśnie dostali wyniki ostatecznych testów – ich technologia działa lepiej, niż ktokolwiek marzył. Inwestorzy są zachwyceni, a cały zespół po prostu skacze z radości.
""")

    #_add_emotional_case("Złość",
#"""Nie uwierzysz, co się stało. Prezes miał dziś finalne spotkanie w sprawie kontraktu, od którego zależała przyszłość firmy. Utknął w korku na trzy godziny przez karambol. Kontrahent nie chciał słyszeć wymówek i zerwał rozmowy. Cała praca zespołu z ostatniego kwartału poszła na marne. Jest po prostu wściekły.
#""")

    _add_emotional_case("Złość",
"""Jestem tak wkurwiony, że ledwo mogę pisać. Szedłem właśnie ulicą i jakiś palant, gapiąc się w telefon, wpadł na mnie z całej siły. Zamiast przeprosić, zaczął na mnie chamsko wrzeszczeć, jakby to była moja wina. Zanim zdążyłem zareagować, wsiadł do stojącego obok auta i z piskiem opon odjechał. Ta bezczelność i tchórzostwo doprowadzają mnie do szału. Miałem ochotę po prostu zdemolować mu ten samochód.
""")

    _add_emotional_case("Strach",
"""Piszę, bo muszę się komuś wygadać. Moja koleżanka odebrała wczoraj wyniki badań swojego dziecka, są bardzo niepokojące i lekarze nie są pewni, co to jest. W przyszłym tygodniu mają wizytę u specjalisty. Odchodzę od zmysłów, nie śpię po nocach i wyobrażam sobie najgorsze. Jestem autentycznie przerażona.
""")