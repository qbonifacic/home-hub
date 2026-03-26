import { X } from 'lucide-react';
import type { Filters, SavedOptions } from './OutdoorPage.tsx';

interface Props {
  filters: Filters;
  setFilters: (f: Filters) => void;
  options: SavedOptions;
}

export default function FilterBar({ filters, setFilters, options }: Props) {
  const hasFilters = Object.values(filters).some((v) => v !== '');

  const clearFilters = () =>
    setFilters({ start_date: '', end_date: '', location: '', activity: '', weather: '' });

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <input
        type="date"
        value={filters.start_date}
        onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
        className="px-2 py-1.5 bg-bg-card border border-border rounded text-text-primary text-xs focus:outline-none focus:border-accent"
        placeholder="From"
      />
      <input
        type="date"
        value={filters.end_date}
        onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
        className="px-2 py-1.5 bg-bg-card border border-border rounded text-text-primary text-xs focus:outline-none focus:border-accent"
        placeholder="To"
      />
      <select
        value={filters.location}
        onChange={(e) => setFilters({ ...filters, location: e.target.value })}
        className="px-2 py-1.5 bg-bg-card border border-border rounded text-text-primary text-xs focus:outline-none focus:border-accent"
      >
        <option value="">All Locations</option>
        {options.location.map((o) => (
          <option key={o.value} value={o.value}>{o.value}</option>
        ))}
      </select>
      <select
        value={filters.activity}
        onChange={(e) => setFilters({ ...filters, activity: e.target.value })}
        className="px-2 py-1.5 bg-bg-card border border-border rounded text-text-primary text-xs focus:outline-none focus:border-accent"
      >
        <option value="">All Activities</option>
        {options.activity.map((o) => (
          <option key={o.value} value={o.value}>{o.value}</option>
        ))}
      </select>
      <select
        value={filters.weather}
        onChange={(e) => setFilters({ ...filters, weather: e.target.value })}
        className="px-2 py-1.5 bg-bg-card border border-border rounded text-text-primary text-xs focus:outline-none focus:border-accent"
      >
        <option value="">All Weather</option>
        {options.weather.map((o) => (
          <option key={o.value} value={o.value}>{o.value}</option>
        ))}
      </select>
      {hasFilters && (
        <button
          onClick={clearFilters}
          className="flex items-center gap-1 px-2 py-1.5 bg-status-danger/10 text-status-danger rounded text-xs hover:bg-status-danger/20"
        >
          <X size={12} /> Clear
        </button>
      )}
    </div>
  );
}
