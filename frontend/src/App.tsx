import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { HomePage } from '@/pages/HomePage';
import { SearchPage } from '@/pages/SearchPage';
import { SavedPage } from '@/pages/SavedPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { DetailPage } from '@/pages/DetailPage';
import { PrivacyPage } from '@/pages/PrivacyPage';
import { TermsPage } from '@/pages/TermsPage';
import { PublicDataProvider } from '@/state/PublicDataContext';

function NotFound() {
  return <p className="status">ページが見つかりません</p>;
}

function AppRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/saved" element={<SavedPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/videos/:id" element={<DetailPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="*" element={<NotFound />} />
        <Route path="/admin" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export function App() {
  return (
    <PublicDataProvider>
      <AppRoutes />
    </PublicDataProvider>
  );
}
