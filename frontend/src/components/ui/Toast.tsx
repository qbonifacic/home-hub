import { useEffect } from 'react';
import { X } from 'lucide-react';
import { useStore } from '../../store.ts';

export default function Toast() {
  const toast = useStore((s) => s.toast);
  const hideToast = useStore((s) => s.hideToast);

  useEffect(() => {
    if (toast.visible) {
      const timer = setTimeout(() => {
        hideToast();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toast.visible, hideToast]);

  if (!toast.visible) return null;

  const colorMap = {
    success: 'bg-status-success',
    error: 'bg-status-danger',
    info: 'bg-status-info',
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-slide-in">
      <div
        className={`${colorMap[toast.type]} text-white px-5 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[280px]`}
      >
        <span className="flex-1 text-sm font-medium">{toast.message}</span>
        <button
          onClick={hideToast}
          className="text-white/80 hover:text-white transition-colors"
        >
          <X size={16} />
        </button>
      </div>
      <style>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
