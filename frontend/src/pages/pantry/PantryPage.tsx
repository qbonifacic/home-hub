import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Search,
  Package,
  Trash2,
  Edit2,
  X,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { PantryItem } from '../../types.ts';

const STORAGE_LOCATIONS = ['Pantry', 'Fridge', 'Freezer'];
const LOCATION_ICONS: Record<string, string> = {
  Pantry: '🗄️',
  Fridge: '🧊',
  Freezer: '❄️',
};

function daysUntilExpiry(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const exp = new Date(dateStr + 'T00:00:00');
  return Math.ceil((exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function expiryBadge(dateStr: string | null): { text: string; className: string } | null {
  const days = daysUntilExpiry(dateStr);
  if (days === null) return null;
  if (days < 0) return { text: `Expired ${Math.abs(days)}d ago`, className: 'bg-status-danger/20 text-status-danger' };
  if (days === 0) return { text: 'Expires today', className: 'bg-status-danger/20 text-status-danger' };
  if (days <= 3) return { text: `${days}d left`, className: 'bg-status-warning/20 text-status-warning' };
  if (days <= 7) return { text: `${days}d left`, className: 'bg-status-info/20 text-status-info' };
  return { text: `${days}d left`, className: 'bg-bg-input text-text-muted' };
}

export default function PantryPage() {
  const showToast = useStore((s) => s.showToast);
  const [items, setItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterLocation, setFilterLocation] = useState<string | null>(null);
  const [showConsumed, setShowConsumed] = useState(false);

  // Add/Edit modal
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<PantryItem | null>(null);
  const [formName, setFormName] = useState('');
  const [formCategory, setFormCategory] = useState('');
  const [formQuantity, setFormQuantity] = useState('');
  const [formUnit, setFormUnit] = useState('');
  const [formLocation, setFormLocation] = useState('Pantry');
  const [formExpDate, setFormExpDate] = useState('');
  const [formIsOpened, setFormIsOpened] = useState(false);
  const [formAlertDays, setFormAlertDays] = useState(3);

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | boolean> = {};
      if (filterLocation) params.location = filterLocation;
      if (showConsumed) params.show_consumed = true;
      const res = await api.get('/pantry', { params });
      setItems(res.data);
    } catch {
      showToast('Failed to load pantry', 'error');
    } finally {
      setLoading(false);
    }
  }, [filterLocation, showConsumed, showToast]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const resetForm = () => {
    setFormName('');
    setFormCategory('');
    setFormQuantity('');
    setFormUnit('');
    setFormLocation('Pantry');
    setFormExpDate('');
    setFormIsOpened(false);
    setFormAlertDays(3);
    setEditing(null);
  };

  const openAddModal = (location?: string) => {
    resetForm();
    if (location) setFormLocation(location);
    setShowModal(true);
  };

  const openEditModal = (item: PantryItem) => {
    setEditing(item);
    setFormName(item.item_name);
    setFormCategory(item.category || '');
    setFormQuantity(item.quantity || '');
    setFormUnit(item.unit || '');
    setFormLocation(item.storage_location);
    setFormExpDate(item.expiration_date || '');
    setFormIsOpened(item.is_opened);
    setFormAlertDays(item.alert_days_before);
    setShowModal(true);
  };

  const saveItem = async () => {
    if (!formName.trim()) return;
    try {
      const payload: Record<string, unknown> = {
        item_name: formName.trim(),
        category: formCategory.trim() || null,
        quantity: formQuantity.trim() || null,
        unit: formUnit.trim() || null,
        storage_location: formLocation,
        expiration_date: formExpDate || null,
        is_opened: formIsOpened,
        alert_days_before: formAlertDays,
      };

      if (editing) {
        await api.put(`/pantry/${editing.id}`, payload);
        showToast('Item updated', 'success');
      } else {
        await api.post('/pantry', payload);
        showToast('Item added', 'success');
      }
      setShowModal(false);
      resetForm();
      loadItems();
    } catch {
      showToast('Failed to save item', 'error');
    }
  };

  const deleteItem = async (id: number) => {
    try {
      await api.delete(`/pantry/${id}`);
      showToast('Item removed', 'success');
      loadItems();
    } catch {
      showToast('Failed to delete item', 'error');
    }
  };

  const markConsumed = async (id: number) => {
    try {
      await api.post(`/pantry/${id}/consumed`);
      showToast('Marked as consumed', 'success');
      loadItems();
    } catch {
      showToast('Failed to update item', 'error');
    }
  };

  // Filter items by search
  const filteredItems = items.filter((item) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      item.item_name.toLowerCase().includes(s) ||
      (item.category && item.category.toLowerCase().includes(s))
    );
  });

  // Group by location
  const grouped: Record<string, PantryItem[]> = {};
  for (const item of filteredItems) {
    const loc = item.storage_location || 'Other';
    if (!grouped[loc]) grouped[loc] = [];
    grouped[loc].push(item);
  }

  // Sort within groups: expired first, then by expiration date
  for (const loc of Object.keys(grouped)) {
    grouped[loc].sort((a, b) => {
      const aDays = daysUntilExpiry(a.expiration_date);
      const bDays = daysUntilExpiry(b.expiration_date);
      if (aDays === null && bDays === null) return a.item_name.localeCompare(b.item_name);
      if (aDays === null) return 1;
      if (bDays === null) return -1;
      return aDays - bDays;
    });
  }

  // Ordering: Fridge, Pantry, Freezer, then others
  const locationOrder = ['Fridge', 'Pantry', 'Freezer'];
  const sortedLocations = Object.keys(grouped).sort((a, b) => {
    const ai = locationOrder.indexOf(a);
    const bi = locationOrder.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  const totalItems = items.filter((i) => !i.is_consumed).length;
  const expiringCount = items.filter((i) => {
    if (i.is_consumed) return false;
    const days = daysUntilExpiry(i.expiration_date);
    return days !== null && days <= 7;
  }).length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Pantry Inventory</h1>
          <p className="text-sm text-text-muted">
            {totalItems} item{totalItems !== 1 ? 's' : ''}
            {expiringCount > 0 && (
              <span className="text-status-warning ml-2">
                {expiringCount} expiring soon
              </span>
            )}
          </p>
        </div>
        <button
          onClick={() => openAddModal()}
          className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Add Item
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search items..."
            className="w-full pl-9 pr-3 py-2 bg-bg-card border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex items-center gap-2">
          {STORAGE_LOCATIONS.map((loc) => (
            <button
              key={loc}
              onClick={() => setFilterLocation(filterLocation === loc ? null : loc)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                filterLocation === loc
                  ? 'bg-accent text-white'
                  : 'bg-bg-card text-text-muted hover:bg-bg-hover'
              }`}
            >
              {LOCATION_ICONS[loc]} {loc}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-xs text-text-muted cursor-pointer">
          <input
            type="checkbox"
            checked={showConsumed}
            onChange={(e) => setShowConsumed(e.target.checked)}
            className="rounded"
          />
          Show consumed
        </label>
      </div>

      {/* Items grouped by location */}
      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading pantry...</div>
      ) : sortedLocations.length === 0 ? (
        <div className="bg-bg-card rounded-lg border border-border p-8 text-center">
          <Package className="mx-auto text-text-muted mb-3" size={36} />
          <p className="text-text-secondary font-medium">No items in your pantry</p>
          <p className="text-text-muted text-sm mt-1">Add items to track your food inventory</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedLocations.map((location) => (
            <div key={location} className="bg-bg-card rounded-lg border border-border overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  <span>{LOCATION_ICONS[location] || '📦'}</span>
                  {location}
                  <span className="text-xs text-text-muted font-normal">
                    ({grouped[location].length})
                  </span>
                </h2>
                <button
                  onClick={() => openAddModal(location)}
                  className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                >
                  <Plus size={16} />
                </button>
              </div>

              <div className="divide-y divide-border">
                {grouped[location].map((item) => {
                  const badge = expiryBadge(item.expiration_date);
                  return (
                    <div
                      key={item.id}
                      className={`flex items-center justify-between px-4 py-3 ${
                        item.is_consumed ? 'opacity-50' : ''
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className="min-w-0">
                          <p className={`text-sm font-medium truncate ${
                            item.is_consumed ? 'text-text-muted line-through' : 'text-text-primary'
                          }`}>
                            {item.item_name}
                            {item.is_opened && (
                              <span className="ml-2 text-[10px] bg-status-warning/20 text-status-warning px-1.5 py-0.5 rounded">
                                Opened
                              </span>
                            )}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {item.quantity && (
                              <span className="text-xs text-text-muted">
                                {item.quantity}{item.unit ? ` ${item.unit}` : ''}
                              </span>
                            )}
                            {item.category && (
                              <span className="text-xs text-text-muted">
                                {item.category}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {badge && (
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${badge.className}`}>
                            {badge.text}
                          </span>
                        )}

                        {!item.is_consumed && (
                          <button
                            onClick={() => markConsumed(item.id)}
                            className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-success"
                            title="Mark consumed"
                          >
                            <CheckCircle2 size={15} />
                          </button>
                        )}
                        <button
                          onClick={() => openEditModal(item)}
                          className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          onClick={() => deleteItem(item.id)}
                          className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editing ? 'Edit Item' : 'Add Pantry Item'}
              </h3>
              <button
                onClick={() => { setShowModal(false); resetForm(); }}
                className="p-1 rounded hover:bg-bg-hover text-text-muted"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Item Name *</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. Chicken Breast"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  autoFocus
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Quantity</label>
                  <input
                    type="text"
                    value={formQuantity}
                    onChange={(e) => setFormQuantity(e.target.value)}
                    placeholder="e.g. 2"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Unit</label>
                  <input
                    type="text"
                    value={formUnit}
                    onChange={(e) => setFormUnit(e.target.value)}
                    placeholder="e.g. lbs, oz, ct"
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                <input
                  type="text"
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  placeholder="e.g. Protein, Dairy, Produce"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Storage Location</label>
                <div className="grid grid-cols-3 gap-2">
                  {STORAGE_LOCATIONS.map((loc) => (
                    <button
                      key={loc}
                      onClick={() => setFormLocation(loc)}
                      className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                        formLocation === loc
                          ? 'bg-accent text-white'
                          : 'bg-bg-input text-text-muted hover:bg-bg-hover'
                      }`}
                    >
                      {LOCATION_ICONS[loc]} {loc}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Expiration Date</label>
                <input
                  type="date"
                  value={formExpDate}
                  onChange={(e) => setFormExpDate(e.target.value)}
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formIsOpened}
                    onChange={(e) => setFormIsOpened(e.target.checked)}
                    className="rounded"
                  />
                  Item is opened
                </label>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-text-secondary">Alert</label>
                  <select
                    value={formAlertDays}
                    onChange={(e) => setFormAlertDays(Number(e.target.value))}
                    className="px-2 py-1 bg-bg-input border border-border rounded text-text-primary text-xs"
                  >
                    <option value={1}>1 day before</option>
                    <option value={3}>3 days before</option>
                    <option value={5}>5 days before</option>
                    <option value={7}>1 week before</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => { setShowModal(false); resetForm(); }}
                  className="flex-1 px-4 py-2 bg-bg-input text-text-secondary rounded-lg text-sm hover:bg-bg-hover"
                >
                  Cancel
                </button>
                <button
                  onClick={saveItem}
                  disabled={!formName.trim()}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50"
                >
                  {editing ? 'Update' : 'Add Item'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
