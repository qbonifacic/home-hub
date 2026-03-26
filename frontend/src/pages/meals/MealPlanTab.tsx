import { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Sparkles,
  Trash2,
  Edit2,
  X,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { MealPlanWeek, MealPlan } from '../../types.ts';

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'] as const;
const MEAL_TYPE_ICONS: Record<string, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍿',
};

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.getFullYear(), d.getMonth(), diff);
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function isoDate(d: Date): string {
  return d.toISOString().split('T')[0];
}

export default function MealPlanTab() {
  const showToast = useStore((s) => s.showToast);
  const [weekData, setWeekData] = useState<MealPlanWeek | null>(null);
  const [weekOf, setWeekOf] = useState<Date>(getMonday(new Date()));
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Add meal modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [addDate, setAddDate] = useState('');
  const [addType, setAddType] = useState('dinner');
  const [addName, setAddName] = useState('');
  const [editingMeal, setEditingMeal] = useState<MealPlan | null>(null);

  // AI generate modal
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiPreferences, setAiPreferences] = useState('');

  const loadWeek = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/meals/week', { params: { week_of: isoDate(weekOf) } });
      setWeekData(res.data);
    } catch {
      showToast('Failed to load meal plan', 'error');
    } finally {
      setLoading(false);
    }
  }, [weekOf, showToast]);

  useEffect(() => {
    loadWeek();
  }, [loadWeek]);

  const prevWeek = () => {
    const d = new Date(weekOf);
    d.setDate(d.getDate() - 7);
    setWeekOf(d);
  };

  const nextWeek = () => {
    const d = new Date(weekOf);
    d.setDate(d.getDate() + 7);
    setWeekOf(d);
  };

  const thisWeek = () => setWeekOf(getMonday(new Date()));

  const openAddModal = (dateStr: string, mealType: string = 'dinner') => {
    setAddDate(dateStr);
    setAddType(mealType);
    setAddName('');
    setEditingMeal(null);
    setShowAddModal(true);
  };

  const openEditModal = (meal: MealPlan) => {
    setAddDate(meal.plan_date);
    setAddType(meal.meal_type);
    setAddName(meal.meal_name);
    setEditingMeal(meal);
    setShowAddModal(true);
  };

  const saveMeal = async () => {
    if (!addName.trim()) return;
    try {
      if (editingMeal) {
        await api.put(`/meals/${editingMeal.id}`, {
          meal_name: addName.trim(),
          meal_type: addType,
        });
        showToast('Meal updated', 'success');
      } else {
        await api.post('/meals', {
          plan_date: addDate,
          meal_type: addType,
          meal_name: addName.trim(),
        });
        showToast('Meal added', 'success');
      }
      setShowAddModal(false);
      loadWeek();
    } catch {
      showToast('Failed to save meal', 'error');
    }
  };

  const deleteMeal = async (mealId: number) => {
    try {
      await api.delete(`/meals/${mealId}`);
      showToast('Meal removed', 'success');
      loadWeek();
    } catch {
      showToast('Failed to delete meal', 'error');
    }
  };

  const generateWithAI = async () => {
    setGenerating(true);
    try {
      await api.post('/meals/generate', {
        start_date: isoDate(weekOf),
        preferences: aiPreferences || undefined,
        num_days: 7,
        meal_types: ['breakfast', 'lunch', 'dinner'],
      });
      showToast('AI meal plan generated!', 'success');
      setShowAIModal(false);
      loadWeek();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'AI generation failed';
      showToast(msg, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const today = new Date().toISOString().split('T')[0];
  const weekLabel = `Week of ${formatDate(isoDate(weekOf))}`;

  return (
    <div>
      {/* Week navigation */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <button onClick={prevWeek} className="p-2 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted">
            <ChevronLeft size={18} />
          </button>
          <h2 className="text-lg font-semibold text-text-primary">{weekLabel}</h2>
          <button onClick={nextWeek} className="p-2 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted">
            <ChevronRight size={18} />
          </button>
          <button onClick={thisWeek} className="px-3 py-1 rounded-md bg-bg-card hover:bg-bg-hover text-text-muted text-xs">
            Today
          </button>
        </div>
        <button
          onClick={() => setShowAIModal(true)}
          className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Sparkles size={16} />
          Generate with AI
        </button>
      </div>

      {/* Week grid */}
      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading...</div>
      ) : weekData ? (
        <div className="grid grid-cols-1 gap-3">
          {Object.entries(weekData.days).map(([dateStr, meals]) => {
            const isToday = dateStr === today;
            return (
              <div
                key={dateStr}
                className={`bg-bg-card rounded-lg border p-4 ${
                  isToday ? 'border-accent' : 'border-border'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className={`font-semibold text-sm ${isToday ? 'text-accent' : 'text-text-primary'}`}>
                    {formatDate(dateStr)}
                    {isToday && <span className="ml-2 text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">Today</span>}
                  </h3>
                  <button
                    onClick={() => openAddModal(dateStr)}
                    className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {meals.length === 0 ? (
                  <p className="text-text-muted text-xs italic">No meals planned</p>
                ) : (
                  <div className="space-y-2">
                    {MEAL_TYPES.map((type) => {
                      const typeMeals = meals.filter((m) => m.meal_type === type);
                      if (typeMeals.length === 0) return null;
                      return typeMeals.map((meal) => (
                        <div
                          key={meal.id}
                          className="flex items-center justify-between bg-bg-input rounded-md px-3 py-2"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{MEAL_TYPE_ICONS[meal.meal_type] || '🍽️'}</span>
                            <span className="text-xs text-text-muted capitalize">{meal.meal_type}</span>
                            <span className="text-sm text-text-primary">{meal.meal_name}</span>
                            {meal.source === 'ai' && (
                              <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded">AI</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => openEditModal(meal)}
                              className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              onClick={() => deleteMeal(meal.id)}
                              className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      ));
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Add/Edit Meal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editingMeal ? 'Edit Meal' : 'Add Meal'}
              </h3>
              <button onClick={() => setShowAddModal(false)} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Date</label>
                <input
                  type="date"
                  value={addDate}
                  onChange={(e) => setAddDate(e.target.value)}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Meal Type</label>
                <div className="grid grid-cols-4 gap-2">
                  {MEAL_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => setAddType(type)}
                      className={`px-3 py-2 rounded-lg text-xs font-medium capitalize transition-colors ${
                        addType === type
                          ? 'bg-accent text-white'
                          : 'bg-bg-input text-text-muted hover:bg-bg-hover'
                      }`}
                    >
                      {MEAL_TYPE_ICONS[type]} {type}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Meal Name</label>
                <input
                  type="text"
                  value={addName}
                  onChange={(e) => setAddName(e.target.value)}
                  placeholder="e.g. Grilled Chicken with Rice"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && saveMeal()}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover"
                >
                  Cancel
                </button>
                <button
                  onClick={saveMeal}
                  disabled={!addName.trim()}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50"
                >
                  {editingMeal ? 'Update' : 'Add'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Generate Modal */}
      {showAIModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                <Sparkles size={20} className="text-accent" />
                AI Meal Plan
              </h3>
              <button onClick={() => setShowAIModal(false)} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <p className="text-text-muted text-sm mb-4">
              Generate a full week of meals using Claude AI for the week of {formatDate(isoDate(weekOf))}.
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Preferences (optional)
              </label>
              <textarea
                value={aiPreferences}
                onChange={(e) => setAiPreferences(e.target.value)}
                placeholder="e.g. healthy, kid-friendly, quick meals, no seafood..."
                rows={3}
                className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent resize-none"
              />
            </div>

            <p className="text-xs text-status-warning mb-4">
              This will replace any AI-generated meals for this week. Manually added meals will be kept.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowAIModal(false)}
                className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover"
              >
                Cancel
              </button>
              <button
                onClick={generateWithAI}
                disabled={generating}
                className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {generating ? (
                  <>Generating...</>
                ) : (
                  <>
                    <Sparkles size={14} />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
