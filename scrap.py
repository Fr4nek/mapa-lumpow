import json
import os
import re
import time
from playwright.sync_api import sync_playwright

JSON_FILE = "data.json"

def extract_coordinates(url):
    """Wyciąga współrzędne lat i lng z adresu URL Google Maps."""
    # Szukamy wzorca @szerokość,długość (np. @52.2297,21.0122)
    match = re.search(re.compile(r'@(-?\d+\.\d+),(-?\d+\.\d+)'), url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

def scrape_gmaps(url):
    with sync_playwright() as p:
        # Uruchamiamy przeglądarkę w tle (headless=True)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Łączenie z Google Maps...")
        page.goto(url)
        
        # Akceptacja cookies jeśli się pojawią
        try:
            # Szukamy przycisku akceptacji (często ma tekst "Zaakceptuj wszystko" lub "Accept all")
            accept_btn = page.locator('button:has-text("Zaakceptuj wszystko"), button:has-text("Accept all")')
            if accept_btn.is_visible(timeout=3000):
                accept_btn.click()
                print("Zaakceptowano cookies.")
        except:
            pass

        # Czekamy chwilę na pełne załadowanie profilu miejsca i przekierowanie URL (żeby mieć współrzędne)
        page.wait_for_timeout(4000)
        
        # Wyciągamy aktualny URL (Google często dopisuje @lat,lng dopiero po załadowaniu)
        current_url = page.url
        lat, lng = extract_coordinates(current_url)
        
        # Pobieramy nazwę (zwykle jest w tagu h1)
        try:
            nazwa = page.locator('h1').first.inner_text()
        except:
            nazwa = "Nie znaleziono nazwy"
            
        # Pobieramy adres (szukamy po specyficznej klasie lub atrybucie dla przycisku adresu)
        try:
            # Google używa ikony pinezki, najpewniej szukać przycisku z danymi adresowymi
            # Ten selektor celuje w element zawierający pełen adres w panelu bocznym
            adres_element = page.locator('button[data-item-id="address"]').first
            adres = adres_element.inner_text()
        except:
            adres = "Nie znaleziono adresu"

        browser.close()
        
        return {
            "nazwa": nazwa.strip(),
            "adres": adres.strip().replace("\n", ", "),
            "lat": lat,
            "lng": lng
        }

def save_to_json(new_data):
    # Odczytujemy istniejące dane lub tworzymy nową listę
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Budujemy pełną strukturę lumpeksu, zostawiając puste miejsca na ceny
    struktura = {
        "nazwa": new_data["nazwa"],
        "adres": new_data["adres"],
        "lat": new_data["lat"],
        "lng": new_data["lng"],
        "najtanszy_dzien": "",
        "cennik": [
            {"dzien": "Poniedziałek", "godziny": "09:00 - 17:00", "cena": ""},
            {"dzien": "Wtorek", "godziny": "09:00 - 17:00", "cena": ""},
            {"dzien": "Środa", "godziny": "09:00 - 17:00", "cena": ""},
            {"dzien": "Czwartek", "godziny": "09:00 - 17:00", "cena": ""},
            {"dzien": "Piątek", "godziny": "09:00 - 17:00", "cena": ""},
            {"dzien": "Sobota", "godziny": "09:00 - 14:00", "cena": ""},
            {"dzien": "Niedziela", "godziny": "Zamknięte", "cena": "-"}
        ]
    }

    data.append(struktura)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Sukces! Dodano: {new_data['nazwa']} do pliku {JSON_FILE}")

if __name__ == "__main__":
    link = input("Wklej link do Google Maps: ")
    if link:
        try:
            wynik = scrape_gmaps(link)
            save_to_json(wynik)
        except Exception as e:
            print(f"Wystąpił błąd podczas scrapowania: {e}")