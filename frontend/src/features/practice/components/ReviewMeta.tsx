import { formatRelativeTime } from '../utils/formatReviewTime';

interface ReviewMetaProps {
  lastReviewed: string | null;
  estimatedNext: Date | null;
  answered: boolean;
}

export function ReviewMeta({ lastReviewed, estimatedNext, answered }: ReviewMetaProps) {
  let label: string;

  if (answered && estimatedNext) {
    label = formatRelativeTime(estimatedNext, true);
  } else if (lastReviewed) {
    label = formatRelativeTime(lastReviewed, false);
  } else {
    label = 'new';
  }

  return (
    <span className="text-sm text-muted-foreground select-none">
      {label}
    </span>
  );
}
