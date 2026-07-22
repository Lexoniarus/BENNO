"""Sales user routes for BENNO."""

from typing import Any

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from benno.auth import sales_required
from benno.enums import ReportStatus
from benno.models import Chat, FinalReport
from benno.services.ai_provider import get_ai_service, get_ai_status
from benno.services.report_loop import (
    apply_report_correction,
    build_report_review,
    cancel_report,
    confirm_report,
    is_ready_for_review,
    process_report_message,
    start_report_chat,
)
from benno.services.report_state import display_value

sales_blueprint = Blueprint("sales", __name__, url_prefix="/sales")

OPEN_REPORT_STATUSES = (
    ReportStatus.IN_PROGRESS.value,
    ReportStatus.READY_FOR_REVIEW.value,
    ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value,
    ReportStatus.BLOCKED.value,
)
REPORT_STATUS_LABELS_DE = {
    ReportStatus.BLOCKED.value: "Blockiert",
    ReportStatus.CANCELLED.value: "Abgebrochen",
    ReportStatus.CONFIRMED.value: "Best\u00e4tigt",
    ReportStatus.IN_PROGRESS.value: "In Bearbeitung",
    ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value: "Innendienst n\u00f6tig",
    ReportStatus.READY_FOR_REVIEW.value: "Bereit zur Pr\u00fcfung",
    ReportStatus.SUBMITTED.value: "\u00dcbergeben",
}
REPORT_SECTION_LABELS_DE = {
    "contacts": "Teilnehmer",
    "customer_context": "Kunde oder Lead",
    "final_report": "Finaler Bericht",
    "info_text": "Info",
    "next_action": "N\u00e4chster Schritt",
    "next_appointment_date": "Termin ab",
    "offer_reference": "Angebotsbezug",
    "order_reference": "Auftragsbezug",
    "outcome": "Vereinbarung",
    "ratings": "Bewertungen",
    "reminders": "Wiedervorlagen",
    "strengths": "St\u00e4rke",
    "summary": "Info",
    "user_confirmation": "Best\u00e4tigung",
    "visit_date": "Besuchsdatum",
    "visit_reason": "Ziel/Thema",
    "visit_type": "Besuchsart",
    "weaknesses": "Schw\u00e4che",
}


@sales_blueprint.get("")
@sales_required
def dashboard():
    """Render the sales dashboard."""
    open_report_count = _own_open_chats_query().count()
    completed_report_count = _own_completed_reports_query().count()

    return render_template(
        "sales/dashboard.html",
        open_report_count=open_report_count,
        completed_report_count=completed_report_count,
    )


@sales_blueprint.get("/reports/open")
@sales_required
def open_reports():
    """Render the current user's open report chats."""
    chats = _own_open_chats_query().order_by(Chat.updated_at.desc()).all()

    return render_template(
        "sales/open_reports.html",
        report_rows=_build_open_report_rows(chats),
    )


@sales_blueprint.get("/reports/completed")
@sales_required
def completed_reports():
    """Render the current user's completed reports."""
    reports = (
        _own_completed_reports_query().order_by(FinalReport.created_at.desc()).all()
    )

    return render_template(
        "sales/completed_reports.html",
        report_rows=_build_completed_report_rows(reports),
    )


@sales_blueprint.get("/reports/new")
@sales_required
def new_report():
    """Start a new deterministic report chat."""
    chat = start_report_chat(current_user)

    return redirect(url_for("sales.report_chat", chat_id=chat.id))


@sales_blueprint.get("/reports/<int:chat_id>")
@sales_required
def report_chat(chat_id: int):
    """Render one report chat for the current sales user."""
    chat = _get_own_chat_or_404(chat_id)

    return render_template(
        "sales/report_chat.html",
        chat=chat,
        draft=chat.report_draft,
        ready_for_review=is_ready_for_review(chat),
        ai_status=get_ai_status(),
        section_labels=REPORT_SECTION_LABELS_DE,
        status_labels=REPORT_STATUS_LABELS_DE,
    )


@sales_blueprint.post("/reports/<int:chat_id>/messages")
@sales_required
def report_message(chat_id: int):
    """Store a user message and advance the report chat."""
    chat = _get_own_chat_or_404(chat_id)
    message_text = request.form.get("message", "")
    if not message_text.strip():
        flash("Bitte gib vor dem Senden eine Nachricht ein.", "warning")
        return redirect(url_for("sales.report_chat", chat_id=chat.id))

    try:
        process_report_message(chat, message_text)
    except ValueError as error:
        flash(str(error), "warning")

    return redirect(url_for("sales.report_chat", chat_id=chat.id))


@sales_blueprint.get("/reports/<int:chat_id>/review")
@sales_required
def report_review(chat_id: int):
    """Render the block-based final review for a completed draft."""
    chat = _get_own_chat_or_404(chat_id)
    if not is_ready_for_review(chat):
        flash(
            "Bitte vervollstaendige zuerst die fehlenden Berichtsbereiche.", "warning"
        )
        return redirect(url_for("sales.report_chat", chat_id=chat.id))

    return render_template(
        "sales/report_review.html",
        chat=chat,
        review=build_report_review(chat.report_draft, get_ai_service()),
    )


@sales_blueprint.post("/reports/<int:chat_id>/corrections")
@sales_required
def report_correction(chat_id: int):
    """Apply a targeted correction to a report draft under review."""
    chat = _get_own_chat_or_404(chat_id)
    field_key = request.form.get("field_key", "").strip()
    correction_text = request.form.get("correction_text", "").strip()
    try:
        apply_report_correction(chat, field_key, correction_text)
    except ValueError as error:
        flash(str(error), "warning")

    return redirect(url_for("sales.report_review", chat_id=chat.id))


@sales_blueprint.post("/reports/<int:chat_id>/confirm")
@sales_required
def confirm_report_route(chat_id: int):
    """Confirm and save a report draft."""
    chat = _get_own_chat_or_404(chat_id)
    try:
        final_report = confirm_report(chat, get_ai_service())
    except ValueError as error:
        flash(str(error), "warning")
        return redirect(url_for("sales.report_chat", chat_id=chat.id))

    return redirect(url_for("sales.final_report_detail", report_id=final_report.id))


@sales_blueprint.post("/reports/<int:chat_id>/cancel")
@sales_required
def cancel_report_route(chat_id: int):
    """Cancel an unfinished report chat."""
    chat = _get_own_chat_or_404(chat_id)
    try:
        cancel_report(chat)
    except ValueError as error:
        flash(str(error), "warning")
        return redirect(url_for("sales.report_chat", chat_id=chat.id))

    return redirect(url_for("sales.open_reports"))


@sales_blueprint.get("/reports/final/<int:report_id>")
@sales_required
def final_report_detail(report_id: int):
    """Render a saved final report for the current sales user."""
    final_report = _get_own_final_report_or_404(report_id)

    return render_template(
        "sales/final_report.html",
        report=final_report,
        report_sections=_build_final_report_sections(final_report),
    )


@sales_blueprint.get("/options")
@sales_required
def options():
    """Render basic sales user options."""
    return render_template("sales/options.html")


def _own_open_chats_query():
    return Chat.query.filter(
        Chat.sales_user_id == current_user.id,
        Chat.status.in_(OPEN_REPORT_STATUSES),
    )


def _own_completed_reports_query():
    return FinalReport.query.filter_by(sales_user_id=current_user.id)


def _get_own_chat_or_404(chat_id: int) -> Chat:
    chat = Chat.query.filter_by(
        id=chat_id,
        sales_user_id=current_user.id,
    ).one_or_none()
    if chat is None:
        abort(404)

    return chat


def _get_own_final_report_or_404(report_id: int) -> FinalReport:
    final_report = FinalReport.query.filter_by(
        id=report_id,
        sales_user_id=current_user.id,
    ).one_or_none()
    if final_report is None:
        abort(404)

    return final_report


def _build_open_report_rows(chats: list[Chat]) -> list[dict[str, object]]:
    return [_build_open_report_row(chat) for chat in chats]


def _build_completed_report_rows(
    reports: list[FinalReport],
) -> list[dict[str, object]]:
    return [_build_completed_report_row(report) for report in reports]


def _build_open_report_row(chat: Chat) -> dict[str, object]:
    draft = chat.report_draft
    answers = dict(draft.draft_data_json.get("answers", {})) if draft else {}
    return {
        "chat": chat,
        "customer_label": _first_present_text(
            answers.get("visit_context"),
            getattr(getattr(draft, "account", None), "display_name", None),
            getattr(getattr(draft, "account", None), "search_name", None),
            fallback="Noch kein Kunde erkannt",
        ),
        "topic_label": _first_present_text(
            answers.get("target_topic"),
            getattr(draft, "summary", None),
            fallback="Noch kein Thema erkannt",
        ),
        "progress_label": _open_report_progress_label(draft),
        "status_label": REPORT_STATUS_LABELS_DE.get(chat.status, chat.status),
        "last_question": getattr(draft, "last_question", None),
    }


def _build_completed_report_row(report: FinalReport) -> dict[str, object]:
    mock_visit_report = report.mock_visit_report
    report_number = _completed_report_number(report)
    return {
        "report": report,
        "report_number": report_number,
        "customer_label": _first_present_text(
            getattr(mock_visit_report, "account_search_name", None),
            getattr(getattr(report, "account", None), "display_name", None),
            getattr(getattr(report, "account", None), "search_name", None),
            fallback="Nicht erkannt",
        ),
        "topic_label": _first_present_text(
            getattr(mock_visit_report, "target_topic", None),
            report.summary,
            fallback="Kein Thema gespeichert",
        ),
        "status_label": REPORT_STATUS_LABELS_DE.get(report.status, report.status),
        "visit_date_label": report.visit_date or "Nicht gesetzt",
    }


def _completed_report_number(report: FinalReport) -> str:
    if report.mock_visit_report is None:
        return f"#{report.id}"

    return report.mock_visit_report.visit_report_number


def _build_final_report_sections(report: FinalReport) -> list[tuple[str, str]]:
    mock_visit_report = report.mock_visit_report
    if mock_visit_report is None:
        return _fallback_final_report_sections(report)

    return [
        ("Kunde/Lead", display_value(mock_visit_report.account_search_name)),
        ("Besuchsart", display_value(mock_visit_report.visit_type)),
        ("Teilnehmer", display_value(mock_visit_report.contact_name)),
        ("Besuchsdatum", display_value(mock_visit_report.visit_date)),
        ("Ziel/Thema", display_value(mock_visit_report.target_topic)),
        ("Info", display_value(mock_visit_report.info_text)),
        ("Vereinbarung", display_value(mock_visit_report.agreement_text)),
        ("Nächster Schritt", display_value(report.next_action)),
        (
            "Termin ab",
            _display_optional_reference(mock_visit_report.next_appointment_date),
        ),
        (
            "Angebotsbezug",
            _display_optional_reference(mock_visit_report.offer_reference),
        ),
        (
            "Auftragsbezug",
            _display_optional_reference(mock_visit_report.order_reference),
        ),
        (
            "Stärke",
            display_value(mock_visit_report.strength_text, empty="Nicht angegeben"),
        ),
        (
            "Schwäche",
            display_value(mock_visit_report.weakness_text, empty="Nicht angegeben"),
        ),
        ("Bewertungen", _format_mock_visit_report_ratings(mock_visit_report)),
        ("Status", REPORT_STATUS_LABELS_DE.get(report.status, report.status)),
        ("Wiedervorlagen", str(len(mock_visit_report.reminders))),
    ]


def _fallback_final_report_sections(report: FinalReport) -> list[tuple[str, str]]:
    return [
        ("Kunde/Lead", display_value(getattr(report.account, "search_name", None))),
        ("Besuchsart", display_value(report.visit_type)),
        ("Besuchsdatum", display_value(report.visit_date)),
        ("Info", display_value(report.summary)),
        ("Vereinbarung", display_value(report.outcome, empty="Nicht angegeben")),
        (
            "Nächster Schritt",
            display_value(report.next_action, empty="Nicht angegeben"),
        ),
        ("Bewertungen", _format_final_report_ratings(report)),
        ("Status", REPORT_STATUS_LABELS_DE.get(report.status, report.status)),
        ("Wiedervorlagen", "0"),
    ]


def _display_optional_reference(value: Any) -> str:
    if value is None:
        return "Nicht relevant"

    text = str(value).strip()
    if not text or text.lower() in {"keine", "keiner", "kein", "none"}:
        return "Nicht relevant"

    return display_value(text)


def _format_mock_visit_report_ratings(mock_visit_report: Any) -> str:
    ratings = [
        ("Zufriedenheit", mock_visit_report.customer_satisfaction_rating),
        ("Technische Attraktivität", mock_visit_report.technical_attractiveness_rating),
        (
            "Kaufmännische Attraktivität",
            mock_visit_report.commercial_attractiveness_rating,
        ),
        ("Priorität", mock_visit_report.priority_rating),
    ]
    formatted_ratings = [
        f"{label}: {value}/10" for label, value in ratings if value is not None
    ]
    return "; ".join(formatted_ratings) if formatted_ratings else "Nicht angegeben"


def _format_final_report_ratings(report: FinalReport) -> str:
    labels = {
        "customer_satisfaction_rating": "Zufriedenheit",
        "technical_attractiveness_rating": "Technische Attraktivität",
        "commercial_attractiveness_rating": "Kaufmännische Attraktivität",
        "priority_rating": "Priorität",
    }
    formatted_ratings = []
    for rating_key, label in labels.items():
        rating = dict(report.ratings_json or {}).get(rating_key)
        if not isinstance(rating, dict):
            continue

        value = rating.get("value")
        if value is not None:
            formatted_ratings.append(f"{label}: {value}/10")

    return "; ".join(formatted_ratings) if formatted_ratings else "Nicht angegeben"


def _open_report_progress_label(draft) -> str:
    if draft is None:
        return "Noch kein Fortschritt"

    section_statuses = dict(draft.section_statuses_json or {})
    total_sections = len(
        [
            section
            for section in section_statuses
            if section not in {"final_report", "user_confirmation"}
        ]
    )
    missing_sections = len(draft.missing_sections_json or [])
    completed_sections = max(total_sections - missing_sections, 0)
    if total_sections == 0:
        return "Noch kein Fortschritt"

    return f"{completed_sections}/{total_sections} Bereiche"


def _first_present_text(*values, fallback: str) -> str:
    for value in values:
        if value is None:
            continue

        text = str(value).strip()
        if text:
            return text

    return fallback
