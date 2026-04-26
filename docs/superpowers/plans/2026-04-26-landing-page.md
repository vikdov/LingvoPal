# Landing Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Editorial Atelier landing page with a dark-first modern startup page (Vercel/Supabase style) with light mode toggle, method-first copy, and all sections from the approved spec.

**Architecture:** `LandingView` owns theme state, wraps everything in `[data-lp]` + `[data-theme]` attributes, and composes all section components. Landing CSS tokens (`--lp-*`) live in `landing.css` scoped to `[data-lp]` — zero conflict with `globals.css` app tokens. `PublicLayout` is renamed to `LandingLayout` (thin pass-through); nav moves inside `LandingView`.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (CSS-first), React Router v6, `cn()` from `src/lib/utils.ts`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| **Create** | `src/features/landing/styles/landing.css` | All `--lp-*` CSS tokens, dark + light, gradient text class |
| **Create** | `src/features/landing/hooks/useTheme.ts` | Read/write `localStorage`, return `{ theme, toggleTheme }` |
| **Create** | `src/features/landing/components/LandingNav.tsx` | Sticky nav: logo, theme toggle, sign-in, CTA |
| **Rewrite** | `src/features/landing/components/Hero.tsx` | Full hero with all spec elements |
| **Create** | `src/features/landing/components/HowItWorks.tsx` | 3-step grid with real examples |
| **Create** | `src/features/landing/components/FeaturesBento.tsx` | 3×2 bento grid |
| **Delete** | `src/features/landing/components/FeatureList.tsx` | Replaced by FeaturesBento |
| **Create** | `src/features/landing/components/ObjectionHandler.tsx` | 3-card objection row |
| **Rewrite** | `src/features/landing/components/DemoSection.tsx` | Browser chrome wrapper; inner loop logic kept |
| **Rewrite** | `src/features/landing/components/CallToAction.tsx` | New CTA with gradient quote |
| **Create** | `src/features/landing/components/LandingFooter.tsx` | Minimal footer bar |
| **Rewrite** | `src/features/landing/views/LandingView.tsx` | Compose all sections, manage theme |
| **Update** | `src/features/landing/index.ts` | No change needed (still exports `LandingView`) |
| **Rename+Rewrite** | `src/components/layout/PublicLayout.tsx` → `LandingLayout.tsx` | Thin `<Outlet />` wrapper, no nav |
| **Update** | `src/app/router.tsx` | Import `LandingLayout` instead of `PublicLayout` |

---

## Task 1: CSS Tokens

**Files:**
- Create: `src/features/landing/styles/landing.css`

- [ ] **Step 1: Create landing.css**

```css
/* Landing page design tokens — scoped to [data-lp] */
/* Zero overlap with globals.css --color-* vars */

[data-lp] {
  --lp-bg:           #09090b;
  --lp-surface:      #18181b;
  --lp-surface-alt:  #1f1f23;
  --lp-border:       #27272a;
  --lp-text:         #fafafa;
  --lp-text-muted:   #a1a1aa;
  --lp-text-faint:   #52525b;
  --lp-accent:       #6366f1;
  --lp-accent2:      #8b5cf6;
  --lp-brand:        #D96374;
  --lp-teal:         #78AFA7;
  --lp-gradient:     linear-gradient(135deg, #818cf8, #a78bfa, #e879f9);

  background-color: var(--lp-bg);
  color: var(--lp-text);
  min-height: 100vh;
}

[data-lp][data-theme="light"] {
  --lp-bg:          #fafafa;
  --lp-surface:     #ffffff;
  --lp-surface-alt: #f4f4f5;
  --lp-border:      #e4e4e7;
  --lp-text:        #09090b;
  --lp-text-muted:  #71717a;
  --lp-text-faint:  #a1a1aa;
}

/* Gradient text utility */
[data-lp] .lp-gradient-text {
  background: var(--lp-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Section label pill */
[data-lp] .lp-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--lp-text-faint);
  border: 1px solid var(--lp-border);
  border-radius: 9999px;
  padding: 4px 12px;
  font-family: monospace;
}

[data-lp] .lp-dot {
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--lp-accent);
  box-shadow: 0 0 6px var(--lp-accent);
}

/* Cursor blink — used by DemoSection */
@keyframes lp-cursor-blink {
  0%, 45%  { opacity: 1; }
  55%, 100% { opacity: 0; }
}
```

- [ ] **Step 2: Start dev server and verify no import errors**

```bash
cd frontend && npm run dev
```

Expected: server starts at `http://localhost:5173`, no errors in terminal. File not imported anywhere yet — that's fine.

---

## Task 2: useTheme Hook

**Files:**
- Create: `src/features/landing/hooks/useTheme.ts`

- [ ] **Step 1: Create useTheme.ts**

```ts
import { useState, useEffect } from 'react';

export type LpTheme = 'dark' | 'light';

export function useTheme() {
  const [theme, setTheme] = useState<LpTheme>(() => {
    try {
      return (localStorage.getItem('lp-theme') as LpTheme) ?? 'dark';
    } catch {
      return 'dark';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('lp-theme', theme);
    } catch {
      // localStorage unavailable — proceed without persistence
    }
  }, [theme]);

  function toggleTheme() {
    setTheme(t => (t === 'dark' ? 'light' : 'dark'));
  }

  return { theme, toggleTheme };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npm run lint
```

Expected: no errors on the new file.

- [ ] **Step 3: Commit**

```bash
git add src/features/landing/styles/landing.css src/features/landing/hooks/useTheme.ts
git commit -m "feat(landing): add CSS tokens and useTheme hook"
```

---

## Task 3: LandingLayout + Router Update

**Files:**
- Create: `src/components/layout/LandingLayout.tsx`
- Delete: `src/components/layout/PublicLayout.tsx`
- Modify: `src/app/router.tsx`

- [ ] **Step 1: Create LandingLayout.tsx**

```tsx
import { Outlet } from 'react-router-dom';

export function LandingLayout() {
  return <Outlet />;
}
```

The nav is now rendered inside `LandingView` — this layout is intentionally minimal.

- [ ] **Step 2: Update router.tsx**

Replace the `PublicLayout` import with `LandingLayout`:

```tsx
// Remove:
import { PublicLayout } from '@/components/layout/PublicLayout';

// Add:
import { LandingLayout } from '@/components/layout/LandingLayout';
```

Replace usage in the route tree (line ~29):

```tsx
// Before:
{
  path: '/',
  element: <PublicLayout />,
  children: [
    { index: true, element: <LandingView /> },
  ],
},

// After:
{
  path: '/',
  element: <LandingLayout />,
  children: [
    { index: true, element: <LandingView /> },
  ],
},
```

- [ ] **Step 3: Delete PublicLayout.tsx**

```bash
rm src/components/layout/PublicLayout.tsx
```

- [ ] **Step 4: Verify no broken imports**

```bash
cd frontend && npm run lint
```

Expected: no errors referencing `PublicLayout`.

- [ ] **Step 5: Commit**

```bash
git add src/components/layout/LandingLayout.tsx src/app/router.tsx
git commit -m "feat(landing): replace PublicLayout with thin LandingLayout"
```

---

## Task 4: LandingNav Component

**Files:**
- Create: `src/features/landing/components/LandingNav.tsx`

- [ ] **Step 1: Create LandingNav.tsx**

```tsx
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import type { LpTheme } from '../hooks/useTheme';

interface LandingNavProps {
  theme: LpTheme;
  onToggleTheme: () => void;
}

export function LandingNav({ theme, onToggleTheme }: LandingNavProps) {
  return (
    <header
      className={cn(
        'sticky top-0 z-50 flex items-center justify-between',
        'px-6 h-14 border-b border-[var(--lp-border)]',
        'backdrop-blur-md',
      )}
      style={{
        background:
          theme === 'light'
            ? 'rgba(250,250,250,0.85)'
            : 'rgba(9,9,11,0.8)',
      }}
    >
      <Link
        to="/"
        className="font-bold text-[15px] tracking-tight text-[var(--lp-text)] no-underline"
      >
        Lingvo<em className="not-italic text-[var(--lp-brand)]">Pal</em>
      </Link>

      <div className="flex items-center gap-3">
        <button
          onClick={onToggleTheme}
          aria-label="Toggle light/dark theme"
          className={cn(
            'w-8 h-8 flex items-center justify-center rounded-md text-sm cursor-pointer',
            'border border-[var(--lp-border)] text-[var(--lp-text-muted)]',
            'hover:text-[var(--lp-text)] hover:border-[var(--lp-text-muted)] transition-colors',
          )}
        >
          {theme === 'dark' ? '☀' : '🌙'}
        </button>

        <Link
          to="/auth/login"
          className={cn(
            'text-[13px] text-[var(--lp-text-muted)] no-underline',
            'px-3 py-1.5 rounded-md border border-[var(--lp-border)]',
            'hover:text-[var(--lp-text)] hover:border-[var(--lp-text-muted)] transition-colors',
          )}
        >
          Sign in
        </Link>

        <Link
          to="/auth/register"
          className="text-[13px] font-semibold text-white no-underline px-4 py-1.5 rounded-md bg-[var(--lp-accent)] hover:bg-[#5558e3] transition-colors"
          style={{ boxShadow: '0 0 16px -4px rgba(99,102,241,0.5)' }}
        >
          Write your first sentence →
        </Link>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Verify lint passes**

```bash
cd frontend && npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/features/landing/components/LandingNav.tsx
git commit -m "feat(landing): add LandingNav with theme toggle"
```

---

## Task 5: Hero Component

**Files:**
- Rewrite: `src/features/landing/components/Hero.tsx`

- [ ] **Step 1: Rewrite Hero.tsx**

```tsx
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function Hero() {
  return (
    <section className="relative flex flex-col items-center text-center px-6 pt-24 pb-20 overflow-hidden gap-5">
      {/* Dot grid */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),' +
            'linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          maskImage:
            'radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)',
        }}
      />
      {/* Radial glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute"
        style={{
          top: '-80px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '300px',
          background:
            'radial-gradient(ellipse, rgba(99,102,241,0.22) 0%, rgba(139,92,246,0.1) 40%, transparent 70%)',
        }}
      />

      {/* Who it's for */}
      <p className="relative font-mono text-[11px] tracking-widest uppercase text-[var(--lp-text-faint)]">
        For learners who want to actually remember, not just recognize.
      </p>

      {/* Badge */}
      <div className="relative inline-flex items-center gap-2 border border-indigo-500/30 rounded-full px-4 py-1 text-[12px] text-indigo-300 font-mono bg-indigo-500/5">
        <span aria-hidden>✦</span> Active recall · Spaced repetition
      </div>

      {/* H1 */}
      <h1
        className="relative font-extrabold tracking-[-0.04em] leading-none text-[var(--lp-text)]"
        style={{ fontSize: 'clamp(2.5rem, 6vw, 4.5rem)' }}
      >
        Learn a language by{' '}
        <span className="lp-gradient-text">writing</span> it.
      </h1>

      {/* Differentiator — must be prominent */}
      <p className="relative text-[1.0625rem] font-semibold text-[var(--lp-text)] max-w-[34ch]">
        You don't recognize words — you produce them.
      </p>

      {/* Subtext */}
      <p className="relative text-[0.9375rem] text-[var(--lp-text-muted)] max-w-[40ch] leading-relaxed">
        No multiple choice. No guessing. Type the word from memory,
        in context — every time.
      </p>

      {/* Difficulty honesty */}
      <p className="relative font-mono text-[11px] italic text-[var(--lp-text-faint)]">
        It's harder than tapping pictures. That's exactly why it works.
      </p>

      {/* CTAs */}
      <div className="relative flex items-center gap-3 flex-wrap justify-center mt-1">
        <Link
          to="/auth/register"
          className="text-[14px] font-semibold text-white no-underline px-6 py-2.5 rounded-md bg-[var(--lp-accent)] hover:bg-[#5558e3] transition-colors"
          style={{
            boxShadow:
              '0 0 24px -6px rgba(99,102,241,0.5), 0 1px 0 rgba(255,255,255,0.08) inset',
          }}
        >
          Write your first sentence →
        </Link>
        <a
          href="#how-it-works"
          className={cn(
            'text-[14px] text-[var(--lp-text-muted)] no-underline px-6 py-2.5 rounded-md',
            'border border-[var(--lp-border)]',
            'hover:border-[var(--lp-text-muted)] hover:text-[var(--lp-text)] transition-colors',
          )}
        >
          See how it works ↓
        </a>
      </div>

      {/* Trust signals — surfaced early */}
      <p className="relative font-mono text-[11px] tracking-widest text-[var(--lp-text-faint)]">
        open source · no tracking · self-hostable
      </p>

      {/* Floating demo card */}
      <div
        className="relative w-full max-w-[580px] mt-4 text-left rounded-xl border border-[var(--lp-border)] bg-[var(--lp-surface)]"
        style={{
          boxShadow:
            '0 0 0 1px rgba(99,102,241,0.08), 0 32px 64px -32px rgba(0,0,0,0.6), 0 0 40px -10px rgba(99,102,241,0.1)',
        }}
      >
        {/* Browser chrome */}
        <div className="flex items-center gap-1.5 px-4 py-3 border-b border-[var(--lp-border)]">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-[var(--lp-text-faint)]">
            Italian · imperfetto · leggere
          </span>
        </div>
        <div className="px-6 py-5 flex flex-col gap-3">
          <p
            className="font-[var(--font-display)] leading-relaxed text-[var(--lp-text)]"
            style={{ fontSize: 'clamp(1.1rem, 2vw, 1.35rem)' }}
          >
            Da bambino,{' '}
            <span
              className="font-mono text-[0.92em] text-[#a78bfa] px-0.5"
              style={{ borderBottom: '2px solid var(--lp-accent)' }}
            >
              leggevo
            </span>
            {' '}ogni sera fino a mezzanotte.
          </p>
          <p className="text-[0.875rem] text-[var(--lp-text-muted)] italic">
            "As a boy, I used to read every evening until midnight."
          </p>
          <div className="flex gap-1.5 flex-wrap pt-3 border-t border-[var(--lp-border)]">
            <HeroChip>new word</HeroChip>
            <HeroChip>interval · 6h</HeroChip>
            <HeroChip accent>✓ correct · next review tomorrow</HeroChip>
          </div>
        </div>
      </div>
    </section>
  );
}

function HeroChip({
  children,
  accent,
}: {
  children: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <span
      className={cn(
        'font-mono text-[10px] tracking-widest uppercase px-2 py-1 rounded-sm border',
        accent
          ? 'border-indigo-700 text-indigo-400 bg-indigo-500/5'
          : 'border-[var(--lp-border)] text-[var(--lp-text-faint)]',
      )}
    >
      {children}
    </span>
  );
}
```

- [ ] **Step 2: Lint**

```bash
cd frontend && npm run lint
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/features/landing/components/Hero.tsx
git commit -m "feat(landing): rewrite Hero with differentiator line and trust signals"
```

---

## Task 6: HowItWorks Component

**Files:**
- Create: `src/features/landing/components/HowItWorks.tsx`

- [ ] **Step 1: Create HowItWorks.tsx**

```tsx
const STEPS: ReadonlyArray<{
  num: string;
  title: string;
  body: string;
  example: string;
}> = [
  {
    num: '01',
    title: 'Add your vocabulary',
    body: 'Import a word, phrase, or conjugation. Pair it with a real sentence.',
    example: 'gehen → Ich gehe jeden Tag zur Arbeit.',
  },
  {
    num: '02',
    title: 'Practice in context',
    body: 'Fill the gap. Type from memory, letter by letter. No hints. No word bank.',
    example: 'Ich ___ jeden Tag zur Arbeit.\nYou type: gehe',
  },
  {
    num: '03',
    title: 'SM-2 schedules the rest',
    body: 'Your ease and lapse history shape when you see it again. Optimal spacing, automatic.',
    example: '6h → 1d → 3d → 9d → …',
  },
];

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="flex flex-col items-center gap-12 px-6 py-20 border-t border-[var(--lp-border)]"
    >
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="lp-label">
          <span className="lp-dot" /> The method
        </div>
        <h2
          className="font-bold tracking-[-0.03em] text-[var(--lp-text)]"
          style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
        >
          Three steps. One habit.
        </h2>
        <p className="text-[0.9375rem] text-[var(--lp-text-muted)] max-w-[40ch] leading-relaxed">
          No passive review. No tapping pictures. Just writing — the way your brain
          actually learns.
        </p>
      </div>

      <div
        className="w-full max-w-[860px] rounded-xl overflow-hidden border border-[var(--lp-border)]"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          background: 'var(--lp-border)',
          gap: '1px',
        }}
      >
        {STEPS.map((step) => (
          <div
            key={step.num}
            className="flex flex-col gap-3 p-7 bg-[var(--lp-bg)] hover:bg-[var(--lp-surface)] transition-colors"
          >
            <div className="flex items-center gap-2 font-mono text-[11px] tracking-widest uppercase text-[var(--lp-accent)]">
              <span
                aria-hidden
                className="w-6 h-px bg-[var(--lp-accent)] opacity-40"
              />
              {step.num}
            </div>
            <h3 className="font-semibold tracking-[-0.02em] text-[var(--lp-text)] text-[1.0625rem]">
              {step.title}
            </h3>
            <p className="text-[0.875rem] text-[var(--lp-text-muted)] leading-relaxed">
              {step.body}
            </p>
            <pre className="mt-1 text-[11px] font-mono text-[var(--lp-text-muted)] bg-[var(--lp-surface)] border border-[var(--lp-border)] rounded-md p-3 whitespace-pre-wrap leading-relaxed">
              {step.example}
            </pre>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Lint + commit**

```bash
cd frontend && npm run lint
git add src/features/landing/components/HowItWorks.tsx
git commit -m "feat(landing): add HowItWorks with real examples"
```

---

## Task 7: FeaturesBento Component

**Files:**
- Create: `src/features/landing/components/FeaturesBento.tsx`
- Delete: `src/features/landing/components/FeatureList.tsx`

- [ ] **Step 1: Create FeaturesBento.tsx**

```tsx
import { cn } from '@/lib/utils';

interface BentoCard {
  wide?: boolean;
  accent?: boolean;
  title: string;
  body: string;
  example?: string;
  tag?: string;
}

const CARDS: BentoCard[] = [
  {
    wide: true,
    title: "You produce words — you don't just recognize them",
    body: 'Every session asks you to type the word from memory, in the exact form it appears in speech. No word bank. No multiple choice. This is why it sticks.',
    example: 'Da bambino, ___ ogni sera…\nYou type: leggevo',
    tag: 'active recall',
  },
  {
    title: 'Words live inside real sentences',
    body: 'Not flashcards in isolation — an imperfetto in a memoir, a subjunctive in a letter. Context makes recall more likely.',
    tag: 'context-driven',
  },
  {
    title: 'You review right before you forget',
    body: 'SM-2 tracks your ease, pace, and lapse history and schedules the exact moment to review for maximum retention.',
    tag: 'SM-2 · adaptive',
  },
  {
    title: 'Your first review comes today',
    body: 'New words get a 6-hour first interval — not the next day — so they anchor before they fade.',
  },
  {
    title: 'Any language, your vocabulary',
    body: "Build sets from your own words or import existing decks. Italian, French, German, Japanese — whatever you're learning.",
  },
  {
    accent: true,
    title: 'Free. Open source. Self-hostable.',
    body: 'No subscription. Run it on your own server. Your data stays yours.',
  },
];

export function FeaturesBento() {
  return (
    <section className="flex flex-col items-center gap-10 px-6 py-20 border-t border-[var(--lp-border)]">
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="lp-label">
          <span className="lp-dot" /> Features
        </div>
        <h2
          className="font-bold tracking-[-0.03em] text-[var(--lp-text)]"
          style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
        >
          Built for how memory works.
        </h2>
      </div>

      <div
        className="w-full max-w-[900px] rounded-xl overflow-hidden border border-[var(--lp-border)]"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          background: 'var(--lp-border)',
          gap: '1px',
        }}
      >
        {CARDS.map((card, i) => (
          <div
            key={i}
            className={cn(
              'flex flex-col gap-3 p-7 transition-colors',
              card.wide && 'col-span-2',
              card.accent
                ? 'bg-[var(--lp-surface-alt)] hover:bg-[var(--lp-surface)]'
                : 'bg-[var(--lp-surface)] hover:bg-[var(--lp-surface-alt)]',
            )}
          >
            <h3 className="font-semibold tracking-[-0.02em] text-[var(--lp-text)] text-[0.9375rem] leading-snug">
              {card.title}
            </h3>
            <p className="text-[0.8125rem] text-[var(--lp-text-muted)] leading-relaxed">
              {card.body}
            </p>
            {card.example && (
              <pre className="text-[11px] font-mono text-[var(--lp-text-muted)] bg-[var(--lp-bg)] border border-[var(--lp-border)] rounded-md p-3 whitespace-pre-wrap leading-relaxed mt-1">
                {card.example}
              </pre>
            )}
            {card.tag && (
              <span className="mt-auto self-start font-mono text-[9px] tracking-widest uppercase text-[var(--lp-teal)] border border-[rgba(120,175,167,0.3)] rounded-sm px-1.5 py-0.5">
                {card.tag}
              </span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Delete FeatureList.tsx**

```bash
rm src/features/landing/components/FeatureList.tsx
```

- [ ] **Step 3: Lint**

```bash
cd frontend && npm run lint
```

Expected: no errors (FeatureList is not imported anywhere else after LandingView update in Task 11).

- [ ] **Step 4: Commit**

```bash
git add src/features/landing/components/FeaturesBento.tsx
git rm src/features/landing/components/FeatureList.tsx
git commit -m "feat(landing): add FeaturesBento, delete FeatureList"
```

---

## Task 8: ObjectionHandler Component

**Files:**
- Create: `src/features/landing/components/ObjectionHandler.tsx`

- [ ] **Step 1: Create ObjectionHandler.tsx**

```tsx
interface Objection {
  question: string;
  answer: string;
}

const OBJECTIONS: Objection[] = [
  {
    question: "I'm a beginner — is this too hard?",
    answer:
      "Sentences provide full context. You're not guessing a word in isolation — the surrounding sentence gives you the clue.",
  },
  {
    question: 'Can I use my own vocabulary?',
    answer:
      "Yes. Build sets from your own words, your textbook, or your teacher's list.",
  },
  {
    question: "Isn't it just harder Anki?",
    answer:
      'Similar scheduling, completely different input. Anki asks you to rate how well you remember. LingvoPal asks you to prove it.',
  },
];

export function ObjectionHandler() {
  return (
    <section className="px-6 py-10 border-t border-[var(--lp-border)]">
      <div
        className="w-full max-w-[900px] mx-auto rounded-xl overflow-hidden border border-[var(--lp-border)]"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          background: 'var(--lp-border)',
          gap: '1px',
        }}
      >
        {OBJECTIONS.map((o) => (
          <div
            key={o.question}
            className="flex flex-col gap-2 p-6 bg-[var(--lp-surface)]"
          >
            <p className="font-semibold text-[0.875rem] text-[var(--lp-text)] leading-snug">
              "{o.question}"
            </p>
            <p className="text-[0.8125rem] text-[var(--lp-text-muted)] leading-relaxed">
              {o.answer}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Lint + commit**

```bash
cd frontend && npm run lint
git add src/features/landing/components/ObjectionHandler.tsx
git commit -m "feat(landing): add ObjectionHandler section"
```

---

## Task 9: DemoSection Update

**Files:**
- Rewrite: `src/features/landing/components/DemoSection.tsx`

The inner logic (`useDemoLoop`, `GapWord`, `Chip`, `ANSWER`/`BEFORE`/`AFTER`/`TRANSLATION` constants) is **kept exactly as-is**. Only the outer JSX shell changes: new heading, browser chrome wrapper, `--lp-*` color vars on `GapWord` and `Chip`.

`GapWord` must use `--lp-accent`, `--lp-brand`, `--lp-border` instead of `--color-accent`, `--color-primary`, `--color-border` so it renders correctly in both landing dark and light modes.

- [ ] **Step 1: Rewrite DemoSection.tsx**

```tsx
import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

const ANSWER = 'leggevo';
const BEFORE = 'Da bambino, ';
const AFTER = ' ogni sera fino a mezzanotte.';
const TRANSLATION = '"As a boy, I used to read every evening until midnight."';

type Phase = 'idle' | 'typing' | 'correct';

function useDemoLoop() {
  const [phase, setPhase] = useState<Phase>('idle');
  const [typed, setTyped] = useState('');

  useEffect(() => {
    let t: ReturnType<typeof setTimeout>;

    if (phase === 'idle') {
      t = setTimeout(() => setPhase('typing'), 1800);
    } else if (phase === 'typing') {
      if (typed.length < ANSWER.length) {
        t = setTimeout(
          () => setTyped(ANSWER.slice(0, typed.length + 1)),
          typed.length === 0 ? 400 : 210,
        );
      } else {
        t = setTimeout(() => setPhase('correct'), 380);
      }
    } else {
      t = setTimeout(() => {
        setTyped('');
        setPhase('idle');
      }, 2600);
    }

    return () => clearTimeout(t);
  }, [phase, typed]);

  return { phase, typed };
}

export function DemoSection() {
  const { phase, typed } = useDemoLoop();
  const isCorrect = phase === 'correct';
  const isIdle = phase === 'idle' && typed.length === 0;

  return (
    <section className="flex flex-col items-center gap-8 px-6 py-20 bg-[var(--lp-surface)] border-y border-[var(--lp-border)]">
      <div className="lp-label">
        <span className="lp-dot" /> Interaction preview
      </div>

      <div className="flex flex-col items-center gap-2 text-center">
        <h2
          className="font-bold tracking-[-0.03em] text-[var(--lp-text)]"
          style={{ fontSize: 'clamp(1.75rem, 3vw, 2.25rem)' }}
        >
          This is the entire learning loop.
        </h2>
        <p className="text-[0.9375rem] text-[var(--lp-text-muted)]">
          This is exactly what you'll do every day.
        </p>
      </div>

      {/* Browser window chrome */}
      <div
        className="w-full max-w-[680px] rounded-xl overflow-hidden border border-[var(--lp-border)]"
        style={{ boxShadow: '0 32px 64px -32px rgba(0,0,0,0.5)' }}
      >
        <div className="flex items-center gap-1.5 px-4 py-3 bg-[var(--lp-surface-alt)] border-b border-[var(--lp-border)]">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-[var(--lp-text-faint)]">
            lingvopal — practice
          </span>
        </div>

        <div className="px-8 py-6 bg-[var(--lp-bg)] flex flex-col gap-5">
          <div className="flex items-baseline justify-between gap-4 pb-4 border-b border-[var(--lp-border)]">
            <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--lp-text-faint)]">
              Specimen — Italian · verb · imperfetto
            </span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--lp-text-faint)] shrink-0">
              leggere
            </span>
          </div>

          <p
            className="font-[var(--font-display)] leading-relaxed text-[var(--lp-text)]"
            style={{ fontSize: 'clamp(1.125rem, 2vw, 1.5rem)' }}
          >
            {BEFORE}
            <GapWord typed={typed} isCorrect={isCorrect} isIdle={isIdle} />
            {AFTER}
          </p>

          <p className="text-[0.9375rem] text-[var(--lp-text-muted)] italic leading-relaxed">
            {TRANSLATION}
          </p>

          <div className="flex gap-1.5 flex-wrap pt-4 border-t border-[var(--lp-border)]">
            <Chip>new word</Chip>
            <Chip>interval · 6h</Chip>
            {isCorrect
              ? <Chip accent>✓ correct · next review tomorrow</Chip>
              : <Chip>SM-2 · ease 2.5</Chip>}
          </div>
        </div>
      </div>

      <p className="font-mono text-[10px] uppercase tracking-widest text-[var(--lp-text-faint)]">
        Auto-demo — try it live after signing up
      </p>
    </section>
  );
}

interface GapWordProps {
  typed: string;
  isCorrect: boolean;
  isIdle: boolean;
}

function GapWord({ typed, isCorrect, isIdle }: GapWordProps) {
  const isEmpty = isIdle && typed.length === 0;
  const isTyping = !isEmpty && !isCorrect;

  const color = isCorrect
    ? 'var(--lp-teal)'
    : isEmpty
      ? 'var(--lp-text-faint)'
      : 'var(--lp-brand)';

  const bg = isCorrect
    ? 'rgba(120,175,167,0.1)'
    : isEmpty
      ? 'transparent'
      : 'rgba(217,99,116,0.08)';

  const borderColor = isCorrect
    ? 'var(--lp-teal)'
    : isEmpty
      ? 'var(--lp-border)'
      : 'var(--lp-brand)';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'baseline',
        padding: '0.05em 0.3em',
        fontFamily: 'monospace',
        fontWeight: 500,
        fontSize: '0.92em',
        color,
        background: bg,
        borderBottom: `2px solid ${borderColor}`,
        transition: 'color 0.25s, background 0.25s, border-color 0.25s',
        minWidth: '5.5ch',
        verticalAlign: 'baseline',
        lineHeight: 1.4,
      }}
    >
      {isEmpty ? '___' : typed.length === 0 ? ' ' : typed}
      {isTyping && (
        <span
          aria-hidden
          style={{
            display: 'inline-block',
            width: '2px',
            height: '0.9em',
            marginLeft: '1px',
            background: 'var(--lp-accent)',
            animation: 'lp-cursor-blink 1.05s steps(1) infinite',
            verticalAlign: 'middle',
            flexShrink: 0,
          }}
        />
      )}
    </span>
  );
}

function Chip({
  children,
  accent,
}: {
  children: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <span
      className={cn(
        'font-mono text-[10px] tracking-widest uppercase px-2 py-1 rounded-sm border transition-colors',
        accent
          ? 'border-[var(--lp-teal)]/40 text-[var(--lp-teal)] bg-[rgba(120,175,167,0.06)]'
          : 'border-[var(--lp-border)] text-[var(--lp-text-faint)]',
      )}
    >
      {children}
    </span>
  );
}
```

- [ ] **Step 2: Lint + commit**

```bash
cd frontend && npm run lint
git add src/features/landing/components/DemoSection.tsx
git commit -m "feat(landing): update DemoSection with browser chrome and lp-* tokens"
```

---

## Task 10: CallToAction + LandingFooter

**Files:**
- Rewrite: `src/features/landing/components/CallToAction.tsx`
- Create: `src/features/landing/components/LandingFooter.tsx`

- [ ] **Step 1: Rewrite CallToAction.tsx**

```tsx
import { Link } from 'react-router-dom';

export function CallToAction() {
  return (
    <section className="relative flex flex-col items-center text-center gap-7 px-6 py-28 overflow-hidden border-t border-[var(--lp-border)]">
      {/* Bottom glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-1/2 -translate-x-1/2"
        style={{
          width: '500px',
          height: '250px',
          background:
            'radial-gradient(ellipse, rgba(99,102,241,0.18) 0%, transparent 70%)',
        }}
      />

      <div className="lp-label">
        <span className="lp-dot" /> Get started
      </div>

      <h2
        className="relative font-bold tracking-[-0.03em] leading-tight text-[var(--lp-text)] max-w-[20ch]"
        style={{ fontSize: 'clamp(2rem, 4vw, 3rem)' }}
      >
        A language isn't learned.{' '}
        <span className="lp-gradient-text">It's written into you.</span>
      </h2>

      <p className="relative text-[0.9375rem] text-[var(--lp-text-muted)]">
        One sentence at a time. No credit card. No commitment.
      </p>

      <Link
        to="/auth/register"
        className="relative text-[15px] font-semibold text-white no-underline px-7 py-3 rounded-md bg-[var(--lp-accent)] hover:bg-[#5558e3] transition-colors"
        style={{ boxShadow: '0 0 30px -8px rgba(99,102,241,0.6)' }}
      >
        Start your first recall session →
      </Link>

      <p className="relative font-mono text-[11px] tracking-widest uppercase text-[var(--lp-text-faint)]">
        free · self-hostable · no tracking · open source
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Create LandingFooter.tsx**

```tsx
export function LandingFooter() {
  return (
    <footer className="flex items-center justify-between px-6 py-6 border-t border-[var(--lp-border)]">
      <span className="font-bold text-[13px] tracking-tight text-[var(--lp-text-muted)]">
        Lingvo<em className="not-italic text-[var(--lp-brand)]">Pal</em>
        <span className="ml-2 font-normal text-[var(--lp-text-faint)]">
          — writing-first language learning
        </span>
      </span>
      <span className="font-mono text-[11px] text-[var(--lp-text-faint)]">
        © 2026
      </span>
    </footer>
  );
}
```

- [ ] **Step 3: Lint + commit**

```bash
cd frontend && npm run lint
git add src/features/landing/components/CallToAction.tsx src/features/landing/components/LandingFooter.tsx
git commit -m "feat(landing): rewrite CTA and add LandingFooter"
```

---

## Task 11: LandingView — Compose Everything

**Files:**
- Rewrite: `src/features/landing/views/LandingView.tsx`

- [ ] **Step 1: Rewrite LandingView.tsx**

```tsx
import '../styles/landing.css';
import { useTheme } from '../hooks/useTheme';
import { LandingNav } from '../components/LandingNav';
import { Hero } from '../components/Hero';
import { HowItWorks } from '../components/HowItWorks';
import { FeaturesBento } from '../components/FeaturesBento';
import { ObjectionHandler } from '../components/ObjectionHandler';
import { DemoSection } from '../components/DemoSection';
import { CallToAction } from '../components/CallToAction';
import { LandingFooter } from '../components/LandingFooter';

export function LandingView() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div data-lp="" data-theme={theme}>
      <LandingNav theme={theme} onToggleTheme={toggleTheme} />
      <main>
        <Hero />
        <HowItWorks />
        <FeaturesBento />
        <ObjectionHandler />
        <DemoSection />
        <CallToAction />
      </main>
      <LandingFooter />
    </div>
  );
}
```

- [ ] **Step 2: Verify index.ts barrel still works**

`src/features/landing/index.ts` exports `LandingView` — no change needed:

```ts
export { LandingView } from './views/LandingView';
```

Confirm the file content matches. If it imports `FeatureList` anywhere, remove that import.

- [ ] **Step 3: Lint**

```bash
cd frontend && npm run lint
```

Expected: no errors. If `FeatureList` is still referenced somewhere, remove those lines.

- [ ] **Step 4: Commit**

```bash
git add src/features/landing/views/LandingView.tsx src/features/landing/index.ts
git commit -m "feat(landing): compose LandingView with all new sections"
```

---

## Task 12: Visual QA

- [ ] **Step 1: Start dev server**

```bash
cd frontend && npm run dev
```

Navigate to `http://localhost:5173`.

- [ ] **Step 2: Dark mode checklist**

- [ ] Page has black (`#09090b`) background
- [ ] Nav is sticky and blurs on scroll
- [ ] H1 "writing" has indigo→violet→pink gradient
- [ ] "You don't recognize words — you produce them." is visible and prominent (not muted)
- [ ] Trust signals (`open source · no tracking · self-hostable`) appear below CTAs in hero
- [ ] How It Works shows 3 columns with monospace example blocks
- [ ] Features bento renders 6 cards (wide first card spans 2 columns)
- [ ] Objection handler renders 3 equal columns with no heading
- [ ] Demo section shows browser chrome wrapper with typing animation running
- [ ] Cursor blink uses `lp-cursor-blink` animation (not `cursor-blink` from old globals)
- [ ] CTA quote has gradient text
- [ ] CTA button reads "Start your first recall session →"
- [ ] Footer bar is minimal (wordmark + year)

- [ ] **Step 3: Light mode checklist**

Click ☀ toggle in nav.

- [ ] Background switches to `#fafafa`
- [ ] All text remains readable (no white-on-white or black-on-black)
- [ ] Nav background switches to `rgba(250,250,250,0.85)`
- [ ] Theme persists on page reload (check `localStorage.getItem('lp-theme')` in devtools)

- [ ] **Step 4: Responsive check**

Resize browser to 375px width.

- [ ] Nav wraps cleanly (CTAs may overflow — acceptable for MVP)
- [ ] How It Works 3-col grid: add responsive breakpoint if columns are too narrow

  If columns are too narrow on mobile, add to `HowItWorks.tsx`:
  ```tsx
  style={{
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    background: 'var(--lp-border)',
    gap: '1px',
  }}
  ```
  Apply the same fix to `FeaturesBento.tsx` and `ObjectionHandler.tsx` grids.

- [ ] **Step 5: Final lint**

```bash
cd frontend && npm run lint
```

Expected: zero errors.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(landing): complete dark-first landing page redesign"
```
