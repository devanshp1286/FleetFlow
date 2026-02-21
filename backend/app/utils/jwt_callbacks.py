from flask import jsonify


def register_jwt_callbacks(jwt):

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"status": "error", "code": "TOKEN_EXPIRED", "message": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token(error):
        return jsonify({"status": "error", "code": "TOKEN_INVALID", "message": "Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token(error):
        return jsonify({"status": "error", "code": "TOKEN_MISSING", "message": "Authorization token required."}), 401
