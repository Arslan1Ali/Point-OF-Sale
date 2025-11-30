# Cashier Workflow & Permissions Plan

## Overview
This document outlines the workflow for Cashiers and the permission model ensuring strict separation of duties between Admins/Managers and Cashiers.

## Role Definitions

### Admin / Manager
- **Capabilities**:
    - Full access to all modules.
    - **Exclusive Right**: Create and manage employees (including Cashiers).
    - **Exclusive Right**: Manage Inventory (Add/Edit products, Stock adjustments).
    - View detailed financial reports.
- **Responsibilities**:
    - Onboarding new cashiers.
    - Setting salaries and bonuses.
    - Monitoring store performance.

### Cashier
- **Capabilities**:
    - **Primary Interface**: POS View (Point of Sale).
    - Process Sales (Scan products, accept payments).
    - View Product List (Read-only search).
    - View Customers (Read-only or Create new customer during checkout).
    - Process Returns (Subject to policy).
    - View own profile (optional).
- **Restrictions**:
    - **CANNOT** create or edit other employees.
    - **CANNOT** see salaries or bonuses of others.
    - **CANNOT** edit product details or stock levels manually.
    - **CANNOT** access backend admin panels.

## Authentication Flow
1.  **Login**: Cashier logs in with email/password.
2.  **Token Decoding**: The frontend decodes the JWT to determine the role (`CASHIER`).
3.  **Routing**:
    - Cashier is redirected to `POS View` instead of `Dashboard`.
    - Sidebar menu is filtered to show only relevant items (POS, Orders, Customers, Returns).

## Implementation Plan

### 1. Frontend Role Management
-   **Dependency**: Add `PyJWT` to `modern_client`.
-   **Logic**:
    -   Decode JWT on login.
    -   Store `user_role` in `ModernPOSApp` state.
    -   Expose `user_role` to all views.

### 2. UI Restrictions
-   **Sidebar**:
    -   Hide "Employees", "Inventory", "Dashboard" (maybe) for Cashiers.
-   **Employees View**:
    -   If a Cashier somehow accesses this view, hide "Add Employee" button.
    -   Hide "Financials" button.
-   **Inventory View**:
    -   Hide "Add Product" and "Edit" buttons.
    -   Make fields read-only.

### 3. Backend Enforcement (Already Implemented)
-   `create_employee` endpoint requires `MANAGEMENT_ROLES` (Admin/Manager).
-   `update_employee` endpoint requires `MANAGEMENT_ROLES`.
-   Inventory modification endpoints require `INVENTORY_ROLES`.

## Cashier Daily Workflow
1.  **Start Shift**: Log in.
2.  **Sales**:
    -   Go to POS.
    -   Add items to cart.
    -   Select/Create Customer.
    -   Checkout.
3.  **Returns**:
    -   Go to Returns view.
    -   Search by Order ID.
    -   Process return.
4.  **End Shift**: Log out.
