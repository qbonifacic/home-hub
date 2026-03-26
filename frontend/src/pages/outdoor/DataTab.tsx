import { useState } from 'react';
import { Plus, Edit2, Trash2, X } from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { OutdoorSession, SavedOptions, Filters } from './OutdoorPage.tsx';
import FilterBar from './FilterBar.tsx';

interface Props {
  sessions: OutdoorSession[];
  options: SavedOptions;
  filters: Filters;
  setFilters: (f: Filters) => void;
  onRefresh: () => void;
  loading: boolean;
}

function fmtDuration(min: number): string {
  if (min < 60) return `${Math.round(min)}m`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function DataTab({ sessions, options, filters, setFilters, onRefresh, loading }: Props) {
  const showToast = useStore((s) => s.showToast);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<OutdoorSession | null>(null);
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formStart, setFormStart] = useState('');
  const [formEnd, setFormEnd] = useState('');
  const [formLocation, setFormLocation] = useState('');
  const [formActivity, setFormActivity] = useState('');
  const [formWeather, setFormWeather] = useState('');
  const [formNotes, setFormNotes] = useState('');

  const resetForm = () => {
    setFormDate(new Date().toISOString().split('T')[0]);
    setFormStart('');
    setFormEnd('');
    setFormLocation('');
    setFormActivity('');
    setFormWeather('');
    setFormNotes('');
    setEditing(null);
  };

  const openCreate = () => {
    resetForm();
    setShowForm(true);
  };

  const openEdit = (s: OutdoorSession) => {
    setEditing(s);
    setFormDate(s.session_date);
    setFormStart(s.start_time);
    setFormEnd(s.end_time);
    setFormLocation(s.location);
    setFormActivity(s.activity || '');
    setFormWeather(s.weather || '');
    setFormNotes(s.notes || '');
    setShowForm(true);
  };

  const saveSession = async () => {
    if (!formDate || !formStart || !formEnd || !formLocation.trim()) {
      showToast('Date, start/end time, and location are required', 'error');
      return;
    }

    const payload = {
      session_date: formDate,
      start_time: formStart,
      end_time: formEnd,
      location: formLocation.trim(),
      activity: formActivity.trim() || null,
      weather: formWeather.trim() || null,
      notes: formNotes.trim() || null,
    };

    try {
      if (editing) {
        await api.put(`/outdoor/sessions/${editing.id}`, payload);
        showToast('Session updated', 'success');
      } else {
        await api.post('/outdoor/sessions', payload);
        showToast('Session logged!', 'success');
      }
      setShowForm(false);
      resetForm();
      onRefresh();
    } catch {
      showToast('Failed to save session', 'error');
    }
  };

  const deleteSession = async (id: number) => {
    try {
      await api.delete(`/outdoor/sessions/${id}`);
      showToast('Session deleted', 'success');
      onRefresh();
    } catch {
      showToast('Failed to delete session', 'error');
    }
  };

  return (
    <div>
      <FilterBar filters={filters} setFilters={setFilters} options={options} />

      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-text-muted">{sessions.length} sessions</span>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Log Session
        </button>
      </div>

      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading...</div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-muted text-sm">No sessions found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="bg-bg-card rounded-lg border border-border p-3 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-text-primary">{formatDate(s.session_date)}</span>
                  <span className="text-xs text-text-muted">{s.start_time} – {s.end_time}</span>
                  <span className="text-xs font-semibold text-status-success">{fmtDuration(s.duration_minutes)}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <span className="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded">{s.location}</span>
                  {s.activity && (
                    <span className="text-xs bg-status-success/10 text-status-success px-1.5 py-0.5 rounded">{s.activity}</span>
                  )}
                  {s.weather && (
                    <span className="text-xs bg-status-warning/10 text-status-warning px-1.5 py-0.5 rounded">{s.weather}</span>
                  )}
                  {s.source !== 'manual' && (
                    <span className="text-[10px] bg-bg-hover text-text-muted px-1 py-0.5 rounded">via {s.source}</span>
                  )}
                </div>
                {s.notes && <p className="text-xs text-text-muted mt-1">{s.notes}</p>}
              </div>
              <div className="flex items-center gap-1 ml-3">
                <button
                  onClick={() => openEdit(s)}
                  className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                >
                  <Edit2 size={14} />
                </button>
                <button
                  onClick={() => deleteSession(s.id)}
                  className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Log/Edit Session Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editing ? 'Edit Session' : 'Log Outdoor Session'}
              </h3>
              <button onClick={() => { setShowForm(false); resetForm(); }} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Date *</label>
                <input
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">Start Time *</label>
                  <input
                    type="time"
                    value={formStart}
                    onChange={(e) => setFormStart(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">End Time *</label>
                  <input
                    type="time"
                    value={formEnd}
                    onChange={(e) => setFormEnd(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Location *</label>
                <input
                  type="text"
                  value={formLocation}
                  onChange={(e) => setFormLocation(e.target.value)}
                  list="loc-options"
                  placeholder="e.g. Spring Canyon Park"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
                <datalist id="loc-options">
                  {options.location.map((o) => <option key={o.value} value={o.value} />)}
                </datalist>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Activity</label>
                <input
                  type="text"
                  value={formActivity}
                  onChange={(e) => setFormActivity(e.target.value)}
                  list="act-options"
                  placeholder="e.g. Playground, Bike ride"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
                <datalist id="act-options">
                  {options.activity.map((o) => <option key={o.value} value={o.value} />)}
                </datalist>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Weather</label>
                <input
                  type="text"
                  value={formWeather}
                  onChange={(e) => setFormWeather(e.target.value)}
                  list="weather-options"
                  placeholder="e.g. Sunny, Cloudy"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
                <datalist id="weather-options">
                  {options.weather.map((o) => <option key={o.value} value={o.value} />)}
                </datalist>
              </div>

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Notes</label>
                <textarea
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  rows={2}
                  placeholder="Optional notes..."
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent resize-none"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => { setShowForm(false); resetForm(); }}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSession}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover"
                >
                  {editing ? 'Update' : 'Log Session'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
