import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload CSV" },
  { to: "/batches", label: "Batches" },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const initial = user?.full_name?.[0]?.toUpperCase() ?? "?";
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>FAILSAFE</h1>
        <p className="muted" style={{ marginTop: -10, fontSize: 12 }}>
          Early-warning intelligence
        </p>
        <nav style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 4 }}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: "auto", fontSize: 12 }} className="muted">
          Logged in as <strong style={{ color: "white" }}>{user?.role.toUpperCase()}</strong>
          <br />
          {user?.department ?? "No department"}
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <h2>Welcome, {user?.full_name?.split(" ")[0]}</h2>
          <div className="user-chip">
            <div className="avatar">{initial}</div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <strong style={{ fontSize: 13 }}>{user?.full_name}</strong>
              <span className="muted" style={{ fontSize: 11 }}>{user?.email}</span>
            </div>
            <button
              className="btn btn-ghost"
              style={{ marginLeft: 8 }}
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Logout
            </button>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
