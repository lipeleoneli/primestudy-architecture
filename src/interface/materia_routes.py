"""
Rotas de matérias (disciplinas).

GET    /api/materias            — lista as matérias do usuário.
POST   /api/materias            — cria uma matéria.
DELETE /api/materias/<id>       — remove uma matéria (estudos só desvinculados).
GET    /api/materias/<id>/estudos — lista os estudos de uma matéria.

As rotas só orquestram HTTP; toda regra está nos use cases.
"""
from flask import Blueprint, current_app, g, jsonify, request

from src.application.use_cases.gerenciar_materias import CriarMateriaInput
from src.interface.auth_guard import requer_login
from src.interface.serializers import estudo_para_json, materia_para_json

bp = Blueprint("materia", __name__, url_prefix="/api/materias")


def _uc():
    return current_app.extensions["primestudy"].gerenciar_materias


@bp.get("")
@requer_login
def listar_materias():
    materias = _uc().listar_materias(g.uid)
    return jsonify({"materias": [materia_para_json(m) for m in materias]})


@bp.post("")
@requer_login
def criar_materia():
    corpo = request.get_json(silent=True) or {}
    dados = CriarMateriaInput(uid=g.uid, nome=corpo.get("nome", ""), cor=corpo.get("cor", "c-blue"))
    materia_id = _uc().criar_materia(dados)   # ValueError (nome vazio) → 400
    return jsonify({"materia_id": materia_id}), 201


@bp.delete("/<materia_id>")
@requer_login
def deletar_materia(materia_id: str):
    _uc().deletar_materia(g.uid, materia_id)
    return "", 204


@bp.get("/<materia_id>/estudos")
@requer_login
def listar_estudos_da_materia(materia_id: str):
    estudos = _uc().listar_estudos_da_materia(g.uid, materia_id)  # ValueError → 400
    return jsonify({"estudos": [estudo_para_json(e) for e in estudos]})
