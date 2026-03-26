import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckCircle2,
  UtensilsCrossed,
  CalendarDays,
  Sun,
  Package,
  Wrench,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Home' },
  { to: '/chores', icon: CheckCircle2, label: 'Chores' },
  { to: '/meals', icon: UtensilsCrossed, label: 'Meals' },
  { to: '/calendar', icon: CalendarDays, label: 'Calendar' },
  { to: '/outdoor', icon: Sun, label: 'Outside' },
  { to: '/pantry', icon: Package, label: 'Pantry' },
  { to: '/home', icon: Wrench, label: 'Maint.' },
];

export default function BottomNav() {
  return (
    <nav className="bottom-nav fixed bottom-0 left-0 right-0 z-40 bg-bg-card border-t border-border">
      <div className="flex items-center justify-around h-16 px-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-0.5 px-2 py-1 rounded-md transition-colors ${
                isActive
                  ? 'text-accent'
                  : 'text-text-muted hover:text-text-secondary'
              }`
            }
          >
            <item.icon size={20} />
            <span className="hidden sm:block text-[10px] font-medium leading-tight">
              {item.label}
            </span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
