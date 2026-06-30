"""Sales user routes for BENNO."""

from flask import Blueprint, render_template
from flask_login import current_user

from benno.auth import sales_required
from benno.enums import ReportStatus
from benno.models import Chat, FinalReport

sales_blueprint = Blueprint("sales", __name__, url_prefix="/sales")

OPEN_REPORT_STATUSES = (
    ReportStatus.IN_PROGRESS.value,
    ReportStatus.READY_FOR_REVIEW.value,
    ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value,
    ReportStatus.BLOCKED.value,
)


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

    return render_template("sales/open_reports.html", chats=chats)


@sales_blueprint.get("/reports/completed")
@sales_required
def completed_reports():
    """Render the current user's completed reports."""
    reports = (
        _own_completed_reports_query().order_by(FinalReport.created_at.desc()).all()
    )

    return render_template("sales/completed_reports.html", reports=reports)


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
