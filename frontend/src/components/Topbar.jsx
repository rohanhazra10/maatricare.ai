
import { useState } from "react";
import { Bell, Search, Wifi, WifiOff, X } from "lucide-react";

export default function Topbar({ title, online, patients = [], visits = [], setPage }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const filteredPatients = patients.filter((patient) =>
  [patient.name, patient.id, patient.village]
    .filter(Boolean)
    .some((value) =>
      String(value)
        .toLowerCase()
        .includes(query.trim().toLowerCase())
    )
);
const [notificationsOpen, setNotificationsOpen] = useState(false);

const today = new Date();
today.setHours(0, 0, 0, 0);

const notifications = visits
  .filter((visit) => visit.nextFollowUpDate)
  .map((visit) => {
    const patient = patients.find(
      (p) => p.id === visit.patientId
    );

    const followUpDate = new Date(
      visit.nextFollowUpDate + "T00:00:00"
    );

    return {
      id: visit.id,
      patientName: patient?.name || "Unknown patient",
      date: visit.nextFollowUpDate,
      overdue: followUpDate < today
    };
  });

  // ADD NOTIFICATION CODE HERE

  return (
    <header className="topbar">
      <div>
        <div className="breadcrumb">
          MAATRICARE.ai <span>/</span> Workspace
        </div>
        <h1>{title || "Dashboard"}</h1>
      </div>

      <div className="top-actions">
        <div className={`connection ${online ? "online" : "offline"}`}>
          {online ? <Wifi size={15} /> : <WifiOff size={15} />}
          {online ? "Online" : "Offline"}
        </div>

        <button
          className="icon-button"
          aria-label="Search"
          onClick={() => setSearchOpen(!searchOpen)}
        >
          {searchOpen ? <X size={19} /> : <Search size={19} />}
        </button>

        <button
  className="icon-button"
  aria-label="Notifications"
  onClick={() => setNotificationsOpen(!notificationsOpen)}
>
  <Bell size={19} />
  <i />
</button>

        <div className="avatar">FK</div>
      </div>

      {searchOpen && (
        <div className="global-search">
          <Search size={17} />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search patients..."
          />
          <button onClick={() => setQuery("")}>Clear</button>
          <div className="global-search-results">
  {query.trim() !== "" && (
    filteredPatients.length > 0 ? (
      filteredPatients.map((patient) => (
        <button
          key={patient.id}
          className="global-search-result"
          onClick={() => {
            setPage("patients");
            setSearchOpen(false);
            setQuery("");
          }}
        >
          <strong>{patient.name}</strong>
          <small>
            {patient.id} · {patient.village || "Village not recorded"}
          </small>
        </button>
      ))
    ) : (
      <p>No matching patients found.</p>
    )
  )}
</div>
        </div>
      )}
            {notificationsOpen && (
        <div className="notification-panel">
          <h3>Notifications</h3>

          {notifications.length === 0 ? (
            <p>No follow-up notifications available.</p>
          ) : (
            notifications.map((item) => (
              <div key={item.id} className="notification-item">
                <strong>{item.patientName}</strong>

                <p>
                  {item.overdue
                    ? "Overdue follow-up"
                    : "Upcoming follow-up"}
                </p>

                <small>{item.date}</small>
              </div>
            ))
          )}
        </div>
      )}
    </header>
  );
}
