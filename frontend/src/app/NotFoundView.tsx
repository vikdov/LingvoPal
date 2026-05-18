import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

export function NotFoundView() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-6xl font-bold tracking-tight">404</h1>
      <p className="text-muted-foreground">{t('notFound.pageNotFound')}</p>
      <Button asChild>
        <Link to="/">{t('notFound.goHome')}</Link>
      </Button>
    </div>
  );
}
