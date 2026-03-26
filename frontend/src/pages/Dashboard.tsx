import { useEffect, useState, useCallback } from 'react';
import {
  Cloud,
  Droplets,
  Wind,
  Thermometer,
  AlertTriangle,
  CheckCircle2,
  UtensilsCrossed,
  CalendarDays,
  Sun,
  Package,
  Wrench,
} from 'lucide-react';
import { api } from '../api.ts';
import { useStore } from '../store.ts';
import type { DashboardData } from '../types.ts';
import ChatWidget from '../components/ChatWidget.tsx';

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

function formatDate(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function Dashboard() {
  const user = useStore((s) => s.auth.user);
  const showToast = useStore((s) => s.showToast);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await api.get('/dashboard');
      setData(res.data);
    } catch {
      showToast('Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const displayName = user?.display_name ?? user?.username ?? 'there';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-muted text-sm">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          {getGreeting()}, {displayName}
        </h1>
        <p className="text-text-secondary text-sm mt-1">{formatDate()}</p>
      </div>

      {/* AI Chat */}
      <ChatWidget onActionComplete={fetchDashboard} />

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Weather Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Cloud className="text-status-info" size={18} />
            <h2 className="text-sm font-semibold text-text-primary">Weather</h2>
          </div>
          {data?.weather ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-bold text-text-primary">
                    {Math.round(data.weather.temp_f)}&deg;F
                  </p>
                  <p className="text-sm text-text-secondary capitalize">
                    {data.weather.desc}
                  </p>
                </div>
                <span className="text-5xl leading-none" role="img" aria-label={data.weather.desc}>
                  {data.weather.icon}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-text-muted">
                <div className="flex items-center gap-1.5">
                  <Thermometer size={13} />
                  <span>Feels {Math.round(data.weather.feels_like)}&deg;</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Droplets size={13} />
                  <span>{data.weather.humidity}% humidity</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Wind size={13} />
                  <span>{data.weather.wind_mph} mph wind</span>
                </div>
                {data.weather.high !== null && data.weather.low !== null && (
                  <div className="flex items-center gap-1.5">
                    <span>H: {Math.round(data.weather.high)}&deg; L: {Math.round(data.weather.low)}&deg;</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-text-muted">Weather data unavailable</p>
          )}
        </div>

        {/* Overdue Chores Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-status-danger" size={18} />
              <h2 className="text-sm font-semibold text-text-primary">Overdue</h2>
            </div>
            {data?.overdue_chores && data.overdue_chores.length > 0 && (
              <span className="bg-status-danger/20 text-status-danger text-xs font-medium px-2 py-0.5 rounded-full">
                {data.overdue_chores.length}
              </span>
            )}
          </div>
          {data?.overdue_chores && data.overdue_chores.length > 0 ? (
            <ul className="space-y-2">
              {data.overdue_chores.slice(0, 5).map((chore) => (
                <li key={chore.id} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-status-danger mt-1.5 shrink-0" />
                  <span>{chore.title}</span>
                </li>
              ))}
              {data.overdue_chores.length > 5 && (
                <li className="text-xs text-text-muted pl-3.5">
                  +{data.overdue_chores.length - 5} more
                </li>
              )}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">All caught up!</p>
          )}
        </div>

        {/* Due Today Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="text-status-warning" size={18} />
              <h2 className="text-sm font-semibold text-text-primary">Due Today</h2>
            </div>
            {data?.due_today_chores && data.due_today_chores.length > 0 && (
              <span className="bg-status-warning/20 text-status-warning text-xs font-medium px-2 py-0.5 rounded-full">
                {data.due_today_chores.length}
              </span>
            )}
          </div>
          {data?.due_today_chores && data.due_today_chores.length > 0 ? (
            <ul className="space-y-2">
              {data.due_today_chores.slice(0, 5).map((chore) => (
                <li key={chore.id} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-status-warning mt-1.5 shrink-0" />
                  <span>{chore.title}</span>
                </li>
              ))}
              {data.due_today_chores.length > 5 && (
                <li className="text-xs text-text-muted pl-3.5">
                  +{data.due_today_chores.length - 5} more
                </li>
              )}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">Nothing due today</p>
          )}
        </div>

        {/* Today's Meals Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <UtensilsCrossed className="text-status-success" size={18} />
            <h2 className="text-sm font-semibold text-text-primary">Today&apos;s Meals</h2>
          </div>
          {data?.todays_meals && data.todays_meals.length > 0 ? (
            <ul className="space-y-2">
              {data.todays_meals.map((meal) => (
                <li key={meal.id} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="text-xs capitalize text-text-muted w-14 shrink-0">{meal.meal_type}</span>
                  <span>{meal.meal_name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">No meals planned today</p>
          )}
        </div>

        {/* Calendar Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <CalendarDays className="text-accent" size={18} />
            <h2 className="text-sm font-semibold text-text-primary">Upcoming Events</h2>
          </div>
          {data?.upcoming_events && data.upcoming_events.length > 0 ? (
            <ul className="space-y-2">
              {data.upcoming_events.map((event, i) => (
                <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                  <div
                    className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                    style={{ backgroundColor: event.source_color }}
                  />
                  <div>
                    <span>{event.summary}</span>
                    <p className="text-xs text-text-muted">
                      {new Date(event.start).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      {' '}
                      {new Date(event.start).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">No upcoming events</p>
          )}
        </div>

        {/* Outdoor This Week Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center gap-2 mb-3">
            <Sun className="text-status-warning" size={18} />
            <h2 className="text-sm font-semibold text-text-primary">Outdoor This Week</h2>
          </div>
          {data?.outdoor_this_week && data.outdoor_this_week.sessions ? (
            <div className="space-y-1">
              <p className="text-2xl font-bold text-text-primary">
                {data.outdoor_this_week.total_hours ?? 0}h
              </p>
              <p className="text-xs text-text-muted">
                {data.outdoor_this_week.sessions} sessions this week
              </p>
            </div>
          ) : (
            <p className="text-sm text-text-muted">No outdoor time logged this week</p>
          )}
        </div>

        {/* Expiring Pantry Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Package className="text-status-warning" size={18} />
              <h2 className="text-sm font-semibold text-text-primary">Expiring Soon</h2>
            </div>
            {data?.expiring_pantry && data.expiring_pantry.length > 0 && (
              <span className="bg-status-warning/20 text-status-warning text-xs font-medium px-2 py-0.5 rounded-full">
                {data.expiring_pantry.length}
              </span>
            )}
          </div>
          {data?.expiring_pantry && data.expiring_pantry.length > 0 ? (
            <ul className="space-y-2">
              {data.expiring_pantry.map((item) => (
                <li key={item.id} className="text-sm text-text-secondary flex items-start justify-between">
                  <span>{item.item_name}</span>
                  <span className="text-xs text-text-muted shrink-0 ml-2">{item.expiration_date}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">No items expiring soon</p>
          )}
        </div>

        {/* Maintenance Due Card */}
        <div className="bg-bg-card rounded-lg p-4 border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Wrench className="text-status-info" size={18} />
              <h2 className="text-sm font-semibold text-text-primary">Maintenance Due</h2>
            </div>
            {data?.maintenance_due && data.maintenance_due.length > 0 && (
              <span className="bg-status-info/20 text-status-info text-xs font-medium px-2 py-0.5 rounded-full">
                {data.maintenance_due.length}
              </span>
            )}
          </div>
          {data?.maintenance_due && data.maintenance_due.length > 0 ? (
            <ul className="space-y-2">
              {data.maintenance_due.map((task) => (
                <li key={task.id} className="text-sm text-text-secondary flex items-start justify-between">
                  <span>{task.title}</span>
                  {task.next_due && (
                    <span className="text-xs text-text-muted shrink-0 ml-2">{task.next_due}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-muted">No maintenance due</p>
          )}
        </div>
      </div>
    </div>
  );
}
