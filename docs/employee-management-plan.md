# Employee Management & Payroll Plan

## Overview
This module aims to manage employee records, including their personal details, roles, and financial compensation (Salary, Bonuses, and Increments).

## 1. Database Schema (Backend)

We will introduce three new tables to handle employee data and financial history.

### `employees` Table
Stores core employee information.
- `id` (ULID, PK)
- `first_name` (String)
- `last_name` (String)
- `email` (String, Unique)
- `phone` (String)
- `position` (String) - e.g., "Cashier", "Manager"
- `hire_date` (Date)
- `base_salary` (Decimal) - Current monthly/hourly rate
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### `employee_bonuses` Table
Tracks one-time bonus payments.
- `id` (ULID, PK)
- `employee_id` (FK -> employees.id)
- `amount` (Decimal)
- `reason` (String)
- `date_awarded` (Date)
- `created_at` (DateTime)

### `salary_history` Table
Tracks salary increments and changes over time.
- `id` (ULID, PK)
- `employee_id` (FK -> employees.id)
- `previous_salary` (Decimal)
- `new_salary` (Decimal)
- `change_date` (Date)
- `reason` (String) - e.g., "Annual Increment", "Promotion"
- `created_at` (DateTime)

## 2. Backend API (`app/api/routers/employees.py`)

### Endpoints

#### Employee Management
- `GET /employees` - List all employees (with pagination/filtering).
- `POST /employees` - Create a new employee.
- `GET /employees/{id}` - Get details of a specific employee.
- `PATCH /employees/{id}` - Update employee details (excluding salary).

#### Financials
- `POST /employees/{id}/increment` - Update base salary and record history.
    - Payload: `{ "new_salary": 5000, "reason": "Performance Review" }`
- `POST /employees/{id}/bonus` - Record a bonus.
    - Payload: `{ "amount": 500, "reason": "Holiday Bonus" }`
- `GET /employees/{id}/financial-history` - Get list of past bonuses and salary changes.

## 3. Frontend Implementation (Modern Client)

### Sidebar
- Add **"Employees"** section (Icon: `badge` or `people_alt`).

### Views (`views/employees.py`)

#### Main List View
- Data Table showing: Name, Position, Email, Status.
- "Add Employee" button.

#### Employee Detail / Financial View
- **Profile Section**: Edit basic info.
- **Financial Overview**:
    - Current Base Salary (Large Text).
    - **Actions**:
        - [Button] "Grant Increment" -> Opens Modal.
        - [Button] "Give Bonus" -> Opens Modal.
- **History Tabs**:
    - **Bonuses**: Table of past bonuses.
    - **Salary Changes**: Table of salary progression.

## 4. Implementation Steps
1.  **Migration**: Create Alembic script `0015_create_employee_tables.py`.
2.  **Domain**: Define Entities and Repository interfaces.
3.  **Infrastructure**: Implement SQLAlchemy models and repositories.
4.  **API**: Create Routers and Schemas.
5.  **Frontend**: Build the UI views and integrate with API.
