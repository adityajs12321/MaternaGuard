import { Outlet, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/AuthContext';
import { maternaguardApi } from '@/api/maternaguard';
import { LayoutDashboard, Activity, Bell, User, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

const patientTabs = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/log', label: 'Log', icon: Activity },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/profile', label: 'Profile', icon: User },
];

const adminTabs = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/log', label: 'Log', icon: Activity },
  { path: '/alerts', label: 'Alerts', icon: Bell },
  { path: '/provider', label: 'Patients', icon: Shield },
  { path: '/profile', label: 'Profile', icon: User },
];

export default function Layout() {
  const location = useLocation();
  const { user } = useAuth();
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    if (!user?.device_id || user.role === 'admin') {
      setAlertCount(0);
      return;
    }

    maternaguardApi
      .getDeviceAssessments(user.device_id, 50)
      .then((items) => {
        if (cancelled) return;
        const highRiskCount = items.filter((entry) => entry.risk_level === 'high').length;
        setAlertCount(highRiskCount);
      })
      .catch(() => {
        if (!cancelled) setAlertCount(0);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  const tabs = user?.role === 'admin' ? adminTabs : patientTabs;

  return (
    <div className="flex flex-col min-h-screen max-w-md mx-auto bg-background relative">
      {/* Scrollable content area with bottom padding for tab bar */}
      <main className="flex-1 overflow-y-auto pb-20">
        <Outlet context={{ user }} />
      </main>

      {/* Bottom tab bar */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-card border-t border-border z-50 flex items-stretch">
        {tabs.map(({ path, label, icon: Icon }) => {
          const active = location.pathname === path;
          const isAlerts = path === '/alerts';
          return (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex-1 flex flex-col items-center justify-center py-2 gap-0.5 relative transition-colors',
                active ? 'text-primary' : 'text-muted-foreground'
              )}
            >
              <div className="relative">
                <Icon size={22} strokeWidth={active ? 2.5 : 1.8} />
                {isAlerts && alertCount > 0 && (
                  <span className="absolute -top-1 -right-1.5 w-4 h-4 bg-red-500 rounded-full text-white text-[9px] flex items-center justify-center font-bold">
                    {alertCount > 9 ? '9+' : alertCount}
                  </span>
                )}
              </div>
              <span className={cn('text-[10px] font-medium', active ? 'text-primary' : 'text-muted-foreground')}>
                {label}
              </span>
              {active && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-primary rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}