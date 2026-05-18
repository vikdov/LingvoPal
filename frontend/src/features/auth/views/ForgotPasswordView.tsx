import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { authApi } from '../api/auth.api';
import { LingvoLogo } from '@/components/LingvoLogo';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
});

type FormData = z.infer<typeof schema>;

export function ForgotPasswordView() {
  const { t } = useTranslation();
  const [submitted, setSubmitted] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
  });

  async function onSubmit(data: FormData) {
    await authApi.forgotPassword({ email: data.email });
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="space-y-6 text-center">
        <div className="lg:hidden flex justify-center mb-2">
          <LingvoLogo className="h-9 w-auto" />
        </div>
        <CheckCircle className="mx-auto size-12 text-green-500" />
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">{t('auth.forgotPassword.successTitle')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('auth.forgotPassword.successMessage')}
          </p>
        </div>
        <Button asChild variant="outline" className="w-full">
          <Link to="/auth/login">{t('auth.forgotPassword.backToSignIn')}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t('auth.forgotPassword.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('auth.forgotPassword.subtitle')}</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('common.email')}</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder={t('auth.emailPlaceholder')}
                    autoComplete="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? t('common.sending') : t('auth.forgotPassword.sendResetLink')}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-muted-foreground">
        {t('auth.forgotPassword.rememberIt')}{' '}
        <Button variant="link" size="sm" asChild className="h-auto p-0 font-medium">
          <Link to="/auth/login">{t('common.signIn')}</Link>
        </Button>
      </p>
    </div>
  );
}
