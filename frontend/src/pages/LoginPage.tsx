import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import type { Role } from "../api/types";

type Mode = "login" | "register";

interface LocationState {
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login, register, loading, token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const dest = (location.state as LocationState | null)?.from?.pathname ?? "/dashboard";

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [role, setRole] = useState<Role>("faculty");
  const [error, setError] = useState<string | null>(null);

  if (token) {
    navigate(dest, { replace: true });
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register({
          email,
          password,
          full_name: fullName,
          department: department || undefined,
          role,
        });
      }
      navigate(dest, { replace: true });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Something went wrong. Please try again.";
      setError(msg);
    }
  };

  return (
    <div className="login-shell">
      <div className="card login-card">
        <h2 style={{ marginBottom: 4 }}>FAILSAFE</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Predict, explain, and act before the semester slips away.
        </p>
        <div className="tabs">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => setMode("register")}
          >
            Create account
          </button>
        </div>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={submit}>
          {mode === "register" && (
            <>
              <label className="label">Full name</label>
              <input
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="Dr. Avni Sharma"
                style={{ marginBottom: 14 }}
              />
              <div className="grid cols-2" style={{ marginBottom: 14 }}>
                <div>
                  <label className="label">Department</label>
                  <input
                    className="input"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="CSE"
                  />
                </div>
                <div>
                  <label className="label">Role</label>
                  <select
                    className="select"
                    value={role}
                    onChange={(e) => setRole(e.target.value as Role)}
                  >
                    <option value="faculty">Faculty</option>
                    <option value="hod">HOD</option>
                  </select>
                </div>
              </div>
            </>
          )}
          <label className="label">Email</label>
          <input
            className="input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ marginBottom: 14 }}
          />
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            style={{ marginBottom: 18 }}
          />
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? <span className="spinner" /> : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
          Tip: HOD accounts can see batches uploaded by everyone in the
          institution; faculty accounts only see their own.
        </p>
      </div>
    </div>
  );
}
