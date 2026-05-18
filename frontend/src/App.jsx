import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import { SettingsProvider } from "./context/SettingsContext.jsx";
import { ProtectedRoute } from "./components/ProtectedRoute.jsx";
import { AppLayout } from "./layouts/AppLayout.jsx";
import { Dashboard } from "./pages/Dashboard.jsx";
import { HistoryPage } from "./pages/HistoryPage.jsx";
import { InventoryPage } from "./pages/InventoryPage.jsx";
import { Login } from "./pages/Login.jsx";
import { NotificationsPage } from "./pages/NotificationsPage.jsx";
import { Register } from "./pages/Register.jsx";
import { SettingsPage } from "./pages/SettingsPage.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SettingsProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </SettingsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
