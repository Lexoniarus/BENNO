"""Authentication routes and role guards for BENNO."""

from collections.abc import Callable
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from benno.enums import UserRole
from benno.models import User

auth_blueprint = Blueprint("auth", __name__)


def authenticate_user(email: str, password: str) -> User | None:
    """Return an active user when email and password are valid."""
    normalized_email = email.strip().lower()
    user = User.query.filter_by(email=normalized_email).one_or_none()

    if user is None or not user.is_active:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user


def role_required(role: UserRole) -> Callable:
    """Require a specific role for a route."""

    def decorator(view_function: Callable) -> Callable:
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role != role.value:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


def admin_required(view_function: Callable) -> Callable:
    """Require the admin role for a route."""
    return role_required(UserRole.ADMIN)(view_function)


def sales_required(view_function: Callable) -> Callable:
    """Require the sales representative role for a route."""
    return role_required(UserRole.SALES_REP)(view_function)


def redirect_for_user(user: User):
    """Redirect the user to the dashboard for their role."""
    if user.role == UserRole.ADMIN.value:
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("sales.dashboard"))


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Log a user into BENNO."""
    if current_user.is_authenticated:
        return redirect_for_user(current_user)

    error_message = None
    if request.method == "POST":
        user = authenticate_user(
            email=request.form.get("email", ""),
            password=request.form.get("password", ""),
        )
        if user is None:
            error_message = "Invalid email or password."
        else:
            login_user(user)
            return redirect_for_user(user)

    return render_template("auth/login.html", error_message=error_message)


@auth_blueprint.get("/logout")
@login_required
def logout():
    """Log the current user out of BENNO."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
