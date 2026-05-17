import { Outlet, NavLink } from 'react-router-dom';
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const NAV_MAIN = [
  { label: 'Dashboard', to: '/dashboard',     icon: LayoutDashboard },
  { label: 'Library',   to: '/sets',          icon: BookOpen },
  { label: 'Discover',  to: '/sets/discover', icon: Compass },
  { label: 'Practice',  to: '/practice',      icon: PenLine },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <Sidebar>
          <SidebarHeader className="px-4 py-4">
            <LingvoLogo className="h-8 w-auto" />
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarMenu>
                {NAV_MAIN.map(({ label, to, icon: Icon }) => (
                  <SidebarMenuItem key={to}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={to}
                        end={to === '/sets'}
                        className={({ isActive }) =>
                          isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                        }
                      >
                        <Icon className="size-4" />
                        <span className="flex-1">{label}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
                {user?.is_admin && (
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to="/admin"
                        className={({ isActive }) =>
                          isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                        }
                      >
                        <ShieldCheck className="size-4" />
                        <span>Admin</span>
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
                <SidebarMenuButton asChild>
                  <NavLink
                    to="/settings"
                    className={({ isActive }) =>
                      isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''
                    }
                  >
                    <Settings className="size-4" />
                    <span>Settings</span>
                    {user && !user.email_verified && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <AlertCircle className="size-3.5 text-amber-500 ml-auto shrink-0" />
                          </TooltipTrigger>
                          <TooltipContent side="right">
                            Email not verified.
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
                  className="text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="size-4" />
                  <span>Sign out</span>
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
            <LanguageSwitcher />
          </header>
          <main className="flex-1 overflow-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
