import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { X } from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { Chore } from '../../types.ts';

interface ChoreFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  chore?: Chore | null;
}

const FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'every_other_day', label: 'Every Other Day' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Biweekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'one_time', label: 'One Time' },
];

const ASSIGNED_OPTIONS = [
  { value: '', label: 'Unassigned' },
  { value: 'dj', label: 'DJ' },
  { value: 'wife', label: 'Wife' },
  { value: 'either', label: 'Either' },
  { value: 'both', label: 'Both' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

export default function ChoreForm({ isOpen, onClose, onSaved, chore }: ChoreFormProps) {
  const showToast = useStore((s) => s.showToast);
  const [saving, setSaving] = useState(false);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('weekly');
  const [assignedTo, setAssignedTo] = useState('');
  const [category, setCategory] = useState('');
  const [priority, setPriority] = useState('medium');

  const isEdit = !!chore;

  useEffect(() => {
    if (chore) {
      setTitle(chore.title);
      setDescription(chore.description ?? '');
      setFrequency(chore.frequency);
      setAssignedTo(chore.assigned_to ?? '');
      setCategory(chore.category ?? '');
      setPriority(chore.priority);
    } else {
      setTitle('');
      setDescription('');
      setFrequency('weekly');
      setAssignedTo('');
      setCategory('');
      setPriority('medium');
    }
  }, [chore, isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      showToast('Title is required', 'error');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || null,
        frequency,
        assigned_to: assignedTo || null,
        category: category.trim() || null,
        priority,
      };

      if (isEdit) {
        await api.put(`/chores/${chore.id}`, payload);
        showToast('Chore updated', 'success');
      } else {
        await api.post('/chores', payload);
        showToast('Chore created', 'success');
      }
      onSaved();
      onClose();
    } catch {
      showToast(isEdit ? 'Failed to update chore' : 'Failed to create chore', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-bg-card border border-border rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-text-primary">
            {isEdit ? 'Edit Chore' : 'Add Chore'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-text-muted hover:text-text-primary rounded-md hover:bg-bg-hover transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Title */}
          <div>
            <label htmlFor="chore-title" className="block text-sm font-medium text-text-secondary mb-1.5">
              Title *
            </label>
            <input
              id="chore-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
              placeholder="e.g., Vacuum living room"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="chore-desc" className="block text-sm font-medium text-text-secondary mb-1.5">
              Description
            </label>
            <textarea
              id="chore-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent resize-none"
              placeholder="Optional details..."
            />
          </div>

          {/* Frequency */}
          <div>
            <label htmlFor="chore-freq" className="block text-sm font-medium text-text-secondary mb-1.5">
              Frequency
            </label>
            <select
              id="chore-freq"
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              {FREQUENCIES.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>

          {/* Assigned To */}
          <div>
            <label htmlFor="chore-assigned" className="block text-sm font-medium text-text-secondary mb-1.5">
              Assigned To
            </label>
            <select
              id="chore-assigned"
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              {ASSIGNED_OPTIONS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label htmlFor="chore-cat" className="block text-sm font-medium text-text-secondary mb-1.5">
              Category
            </label>
            <input
              id="chore-cat"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
              placeholder="e.g., Kitchen, Bathroom"
            />
          </div>

          {/* Priority */}
          <div>
            <label htmlFor="chore-priority" className="block text-sm font-medium text-text-secondary mb-1.5">
              Priority
            </label>
            <select
              id="chore-priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 bg-bg-input border border-border rounded-md text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              {PRIORITY_OPTIONS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-accent hover:bg-accent-hover text-white py-2.5 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : isEdit ? 'Update Chore' : 'Create Chore'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-bg-hover text-text-secondary hover:text-text-primary py-2.5 rounded-md text-sm font-medium transition-colors border border-border"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
