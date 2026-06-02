"""
Guarda de autenticação para as rotas HTTP.

Em produção exige uid na sessão (criada por /api/sessao após verificar o
idToken do Firebase). No modo DEMO injeta um uid fixo para que a API possa
ser explorada sem login (decisão de design — ver README).
"""
from functools import wraps

from flask import current_app, g, jsonify, session


def requer_login(rota):
    """Decorator: bloqueia a rota se não houver usuário autenticado."""
    @wraps(rota)
    def wrapper(*args, **kwargs):
        deps = current_app.extensions["primestudy"]
        uid = session.get("uid")

        if not uid and deps.config.eh_demo:
            uid = deps.config.demo_uid
            session["uid"] = uid

        if not uid:
            return jsonify({
                "erro": "Autenticação necessária.",
                "codigo": "NAO_AUTENTICADO",
            }), 401

        g.uid = uid
        return rota(*args, **kwargs)

    return wrapper
