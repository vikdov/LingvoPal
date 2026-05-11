import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { CheckCircle2, MailWarning } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { ApiError } from '@/services/api';
import { useMyProfile, useUpdateProfile, useResendVerification, useChangePassword } from '../hooks/useSettings';

function ProfileSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-9 w-full" />
    </div>
  );
}

export function AccountTab() {
  const { data: profile, isLoading } = useMyProfile();
  const updateProfile = useUpdateProfile();
  const resendVerification = useResendVerification();
  const changePassword = useChangePassword();

  const [username, setUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (profile) setUsername(profile.username ?? '');
  }, [profile]);

  function handleSaveUsername() {
    if (!username.trim()) return;
    updateProfile.mutate(
      { username: username.trim() },
      {
        onSuccess: () => toast.success('Username updated'),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to update username'),
      },
    );
  }

  function handleResendVerification() {
    resendVerification.mutate(undefined, {
      onSuccess: () => toast.success('Verification email sent — check your inbox'),
      onError: () => toast.error('Failed to send verification email'),
    });
  }

  function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success('Password changed');
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
        },
        onError: (err) => toast.error(err instanceof ApiError ? err.message : 'Failed to change password'),
      },
    );
  }

  return (
    <div className="space-y-6">
      {/* Email verification banner */}
      {profile && !profile.email_verified && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
          <MailWarning className="mt-0.5 size-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
              Email not verified
            </p>
            <p className="text-sm text-amber-700 dark:text-amber-400">
              Verify your email to secure your account and enable reminders.
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleResendVerification}
            disabled={resendVerification.isPending || resendVerification.isSuccess}
            className="shrink-0 border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-300"
          >
            {resendVerification.isSuccess ? 'Sent!' : resendVerification.isPending ? 'Sending…' : 'Resend email'}
          </Button>
        </div>
      )}

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your public display name and account email.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <ProfileSkeleton />
          ) : (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your_username"
                  maxLength={50}
                />
                <p className="text-xs text-muted-foreground">Letters, numbers, underscores and hyphens only.</p>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <div className="flex items-center gap-2">
                  <Input id="email" value={profile?.email ?? ''} readOnly className="flex-1 text-muted-foreground" />
                  {profile?.email_verified ? (
                    <Badge variant="secondary" className="shrink-0 gap-1 text-green-700 dark:text-green-400">
                      <CheckCircle2 className="size-3" />
                      Verified
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="shrink-0 text-amber-700 dark:text-amber-400">
                      Unverified
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">Email changes are not supported yet.</p>
              </div>
              <Button
                onClick={handleSaveUsername}
                disabled={updateProfile.isPending || !username.trim()}
              >
                {updateProfile.isPending ? 'Saving…' : 'Save profile'}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Change password */}
      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
          <CardDescription>Use a strong password of at least 8 characters.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="current-password">Current password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <Separator />
            <div className="space-y-1.5">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm-password">Confirm new password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <Button
              type="submit"
              disabled={changePassword.isPending || !currentPassword || !newPassword || !confirmPassword}
            >
              {changePassword.isPending ? 'Saving…' : 'Change password'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
