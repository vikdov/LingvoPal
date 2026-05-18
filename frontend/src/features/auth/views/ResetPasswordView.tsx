import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

import { authApi } from '../api/auth.api';
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

const passwordSchema = z
  .string()
  .min(8, 'At least 8 characters')
  .max(128, 'Too long');

const schema = z
  .object({
    new_password: passwordSchema,
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type FormData = z.infer<typeof schema>;

export function ResetPasswordView() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { new_password: '', confirm_password: '' },
  });

  if (!token) {
    return (
      <div className="space-y-6 text-center">
        <div className="lg:hidden flex justify-center mb-2">
          <LingvoLogo className="h-9 w-auto" />
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">{t('auth.resetPassword.invalidLinkTitle')}</h1>
          <p className="text-sm text-muted-foreground">{t('auth.resetPassword.invalidLinkMessage')}</p>
        </div>
        <Button asChild variant="outline" className="w-full">
          <Link to="/auth/forgot-password">{t('auth.resetPassword.requestResetLink')}</Link>
        </Button>
      </div>
    );
  }

  async function onSubmit(data: FormData) {
    try {
      await authApi.resetPassword({ token, new_password: data.new_password });
      toast.success(t('auth.resetPassword.successToast'));
      navigate('/auth/login');
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : t('auth.resetPassword.errorToast'));
    }
  }

  return (
    <div className="space-y-6">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t('auth.resetPassword.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('auth.resetPassword.subtitle')}</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="new_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('auth.resetPassword.newPassword')}</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder={t('auth.passwordPlaceholder')}
                      autoComplete="new-password"
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

          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('auth.resetPassword.confirmPassword')}</FormLabel>
                <FormControl>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={t('auth.passwordPlaceholder')}
                    autoComplete="new-password"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? t('auth.resetPassword.saving') : t('auth.resetPassword.resetPassword')}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-muted-foreground">
        <Button variant="link" size="sm" asChild className="h-auto p-0 font-medium">
          <Link to="/auth/login">{t('auth.forgotPassword.backToSignIn')}</Link>
        </Button>
      </p>
    </div>
  );
}
