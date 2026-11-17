
import axios from "axios";

const DEMO_MODE = import.meta.env.VITE_USE_DEMO_DATA !== "false";

const PATIENTS_KEY = "maatricare_patients";
const VISITS_KEY = "maatricare_visits";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("maatricare_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Read temporary browser data
function readLocalData(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

// Save temporary browser data
function saveLocalData(key, data) {
  localStorage.setItem(key, JSON.stringify(data));
}

// Get patients
export async function getPatients() {
  if (DEMO_MODE) {
    return readLocalData(PATIENTS_KEY);
  }

  const { data } = await api.get("/patients");
  return data;
}

// Register patient

export async function createPatient(payload) {
  if (DEMO_MODE) {
    const patients = readLocalData(PATIENTS_KEY);

    const newPatient = {
      ...payload,
      id: `MAT-${Date.now()}`,
      createdAt: new Date().toISOString(),
      storageMode: "browser-demo"
    };

    patients.push(newPatient);
    saveLocalData(PATIENTS_KEY, patients);

    return newPatient;
  }

  const { data } = await api.post("/patients", payload);
  return data;
}

// Create clinical visit
export async function createVisit(payload) {
  if (DEMO_MODE) {
    const visits = readLocalData(VISITS_KEY);

    const newVisit = {
      ...payload,
      id: `VISIT-${Date.now()}`,
      createdAt: new Date().toISOString(),
      storageMode: "browser-demo"
    };

    visits.push(newVisit);
    saveLocalData(VISITS_KEY, visits);

    return newVisit;
  }

  const { data } = await api.post("/visits", payload);
  return data;
}

// Get referrals
export async function getReferrals() {
  if (DEMO_MODE) {
    return [];
  }

  const { data } = await api.get("/referrals");
  return data;
}

export { DEMO_MODE };
