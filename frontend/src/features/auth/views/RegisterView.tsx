import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

import { useAuth } from '../hooks/useAuth';
import { ApiError } from '@/services/api';
import { languagesApi, detectNativeLangId } from '@/services/languages.api';
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
      .max(128, 'At most 128 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[a-z]/, 'Must contain a lowercase letter')
      .regex(/[0-9]/, 'Must contain a digit')
      .regex(/[!@#$%^&*+-]/, 'Must contain a special character (!@#$%^&*+-)'),
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
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const { data: languages = [], isLoading: loadingLanguages } = useQuery({
    queryKey: ['languages'],
    queryFn: languagesApi.list,
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
      toast.error(err instanceof ApiError ? err.message : 'Registration failed. Please try again.');
    }
  }

  return (
    <div className="space-y-6">
      <div className="lg:hidden flex justify-center mb-2">
        <LingvoLogo className="h-9 w-auto" />
      </div>

      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Create an account</h1>
        <p className="text-sm text-muted-foreground">
          Start your language learning journey
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="you@example.com"
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
                <FormLabel>Username</FormLabel>
                <FormControl>
                  <Input
                    placeholder="your_username"
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
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
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
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
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
                <FormLabel>Confirm password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showConfirm ? 'text' : 'password'}
                      placeholder="••••••••"
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
                      aria-label={showConfirm ? 'Hide password' : 'Show password'}
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
                    I agree to the{' '}
                    <Link to="/terms" className="underline hover:text-foreground">
                      Terms of Service
                    </Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="underline hover:text-foreground">
                      Privacy Policy
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
            {form.formState.isSubmitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>
      </Form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Button variant="link" size="sm" asChild className="h-auto p-0 font-medium">
          <Link to="/auth/login">Sign in</Link>
        </Button>
      </p>
    </div>
  );
}
