from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def success(data, code=200, meta=None):
    r = {"status": "success", "data": data}
    if meta:
        r["meta"] = meta
    return jsonify(r), code


def error(message, code=400, error_code=None):
    r = {"status": "error", "message": message}
    if error_code:
        r["code"] = error_code
    return jsonify(r), code


def require_role(*roles):
    """Decorator: JWT required + role check."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return error("Insufficient permissions.", 403, "FORBIDDEN")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def paginate(query, page, per_page=20):
    """Paginate a SQLAlchemy query and return items + meta."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated.items, {
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total": paginated.total,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
    }
