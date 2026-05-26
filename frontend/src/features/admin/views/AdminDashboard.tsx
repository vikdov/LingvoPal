import { useRef, useState } from 'react';
import { toast } from 'sonner';
import {
  CheckIcon,
  XIcon,
  StarIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  LayersIcon,
  ClockIcon,
  FlagIcon,
  ArrowRightIcon,
  Trash2Icon,
  MessageSquareIcon,
  UploadIcon,
  DownloadIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useAdminOverview,
  useModerationQueue,
  useApprove,
  useReject,
  usePromotionCandidates,
  usePromoteToOfficial,
  useAdminComplaints,
  useAuditLog,
  useDismissComplaint,
  useDeleteContent,
  useOfficialSets,
  useImportOfficialSet,
  useExportSet,
} from '../hooks/useAdmin';
import type {
  PendingModerationEntry,
  ModerationStatus,
  ModerationTargetType,
  PromotionCandidateItem,
  ComplaintResponse,
  ComplaintReason,
  AuditLogEntry,
  OfficialSetEntry,
} from '../types/admin.types';

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_BADGE: Record<ModerationStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  pending: 'secondary',
  approved: 'default',
  rejected: 'destructive',
};

const REASON_LABELS: Record<ComplaintReason, string> = {
  wrong_language: 'Wrong language',
  incorrect_translation: 'Incorrect translation',
  inappropriate: 'Inappropriate',
  spam: 'Spam',
  duplicate: 'Duplicate',
  other: 'Other',
};

function fmt(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

function fmtDatetime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function pct(n: number) {
  return `${(n * 100).toFixed(0)}%`;
}

// ── Overview tab ──────────────────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, description }: {
  label: string;
  value: number | string | undefined;
  icon: React.ElementType;
  description?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardDescription>{label}</CardDescription>
          <Icon className="size-4 text-muted-foreground" />
        </div>
        <CardTitle className="text-3xl tabular-nums">
          {value ?? <Skeleton className="h-9 w-16" />}
        </CardTitle>
      </CardHeader>
      {description && (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">{description}</p>
        </CardContent>
      )}
    </Card>
  );
}

function OverviewTab() {
  const { data, isLoading } = useAdminOverview();

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Community items"
          value={isLoading ? undefined : data?.community_count}
          icon={LayersIcon}
          description="Publicly visible, awaiting admin review"
        />
        <StatCard
          label="Pending queue"
          value={isLoading ? undefined : data?.pending_queue_count}
          icon={ClockIcon}
          description="Moderation submissions awaiting action"
        />
        <StatCard
          label="Total complaints"
          value={isLoading ? undefined : data?.total_complaints}
          icon={FlagIcon}
          description="Cumulative reports filed by users"
        />
      </div>
    </div>
  );
}

// ── Reject dialog ─────────────────────────────────────────────────────────────

interface RejectDialogProps {
  entry: PendingModerationEntry;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function RejectDialog({ entry, open, onOpenChange }: RejectDialogProps) {
  const [feedback, setFeedback] = useState('');
  const reject = useReject();

  function handleReject() {
    if (!feedback.trim()) return;
    reject.mutate(
      { id: entry.id, feedback: feedback.trim() },
      {
        onSuccess: () => {
          toast.success('Submission rejected.');
          onOpenChange(false);
          setFeedback('');
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reject submission</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <p className="text-sm text-muted-foreground">
            Rejection reason is shown to the creator. Be specific.
          </p>
          <Textarea
            placeholder="Rejection reason (required)…"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
            autoFocus
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={reject.isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleReject}
            disabled={!feedback.trim() || reject.isPending}
          >
            {reject.isPending ? 'Rejecting…' : 'Reject'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Approve dialog (with optional feedback) ───────────────────────────────────

interface ApproveDialogProps {
  entry: PendingModerationEntry;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ApproveDialog({ entry, open, onOpenChange }: ApproveDialogProps) {
  const [feedback, setFeedback] = useState('');
  const approve = useApprove();

  function handleApprove() {
    approve.mutate(
      { id: entry.id, feedback: feedback.trim() || undefined },
      {
        onSuccess: () => {
          toast.success('Approved.');
          onOpenChange(false);
          setFeedback('');
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Approve submission</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <p className="text-sm text-muted-foreground">
            Content will become publicly visible. Optionally leave a note for the creator.
          </p>
          <Textarea
            placeholder="Approval note (optional)…"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={3}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={approve.isPending}>
            Cancel
          </Button>
          <Button onClick={handleApprove} disabled={approve.isPending}>
            <CheckIcon className="size-3.5" />
            {approve.isPending ? 'Approving…' : 'Approve'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Delete content dialog ─────────────────────────────────────────────────────

interface DeleteContentDialogProps {
  entry: PendingModerationEntry;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function DeleteContentDialog({ entry, open, onOpenChange }: DeleteContentDialogProps) {
  const [reason, setReason] = useState('');
  const deleteContent = useDeleteContent();

  const targetType = entry.target_type === 'item' || entry.target_type === 'set'
    ? entry.target_type
    : null;

  function handleDelete() {
    if (!reason.trim() || !targetType) return;
    deleteContent.mutate(
      { targetType, id: entry.target_id, reason: reason.trim() },
      {
        onSuccess: () => {
          toast.success(`${entry.target_type} #${entry.target_id} deleted.`);
          onOpenChange(false);
          setReason('');
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-destructive">
            Delete {entry.target_type} #{entry.target_id}
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <p className="text-sm text-muted-foreground">
            This permanently removes the content. The creator will see your reason.
            Any pending moderation entry is auto-rejected.
          </p>
          <Textarea
            placeholder="Removal reason (required)…"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            autoFocus
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={deleteContent.isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={!reason.trim() || !targetType || deleteContent.isPending}
          >
            <Trash2Icon className="size-3.5" />
            {deleteContent.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Moderation entry card ─────────────────────────────────────────────────────

interface ModerationEntryCardProps {
  entry: PendingModerationEntry;
}

function ModerationEntryCard({ entry }: ModerationEntryCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const qm = entry.quality_metrics;
  const canDelete = entry.target_type === 'item' || entry.target_type === 'set';

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="uppercase text-xs font-mono">
                {entry.target_type} #{entry.target_id}
              </Badge>
              <Badge variant={STATUS_BADGE[entry.status]}>{entry.status}</Badge>
              {entry.complaint_count > 0 && (
                <Badge variant="destructive" className="gap-1">
                  <FlagIcon className="size-3" />
                  {entry.complaint_count}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground">{fmt(entry.created_at)}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="shrink-0 h-7 w-7 p-0"
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? <ChevronUpIcon className="size-4" /> : <ChevronDownIcon className="size-4" />}
            </Button>
          </div>

          {entry.feedback && (
            <CardDescription className="mt-1 italic">
              &ldquo;{entry.feedback}&rdquo;
            </CardDescription>
          )}
        </CardHeader>

        {/* Quality metrics row */}
        {qm && (
          <CardContent className="py-0 pb-2">
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span>
                <span className="font-medium text-foreground">{pct(qm.global_success_rate)}</span>
                {' '}success rate
              </span>
              <span>
                <span className="font-medium text-foreground">{qm.learner_count}</span>
                {' '}learners
              </span>
              <span>
                <span className="font-medium text-foreground">{qm.avg_interval.toFixed(1)}d</span>
                {' '}avg interval
              </span>
              <span>
                <span className="font-medium text-foreground">{qm.sample_size}</span>
                {' '}reviews
              </span>
            </div>
          </CardContent>
        )}

        {/* Expandable patch data */}
        {expanded && (
          <CardContent className="pt-0">
            <Separator className="mb-3" />
            <div className="rounded-md bg-muted p-3 text-xs font-mono space-y-1">
              {Object.entries(entry.patch_data).map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-muted-foreground min-w-[110px] shrink-0">{k}:</span>
                  <span className="break-all">{String(v)}</span>
                </div>
              ))}
            </div>
            {entry.resolution_feedback && (
              <p className="mt-2 text-xs text-muted-foreground">
                <MessageSquareIcon className="inline size-3 mr-1" />
                {entry.resolution_feedback}
              </p>
            )}
          </CardContent>
        )}

        <CardFooter className="gap-2 pt-2 flex-wrap">
          {entry.status === 'pending' && (
            <>
              <Button size="sm" onClick={() => setApproveOpen(true)}>
                <CheckIcon className="size-3.5" />
                Approve
              </Button>
              <Button size="sm" variant="outline" onClick={() => setRejectOpen(true)}>
                <XIcon className="size-3.5" />
                Reject
              </Button>
            </>
          )}
          {canDelete && (
            <Button
              size="sm"
              variant="ghost"
              className="ml-auto text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2Icon className="size-3.5" />
              Delete content
            </Button>
          )}
        </CardFooter>
      </Card>

      <ApproveDialog entry={entry} open={approveOpen} onOpenChange={setApproveOpen} />
      <RejectDialog entry={entry} open={rejectOpen} onOpenChange={setRejectOpen} />
      <DeleteContentDialog entry={entry} open={deleteOpen} onOpenChange={setDeleteOpen} />
    </>
  );
}

// ── Moderation queue tab ──────────────────────────────────────────────────────

function ModerationQueueTab() {
  const [targetType, setTargetType] = useState<ModerationTargetType | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<ModerationStatus | 'all'>('pending');

  const params = {
    target_type: targetType !== 'all' ? (targetType as ModerationTargetType) : undefined,
    status: statusFilter !== 'all' ? (statusFilter as ModerationStatus) : undefined,
    limit: 50,
  };

  const { data, isLoading, isError, error } = useModerationQueue(params);
  const entries = data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={targetType} onValueChange={(v) => setTargetType(v as typeof targetType)}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="item">Items</SelectItem>
            <SelectItem value="set">Sets</SelectItem>
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>

        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} {data.total === 1 ? 'entry' : 'entries'}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)}
        </div>
      )}

      {isError && <p className="text-sm text-destructive">{error.message}</p>}

      {!isLoading && !isError && entries.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No submissions match these filters.
        </p>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <div className="flex flex-col gap-3">
          {entries.map((e) => <ModerationEntryCard key={e.id} entry={e} />)}
        </div>
      )}
    </div>
  );
}

// ── Complaints tab ────────────────────────────────────────────────────────────

function ComplaintRow({ complaint }: { complaint: ComplaintResponse }) {
  const dismiss = useDismissComplaint();

  return (
    <TableRow>
      <TableCell className="font-mono text-xs">
        <Badge variant="outline" className="uppercase">
          {complaint.target_type}
        </Badge>
        <span className="ml-2 text-muted-foreground">#{complaint.target_id}</span>
      </TableCell>
      <TableCell>
        <Badge variant="secondary" className="text-xs">
          {REASON_LABELS[complaint.reason]}
        </Badge>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
        {complaint.details ?? '—'}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
        user #{complaint.reporter_id}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
        {fmt(complaint.created_at)}
      </TableCell>
      <TableCell>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
          disabled={dismiss.isPending}
          onClick={() =>
            dismiss.mutate(complaint.id, {
              onSuccess: () => toast.success('Complaint dismissed.'),
              onError: (err) => toast.error(err.message),
            })
          }
        >
          <XIcon className="size-3.5" />
          Dismiss
        </Button>
      </TableCell>
    </TableRow>
  );
}

function ComplaintsTab() {
  const [targetType, setTargetType] = useState<ModerationTargetType | 'all'>('all');

  const params = {
    target_type: targetType !== 'all' ? (targetType as ModerationTargetType) : undefined,
    limit: 50,
  };

  const { data, isLoading, isError, error } = useAdminComplaints(params);
  const complaints = data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={targetType} onValueChange={(v) => setTargetType(v as typeof targetType)}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="item">Items</SelectItem>
            <SelectItem value="set">Sets</SelectItem>
          </SelectContent>
        </Select>

        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} {data.total === 1 ? 'complaint' : 'complaints'}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
        </div>
      )}

      {isError && <p className="text-sm text-destructive">{error.message}</p>}

      {!isLoading && !isError && complaints.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">No complaints filed.</p>
      )}

      {!isLoading && !isError && complaints.length > 0 && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Target</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Reporter</TableHead>
                <TableHead>Date</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {complaints.map((c) => <ComplaintRow key={c.id} complaint={c} />)}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ── Promotion tab ─────────────────────────────────────────────────────────────

interface PromoteDialogProps {
  item: PromotionCandidateItem;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function PromoteDialog({ item, open, onOpenChange }: PromoteDialogProps) {
  const [override, setOverride] = useState(false);
  const promote = usePromoteToOfficial();

  function handlePromote() {
    promote.mutate(
      { itemId: item.id, override },
      {
        onSuccess: () => {
          toast.success(`"${item.term}" promoted to Official.`);
          onOpenChange(false);
          setOverride(false);
        },
        onError: (err) => {
          if (err.message.toLowerCase().includes('threshold')) {
            setOverride(true);
            toast.error('Below quality threshold. Enable override to promote anyway.');
          } else {
            toast.error(err.message);
          }
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Promote to Official</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3 py-1">
          <p className="text-sm text-muted-foreground">
            Promote <strong>&ldquo;{item.term}&rdquo;</strong> to the Official tier.
          </p>
          {override && (
            <p className="rounded-md bg-amber-50 p-2 text-sm text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
              Quality thresholds not met. Promoting with admin override.
            </p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={promote.isPending}>
            Cancel
          </Button>
          <Button onClick={handlePromote} disabled={promote.isPending}>
            {promote.isPending ? 'Promoting…' : override ? 'Promote (override)' : 'Promote'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PromotionCandidateCard({ item }: { item: PromotionCandidateItem }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-base">{item.term}</CardTitle>
            <Badge variant="outline" className="shrink-0 font-mono text-xs">#{item.id}</Badge>
          </div>
          {item.context && (
            <CardDescription className="line-clamp-1 italic">
              &ldquo;{item.context}&rdquo;
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 pb-2 pt-0">
          {item.part_of_speech && (
            <Badge variant="outline" className="text-xs">{item.part_of_speech}</Badge>
          )}
          <Badge variant="default" className="text-xs capitalize">{item.status}</Badge>
        </CardContent>
        <CardFooter className="pt-2">
          <Button size="sm" onClick={() => setOpen(true)}>
            <StarIcon className="size-3.5" />
            Promote to Official
          </Button>
        </CardFooter>
      </Card>
      <PromoteDialog item={item} open={open} onOpenChange={setOpen} />
    </>
  );
}

function PromotionTab() {
  const { data: candidates, isLoading, isError, error } = usePromotionCandidates();

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Approved items meeting Official thresholds — ≥20 learners, ≥70% success rate.
      </p>

      {isLoading && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-36 rounded-lg" />)}
        </div>
      )}

      {isError && <p className="text-sm text-destructive">{error.message}</p>}

      {!isLoading && !isError && (!candidates || candidates.length === 0) && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No items currently meet the Official promotion thresholds.
        </p>
      )}

      {!isLoading && !isError && candidates && candidates.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {candidates.map((item) => <PromotionCandidateCard key={item.id} item={item} />)}
        </div>
      )}
    </div>
  );
}

// ── Audit log tab ─────────────────────────────────────────────────────────────

const ACTION_BADGE: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  INSERT: 'default',
  UPDATE: 'secondary',
  DELETE: 'destructive',
};

function AuditLogRow({ entry }: { entry: AuditLogEntry }) {
  const [expanded, setExpanded] = useState(false);

  const hasChanges = entry.old_values || entry.new_values;

  return (
    <>
      <TableRow
        className={hasChanges ? 'cursor-pointer hover:bg-muted/50' : ''}
        onClick={() => hasChanges && setExpanded((v) => !v)}
      >
        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
          {fmtDatetime(entry.created_at)}
        </TableCell>
        <TableCell>
          <Badge variant={ACTION_BADGE[entry.action] ?? 'outline'} className="text-xs">
            {entry.action}
          </Badge>
        </TableCell>
        <TableCell className="font-mono text-xs">
          {entry.table_name}
          <span className="text-muted-foreground ml-1">#{entry.record_id}</span>
        </TableCell>
        <TableCell className="text-xs text-muted-foreground">
          {entry.user_id ? `user #${entry.user_id}` : '—'}
        </TableCell>
        {hasChanges && (
          <TableCell className="text-xs text-muted-foreground">
            {expanded ? <ChevronUpIcon className="size-3.5" /> : <ChevronDownIcon className="size-3.5" />}
          </TableCell>
        )}
        {!hasChanges && <TableCell />}
      </TableRow>

      {expanded && hasChanges && (
        <TableRow>
          <TableCell colSpan={5} className="bg-muted/30 py-2">
            <div className="flex gap-6 text-xs font-mono px-2">
              {entry.old_values && (
                <div className="flex-1">
                  <p className="mb-1 font-sans text-muted-foreground font-medium">Before</p>
                  {Object.entries(entry.old_values).map(([k, v]) => (
                    <div key={k} className="flex gap-2">
                      <span className="text-muted-foreground min-w-[80px]">{k}:</span>
                      <span className="text-destructive">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
              {entry.old_values && entry.new_values && (
                <ArrowRightIcon className="size-4 text-muted-foreground self-center shrink-0" />
              )}
              {entry.new_values && (
                <div className="flex-1">
                  <p className="mb-1 font-sans text-muted-foreground font-medium">After</p>
                  {Object.entries(entry.new_values).map(([k, v]) => (
                    <div key={k} className="flex gap-2">
                      <span className="text-muted-foreground min-w-[80px]">{k}:</span>
                      <span className="text-green-600 dark:text-green-400">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function AuditLogTab() {
  const [tableFilter, setTableFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('all');

  const params = {
    table_name: tableFilter || undefined,
    action: actionFilter !== 'all' ? actionFilter : undefined,
    limit: 100,
  };

  const { data, isLoading, isError, error } = useAuditLog(params);
  const entries = data?.data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All actions</SelectItem>
            <SelectItem value="INSERT">INSERT</SelectItem>
            <SelectItem value="UPDATE">UPDATE</SelectItem>
            <SelectItem value="DELETE">DELETE</SelectItem>
          </SelectContent>
        </Select>

        <Select value={tableFilter || 'all'} onValueChange={(v) => setTableFilter(v === 'all' ? '' : v)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All tables</SelectItem>
            <SelectItem value="items">items</SelectItem>
            <SelectItem value="sets">sets</SelectItem>
          </SelectContent>
        </Select>

        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} {data.total === 1 ? 'entry' : 'entries'}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
        </div>
      )}

      {isError && <p className="text-sm text-destructive">{error.message}</p>}

      {!isLoading && !isError && entries.length === 0 && (
        <p className="py-8 text-center text-sm text-muted-foreground">No audit log entries.</p>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>By</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((e) => <AuditLogRow key={e.id} entry={e} />)}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ── Official Sets tab ─────────────────────────────────────────────────────────

function OfficialSetRow({ set }: { set: OfficialSetEntry }) {
  const exportSet = useExportSet();

  return (
    <TableRow>
      <TableCell className="font-medium">{set.title}</TableCell>
      <TableCell className="text-sm text-muted-foreground font-mono">
        {set.source_lang_id}
        {set.target_lang_id ? ` → ${set.target_lang_id}` : ''}
      </TableCell>
      <TableCell className="text-sm tabular-nums">{set.item_count}</TableCell>
      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
        {fmt(set.created_at)}
      </TableCell>
      <TableCell>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-xs"
          disabled={exportSet.isPending}
          onClick={() =>
            exportSet.mutate(
              { setId: set.id, title: set.title },
              { onError: (err) => toast.error(err.message) },
            )
          }
        >
          <DownloadIcon className="size-3.5" />
          Export
        </Button>
      </TableCell>
    </TableRow>
  );
}

function OfficialSetsTab() {
  const { data: sets, isLoading, isError, error } = useOfficialSets();
  const importSet = useImportOfficialSet();
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    importSet.mutate(file, {
      onSuccess: (result) => {
        toast.success(
          `"${result.title}" imported — ${result.item_count} new items, ${result.skipped_count} reused.`,
        );
      },
      onError: (err) => toast.error(err.message),
    });
    e.target.value = '';
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {sets ? `${sets.length} official set${sets.length === 1 ? '' : 's'}` : ''}
        </p>
        <Button
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={importSet.isPending}
        >
          <UploadIcon className="size-3.5" />
          {importSet.isPending ? 'Importing…' : 'Import .lpset'}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".lpset"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      )}

      {isError && <p className="text-sm text-destructive">{error.message}</p>}

      {!isLoading && !isError && (!sets || sets.length === 0) && (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No official sets. Import a .lpset bundle to get started.
        </p>
      )}

      {!isLoading && !isError && sets && sets.length > 0 && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Languages</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Created</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sets.map((s) => (
                <OfficialSetRow key={s.id} set={s} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export function AdminDashboard() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Admin</h1>
        <p className="text-sm text-muted-foreground">
          Content moderation, complaint management, and quality promotion.
        </p>
      </div>

      <Tabs defaultValue="overview">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="queue">Moderation Queue</TabsTrigger>
          <TabsTrigger value="complaints">Complaints</TabsTrigger>
          <TabsTrigger value="promotion">Promotion</TabsTrigger>
          <TabsTrigger value="official">Official Sets</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="queue" className="mt-4">
          <ModerationQueueTab />
        </TabsContent>

        <TabsContent value="complaints" className="mt-4">
          <ComplaintsTab />
        </TabsContent>

        <TabsContent value="promotion" className="mt-4">
          <PromotionTab />
        </TabsContent>

        <TabsContent value="official" className="mt-4">
          <OfficialSetsTab />
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <AuditLogTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
