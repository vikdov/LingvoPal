import { Badge } from '@/components/ui/badge';
import { BentoItem } from '@/components/ui/cybernetic-bento-grid';
import { ShieldCheckIcon, UsersIcon, BookOpenIcon } from 'lucide-react';
import { FadeUp, StaggerGroup, StaggerItem } from '@/components/ui/animate';

const CARDS = [
  {
    icon: BookOpenIcon,
    title: 'Curated sets',
    body: 'Official vocabulary sets for Italian, French, German, and more — built around grammar topics and frequency lists.',
    tag: 'official',
  },
  {
    icon: UsersIcon,
    title: 'Community sets',
    body: 'Learners publish their own sets. Clone any set and personalize it with your own sentences and context.',
    tag: 'community',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Reviewed content',
    body: 'Public sets go through moderation before appearing in discovery. Quality over quantity.',
    tag: 'moderated',
  },
];

export function CommunitySection() {
  return (
    <section className="flex flex-col items-center gap-10 px-6 py-20 border-t border-border">
      <FadeUp>
        <div className="flex flex-col items-center gap-3 text-center">
          <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground gap-1.5 border-border">
            <span className="inline-block w-[5px] h-[5px] rounded-full bg-primary shrink-0" /> Content
          </Badge>
          <h2
            className="font-bold tracking-[-0.03em] text-foreground"
            style={{ fontSize: 'clamp(1.5rem, 2.5vw, 1.875rem)' }}
          >
            Start with what's already there.
          </h2>
          <p className="text-[0.9375rem] text-muted-foreground max-w-[40ch] leading-relaxed">
            Curated sets to get you started. Community sets to keep you going. Your own sets for what matters to you.
          </p>
        </div>
      </FadeUp>

      <StaggerGroup className="w-full max-w-[860px] grid grid-cols-1 md:grid-cols-3 gap-4" delayChildren={0.1}>
        {CARDS.map(({ icon: Icon, title, body, tag }) => (
          <StaggerItem key={title}>
            <BentoItem className="flex flex-col gap-3 h-full">
              <div className="flex items-start justify-between gap-2">
                <Icon className="size-4 text-primary mt-0.5" />
                <Badge
                  variant="outline"
                  className="font-mono text-[9px] tracking-widest uppercase text-muted-foreground border-border rounded-sm"
                >
                  {tag}
                </Badge>
              </div>
              <h3 className="text-[0.9375rem] font-semibold tracking-[-0.02em] text-foreground">
                {title}
              </h3>
              <p className="text-[0.8125rem] text-muted-foreground leading-relaxed">{body}</p>
            </BentoItem>
          </StaggerItem>
        ))}
      </StaggerGroup>
    </section>
  );
}
