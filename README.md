# LingvoPal
# Projekt Platformy do wspomagania nauki językowej LingvoPal
### _**Strona internetowa:**_

_**Logowanie&Rejestracja:**_ hasło login, przez google, możliwość rejestracji, reset hasła, potwierdzenie adresu przez skrzynkę.

_**Main Page:**_ opis projektu, dlaczego warto, funkcjonalności i tak dalej, przejścia do chatu z AI asystentem, gry w flash cards, ustawienia, support, podstrony rozszerzenia do przeglądarki z opisem.

_**Settings**_: Wybór języka, poziomu biegłości, opcja „zanurzenia językowego” wszystko jest w języku obcym, powiadomienia dla przypomnienia o nauce.

_**Flash card game:**_ wykorzystanie zdań i obrazów dla lepszego zapamiętywania. Użytkownik musi pisać słowa w określonym miejscu w zdaniu. System powtórek opartych na krzywej zapomnienia (spaced repetition). Można też całe wyrażenie idiomatyczne. (Też tryb dopasowywania definicji słów, układanie zdań dla praktyki gramatycznej). Dostępne wyszukiwanie zbiorów słów, tworzenie własnych, dodanie słów, Eksport/import gotowych z anki i td.

_**Chat with AI assistant:**_ Użytkownicy mogą zadawać pytania, ćwiczyć mowę za pomocą interaktywnych dialogów z botem, który symuluje rozmowy w języku obcym, daje wskazówki i ocenia poprawność daje sugestie stylistyczne. Trenowanie pisania krótkich odpowiedzi i ich sprawdzenie z botem (opisz obrazek, pisanie maili (formalnych/nieformalnych), listów motywacyjnych, opowiadań, essajów). Czytanie gotowych lub wygenerowanych treści i odpowiedzi na pytania dotyczące ich od bota. 

Asystent automatycznie dostosowuje poziom trudności w zależności od postępów użytkownika. Z czasem, kiedy użytkownik poprawia swoje umiejętności, bot zacznie dostarczać trudniejsze treści i bardziej zaawansowane ćwiczenia.

Indywidualne ścieżki nauki – użytkownik może wybrać, czy chce się skupić na słownictwie, gramatyce, wymowie itp.

Personalizacja celów nauki - uczenie się do pracy, podróży, nauki, czy jakiś inny powód. Przybliżone wyznaczenie poziomu użytkownika poprzez testy i progres uczenia się na platformie.

Tryb nauki kontekstowej - użytkownik czyta artykuły w języku obcym (analiza za pomocą rozszerzenia) i AI generuje ćwiczenia bazujące na tym tekście.

_**Progress page:**_ Zaawansowane statystyki – wykresy postępów, najczęściej popełniane błędy, czas nauki, ilość nauczonych słówek.

### _**Rozszerzenie do przeglądarki:**_

Dodanie wydzielonych słów do słownika. Najeżdżanie kursorem na słowo lub wybranie zdania i przetłumaczenie nad nim. Użytkownik może kliknąć wyjaśnij przy najeżdżaniu, by zobaczyć pełne tłumaczenie, wymowę i przykłady użycia w kontekście. 
_**Read text review**_: Bot na stronie głównej dostarcza ćwiczenia związane z tekstami, które użytkownik właśnie przeglądał, i rozszerzenie przeskanowało i dodawało do kontekstu konserwacji z asystentem. Na przykład, po przeczytaniu artykułu, bot może zaproponować test na stronie platformy, w którym użytkownik będzie musiał wypełnić luki w zdaniach, wybierając odpowiednie słowa z kontekstu. 

_**Opcjonalnie:**
- Powiadomienie o nauce przez mail lub wbudowane w przeglądarkę. 
- System wyzwań i nagród, dzięki któremu użytkownicy mogą ustawić cele codziennej nauki i otrzymywać punkty lub medale za ich realizację.
- Ćwiczenia z rozumienia ze słuchu audio z botem i pytaniami sprawdzającymi zrozumienie - Rozmowa głosowa z botem.
- Spersonalizowane rekomendacje nauki: AI analizuje postępy użytkownika i sugeruje, na czym warto się skupić.
- Analiza wymowy użytkowników poprzez API innych AI
- Sekcja zbiorów reguł gramatycznych

[[Plan wykonania zgodnie z MVP w Agile]]
[[Data Base Schema]]
## Technologie do wykorzystania:

### **1. Frontend (strona internetowa i rozszerzenie przeglądarki)**

- **React.js** – elastyczny i szybki framework do budowy interaktywnych UI
- **+~Vite** – zamiast Create React App dla lepszego performance'u
- **~Next.js** - framework React z SSR, ułatwiający routing i zarządzanie stanem
- **TypeScript** - typy statyczne dla JavaScript, pomagają uniknąć błędów podczas rozwoju
- **Tailwind CSS** / **Material UI** – do stylizacji
- **~Redux Toolkit** lub **Zustand** – do zarządzania stanem (np. ustawienia użytkownika)
- **Manifest V3 + Chrome API** – do stworzenia rozszerzenia przeglądarki
### **2. Backend**

- **FastAPI** (Python) – szybkie i nowoczesne API do obsługi logiki aplikacji
- **PostgreSQL/SQL Lite**– relacyjna baza danych do przechowywania użytkowników, postępów itp.
- **~Redis** – do cache’owania powtarzających się zapytań (np. tłumaczenia)
- **Firebase Authentication** – do logowania przez Google
- **~Celery + RabbitMQ** – do obsługi zadań asynchronicznych, np. generowanie treści przez 
-  **Hosting**: Vercel (frontend), Railway / Render (backend + DB)
### **3. AI Assistant (chat, generowanie ćwiczeń)**

- **OpenAI GPT-4-turbo / Llama 3** – do generowania dialogów i ćwiczeń językowych
- **Whisper** – do rozpoznawania mowy (jeśli chcecie analizować wymowę użytkownika)
- **spaCy / NLTK** – do przetwarzania tekstu i analizy gramatycznej

**Tłumaczenia:**

- **DeepL API** (lepsza jakość niż Google Translate)

### **4. Flashcard Game & Progress Page**

- **IndexedDB (Dexie.js)** – do przechowywania danych offline
- **Recharts** – do wizualizacji postępów użytkownika
- **SuperMemo SM-2** – do zaimplementowania algorytmu powtórek.

### **5. Testowanie i Development**

- **Vitest + React Testing Library** – testy jednostkowe
- **Cypress** – testy end-to-end
- **Pytest** – testy logiki back-endu

Wersja Groka

### Back-end (Python)

1. **Framework:**
    
    **FastAPI**:
    
    - **FastAPI**: Nowoczesny, szybki framework z automatyczną dokumentacją Swagger. Jeśli planujesz intensywnie korzystać z API (np. OpenAI), FastAPI może być lepszym wyborem dzięki obsłudze asynchroniczności.
2. **Baza danych:**

    - **SQLite**: Ponieważ aplikacja działa lokalnie, SQLite jest idealnym wyborem – lekka, nie wymaga osobnego serwera, a Python ma wbudowane wsparcie (sqlite3).
3. **Autoryzacja i logowanie:**
    
    - **Flask-Login** (dla Flask) lub **Passlib**: Do zarządzania sesjami i haszami haseł.
    - **OAuth2** (np. Google Login): Biblioteka Authlib lub python-social-auth do integracji z Google.
    - Potwierdzenie e-mail: Lokalnie możesz symulować wysyłkę e-maili zapisując je do pliku lub korzystając z biblioteki smtplib (testowo).
4. **API OpenAI:**
    
    - Biblioteka openai: Oficialny klient Pythona do integracji z API OpenAI. Umożliwi komunikację z AI w chacie, generowanie ćwiczeń i ocenę odpowiedzi użytkownika.
    - **Prompt Engineering**: Zaprojektuj precyzyjne prompty, aby AI dostosowywało poziom trudności i generowało odpowiednie treści (np. dialogi, ćwiczenia kontekstowe).
5. **System powtórek (Spaced Repetition):**
    
    - Zaimplementuj algorytm oparty na krzywej zapomnienia (np. SuperMemo SM-2). Możesz użyć prostych struktur danych w Pythonie (listy, słowniki) lub biblioteki pandas do analizy i planowania powtórek.
6. **Przetwarzanie danych:**
    
    - **Pandas**: Do analizy statystyk użytkownika (postępy, błędy).
    - **Matplotlib** lub **Plotly**: Do generowania wykresów na stronie postępów.

---

### Front-end

Skoro aplikacja działa lokalnie, front-end powinien być lekki i zintegrowany z back-endem.

1. **HTML/CSS/JavaScript:**
    - **Jinja2** (z Flask): Do renderowania dynamicznych stron (np. main page, settings, progress).
    - **Bootstrap** lub **Tailwind CSS**: Proste i responsywne stylowanie interfejsu.
2. **Gry Flash Cards:**
    - **Vanilla JavaScript** lub **React**: Do interaktywnych elementów, takich jak układanie zdań czy dopasowywanie definicji.
    - **Canvas API** lub **SVG**: Do prostych animacji lub wyświetlania obrazów w grach.
3. **Chat z AI:**
    - WebSocket (np. Flask-SocketIO) lub AJAX: Do dynamicznej komunikacji z AI w czasie rzeczywistym.
4. **Samouczek:**
    - Prosty modal w JavaScript lub biblioteka jak **Intro.js**.

---

### Rozszerzenie do przeglądarki

1. **Technologie:**
    - **WebExtensions API**: Do tworzenia rozszerzenia kompatybilnego z Chrome/Firefox.
    - **JavaScript**: Do wykrywania słów, wyświetlania tooltipów i komunikacji z back-endem.
    - **Manifest V3**: Standard dla nowoczesnych rozszerzeń.
2. **Integracja z back-endem:**
    - Lokalny serwer (np. Flask) będzie działał jako API dla rozszerzenia. Użyj fetch w JavaScript, aby wysyłać dane (np. dodane słowa) do bazy SQLite.
3. **Funkcjonalności:**
    - **Tłumaczenie i wymowa**: Możesz zintegrować dodatkowe API (np. Google Translate lub Forvo) lub lokalnie przechowywać dane słownikowe.
    - **Ćwiczenia kontekstowe**: Back-end z API OpenAI może generować zadania na podstawie przesłanego tekstu.

---

### Dodatkowe narzędzia i technologie

1. **Lokalne przechowywanie danych:**
    - **JSON** lub **CSV**: Do eksportu/importu zestawów słów (kompatybilność z Anki).
2. **Testowanie:**
    - **Pytest**: Do testowania logiki back-endu (np. algorytmu powtórek, integracji z OpenAI).
3. **Zarządzanie projektem:**
    - **Virtualenv**: Do izolacji zależności Pythona.
    - **Git**: Do kontroli wersji.

---

### Architektura (propozycja)

- **Back-end**: Flask/FastAPI + SQLite + OpenAI API.
- **Front-end**: HTML/CSS/JS z Jinja2, obsługiwane lokalnie przez serwer Flask.
- **Rozszerzenie**: JavaScript + WebExtensions API, komunikujące się z lokalnym API.
- **Dane**: SQLite (użytkownicy, słownictwo, postępy) + JSON (eksport/import).
