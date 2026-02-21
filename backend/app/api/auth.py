from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timezone

from app import db, limiter
from app.models import User

auth_bp = Blueprint("auth", __name__)
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def success(data, code=200):
    return jsonify({"status": "success", "data": data}), code


def error(message, code=400, error_code=None):
    r = {"status": "error", "message": message}
    if error_code:
        r["code"] = error_code
    return jsonify(r), code


# ── POST /auth/login ──────────────────────────────────────────────────────────

@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        return error("Username and password are required.", 422)

    user = User.query.filter_by(username=username, is_active=True).first()
    if not user:
        return error("Invalid credentials.", 401, "INVALID_CREDENTIALS")

    try:
        ph.verify(user.password_hash, password)
    except VerifyMismatchError:
        return error("Invalid credentials.", 401, "INVALID_CREDENTIALS")

    # Rehash if needed
    if ph.check_needs_rehash(user.password_hash):
        user.password_hash = ph.hash(password)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    additional = {"role": user.role, "username": user.username}
    access_token  = create_access_token(identity=user.id, additional_claims=additional)
    refresh_token = create_refresh_token(identity=user.id, additional_claims=additional)

    return success({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    })


# ── POST /auth/register ───────────────────────────────────────────────────────

@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    body = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    email    = body.get("email", "").strip().lower()
    password = body.get("password", "")
    role     = body.get("role", "dispatcher")

    if not username or not email or not password:
        return error("username, email, and password are required.", 422)
    if len(password) < 8:
        return error("Password must be at least 8 characters.", 422)
    if role not in ("admin", "dispatcher", "driver", "viewer"):
        return error("Invalid role.", 422)
    if User.query.filter_by(username=username).first():
        return error("Username already taken.", 409, "USERNAME_TAKEN")
    if User.query.filter_by(email=email).first():
        return error("Email already registered.", 409, "EMAIL_TAKEN")

    user = User(
        username=username, email=email,
        password_hash=ph.hash(password), role=role
    )
    db.session.add(user)
    db.session.commit()

    additional = {"role": user.role, "username": user.username}
    access_token  = create_access_token(identity=user.id, additional_claims=additional)
    refresh_token = create_refresh_token(identity=user.id, additional_claims=additional)

    return success({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }, 201)


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims   = get_jwt()
    additional = {"role": claims.get("role"), "username": claims.get("username")}
    access_token = create_access_token(identity=identity, additional_claims=additional)
    return success({"access_token": access_token})


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return error("User not found.", 404)
    return success(user.to_dict())
