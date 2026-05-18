import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../hooks/useAuth';
import { ApiError } from '@/services/api';
import { languagesApi, detectNativeLangId } from '@/features/languages';
import { LingvoLogo } from '@/components/LingvoLogo';
import { Checkbox } from '@/components/ui/checkbox';
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

const schema = z
  .object({
    email: z.string().email('Enter a valid email address'),
    username: z
      .string()
      .min(3, 'At least 3 characters')
      .max(50, 'At most 50 characters')
      .regex(/^[a-zA-Z0-9_-]+$/, 'Letters, numbers, _ and - only'),
    password: z
      .string()
      .min(8, 'At least 8 characters')
      .max(72, 'At most 72 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[a-z]/, 'Must contain a lowercase letter')
      .regex(/[0-9]/, 'Must contain a digit')
      .regex(/[^a-zA-Z0-9\s]/, 'Must contain a special character (e.g. !@#$%^&*)'),
    confirmPassword: z.string(),
    native_lang_id: z.coerce
      .number({ invalid_type_error: 'Select your native language' })
      .int()
      .positive('Select your native language'),
    agreedToTerms: z.boolean().refine((v) => v === true, {
      message: 'You must accept the terms and privacy policy',
    }),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type FormData = z.infer<typeof schema>;

export function RegisterView() {
  const { t } = useTranslation();
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const { data: languages = [], isLoading: loadingLanguages } = useQuery({
    queryKey: ['languages'],
    queryFn: languagesApi.getAll,
    staleTime: Infinity,
  });

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
      native_lang_id: 0,
      agreedToTerms: false,
    },
  });

  useEffect(() => {
    if (languages.length > 0) {
      form.setValue('native_lang_id', detectNativeLangId(languages));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [languages]);

  async function onSubmit(data: FormData) {
    try {
      const { confirmPassword: _, agreedToTerms: __, ...payload } = data;
      await signup({
        ...payload,
        native_lang_id: Number(payload.native_lang_id),
      });
      navigate('/dashboard');
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : t('auth.register.error'));
    }
  }

  return (
    <div className="space-y-6">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">{t('auth.register.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('auth.register.subtitle')}</p>
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
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('common.username')}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t('auth.register.usernamePlaceholder')}
                    autoComplete="username"
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
                <FormLabel>{t('common.password')}</FormLabel>
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
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('auth.register.confirmPassword')}</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showConfirm ? 'text' : 'password'}
                      placeholder={t('auth.passwordPlaceholder')}
                      autoComplete="new-password"
                      className="pr-10"
                      {...field}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setShowConfirm((v) => !v)}
                      className="absolute inset-y-0 right-1 my-auto text-muted-foreground hover:text-foreground"
                      aria-label={showConfirm ? t('auth.hidePassword') : t('auth.showPassword')}
                    >
                      {showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="agreedToTerms"
            render={({ field }) => (
              <FormItem className="flex items-start gap-3 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel className="text-sm font-normal cursor-pointer">
                    {t('auth.register.agreeTermsPre')}{' '}
                    <Link to="/terms" className="underline hover:text-foreground">
                      {t('auth.register.termsOfService')}
                    </Link>
                    {' '}{t('auth.register.and')}{' '}
                    <Link to="/privacy" className="underline hover:text-foreground">
                      {t('auth.register.privacyPolicy')}
                    </Link>
                  </FormLabel>
                  <FormMessage />
                </div>
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full"
            disabled={form.formState.isSubmitting || loadingLanguages}
          >
            {form.formState.isSubmitting ? t('auth.register.creatingAccount') : t('auth.register.createAccount')}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-muted-foreground">
        {t('auth.register.alreadyHaveAccount')}{' '}
        <Button variant="link" size="sm" asChild className="h-auto p-0 font-medium">
          <Link to="/auth/login">{t('common.signIn')}</Link>
        </Button>
      </p>
    </div>
  );
}
