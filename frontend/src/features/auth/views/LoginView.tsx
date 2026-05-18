import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../hooks/useAuth';
import { ApiError } from '@/services/api';
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
  password: z.string().min(1, 'Password is required'),
});

type FormData = z.infer<typeof schema>;

export function LoginView() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  async function onSubmit(data: FormData) {
    try {
      await login(data);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : t('auth.login.error'));
    }
  }

  return (
    <div className="space-y-6">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t('auth.login.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('auth.login.subtitle')}</p>
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

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center justify-between">
                  <FormLabel>{t('common.password')}</FormLabel>
                  <Button
                    variant="link"
                    size="sm"
                    asChild
                    className="h-auto p-0 text-xs font-normal text-muted-foreground"
                    tabIndex={-1}
                  >
                    <Link to="/auth/forgot-password">{t('auth.login.forgotPassword')}</Link>
                  </Button>
                </div>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder={t('auth.passwordPlaceholder')}
                      autoComplete="current-password"
                      className="pr-10"
                      {...field}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute inset-y-0 right-1 my-auto text-muted-foreground hover:text-foreground"
                      aria-label={showPassword ? t('auth.hidePassword') : t('auth.showPassword')}
                    >
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? t('auth.login.signingIn') : t('common.signIn')}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-muted-foreground">
        {t('auth.login.noAccount')}{' '}
        <Button variant="link" size="sm" asChild className="h-auto p-0 font-medium">
          <Link to="/auth/register">{t('common.signUp')}</Link>
        </Button>
      </p>
    </div>
  );
}
