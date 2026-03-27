import { Toaster } from "@/components/ui/toaster"
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClientInstance } from '@/lib/query-client'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PageNotFound from './lib/PageNotFound';
import { AuthProvider, useAuth } from '@/lib/AuthContext';
import { Toaster as SonnerToaster } from 'sonner';
import Layout from '@/components/layout';
import Dashboard from '@/pages/Dashboard';
import LogHealth from '@/pages/LogHealth';
import Alerts from '@/pages/Alerts';
import Profile from '@/pages/Profile';
import ProviderDashboard from '@/pages/ProviderDashboard';

const AuthenticatedApp = () => {
  const { isLoadingAuth, authError } = useAuth();

  if (isLoadingAuth) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto"></div>
          <p className="text-sm text-muted-foreground font-medium">Loading MaternáGuard...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {authError?.type === 'backend_unreachable' && (
        <div className="bg-yellow-100 border-b border-yellow-300 text-yellow-900 text-xs px-4 py-2 text-center">
          Backend unavailable: {authError.message}
        </div>
      )}
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/log" element={<LogHealth />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/provider" element={<ProviderDashboard />} />
        </Route>
        <Route path="*" element={<PageNotFound />} />
      </Routes>
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClientInstance}>
        <Router>
          <AuthenticatedApp />
        </Router>
        <Toaster />
        <SonnerToaster position="top-right" richColors />
      </QueryClientProvider>
    </AuthProvider>
  )
}

export default App