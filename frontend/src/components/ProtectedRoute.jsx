import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const useDummy = import.meta.env.VITE_USE_DUMMY === "true";

export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (useDummy) return children;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950 text-cyan-300">
        Loading session…
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
