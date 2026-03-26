import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Trash2,
  Edit2,
  X,
  CheckCircle2,
  Wrench,
  Home,
  ChevronDown,
  ChevronRight,
  Clock,
  DollarSign,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { Appliance, MaintenanceTask } from '../../types.ts';

const APPLIANCE_CATEGORIES = ['Kitchen', 'HVAC', 'Plumbing', 'Electrical', 'Outdoor', 'Other'];
const CATEGORY_ICONS: Record<string, string> = {
  Kitchen: '🍳',
  HVAC: '🌡️',
  Plumbing: '🔧',
  Electrical: '⚡',
  Outdoor: '🌿',
  Other: '🏠',
};

const FREQUENCIES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'semi_annual', label: 'Semi-Annual' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'one_time', label: 'One-time' },
];

function daysUntilDue(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(dateStr + 'T00:00:00');
  return Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function dueBadge(dateStr: string | null): { text: string; className: string } | null {
  const days = daysUntilDue(dateStr);
  if (days === null) return null;
  if (days < 0) return { text: `Overdue ${Math.abs(days)}d`, className: 'bg-status-danger/20 text-status-danger' };
  if (days === 0) return { text: 'Due today', className: 'bg-status-warning/20 text-status-warning' };
  if (days <= 7) return { text: `${days}d left`, className: 'bg-status-warning/20 text-status-warning' };
  if (days <= 30) return { text: `${days}d left`, className: 'bg-status-info/20 text-status-info' };
  return { text: `${days}d left`, className: 'bg-bg-input text-text-muted' };
}

export default function HomePage() {
  const showToast = useStore((s) => s.showToast);
  const [tab, setTab] = useState<'tasks' | 'appliances'>('tasks');
  const [appliances, setAppliances] = useState<Appliance[]>([]);
  const [tasks, setTasks] = useState<MaintenanceTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedAppliance, setExpandedAppliance] = useState<number | null>(null);

  // Appliance modal
  const [showAppModal, setShowAppModal] = useState(false);
  const [editingApp, setEditingApp] = useState<Appliance | null>(null);
  const [appName, setAppName] = useState('');
  const [appCategory, setAppCategory] = useState('Kitchen');
  const [appBrand, setAppBrand] = useState('');
  const [appModel, setAppModel] = useState('');
  const [appSerial, setAppSerial] = useState('');
  const [appPurchaseDate, setAppPurchaseDate] = useState('');
  const [appWarranty, setAppWarranty] = useState('');
  const [appLocation, setAppLocation] = useState('');
  const [appNotes, setAppNotes] = useState('');

  // Task modal
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [editingTask, setEditingTask] = useState<MaintenanceTask | null>(null);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskAppId, setTaskAppId] = useState<number | null>(null);
  const [taskFrequency, setTaskFrequency] = useState('quarterly');
  const [taskNextDue, setTaskNextDue] = useState('');
  const [taskCost, setTaskCost] = useState('');
  const [taskVendor, setTaskVendor] = useState('');

  // Complete modal
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [completingTask, setCompletingTask] = useState<MaintenanceTask | null>(null);
  const [completeNotes, setCompleteNotes] = useState('');
  const [completeCost, setCompleteCost] = useState('');

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [appRes, taskRes] = await Promise.all([
        api.get('/home/appliances'),
        api.get('/home/tasks'),
      ]);
      setAppliances(appRes.data);
      setTasks(taskRes.data);
    } catch {
      showToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // ── Appliance CRUD ───────────────────────────────
  const resetAppForm = () => {
    setAppName(''); setAppCategory('Kitchen'); setAppBrand(''); setAppModel('');
    setAppSerial(''); setAppPurchaseDate(''); setAppWarranty(''); setAppLocation('');
    setAppNotes(''); setEditingApp(null);
  };

  const openAddApp = () => { resetAppForm(); setShowAppModal(true); };

  const openEditApp = (app: Appliance) => {
    setEditingApp(app);
    setAppName(app.name);
    setAppCategory(app.category || 'Kitchen');
    setAppBrand(app.brand || '');
    setAppModel(app.model_number || '');
    setAppSerial(app.serial_number || '');
    setAppPurchaseDate(app.purchase_date || '');
    setAppWarranty(app.warranty_until || '');
    setAppLocation(app.location || '');
    setAppNotes(app.notes || '');
    setShowAppModal(true);
  };

  const saveAppliance = async () => {
    if (!appName.trim()) return;
    try {
      const payload: Record<string, unknown> = {
        name: appName.trim(),
        category: appCategory || null,
        brand: appBrand.trim() || null,
        model_number: appModel.trim() || null,
        serial_number: appSerial.trim() || null,
        purchase_date: appPurchaseDate || null,
        warranty_until: appWarranty || null,
        location: appLocation.trim() || null,
        notes: appNotes.trim() || null,
      };
      if (editingApp) {
        await api.put(`/home/appliances/${editingApp.id}`, payload);
        showToast('Appliance updated', 'success');
      } else {
        await api.post('/home/appliances', payload);
        showToast('Appliance added', 'success');
      }
      setShowAppModal(false);
      resetAppForm();
      loadAll();
    } catch {
      showToast('Failed to save appliance', 'error');
    }
  };

  const deleteAppliance = async (id: number) => {
    try {
      await api.delete(`/home/appliances/${id}`);
      showToast('Appliance removed', 'success');
      loadAll();
    } catch {
      showToast('Failed to delete appliance', 'error');
    }
  };

  // ── Task CRUD ───────────────────────────────────
  const resetTaskForm = () => {
    setTaskTitle(''); setTaskDesc(''); setTaskAppId(null); setTaskFrequency('quarterly');
    setTaskNextDue(''); setTaskCost(''); setTaskVendor(''); setEditingTask(null);
  };

  const openAddTask = (applianceId?: number) => {
    resetTaskForm();
    if (applianceId) setTaskAppId(applianceId);
    setShowTaskModal(true);
  };

  const openEditTask = (task: MaintenanceTask) => {
    setEditingTask(task);
    setTaskTitle(task.title);
    setTaskDesc(task.description || '');
    setTaskAppId(task.appliance_id || null);
    setTaskFrequency(task.frequency || 'quarterly');
    setTaskNextDue(task.next_due || '');
    setTaskCost(task.estimated_cost ? String(task.estimated_cost) : '');
    setTaskVendor(task.vendor || '');
    setShowTaskModal(true);
  };

  const saveTask = async () => {
    if (!taskTitle.trim()) return;
    try {
      const payload: Record<string, unknown> = {
        title: taskTitle.trim(),
        description: taskDesc.trim() || null,
        appliance_id: taskAppId || null,
        frequency: taskFrequency || null,
        next_due: taskNextDue || null,
        estimated_cost: taskCost ? parseFloat(taskCost) : null,
        vendor: taskVendor.trim() || null,
      };
      if (editingTask) {
        await api.put(`/home/tasks/${editingTask.id}`, payload);
        showToast('Task updated', 'success');
      } else {
        await api.post('/home/tasks', payload);
        showToast('Task created', 'success');
      }
      setShowTaskModal(false);
      resetTaskForm();
      loadAll();
    } catch {
      showToast('Failed to save task', 'error');
    }
  };

  const deleteTask = async (id: number) => {
    try {
      await api.delete(`/home/tasks/${id}`);
      showToast('Task removed', 'success');
      loadAll();
    } catch {
      showToast('Failed to delete task', 'error');
    }
  };

  // ── Complete Task ────────────────────────────────
  const openCompleteModal = (task: MaintenanceTask) => {
    setCompletingTask(task);
    setCompleteNotes('');
    setCompleteCost(task.estimated_cost ? String(task.estimated_cost) : '');
    setShowCompleteModal(true);
  };

  const completeTask = async () => {
    if (!completingTask) return;
    try {
      await api.post(`/home/tasks/${completingTask.id}/complete`, null, {
        params: {
          notes: completeNotes.trim() || undefined,
          cost: completeCost ? parseFloat(completeCost) : undefined,
        },
      });
      showToast('Task completed! Next due date set.', 'success');
      setShowCompleteModal(false);
      loadAll();
    } catch {
      showToast('Failed to complete task', 'error');
    }
  };

  // Computed
  const overdueCount = tasks.filter((t) => {
    const d = daysUntilDue(t.next_due);
    return d !== null && d < 0;
  }).length;

  const dueSoonCount = tasks.filter((t) => {
    const d = daysUntilDue(t.next_due);
    return d !== null && d >= 0 && d <= 14;
  }).length;

  // Sort tasks: overdue first, then by due date
  const sortedTasks = [...tasks].sort((a, b) => {
    const ad = daysUntilDue(a.next_due);
    const bd = daysUntilDue(b.next_due);
    if (ad === null && bd === null) return a.title.localeCompare(b.title);
    if (ad === null) return 1;
    if (bd === null) return -1;
    return ad - bd;
  });

  // Group appliances by category
  const appsByCategory: Record<string, Appliance[]> = {};
  for (const app of appliances) {
    const cat = app.category || 'Other';
    if (!appsByCategory[cat]) appsByCategory[cat] = [];
    appsByCategory[cat].push(app);
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Home Maintenance</h1>
          <p className="text-sm text-text-muted">
            {appliances.length} appliance{appliances.length !== 1 ? 's' : ''} &middot;{' '}
            {tasks.length} task{tasks.length !== 1 ? 's' : ''}
            {overdueCount > 0 && (
              <span className="text-status-danger ml-2">{overdueCount} overdue</span>
            )}
            {dueSoonCount > 0 && (
              <span className="text-status-warning ml-2">{dueSoonCount} due soon</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => openAddTask()}
            className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            Add Task
          </button>
          <button
            onClick={openAddApp}
            className="flex items-center gap-1.5 px-3 py-2 bg-bg-card hover:bg-bg-hover text-text-secondary rounded-lg text-sm font-medium transition-colors border border-border"
          >
            <Plus size={16} />
            Add Appliance
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-bg-card rounded-lg p-1 border border-border">
        <button
          onClick={() => setTab('tasks')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'tasks' ? 'bg-accent text-white' : 'text-text-muted hover:text-text-primary'
          }`}
        >
          <Wrench size={14} className="inline mr-1.5" />
          Tasks
          {(overdueCount + dueSoonCount) > 0 && (
            <span className="ml-1.5 text-xs bg-white/20 px-1.5 py-0.5 rounded-full">
              {overdueCount + dueSoonCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setTab('appliances')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === 'appliances' ? 'bg-accent text-white' : 'text-text-muted hover:text-text-primary'
          }`}
        >
          <Home size={14} className="inline mr-1.5" />
          Appliances ({appliances.length})
        </button>
      </div>

      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading...</div>
      ) : tab === 'tasks' ? (
        /* ── Tasks Tab ──────────────────────────── */
        <div className="space-y-2">
          {sortedTasks.length === 0 ? (
            <div className="bg-bg-card rounded-lg border border-border p-8 text-center">
              <Wrench className="mx-auto text-text-muted mb-3" size={36} />
              <p className="text-text-secondary font-medium">No maintenance tasks</p>
              <p className="text-text-muted text-sm mt-1">Add tasks to track home maintenance schedules</p>
            </div>
          ) : (
            sortedTasks.map((task) => {
              const badge = dueBadge(task.next_due);
              const applianceName = appliances.find((a) => a.id === task.appliance_id)?.name;
              return (
                <div
                  key={task.id}
                  className="bg-bg-card rounded-lg border border-border p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-text-primary truncate">{task.title}</p>
                        {badge && (
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${badge.className}`}>
                            {badge.text}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
                        {applianceName && (
                          <span className="flex items-center gap-1">
                            <Home size={11} />
                            {applianceName}
                          </span>
                        )}
                        {task.frequency && (
                          <span className="flex items-center gap-1">
                            <Clock size={11} />
                            {task.frequency.replace('_', '-')}
                          </span>
                        )}
                        {task.estimated_cost && (
                          <span className="flex items-center gap-1">
                            <DollarSign size={11} />
                            ~${task.estimated_cost}
                          </span>
                        )}
                        {task.vendor && (
                          <span>{task.vendor}</span>
                        )}
                      </div>
                      {task.description && (
                        <p className="text-xs text-text-muted mt-1.5">{task.description}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-1 shrink-0 ml-3">
                      <button
                        onClick={() => openCompleteModal(task)}
                        className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-status-success"
                        title="Mark complete"
                      >
                        <CheckCircle2 size={16} />
                      </button>
                      <button
                        onClick={() => openEditTask(task)}
                        className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => deleteTask(task.id)}
                        className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* ── Appliances Tab ──────────────────────── */
        <div className="space-y-4">
          {Object.keys(appsByCategory).length === 0 ? (
            <div className="bg-bg-card rounded-lg border border-border p-8 text-center">
              <Home className="mx-auto text-text-muted mb-3" size={36} />
              <p className="text-text-secondary font-medium">No appliances registered</p>
              <p className="text-text-muted text-sm mt-1">Add your home appliances to track maintenance</p>
            </div>
          ) : (
            Object.entries(appsByCategory).map(([category, apps]) => (
              <div key={category} className="bg-bg-card rounded-lg border border-border overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <span>{CATEGORY_ICONS[category] || '🏠'}</span>
                    {category}
                    <span className="text-xs text-text-muted font-normal">({apps.length})</span>
                  </h2>
                </div>

                <div className="divide-y divide-border">
                  {apps.map((app) => {
                    const appTasks = tasks.filter((t) => t.appliance_id === app.id);
                    const isExpanded = expandedAppliance === app.id;

                    return (
                      <div key={app.id}>
                        <div
                          className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-bg-hover/50"
                          onClick={() => setExpandedAppliance(isExpanded ? null : app.id)}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            {isExpanded ? <ChevronDown size={14} className="text-text-muted shrink-0" /> : <ChevronRight size={14} className="text-text-muted shrink-0" />}
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-text-primary truncate">{app.name}</p>
                              <div className="flex items-center gap-2 text-xs text-text-muted">
                                {app.brand && <span>{app.brand}</span>}
                                {app.location && <span>{app.location}</span>}
                                {appTasks.length > 0 && (
                                  <span className="text-accent">{appTasks.length} task{appTasks.length !== 1 ? 's' : ''}</span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => openAddTask(app.id)}
                              className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                              title="Add task"
                            >
                              <Plus size={14} />
                            </button>
                            <button
                              onClick={() => openEditApp(app)}
                              className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              onClick={() => deleteAppliance(app.id)}
                              className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="px-4 pb-3 pl-10 space-y-2">
                            {app.model_number && (
                              <p className="text-xs text-text-muted">Model: {app.model_number}</p>
                            )}
                            {app.serial_number && (
                              <p className="text-xs text-text-muted">Serial: {app.serial_number}</p>
                            )}
                            {app.purchase_date && (
                              <p className="text-xs text-text-muted">Purchased: {app.purchase_date}</p>
                            )}
                            {app.warranty_until && (
                              <p className="text-xs text-text-muted">Warranty: {app.warranty_until}</p>
                            )}
                            {app.notes && (
                              <p className="text-xs text-text-muted">{app.notes}</p>
                            )}
                            {appTasks.length > 0 && (
                              <div className="mt-2 space-y-1">
                                <p className="text-xs font-medium text-text-secondary">Maintenance Tasks:</p>
                                {appTasks.map((t) => {
                                  const badge = dueBadge(t.next_due);
                                  return (
                                    <div key={t.id} className="flex items-center justify-between bg-bg-input rounded px-2 py-1.5">
                                      <span className="text-xs text-text-primary">{t.title}</span>
                                      {badge && (
                                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badge.className}`}>
                                          {badge.text}
                                        </span>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Add/Edit Appliance Modal */}
      {showAppModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editingApp ? 'Edit Appliance' : 'Add Appliance'}
              </h3>
              <button onClick={() => { setShowAppModal(false); resetAppForm(); }} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Name *</label>
                <input type="text" value={appName} onChange={(e) => setAppName(e.target.value)}
                  placeholder="e.g. Samsung Refrigerator"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" autoFocus />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                <select value={appCategory} onChange={(e) => setAppCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent">
                  {APPLIANCE_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{CATEGORY_ICONS[c]} {c}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Brand</label>
                  <input type="text" value={appBrand} onChange={(e) => setAppBrand(e.target.value)}
                    placeholder="e.g. Samsung"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Location</label>
                  <input type="text" value={appLocation} onChange={(e) => setAppLocation(e.target.value)}
                    placeholder="e.g. Kitchen"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Model #</label>
                  <input type="text" value={appModel} onChange={(e) => setAppModel(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Serial #</label>
                  <input type="text" value={appSerial} onChange={(e) => setAppSerial(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Purchase Date</label>
                  <input type="date" value={appPurchaseDate} onChange={(e) => setAppPurchaseDate(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Warranty Until</label>
                  <input type="date" value={appWarranty} onChange={(e) => setAppWarranty(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Notes</label>
                <textarea value={appNotes} onChange={(e) => setAppNotes(e.target.value)} rows={2}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent resize-none" />
              </div>

              <div className="flex gap-3 pt-2">
                <button onClick={() => { setShowAppModal(false); resetAppForm(); }}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover">Cancel</button>
                <button onClick={saveAppliance} disabled={!appName.trim()}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50">
                  {editingApp ? 'Update' : 'Add'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Task Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editingTask ? 'Edit Task' : 'Add Maintenance Task'}
              </h3>
              <button onClick={() => { setShowTaskModal(false); resetTaskForm(); }} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Title *</label>
                <input type="text" value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)}
                  placeholder="e.g. Replace HVAC filter"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" autoFocus />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Appliance</label>
                <select value={taskAppId ?? ''} onChange={(e) => setTaskAppId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent">
                  <option value="">None (general)</option>
                  {appliances.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                <textarea value={taskDesc} onChange={(e) => setTaskDesc(e.target.value)} rows={2}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent resize-none" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Frequency</label>
                  <select value={taskFrequency} onChange={(e) => setTaskFrequency(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent">
                    {FREQUENCIES.map((f) => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Next Due</label>
                  <input type="date" value={taskNextDue} onChange={(e) => setTaskNextDue(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Est. Cost ($)</label>
                  <input type="number" value={taskCost} onChange={(e) => setTaskCost(e.target.value)}
                    placeholder="0.00" step="0.01"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Vendor</label>
                  <input type="text" value={taskVendor} onChange={(e) => setTaskVendor(e.target.value)}
                    placeholder="e.g. Home Depot"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button onClick={() => { setShowTaskModal(false); resetTaskForm(); }}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover">Cancel</button>
                <button onClick={saveTask} disabled={!taskTitle.trim()}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50">
                  {editingTask ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Complete Task Modal */}
      {showCompleteModal && completingTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Complete Task</h3>
              <button onClick={() => setShowCompleteModal(false)} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <p className="text-sm text-text-secondary mb-4">
              Mark &quot;{completingTask.title}&quot; as done?
              {completingTask.frequency && completingTask.frequency !== 'one_time' && (
                <span className="block text-xs text-text-muted mt-1">
                  Next due date will be auto-calculated based on {completingTask.frequency.replace('_', '-')} frequency.
                </span>
              )}
            </p>

            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Cost ($)</label>
                <input type="number" value={completeCost} onChange={(e) => setCompleteCost(e.target.value)}
                  placeholder="Actual cost" step="0.01"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">Notes</label>
                <input type="text" value={completeNotes} onChange={(e) => setCompleteNotes(e.target.value)}
                  placeholder="Optional notes"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent" />
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setShowCompleteModal(false)}
                className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover">Cancel</button>
              <button onClick={completeTask}
                className="flex-1 px-4 py-2 bg-status-success text-white rounded-lg text-sm font-medium hover:bg-status-success/80">
                Complete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
