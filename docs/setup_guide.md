# 🛠️ DataForge — Setup, Launch & User Guide

Everything you need to install, run, and use DataForge.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 16+** with npm

---

## One-Time Setup

```bash
# 1. Create virtual environment and install backend dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..
```

---

## Running the App

### Option A — Browser Mode
```bash
./start_app.sh
```
Opens the backend on port **8000** and frontend on port **5173**.  
Navigate to `http://localhost:5173` in your browser.

### Option B — Desktop App (Electron)
```bash
cd electron-app
npm start
```
A native window opens automatically. The backend and frontend start in the background — a loading screen is shown while they boot (~5–10 seconds), then the full app loads.  
Closing the window kills all background processes cleanly.

---

## The Workspace

The interface has three zones:

| Zone | Location | Purpose |
|---|---|---|
| **Control Panel** | Left sidebar | Column selector, statistics, operation buttons |
| **Data Preview** | Centre | Live scrollable table (first 100 rows). Click a column to select it |
| **Console & Log** | Bottom | History of applied steps + NLP command input |

---

## Applying Transformations

**Option 1 — Buttons:** Click a column in the preview table → choose an operation from the sidebar.

**Option 2 — NLP Console:** Type a natural language command at the bottom, e.g.:
```
fill age with mean
scale salary between 0 and 1
validate email format in contact_col
remove outliers from age
```
See [nlp_commands.md](./nlp_commands.md) for the full command reference.

---

## Column Statistics Panel

When you click a column, a compact stats card appears at the top of the sidebar showing:
- Detected type, Null count, Null %, Unique count
- Min / Max / Mean (for numeric columns)
- Sample values (for text columns)

Stats **automatically refresh** after every operation.

---

## Pipeline Management

| Action | How |
|---|---|
| Undo a step | Click `✕` next to the step in the log |
| Reset all steps | Click **Reset** |
| Save pipeline | Click **Save Pipeline** in the header |
| Apply saved pipeline to new dataset | Click **Apply Template** |
| Export cleaned data | Click **Export CSV** or **Export Excel** |

---

## Quality Alerts

DataForge auto-scans your dataset on load and flags:
- Columns with high null percentages
- Columns with mixed types (numbers + text)

Alerts are shown in the header of the workspace.

---

## Data Integrity & Safety

- **Type Safety** — The system blocks operations that would corrupt column types (e.g. filling a numeric column with text).
- **Replay Consistency** — Pipelines are replayed from the original file, guaranteeing bit-perfect results.
- **100% Offline** — No data ever leaves your machine.

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Loading screen stuck (Electron) | venv or Node not found | Run `./start_app.sh` manually to check errors |
| "Operation Blocked: Implicit Cast" | Tried to fill numeric col with text | Use Convert Type first, or use a numeric fill value |
| "No Data Loaded" in preview | Dataset empty or backend error | Click Reset; re-import if corrupted |
| NLP command not recognised | Phrasing too complex | Use simple keywords: `drop`, `fill`, `scale`, `validate` |
| Port conflict (8000 / 5173) | Another process using the port | `lsof -ti:8000 \| xargs kill` and `lsof -ti:5173 \| xargs kill` |
