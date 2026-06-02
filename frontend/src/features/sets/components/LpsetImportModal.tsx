import { useRef } from 'react';
import { toast } from 'sonner';
import { UploadCloudIcon, Loader2Icon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { useLpsetImport } from '../hooks/useLpsetImport';

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function LpsetImportModal({ open, onOpenChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const mutation = useLpsetImport();

  function handleOpenChange(val: boolean) {
    if (!val && mutation.isPending) return;
    onOpenChange(val);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    mutation.mutate(file, {
      onSuccess: (data) => {
        const parts = [`${data.item_count} items`];
        if (data.reused_count > 0) parts.push(`${data.reused_count} reused`);
        if (data.skipped_count > 0) parts.push(`${data.skipped_count} skipped`);
        toast.success(`Imported "${data.title}" — ${parts.join(', ')}.`);
        onOpenChange(false);
      },
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : 'Import failed.');
      },
    });
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Import .lpset</SheetTitle>
        </SheetHeader>

        <div className="flex flex-col gap-6 p-4">
          {mutation.isPending ? (
            <div className="flex flex-col items-center gap-4 py-12">
              <Loader2Icon className="size-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Importing set…</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-muted-foreground">
                Upload a LingvoPal set bundle (.lpset) exported from another account or the admin panel.
                The set will be added to your library as a draft.
              </p>
              <input
                ref={inputRef}
                type="file"
                accept=".lpset"
                className="sr-only"
                onChange={handleFileChange}
              />
              <button
                type="button"
                className="flex flex-col items-center gap-3 rounded-lg border-2 border-dashed border-border p-10 text-center transition-colors hover:border-primary hover:bg-muted/50"
                onClick={() => inputRef.current?.click()}
              >
                <UploadCloudIcon className="size-10 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Drop your .lpset file here</p>
                  <p className="text-xs text-muted-foreground">or click to browse</p>
                </div>
              </button>
            </div>
          )}
        </div>

        <SheetFooter className="px-4 pb-4">
          <Button
            variant="outline"
            className="w-full"
            disabled={mutation.isPending}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
