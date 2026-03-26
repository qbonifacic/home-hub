import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Search,
  Heart,
  Clock,
  Users,
  Trash2,
  Edit2,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';
import { api } from '../../api.ts';
import { useStore } from '../../store.ts';
import type { Recipe, IngredientItem } from '../../types.ts';

const EMPTY_INGREDIENT: IngredientItem = { name: '', quantity: '', unit: '' };

export default function RecipesTab() {
  const showToast = useStore((s) => s.showToast);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [favOnly, setFavOnly] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Recipe | null>(null);
  const [formName, setFormName] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formInstructions, setFormInstructions] = useState('');
  const [formIngredients, setFormIngredients] = useState<IngredientItem[]>([{ ...EMPTY_INGREDIENT }]);
  const [formPrepTime, setFormPrepTime] = useState('');
  const [formCookTime, setFormCookTime] = useState('');
  const [formServings, setFormServings] = useState('');
  const [formTags, setFormTags] = useState('');

  const loadRecipes = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | boolean> = {};
      if (search) params.search = search;
      if (favOnly) params.favorites = true;
      const res = await api.get('/recipes', { params });
      setRecipes(res.data);
    } catch {
      showToast('Failed to load recipes', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, favOnly, showToast]);

  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

  const resetForm = () => {
    setFormName('');
    setFormDesc('');
    setFormInstructions('');
    setFormIngredients([{ ...EMPTY_INGREDIENT }]);
    setFormPrepTime('');
    setFormCookTime('');
    setFormServings('');
    setFormTags('');
    setEditing(null);
  };

  const openCreate = () => {
    resetForm();
    setShowForm(true);
  };

  const openEdit = (recipe: Recipe) => {
    setEditing(recipe);
    setFormName(recipe.name);
    setFormDesc(recipe.description || '');
    setFormInstructions(recipe.instructions || '');
    setFormIngredients(
      recipe.ingredients?.length ? recipe.ingredients : [{ ...EMPTY_INGREDIENT }]
    );
    setFormPrepTime(recipe.prep_time_min?.toString() || '');
    setFormCookTime(recipe.cook_time_min?.toString() || '');
    setFormServings(recipe.servings?.toString() || '');
    setFormTags(recipe.tags?.join(', ') || '');
    setShowForm(true);
  };

  const addIngredientRow = () => {
    setFormIngredients([...formIngredients, { ...EMPTY_INGREDIENT }]);
  };

  const updateIngredient = (idx: number, field: keyof IngredientItem, value: string) => {
    const updated = [...formIngredients];
    updated[idx] = { ...updated[idx], [field]: value };
    setFormIngredients(updated);
  };

  const removeIngredient = (idx: number) => {
    if (formIngredients.length <= 1) return;
    setFormIngredients(formIngredients.filter((_, i) => i !== idx));
  };

  const saveRecipe = async () => {
    if (!formName.trim()) return;
    const payload = {
      name: formName.trim(),
      description: formDesc.trim() || null,
      instructions: formInstructions.trim() || null,
      ingredients: formIngredients.filter((i) => i.name.trim()),
      prep_time_min: formPrepTime ? parseInt(formPrepTime) : null,
      cook_time_min: formCookTime ? parseInt(formCookTime) : null,
      servings: formServings ? parseInt(formServings) : null,
      tags: formTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    };

    try {
      if (editing) {
        await api.put(`/recipes/${editing.id}`, payload);
        showToast('Recipe updated', 'success');
      } else {
        await api.post('/recipes', payload);
        showToast('Recipe created', 'success');
      }
      setShowForm(false);
      resetForm();
      loadRecipes();
    } catch {
      showToast('Failed to save recipe', 'error');
    }
  };

  const deleteRecipe = async (id: number) => {
    try {
      await api.delete(`/recipes/${id}`);
      showToast('Recipe deleted', 'success');
      loadRecipes();
    } catch {
      showToast('Failed to delete recipe', 'error');
    }
  };

  const toggleFavorite = async (id: number) => {
    try {
      await api.post(`/recipes/${id}/favorite`);
      loadRecipes();
    } catch {
      showToast('Failed to toggle favorite', 'error');
    }
  };

  return (
    <div>
      {/* Search & filter bar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search recipes..."
            className="w-full pl-10 pr-3 py-2 bg-bg-card border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
          />
        </div>
        <button
          onClick={() => setFavOnly(!favOnly)}
          className={`p-2 rounded-lg border transition-colors ${
            favOnly ? 'border-status-danger bg-status-danger/10 text-status-danger' : 'border-border text-text-muted hover:bg-bg-hover'
          }`}
        >
          <Heart size={18} fill={favOnly ? 'currentColor' : 'none'} />
        </button>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 px-3 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Add Recipe
        </button>
      </div>

      {/* Recipe list */}
      {loading ? (
        <div className="text-text-muted text-sm py-8 text-center">Loading...</div>
      ) : recipes.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-muted text-sm mb-2">No recipes yet</p>
          <button onClick={openCreate} className="text-accent hover:underline text-sm">
            Add your first recipe
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {recipes.map((recipe) => {
            const expanded = expandedId === recipe.id;
            return (
              <div key={recipe.id} className="bg-bg-card rounded-lg border border-border overflow-hidden">
                {/* Header row */}
                <div className="flex items-center justify-between p-4">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => setExpandedId(expanded ? null : recipe.id)}
                  >
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-text-primary">{recipe.name}</h3>
                      {recipe.tags?.map((tag) => (
                        <span key={tag} className="text-[10px] bg-accent/10 text-accent px-1.5 py-0.5 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
                      {recipe.prep_time_min != null && (
                        <span className="flex items-center gap-1">
                          <Clock size={11} /> Prep: {recipe.prep_time_min}m
                        </span>
                      )}
                      {recipe.cook_time_min != null && (
                        <span className="flex items-center gap-1">
                          <Clock size={11} /> Cook: {recipe.cook_time_min}m
                        </span>
                      )}
                      {recipe.servings != null && (
                        <span className="flex items-center gap-1">
                          <Users size={11} /> {recipe.servings} servings
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => toggleFavorite(recipe.id)}
                      className={`p-1.5 rounded hover:bg-bg-hover ${
                        recipe.is_favorite ? 'text-status-danger' : 'text-text-muted'
                      }`}
                    >
                      <Heart size={15} fill={recipe.is_favorite ? 'currentColor' : 'none'} />
                    </button>
                    <button
                      onClick={() => openEdit(recipe)}
                      className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-accent"
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      onClick={() => deleteRecipe(recipe.id)}
                      className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                    >
                      <Trash2 size={15} />
                    </button>
                    <button
                      onClick={() => setExpandedId(expanded ? null : recipe.id)}
                      className="p-1.5 rounded hover:bg-bg-hover text-text-muted"
                    >
                      {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                    </button>
                  </div>
                </div>

                {/* Expanded details */}
                {expanded && (
                  <div className="border-t border-border p-4 space-y-3">
                    {recipe.description && (
                      <p className="text-sm text-text-secondary">{recipe.description}</p>
                    )}

                    {recipe.ingredients && recipe.ingredients.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Ingredients</h4>
                        <ul className="grid grid-cols-2 gap-1">
                          {recipe.ingredients.map((ing, i) => (
                            <li key={i} className="text-sm text-text-secondary flex items-start gap-1">
                              <span className="text-accent mt-0.5">•</span>
                              {ing.quantity && <span>{ing.quantity}</span>}
                              {ing.unit && <span>{ing.unit}</span>}
                              <span>{ing.name}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {recipe.instructions && (
                      <div>
                        <h4 className="text-xs font-semibold text-text-muted uppercase mb-2">Instructions</h4>
                        <p className="text-sm text-text-secondary whitespace-pre-wrap">{recipe.instructions}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Recipe Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 p-4 overflow-y-auto">
          <div className="bg-bg-card rounded-xl border border-border p-6 w-full max-w-lg my-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">
                {editing ? 'Edit Recipe' : 'New Recipe'}
              </h3>
              <button onClick={() => { setShowForm(false); resetForm(); }} className="p-1 rounded hover:bg-bg-hover text-text-muted">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Name *</label>
                <input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="Recipe name"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                <input
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  placeholder="Brief description"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Prep (min)</label>
                  <input
                    type="number"
                    value={formPrepTime}
                    onChange={(e) => setFormPrepTime(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Cook (min)</label>
                  <input
                    type="number"
                    value={formCookTime}
                    onChange={(e) => setFormCookTime(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Servings</label>
                  <input
                    type="number"
                    value={formServings}
                    onChange={(e) => setFormServings(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Tags</label>
                <input
                  value={formTags}
                  onChange={(e) => setFormTags(e.target.value)}
                  placeholder="comma-separated: quick, mexican, kid-friendly"
                  className="w-full px-3 py-2 bg-bg-input border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:border-accent"
                />
              </div>

              {/* Ingredients */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-text-secondary">Ingredients</label>
                  <button onClick={addIngredientRow} className="text-xs text-accent hover:underline">
                    + Add ingredient
                  </button>
                </div>
                <div className="space-y-2">
                  {formIngredients.map((ing, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        value={ing.quantity || ''}
                        onChange={(e) => updateIngredient(i, 'quantity', e.target.value)}
                        placeholder="Qty"
                        className="w-16 px-2 py-1.5 bg-bg-input border border-border rounded text-text-primary text-sm focus:outline-none focus:border-accent"
                      />
                      <input
                        value={ing.unit || ''}
                        onChange={(e) => updateIngredient(i, 'unit', e.target.value)}
                        placeholder="Unit"
                        className="w-16 px-2 py-1.5 bg-bg-input border border-border rounded text-text-primary text-sm focus:outline-none focus:border-accent"
                      />
                      <input
                        value={ing.name}
                        onChange={(e) => updateIngredient(i, 'name', e.target.value)}
                        placeholder="Ingredient name"
                        className="flex-1 px-2 py-1.5 bg-bg-input border border-border rounded text-text-primary text-sm focus:outline-none focus:border-accent"
                      />
                      <button
                        onClick={() => removeIngredient(i)}
                        className="p-1 rounded hover:bg-bg-hover text-text-muted hover:text-status-danger"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Instructions</label>
                <textarea
                  value={formInstructions}
                  onChange={(e) => setFormInstructions(e.target.value)}
                  placeholder="Step by step instructions..."
                  rows={4}
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
                  onClick={saveRecipe}
                  disabled={!formName.trim()}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-accent-hover disabled:opacity-50"
                >
                  {editing ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
