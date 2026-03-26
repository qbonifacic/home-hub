export interface User {
  id: number;
  username: string;
  display_name: string | null;
}

export interface Chore {
  id: number;
  title: string;
  description: string | null;
  frequency: string;
  frequency_days: number | null;
  assigned_to: string | null;
  category: string | null;
  priority: string;
  next_due: string | null;
  last_done: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WeatherData {
  temp_f: number;
  desc: string;
  icon: string;
  humidity: number;
  feels_like: number;
  wind_mph: number;
  high: number | null;
  low: number | null;
}

// ── Meals / Recipes / Grocery ───────────────────────────────

export interface IngredientItem {
  name: string;
  quantity?: string | null;
  unit?: string | null;
  category?: string | null;
}

export interface Recipe {
  id: number;
  name: string;
  description: string | null;
  ingredients: IngredientItem[];
  instructions: string | null;
  prep_time_min: number | null;
  cook_time_min: number | null;
  servings: number | null;
  nutritional_info: Record<string, number> | null;
  tags: string[];
  image_url: string | null;
  is_favorite: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MealPlan {
  id: number;
  plan_date: string;
  meal_type: string;
  meal_name: string;
  recipe_id: number | null;
  notes: string | null;
  created_by: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface MealPlanWeek {
  week_of: string;
  days: Record<string, MealPlan[]>;
}

export interface GroceryItem {
  id: number;
  list_id: number;
  item_name: string;
  category: string;
  quantity: string | null;
  is_purchased: boolean;
  is_manual: boolean;
  purchased_at: string | null;
  purchased_by: string | null;
  sprouts_url: string | null;
  wholefoods_url: string | null;
  notes: string | null;
  created_at: string;
}

export interface GroceryList {
  id: number;
  week_of: string;
  name: string | null;
  status: string;
  items: GroceryItem[];
  created_at: string;
}

export interface DashboardMeal {
  id: number;
  meal_type: string;
  meal_name: string;
}

// ── Calendar ────────────────────────────────────────────────

export interface CalendarSource {
  id: number;
  user_id: number;
  provider: string;
  name: string;
  caldav_url: string;
  username: string;
  color: string;
  is_active: boolean;
}

export interface CalendarEvent {
  uid: string;
  summary: string;
  start: string;
  end: string | null;
  location: string | null;
  description: string | null;
  source_name: string;
  source_color: string;
  all_day: boolean;
}

// ── Pantry ──────────────────────────────────────────────────

export interface PantryItem {
  id: number;
  item_name: string;
  category: string | null;
  quantity: string | null;
  unit: string | null;
  storage_location: string;
  expiration_date: string | null;
  expiration_source: string | null;
  image_path: string | null;
  is_opened: boolean;
  is_consumed: boolean;
  alert_days_before: number;
  created_at: string;
  updated_at: string;
}

// ── Home Maintenance ────────────────────────────────────────

export interface Appliance {
  id: number;
  name: string;
  category: string | null;
  brand: string | null;
  model_number: string | null;
  serial_number: string | null;
  purchase_date: string | null;
  warranty_until: string | null;
  location: string | null;
  notes: string | null;
  created_at: string;
}

export interface MaintenanceTask {
  id: number;
  appliance_id: number | null;
  title: string;
  description: string | null;
  frequency: string | null;
  frequency_days: number | null;
  next_due: string | null;
  last_done: string | null;
  estimated_cost: number | null;
  vendor: string | null;
  created_at: string;
}

export interface MaintenanceLog {
  id: number;
  task_id: number | null;
  appliance_id: number | null;
  performed_date: string;
  cost: number | null;
  notes: string | null;
  vendor: string | null;
  receipt_path: string | null;
  created_at: string;
}

// ── Dashboard ───────────────────────────────────────────────

export interface DashboardEvent {
  uid: string;
  summary: string;
  start: string;
  source_name: string;
  source_color: string;
}

export interface DashboardPantryItem {
  id: number;
  item_name: string;
  expiration_date: string;
  storage_location: string;
}

export interface DashboardMaintenanceTask {
  id: number;
  title: string;
  next_due: string | null;
}

export interface DashboardData {
  weather: WeatherData | null;
  overdue_chores: Chore[];
  due_today_chores: Chore[];
  todays_meals: DashboardMeal[];
  upcoming_events: DashboardEvent[];
  expiring_pantry: DashboardPantryItem[];
  outdoor_this_week: { sessions: number; total_hours: number } | null;
  maintenance_due: DashboardMaintenanceTask[];
}
