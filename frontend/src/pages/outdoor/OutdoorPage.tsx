import { useState, useEffect, useCallback } from 'react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import OverviewTab from './OverviewTab.tsx';
import ChartsTab from './ChartsTab.tsx';
import DataTab from './DataTab.tsx';

export interface OutdoorSession {
  id: number;
  session_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  location: string;
  activity: string | null;
  weather: string | null;
  notes: string | null;
  source: string;
  created_by: string | null;
  created_at: string;
}

export interface SavedOptions {
  location: { value: string; use_count: number }[];
  activity: { value: string; use_count: number }[];
  weather: { value: string; use_count: number }[];
}

export interface OutdoorStats {
  totals: { total_sessions: number; total_minutes: number; avg_minutes: number };
  by_location: { location: string; sessions: number; total_minutes: number }[];
  by_activity: { activity: string; sessions: number; total_minutes: number }[];
  daily: { date: string; total_minutes: number; sessions: number }[];
  weekly: { week: string; total_minutes: number; sessions: number }[];
  monthly: { month: string; total_minutes: number; sessions: number }[];
}

export interface Filters {
  start_date: string;
  end_date: string;
  location: string;
  activity: string;
  weather: string;
}

const tabs = ['Overview', 'Charts', 'Data'] as const;
type Tab = (typeof tabs)[number];

export default function OutdoorPage() {
  const showToast = useStore((s) => s.showToast);
  const [activeTab, setActiveTab] = useState<Tab>('Overview');
  const [sessions, setSessions] = useState<OutdoorSession[]>([]);
  const [stats, setStats] = useState<OutdoorStats | null>(null);
  const [options, setOptions] = useState<SavedOptions>({ location: [], activity: [], weather: [] });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>({
    start_date: '',
    end_date: '',
    location: '',
    activity: '',
    weather: '',
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.location) params.location = filters.location;
      if (filters.activity) params.activity = filters.activity;
      if (filters.weather) params.weather = filters.weather;

      const [sessRes, statsRes, optsRes] = await Promise.all([
        api.get('/outdoor/sessions', { params }),
        api.get('/outdoor/stats', { params }),
        api.get('/outdoor/options'),
      ]);
      setSessions(sessRes.data);
      setStats(statsRes.data);
      setOptions(optsRes.data);
    } catch {
      showToast('Failed to load outdoor data', 'error');
    } finally {
      setLoading(false);
    }
  }, [filters, showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Outside Time</h1>
          <p className="text-text-muted text-sm">Track kids' outdoor activities</p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 bg-bg-card rounded-lg p-1">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-accent text-white'
                : 'text-text-muted hover:text-text-secondary hover:bg-bg-hover'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <OverviewTab stats={stats} loading={loading} />
      )}
      {activeTab === 'Charts' && (
        <ChartsTab stats={stats} filters={filters} setFilters={setFilters} options={options} loading={loading} />
      )}
      {activeTab === 'Data' && (
        <DataTab
          sessions={sessions}
          options={options}
          filters={filters}
          setFilters={setFilters}
          onRefresh={fetchData}
          loading={loading}
        />
      )}
    </div>
  );
}
