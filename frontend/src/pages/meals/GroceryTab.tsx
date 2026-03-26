import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  ShoppingCart,
  Check,
  Trash2,
  RefreshCw,
  X,
  Package,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { GroceryList, GroceryItem } from '../../types.ts';

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.getFullYear(), d.getMonth(), diff);
}

function isoDate(d: Date): string {
  return d.toISOString().split('T')[0];
}

// Group items by category
function groupByCategory(items: GroceryItem[]): Record<string, GroceryItem[]> {
  const groups: Record<string, GroceryItem[]> = {};
  for (const item of items) {
    const cat = item.category || 'Other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(item);
  }
  // Sort categories
  return Object.fromEntries(
    Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
  );
}

const CATEGORY_ICONS: Record<string, string> = {
  'Produce': '🥬',
  'Meat & Seafood': '🥩',
  'Dairy & Eggs': '🥛',
  'Bakery & Bread': '🍞',
  'Pantry': '🥫',
  'Spices & Seasonings': '🧂',
  'Frozen': '🧊',
  'Beverages': '🥤',
  'Snacks': '🍿',
};

export default function GroceryTab() {
  const showToast = useStore((s) => s.showToast);
  const [lists, setLists] = useState<GroceryList[]>([]);
  const [activeList, setActiveList] = useState<GroceryList | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Add item
  const [showAddItem, setShowAddItem] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState('');

  const loadLists = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/grocery');
      setLists(res.data);
      if (res.data.length > 0 && !activeList) {
        setActiveList(res.data[0]);
      } else if (activeList) {
        // Refresh active list data
        const updated = res.data.find((l: GroceryList) => l.id === activeList.id);
        if (updated) setActiveList(updated);
      }
    } catch {
      showToast('Failed to load grocery lists', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadLists();
  }, [loadLists]);

  const generateFromMeals = async () => {
    setGenerating(true);
    try {
      const weekOf = isoDate(getMonday(new Date()));
      const res = await api.post('/grocery/generate', { week_of: weekOf });
      showToast('Grocery list generated from meal plan!', 'success');
      setActiveList(res.data);
      loadLists();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to generate grocery list';
      showToast(msg, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const togglePurchased = async (item: GroceryItem) => {
    try {
      await api.put(`/grocery/items/${item.id}`, {
        is_purchased: !item.is_purchased,
      });
      loadLists();
    } catch {
      showToast('Failed to update item', 'error');
    }
  };

  const deleteItem = async (itemId: number) => {
    try {
      await api.delete(`/grocery/items/${itemId}`);
      loadLists();
    } catch {
      showToast('Failed to delete item', 'error');
    }
  };

  const addItem = async () => {
    if (!activeList || !newItemName.trim()) return;
    try {
      await api.post(`/grocery/${activeList.id}/items`, {
        item_name: newItemName.trim(),
        quantity: newItemQty.trim() || null,
        is_manual: true,
      });
      setNewItemName('');
      setNewItemQty('');
      setShowAddItem(false);
      showToast('Item added', 'success');
      loadLists();
    } catch {
      showToast('Failed to add item', 'error');
    }
  };

  const items = activeList?.items || [];
  const grouped = groupByCategory(items.filter((i) => !i.is_purchased));
  const purchased = items.filter((i) => i.is_purchased);
  const total = items.length;
  const done = purchased.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {lists.length > 1 && (
            <select
              value={activeList?.id || ''}
              onChange={(e) => {
                const found = lists.find((l) => l.id === parseInt(e.target.value));
                if (found) setActiveList(found);
              }}
              className="px-3 py-2 bg-bg-card border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
            >
              {lists.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name || `Week of ${l.week_of}`}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={generateFromMeals}
            disabled={generating}
            className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {generating ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <ShoppingCart size={16} />
            )}
            {generating ? 'Generating...' : 'Generate from Meals'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading...</div>
      ) : !activeList ? (
        <div className="text-center py-12">
          <Package size={48} className="mx-auto mb-3 text-text-muted opacity-50" />
          <p className="text-text-muted text-sm mb-2">No grocery lists yet</p>
          <p className="text-text-muted text-xs mb-4">
            Add meals to your plan, then generate a grocery list
          </p>
          <button
            onClick={generateFromMeals}
            disabled={generating}
            className="text-accent hover:underline text-sm"
          >
            Generate from this week's meals
          </button>
        </div>
      ) : (
        <div>
          {/* Progress bar */}
          <div className="bg-bg-card rounded-lg border border-border p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-text-secondary font-medium">
                {activeList.name || `Week of ${activeList.week_of}`}
              </span>
              <span className="text-xs text-text-muted">
                {done}/{total} items ({pct}%)
              </span>
            </div>
            <div className="w-full h-2 bg-bg-input rounded-full overflow-hidden">
              <div
                className="h-full bg-status-success rounded-full transition-all"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          {/* Add item button */}
          <div className="mb-4">
            {showAddItem ? (
              <div className="flex items-center gap-2 bg-bg-card rounded-lg border border-border p-3">
                <input
                  value={newItemQty}
                  onChange={(e) => setNewItemQty(e.target.value)}
                  placeholder="Qty"
                  className="w-20 px-2 py-1.5 bg-bg-input border border-border rounded text-text-primary text-sm focus:outline-none focus:border-accent"
                />
                <input
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  placeholder="Item name"
                  className="flex-1 px-2 py-1.5 bg-bg-input border border-border rounded text-text-primary text-sm focus:outline-none focus:border-accent"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && addItem()}
                />
                <button
                  onClick={addItem}
                  disabled={!newItemName.trim()}
                  className="px-3 py-1.5 bg-accent text-white rounded text-sm font-medium disabled:opacity-50"
                >
                  Add
                </button>
                <button onClick={() => setShowAddItem(false)} className="p-1 text-text-muted hover:text-text-primary">
                  <X size={16} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAddItem(true)}
                className="flex items-center gap-1.5 text-sm text-accent hover:underline"
              >
                <Plus size={14} />
                Add item manually
              </button>
            )}
          </div>

          {/* Items by category */}
          {Object.entries(grouped).map(([category, catItems]) => (
            <div key={category} className="mb-4">
              <h3 className="text-xs font-semibold text-text-muted uppercase mb-2 flex items-center gap-1.5">
                <span>{CATEGORY_ICONS[category] || '📦'}</span>
                {category} ({catItems.length})
              </h3>
              <div className="space-y-1">
                {catItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between bg-bg-card rounded-lg border border-border px-3 py-2"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <button
                        onClick={() => togglePurchased(item)}
                        className="w-5 h-5 rounded border border-border flex items-center justify-center hover:border-accent"
                      >
                        {item.is_purchased && <Check size={13} className="text-status-success" />}
                      </button>
                      <div className="flex-1">
                        <span className="text-sm text-text-primary">{item.item_name}</span>
                        {item.quantity && (
                          <span className="text-xs text-text-muted ml-2">({item.quantity})</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {item.sprouts_url && (
                        <a
                          href={item.sprouts_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-success text-[10px]"
                          title="Search Sprouts"
                        >
                          🥬
                        </a>
                      )}
                      {item.wholefoods_url && (
                        <a
                          href={item.wholefoods_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-success text-[10px]"
                          title="Search Whole Foods"
                        >
                          🏪
                        </a>
                      )}
                      <button
                        onClick={() => deleteItem(item.id)}
                        className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Purchased items (collapsed) */}
          {purchased.length > 0 && (
            <div className="mt-6">
              <h3 className="text-xs font-semibold text-text-muted uppercase mb-2">
                ✅ Purchased ({purchased.length})
              </h3>
              <div className="space-y-1 opacity-60">
                {purchased.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between bg-bg-card rounded-lg border border-border px-3 py-2"
                  >
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => togglePurchased(item)}
                        className="w-5 h-5 rounded border border-status-success bg-status-success/10 flex items-center justify-center"
                      >
                        <Check size={13} className="text-status-success" />
                      </button>
                      <span className="text-sm text-text-muted line-through">{item.item_name}</span>
                    </div>
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
