import {
  Activity,
  LayoutDashboard,
  Users,
  UserPlus,
  ClipboardList,
  GitPullRequest,
  HeartPulse,
  LogOut,
  MapPin
} from "lucide-react";

const ashaItems = [
  ["Dashboard", "dashboard", LayoutDashboard],
  ["Patients", "patients", Users],
  ["Register patient", "register", UserPlus],
  ["New clinical visit", "visit", ClipboardList],
  ["Patient timeline", "timeline", Activity],
  ["Hospital Finder", "hospital-finder", MapPin]
];

const hospitalItems = [
  ["Dashboard", "dashboard", LayoutDashboard],
  ["Referrals", "referrals", GitPullRequest],
  ["Patients", "patients", Users],
  ["Patient timeline", "timeline", Activity]
];

export default function Sidebar({ portal, page, setPage, setPortal }) {
  const items = portal === "asha" ? ashaItems : hospitalItems;

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <HeartPulse size={22} />
        </div>
        <div>
          <strong>
            MAATRICARE<span>.ai</span>
          </strong>
          <small>Maternal care platform</small>
        </div>
      </div>

      <div className="portal-switch">
        <button
          className={portal === "asha" ? "selected" : ""}
          onClick={() => {
            setPortal("asha");
            setPage("dashboard");
          }}
        >
          ASHA Portal
        </button>

        <button
          className={portal === "hospital" ? "selected" : ""}
          onClick={() => {
            setPortal("hospital");
            setPage("dashboard");
          }}
        >
          Hospital Portal
        </button>
      </div>

      <p className="nav-label">WORKSPACE</p>

      <nav>
        {items.map(([label, key, Icon]) => (
          <button
            key={key}
            className={`nav-item ${page === key ? "active" : ""}`}
            onClick={() => setPage(key)}
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="profile">
          <div className="avatar">FK</div>
          <div>
            <b>Fardeen Khan</b>
            <small>
              {portal === "asha"
                ? "ASHA Worker · Demo"
                : "Hospital Staff · Demo"}
            </small>
          </div>
        </div>

        <button
          className="nav-item"
          onClick={() => {
            setPortal("asha");
            setPage("dashboard");
          }}
        >
          <LogOut size={18} />
          <span>Switch workspace</span>
        </button>

        <small className="version">Frontend prototype · v1.0</small>
      </div>
    </aside>
  );
}