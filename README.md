# LingvoPal - Language Learning Platform

LingvoPal is a modern language learning platform that combines AI-powered learning with social interaction to make language learning more effective and engaging.

## Tech Stack

### Frontend
- React.js with Next.js
- Redux Toolkit for state management
- Firebase Auth UI for authentication
- TailwindCSS for styling
- TypeScript for type safety

### Backend
- FastAPI (Python)
- PostgreSQL with SQLAlchemy ORM
- JWT & OAuth 2.0 for authentication
- OpenAI GPT API integration

## Project Structure

```
lingvopal/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js 13+ app directory
│   │   │   ├── components/      # Reusable React components
│   │   │   ├── store/          # Redux store configuration
│   │   │   ├── styles/         # Global styles and Tailwind config
│   │   │   └── types/          # TypeScript type definitions
│   │   ├── public/             # Static assets
│   │   └── package.json
│   │
│   ├── backend/                 # FastAPI backend application
│   │   ├── app/
│   │   │   ├── api/            # API routes
│   │   │   ├── core/           # Core functionality
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Business logic
│   │   ├── tests/              # Backend tests
│   │   └── requirements.txt
│   │
│   ├── database/               # Database migrations and seeds
│   │   ├── migrations/
│   │   └── seeds/
│   │
│   └── docker/                 # Docker configuration files
│       ├── frontend/
│       ├── backend/
│       └── database/
```

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 14+
- Docker and Docker Compose

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lingvopal.git
cd lingvopal
```

2. Set up the frontend:
```bash
cd frontend
npm install
npm run dev
```

3. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Set up the database:
```bash
# Using Docker
docker-compose up -d db
```

### Environment Variables

Create `.env` files in both frontend and backend directories:

Frontend (.env):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_CONFIG={your_firebase_config}
```

Backend (.env):
```
DATABASE_URL=postgresql://user:password@localhost:5432/lingvopal
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
```

## Features

- User authentication with social login
- AI-powered language learning exercises
- Progress tracking and analytics
- Social features for language exchange
- Real-time chat and voice calls
- Customizable learning paths

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- The open-source community for various tools and libraries used in this project
