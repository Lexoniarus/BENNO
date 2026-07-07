"""Database models for BENNO."""

from datetime import UTC, datetime

from benno.enums import (
    AccountType,
    AiProvider,
    InsideSalesTaskStatus,
    ReminderStatus,
    ReportStatus,
    SessionLanguage,
    UserRole,
    ValidationStatus,
    VisitReportStatus,
)
from benno.extensions import db


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class TimestampMixin:
    """Common timestamp columns for mutable records."""

    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(db.Model, TimestampMixin):
    """A BENNO user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    username = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    preferred_language = db.Column(
        db.String(10),
        nullable=False,
        default=SessionLanguage.DE.value,
    )
    ai_provider_override = db.Column(db.String(50), nullable=True)
    external_sales_rep_id = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    chats = db.relationship("Chat", back_populates="sales_user")
    report_drafts = db.relationship("ReportDraft", back_populates="sales_user")
    final_reports = db.relationship("FinalReport", back_populates="sales_user")

    @property
    def is_admin(self) -> bool:
        """Return whether the user has the admin role."""
        return self.role == UserRole.ADMIN.value

    @property
    def is_authenticated(self) -> bool:
        """Return whether the user is authenticated."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return whether the user is anonymous."""
        return False

    def get_id(self) -> str:
        """Return the Flask-Login user identifier."""
        return str(self.id)

    @property
    def is_sales_rep(self) -> bool:
        """Return whether the user has the sales representative role."""
        return self.role == UserRole.SALES_REP.value


class GlobalSetting(db.Model, TimestampMixin):
    """Global BENNO settings."""

    __tablename__ = "global_settings"

    id = db.Column(db.Integer, primary_key=True)
    default_language = db.Column(
        db.String(10),
        nullable=False,
        default=SessionLanguage.DE.value,
    )
    ai_provider = db.Column(
        db.String(50),
        nullable=False,
        default=AiProvider.GEMINI.value,
    )


class Chat(db.Model, TimestampMixin):
    """A visit report chat session."""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    sales_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_language = db.Column(
        db.String(10),
        nullable=False,
        default=SessionLanguage.DE.value,
    )
    status = db.Column(
        db.String(50),
        nullable=False,
        default=ReportStatus.IN_PROGRESS.value,
    )

    sales_user = db.relationship("User", back_populates="chats")
    messages = db.relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    report_draft = db.relationship(
        "ReportDraft",
        back_populates="chat",
        cascade="all, delete-orphan",
        uselist=False,
    )
    final_report = db.relationship(
        "FinalReport",
        back_populates="chat",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ChatMessage(db.Model):
    """A single message inside a chat."""

    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    chat = db.relationship("Chat", back_populates="messages")


class ReportDraft(db.Model, TimestampMixin):
    """Structured in-progress report state."""

    __tablename__ = "report_drafts"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(
        db.Integer, db.ForeignKey("chats.id"), nullable=False, unique=True
    )
    sales_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    report_status = db.Column(
        db.String(50),
        nullable=False,
        default=ReportStatus.IN_PROGRESS.value,
    )
    session_language = db.Column(
        db.String(10),
        nullable=False,
        default=SessionLanguage.DE.value,
    )
    customer_context_type = db.Column(db.String(50), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("mock_customers.id"), nullable=True
    )
    lead_id = db.Column(db.Integer, db.ForeignKey("mock_leads.id"), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("mock_contacts.id"), nullable=True)
    visit_date = db.Column(db.Date, nullable=True)
    visit_type = db.Column(db.String(50), nullable=True)
    reason_code = db.Column(db.String(50), nullable=True)
    related_offer_id = db.Column(
        db.Integer, db.ForeignKey("mock_offers.id"), nullable=True
    )
    related_order_id = db.Column(
        db.Integer, db.ForeignKey("mock_orders.id"), nullable=True
    )
    external_offer_reference = db.Column(db.String(120), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Text, nullable=True)
    next_action = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    validation_status = db.Column(
        db.String(50),
        nullable=False,
        default=ValidationStatus.NOT_PROVIDED.value,
    )
    section_statuses_json = db.Column(db.JSON, nullable=False, default=dict)
    missing_sections_json = db.Column(db.JSON, nullable=False, default=list)
    ratings_json = db.Column(db.JSON, nullable=False, default=dict)
    draft_data_json = db.Column(db.JSON, nullable=False, default=dict)
    last_question = db.Column(db.Text, nullable=True)

    chat = db.relationship("Chat", back_populates="report_draft")
    sales_user = db.relationship("User", back_populates="report_drafts")
    account = db.relationship("MockAccount")
    customer = db.relationship("MockCustomer")
    lead = db.relationship("MockLead")
    contact = db.relationship("MockContact")
    related_offer = db.relationship("MockOffer")
    related_order = db.relationship("MockOrder")


class FinalReport(db.Model):
    """A confirmed or submitted visit report."""

    __tablename__ = "final_reports"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(
        db.Integer, db.ForeignKey("chats.id"), nullable=False, unique=True
    )
    sales_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("mock_customers.id"), nullable=True
    )
    lead_id = db.Column(db.Integer, db.ForeignKey("mock_leads.id"), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("mock_contacts.id"), nullable=True)
    visit_date = db.Column(db.Date, nullable=True)
    visit_type = db.Column(db.String(50), nullable=True)
    reason_code = db.Column(db.String(50), nullable=True)
    related_offer_id = db.Column(
        db.Integer, db.ForeignKey("mock_offers.id"), nullable=True
    )
    related_order_id = db.Column(
        db.Integer, db.ForeignKey("mock_orders.id"), nullable=True
    )
    external_offer_reference = db.Column(db.String(120), nullable=True)
    summary = db.Column(db.Text, nullable=False)
    outcome = db.Column(db.Text, nullable=True)
    next_action = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    ratings_json = db.Column(db.JSON, nullable=False, default=dict)
    report_language = db.Column(
        db.String(10),
        nullable=False,
        default=SessionLanguage.DE.value,
    )
    final_report_text = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(50),
        nullable=False,
        default=ReportStatus.CONFIRMED.value,
    )
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    chat = db.relationship("Chat", back_populates="final_report")
    sales_user = db.relationship("User", back_populates="final_reports")
    account = db.relationship("MockAccount")
    customer = db.relationship("MockCustomer")
    lead = db.relationship("MockLead")
    contact = db.relationship("MockContact")
    related_offer = db.relationship("MockOffer")
    related_order = db.relationship("MockOrder")
    inside_sales_tasks = db.relationship(
        "InsideSalesTask",
        back_populates="final_report",
        cascade="all, delete-orphan",
    )
    mock_visit_report = db.relationship(
        "MockVisitReport",
        back_populates="final_report",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MockAccount(db.Model):
    """Mock AKL-like account/address record."""

    __tablename__ = "mock_accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(120), nullable=False, unique=True)
    account_type = db.Column(
        db.String(10),
        nullable=False,
        default=AccountType.CUSTOMER.value,
    )
    search_name = db.Column(db.String(255), nullable=False, index=True)
    display_name = db.Column(db.String(255), nullable=False)
    address_text = db.Column(db.Text, nullable=True)
    address_restriction = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    contacts = db.relationship(
        "MockContact",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    offers = db.relationship(
        "MockOffer",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    orders = db.relationship(
        "MockOrder",
        back_populates="account",
        cascade="all, delete-orphan",
    )


class MockCrmUser(db.Model):
    """Mock CRM user or responsible user."""

    __tablename__ = "mock_crm_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    display_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class MockFieldSalesRepresentative(db.Model):
    """Mock field sales representative master data."""

    __tablename__ = "mock_field_sales_representatives"

    id = db.Column(db.Integer, primary_key=True)
    representative_number = db.Column(db.String(120), nullable=False, unique=True)
    display_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class InsideSalesTask(db.Model):
    """A follow-up task for inside sales."""

    __tablename__ = "inside_sales_tasks"

    id = db.Column(db.Integer, primary_key=True)
    linked_final_report_id = db.Column(
        db.Integer,
        db.ForeignKey("final_reports.id"),
        nullable=True,
    )
    task_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    detected_customer_name = db.Column(db.String(255), nullable=True)
    detected_contact_name = db.Column(db.String(255), nullable=True)
    related_customer_id = db.Column(
        db.Integer,
        db.ForeignKey("mock_customers.id"),
        nullable=True,
    )
    status = db.Column(
        db.String(50),
        nullable=False,
        default=InsideSalesTaskStatus.OPEN.value,
    )
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    final_report = db.relationship("FinalReport", back_populates="inside_sales_tasks")
    related_customer = db.relationship("MockCustomer")


class MockCustomer(db.Model):
    """Mock CRM/ERP customer."""

    __tablename__ = "mock_customers"

    id = db.Column(db.Integer, primary_key=True)
    external_customer_id = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    city = db.Column(db.String(120), nullable=True)
    industry = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    contacts = db.relationship(
        "MockContact",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    offers = db.relationship(
        "MockOffer",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    orders = db.relationship(
        "MockOrder",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class MockLead(db.Model):
    """Mock lead or address record."""

    __tablename__ = "mock_leads"

    id = db.Column(db.Integer, primary_key=True)
    external_lead_id = db.Column(db.String(120), nullable=False, unique=True)
    company_name = db.Column(db.String(255), nullable=False, index=True)
    contact_name = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    source = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class MockContact(db.Model):
    """Mock CRM/ERP contact."""

    __tablename__ = "mock_contacts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("mock_customers.id"), nullable=True
    )
    external_contact_id = db.Column(db.String(120), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=True)
    role_title = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    account = db.relationship("MockAccount", back_populates="contacts")
    customer = db.relationship("MockCustomer", back_populates="contacts")


class MockOffer(db.Model):
    """Mock CRM/ERP offer reference."""

    __tablename__ = "mock_offers"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("mock_customers.id"), nullable=True
    )
    external_offer_id = db.Column(db.String(120), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    account = db.relationship("MockAccount", back_populates="offers")
    customer = db.relationship("MockCustomer", back_populates="offers")


class MockOrder(db.Model):
    """Mock CRM/ERP order reference."""

    __tablename__ = "mock_orders"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("mock_customers.id"), nullable=True
    )
    external_order_id = db.Column(db.String(120), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    account = db.relationship("MockAccount", back_populates="orders")
    customer = db.relationship("MockCustomer", back_populates="orders")


class MockVisitReport(db.Model):
    """Mock eNVenta-shaped visit report write target."""

    __tablename__ = "mock_visit_reports"

    id = db.Column(db.Integer, primary_key=True)
    visit_report_number = db.Column(db.String(120), nullable=False, unique=True)
    final_report_id = db.Column(
        db.Integer,
        db.ForeignKey("final_reports.id"),
        nullable=False,
        unique=True,
    )
    visit_type = db.Column(db.String(50), nullable=False)
    visit_report_status = db.Column(
        db.String(50),
        nullable=False,
        default=VisitReportStatus.CLOSED.value,
    )
    report_status = db.Column(
        db.String(50),
        nullable=False,
        default=VisitReportStatus.CLOSED.value,
    )
    account_id = db.Column(db.Integer, db.ForeignKey("mock_accounts.id"), nullable=True)
    account_number = db.Column(db.String(120), nullable=True)
    account_type = db.Column(db.String(10), nullable=True)
    account_search_name = db.Column(db.String(255), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("mock_contacts.id"), nullable=True)
    contact_name = db.Column(db.String(255), nullable=True)
    field_sales_representative_id = db.Column(
        db.Integer,
        db.ForeignKey("mock_field_sales_representatives.id"),
        nullable=True,
    )
    responsible_user_id = db.Column(
        db.Integer,
        db.ForeignKey("mock_crm_users.id"),
        nullable=True,
    )
    visit_date = db.Column(db.Date, nullable=True)
    visit_time = db.Column(db.Time, nullable=True)
    target_topic = db.Column(db.Text, nullable=False)
    info_text = db.Column(db.Text, nullable=False)
    agreement_text = db.Column(db.Text, nullable=False)
    strength_text = db.Column(db.Text, nullable=True)
    weakness_text = db.Column(db.Text, nullable=True)
    customer_satisfaction_rating = db.Column(db.Integer, nullable=True)
    technical_attractiveness_rating = db.Column(db.Integer, nullable=True)
    commercial_attractiveness_rating = db.Column(db.Integer, nullable=True)
    priority_rating = db.Column(db.Integer, nullable=True)
    next_appointment_date = db.Column(db.Date, nullable=True)
    offer_reference = db.Column(db.String(255), nullable=True)
    order_reference = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    final_report = db.relationship("FinalReport", back_populates="mock_visit_report")
    account = db.relationship("MockAccount")
    contact = db.relationship("MockContact")
    field_sales_representative = db.relationship("MockFieldSalesRepresentative")
    responsible_user = db.relationship("MockCrmUser")
    reminders = db.relationship(
        "MockReminder",
        back_populates="visit_report",
        cascade="all, delete-orphan",
    )


class MockReminder(db.Model):
    """Mock eNVenta-like follow-up reminder."""

    __tablename__ = "mock_reminders"

    id = db.Column(db.Integer, primary_key=True)
    visit_report_number = db.Column(
        db.String(120),
        db.ForeignKey("mock_visit_reports.visit_report_number"),
        nullable=False,
        index=True,
    )
    due_date = db.Column(db.Date, nullable=True)
    owner_type = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(50),
        nullable=False,
        default=ReminderStatus.OPEN.value,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    created_by_user = db.relationship("User")
    visit_report = db.relationship("MockVisitReport", back_populates="reminders")
