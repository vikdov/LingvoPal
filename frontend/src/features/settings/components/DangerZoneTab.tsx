import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { RotateCcw, Trash2 } from 'lucide-react';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError } from '@/services/api';
import { useAuthStore } from '@/features/auth/store/auth.store';
import { useResetSettings, useDeleteAccount, useMyProfile } from '../hooks/useSettings';

export function DangerZoneTab() {
  const { data: profile } = useMyProfile();
  const resetSettings = useResetSettings();
  const deleteAccount = useDeleteAccount();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const navigate = useNavigate();

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState('');
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false);

  function handleReset() {
    resetSettings.mutate(undefined, {
      onSuccess: () => {
        setResetConfirmOpen(false);
        toast.success('Settings reset to defaults');
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to reset settings'),
    });
  }

  function handleDelete() {
    deleteAccount.mutate(undefined, {
      onSuccess: () => {
        clearAuth();
        navigate('/', { replace: true });
        toast.success('Account deleted');
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to delete account'),
    });
  }

  const deleteConfirmed = confirmEmail === profile?.email;

  return (
    <div className="space-y-6">
      {/* Reset settings */}
      <Card className="border-amber-200 dark:border-amber-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="size-4" />
            Reset settings
          </CardTitle>
          <CardDescription>
            Restore all learning preferences to their default values. Your language settings and
            study history are preserved.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={resetConfirmOpen} onOpenChange={setResetConfirmOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-950/30">
                Reset to defaults
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Reset settings to defaults?</DialogTitle>
                <DialogDescription>
                  All learning preferences will be restored to their default values. Your languages
                  and study history are not affected.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setResetConfirmOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-700 dark:text-amber-400"
                  onClick={handleReset}
                  disabled={resetSettings.isPending}
                >
                  {resetSettings.isPending ? 'Resetting…' : 'Yes, reset'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Delete account */}
      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <Trash2 className="size-4" />
            Delete account
          </CardTitle>
          <CardDescription>
            Permanently delete your account and all associated data. This action cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={deleteDialogOpen} onOpenChange={(open) => { setDeleteDialogOpen(open); if (!open) setConfirmEmail(''); }}>
            <DialogTrigger asChild>
              <Button variant="destructive">Delete my account</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete your account?</DialogTitle>
                <DialogDescription>
                  This will permanently erase your account, all sets, items, and study history.
                  There is no recovery.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-1.5 py-2">
                <Label htmlFor="confirm-email">
                  Type <span className="font-mono font-medium">{profile?.email}</span> to confirm
                </Label>
                <Input
                  id="confirm-email"
                  type="email"
                  value={confirmEmail}
                  onChange={(e) => setConfirmEmail(e.target.value)}
                  placeholder={profile?.email}
                  autoComplete="off"
                />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => { setDeleteDialogOpen(false); setConfirmEmail(''); }}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  disabled={!deleteConfirmed || deleteAccount.isPending}
                  onClick={handleDelete}
                >
                  {deleteAccount.isPending ? 'Deleting…' : 'Delete account'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
