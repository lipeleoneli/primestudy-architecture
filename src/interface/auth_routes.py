"""
Rotas de autenticação.

POST /api/sessao   — troca um idToken do Firebase por uma sessão server-side.
DELETE /api/sessao — encerra a sessão (logout).

Segurança (ADR-003 / quality.md): o uid vem SEMPRE de um token verificado,
nunca do corpo da requisição. No modo demo a verificação é dispensada.
"""
from flask import Blueprint, current_app, jsonify, request, session

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.post("/sessao")
def criar_sessao():
    deps = current_app.extensions["primestudy"]

    if deps.config.eh_demo:
        session["uid"] = deps.config.demo_uid
        return jsonify({"uid": deps.config.demo_uid, "modo": "demo"}), 200

    corpo = request.get_json(silent=True) or {}
    id_token = corpo.get("idToken")
    if not id_token:
        raise ValueError("Campo 'idToken' é obrigatório.")

    uid = deps.firebase_auth.verificar_id_token(id_token)
    session["uid"] = uid
    return jsonify({"uid": uid, "modo": "real"}), 200


@bp.delete("/sessao")
def encerrar_sessao():
    session.clear()
    return "", 204
