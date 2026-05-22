"""
QuBE Seed Data - Healthcare + Business Domain

Generates realistic demo data using Faker.
"""

import random
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.models.models import (
    User, UserRole,
    Department,
    Employee,
    Patient, Gender,
    Service,
    Appointment, AppointmentStatus,
    Consultation,
    Invoice, InvoiceStatus,
    InvoiceItem,
    Payment, PaymentMethod,
    Receipt,
)

fake = Faker()
logger = get_logger("seeder")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def rand_date_past(days: int) -> datetime:
    delta = random.randint(1, days)
    return datetime.now(timezone.utc) - timedelta(days=delta)


def rand_future_date(days: int = 30) -> date:
    delta = random.randint(1, days)
    return (datetime.now(timezone.utc) + timedelta(days=delta)).date()


BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

INSURANCE_PROVIDERS = [
    "BlueCross BlueShield", "Aetna", "Cigna", "United Healthcare",
    "Humana", "Kaiser Permanente", "Medicare", "Medicaid", "Self-Pay",
]


# ─── Departments ──────────────────────────────────────────────────────────────

DEPARTMENTS_DATA = [
    ("Cardiology", "Heart and cardiovascular care", "Building A, Floor 3"),
    ("Radiology", "Imaging and diagnostic services", "Building B, Floor 1"),
    ("Emergency", "Emergency and trauma care", "Building A, Floor 1"),
    ("Orthopedics", "Bone and joint care", "Building C, Floor 2"),
    ("Pediatrics", "Children's healthcare", "Building D, Floor 2"),
    ("Oncology", "Cancer treatment and care", "Building E, Floor 4"),
    ("Neurology", "Brain and nervous system", "Building A, Floor 4"),
    ("General Surgery", "Surgical procedures", "Building B, Floor 3"),
    ("Finance", "Billing and financial operations", "Admin Building, Floor 2"),
    ("Administration", "Hospital administration", "Admin Building, Floor 1"),
]


async def seed_departments(session: AsyncSession) -> list[Department]:
    logger.info("Seeding departments...")
    departments = []
    for name, desc, location in DEPARTMENTS_DATA:
        dept = Department(name=name, description=desc, location=location, phone=fake.phone_number()[:20])
        session.add(dept)
        departments.append(dept)
    await session.flush()
    logger.info(f"  ✓ {len(departments)} departments")
    return departments


# ─── Users ────────────────────────────────────────────────────────────────────

async def seed_users(session: AsyncSession) -> list[User]:
    logger.info("Seeding users...")

    # Check if already seeded
    result = await session.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        logger.info("  ℹ️  Users already exist, skipping")
        return []

    users_data = [
        ("admin", "admin@qube.demo", "Admin123!", "Sarah Mitchell", UserRole.admin),
        ("analyst1", "analyst@qube.demo", "Analyst123!", "James Chen", UserRole.analyst),
        ("viewer1", "viewer@qube.demo", "Viewer123!", "Maria Santos", UserRole.viewer),
        ("john_doe", "john@qube.demo", "John123!", "John Doe", UserRole.analyst),
        ("jane_smith", "jane@qube.demo", "Jane123!", "Jane Smith", UserRole.analyst),
    ]

    users = []
    for username, email, password, full_name, role in users_data:
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        session.add(user)
        users.append(user)
    await session.flush()
    logger.info(f"  ✓ {len(users)} users (admin@qube.demo / Admin123!)")
    return users


# ─── Employees ────────────────────────────────────────────────────────────────

POSITIONS = [
    "Cardiologist", "Radiologist", "Emergency Physician", "Orthopedic Surgeon",
    "Pediatrician", "Oncologist", "Neurologist", "General Surgeon",
    "Nurse Practitioner", "Registered Nurse", "Medical Assistant",
    "Billing Specialist", "Administrative Coordinator", "Department Head",
    "Resident Physician", "Physician Assistant",
]


async def seed_employees(session: AsyncSession) -> list[Employee]:
    logger.info("Seeding employees...")
    result = await session.execute(select(Department))
    departments = list(result.scalars().all())

    employees = []
    for i in range(40):
        dept = random.choice(departments)
        hire_date = rand_date_past(365 * 8).date()
        emp = Employee(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number()[:20],
            position=random.choice(POSITIONS),
            department_id=dept.id,
            hire_date=hire_date,
            salary=Decimal(str(round(random.uniform(55000, 250000), 2))),
            is_active=random.random() > 0.05,
        )
        session.add(emp)
        employees.append(emp)
    await session.flush()
    logger.info(f"  ✓ {len(employees)} employees")
    return employees


# ─── Patients ─────────────────────────────────────────────────────────────────

async def seed_patients(session: AsyncSession) -> list[Patient]:
    logger.info("Seeding patients...")
    patients = []
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]

    for _ in range(120):
        dob = fake.date_of_birth(minimum_age=5, maximum_age=85)
        pat = Patient(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email() if random.random() > 0.1 else None,
            phone=fake.phone_number()[:20],
            date_of_birth=dob,
            gender=random.choice(list(Gender)),
            address=fake.street_address(),
            city=random.choice(cities),
            insurance_provider=random.choice(INSURANCE_PROVIDERS),
            insurance_number=fake.bothify("INS-####-????").upper() if random.random() > 0.2 else None,
            blood_type=random.choice(BLOOD_TYPES),
            is_active=True,
        )
        session.add(pat)
        patients.append(pat)
    await session.flush()
    logger.info(f"  ✓ {len(patients)} patients")
    return patients


# ─── Services ─────────────────────────────────────────────────────────────────

SERVICES_DATA = [
    ("General Consultation", "CONS-001", "Consultation", 150.00, 30),
    ("Specialist Consultation", "CONS-002", "Consultation", 250.00, 45),
    ("Emergency Consultation", "CONS-003", "Consultation", 350.00, 60),
    ("ECG Test", "CARD-001", "Cardiology", 120.00, 20),
    ("Echocardiogram", "CARD-002", "Cardiology", 450.00, 60),
    ("Stress Test", "CARD-003", "Cardiology", 380.00, 90),
    ("Chest X-Ray", "RAD-001", "Radiology", 180.00, 15),
    ("MRI Brain", "RAD-002", "Radiology", 1200.00, 45),
    ("CT Scan Abdomen", "RAD-003", "Radiology", 950.00, 30),
    ("Blood Panel Complete", "LAB-001", "Laboratory", 85.00, 15),
    ("Glucose Test", "LAB-002", "Laboratory", 35.00, 10),
    ("Lipid Profile", "LAB-003", "Laboratory", 65.00, 10),
    ("Orthopedic Evaluation", "ORTH-001", "Orthopedics", 280.00, 45),
    ("Bone Density Scan", "ORTH-002", "Orthopedics", 320.00, 30),
    ("Joint Injection", "ORTH-003", "Orthopedics", 420.00, 30),
    ("Pediatric Checkup", "PED-001", "Pediatrics", 130.00, 30),
    ("Vaccination", "PED-002", "Pediatrics", 80.00, 15),
    ("Chemotherapy Session", "ONC-001", "Oncology", 1800.00, 240),
    ("Radiation Therapy", "ONC-002", "Oncology", 2200.00, 60),
    ("Tumor Marker Test", "ONC-003", "Oncology", 180.00, 20),
    ("Neurological Assessment", "NEUR-001", "Neurology", 320.00, 60),
    ("EEG Test", "NEUR-002", "Neurology", 280.00, 45),
    ("Appendectomy", "SURG-001", "General Surgery", 4500.00, 120),
    ("Cholecystectomy", "SURG-002", "General Surgery", 6200.00, 90),
    ("Physical Therapy Session", "PT-001", "Physical Therapy", 110.00, 60),
]


async def seed_services(session: AsyncSession) -> list[Service]:
    logger.info("Seeding services...")
    services = []
    for name, code, category, price, duration in SERVICES_DATA:
        svc = Service(
            name=name,
            code=code,
            category=category,
            unit_price=Decimal(str(price)),
            duration_minutes=duration,
            is_active=True,
        )
        session.add(svc)
        services.append(svc)
    await session.flush()
    logger.info(f"  ✓ {len(services)} services")
    return services


# ─── Appointments ─────────────────────────────────────────────────────────────

async def seed_appointments(session: AsyncSession) -> list[Appointment]:
    logger.info("Seeding appointments...")

    patients_res = await session.execute(select(Patient))
    employees_res = await session.execute(select(Employee))
    depts_res = await session.execute(select(Department))
    services_res = await session.execute(select(Service))

    patients = list(patients_res.scalars().all())
    employees = list(employees_res.scalars().all())
    departments = list(depts_res.scalars().all())
    services = list(services_res.scalars().all())

    appointments = []

    # Status distribution: 60% completed, 25% scheduled, 10% cancelled, 5% no_show
    status_weights = [
        (AppointmentStatus.completed, 60),
        (AppointmentStatus.scheduled, 25),
        (AppointmentStatus.cancelled, 10),
        (AppointmentStatus.no_show, 5),
    ]
    statuses = [s for s, w in status_weights for _ in range(w)]

    for _ in range(250):
        status = random.choice(statuses)
        days_back = random.randint(1, 180)

        if status == AppointmentStatus.scheduled:
            # Future appointments
            appt_date = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 30))
        else:
            appt_date = datetime.now(timezone.utc) - timedelta(days=days_back)

        appt = Appointment(
            patient_id=random.choice(patients).id,
            department_id=random.choice(departments).id,
            doctor_id=random.choice(employees).id,
            service_id=random.choice(services).id,
            appointment_date=appt_date,
            status=status,
            notes=fake.sentence() if random.random() > 0.6 else None,
            follow_up_required=random.random() > 0.7,
        )
        session.add(appt)
        appointments.append(appt)

    await session.flush()
    logger.info(f"  ✓ {len(appointments)} appointments")
    return appointments


# ─── Consultations ────────────────────────────────────────────────────────────

DIAGNOSES = [
    "Hypertension", "Type 2 Diabetes", "Acute Myocardial Infarction",
    "Pneumonia", "Fractured Radius", "Migraine", "Gastroenteritis",
    "Appendicitis", "Osteoarthritis", "Anxiety Disorder",
    "Asthma", "COPD", "Anemia", "Urinary Tract Infection",
    "Lower Back Pain", "Hyperlipidemia", "Hypothyroidism",
]


async def seed_consultations(session: AsyncSession) -> list[Consultation]:
    logger.info("Seeding consultations...")

    appointments_res = await session.execute(
        select(Appointment).where(Appointment.status == AppointmentStatus.completed)
    )
    completed_appts = list(appointments_res.scalars().all())
    employees_res = await session.execute(select(Employee))
    employees = list(employees_res.scalars().all())

    consultations = []
    for appt in random.sample(completed_appts, min(180, len(completed_appts))):
        cons = Consultation(
            appointment_id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id or random.choice(employees).id,
            consultation_date=appt.appointment_date,
            diagnosis=random.choice(DIAGNOSES),
            symptoms=fake.sentence(nb_words=8),
            treatment_plan=fake.sentence(nb_words=12),
            prescription=f"{fake.word().capitalize()} {random.randint(50, 500)}mg" if random.random() > 0.3 else None,
            follow_up_date=rand_future_date(60) if random.random() > 0.5 else None,
            fee=Decimal(str(round(random.uniform(50, 300), 2))),
        )
        session.add(cons)
        consultations.append(cons)

    await session.flush()
    logger.info(f"  ✓ {len(consultations)} consultations")
    return consultations


# ─── Invoices ─────────────────────────────────────────────────────────────────

async def seed_invoices(session: AsyncSession) -> list[Invoice]:
    logger.info("Seeding invoices...")

    patients_res = await session.execute(select(Patient))
    services_res = await session.execute(select(Service))
    patients = list(patients_res.scalars().all())
    services = list(services_res.scalars().all())

    # Status distribution: 55% paid, 15% sent, 15% cancelled, 10% draft, 5% overdue
    status_pool = (
        [InvoiceStatus.paid] * 55 +
        [InvoiceStatus.sent] * 15 +
        [InvoiceStatus.cancelled] * 15 +
        [InvoiceStatus.draft] * 10 +
        [InvoiceStatus.overdue] * 5
    )

    invoices = []
    for i in range(350):
        status = random.choice(status_pool)
        days_back = random.randint(1, 365)
        created = datetime.now(timezone.utc) - timedelta(days=days_back)
        invoice_num = f"INV-{2024 if days_back > 180 else 2025}-{str(i + 1).zfill(5)}"

        # 1-4 line items per invoice
        n_items = random.randint(1, 4)
        inv_services = random.sample(services, min(n_items, len(services)))

        subtotal = Decimal("0")
        invoice_items_data = []
        for svc in inv_services:
            qty = random.randint(1, 3)
            discount = Decimal(str(random.choice([0, 0, 0, 5, 10, 15])))
            unit_price = svc.unit_price
            line_total = unit_price * qty * (1 - discount / 100)
            subtotal += line_total
            invoice_items_data.append((svc, qty, unit_price, discount, line_total))

        tax = round(subtotal * Decimal("0.08"), 2)
        total = subtotal + tax

        paid_date = None
        cancelled_reason = None
        if status == InvoiceStatus.paid:
            paid_date = (created + timedelta(days=random.randint(1, 30))).date()
        elif status == InvoiceStatus.cancelled:
            cancelled_reason = random.choice([
                "Patient requested cancellation",
                "Duplicate invoice",
                "Insurance rejected claim",
                "Services not rendered",
                "Patient transferred",
            ])

        inv = Invoice(
            invoice_number=invoice_num,
            patient_id=random.choice(patients).id,
            status=status,
            subtotal=round(subtotal, 2),
            tax_amount=tax,
            discount_amount=Decimal("0"),
            total_amount=round(total, 2),
            due_date=(created + timedelta(days=30)).date(),
            paid_date=paid_date,
            notes=fake.sentence() if random.random() > 0.8 else None,
            cancelled_reason=cancelled_reason,
            created_at=created,
            updated_at=created,
        )
        # Override auto-timestamps for realistic data
        inv.__dict__["created_at"] = created
        inv.__dict__["updated_at"] = created
        session.add(inv)
        await session.flush()

        # Add line items
        for svc, qty, unit_price, discount, line_total in invoice_items_data:
            item = InvoiceItem(
                invoice_id=inv.id,
                service_id=svc.id,
                description=svc.name,
                quantity=qty,
                unit_price=unit_price,
                discount_percent=discount,
                line_total=round(line_total, 2),
            )
            session.add(item)

        invoices.append(inv)

    await session.flush()
    logger.info(f"  ✓ {len(invoices)} invoices")
    return invoices


# ─── Payments + Receipts ──────────────────────────────────────────────────────

async def seed_payments_and_receipts(session: AsyncSession) -> None:
    logger.info("Seeding payments and receipts...")

    paid_invoices_res = await session.execute(
        select(Invoice).where(Invoice.status == InvoiceStatus.paid)
    )
    paid_invoices = list(paid_invoices_res.scalars().all())

    payment_count = 0
    receipt_count = 0

    for inv in paid_invoices:
        method = random.choice(list(PaymentMethod))
        payment = Payment(
            invoice_id=inv.id,
            amount=inv.total_amount,
            payment_method=method,
            payment_date=datetime.combine(inv.paid_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            reference_number=fake.bothify("REF-????-####").upper(),
        )
        session.add(payment)
        await session.flush()

        receipt = Receipt(
            receipt_number=f"RCP-{str(inv.id).zfill(6)}",
            invoice_id=inv.id,
            payment_id=payment.id,
            amount=inv.total_amount,
        )
        session.add(receipt)
        payment_count += 1
        receipt_count += 1

    await session.flush()
    logger.info(f"  ✓ {payment_count} payments, {receipt_count} receipts")
