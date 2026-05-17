import { useState } from 'react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useReportItem, useReportSet } from '../hooks/useSetsQuery';
import type { ComplaintReason } from '@/features/admin/types/admin.types';

const COMPLAINT_REASONS: { value: ComplaintReason; label: string }[] = [
  { value: 'wrong_language', label: 'Wrong language' },
  { value: 'incorrect_translation', label: 'Incorrect translation' },
  { value: 'inappropriate', label: 'Inappropriate content' },
  { value: 'spam', label: 'Spam' },
  { value: 'duplicate', label: 'Duplicate' },
  { value: 'other', label: 'Other' },
];

interface ReportDialogProps {
  targetId: number;
  targetType: 'item' | 'set';
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReportDialog({ targetId, targetType, open, onOpenChange }: ReportDialogProps) {
  const [reason, setReason] = useState<ComplaintReason | ''>('');
  const [details, setDetails] = useState('');
  const reportItem = useReportItem();
  const reportSet = useReportSet();

  const isPending = reportItem.isPending || reportSet.isPending;

  function handleSubmit() {
    if (!reason) return;
    const opts = {
      onSuccess: () => {
        toast.success('Report submitted. Thank you.');
        onOpenChange(false);
        setReason('');
        setDetails('');
      },
      onError: (err: Error) => toast.error(err.message),
    };
    if (targetType === 'item') {
      reportItem.mutate({ itemId: targetId, reason, details: details.trim() || undefined }, opts);
    } else {
      reportSet.mutate({ setId: targetId, reason, details: details.trim() || undefined }, opts);
    }
  }

  function handleOpenChange(v: boolean) {
    if (!v) { setReason(''); setDetails(''); }
    onOpenChange(v);
  }

  const label = targetType === 'item' ? 'expression' : 'set';

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Report this {label}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <Select value={reason} onValueChange={(v) => setReason(v as ComplaintReason)}>
            <SelectTrigger>
              <SelectValue placeholder="Select a reason…" />
            </SelectTrigger>
            <SelectContent>
              {COMPLAINT_REASONS.map((r) => (
                <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Textarea
            placeholder="Additional details (optional)"
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            rows={3}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleSubmit}
            disabled={!reason || isPending}
          >
            {isPending ? 'Submitting…' : 'Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
