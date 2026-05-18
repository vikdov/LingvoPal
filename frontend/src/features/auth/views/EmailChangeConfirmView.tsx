import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { settingsApi } from '@/features/settings/api/settings.api';
import { ApiError } from '@/services/api';
import { useAuthStore } from '../store/auth.store';
import { LingvoLogo } from '@/components/LingvoLogo';
import { Button } from '@/components/ui/button';

type Status = 'loading' | 'success' | 'error';

export function EmailChangeConfirmView() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<Status>('loading');
  const [newEmail, setNewEmail] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const calledRef = useRef(false);
  const updateUser = useAuthStore((s) => s.updateUser);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    if (!token) {
      setErrorMessage(t('auth.emailChange.noToken'));
      setStatus('error');
      return;
    }

    settingsApi
      .confirmEmailChange(token)
      .then((profile) => {
        updateUser({ email: profile.email });
        setNewEmail(profile.email);
        setStatus('success');
      })
      .catch((err) => {
        setErrorMessage(
          err instanceof ApiError
            ? err.message
            : t('auth.emailChange.linkExpired'),
        );
        setStatus('error');
      });
  }, [token, updateUser, t]);

  return (
    <div className="space-y-6 text-center">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      {status === 'loading' && (
        <div className="space-y-3">
          <Loader2 className="mx-auto size-10 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{t('auth.emailChange.confirming')}</p>
        </div>
      )}

      {status === 'success' && (
        <div className="space-y-4">
          <CheckCircle className="mx-auto size-12 text-green-500" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">{t('auth.emailChange.successTitle')}</h1>
            <p className="text-sm text-muted-foreground">
              {t('auth.emailChange.successMessage', { email: newEmail })}
            </p>
          </div>
          <Button asChild className="w-full">
            <Link to="/settings">{t('auth.emailChange.goToSettings')}</Link>
          </Button>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-4">
          <XCircle className="mx-auto size-12 text-destructive" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">{t('auth.emailChange.errorTitle')}</h1>
            <p className="text-sm text-muted-foreground">{errorMessage}</p>
          </div>
          <Button asChild variant="outline" className="w-full">
            <Link to="/settings">{t('auth.emailChange.goToSettings')}</Link>
          </Button>
        </div>
      )}
    </div>
  );
}
