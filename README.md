# ScrapLink

Welcome to **ScrapLink**! This repository houses both the Frontend and Backend services for the project.

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [1. Cloning the Repository](#1-cloning-the-repository)
- [2. Git Branching & Contribution Workflow](#2-git-branching--contribution-workflow)
- [3. Running the Frontend](#3-running-the-frontend)
- [4. Running the Backend](#4-running-the-backend)
- [Project Structure](#-project-structure)

---

## ⚙️ Prerequisites

Before getting started, make sure you have the following installed on your machine:

- **Git** (for version control)
- **Node.js** (v18 or higher) and **npm**
- **Python** (v3.12 or higher)
- *(Optional)* **uv** (Fast Python package installer and dependency manager)

---

## 1. Cloning the Repository

To clone the entire repository onto your local system, run:

```bash
git clone <REPOSITORY_URL>
cd ScrapLink
```
> Replace `<REPOSITORY_URL>` with your actual Git clone link.

---

## 2. Git Branching & Contribution Workflow

To keep the `main` branch stable, **do not commit directly to `main`**. Always create your own local feature branch, publish it remotely, and submit a Pull Request (PR).

### Step-by-Step Branching Guide:

1. **Switch to `main` and get the latest updates:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create and switch to your feature branch:**
   Use a descriptive name (e.g., `feature/login-page`, `fix/api-error`, `feat/scraping-logic`):
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Publish your branch to the remote repository:**
   Set the upstream branch on the remote server:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. **Work on your feature & commit changes locally:**
   ```bash
   git add .
   git commit -m "feat: add user authentication layout"
   ```

5. **Push your changes to your remote branch:**
   ```bash
   git push
   ```

6. **Create a Pull Request (PR):**
   - Go to the repository page on GitHub / GitLab / Bitbucket.
   - You will see a prompt to **Compare & pull request** for your branch (`feature/your-feature-name`).
   - Fill out the PR description, assign reviewers, and open the PR.
   - Once approved and tested, merge your PR into `main`.

---

## 3. Running the Frontend

The Frontend is built using **React** and **Vite**.

1. **Navigate to the `Frontend` folder:**
   ```bash
   cd Frontend
   ```

2. **Install node dependencies:**
   ```bash
   npm install
   ```

3. **Configure Environment Variables:**
   If `.env.example` exists, create your `.env` file:
   ```bash
   cp .env.example .env
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. Open your browser and visit `http://localhost:5173`.

---

## 4. Running the Backend

The Backend is built with **Python 3.12+**.

1. **Navigate to the `Backend` folder:**
   ```bash
   cd Backend
   ```

2. **Configure Environment Variables:**
   If `.env.example` exists, create your `.env` file:
   ```bash
   cp .env.example .env
   ```

3. **Set up virtual environment & install dependencies:**

   - **Option A: Using standard Python (`venv`)**
     ```bash
     # Create virtual environment
     python -m venv .venv

     # Activate virtual environment
     # On Windows (PowerShell):
     .\.venv\Scripts\Activate.ps1
     # On macOS / Linux:
     source .venv/bin/activate

     # Install dependencies
     pip install -r requirements.txt
     ```

   - **Option B: Using `uv` (Recommended)**
     ```bash
     uv sync
     ```

4. **Run the Backend server:**
   ```bash
   # Standard Python
   python main.py

   # Or using uv
   uv run main.py
   ```

---

## 📁 Project Structure

```text
ScrapLink/
├── Backend/             # Python backend code & scripts
│   ├── main.py          # Entry point
│   ├── pyproject.toml   # Project configuration & dependencies
│   └── .env.example     # Environment variables template
├── Frontend/            # Vite + React web application
│   ├── src/             # Source code (Components, Pages, App)
│   ├── package.json     # Node dependencies & scripts
│   └── .env.example     # Environment variables template
└── README.md            # Repository documentation
```
