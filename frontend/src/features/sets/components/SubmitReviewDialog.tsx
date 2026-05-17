import { useState } from 'react';
import { SendIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

interface SubmitReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetLabel: string;
  isPending: boolean;
  onSubmit: (feedback?: string) => void;
}

export function SubmitReviewDialog({
  open,
  onOpenChange,
  targetLabel,
  isPending,
  onSubmit,
}: SubmitReviewDialogProps) {
  const [feedback, setFeedback] = useState('');

  function handleSubmit() {
    onSubmit(feedback.trim() || undefined);
  }

  function handleOpenChange(v: boolean) {
    if (!isPending) {
      if (!v) setFeedback('');
      onOpenChange(v);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Submit for Community Review</DialogTitle>
          <DialogDescription>
            <strong>{targetLabel}</strong> will become visible to the community immediately.
            A moderator will review and approve or reject it.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium">Note for reviewer <span className="text-muted-foreground font-normal">(optional)</span></label>
          <Textarea
            placeholder="e.g. Verified with native speaker, source: …"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={3}
            maxLength={500}
          />
          <p className="text-xs text-muted-foreground text-right">{feedback.length}/500</p>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => handleOpenChange(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isPending}>
            <SendIcon className="size-3.5" />
            {isPending ? 'Submitting…' : 'Submit for Review'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
