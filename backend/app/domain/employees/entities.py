from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from app.domain.common.errors import ValidationError
from app.domain.common.identifiers import new_ulid
from app.domain.common.money import Money


@dataclass(slots=True)
class EmployeeBonus:
    id: str
    employee_id: str
    amount: Money
    reason: str
    date_awarded: date
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(employee_id: str, amount: Money, reason: str, date_awarded: date | None = None) -> EmployeeBonus:
        if amount.amount <= 0:
            raise ValidationError("Bonus amount must be positive")
        if not reason:
            raise ValidationError("Bonus reason is required")
        
        return EmployeeBonus(
            id=new_ulid(),
            employee_id=employee_id,
            amount=amount,
            reason=reason,
            date_awarded=date_awarded or datetime.now(UTC).date(),
        )


@dataclass(slots=True)
class SalaryHistory:
    id: str
    employee_id: str
    previous_salary: Money
    new_salary: Money
    change_date: date
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        employee_id: str, 
        previous_salary: Money, 
        new_salary: Money, 
        reason: str, 
        change_date: date | None = None
    ) -> SalaryHistory:
        if not reason:
            raise ValidationError("Salary change reason is required")
            
        return SalaryHistory(
            id=new_ulid(),
            employee_id=employee_id,
            previous_salary=previous_salary,
            new_salary=new_salary,
            change_date=change_date or datetime.now(UTC).date(),
            reason=reason,
        )


@dataclass(slots=True)
class Employee:
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    position: str
    hire_date: date
    base_salary: Money
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        first_name: str,
        last_name: str,
        email: str,
        position: str,
        base_salary: Money,
        hire_date: date,
        phone: str | None = None,
    ) -> Employee:
        if not first_name or not last_name:
            raise ValidationError("First and last name are required")
        if not email:
            raise ValidationError("Email is required")
        if base_salary.amount < 0:
            raise ValidationError("Base salary cannot be negative")

        return Employee(
            id=new_ulid(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            position=position,
            hire_date=hire_date,
            base_salary=base_salary,
        )

    def update(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        position: str | None = None,
        is_active: bool | None = None,
    ) -> None:
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if position is not None:
            self.position = position
        if is_active is not None:
            self.is_active = is_active
        self.updated_at = datetime.now(UTC)

    def change_salary(self, new_salary: Money, reason: str, change_date: date | None = None) -> SalaryHistory:
        if new_salary.amount < 0:
            raise ValidationError("New salary cannot be negative")
        
        history = SalaryHistory.create(
            employee_id=self.id,
            previous_salary=self.base_salary,
            new_salary=new_salary,
            reason=reason,
            change_date=change_date,
        )
        
        self.base_salary = new_salary
        self.updated_at = datetime.now(UTC)
        return history

    def give_bonus(self, amount: Money, reason: str, date_awarded: date | None = None) -> EmployeeBonus:
        return EmployeeBonus.create(
            employee_id=self.id,
            amount=amount,
            reason=reason,
            date_awarded=date_awarded,
        )
