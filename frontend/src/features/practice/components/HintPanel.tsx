import type { ItemHint, ComparisonConfig, AnswerLifecycle } from '../types/practice.types';

interface HintPanelProps {
  item: ItemHint;
  config: ComparisonConfig;
  lifecycle: AnswerLifecycle;
  posColorClass?: string;
}

const MARKER_RE = /\{(.+?)\}/;

function renderContextTrans(text: string, colorClass: string) {
  const match = MARKER_RE.exec(text);
  if (!match) return <>{text}</>;
  return (
    <>
      {text.slice(0, match.index)}
      <span className={colorClass}>{match[1]}</span>
      {text.slice(match.index + match[0].length)}
    </>
  );
}

export function HintPanel({ item, config, lifecycle, posColorClass }: HintPanelProps) {
  const unanswered = lifecycle === 'unanswered';
  const retrying = lifecycle === 'retrying';
  const correct = lifecycle === 'correct' || lifecycle === 'corrected';
  const color = posColorClass ?? 'text-muted-foreground';

  if (unanswered || (retrying && config.show_hints_on_fails)) {
    const hasSynonyms = config.show_synonyms && item.synonyms.length > 0;
    const hasTranslation = config.show_translations && item.prompt;

    if (!hasSynonyms && !hasTranslation) return null;

    return (
      <div className="flex flex-col items-center gap-1.5">
        {hasTranslation && (
          <p className={`text-base font-semibold ${color}`}>{item.prompt}</p>
        )}
        {hasSynonyms && (
          <p className="text-sm font-semibold text-navy">
            ( {item.synonyms.slice(0, 3).join(', ')} )
          </p>
        )}
      </div>
    );
  }

  if (correct && item.context_trans) {
    return (
      <p className="text-sm font-semibold text-muted-foreground text-center max-w-sm">
        {renderContextTrans(item.context_trans, color)}
      </p>
    );
  }

  return null;
}
