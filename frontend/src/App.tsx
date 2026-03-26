import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { api } from './api.ts';
import { useStore } from './store.ts';
import Sidebar from './components/layout/Sidebar.tsx';
import BottomNav from './components/layout/BottomNav.tsx';
import Toast from './components/ui/Toast.tsx';
import Login from './pages/Login.tsx';
import Dashboard from './pages/Dashboard.tsx';
import ChoresPage from './pages/chores/ChoresPage.tsx';
import MealsPage from './pages/meals/MealsPage.tsx';
import OutdoorPage from './pages/outdoor/OutdoorPage.tsx';
import CalendarPage from './pages/calendar/CalendarPage.tsx';
import PantryPage from './pages/pantry/PantryPage.tsx';
import HomePage from './pages/home/HomePage.tsx';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const isAuthenticated = useStore((s) => s.auth.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AuthenticatedLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-primary">
      <Sidebar />
      <div className="main-content">
        <main className="p-6">
          {children}
        </main>
      </div>
      <BottomNav />
    </div>
  );
}

export default function App() {
  const login = useStore((s) => s.login);
  const isAuthenticated = useStore((s) => s.auth.isAuthenticated);
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await api.get('/auth/me');
        login(res.data);
      } catch {
        if (window.location.pathname !== '/login') {
          navigate('/login', { replace: true });
        }
      } finally {
        setChecking(false);
      }
    };
    checkAuth();
  }, [login, navigate]);

  if (checking) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-text-muted text-sm">Loading...</div>
      </div>
    );
  }

  return (
    <>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <Login />
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <Dashboard />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chores"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <ChoresPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/meals"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <MealsPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/calendar"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <CalendarPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/outdoor"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <OutdoorPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/pantry"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <PantryPage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <HomePage />
              </AuthenticatedLayout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toast />
    </>
  );
}
