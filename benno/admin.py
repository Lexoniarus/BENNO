"""Admin routes for BENNO."""

from flask import Blueprint, render_template

from benno.auth import admin_required
from benno.enums import ReminderStatus, ReportStatus
from benno.models import Chat, FinalReport, GlobalSetting, MockReminder, User

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@admin_blueprint.get("")
@admin_required
def dashboard():
    """Render the admin dashboard."""
    return render_template("admin/dashboard.html", status=_build_status_overview())


@admin_blueprint.get("/users")
@admin_required
def users():
    """Render the admin user list."""
    user_list = User.query.order_by(User.email).all()

    return render_template("admin/users.html", users=user_list)


@admin_blueprint.get("/settings")
@admin_required
def settings():
    """Render simple global provider and language settings."""
    global_setting = GlobalSetting.query.order_by(GlobalSetting.id).first()

    return render_template("admin/settings.html", global_setting=global_setting)


def _build_status_overview() -> dict[str, int]:
    return {
        "active_users": User.query.filter_by(is_active=True).count(),
        "blocked_chats": Chat.query.filter_by(
            status=ReportStatus.BLOCKED.value
        ).count(),
        "completed_reports": FinalReport.query.count(),
        "inside_sales_input_required": FinalReport.query.filter_by(
            status=ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value
        ).count(),
        "open_chats": Chat.query.filter_by(
            status=ReportStatus.IN_PROGRESS.value
        ).count(),
        "open_reminders": MockReminder.query.filter_by(
            status=ReminderStatus.OPEN.value
        ).count(),
        "total_users": User.query.count(),
    }
