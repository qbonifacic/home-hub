import { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Settings,
  Trash2,
  Edit2,
  X,
  RefreshCw,
  Calendar,
  Clock,
  MapPin,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { CalendarEvent, CalendarSource } from '../../types.ts';

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.getFullYear(), d.getMonth(), diff);
}

function isoDate(d: Date): string {
  return d.toISOString().split('T')[0];
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function formatDayHeader(d: Date): string {
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function isSameDay(iso: string, date: Date): boolean {
  const d = new Date(iso);
  return d.getFullYear() === date.getFullYear() &&
    d.getMonth() === date.getMonth() &&
    d.getDate() === date.getDate();
}

const PROVIDERS = [
  { value: 'proton', label: 'Proton Calendar' },
  { value: 'google', label: 'Google Calendar' },
  { value: 'apple', label: 'Apple Calendar (iCloud)' },
  { value: 'generic', label: 'Other CalDAV' },
];

const DEFAULT_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#8b5cf6', '#14b8a6'];

export default function CalendarPage() {
  const showToast = useStore((s) => s.showToast);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [sources, setSources] = useState<CalendarSource[]>([]);
  const [weekOf, setWeekOf] = useState<Date>(getMonday(new Date()));
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Sources management
  const [showSources, setShowSources] = useState(false);
  const [showAddSource, setShowAddSource] = useState(false);
  const [editingSource, setEditingSource] = useState<CalendarSource | null>(null);

  // Source form
  const [srcProvider, setSrcProvider] = useState('proton');
  const [srcName, setSrcName] = useState('');
  const [srcUrl, setSrcUrl] = useState('');
  const [srcUser, setSrcUser] = useState('');
  const [srcPass, setSrcPass] = useState('');
  const [srcColor, setSrcColor] = useState('#6366f1');

  const weekOfStr = isoDate(weekOf);

  const loadEvents = useCallback(async () => {
    try {
      const start = new Date(weekOfStr + 'T00:00:00');
      const end = addDays(start, 7);
      const res = await api.get('/calendar/events', {
        params: {
          start: start.toISOString(),
          end: end.toISOString(),
        },
      });
      setEvents(res.data);
    } catch {
      // Silently fail - events are optional
    }
  }, [weekOfStr]);

  const loadSources = useCallback(async () => {
    try {
      const res = await api.get('/calendar/sources');
      setSources(res.data);
    } catch {
      // Silently fail
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadEvents(), loadSources()]);
    setLoading(false);
  }, [loadEvents, loadSources]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const refresh = async () => {
    setRefreshing(true);
    await loadEvents();
    setRefreshing(false);
    showToast('Calendar refreshed', 'success');
  };

  const prevWeek = () => setWeekOf(addDays(weekOf, -7));
  const nextWeek = () => setWeekOf(addDays(weekOf, 7));
  const thisWeek = () => setWeekOf(getMonday(new Date()));

  const resetSourceForm = () => {
    setSrcProvider('proton');
    setSrcName('');
    setSrcUrl('');
    setSrcUser('');
    setSrcPass('');
    setSrcColor('#6366f1');
    setEditingSource(null);
  };

  const openAddSource = () => {
    resetSourceForm();
    setShowAddSource(true);
  };

  const openEditSource = (src: CalendarSource) => {
    setEditingSource(src);
    setSrcProvider(src.provider);
    setSrcName(src.name);
    setSrcUrl(src.caldav_url);
    setSrcUser(src.username);
    setSrcPass('');
    setSrcColor(src.color);
    setShowAddSource(true);
  };

  const saveSource = async () => {
    if (!srcName.trim() || !srcUrl.trim() || !srcUser.trim()) {
      showToast('Please fill in all required fields', 'error');
      return;
    }
    try {
      if (editingSource) {
        const payload: Record<string, unknown> = {
          name: srcName.trim(),
          caldav_url: srcUrl.trim(),
          username: srcUser.trim(),
          color: srcColor,
        };
        if (srcPass) payload.password = srcPass;
        await api.put(`/calendar/sources/${editingSource.id}`, payload);
        showToast('Calendar source updated', 'success');
      } else {
        if (!srcPass) {
          showToast('Password is required for new sources', 'error');
          return;
        }
        await api.post('/calendar/sources', {
          provider: srcProvider,
          name: srcName.trim(),
          caldav_url: srcUrl.trim(),
          username: srcUser.trim(),
          password: srcPass,
          color: srcColor,
        });
        showToast('Calendar source added', 'success');
      }
      setShowAddSource(false);
      resetSourceForm();
      loadAll();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to save source';
      showToast(msg, 'error');
    }
  };

  const deleteSource = async (sourceId: number) => {
    try {
      await api.delete(`/calendar/sources/${sourceId}`);
      showToast('Calendar source removed', 'success');
      loadAll();
    } catch {
      showToast('Failed to delete source', 'error');
    }
  };

  const today = new Date();
  const todayStr = isoDate(today);

  // Build days array
  const days: Date[] = [];
  for (let i = 0; i < 7; i++) {
    days.push(addDays(weekOf, i));
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Calendar</h1>
          <p className="text-sm text-text-muted">
            {sources.length > 0
              ? `${sources.filter((s) => s.is_active).length} active source${sources.filter((s) => s.is_active).length !== 1 ? 's' : ''}`
              : 'No calendar sources configured'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            disabled={refreshing}
            className="p-2 rounded-lg bg-bg-card hover:bg-bg-hover text-text-muted transition-colors"
            title="Refresh events"
          >
            <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={() => setShowSources(!showSources)}
            className={`p-2 rounded-lg transition-colors ${
              showSources ? 'bg-accent text-white' : 'bg-bg-card hover:bg-bg-hover text-text-muted'
            }`}
            title="Manage sources"
          >
            <Settings size={18} />
          </button>
        </div>
      </div>

      {/* Sources Panel */}
      {showSources && (
        <div className="bg-bg-card rounded-lg border border-border p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-text-primary">Calendar Sources</h2>
            <button
              onClick={openAddSource}
              className="flex items-center gap-1 px-3 py-1.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-xs font-medium"
            >
              <Plus size={14} />
              Add Source
            </button>
          </div>

          {sources.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">
              No calendar sources configured. Add a CalDAV source to see your events.
            </p>
          ) : (
            <div className="space-y-2">
              {sources.map((src) => (
                <div
                  key={src.id}
                  className="flex items-center justify-between bg-bg-input rounded-lg px-3 py-2.5"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: src.color }}
                    />
                    <div>
                      <p className="text-sm font-medium text-text-primary">{src.name}</p>
                      <p className="text-xs text-text-muted capitalize">{src.provider}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full ${
                        src.is_active
                          ? 'bg-status-success/20 text-status-success'
                          : 'bg-status-danger/20 text-status-danger'
                      }`}
                    >
                      {src.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <button
                      onClick={() => openEditSource(src)}
                      className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                    >
                      <Edit2 size={13} />
                    </button>
                    <button
                      onClick={() => deleteSource(src.id)}
                      className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Week Navigation */}
      <div className="flex items-center gap-2">
        <button onClick={prevWeek} className="p-2 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted">
          <ChevronLeft size={18} />
        </button>
        <h2 className="text-lg font-semibold text-text-primary">
          Week of {formatDayHeader(weekOf)}
        </h2>
        <button onClick={nextWeek} className="p-2 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted">
          <ChevronRight size={18} />
        </button>
        <button onClick={thisWeek} className="px-3 py-1 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted text-xs">
          Today
        </button>
      </div>

      {/* Week View */}
      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading calendar...</div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {days.map((day) => {
            const dayEvents = events
              .filter((e) => isSameDay(e.start, day))
              .sort((a, b) => {
                if (a.all_day && !b.all_day) return -1;
                if (!a.all_day && b.all_day) return 1;
                return new Date(a.start).getTime() - new Date(b.start).getTime();
              });
            const isToday = isoDate(day) === todayStr;

            return (
              <div
                key={isoDate(day)}
                className={`bg-bg-card rounded-lg border p-4 ${
                  isToday ? 'border-accent' : 'border-border'
                }`}
              >
                <h3 className={`font-semibold text-sm mb-3 ${isToday ? 'text-accent' : 'text-text-primary'}`}>
                  {formatDayHeader(day)}
                  {isToday && (
                    <span className="ml-2 text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">Today</span>
                  )}
                </h3>

                {dayEvents.length === 0 ? (
                  <p className="text-text-muted text-xs italic">No events</p>
                ) : (
                  <div className="space-y-2">
                    {dayEvents.map((event, idx) => (
                      <div
                        key={`${event.uid}-${idx}`}
                        className="flex items-start gap-3 bg-bg-input rounded-md px-3 py-2"
                      >
                        <div
                          className="w-1 h-full min-h-[2rem] rounded-full shrink-0 mt-0.5"
                          style={{ backgroundColor: event.source_color }}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-text-primary truncate">
                            {event.summary}
                          </p>
                          <div className="flex items-center gap-3 mt-1">
                            {event.all_day ? (
                              <span className="text-xs text-text-muted flex items-center gap-1">
                                <Calendar size={11} />
                                All day
                              </span>
                            ) : (
                              <span className="text-xs text-text-muted flex items-center gap-1">
                                <Clock size={11} />
                                {formatTime(event.start)}
                                {event.end && ` - ${formatTime(event.end)}`}
                              </span>
                            )}
                            {event.location && (
                              <span className="text-xs text-text-muted flex items-center gap-1 truncate">
                                <MapPin size={11} />
                                {event.location}
                              </span>
                            )}
                            <span
                              className="text-[10px] px-1.5 py-0.5 rounded"
                              style={{
                                backgroundColor: event.source_color + '30',
                                color: event.source_color,
                              }}
                            >
                              {event.source_name}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add/Edit Source Modal */}
      {showAddSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editingSource ? 'Edit Calendar Source' : 'Add Calendar Source'}
              </h3>
              <button
                onClick={() => { setShowAddSource(false); resetSourceForm(); }}
                className="p-1 rounded hover:bg-bg-hover text-text-muted"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              {!editingSource && (
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Provider</label>
                  <select
                    value={srcProvider}
                    onChange={(e) => setSrcProvider(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Name *</label>
                <input
                  type="text"
                  value={srcName}
                  onChange={(e) => setSrcName(e.target.value)}
                  placeholder="e.g. Work Calendar"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">CalDAV URL *</label>
                <input
                  type="url"
                  value={srcUrl}
                  onChange={(e) => setSrcUrl(e.target.value)}
                  placeholder="https://calendar.proton.me/api/calendars/..."
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Username *</label>
                <input
                  type="text"
                  value={srcUser}
                  onChange={(e) => setSrcUser(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Password {editingSource ? '(leave blank to keep current)' : '*'}
                </label>
                <input
                  type="password"
                  value={srcPass}
                  onChange={(e) => setSrcPass(e.target.value)}
                  placeholder={editingSource ? '********' : 'App password or CalDAV password'}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Color</label>
                <div className="flex gap-2 flex-wrap">
                  {DEFAULT_COLORS.map((c) => (
                    <button
                      key={c}
                      onClick={() => setSrcColor(c)}
                      className={`w-8 h-8 rounded-full transition-all ${
                        srcColor === c ? 'ring-2 ring-white ring-offset-2 ring-offset-bg-card scale-110' : 'hover:scale-105'
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => { setShowAddSource(false); resetSourceForm(); }}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSource}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover"
                >
                  {editingSource ? 'Update' : 'Add Source'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
