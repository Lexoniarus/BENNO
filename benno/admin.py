"""Admin routes for BENNO."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from benno.auth import admin_required
from benno.enums import ReminderStatus, ReportStatus, UserSetupTokenPurpose
from benno.extensions import db
from benno.models import Chat, FinalReport, GlobalSetting, MockReminder, User
from benno.services.admin_users import (
    choices_for_admin_forms,
    create_user_from_form,
    create_user_setup_token,
    update_global_settings_from_form,
    update_user_from_form,
)

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")


@admin_blueprint.get("")
@admin_required
def dashboard():
    """Render the admin dashboard."""
    return render_template(
        "admin/dashboard.html",
        status_cards=_build_status_cards(),
        user_rows=_build_user_status_rows(),
    )


@admin_blueprint.get("/users")
@admin_required
def users():
    """Render the admin user list."""
    user_list = User.query.order_by(User.email).all()

    return render_template(
        "admin/users.html",
        choices=choices_for_admin_forms(),
        user_rows=[_build_user_row(user) for user in user_list],
    )


@admin_blueprint.route("/users/new", methods=["GET", "POST"])
@admin_required
def new_user():
    """Create a local BENNO user and show a setup link."""
    if request.method == "POST":
        try:
            user = create_user_from_form(request.form)
            _, raw_token = create_user_setup_token(
                user,
                UserSetupTokenPurpose.SETUP,
            )
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "warning")
        else:
            return _render_setup_link(user, raw_token, "Setup-Link")

    return render_template(
        "admin/user_form.html",
        choices=choices_for_admin_forms(),
        form_action=url_for("admin.new_user"),
        form_title="Benutzer hinzufügen",
        submit_label="Benutzer anlegen",
        user=None,
    )


@admin_blueprint.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id: int):
    """Edit a local BENNO user."""
    user = db.get_or_404(User, user_id)
    if request.method == "POST":
        try:
            update_user_from_form(user, request.form)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "warning")
        else:
            flash("Benutzer wurde gespeichert.", "success")
            return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html",
        choices=choices_for_admin_forms(),
        form_action=url_for("admin.edit_user", user_id=user.id),
        form_title="Benutzer bearbeiten",
        submit_label="Änderungen speichern",
        user=user,
    )


@admin_blueprint.post("/users/<int:user_id>/setup-link")
@admin_required
def setup_link(user_id: int):
    """Create a local setup link for a user."""
    user = db.get_or_404(User, user_id)
    _, raw_token = create_user_setup_token(user, UserSetupTokenPurpose.SETUP)
    db.session.commit()
    return _render_setup_link(user, raw_token, "Setup-Link")


@admin_blueprint.post("/users/<int:user_id>/reset-link")
@admin_required
def reset_link(user_id: int):
    """Create a local password reset link for a user."""
    user = db.get_or_404(User, user_id)
    _, raw_token = create_user_setup_token(user, UserSetupTokenPurpose.RESET)
    db.session.commit()
    return _render_setup_link(user, raw_token, "Reset-Link")


@admin_blueprint.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    """Render and update simple global provider and language settings."""
    global_setting = GlobalSetting.query.order_by(GlobalSetting.id).first()
    if request.method == "POST":
        try:
            global_setting = update_global_settings_from_form(request.form)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "warning")
        else:
            flash("Globale Einstellungen wurden gespeichert.", "success")
            return redirect(url_for("admin.settings"))

    return render_template(
        "admin/settings.html",
        choices=choices_for_admin_forms(),
        global_setting=global_setting,
    )


def _render_setup_link(user: User, raw_token: str, link_label: str):
    setup_url = url_for("auth.setup_password", token=raw_token, _external=True)
    return render_template(
        "admin/setup_link.html",
        link_label=link_label,
        setup_url=setup_url,
        user=user,
    )


def _build_status_cards() -> list[dict[str, int | str]]:
    return [
        {
            "label": "Aktive Benutzer",
            "value": User.query.filter_by(is_active=True).count(),
        },
        {
            "label": "Offene Berichte",
            "value": Chat.query.filter_by(
                status=ReportStatus.IN_PROGRESS.value
            ).count(),
        },
        {
            "label": "Fertige Berichte",
            "value": FinalReport.query.count(),
        },
        {
            "label": "Problemfälle",
            "value": Chat.query.filter(
                Chat.status.in_(
                    [
                        ReportStatus.BLOCKED.value,
                        ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value,
                    ]
                )
            ).count(),
        },
        {
            "label": "Offene Wiedervorlagen",
            "value": MockReminder.query.filter_by(
                status=ReminderStatus.OPEN.value
            ).count(),
        },
    ]


def _build_user_status_rows() -> list[dict[str, int | str | bool]]:
    users = User.query.order_by(User.email).all()
    return [_build_user_row(user) for user in users]


def _build_user_row(user: User) -> dict[str, int | str | bool | User]:
    return {
        "user": user,
        "open_chats": Chat.query.filter_by(
            sales_user_id=user.id,
            status=ReportStatus.IN_PROGRESS.value,
        ).count(),
        "completed_reports": FinalReport.query.filter_by(
            sales_user_id=user.id,
        ).count(),
        "problem_chats": Chat.query.filter(
            Chat.sales_user_id == user.id,
            Chat.status.in_(
                [
                    ReportStatus.BLOCKED.value,
                    ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value,
                ]
            ),
        ).count(),
    }
