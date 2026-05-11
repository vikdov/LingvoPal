import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

import { authApi } from '../api/auth.api';
import { ApiError } from '@/services/api';
import { LingvoLogo } from '@/components/LingvoLogo';
import { Button } from '@/components/ui/button';

type Status = 'loading' | 'success' | 'error';

export function VerifyEmailView() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<Status>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    if (!token) {
      setErrorMessage('No verification token found. Check your email link.');
      setStatus('error');
      return;
    }

    authApi
      .verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setErrorMessage(
          err instanceof ApiError
            ? err.message
            : 'Verification failed. The link may have expired.',
        );
        setStatus('error');
      });
  }, [token]);

  return (
    <div className="space-y-6 text-center">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      {status === 'loading' && (
        <div className="space-y-3">
          <Loader2 className="mx-auto size-10 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Verifying your email…</p>
        </div>
      )}

      {status === 'success' && (
        <div className="space-y-4">
          <CheckCircle className="mx-auto size-12 text-green-500" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">Email verified</h1>
            <p className="text-sm text-muted-foreground">
              Your email address has been confirmed.
            </p>
          </div>
          <Button asChild className="w-full">
            <Link to="/dashboard">Go to dashboard</Link>
          </Button>
        </div>
      )}

      {status === 'error' && (
        <div className="space-y-4">
          <XCircle className="mx-auto size-12 text-destructive" />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">Verification failed</h1>
            <p className="text-sm text-muted-foreground">{errorMessage}</p>
          </div>
          <div className="space-y-2">
            <Button asChild variant="outline" className="w-full">
              <Link to="/dashboard">Go to dashboard</Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
