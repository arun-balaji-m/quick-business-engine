import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.core.config import settings

S = settings.db_schema  # shorthand for schema name


# ─── Enumerations ────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    cancelled = "cancelled"
    overdue = "overdue"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    insurance = "insurance"
    bank_transfer = "bank_transfer"


class TicketStatus(str, enum.Enum):
    open = "OPEN"
    in_progress = "IN_PROGRESS"
    closed = "CLOSED"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


# ─── User ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, schema=S), default=UserRole.analyst, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="user")
    query_histories: Mapped[list["QueryHistory"]] = relationship(
        "QueryHistory", back_populates="user"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")


# ─── Department ──────────────────────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="department")
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="department"
    )


# ─── Employee ─────────────────────────────────────────────────────────────────

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.departments.id"), index=True
    )
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="employees"
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation", back_populates="doctor"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="doctor"
    )


# ─── Patient ─────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender, schema=S))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    insurance_provider: Mapped[str | None] = mapped_column(String(100))
    insurance_number: Mapped[str | None] = mapped_column(String(50))
    blood_type: Mapped[str | None] = mapped_column(String(5))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="patient"
    )
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="patient")
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation", back_populates="patient"
    )


# ─── Service ─────────────────────────────────────────────────────────────────

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    invoice_items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="service"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="service"
    )


# ─── Appointment ─────────────────────────────────────────────────────────────

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.patients.id"), nullable=False, index=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.departments.id"), index=True
    )
    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.employees.id"), index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.services.id"), index=True
    )
    appointment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, schema=S), default=AppointmentStatus.scheduled, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="appointments"
    )
    doctor: Mapped["Employee | None"] = relationship("Employee", back_populates="appointments")
    service: Mapped["Service | None"] = relationship("Service", back_populates="appointments")
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation", back_populates="appointment"
    )


# ─── Consultation ─────────────────────────────────────────────────────────────

class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.appointments.id"), index=True
    )
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.patients.id"), nullable=False, index=True
    )
    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.employees.id"), index=True
    )
    consultation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text)
    symptoms: Mapped[str | None] = mapped_column(Text)
    treatment_plan: Mapped[str | None] = mapped_column(Text)
    prescription: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Relationships
    appointment: Mapped["Appointment | None"] = relationship(
        "Appointment", back_populates="consultations"
    )
    patient: Mapped["Patient"] = relationship("Patient", back_populates="consultations")
    doctor: Mapped["Employee | None"] = relationship("Employee", back_populates="consultations")


# ─── Invoice ─────────────────────────────────────────────────────────────────

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.patients.id"), nullable=False, index=True
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, schema=S), default=InvoiceStatus.draft, nullable=False, index=True
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    paid_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    cancelled_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="invoices")
    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="invoice")
    receipts: Mapped[list["Receipt"]] = relationship("Receipt", back_populates="invoice")


# ─── InvoiceItem ─────────────────────────────────────────────────────────────

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.invoices.id"), nullable=False, index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.services.id"), index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
    service: Mapped["Service | None"] = relationship("Service", back_populates="invoice_items")


# ─── Payment ─────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.invoices.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, schema=S), nullable=False
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reference_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")
    receipt: Mapped["Receipt | None"] = relationship("Receipt", back_populates="payment", uselist=False)


# ─── Receipt ─────────────────────────────────────────────────────────────────

class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.invoices.id"), nullable=False, index=True
    )
    payment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.payments.id"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    issued_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="receipts")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="receipt")


# ─── Ticket ──────────────────────────────────────────────────────────────────

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.users.id"), nullable=False, index=True
    )
    query_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.query_history.id"), index=True
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, schema=S), default=TicketStatus.open, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    is_satisfied: Mapped[bool | None] = mapped_column(Boolean)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    query: Mapped["QueryHistory | None"] = relationship("QueryHistory", back_populates="ticket")


# ─── QueryHistory ─────────────────────────────────────────────────────────────

class QueryHistory(Base):
    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(f"{S}.users.id"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    result_count: Mapped[int | None] = mapped_column(Integer)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    tables_used: Mapped[str | None] = mapped_column(Text)  # JSON array stored as string

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="query_histories")
    ticket: Mapped["Ticket | None"] = relationship("Ticket", back_populates="query")


# ─── AuditLog ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(f"{S}.users.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")


# ─── DashboardCache ──────────────────────────────────────────────────────────

class DashboardCache(Base):
    __tablename__ = "dashboard_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    data: Mapped[str | None] = mapped_column(Text)  # JSON
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
