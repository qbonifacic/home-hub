import { useState } from 'react';
import MealPlanTab from './MealPlanTab.tsx';
import RecipesTab from './RecipesTab.tsx';
import GroceryTab from './GroceryTab.tsx';

const tabs = ['Meal Plan', 'Recipes', 'Grocery'] as const;
type Tab = (typeof tabs)[number];

export default function MealsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('Meal Plan');

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Meals</h1>
          <p className="text-text-muted text-sm">Plan meals, manage recipes & grocery lists</p>
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

      {/* Tab content */}
      {activeTab === 'Meal Plan' && <MealPlanTab />}
      {activeTab === 'Recipes' && <RecipesTab />}
      {activeTab === 'Grocery' && <GroceryTab />}
    </div>
  );
}
