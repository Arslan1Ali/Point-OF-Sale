from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    position: str = Field(min_length=1, max_length=100)
    hire_date: date
    base_salary: Decimal = Field(ge=0)


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    position: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None


class EmployeeOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    position: str
    hire_date: date
    base_salary: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = dict(from_attributes=True)


class BonusCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=255)
    date_awarded: date | None = None


class BonusOut(BaseModel):
    id: str
    employee_id: str
    amount: Decimal
    reason: str
    date_awarded: date
    created_at: datetime

    model_config = dict(from_attributes=True)


class IncrementCreate(BaseModel):
    new_salary: Decimal = Field(ge=0)
    reason: str = Field(min_length=1, max_length=255)
    change_date: date | None = None


class SalaryHistoryOut(BaseModel):
    id: str
    employee_id: str
    previous_salary: Decimal
    new_salary: Decimal
    change_date: date
    reason: str
    created_at: datetime

    model_config = dict(from_attributes=True)
