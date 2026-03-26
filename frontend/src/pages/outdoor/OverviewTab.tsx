import { Clock, MapPin, Activity, Sun } from 'lucide-react';
import type { OutdoorStats } from './OutdoorPage.tsx';

interface Props {
  stats: OutdoorStats | null;
  loading: boolean;
}

function fmtDuration(min: number): string {
  if (min < 60) return `${Math.round(min)}m`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export default function OverviewTab({ stats, loading }: Props) {
  if (loading) {
    return <div className="text-text-muted text-sm py-8 text-center">Loading...</div>;
  }

  const totals = stats?.totals ?? { total_sessions: 0, total_minutes: 0, avg_minutes: 0 };
  const totalHours = (totals.total_minutes / 60).toFixed(1);
  const topLocations = stats?.by_location?.slice(0, 5) ?? [];
  const topActivities = stats?.by_activity?.slice(0, 5) ?? [];

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={16} className="text-status-success" />
            <span className="text-xs text-text-muted">Total Sessions</span>
          </div>
          <p className="text-2xl font-bold text-text-primary">{totals.total_sessions}</p>
        </div>
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={16} className="text-status-info" />
            <span className="text-xs text-text-muted">Total Time</span>
          </div>
          <p className="text-2xl font-bold text-text-primary">{totalHours}h</p>
        </div>
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Sun size={16} className="text-status-warning" />
            <span className="text-xs text-text-muted">Avg Session</span>
          </div>
          <p className="text-2xl font-bold text-text-primary">{fmtDuration(totals.avg_minutes)}</p>
        </div>
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <div className="flex items-center gap-2 mb-2">
            <MapPin size={16} className="text-accent" />
            <span className="text-xs text-text-muted">Locations</span>
          </div>
          <p className="text-2xl font-bold text-text-primary">{topLocations.length}</p>
        </div>
      </div>

      {/* Top locations & activities */}
      <div className="grid grid-cols-1 gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
            <MapPin size={14} className="text-accent" />
            Top Locations
          </h3>
          {topLocations.length === 0 ? (
            <p className="text-text-muted text-sm">No data yet</p>
          ) : (
            <div className="space-y-2">
              {topLocations.map((loc) => (
                <div key={loc.location} className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">{loc.location}</span>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span>{loc.sessions} sessions</span>
                    <span className="font-medium text-text-primary">{fmtDuration(loc.total_minutes)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-bg-card rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
            <Activity size={14} className="text-status-success" />
            Top Activities
          </h3>
          {topActivities.length === 0 ? (
            <p className="text-text-muted text-sm">No data yet</p>
          ) : (
            <div className="space-y-2">
              {topActivities.map((act) => (
                <div key={act.activity} className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">{act.activity}</span>
                  <div className="flex items-center gap-3 text-xs text-text-muted">
                    <span>{act.sessions} sessions</span>
                    <span className="font-medium text-text-primary">{fmtDuration(act.total_minutes)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick tips */}
      {totals.total_sessions === 0 && (
        <div className="bg-bg-card rounded-lg border border-border p-6 text-center">
          <Sun size={48} className="mx-auto mb-3 text-status-warning opacity-50" />
          <h3 className="text-text-primary font-medium mb-1">Start tracking outdoor time!</h3>
          <p className="text-text-muted text-sm">
            Go to the Data tab to log your first outdoor session.
          </p>
        </div>
      )}
    </div>
  );
}
