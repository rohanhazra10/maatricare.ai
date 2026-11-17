
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { HeartPulse, LockKeyhole, Mail } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Unable to log in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo">
            <HeartPulse size={30} />
          </div>
          <h1>MAATRICARE<span>.ai</span></h1>
          <p>Maternal Healthcare Management Platform</p>
        </div>

        <div className="login-heading">
          <h2>ASHA Worker Login</h2>
          <p>Sign in to access your healthcare workspace.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label>Email address</label>
          <div className="login-input">
            <Mail size={18} />
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <label>Password</label>
          <div className="login-input">
            <LockKeyhole size={18} />
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="login-demo-note">
          Frontend demonstration mode. Authentication is not yet
          connected to the central server.
        </div>

        <footer>MAATRICARE.ai · ASHA Workspace</footer>
      </div>
    </div>
  );
}
