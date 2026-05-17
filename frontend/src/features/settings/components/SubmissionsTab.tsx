import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ClockIcon, CheckCircleIcon, XCircleIcon, LayersIcon, BookOpenIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty';
import { PaginationBar } from '@/components/ui/pagination-bar';
import { useMySubmissions } from '@/features/sets/hooks/useSetsQuery';
import type { ModerationSubmission } from '@/features/sets/types/sets.types';

function StatusBadge({ status }: { status: ModerationSubmission['status'] }) {
  if (status === 'pending') {
    return (
      <Badge variant="outline" className="border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-400 gap-1">
        <ClockIcon className="size-3" /> Under review
      </Badge>
    );
  }
  if (status === 'approved') {
    return (
      <Badge variant="outline" className="border-green-300 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950/30 dark:text-green-400 gap-1">
        <CheckCircleIcon className="size-3" /> Approved
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="border-red-300 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-400 gap-1">
      <XCircleIcon className="size-3" /> Rejected
    </Badge>
  );
}

function SubmissionCard({ entry }: { entry: ModerationSubmission }) {
  const targetPath = entry.target_type === 'set' ? `/sets/${entry.target_id}` : null;

  return (
    <Card size="sm">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              {entry.target_type === 'set' ? (
                <LayersIcon className="size-3.5 shrink-0 text-muted-foreground" />
              ) : (
                <BookOpenIcon className="size-3.5 shrink-0 text-muted-foreground" />
              )}
              <CardTitle className="text-sm capitalize">
                {entry.target_type} #{entry.target_id}
                {targetPath && (
                  <Link to={targetPath} className="ml-1 text-xs text-muted-foreground underline-offset-2 hover:underline">
                    view
                  </Link>
                )}
              </CardTitle>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Submitted {new Date(entry.created_at).toLocaleDateString()}
              {entry.resolved_at && ` · Resolved ${new Date(entry.resolved_at).toLocaleDateString()}`}
            </p>
          </div>
          <StatusBadge status={entry.status} />
        </div>
      </CardHeader>

      {(entry.feedback || entry.resolution_feedback) && (
        <CardContent className="flex flex-col gap-2">
          {entry.feedback && (
            <div>
              <p className="text-xs font-medium text-muted-foreground">Your note</p>
              <p className="text-sm text-foreground/80 italic">&ldquo;{entry.feedback}&rdquo;</p>
            </div>
          )}
          {entry.resolution_feedback && (
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                {entry.status === 'rejected' ? 'Rejection reason' : 'Moderator note'}
              </p>
              <p className={`text-sm italic ${entry.status === 'rejected' ? 'text-red-700 dark:text-red-400' : 'text-foreground/80'}`}>
                &ldquo;{entry.resolution_feedback}&rdquo;
              </p>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export function SubmissionsTab() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const skip = (page - 1) * pageSize;

  const { data, isLoading, isFetching } = useMySubmissions(skip, pageSize);
  const submissions = data?.data ?? [];
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 0;

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} size="sm">
            <CardHeader>
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </CardHeader>
          </Card>
        ))}
      </div>
    );
  }

  if (submissions.length === 0) {
    return (
      <Empty>
        <EmptyMedia variant="icon">
          <ClockIcon className="size-4" />
        </EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>No submissions yet</EmptyTitle>
          <EmptyDescription>
            Submit a set or expression for review to see it here.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className={`flex flex-col gap-3 transition-opacity duration-150 ${isFetching ? 'opacity-60' : 'opacity-100'}`}>
        {submissions.map((entry) => (
          <SubmissionCard key={entry.id} entry={entry} />
        ))}
      </div>
      {pages > 1 && (
        <PaginationBar
          page={page}
          pages={pages}
          pageSize={pageSize}
          total={total}
          skip={skip}
          isFetching={isFetching}
          onPageChange={setPage}
          onPageSizeChange={() => {}}
        />
      )}
    </div>
  );
}
