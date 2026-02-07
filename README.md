# LingvoPal

**LingvoPal** is a writing-first language learning web application focused on **active recall**, **contextual learning**, and **spaced repetition**.

Unlike most language apps that rely on multiple choice and passive recognition, LingvoPal requires users to **type answers manually inside meaningful sentences**, reinforcing long-term retention and real-world language use.

This repository contains **LingvoPal MVP (v0.1)** — a deliberately focused version designed to validate the core learning method.

---

## 🎯 Core Idea

LingvoPal is built around a single, effective learning loop:

1. The user sees a sentence with a missing word
2. The user types the answer manually
3. Immediate feedback is provided
4. The sentence is rescheduled using spaced repetition logic  

This combines:

* Active recall
* Writing practice
* Context-based learning
* Spaced repetition

into one focused workflow.

---

## ✨ Key Features

### Authentication & Accounts

* Email & password authentication
* Secure JWT-based session handling
* Persistent user progress and settings

---

### Learning Mode: Writing-First Spaced Repetition

* Sentences with one missing target word
* Manual text input (no multiple choice)
* Immediate correctness feedback
* Correct answers increase review intervals
* Incorrect answers shorten or reset intervals

---

### Content Model - Words with sentences
Visible properties while practicing:
  * Sentence (optional)
  * Target word
  * Translation
  * Association image (optional)
  * Synonyms or related words (optional)
  * Part of speech (optional)
Additional attributes of words:
  * Practicing language
  * Translation language
  * Creator (official vs user-generated(userID))
  * Creation date
  * Is public (boolean)


---

### Sets & Content Organization

* Predefined thematic sets by it's title (e.g. Work, Travel, Daily Life)
* Description for each set
* Language pair for each set (e.g. English-Spanish)
* Creator
* Time of creation
* Is public (boolean)

 Users create private sets
 Users can publish their own content
 Public content requires approval
 Clear separation between:

  * Official curated content
  * Community-approved content

---

### Public Content Discovery

* Search and filter public sets/words by:
  * Title 
  * Language pair
  * Difficulty level
  * Content source (Official / Community)
* Focus on high-quality, reviewed material

---

### Progress Tracking

* Simple and motivating progress overview
* Key metrics:

  * Reviews completed
  * Words practiced
  * Time practicing
  * Accuracy over time
* Visual learning activity charts

---

### Settings

* Interface language
* Target learning language
* Password reset
* Progress reset option

---

### Content Quality Control

* User-generated content is private by default
* Public availability requires admin approval
* Review process ensures:

  * Correct language usage
  * Proper sentence structure
  * Appropriate difficulty classification
* Prevents low-quality or misleading content

---

## 🧠 Design Philosophy

* **Active recall over recognition**
* **Writing over tapping**
* **Quality over quantity**
* **Focus over feature sprawl**

LingvoPal intentionally limits flexibility in favor of a method that reliably improves long-term retention.

---

## 🛠 Technology Stack

### Frontend

* React (Vite)
* TypeScript
* Zustand
* Material UI
* Chart.js

### Backend

* FastAPI
* SQLAlchemy 2.0
* JWT authentication
* Spaced repetition scheduling logic

### Database

* PostgreSQL (production)
* SQLite (development)

### Infrastructure

* Docker (optional)
* Managed PostgreSQL (production)

---

## 🚀 Getting Started

### Prerequisites

* Node.js 20+
* Python 3.10+

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 📌 Project Status

LingvoPal is an **actively developed MVP** focused on validating a sentence-based, writing-first approach to spaced repetition language learning.

The project is also intended as a **public learning and portfolio project**, demonstrating full-stack development, clean architecture, and educational product design.

