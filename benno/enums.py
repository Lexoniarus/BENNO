"""Controlled internal codes for BENNO."""

from enum import StrEnum


class AiProvider(StrEnum):
    """Supported AI provider codes."""

    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"


class UserIntent(StrEnum):
    """Allowed intent labels for interpreted user messages."""

    ANSWER = "answer"
    CORRECTION = "correction"
    ADDITIONAL_INFO = "additional_info"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    REPEAT = "repeat"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


class CustomerContextType(StrEnum):
    """Customer or lead context for a report draft."""

    EXISTING_CUSTOMER = "existing_customer"
    EXISTING_LEAD = "existing_lead"
    NEW_LEAD = "new_lead"
    UNCLEAR = "unclear"


class AccountType(StrEnum):
    """AKL-like account type codes."""

    ADDRESS = "A"
    CUSTOMER = "K"
    SUPPLIER = "L"


class InsideSalesTaskStatus(StrEnum):
    """Lifecycle status for inside sales tasks."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class InsideSalesTaskType(StrEnum):
    """Canonical inside sales task types."""

    COMPLETE_MASTER_DATA = "complete_master_data"
    CREATE_OFFER = "create_offer"
    CLARIFY_DETAILS = "clarify_details"
    FOLLOW_UP_CALL = "follow_up_call"


class MessageSender(StrEnum):
    """Allowed chat message senders."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(StrEnum):
    """Allowed chat message types."""

    FREE_INPUT = "free_input"
    ASSISTANT_QUESTION = "assistant_question"
    ASSISTANT_CONFIRMATION = "assistant_confirmation"
    CORRECTION = "correction"
    FINAL_REVIEW = "final_review"
    SYSTEM_EVENT = "system_event"


class ReasonCode(StrEnum):
    """Visit reason codes."""

    OFFER_FOLLOW_UP = "offer_follow_up"
    NEW_DEMAND = "new_demand"
    RELATIONSHIP_MEETING = "relationship_meeting"
    CONTRACT_DISCUSSION = "contract_discussion"
    LEAD_INITIAL_CONTACT = "lead_initial_contact"
    COMPLAINT_RELATED = "complaint_related"
    OTHER = "other"


class ReportSection(StrEnum):
    """Internal report sections used before final eNVenta field mapping."""

    CUSTOMER_CONTEXT = "customer_context"
    VISIT_TYPE = "visit_type"
    VISIT_DATE = "visit_date"
    CONTACTS = "contacts"
    VISIT_REASON = "visit_reason"
    SUMMARY = "summary"
    OUTCOME = "outcome"
    NEXT_ACTION = "next_action"
    NEXT_APPOINTMENT_DATE = "next_appointment_date"
    OFFER_REFERENCE = "offer_reference"
    ORDER_REFERENCE = "order_reference"
    STRENGTHS = "strengths"
    WEAKNESSES = "weaknesses"
    RATINGS = "ratings"
    REMINDERS = "reminders"
    FINAL_REPORT = "final_report"
    USER_CONFIRMATION = "user_confirmation"


class ReportStatus(StrEnum):
    """Lifecycle status for report work."""

    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    INSIDE_SALES_INPUT_REQUIRED = "inside_sales_input_required"
    BLOCKED = "blocked"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class ReminderOwnerType(StrEnum):
    """Owner domains for mock eNVenta reminders."""

    CRM_USER = "crm_user"
    FIELD_SALES_REPRESENTATIVE = "field_sales_representative"


class ReminderStatus(StrEnum):
    """Lifecycle status for mock eNVenta reminders."""

    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class SectionStatus(StrEnum):
    """Status values for individual report sections."""

    OPEN = "open"
    DETECTED = "detected"
    UNCLEAR = "unclear"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    NOT_APPLICABLE = "not_applicable"


class SessionLanguage(StrEnum):
    """Supported session languages."""

    DE = "de"
    EN = "en"


class UserRole(StrEnum):
    """BENNO user roles."""

    SALES_REP = "sales_rep"
    ADMIN = "admin"


class ValidationStatus(StrEnum):
    """Validation status for CRM/ERP references."""

    NOT_PROVIDED = "not_provided"
    DETECTED_UNVALIDATED = "detected_unvalidated"
    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    CONFIRMED_NEW = "confirmed_new"


class VisitType(StrEnum):
    """Visit type codes."""

    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    PHONE = "phone"


class VisitReportStatus(StrEnum):
    """Mock eNVenta visit report status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
