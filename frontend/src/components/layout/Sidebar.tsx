import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckCircle2,
  UtensilsCrossed,
  CalendarDays,
  Sun,
  Package,
  Wrench,
  Home,
  LogOut,
} from 'lucide-react';
import { useStore } from '../../store.ts';
import { api } from '../../api.ts';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chores', icon: CheckCircle2, label: 'Chores' },
  { to: '/meals', icon: UtensilsCrossed, label: 'Meals' },
  { to: '/calendar', icon: CalendarDays, label: 'Calendar' },
  { to: '/outdoor', icon: Sun, label: 'Outside' },
  { to: '/pantry', icon: Package, label: 'Pantry' },
  { to: '/home', icon: Wrench, label: 'Home' },
];

export default function Sidebar() {
  const user = useStore((s) => s.auth.user);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // ignore logout errors
    }
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar flex-col w-[240px] h-screen bg-bg-card border-r border-border fixed left-0 top-0">
      {/* App Title */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-border">
        <Home className="text-accent" size={24} />
        <h1 className="text-lg font-bold text-text-primary">Home Hub</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-accent text-white'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
              }`
            }
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Info & Logout */}
      <div className="border-t border-border px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">
              {user?.display_name ?? user?.username ?? 'User'}
            </p>
            <p className="text-xs text-text-muted truncate">
              {user?.username}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 text-text-muted hover:text-status-danger rounded-md hover:bg-bg-hover transition-colors"
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}
