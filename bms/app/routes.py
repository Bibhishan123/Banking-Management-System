from flask import Blueprint, request, current_app, jsonify
from . import crud

accounts_bp = Blueprint("accounts", __name__)

def _get_session():
    # session factory placed on app in create_app (scoped_session)
    sf = current_app.session_factory
    return sf()

@accounts_bp.route("/accounts", methods=["POST"])
def create_account_route():
    payload = request.get_json() or {}
    name = payload.get("name")
    number = payload.get("number")
    balance = payload.get("balance", 0)
    sess = _get_session()
    try:
        acct = crud.create_account(sess, name=name, number=number, balance=balance)
        return jsonify(acct.to_dict()), 201
    finally:
        sess.close()


@accounts_bp.route("/accounts/<int:account_id>", methods=["GET"])
def get_account_route(account_id: int):
    sess = _get_session()
    try:
        acct = crud.get_account_by_id(sess, account_id)
        return jsonify(acct.to_dict()), 200
    finally:
        sess.close()


@accounts_bp.route("/accounts", methods=["GET"])
def list_accounts_route():
    limit = request.args.get("limit", 100)
    offset = request.args.get("offset", 0)
    sess = _get_session()
    try:
        accts = crud.list_accounts(sess, limit=limit, offset=offset)
        return jsonify([a.to_dict() for a in accts]), 200
    finally:
        sess.close()


@accounts_bp.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account_route(account_id: int):
    payload = request.get_json() or {}
    sess = _get_session()
    try:
        acct = crud.update_account(sess, account_id, payload)
        return jsonify(acct.to_dict()), 200
    finally:
        sess.close()


@accounts_bp.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account_route(account_id: int):
    sess = _get_session()
    try:
        crud.delete_account(sess, account_id)
        return jsonify({"status": "deleted"}), 200
    finally:
        sess.close()
