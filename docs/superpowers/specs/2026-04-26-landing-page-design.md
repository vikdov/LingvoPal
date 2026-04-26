# Landing Page Redesign — Design Spec

**Date:** 2026-04-26  
**Status:** Approved  

## Goal

Replace the current warm "Editorial Atelier" landing page with a modern dark-first startup page in the style of Vercel/Supabase — while retaining LingvoPal's brand identity (oxblood + pine colors, serif type for display headings).

Light mode must be supported via a toggle in the nav.

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Default mode | Dark | Vercel/Supabase aesthetic |
| Light mode | Yes, toggle in nav | Accessibility + user preference |
| Social proof | None | MVP — no real stats yet |
| Hero layout | Centered + product below | Highest conversion pattern |
| Headline gradient | Indigo→violet→pink | Modern startup feel |
| Brand colors | Kept for interactive elements | Preserve LingvoPal identity |

## Color Tokens (Dark Mode)

These extend `src/styles/globals.css` dark mode vars. The existing warm editorial tokens stay for app UI; the landing page uses a new `[data-page="landing"]` or separate CSS layer.

| Token | Value | Usage |
|---|---|---|
| `--lp-bg` | `#09090b` | Page background (slightly warm zinc) |
| `--lp-surface` | `#18181b` | Cards, demo window |
| `--lp-surface-alt` | `#1f1f23` | Hover states, accent cards |
| `--lp-border` | `#27272a` | All borders |
| `--lp-text` | `#fafafa` | Primary text |
| `--lp-text-muted` | `#a1a1aa` | Subheadings, body |
| `--lp-text-faint` | `#52525b` | Labels, chips |
| `--lp-accent` | `#6366f1` | CTA buttons, glow, gradient anchor |
| `--lp-accent2` | `#8b5cf6` | Gradient mid |
| `--lp-brand` | `#D96374` | Logo italic, kept from design system |
| `--lp-teal` | `#78AFA7` | Bento tags, kept from design system |

Light mode swaps: bg `#fafafa`, surface `#fff`, surface-alt `#f4f4f5`, border `#e4e4e7`, text `#09090b`, muted `#71717a`.

Headline gradient: `linear-gradient(135deg, #818cf8, #a78bfa, #e879f9)` — applied via `-webkit-background-clip: text`.

## Page Sections (in order)

### 1. Sticky Nav
- Left: `LingvoPal` wordmark — body font, bold, italic accent on "Pal" in `--lp-brand`
- Right: theme toggle (☀/🌙 icon) · "Sign in" ghost button · "Start free" filled indigo button
- Background: `rgba(9,9,11,0.8)` + `backdrop-filter: blur(12px)` + bottom border
- Position: `sticky top-0 z-50`

### 2. Hero
- Layout: centered column, `min-height: 100vh` optional, `padding: 6rem 2rem 5rem`
- Background: subtle dot-grid (`background-image` linear-gradient lines at 2-3% opacity) with radial glow above heading (`rgba(99,102,241,0.22)`, `600px × 300px` ellipse)
- **Badge:** pill with `✦ Active recall · Spaced repetition`, indigo border + tint
- **H1:** `"Learn a language by writing it."` — "writing" gets the indigo→violet→pink gradient. Font size `clamp(2.5rem, 6vw, 4.5rem)`, weight 800, tracking `-0.04em`
- **Subtext:** `"No multiple choice. No guessing. You type the word from memory, in context — every time."` — `color: --lp-text-muted`, `max-width: 40ch`
- **CTAs:** `[Start practicing →]` (filled indigo, glow shadow) + `[See how it works ↓]` (ghost border)
- **Floating demo card:** browser chrome bar (3 traffic-light dots + tag label) → sentence with gap word → translation → SM-2 chips. Max-width `580px`, indigo glow box-shadow.

### 3. How It Works
- Section label: pill badge `"The method"`
- H2: `"Three steps. One habit."`
- Layout: 3-column grid separated by `1px` border lines (like a table)
- Steps:
  1. **Add your vocabulary** — import words/phrases, pair with context sentence
  2. **Practice in context** — fill the gap, type from memory, no hints
  3. **SM-2 schedules the rest** — ease + lapse history shapes next interval
- Each step: number `01/02/03` in monospace indigo, title bold, body muted
- Hover: surface highlight on each column

### 4. Features Bento Grid
- Section label: `"Features"` · H2: `"Built for how memory works."`
- 3-column × 2-row grid with `1px` gap lines, `border-radius` on outer container
- Cards:
  - **(Wide, 2-col)** Active recall — title, body, inline code showcase showing gap-fill, teal tag
  - **(1-col)** Real sentence context — subtitle, body, tag
  - **(1-col)** Adaptive SM-2 engine — subtitle, body, tag
  - **(1-col)** 6h first interval — short copy
  - **(1-col)** Any language — short copy
  - **(1-col, accent bg)** Free & self-hostable — short copy
- All cards hover to `--lp-surface-alt`

### 5. Interactive Demo
- Background: `--lp-surface` — visually distinct from adjacent sections
- Section label + H2: `"This is how every session feels."`
- Wrapper: full browser window chrome (traffic-light dots, title bar) around the existing `DemoSection` typing animation
- The existing `useDemoLoop` hook and `GapWord` component are reused as-is — only the outer shell changes
- Caption below: `"Auto-demo — try it live after signing up"` in monospace faint

### 6. CTA Footer
- Centered, `padding: 7rem 2rem`
- Radial glow below (`rgba(99,102,241,0.18)`)
- Section label pill
- H2 quote: `"A language isn't learned. It's written into you."` — "written into you" gets gradient
- Subtext: `"One sentence at a time. Start for free — no credit card needed."`
- Big CTA button: `"Open a fresh page →"` — filled indigo, strong glow
- Footnote: `"free · self-hostable · no tracking · open source"` in monospace faint

### 7. Footer Bar
- Minimal: left = `LingvoPal` wordmark, right = `© 2026`
- Border-top only, `padding: 1.5rem 2rem`

## Component Structure

All components live in `src/features/landing/`. Existing files are rewritten — no new directories.

```
src/features/landing/
  components/
    LandingNav.tsx        ← new: sticky dark nav with theme toggle
    Hero.tsx              ← rewrite
    HowItWorks.tsx        ← new section component
    FeaturesBento.tsx     ← replaces FeatureList.tsx (delete old file, create new)
    DemoSection.tsx       ← outer shell updated, useDemoLoop + GapWord kept as-is
    CallToAction.tsx      ← rewrite
    LandingFooter.tsx     ← new minimal footer bar
  hooks/
    useTheme.ts           ← new: dark/light toggle, persists to localStorage
  views/
    LandingView.tsx       ← updated to compose all new components
  styles/
    landing.css           ← new: --lp-* CSS token definitions
```

`src/components/layout/PublicLayout.tsx` is renamed to `LandingLayout.tsx`. It renders `LandingNav` + `<Outlet />` instead of the generic `Navbar`. `router.tsx` import updated accordingly — no structural routing change needed.

## Styling Rules

- All colors reference `--lp-*` CSS variables defined in `landing.css` — no hardcoded hex in components
- Tailwind utility classes used for layout/spacing where possible; arbitrary `var()` references for brand tokens
- Gradient text: `bg-clip-text text-transparent` Tailwind classes + `background-image` inline or via `landing.css`
- Glow effects: `box-shadow` with `rgba` of `--lp-accent`
- Hover states: Tailwind `hover:` modifiers, never inline style handlers
- `cn()` utility for all conditional classes

## Light Mode

Toggle stored in `localStorage` key `lp-theme`. `useTheme` hook reads on mount, applies `data-theme="light"` to the landing wrapper `<div>`. CSS vars swap via `[data-theme="light"]` selector in `landing.css`.

The existing `globals.css` dark mode is unaffected — landing page scopes its own tokens.

## Animations

- Hero glow: static (no animation — performance)
- Dot-grid bg: static
- `DemoSection` typing loop: existing `useDemoLoop` hook, unchanged
- Scroll reveals: **out of scope for v1** — add in a follow-up
- Respect `prefers-reduced-motion`: existing rule in `globals.css` covers the typing cursor blink

## What Is NOT Changed

- Backend — zero backend changes
- Auth views, app UI, practice UI — untouched
- `globals.css` design tokens — landing uses its own `--lp-*` vars, no conflict
- `PublicLayout` — landing gets its own layout wrapper; auth pages keep existing layout
