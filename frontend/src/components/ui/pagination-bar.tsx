import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export const DEFAULT_PAGE_SIZE_OPTIONS = [20, 50, 100] as const;

interface PaginationBarProps {
  page: number;
  pages: number;
  pageSize: number;
  pageSizeOptions?: readonly number[];
  total: number;
  /** Zero-based offset of the first item on this page */
  skip: number;
  isFetching?: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

function buildPageNumbers(page: number, pages: number): (number | '…')[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);

  const result: (number | '…')[] = [];
  const left = Math.max(2, page - 1);
  const right = Math.min(pages - 1, page + 1);

  result.push(1);
  if (left > 2) result.push('…');
  for (let i = left; i <= right; i++) result.push(i);
  if (right < pages - 1) result.push('…');
  result.push(pages);

  return result;
}

export function PaginationBar({
  page,
  pages,
  pageSize,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
  total,
  skip,
  isFetching = false,
  onPageChange,
  onPageSizeChange,
}: PaginationBarProps) {
  if (total === 0) return null;

  const rangeStart = skip + 1;
  const rangeEnd = Math.min(skip + pageSize, total);
  const pageNumbers = buildPageNumbers(page, pages);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      {/* Left: range info + page size selector */}
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span>
          {rangeStart}–{rangeEnd} of {total}
        </span>
        <div className="flex items-center gap-1.5">
          <span className="hidden sm:inline">Per page:</span>
          <Select
            value={String(pageSize)}
            onValueChange={(v) => onPageSizeChange(Number(v))}
          >
            <SelectTrigger size="sm" className="w-16">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {pageSizeOptions.map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {isFetching && (
          <span className="text-xs text-muted-foreground/60">Loading…</span>
        )}
      </div>

      {/* Right: page navigation */}
      {pages > 1 && (
        <div className="flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Previous page"
          >
            <ChevronLeftIcon className="size-4" />
          </Button>

          {pageNumbers.map((p, i) =>
            p === '…' ? (
              <span
                key={`ellipsis-${i}`}
                className="flex size-8 items-center justify-center text-sm text-muted-foreground"
              >
                …
              </span>
            ) : (
              <Button
                key={p}
                variant={p === page ? 'outline' : 'ghost'}
                size="icon"
                aria-current={p === page ? 'page' : undefined}
                onClick={() => onPageChange(p)}
              >
                <span className="text-sm">{p}</span>
              </Button>
            ),
          )}

          <Button
            variant="ghost"
            size="icon"
            disabled={page >= pages}
            onClick={() => onPageChange(page + 1)}
            aria-label="Next page"
          >
            <ChevronRightIcon className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
