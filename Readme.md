# 4PM CHAI LOVERS
# 🚀 Smart Test Impact Analysis (TIA) Engine

## 📌 Background
Current test execution pipelines often follow a static approach where a predefined set of test cases is executed for every build or commit, regardless of the scope or impact of the code changes. This results in unnecessary execution of irrelevant test cases, increased execution time, and inefficient utilization of CI/CD resources.

## 💡 Our Solution
A smart, dynamic test execution mechanism that analyzes Git commit history and codebase modifications to identify and trigger *only* the relevant subset of test cases impacted by those changes. 

## 🛠 Tech Stack
* **Backend & Core Logic:** Python, FastAPI, GitPython, `ast` module, Pytest
* **Frontend & Visualization:** React (Vite), Tailwind CSS, Recharts
* **DevOps & Version Control:** Git, GitHub Actions, Ngrok

---

## 🗺️ Project Roadmap (24-Hour Execution Plan)

### Phase 1: Ingestion & Diff Extraction
- [ ] Initialize Python virtual environment and Vite React app.
- [ ] Setup dummy target application with a basic unit test suite.
- [ ] Implement Git commit parser using `GitPython` to extract modified files and specific line changes.

### Phase 2: Dependency Mapping (The Brains)
- [ ] Build the core mapping engine using Python's `ast` module.
- [ ] Parse target application files to create a dependency graph between source files and test files.
- [ ] Establish a robust mapping linking modified source code functions to their corresponding tests.

### Phase 3: Selective Execution
- [ ] Integrate the test runner (Pytest) with the mapping engine output.
- [ ] Dynamically construct test execution commands to run only the impacted tests.
- [ ] Capture key execution metrics: Time taken, total tests, tests skipped, and tests run.

### Phase 4: Visualization & Integration
- [ ] Develop a React dashboard to display execution statistics.
- [ ] Implement visual comparisons (Full Pipeline Run vs. Smart Run) using Recharts.
- [ ] Connect the FastAPI backend metrics to the frontend UI for live updates.

### Phase 5: Pipeline Simulation & Demo Polish
- [ ] Finalize end-to-end integration with a simulated GitHub PR webhook via Ngrok.
- [ ] Prepare presentation script emphasizing the "Time Saved" and optimized resource metrics.
- [ ] Conduct rigorous dry runs of the live demo.

---

## 💻 Local Development Setup (Ubuntu/Linux)

### Prerequisites
* Git
* VS Code
* Node.js (for React frontend)
* Python 3.9+ (for FastAPI backend)

### 1️⃣ Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be running at `http://localhost:5173`.

### 2️⃣ Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file inside the `/backend` folder and add your GitHub OAuth App credentials:
```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

**Run the Server:**
Using Uvicorn, run the FastAPI backend pointing to our updated architecture:
```bash
uvicorn app.main:app --reload
```
The API engine will be running at `http://localhost:8000`.
* VS Code
* Node.js (for React frontend)
* Python 3.x