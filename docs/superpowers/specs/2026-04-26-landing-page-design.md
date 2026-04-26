# Landing Page Redesign — Design Spec

**Date:** 2026-04-26  
**Status:** Approved (rev 2)

## Goal

Replace the current warm "Editorial Atelier" landing page with a modern dark-first startup page in the style of Vercel/Supabase — while retaining LingvoPal's brand identity (oxblood + pine colors, serif type for display headings).

Light mode supported via toggle in nav.

The page must communicate not just features but **the learning method** — users compare LingvoPal against Duolingo, Anki, Memrise. If the page doesn't define the difference, they assume it's the same. Every section should reinforce: *you produce words, you don't just recognize them.*

## Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Default mode | Dark | Vercel/Supabase aesthetic |
| Light mode | Yes, toggle in nav | Accessibility + user preference |
| Social proof | None | MVP — no real stats yet |
| Hero layout | Centered + product below | Highest conversion pattern |
| Headline gradient | Indigo→violet→pink | Modern startup feel |
| Brand colors | Kept for interactive elements | Preserve LingvoPal identity |
| Positioning angle | Method-first, not feature-first | Differentiates from other apps |

## Color Tokens (Dark Mode)

These extend `src/styles/globals.css` dark mode vars. The existing warm editorial tokens stay for app UI; the landing page uses a separate `landing.css` scoped to `[data-lp]` attribute on the landing wrapper.

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
- Right: theme toggle (☀/🌙 icon) · "Sign in" ghost button · "Write your first sentence →" filled indigo button
- Background: `rgba(9,9,11,0.8)` + `backdrop-filter: blur(12px)` + bottom border
- Position: `sticky top-0 z-50`
- Trust bar: below nav or embedded in hero — `"open source · no tracking · self-hostable"` in monospace faint. Visible early, not just in footer.

### 2. Hero
- Layout: centered column, `padding: 6rem 2rem 5rem`
- Background: subtle dot-grid (`background-image` linear-gradient lines at 2-3% opacity) with radial glow above heading (`rgba(99,102,241,0.22)`, `600px × 300px` ellipse)
- **"Who it's for" eyebrow:** above the badge — `"For learners who want to actually remember, not just recognize."` in monospace faint. Sets expectation for the right audience immediately.
- **Badge:** pill with `✦ Active recall · Spaced repetition`, indigo border + tint
- **H1:** `"Learn a language by writing it."` — "writing" gets the indigo→violet→pink gradient. Font size `clamp(2.5rem, 6vw, 4.5rem)`, weight 800, tracking `-0.04em`
- **Differentiator line:** immediately below H1, visually distinct (larger body text, not muted):
  > `"You don't recognize words — you produce them."`
  
  This is the single clearest contrast vs Duolingo/Anki. It must be prominent, not buried.
- **Subtext:** `"No multiple choice. No guessing. Type the word from memory, in context — every time."` — `color: --lp-text-muted`, `max-width: 40ch`
- **Difficulty honesty line** (small, below subtext): `"It's harder than tapping pictures. That's exactly why it works."` — `--lp-text-faint`, italic, monospace
- **CTAs:** `[Write your first sentence →]` (filled indigo, glow shadow) + `[See how it works ↓]` (ghost border)
- **Trust signals** (below CTAs, inline row): `"open source"` · `"no tracking"` · `"self-hostable"` in monospace faint with `·` separators — surfaces credibility before the user scrolls
- **Floating demo card:** browser chrome bar (3 traffic-light dots + tag label) → sentence with gap word → translation → SM-2 chips. Max-width `580px`, indigo glow box-shadow.

### 3. How It Works
- Section label: pill badge `"The method"`
- H2: `"Three steps. One habit."`
- Layout: 3-column grid separated by `1px` border lines
- Each step includes a **real example** — not just description. Makes it feel like usage preview, not documentation:

  **01 — Add your vocabulary**
  - Body: "Import a word, phrase, or conjugation. Pair it with a real sentence."
  - Example block (monospace, surface bg):
    ```
    gehen → Ich gehe jeden Tag zur Arbeit.
    ```

  **02 — Practice in context**
  - Body: "Fill the gap. Type from memory, letter by letter. No hints. No word bank."
  - Example block showing the gap-fill interaction:
    ```
    Ich ___ jeden Tag zur Arbeit.
    You type: gehe
    ```

  **03 — SM-2 schedules the rest**
  - Body: "Your ease and lapse history shape when you see it again. Optimal spacing, automatic."
  - Example block showing interval progression:
    ```
    6h → 1d → 3d → 9d → …
    ```

- Each step: number in monospace indigo, title bold, body muted, example in surface-card with border
- Hover: surface highlight per column

### 4. Features Bento Grid
- Section label: `"Features"` · H2: `"Built for how memory works."`
- Copy rule: **feature → user outcome** — never name the mechanism without the benefit
- 3-column × 2-row grid with `1px` gap lines

Cards (titles reframed as outcomes):

| Size | Title | Body |
|---|---|---|
| Wide (2-col) | **You produce words — you don't just recognize them** | Every session asks you to type the word from memory, in the exact form it appears in speech. No word bank. No multiple choice. This is why it sticks. Inline gap-fill code example. |
| 1-col | **Words live inside real sentences** | Not flashcards in isolation — an imperfetto in a memoir, a subjunctive in a letter. Context makes recall 3× more likely. |
| 1-col | **You review right before you forget** | SM-2 tracks your ease, pace, and lapse history and schedules the exact moment to review for maximum retention. |
| 1-col | **Your first review comes today** | New words get a 6-hour first interval — not the next day — so they anchor before they fade. |
| 1-col | **Any language, your vocabulary** | Build sets from your own words or import existing decks. Italian, French, German, Japanese — whatever you're learning. |
| 1-col (accent bg) | **Free. Open source. Self-hostable.** | No subscription. Run it on your own server. Your data stays yours. |

### 5. Objection Handler
A lean 3-card row between the bento and demo sections. Addresses the most common reasons users hesitate silently. No heading needed — just three short punchy callouts.

| Callout | Response |
|---|---|
| "I'm a beginner — is this too hard?" | "Sentences provide full context. You're not guessing a word in isolation — the surrounding sentence gives you the clue." |
| "Can I use my own vocabulary?" | "Yes. Build sets from your own words, your textbook, or your teacher's list. Or import an existing deck." |
| "Isn't it just harder Anki?" | "Similar scheduling, completely different input method. Anki asks you to rate how well you remember. LingvoPal asks you to prove it." |

Layout: 3 equal columns, bordered cards, no icons — plain text, tight padding. The directness is the design.

### 6. Interactive Demo
- Background: `--lp-surface` — visually distinct from adjacent sections
- Section label + H2: **`"This is the entire learning loop."`** (upgraded from "how every session feels")
- Subtext: `"This is exactly what you'll do every day."` — makes it explicit this is usage preview, not marketing
- Wrapper: full browser window chrome (traffic-light dots + title bar) around existing `DemoSection` typing animation
- The existing `useDemoLoop` hook and `GapWord` component are reused as-is — only outer shell changes
- Caption: `"Auto-demo — try it live after signing up"` in monospace faint

### 7. CTA Footer
- Centered, `padding: 7rem 2rem`
- Radial glow below (`rgba(99,102,241,0.18)`)
- Section label pill
- H2 quote: `"A language isn't learned. It's written into you."` — "written into you" gets gradient
- Subtext: `"One sentence at a time. No credit card. No commitment."`
- Big CTA: **`"Start your first recall session →"`** — filled indigo, strong glow. Action-specific, not generic.
- Footnote: `"free · self-hostable · no tracking · open source"` in monospace faint

### 8. Footer Bar
- Minimal: left = `LingvoPal` wordmark, right = `© 2026`
- Border-top only, `padding: 1.5rem 2rem`

## Component Structure

All components live in `src/features/landing/`. Existing files are rewritten — no new directories.

```
src/features/landing/
  components/
    LandingNav.tsx        ← new: sticky dark nav with theme toggle
    Hero.tsx              ← rewrite
    HowItWorks.tsx        ← new section with real examples
    FeaturesBento.tsx     ← replaces FeatureList.tsx (delete old, create new)
    ObjectionHandler.tsx  ← new: 3-card objection row
    DemoSection.tsx       ← outer shell updated, useDemoLoop + GapWord kept as-is
    CallToAction.tsx      ← rewrite
    LandingFooter.tsx     ← new minimal footer bar
  hooks/
    useTheme.ts           ← new: dark/light toggle, persists to localStorage
  views/
    LandingView.tsx       ← updated to compose all new components
  styles/
    landing.css           ← new: --lp-* CSS token definitions, scoped to [data-lp]
```

`src/components/layout/PublicLayout.tsx` is renamed to `LandingLayout.tsx`. It renders `LandingNav` + `<Outlet />` instead of the generic `Navbar`. `router.tsx` import updated accordingly — no structural routing change needed.

## Copy Rules (enforce throughout)

1. **Feature → outcome:** never name a mechanism without the user benefit it produces
2. **Produce, not recognize:** every section reinforces this single differentiator
3. **Honesty over hype:** difficulty is a selling point — don't hide it
4. **Action-specific CTAs:** buttons say what the first action IS, not what the app IS

## Styling Rules

- All colors reference `--lp-*` CSS variables defined in `landing.css` — no hardcoded hex in components
- Tailwind utility classes for layout/spacing; arbitrary `var()` references for brand tokens
- Gradient text: `bg-clip-text text-transparent` Tailwind classes + `background-image` in `landing.css`
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
- `PublicLayout` → renamed to `LandingLayout`; auth pages keep `AuthLayout` as-is
