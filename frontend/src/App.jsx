
import { useEffect, useState } from "react";
import Login from "./pages/Login";
import { useAuth } from "./context/AuthContext";
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  HeartPulse,
  Plus,
  Search,
  ShieldCheck,
  Stethoscope,
  Users,
  Save,
  ClipboardCheck,
  MapPin,
  FileText
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatCard from "./components/StatCard";

import {
  getPatients,
  createPatient,
  createVisit,
  DEMO_MODE
} from "./services/api";

import {
  queueOfflineItem,
  getOfflineQueue,
  removeOfflineItem
} from "./services/offlineQueue";

const titles = {
  dashboard: "Overview",
  patients: "Patient directory",
  register: "Register patient",
  visit: "Clinical visit",
  referrals: "Referral management",
  timeline: "Patient timeline"
};

const riskClass = (risk) =>
  (risk || "unassessed").toLowerCase();

function RiskPill({ risk }) {
  return (
    <span className={`risk-pill ${riskClass(risk)}`}>
      {risk || "UNASSESSED"}
    </span>
  );
}

function SectionTitle({ title, subtitle, action }) {
  return (
    <div className="section-title">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

function readVisits() {
  try {
    return JSON.parse(
      localStorage.getItem("maatricare_visits") || "[]"
    );
  } catch {
    return [];
  }
}
// NEARBY HOSPITAL SEARCH


function HospitalFinder({ patients }) {
  const [selectedPatientId, setSelectedPatientId] = useState("");

  const selectedPatient = patients.find(
    (patient) => patient.id === selectedPatientId
  );

  const patientLocation = selectedPatient
    ? [selectedPatient.village, selectedPatient.district]
        .filter(Boolean)
        .join(", ")
    : "";

  function searchHospitals() {
    if (!selectedPatient) {
      alert("Please select a patient first.");
      return;
    }

    if (!patientLocation) {
      alert("This patient's village and district are not recorded.");
      return;
    }

    const url = `https://www.google.com/maps/search/hospitals+near+${encodeURIComponent(
      patientLocation
    )}`;

    window.open(url, "_blank");
  }

  return (
    <section className="panel">
      <SectionTitle
        title="Patient-wise Hospital Finder"
        subtitle="Find hospitals near a registered patient's location"
      />

      <div className="form-group">
        <label>Select Registered Patient</label>

        <select
          value={selectedPatientId}
          onChange={(e) => setSelectedPatientId(e.target.value)}
        >
          <option value="">Choose a patient...</option>

          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.name} ({patient.id})
            </option>
          ))}
        </select>
      </div>

      {selectedPatient && (
        <div className="patient-history">
          <h4>Patient Location</h4>
          <p><strong>Name:</strong> {selectedPatient.name}</p>
          <p><strong>Village:</strong> {selectedPatient.village || "Not recorded"}</p>
          <p><strong>District:</strong> {selectedPatient.district || "Not recorded"}</p>
        </div>
      )}

      <button
        className="primary-button"
        onClick={searchHospitals}
        disabled={!selectedPatient}
      >
        <MapPin size={16} /> Find Nearest Hospitals
      </button>

      <p className="muted-text">
        Hospital results and directions open in Google Maps.
        Results are approximate when using village and district.
      </p>
    </section>
  );
}

// DASHBOARD

function Dashboard({ portal, patients, visits, setPage, onSyncPending }) {
  const isAsha = portal === "asha";

  const today = new Date().toDateString();

  const visitsToday = visits.filter(
    (visit) =>
      visit.createdAt &&
      new Date(visit.createdAt).toDateString() === today
  ).length;

  const highRiskPatients = patients.filter(
    (patient) =>
      ["HIGH", "CRITICAL"].includes(
        (patient.risk || "").toUpperCase()
      )
  ).length;

  return (
    <>
      <div className="welcome-banner">
        <div>
          <span className="eyebrow">
            {isAsha
              ? "FRONTLINE CARE WORKSPACE"
              : "CLINICAL REVIEW WORKSPACE"}
          </span>

          <h2>
            {isAsha
              ? "Welcome to your ASHA workspace"
              : "Welcome to the hospital workspace"}
          </h2>

          <p>
            {isAsha
              ? "Manage registered patients and antenatal visits."
              : "Review patient records and referral information."}
          </p>
        </div>

        <div className="welcome-art">
          <HeartPulse size={78} />
        </div>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Registered patients"
          value={patients.length}
          hint="Total registered records"
          icon={Users}
        />

        <StatCard
          label={isAsha ? "Visits today" : "Total visits"}
          value={
            isAsha
              ? visitsToday
              : visits.length
          }
          hint="Recorded clinical visits"
          icon={CalendarDays}
          tone="green"
        />

        <StatCard
          label="High-risk cases"
          value={highRiskPatients}
          hint="Based on available assessment data"
          icon={AlertCircle}
          tone="orange"
        />

        <StatCard
  label={isAsha ? "Pending sync" : "Pending reviews"}
  value={
    isAsha
      ? getOfflineQueue().filter(
          (item) => item.status === "pending"
        ).length
      : "0"
  }
  hint={
    isAsha
      ? "Records waiting for backend sync"
      : "Not yet connected to backend"
  }
  icon={Clock3}
  tone="purple"
/>
      </div>

      {/* NEW: Upcoming Follow-ups section */}
      {isAsha && (
        <section className="panel">
          <SectionTitle
            title="Upcoming Follow-ups"
            subtitle="Patients scheduled for their next visit"
          />

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Patient ID</th>
                  <th>Follow-up Date</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {visits
                  .filter((visit) => visit.nextFollowUpDate)
                  .sort(
                    (a, b) =>
                      new Date(a.nextFollowUpDate) -
                      new Date(b.nextFollowUpDate)
                  )
                  .map((visit) => {
                    const patient = patients.find(
                      (p) => p.id === visit.patientId
                    );

                    if (!patient) return null;

                    return (
                      <tr key={visit.id}>
                        <td><b>{patient.name}</b></td>
                        <td>{patient.id}</td>
                        <td>{visit.nextFollowUpDate}</td>
                        <td>
                          {new Date(visit.nextFollowUpDate + "T00:00:00") <
                          new Date(new Date().toDateString())
                            ? "Overdue"
                            : "Scheduled"}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>

            {visits.filter((visit) => visit.nextFollowUpDate).length === 0 && (
              <div className="empty-state">
                No upcoming follow-ups scheduled.
              </div>
            )}
          </div>
        </section>
      )}
             

      {/* EXISTING: Offline patient registrations */}
      {isAsha && getOfflineQueue().some(
        (item) =>
          item.type === "patient" &&
          item.status === "pending"
      ) && (
        <section className="panel">
          <h3>Offline patient registrations</h3>
          <p>
            You have pending patient records waiting to be
            added to your local demo directory.
          </p>
          <button
            className="primary-button"
            onClick={onSyncPending}
          >
            <CheckCircle2 size={16} />
            Sync pending patients
          </button>
        </section>
      )}
      <div className="content-grid">
        <section className="panel">
          <SectionTitle
            title={isAsha ? "Recent patients" : "Registered patients"}
            subtitle="Records available in the system"
            action={
              <button
                className="text-button"
                onClick={() => setPage("patients")}
              >
                View all
              </button>
            }
          />

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Patient ID</th>
                  <th>Pregnancy</th>
                  <th>Risk</th>
                </tr>
              </thead>

              <tbody>
                {patients.slice(0, 5).map((patient) => (
                  <tr key={patient.id}>
                    <td>
                      <b>{patient.name}</b>
                      <small>{patient.village}</small>
                    </td>
                    <td>{patient.id}</td>
                    <td>
                      {patient.weeks
                        ? `${patient.weeks} weeks`
                        : "Not recorded"}
                    </td>
                    <td>
                      <RiskPill risk={patient.risk} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {patients.length === 0 && (
              <div className="empty-state">
                No patients registered yet.
                <p>Register your first patient to get started.</p>
                {isAsha && (
                  <button
                    className="primary-button"
                    onClick={() => setPage("register")}
                  >
                    <Plus size={16} /> Register patient
                  </button>
                )}
              </div>
            )}
          </div>
        </section>

        <section className="panel">
          <SectionTitle
            title="Care overview"
            subtitle="Clinical data summary"
          />

          <div className="empty-state">
            <HeartPulse size={30} />
            <p>No clinical trends available yet.</p>
            <small>
              Trends will appear when real visit measurements
              are available.
            </small>
          </div>
        </section>
      </div>

      <section className="panel">
        <SectionTitle
          title={isAsha ? "Care activity" : "Hospital activity"}
          subtitle="Recent recorded activity"
        />

        <div className="empty-state">
          No activity recorded yet.
        </div>
      </section>
    </>
  );
}

// PATIENT DIRECTORY

function Patients({ patients, visits, setPage }) {
  const [query, setQuery] = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);

  const normalizedQuery = query.trim().toLowerCase();
  const filtered = normalizedQuery
    ? patients.filter((patient) =>
        [patient.name, patient.id, patient.village]
          .filter(Boolean)
          .some((value) =>
            String(value).toLowerCase().includes(normalizedQuery)
          )
      )
    : patients;

  const getLatestVisit = (patientId) => {
    return visits
      .filter((visit) => visit.patientId === patientId)
      .sort(
        (a, b) =>
          new Date(b.createdAt || 0) -
          new Date(a.createdAt || 0)
      )[0];
  };

if (selectedPatient) {
  const patientVisits = visits.filter(
    (visit) => visit.patientId === selectedPatient.id
  );

  return (
    <section className="panel">
      <button
        className="text-button"
        onClick={() => setSelectedPatient(null)}
      >
        ← Back to Patients
      </button>

      <SectionTitle
        title={selectedPatient.name}
        subtitle={`Patient ID: ${selectedPatient.id}`}
      />

      <h3>Personal Information</h3>
      <p>Age: {selectedPatient.age || "—"}</p>
      <p>Phone: {selectedPatient.phone || "—"}</p>
      <p>Village: {selectedPatient.village || "—"}</p>
      <p>District: {selectedPatient.district || "—"}</p>
      <p>LMP: {selectedPatient.lmp || "—"}</p>
      <p>Gestational age: {selectedPatient.weeks || "—"} weeks</p>

      <h3>Medical History</h3>
      <p>Previous complications: {selectedPatient.previousComplications || "—"}</p>
      <p>Pre-existing diabetes: {selectedPatient.preexistingDiabetes || "—"}</p>
      <p>Gestational diabetes: {selectedPatient.gestationalDiabetes || "—"}</p>
      <p>Hypertension: {selectedPatient.hypertension || "—"}</p>
      <p>Other conditions: {selectedPatient.otherConditions || "—"}</p>

      <h3>Clinical Visit History</h3>

      {patientVisits.length === 0 ? (
        <p>No clinical visits recorded.</p>
      ) : (
        patientVisits.map((visit) => (
          <div className="timeline-visit" key={visit.id}>
            <p><strong>Date:</strong> {visit.createdAt ? new Date(visit.createdAt).toLocaleString() : "—"}</p>
            <p>Blood pressure: {visit.bp || "—"}/{visit.diastolic || "—"}</p>
            <p>Blood glucose: {visit.fastingBloodGlucose || "—"}</p>
            <p>HbA1c: {visit.hba1c || "—"}</p>
            <p>BMI: {visit.bmi || "—"}</p>
            <p>Heart rate: {visit.heartRate || "—"}</p>
            <p>Temperature: {visit.temperature || "—"}</p>
            <p>Weight: {visit.weight || "—"}</p>
            <p>Symptoms: {visit.symptoms || "—"}</p>
            <p>Next follow-up: {visit.nextFollowUpDate || "—"}</p>
          </div>
        ))
      )}
    </section>
  );
}


  return (
    <section className="panel">
      <SectionTitle
        title="Patient directory"
        subtitle={`${patients.length} registered patient records`}
        action={
          <button
            className="primary-button"
            onClick={() => setPage("register")}
          >
            <Plus size={16} /> Register patient
          </button>
        }
      />

      <div className="search-field">
        <Search size={17} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, ID or village..."
        />
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Patient</th>
<th>ID</th>
<th>Age</th>
<th>Village</th>
<th>Gestation</th>
<th>Blood Pressure</th>
<th>Fasting Glucose</th>
<th>HbA1c</th>
<th>BMI</th>
<th>Heart Rate</th>
<th>Temperature</th>
<th>Risk</th>
            </tr>
          </thead>

          <tbody>
  {filtered.map((patient) => {
    const latestVisit = getLatestVisit(patient.id);

    return (
      <tr
        key={patient.id}
        onClick={() => setSelectedPatient(patient)}
        style={{ cursor: "pointer" }}
      >
        <td>
          <b>{patient.name}</b>
          <small>{patient.phone}</small>
        </td>

        <td>{patient.id}</td>
        <td>{patient.age || "—"}</td>
        <td>{patient.village || "—"}</td>

        <td>
          {patient.weeks ? `${patient.weeks} weeks` : "—"}
        </td>

        <td>
          {latestVisit
            ? `${latestVisit.bp || "—"}/${latestVisit.diastolic || "—"}`
            : "—"}
        </td>

        <td>{latestVisit?.fastingBloodGlucose || "—"}</td>
        <td>{latestVisit?.hba1c || "—"}</td>
        <td>{latestVisit?.bmi || "—"}</td>
        <td>{latestVisit?.heartRate || "—"}</td>
        <td>{latestVisit?.temperature || "—"}</td>

        <td>
          <RiskPill risk={patient.risk} />
        </td>
      </tr>
    );
  })}
</tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <div className="empty-state">
          {patients.length === 0
            ? "No patients registered yet."
            : "No matching patients found."}
        </div>
      )}
    </section>
  );
}

// FORM FIELD

function Field({ label, ...props }) {
  return (
    <div className="field">
      <label>
        {label}
        {props.required && <em> *</em>}
      </label>
      <input {...props} />
    </div>
  );
}

// PATIENT REGISTRATION

function RegisterPatient({ onPatientCreated }) {
  
const emptyForm = {
  name: "",
  age: "",
  phone: "",
  village: "",
  district: "",
  lmp: "",
  weeks: "",
  nextFollowUpDate: "",
  history: "",
  previousComplications: "Unknown",
preexistingDiabetes: "Unknown",
gestationalDiabetes: "Unknown",
hypertension: "Unknown",
  otherConditions: ""
};


  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const update = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  
async function submit(e) {
  e.preventDefault();
  setMessage("");

  const age = Number(form.age);
  const weeks = form.weeks === "" ? null : Number(form.weeks);
  const phone = form.phone.trim();

  if (age < 15 || age > 55) {
    setMessage("Please enter an age between 15 and 55 years.");
    return;
  }

  if (phone && !/^[6-9]\d{9}$/.test(phone)) {
    setMessage("Please enter a valid 10-digit Indian mobile number.");
    return;
  }

  if (weeks !== null && (weeks < 0 || weeks > 45)) {
    setMessage("Gestational age must be between 0 and 45 weeks.");
    return;
  }

  setSaving(true);

  try {
    if (!navigator.onLine) {
      await queueOfflineItem("patient", form);
      setMessage(
        "Patient saved to this device's offline queue. It is not yet registered in the central database."
      );
    } else {
      const savedPatient = await createPatient(form);
      onPatientCreated(savedPatient);

      setMessage("Patient registration completed successfully.");
    }

    setForm(emptyForm);
  } catch (error) {
    console.error(error);
    setMessage("Unable to save patient. Please try again.");
  } finally {
    setSaving(false);
  }
}

  return (
    <section className="panel form-panel">
      <SectionTitle
        title="Register a patient"
        subtitle="Enter maternal health patient details"
      />

      <form onSubmit={submit}>
        <div className="form-section-label">
          PERSONAL INFORMATION
        </div>

        <div className="form-grid">
          <Field
            label="Patient full name"
            name="name"
            value={form.name}
            onChange={update}
            required
            placeholder="Enter full name"
          />

          <Field
            label="Age"
            name="age"
            type="number"
            min="1"
            value={form.age}
            onChange={update}
            required
            placeholder="Age in years"
          />

          <Field
            label="Phone number"
            name="phone"
            value={form.phone}
            onChange={update}
            placeholder="Contact number"
          />

          <Field
            label="Village / locality"
            name="village"
            value={form.village}
            onChange={update}
            required
            placeholder="Village name"
          />

          <Field
            label="District"
            name="district"
            value={form.district}
            onChange={update}
            placeholder="District"
          />

          <Field
            label="Last menstrual period (LMP)"
            name="lmp"
            type="date"
            value={form.lmp}
            onChange={update}
          />

          <Field
            label="Gestational age (weeks)"
            name="weeks"
            type="number"
            min="0"
            max="45"
            value={form.weeks}
            onChange={update}
            placeholder="e.g. 20"
          />

          
<div className="field">
  <label>Previous pregnancy complications</label>
  <select
    name="previousComplications"
    value={form.previousComplications}
    onChange={update}
  >
    <option value="No">No</option>
    <option value="Yes">Yes</option>
    <option value="Unknown">Unknown</option>
  </select>
</div>

<div className="field">
  <label>Pre-existing diabetes</label>
  <select
    name="preexistingDiabetes"
    value={form.preexistingDiabetes}
    onChange={update}
  >
    <option value="No">No</option>
    <option value="Yes">Yes</option>
    <option value="Unknown">Unknown</option>
  </select>
</div>

<div className="field">
  <label>Gestational diabetes</label>
  <select
    name="gestationalDiabetes"
    value={form.gestationalDiabetes}
    onChange={update}
  >
    <option value="No">No</option>
    <option value="Yes">Yes</option>
    <option value="Unknown">Unknown</option>
  </select>
</div>

<div className="field">
  <label>History of hypertension</label>
  <select
    name="hypertension"
    value={form.hypertension}
    onChange={update}
  >
    <option value="No">No</option>
    <option value="Yes">Yes</option>
    <option value="Unknown">Unknown</option>
  </select>
</div>

<div className="field full">
  <label>Other medical conditions</label>
  <textarea
    name="otherConditions"
    value={form.otherConditions}
    onChange={update}
    placeholder="Enter other relevant medical conditions"
  />
</div>

        </div>

        <div className="form-footer">
          <span className="muted-text">
            Only enter authorized patient information.
          </span>

          <button
            className="primary-button"
            type="submit"
            disabled={saving}
          >
            <Save size={16} />
            {saving ? "Saving..." : "Save patient"}
          </button>
        </div>

        {message && (
          <div className="notice">
            <CheckCircle2 size={17} />
            {message}
          </div>
        )}
      </form>
    </section>
  );
}

// CLINICAL VISIT

function VisitForm({ patients, onVisitCreated }) {
  


const [form, setForm] = useState({
  patientId: "",
  bp: "",
  diastolic: "",
  fastingBloodGlucose: "",
  hba1c: "",
  bmi: "",
  heartRate: "",
  temperature: "",
  weight: "",
  weeks: "",
  nextFollowUpDate: "",
  symptoms: ""
});




  const [message, setMessage] = useState("");

  const update = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  async function submit(e) {
    e.preventDefault();
    setMessage("");

    if (!form.patientId) {
      setMessage("Please register or select a patient first.");
      return;
    }

    try {
      if (!navigator.onLine) {
        await queueOfflineItem("visit", {
  ...form,
  age: patients.find(
    (patient) => patient.id === form.patientId
  )?.age || ""
});
        setMessage("Visit added to the device's offline queue.");
      } else {
        const selectedPatient = patients.find(
  (patient) => patient.id === form.patientId
);

const savedVisit = await createVisit({
  ...form,
  age: selectedPatient?.age || ""
});
        onVisitCreated(savedVisit);

        setMessage(
          DEMO_MODE
            ? "Visit saved in browser testing storage. No risk assessment has been performed."
            : "Clinical visit successfully saved."
        );
      }
    } catch (error) {
      console.error(error);
      setMessage("Unable to save visit.");
    }
  }

  return (
    <section className="panel form-panel">
      <SectionTitle
        title="New clinical visit"
        subtitle="Record antenatal visit measurements"
      />

      <div className="safety-note">
        <ShieldCheck size={18} />
        <span>
          Enter measurements recorded by an authorized health
          worker. This frontend does not calculate clinical risk.
        </span>
      </div>

      {patients.length === 0 ? (
        <div className="empty-state">
          No registered patients available.
          <p>Register a patient before recording a visit.</p>
        </div>
      ) : (
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="field">
              <label>Patient</label>
              <select
                name="patientId"
                value={form.patientId}
                onChange={update}
                required
              >
                <option value="">Select patient</option>

                {patients.map((patient) => (
                  <option
                    key={patient.id}
                    value={patient.id}
                  >
                    {patient.name} · {patient.id}
                  </option>
                ))}
              </select>
            </div>

            <Field
  label="Gestational age (weeks)"
  name="weeks"
  type="number"
  value={form.weeks}
  onChange={update}
  placeholder="e.g. 20"
/>

<Field
  label="Next follow-up date"
  name="nextFollowUpDate"
  type="date"
  value={form.nextFollowUpDate}
  onChange={update}
/>

            <Field
              label="Systolic BP (mmHg)"
              name="bp"
              type="number"
              value={form.bp}
              onChange={update}
              placeholder="Value"
            />

            <Field
              label="Diastolic BP (mmHg)"
              name="diastolic"
              type="number"
              value={form.diastolic}
              onChange={update}
              placeholder="Value"
            />

            <Field
  label="Fasting Blood Glucose (mg/dL)"
  name="fastingBloodGlucose"
  type="number"
  value={form.fastingBloodGlucose}
  onChange={update}
  placeholder="Fasting glucose value"
/>

<Field
  label="HbA1c (%)"
  name="hba1c"
  type="number"
  step="0.1"
  value={form.hba1c}
  onChange={update}
  placeholder="HbA1c value"
/>

<Field
  label="BMI (kg/m²)"
  name="bmi"
  type="number"
  step="0.1"
  value={form.bmi}
  onChange={update}
  placeholder="BMI value"
/>

            <Field
              label="Heart rate (bpm)"
              name="heartRate"
              type="number"
              value={form.heartRate}
              onChange={update}
              placeholder="Value"
            />

            <Field
              label="Temperature (°C)"
              name="temperature"
              type="number"
              value={form.temperature}
              onChange={update}
              placeholder="Value"
            />

            <Field
              label="Weight (kg)"
              name="weight"
              type="number"
              value={form.weight}
              onChange={update}
              placeholder="Value"
            />

            <div className="field full">
              <label>Symptoms / visit notes</label>
              <textarea
                name="symptoms"
                value={form.symptoms}
                onChange={update}
                placeholder="Document visit observations"
              />
            </div>
          </div>

          <div className="form-footer">
            <span className="muted-text">
              No automatic risk prediction is available.
            </span>

            <button className="primary-button" type="submit">
              <Save size={16} /> Save visit
            </button>
          </div>

          {message && (
            <div className="notice">
              <CheckCircle2 size={17} />
              {message}
            </div>
          )}
        </form>
      )}
    </section>
  );
}

// REFERRALS

function Referrals() {
  const [status, setStatus] = useState("All");

  const referrals = [];

  const filteredReferrals =
    status === "All"
      ? referrals
      : referrals.filter(
          (referral) => referral.status === status
        );

  return (
    <section className="panel">
      <SectionTitle
        title="Referral management"
        subtitle="Review and manage maternal health referrals"
      />

      <div className="referral-toolbar">
        <div>
          <strong>Referral records</strong>
          <p>{referrals.length} total referrals</p>
        </div>

        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="All">All statuses</option>
          <option value="Pending">Pending</option>
          <option value="Reviewed">Reviewed</option>
          <option value="Completed">Completed</option>
        </select>
      </div>

      {filteredReferrals.length === 0 ? (
        <div className="empty-state">
          No referral records available.
          <p>
            Referrals will appear here when generated
            through the connected clinical workflow.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Referral ID</th>
                <th>Hospital</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {filteredReferrals.map((referral) => (
                <tr key={referral.id}>
                  <td>{referral.patientName}</td>
                  <td>{referral.id}</td>
                  <td>{referral.hospital}</td>
                  <td>{referral.reason}</td>
                  <td>{referral.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// PATIENT TIMELINE

function Timeline({ patients, visits }) {
  return (
    <section className="panel">
      <SectionTitle
        title="Patient timeline"
        subtitle="Patient history and clinical visit records"
      />

      {patients.length === 0 ? (
        <div className="empty-state">
          No patient records available.
        </div>
      ) : (
        patients.map((patient) => {
          const patientVisits = visits.filter(
            (visit) => visit.patientId === patient.id
          );

          return (
            <div className="timeline-card" key={patient.id}>
              <h3>{patient.name}</h3>
              <p>Patient ID: {patient.id}</p>
              <p>Registration date: {
                patient.createdAt
                  ? new Date(patient.createdAt).toLocaleDateString()
                  : "—"
                             }</p>

              {/* INSERT HERE */}
              <h4>Medical history</h4>

              <div className="patient-history">
                <p>Previous pregnancy complications: {patient.previousComplications || "Not recorded"}</p>
                <p>Pre-existing diabetes: {patient.preexistingDiabetes || "Not recorded"}</p>
                <p>Gestational diabetes: {patient.gestationalDiabetes || "Not recorded"}</p>
                <p>History of hypertension: {patient.hypertension || "Not recorded"}</p>
                <p>Other medical conditions: {patient.otherConditions || "Not recorded"}</p>
              </div>

              <h4>Clinical visit history</h4>

              {patientVisits.length === 0 ? (
                <p>No clinical visits recorded yet.</p>
              ) : (
                patientVisits.map((visit) => (
                  <div className="timeline-visit" key={visit.id}>
                    <p><strong>Date:</strong> {
                      visit.createdAt
                        ? new Date(visit.createdAt).toLocaleString()
                        : "—"
                    }</p>
                    <p>Blood pressure: {visit.bp || "—"}/{visit.diastolic || "—"} mmHg</p>
                    <p>Fasting Blood Glucose: {visit.fastingBloodGlucose || "—"} mg/dL</p>
<p>HbA1c: {visit.hba1c || "—"} %</p>
<p>BMI: {visit.bmi || "—"} kg/m²</p>
                    <p>Heart rate: {visit.heartRate || "—"} bpm</p>
                    <p>Temperature: {visit.temperature || "—"} °C</p>
                    <p>Weight: {visit.weight || "—"} kg</p>
                    <p>Notes: {visit.symptoms || "—"}</p>
                  </div>
                ))
              )}
            </div>
          );
        })
      )}
    </section>
  );
}
// MAIN APPLICATION

 
// MAIN APPLICATION

export default function App() {
  const { isAuthenticated } = useAuth();

  const [portal, setPortal] = useState("asha");
  const [page, setPage] = useState("dashboard");
  const [online, setOnline] = useState(navigator.onLine);

  const [patients, setPatients] = useState([]);
  const [visits, setVisits] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    async function loadData() {
      try {
        const patientData = await getPatients();
        setPatients(Array.isArray(patientData) ? patientData : []);
        setVisits(DEMO_MODE ? readVisits() : []);
      } catch (error) {
        console.error("Unable to load patient records:", error);
        setLoadError("Unable to load patient records.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [isAuthenticated]);

  function handlePatientCreated(patient) {
    setPatients((current) => [
      patient,
      ...current.filter((p) => p.id !== patient.id)
    ]);
  }
  
async function handleSyncPendingPatients() {
  if (!DEMO_MODE) {
    alert("Demo sync is available only in demo mode.");
    return;
  }

  const pendingPatients = getOfflineQueue().filter(
    (item) =>
      item.type === "patient" &&
      item.status === "pending"
  );

  if (pendingPatients.length === 0) {
    alert("No pending patients to sync.");
    return;
  }

  let syncedCount = 0;

  for (const item of pendingPatients) {
    try {
      const savedPatient = await createPatient(item.payload);

      handlePatientCreated(savedPatient);
      removeOfflineItem(item.id);

      syncedCount++;
    } catch (error) {
      console.error("Patient sync failed:", error);
    }
  }

  alert(
    `${syncedCount} patient(s) added to the local demo directory.`
  );
}


  function handleVisitCreated(visit) {
    setVisits((current) => [visit, ...current]);
  }

  // Show login before displaying the dashboard
  if (!isAuthenticated) {
    return <Login />;
  }

  const title = titles[page] || "Overview";

  let content;

  if (loading) {
    content = (
      <section className="panel empty-state">
        Loading patient records...
      </section>
    );
  } else if (page === "dashboard") {
    content = (
      <Dashboard
        portal={portal}
        patients={patients}
        visits={visits}
        setPage={setPage}
        onSyncPending={handleSyncPendingPatients}
      />
    );
  } else if (page === "patients") {
    content = (
      <Patients
  patients={patients}
  visits={visits}
  setPage={setPage}
/>
    );
  } else if (page === "register") {
    content = (
      <RegisterPatient
        onPatientCreated={handlePatientCreated}
      />
    );
  } else if (page === "visit") {
    content = (
      <VisitForm
        patients={patients}
        onVisitCreated={handleVisitCreated}
      />
    );
  }else if (page === "referrals") {
    content = <Referrals />;
  } else if (page === "hospital-finder") {
    content = <HospitalFinder patients={patients} />;
  } else {
    content = (
      <Timeline
        patients={patients}
        visits={visits}
      />
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        portal={portal}
        page={page}
        setPage={setPage}
        setPortal={setPortal}
      />

      <main className="main-area">
        <Topbar
  title={title}
  online={online}
  patients={patients}
  visits={visits}
  setPage={setPage}
/>


        <div className="page-content">
          {loadError && (
            <div className="notice">
              <AlertCircle size={17} />
              {loadError}
            </div>
          )}

          {content}

          <footer className="footer">
            MAATRICARE.ai · Frontend prototype
            <span>
              For demonstration and development only · Not for clinical use
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}
