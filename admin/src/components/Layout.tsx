import { NavLink, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>Chatbot Admin</h2>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/websites">Websites</NavLink>
        </nav>
        <button className="logout-btn" onClick={logout}>
          Log out
        </button>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
