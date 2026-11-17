# MAATRICARE.ai Frontend

React + Vite frontend starter for Fardeen's ASHA and Hospital/Doctor portals.

## Requirements
- Node.js 20 LTS or newer
- npm
- VS Code

## Run in VS Code
1. Extract this ZIP.
2. Open the `maatricare-frontend` folder in VS Code.
3. Open Terminal → New Terminal.
4. Run `npm install`.
5. Copy `.env.example` to `.env`.
6. Run `npm run dev`.
7. Open the URL printed by Vite (normally http://localhost:5173).

## Demo mode
The project starts with demonstration data. It does not authenticate real users, store real patient records, or make clinical decisions. The demo risk labels are illustrative only.

To connect Souryadeep's backend:
1. Set `VITE_API_BASE_URL` in `.env`.
2. Set `VITE_USE_DEMO_DATA=false`.
3. Confirm the actual endpoint paths, request schemas, response schemas, authentication method, and CORS settings with Souryadeep.
4. Update `src/services/api.js` to match the agreed API contract.

## Suggested Git workflow
```bash
git checkout develop
git pull origin develop
git checkout -b feature/asha-hospital-frontend
git add .
git commit -m "feat(frontend): scaffold ASHA and hospital portals"
git push -u origin feature/asha-hospital-frontend
```

Do not commit `.env`, API secrets, or identifiable patient data.

## Project structure
```text
src/
  components/       Shared UI components
  data/             Demonstration data only
  services/         API and offline queue
  App.jsx           Portal navigation and page rendering
  main.jsx          React entry point
  styles.css        Application styles
```

## Important clinical safety note
This is a frontend development scaffold, not a validated medical device. Never use the demonstration risk labels to guide real patient care. Clinical rules, thresholds, escalation pathways, and wording must be approved by qualified clinical reviewers.
