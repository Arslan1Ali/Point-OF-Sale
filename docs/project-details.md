# Retail POS System - Project Documentation

## 1. Project Overview
The Retail POS System is a modern, full-stack Point of Sale solution designed for retail environments. It features a robust backend API built with FastAPI and a responsive desktop client built with Flet (Python wrapper for Flutter). The system emphasizes security, clean architecture, and a streamlined user experience for different staff roles.

## 2. Architecture

### Backend (`/backend`)
- **Framework**: FastAPI (Python 3.11)
- **Architecture Pattern**: Clean Architecture (Domain-Driven Design principles)
    - **Domain Layer**: Core business logic and entities.
    - **Application Layer**: Use cases and business rules.
    - **Infrastructure Layer**: Database adapters, repositories, and external services.
    - **API Layer**: REST endpoints and request/response schemas.
- **Database**: SQLAlchemy (Async ORM) with Alembic for migrations. Supports SQLite (Dev) and PostgreSQL (Prod).
- **Authentication**: JWT (JSON Web Tokens) with Argon2 password hashing.

### Frontend (`/modern_client`)
- **Framework**: Flet (Python)
- **Pattern**: MVVM (Model-View-ViewModel) inspired structure.
- **Communication**: HTTP client (`httpx`) interacting with the Backend API.
- **UI Components**: Material Design 3 widgets.

## 3. Tech Stack

### Backend Dependencies
- `fastapi`: Web framework.
- `uvicorn`: ASGI server.
- `sqlalchemy` + `aiosqlite` / `asyncpg`: Database ORM and drivers.
- `pydantic`: Data validation.
- `alembic`: Database migrations.
- `python-ulid`: Unique identifiers.
- `passlib[argon2]`: Password hashing.
- `pyjwt`: Token handling.

### Frontend Dependencies
- `flet`: UI framework.
- `httpx`: Async HTTP client.
- `pyjwt`: Token decoding.

## 4. Key Features

### 🛒 POS Terminal
- Streamlined checkout interface.
- Product search by Name or SKU.
- Real-time cart calculation (Subtotal, Tax, Total).
- Transaction processing.

### 📦 Inventory Management
- Product CRUD (Create, Read, Update, Delete).
- Stock level tracking.
- Active/Inactive status toggling.
- Price and Cost management.

### 👥 Employee & User Management
- **Employee Records**: Manage personal details, positions, and salaries.
- **User Accounts**: Link employees to system login credentials.
- **Cashier Management**: Dedicated Admin view to manage Cashier accounts (Reset Password, Block/Unblock).

### 📊 Dashboard & Analytics
- Real-time overview of Total Sales, Order Counts, and Customer growth.
- Recent Sales activity feed.

### 🔄 Returns & Refunds
- Look up past orders by ID.
- Process refunds for returned items.

## 5. Role-Based Access Control (RBAC)

The system implements strict RBAC to ensure security and operational integrity.

| Role | Access Level | Accessible Modules |
| :--- | :--- | :--- |
| **ADMIN** | **Full Access** | Dashboard, POS, Orders, Inventory, Customers, Employees, Cashier Management, Returns |
| **MANAGER** | **Management** | Dashboard, POS, Orders, Inventory, Customers, Employees, Returns |
| **CASHIER** | **Restricted** | POS Terminal, Login, Logout |

> **Note**: Cashiers are strictly restricted to the POS view. They do not see the navigation sidebar and cannot access management modules.

## 6. Project Structure

```
/
├── backend/                # FastAPI Backend
│   ├── alembic/            # Database Migrations
│   ├── app/
│   │   ├── api/            # Routers & Schemas
│   │   ├── application/    # Use Cases
│   │   ├── core/           # Config & Security
│   │   ├── domain/         # Entities
│   │   └── infrastructure/ # DB & Repositories
│   └── tests/              # Backend Tests
│
├── modern_client/          # Flet Desktop Client
│   ├── components/         # Reusable UI Widgets (Sidebar, etc.)
│   ├── services/           # API Client
│   ├── views/              # UI Screens (POS, Dashboard, Users, etc.)
│   └── main.py             # Entry Point & Routing
│
├── docs/                   # Documentation
├── scripts/                # Utility Scripts (User creation, DB setup)
└── run_app.ps1             # Startup Script (Windows)
```

## 7. Getting Started

### Prerequisites
- Python 3.11+
- Poetry (Python Dependency Manager)

### Installation
1.  **Backend**:
    ```powershell
    cd backend
    poetry install
    ```
2.  **Frontend**:
    ```powershell
    cd modern_client
    poetry install
    ```

### Running the Application
Use the provided PowerShell script to launch both services:
```powershell
.\run_app.ps1
```
This will:
1.  Start the Backend server on `http://localhost:8000`.
2.  Launch the Desktop Client window.

## 8. Recent Updates (Nov 2025)
- **Strict RBAC**: Implemented navigation guards to lock Cashiers into the POS view.
- **Cashier Management**: Added a dedicated view for Admins to manage Cashier accounts efficiently.
- **UI Polish**: Fixed layout overflow issues and enabled hidden scrolling for a cleaner look.
- **Integrated Workflows**: Combined Employee and User creation into a single flow.
