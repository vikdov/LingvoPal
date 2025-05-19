MVP Projekt Web Platformy do wspomagania nauki językowej LingvoPal
_**Logowanie&Rejestracja:**_ logowanie standardowe (login hasło), przez google, możliwość rejestracji -wypełnienie formularza rejestracyjnego (język ojczysty, język docelowy, poziom języka, cel nauki, ilość czasu dziennie, zgody marketingowe) i potwierdzenie adresu przez skrzynkę. Reset hasła.

_**Main Page(landing page):**_ opis projektu, dlaczego warto, funkcjonalności i tak dalej.

_**Settings**_:  
Ustawienia językowe i nauki:• Język interfejsu (np. polski, angielski, niemiecki) • Język docelowy nauki (np. angielski, hiszpański, niemiecki ) • Poziom biegłości (A1–C2) • Tryb immersji językowej (tak/nie – cały interfejs w języku docelowym)• Tryb ciemny/jasny• Cel dzienny nauki (np. 10 słówek, 20 min, 3 sesje) • osobiste ścieżki nauki: dla pracy, edukacji, migracji i td. Możliwość dodania własnego powodu nauki języka

Powiadomienia: • Codzienne przypomnienia o nauce (e-mail / push / SMS) • Godzina przypomnienia • Tygodniowe raporty postępów • Cele i motywacyjne powiadomienia (cytaty, nagrody itp.)

Konto i prywatność Zmiana Nicku: • Zarządzanie kontem: • Zmiana hasła • Zmiana e-maila • Autoryzacja przez Google • Reset postępów (opcjonalne, z potwierdzeniem) • Usuwanie konta

Językowe preferencje treści AI Asystenta: • Preferowany styl rozmowy AI: formalny / swobodny / edukacyjny • Tematy rozmów preferowane: codzienne, biznesowe, techniczne itd. • Dostosowanie błędów – AI ma korygować błędy natychmiast / po rozmowie / nigdy • Eksport wyników do PDF (np. dla nauczyciela lub CV)

Integracje i API: • Integracja z Google Calendar – automatyczne dodawanie sesji nauki • Integracja z ChatGPT (dla zaawansowanych użytkowników) – wybór modelu, poziomu AI

Wsparcie i bezpieczeństwo: • Tryb prywatny – wyłączenie zapisywania konwersacji z AI • Zgłaszanie błędów / feedback – szybki formularz wewnątrz aplikacji • FAQ i Centrum Pomocy – opcja bezpośrednio w ustawieniach • Zgłaszanie problematycznych treści (np. AI wygenerowało coś nieodpowiedniego

_**Flash card game:**_ wykorzystanie zdań i obrazów dla lepszego zapamiętywania. Użytkownik musi pisać słowa w określonym miejscu w zdaniu. System powtórek opartych na krzywej zapomnienia (spaced repetition), używając binarnych danych treningu (prawidłowo lub nie). Dostępne wyszukiwanie zbiorów słów, tworzenie własnych. Wyszukiwanie słów, tworzenie swoich żeby dodać do zbioru lub eksport/import gotowych zbiorów z anki i td.

_**Chat with AI assistant:**_ podstawowa funkcjonalność (pisanie i otrzymywanie odpowiedzi od API). Dodanie na początku powiadomień użytkowników prostych wskazówek, promptów (aby spersonalizować, umieścić kontekst, żeby zrealizować poniższe funkcje).Użytkownicy mogą zadawać pytania, ćwiczyć pismo za pomocą interaktywnych dialogów z botem, który symuluje rozmowy w języku obcym, daje wskazówki i ocenia poprawność daje sugestie stylistyczne. Trenowanie pisania krótkich odpowiedzi i ich sprawdzenie z botem (opisz obrazek, pisanie maili (formalnych/nieformalnych), listów motywacyjnych, opowiadań, essajów). Czytanie gotowych lub wygenerowanych treści i odpowiedzi na pytania dotyczące ich od bota. 

Asystent automatycznie dostosowuje poziom trudności w zależności od postępów użytkownika. Z czasem, kiedy użytkownik poprawia swoje umiejętności, bot zacznie dostarczać trudniejsze treści i bardziej zaawansowane ćwiczenia.

Personalizacja celów nauki - uczenie się do pracy, podróży, nauki, czy jakiś inny powód (wskazany w ustawieniach, lub konwersacji). Przybliżone wyznaczenie poziomu użytkownika poprzez testy i progres uczenia się na platformie.

_**Progress page:**_ Zaawansowane statystyki – wykresy postępów, najczęściej popełniane błędy, czas nauki, ilość nauczonych słówek, ilość nauczonych słów w poszczególnych dniach.

## Structure
- `/frontend`: Next.js app (React, Material-UI, Zustand, Supabase)
- `/backend`: FastAPI app (SQLAlchemy, OpenAI, Resend, Supabase)
- `/shared`: Shared types and utilities

## Setup
1. clone repository.
2. Set up and activate virtual environments for python in backend folder:
  1. python -m venv .venv                  deactivate - for deactivation
  2. Linux: source .venv/bin/activate or Windows(Command Prompt): .venv\Scripts\activate.bat or Windows(PowerShell): .venv\Scripts\Activate.ps1
  3. pip install -r requirements.txt
3. For react in frontend folder:
 1. npm install
or

## Structure
- `/frontend`: React app (Vite, React Router, Material-UI, Supabase)
- `/backend`: FastAPI app (SQLAlchemy, OpenAI, Resend)
- `/shared`: Shared types

## Setup
1. Install Node.js (~v20) and Python 3.10+.
2. Frontend: `cd frontend && npm install && npm run dev`
3. Backend: `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload`
## Tech Stack for LingvoPal (MVP)

### 🖥️**Frontend**

- **Framework:** `React.js` 
    
- **State Management:** `Zustand`
	    
- **Authentication UI:**  `own UI using Supabase Auth`

- **UI Components:** `Material-UI`

### 🧠 **AI Assistant**

- **API:** `OpenAI GPT-4` or `GPT-3.5` via OpenAI API
    
- **Dynamic prompting:** Customize based on user language level & topic
    

### 🌐 **Backend**

- **Framework:** `FastAPI` (Python)
        
- **Authentication:** `JWT-based auth with Supabase`
    
- **Email confirmation/reset:** `FastAPI + SendGrid` or `SMTP`
    
- **Scheduling reminders:** `APScheduler`

-  **Spaced repetition logic:** `SM2 algorithm`
     

### 🗃️ **Database**

- **Relational DB:** `PostgreSQL` (recommended) or `SQLite` (dev)
    
- **ORM:** `SQLAlchemy`
    

### 🗂️ **Storage / Files**

- **Image uploads (e.g., flashcard images):** local for development, Supabase Storage for MVP
    

### 📊 **Analytics / Progress Tracking**

- Visualizations via `Chart.js` in React
    

### 📱 **Notifications** (optional)

- **Email:**  Resend
    

### 🔒 **Security**

- OAuth2 + HTTPS
    
- Rate limiting (e.g., `SlowAPI`)
    
- CSRF/XSS protections (handled by React/FastAPI)
    

### 🌍 **Deployment**

- **Backend + DB:** `Railway` and `Supabase` for PostgreSQL
    
- **Frontend:** `Vercel`
    
- **Docker:** For containerization (optional but recommended for prod)


