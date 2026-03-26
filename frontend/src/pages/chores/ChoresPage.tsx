import { useEffect, useState, useCallback } from 'react';
import {
  Plus,
  CheckCircle,
  Pencil,
  Trash2,
  Filter,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { Chore } from '../../types.ts';
import ChoreForm from './ChoreForm.tsx';

type FilterTab = 'all' | 'overdue' | 'today' | 'upcoming';

function getDueStatus(nextDue: string | null): 'overdue' | 'today' | 'upcoming' | 'none' {
  if (!nextDue) return 'none';
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(nextDue);
  due.setHours(0, 0, 0, 0);
  if (due < today) return 'overdue';
  if (due.getTime() === today.getTime()) return 'today';
  return 'upcoming';
}

function formatDueDate(nextDue: string | null): string {
  if (!nextDue) return 'No due date';
  const date = new Date(nextDue);
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

function frequencyLabel(freq: string): string {
  const labels: Record<string, string> = {
    daily: 'Daily',
    every_other_day: 'Every Other Day',
    weekly: 'Weekly',
    biweekly: 'Biweekly',
    monthly: 'Monthly',
    quarterly: 'Quarterly',
    yearly: 'Yearly',
    one_time: 'One Time',
  };
  return labels[freq] ?? freq;
}

export default function ChoresPage() {
  const showToast = useStore((s) => s.showToast);
  const [chores, setChores] = useState<Chore[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all');
  const [formOpen, setFormOpen] = useState(false);
  const [editingChore, setEditingChore] = useState<Chore | null>(null);

  const fetchChores = useCallback(async () => {
    try {
      const res = await api.get('/chores');
      setChores(res.data);
    } catch {
      showToast('Failed to load chores', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchChores();
  }, [fetchChores]);

  const handleComplete = async (id: number) => {
    try {
      await api.post(`/chores/${id}/complete`);
      showToast('Chore marked as done!', 'success');
      fetchChores();
    } catch {
      showToast('Failed to complete chore', 'error');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this chore?')) return;
    try {
      await api.delete(`/chores/${id}`);
      showToast('Chore deleted', 'success');
      fetchChores();
    } catch {
      showToast('Failed to delete chore', 'error');
    }
  };

  const openEdit = (chore: Chore) => {
    setEditingChore(chore);
    setFormOpen(true);
  };

  const openCreate = () => {
    setEditingChore(null);
    setFormOpen(true);
  };

  const filteredChores = chores.filter((chore) => {
    if (!chore.is_active) return false;
    if (activeFilter === 'all') return true;
    const status = getDueStatus(chore.next_due);
    return status === activeFilter;
  });

  const filterTabs: { key: FilterTab; label: string; count: number }[] = [
    { key: 'all', label: 'All', count: chores.filter((c) => c.is_active).length },
    {
      key: 'overdue',
      label: 'Overdue',
      count: chores.filter((c) => c.is_active && getDueStatus(c.next_due) === 'overdue').length,
    },
    {
      key: 'today',
      label: 'Due Today',
      count: chores.filter((c) => c.is_active && getDueStatus(c.next_due) === 'today').length,
    },
    {
      key: 'upcoming',
      label: 'Upcoming',
      count: chores.filter((c) => c.is_active && getDueStatus(c.next_due) === 'upcoming').length,
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-text-muted text-sm">Loading chores...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Chores</h1>
          <p className="text-text-secondary text-sm mt-1">Manage household tasks</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-accent hover:bg-accent-hover text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          <span className="hidden sm:inline">Add Chore</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 bg-bg-card rounded-lg p-1 border border-border overflow-x-auto">
        <Filter size={14} className="text-text-muted ml-2 shrink-0" />
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveFilter(tab.key)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
              activeFilter === tab.key
                ? 'bg-accent text-white'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className="ml-1.5 opacity-75">({tab.count})</span>
            )}
          </button>
        ))}
      </div>

      {/* Chore List */}
      {filteredChores.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-muted text-sm">
            {activeFilter === 'all'
              ? 'No chores yet. Add one to get started!'
              : `No ${activeFilter} chores`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredChores.map((chore) => {
            const dueStatus = getDueStatus(chore.next_due);
            const dueColorMap = {
              overdue: 'text-status-danger',
              today: 'text-status-warning',
              upcoming: 'text-status-success',
              none: 'text-text-muted',
            };

            return (
              <div
                key={chore.id}
                className="bg-bg-card rounded-lg p-4 border border-border flex flex-col sm:flex-row sm:items-center gap-3"
              >
                {/* Chore Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-semibold text-text-primary">
                      {chore.title}
                    </h3>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent/20 text-accent font-medium">
                      {frequencyLabel(chore.frequency)}
                    </span>
                    {chore.assigned_to && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-status-info/20 text-status-info font-medium capitalize">
                        {chore.assigned_to}
                      </span>
                    )}
                    {chore.category && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-bg-hover text-text-muted font-medium">
                        {chore.category}
                      </span>
                    )}
                  </div>
                  <p className={`text-xs mt-1 ${dueColorMap[dueStatus]}`}>
                    {dueStatus === 'overdue' && 'Overdue: '}
                    {dueStatus === 'today' && 'Due: '}
                    {formatDueDate(chore.next_due)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleComplete(chore.id)}
                    className="flex items-center gap-1.5 bg-status-success/15 text-status-success hover:bg-status-success/25 px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
                    title="Mark as done"
                  >
                    <CheckCircle size={14} />
                    <span className="hidden sm:inline">Done</span>
                  </button>
                  <button
                    onClick={() => openEdit(chore)}
                    className="p-1.5 text-text-muted hover:text-accent hover:bg-bg-hover rounded-md transition-colors"
                    title="Edit"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(chore.id)}
                    className="p-1.5 text-text-muted hover:text-status-danger hover:bg-bg-hover rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Chore Form Modal */}
      <ChoreForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        onSaved={fetchChores}
        chore={editingChore}
      />
    </div>
  );
}
