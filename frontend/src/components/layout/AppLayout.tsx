import { Outlet, NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup,
  SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton,
  SidebarProvider, SidebarTrigger,
} from '@/components/ui/sidebar';
import { LingvoLogo } from '@/components/LingvoLogo';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  LayoutDashboard, BookOpen, Compass, PenLine, Settings, LogOut, AlertCircle, ShieldCheck,
} from 'lucide-react';
import { Separator } from '@/components/ui/separator';
import { LanguageSwitcher } from '@/features/languages/components/LanguageSwitcher';
import { useUserLanguages } from '@/features/languages';
import { ToggleTheme } from '@/components/ui/toggle-theme';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export function AppLayout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  useUserLanguages();

  const NAV_MAIN = [
    { label: t('nav.dashboard'), to: '/dashboard', icon: LayoutDashboard },
    { label: t('nav.library'), to: '/sets', icon: BookOpen },
    { label: t('nav.discover'), to: '/sets/discover', icon: Compass },
    { label: t('nav.practice'), to: '/practice', icon: PenLine },
  ];

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <Sidebar>
          <SidebarHeader className="px-6 py-4">
            <NavLink to="/dashboard">
              <LingvoLogo className="h-9 w-auto" />
            </NavLink>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarMenu>
                {NAV_MAIN.map(({ label, to, icon: Icon }) => (
                  <SidebarMenuItem key={to}>
                    <SidebarMenuButton asChild className="text-[15px]">
                      <NavLink
                        to={to}
                        end={to === '/sets'}
                        className={({ isActive }) =>
                          isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                        }
                      >
                        <Icon className="size-[18px]" />
                        <span className="flex-1">{label}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
                {user?.is_admin && (
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild className="text-[15px]">
                      <NavLink
                        to="/admin"
                        className={({ isActive }) =>
                          isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                        }
                      >
                        <ShieldCheck className="size-[18px]" />
                        <span>{t('nav.admin')}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )}
              </SidebarMenu>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="px-3 pb-4">
            <Separator className="mb-3" />
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild className="text-[15px]">
                  <NavLink
                    to="/settings"
                    className={({ isActive }) =>
                      isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                    }
                  >
                    <Settings className="size-[18px]" />
                    <span>{t('nav.settings')}</span>
                    {user && !user.email_verified && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <AlertCircle className="size-3.5 text-amber-500 ml-auto shrink-0" />
                          </TooltipTrigger>
                          <TooltipContent side="right">
                            {t('nav.emailNotVerified')}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                  </NavLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={logout}
                  className="text-[15px] text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="size-[18px]" />
                  <span>{t('nav.signOut')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>

            {user && (
              <div className="mt-3 px-2 py-2 rounded-md bg-sidebar-accent/50">
                <p className="text-xs font-semibold text-sidebar-foreground truncate">
                  {user.username}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">{user.email}</p>
              </div>
            )}
          </SidebarFooter>
        </Sidebar>

        <div className="flex flex-1 flex-col min-w-0">
          <header className="flex items-center justify-between h-12 px-4 border-b border-border shrink-0">
            <SidebarTrigger />
            <div className="flex items-center gap-3">
              <ToggleTheme />
              <LanguageSwitcher />
            </div>
          </header>
          <main className="flex-1 overflow-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
