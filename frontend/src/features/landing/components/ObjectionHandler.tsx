import { BentoHoverItem } from '@/components/ui/cybernetic-bento-grid';
import { FadeUp } from '@/components/ui/animate';

const OBJECTIONS = [
  {
    question: "I'm a beginner — is this too hard?",
    answer:
      "Sentences provide full context. You're not guessing a word in isolation — the surrounding sentence gives you the clue. AI can generate beginner-appropriate examples automatically.",
  },
  {
    question: 'Can I use my own vocabulary?',
    answer:
      "Yes. Build sets from your own words, import an Anki deck, or clone a community set and edit it freely.",
  },
  {
    question: "Isn't it just harder Anki?",
    answer:
      'Similar scheduling, completely different input. Anki asks you to rate how well you remember. LingvoPal asks you to prove it — by typing the word.',
  },
] as const;

export function ObjectionHandler() {
  return (
    <section className="px-6 py-10 border-t border-border">
      <FadeUp>
      <div
        className="w-full max-w-[900px] mx-auto rounded-xl overflow-hidden border border-border"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          background: 'var(--border)',
          gap: '1px',
        }}
      >
        {OBJECTIONS.map((o) => (
          <BentoHoverItem
            key={o.question}
            className="flex flex-col gap-2 p-6 bg-card"
          >
            <p className="font-semibold text-[0.875rem] text-foreground leading-snug">
              "{o.question}"
            </p>
            <p className="text-[0.8125rem] text-muted-foreground leading-relaxed">
              {o.answer}
            </p>
          </BentoHoverItem>
        ))}
      </div>
      </FadeUp>
    </section>
  );
}
