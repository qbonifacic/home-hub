import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { OutdoorStats, Filters, SavedOptions } from './OutdoorPage.tsx';
import FilterBar from './FilterBar.tsx';

interface Props {
  stats: OutdoorStats | null;
  filters: Filters;
  setFilters: (f: Filters) => void;
  options: SavedOptions;
  loading: boolean;
}

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#a855f7', '#ef4444', '#06b6d4', '#f97316', '#ec4899', '#84cc16', '#6366f1'];

const tooltipStyle = {
  backgroundColor: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  fontSize: '12px',
};

export default function ChartsTab({ stats, filters, setFilters, options, loading }: Props) {
  if (loading) {
    return <div className="text-text-muted text-sm py-8 text-center">Loading...</div>;
  }

  if (!stats || stats.totals.total_sessions === 0) {
    return (
      <div>
        <FilterBar filters={filters} setFilters={setFilters} options={options} />
        <div className="text-center py-12">
          <p className="text-text-muted text-sm">No data to chart yet. Log some outdoor sessions first!</p>
        </div>
      </div>
    );
  }

  const dailyData = stats.daily.map((d) => ({
    date: d.date.slice(5), // MM-DD
    minutes: Math.round(d.total_minutes),
  }));

  const weeklyData = stats.weekly.map((w) => ({
    week: w.week,
    minutes: Math.round(w.total_minutes),
  }));

  const locationData = stats.by_location.map((l) => ({
    name: l.location,
    value: Math.round(l.total_minutes),
  }));

  const activityData = stats.by_activity.map((a) => ({
    name: a.activity,
    minutes: Math.round(a.total_minutes),
  }));

  return (
    <div className="space-y-6">
      <FilterBar filters={filters} setFilters={setFilters} options={options} />

      {/* Daily Trend */}
      <div className="bg-bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Daily Outdoor Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={dailyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e2e8f0' }} />
            <Line
              type="monotone"
              dataKey="minutes"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ fill: '#22c55e', r: 3 }}
              activeDot={{ r: 5 }}
              name="Minutes"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Location Pie + Activity Bar side by side */}
      <div className="grid grid-cols-1 gap-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
        {/* Time by Location */}
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Time by Location</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={locationData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                dataKey="value"
                label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                labelLine={false}
              >
                {locationData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Time by Activity */}
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Time by Activity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={activityData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} width={100} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e2e8f0' }} />
              <Bar dataKey="minutes" name="Minutes" radius={[0, 4, 4, 0]} barSize={20}>
                {activityData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weekly Totals */}
      <div className="bg-bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Weekly Totals</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={weeklyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
            <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#e2e8f0' }} />
            <Bar dataKey="minutes" name="Minutes" fill="rgba(34,197,94,0.5)" stroke="#22c55e" strokeWidth={1} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
