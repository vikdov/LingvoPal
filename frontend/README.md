frontend/
├── public/
│   └── favicon.svg
│
├── src/
│   ├── app/                          # App wiring only
│   │   ├── router.tsx                # All routes (single source of truth)
│   │   ├── providers.tsx             # Auth, query, theme providers
│   │   ├── App.tsx                   # Root component
│   │   └── NotFoundView.tsx           # 404 (NOT a feature)
│   │
│   ├── features/                     # ⭐ Domain-driven features
│   │
│   │   ├── landing/                  # Public landing page
│   │   │   ├── components/
│   │   │   │   ├── Hero.tsx
│   │   │   │   ├── FeatureList.tsx
│   │   │   │   └── CallToAction.tsx
│   │   │   ├── views/
│   │   │   │   └── LandingView.tsx
│   │   │   └── index.ts
│   │
│   │   ├── auth/
│   │   │   ├── api/auth.api.ts
│   │   │   ├── components/AuthForm.tsx
│   │   │   ├── hooks/useAuth.ts
│   │   │   ├── model/auth.store.ts
│   │   │   ├── types/auth.types.ts
│   │   │   ├── views/
│   │   │   │   ├── LoginView.tsx
│   │   │   │   └── RegisterView.tsx
│   │   │   └── index.ts
│   │
│   │   ├── practice/
│   │   │   ├── api/practice.api.ts
│   │   │   ├── components/
│   │   │   │   ├── PracticeCard.tsx
│   │   │   │   ├── AnswerInput.tsx
│   │   │   │   │── Feedback.tsx
│   │   │   ├── hooks/usePracticeSession.ts
│   │   │   ├── model/practice.store.ts
│   │   │   ├── types/practice.types.ts
│   │   │   ├── views/
│   │   │   │   ├── PracticeView.tsx
│   │   │   │   └── SessionSummaryView.tsx
│   │   │   └── index.ts
│   │
│   │   ├── sets/
│   │   │   ├── api/sets.api.ts
│   │   │   ├── components/
│   │   │   │   ├── SetCard.tsx
│   │   │   │   ├── SetEditor.tsx
│   │   │   │   └── SetFilters.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useSetsQuery.ts
│   │   │   │   └── useAddItemMutation.ts
│   │   │   ├── model/sets.store.ts
│   │   │   ├── types/sets.types.ts
│   │   │   ├── views/
│   │   │   │   ├── SetsListView.tsx
│   │   │   │   └── SetDetailView.tsx
│   │   │   └── index.ts
│   │
│   │   ├── stats/
│   │   │   ├── api/stats.api.ts
│   │   │   ├── components/
│   │   │   │   ├── ProgressChart.tsx
│   │   │   │   └── StatsCard.tsx
│   │   │   ├── hooks/useStats.ts
│   │   │   ├── types/stats.types.ts
│   │   │   ├── views/DashboardView.tsx
│   │   │   └── index.ts
│   │
│   │   ├── settings/                 # User preferences (IMPORTANT)
│   │   │   ├── components/
│   │   │   │   ├── LanguageSelector.tsx
│   │   │   │   ├── ThemeToggle.tsx
│   │   │   │   └── PrivacySettings.tsx
│   │   │   ├── model/settings.store.ts
│   │   │   ├── types/settings.types.ts
│   │   │   ├── views/SettingsView.tsx
│   │   │   └── index.ts
│   │
│   ├── components/                   # Shared, dumb UI
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Spinner.tsx
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── AuthLayout.tsx
│   │   │   └── PublicLayout.tsx
│   │   └── navigation/
│   │       ├── Navbar.tsx
│   │       └── Sidebar.tsx
│   │
│   ├── services/
│   │   └── api.ts
│   │
│   ├── store/
│   │   └── ui.store.ts
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   └── animations.css
│   │
│   ├── types/
│   │   └── common.types.ts
│   │
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── formatting.ts
│   │   └── validation.ts
│   │
│   └── main.tsx
│
├── .env.example
├── .gitignore
├── eslint.config.js
├── prettier.config.js
├── tsconfig.json
├── vite.config.ts
├── package.json
└── README.md
