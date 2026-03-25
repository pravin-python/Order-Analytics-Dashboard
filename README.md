# 📦 OrderPulse v2: Order Analytics Dashboard (Flask)

OrderPulse is a production-grade Flask dashboard designed to fetch, process, and analyze sales orders from the Unicommerce OMS. It features secure credential management, background task processing with SocketIO progress tracking, and flexible multi-database persistence.

---

## 🚀 Quick Start (Running the Project)

### 1. Prerequisites
- **Python 3.9+**
- (Optional) **MySQL/PostgreSQL/MariaDB** if not using the default SQLite.

### 2. Setup Environment
Open your terminal in the project root and run:

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### 3. Configure `.env`
Create a `.env` file in the root directory (one should be there if you're upgrading) and ensure it has the following variables:

```env
# Flask Core
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=generate-a-secure-random-string

# 🔐 Security (REQUIRED for credential storage)
# Generate a 32-byte Fernet key using: cryptography.fernet.Fernet.generate_key().decode()
ENCRYPTION_KEY=YOUR_32_BYTE_FERNET_KEY

# 🗄️ Database Configuration
# Options: sqlite, mysql, postgresql
DB_TYPE=sqlite

# For SQLite:
DB_NAME=instance/orderpulse_v2.db

# For MySQL/Postgres (Optional):
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=password
```

### 4. Run the Application
Run the Following Command:
```bash
python run.py
```
Logout into the dashboard at: `http://localhost:5002`

---

## 🏗️ Project Architecture

| Component | Responsibility |
| :--- | :--- |
| **`app/services/task_manager.py`** | Handles background order fetching using a Thread Pool. |
| **`app/services/order_service.py`** | Business logic for Unicommerce API calls and analytics calculations. |
| **`app/models/order.py`** | Persistent database schema for Orders and Packages. |
| **`app/utils/encryption.py`** | Symmetric (Fernet) encryption for securing API credentials. |
| **`app/routes/api.py`** | Decoupled API endpoints for syncing and reading data. |

---

## 🔐 Key Features & Commands

### 🔄 Order Sync Logic
- The system uses a **Fetch-then-Read** approach.
- Click **"Load Orders"** on the UI to trigger a background sync via `POST /api/fetch-orders`.
- The dashboard UI automatically polls `GET /api/orders` to render data straight from the local Database once synced.

### 🛡️ Secure Credentials
- All API usernames and passwords saved in **Settings** are encrypted using a 32-byte unique key.
- Never hardcode your API password in the code! Always use the dashboard's "Settings" panel to save them.

### 📊 Multi-DB Support
The system dynamically connects to your chosen database based on `DB_TYPE` in `.env`.
- **SQLite**: Zero configuration (Default).
- **MySQL/Postgres**: Provide host and credentials in `.env`, and ensure the relevant drivers (`pymysql` or `psycopg2`) are installed.

---

## 🛠️ Common Commands

| Task | Command |
| :--- | :--- |
| **Initialize DB** | `flask init-db` |
| **Generate Encryption Key** | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| **Debug Mode** | Debugging is enabled by default in `run.py`. |

---

## 📁 Folder Structure
```text
Order-Analytics-Dashboard/
├── app/
│   ├── models/       # DB Schemas (SQLAlchemy)
│   ├── routes/       # API & Page Routing
│   ├── services/     # Task Logic & API Wrappers
│   ├── static/       # JS, CSS, Media Assets
│   └── templates/    # HTML View files
├── instance/         # Default SQLite storage
├── run.py            # Main entry point (Port 5002)
├── config.py         # Dynamic multi-DB config
└── .env              # Secrets & environment variables
```
