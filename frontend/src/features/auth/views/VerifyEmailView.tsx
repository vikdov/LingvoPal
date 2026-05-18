import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

import { authApi } from '../api/auth.api';
import { ApiError } from '@/services/api';
import { useAuthStore } from '../store/auth.store';
import { LingvoLogo } from '@/components/LingvoLogo';
import { Button } from '@/components/ui/button';

type Status = 'loading' | 'success' | 'already_verified' | 'error';

export function VerifyEmailView() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<Status>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [resending, setResending] = useState(false);
  const calledRef = useRef(false);
  const updateUser = useAuthStore((s) => s.updateUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    if (!token) {
      setErrorMessage(t('auth.verifyEmail.noToken'));
      setStatus('error');
      return;
    }

    authApi
      .verifyEmail(token)
      .then(() => {
        updateUser({ email_verified: true });
        setStatus('success');
      })
      .catch((err) => {
        if (err instanceof ApiError && err.code === 'already_verified') {
          updateUser({ email_verified: true });
          setStatus('already_verified');
          return;
        }
        setErrorMessage(
          err instanceof ApiError
            ? err.message
            : t('auth.verifyEmail.linkExpired'),
        );
        setStatus('error');
      });
  }, [token, updateUser, t]);

  async function handleResend() {
    setResending(true);
    try {
      await authApi.resendVerification();
      toast.success(t('auth.verifyEmail.successToast'));
    } catch {
      toast.error(t('auth.verifyEmail.errorToast'));
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="space-y-6 text-center">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      {status === 'loading' && (
        <div className="space-y-3">
          <Loader2 className="mx-auto size-10 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{t('auth.verifyEmail.verifying')}</p>
        </div>
      )}

      {(status === 'success' || status === 'already_verified') && (
        <div className="space-y-4">
          <CheckCircle className="mx-auto size-12 text-green-500" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">{t('auth.verifyEmail.successTitle')}</h1>
            <p className="text-sm text-muted-foreground">
              {status === 'already_verified'
                ? t('auth.verifyEmail.alreadyVerified')
                : t('auth.verifyEmail.justVerified')}
            </p>
          </div>
          <Button asChild className="w-full">
            <Link to="/dashboard">{t('auth.verifyEmail.goToDashboard')}</Link>
          </Button>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-4">
          <XCircle className="mx-auto size-12 text-destructive" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">{t('auth.verifyEmail.errorTitle')}</h1>
            <p className="text-sm text-muted-foreground">{errorMessage}</p>
          </div>
          <div className="space-y-2">
            {isAuthenticated && (
              <Button
                className="w-full"
                onClick={handleResend}
                disabled={resending}
              >
                {resending ? t('common.sending') : t('auth.verifyEmail.resend')}
              </Button>
            )}
            <Button asChild variant="outline" className="w-full">
              <Link to="/dashboard">{t('auth.verifyEmail.goToDashboard')}</Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
