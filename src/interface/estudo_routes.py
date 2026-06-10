"""
Rotas de estudos.

POST   /api/estudos                  — cria estudo a partir de upload de PDF.
GET    /api/estudos                  — lista estudos recentes (paginado).
GET    /api/estudos/<id>             — detalha um estudo (com conteúdo).
PATCH  /api/estudos/<id>             — renomeia um estudo.
DELETE /api/estudos/<id>             — remove um estudo.
POST   /api/estudos/<id>/conteudo    — gera/amplia um tipo de conteúdo (IA).
GET    /api/estudos/<id>/checklist   — obtém (ou gera) a checklist de tópicos.
PUT    /api/estudos/<id>/checklist   — salva o estado da checklist.
PUT    /api/estudos/<id>/materia     — vincula/desvincula de uma matéria.

Leituras/edições triviais usam o port IEstudoRepository direto (dependência
para dentro, permitida). Operações com regra passam pelos use cases.
"""
from flask import Blueprint, current_app, g, jsonify, request

from src.application.use_cases.gerar_conteudo import GerarConteudoInput
from src.application.use_cases.gerenciar_checklist import SalvarChecklistInput
from src.application.use_cases.gerenciar_materias import VincularEstudoInput
from src.domain.exceptions import RecursoNaoEncontradoError
from src.interface.auth_guard import requer_login
from src.interface.serializers import (
    estudo_para_json,
    item_checklist_para_json,
)

bp = Blueprint("estudo", __name__, url_prefix="/api/estudos")


def _deps():
    return current_app.extensions["primestudy"]


# ── CRUD de estudos ──────────────────────────────────────────────────────────

@bp.post("")
@requer_login
def criar_estudo():
    from src.application.use_cases.processar_pdf import ProcessarPDFInput

    arquivo = request.files.get("arquivo")
    if arquivo is None or not arquivo.filename:
        raise ValueError("Envie um arquivo PDF no campo 'arquivo'.")

    dados = ProcessarPDFInput(
        uid=g.uid,
        conteudo_bytes=arquivo.read(),
        nome_arquivo=arquivo.filename,
        materia_id=request.form.get("materia_id") or None,
    )
    saida = _deps().processar_pdf.executar(dados)   # ValueError/RuntimeError → handlers
    return jsonify({"estudo_id": saida.estudo_id, "redirect_url": saida.redirect_url}), 201


@bp.get("")
@requer_login
def listar_estudos():
    limite, offset = _ler_paginacao()
    todos = _deps().repositorio.listar_estudos_recentes(g.uid, limite=offset + limite)
    pagina = todos[offset:offset + limite]
    return jsonify({
        "estudos": [estudo_para_json(e) for e in pagina],
        "limite": limite,
        "offset": offset,
        "total_retornado": len(pagina),
    })


@bp.get("/<estudo_id>")
@requer_login
def obter_estudo(estudo_id: str):
    estudo = _deps().repositorio.buscar_estudo(g.uid, estudo_id)
    if estudo is None:
        raise RecursoNaoEncontradoError(f"Estudo '{estudo_id}' não encontrado.")
    return jsonify(estudo_para_json(estudo, incluir_texto=True))


@bp.patch("/<estudo_id>")
@requer_login
def renomear_estudo(estudo_id: str):
    corpo = request.get_json(silent=True) or {}
    novo_nome = (corpo.get("nome") or "").strip()
    if not novo_nome:
        raise ValueError("O campo 'nome' não pode ser vazio.")
    _deps().repositorio.renomear_estudo(g.uid, estudo_id, novo_nome)
    return jsonify({"id": estudo_id, "nome": novo_nome})


@bp.delete("/<estudo_id>")
@requer_login
def deletar_estudo(estudo_id: str):
    _deps().repositorio.deletar_estudo(g.uid, estudo_id)
    return "", 204


# ── Geração de conteúdo (IA) ─────────────────────────────────────────────────

@bp.post("/<estudo_id>/conteudo")
@requer_login
def gerar_conteudo(estudo_id: str):
    corpo = request.get_json(silent=True) or {}
    tipo = corpo.get("tipo")
    if not tipo:
        raise ValueError("O campo 'tipo' é obrigatório.")

    dados = GerarConteudoInput(
        uid=g.uid,
        estudo_id=estudo_id,
        tipo=tipo,
        acao=corpo.get("acao", "novo"),
    )
    saida = _deps().gerar_conteudo.executar(dados)
    return jsonify({"conteudo": saida.conteudo, "tipo_render": saida.tipo_render})


# ── Checklist ────────────────────────────────────────────────────────────────

@bp.get("/<estudo_id>/checklist")
@requer_login
def obter_checklist(estudo_id: str):
    itens = _deps().gerenciar_checklist.obter_ou_gerar(g.uid, estudo_id)
    return jsonify({"itens": [item_checklist_para_json(i) for i in itens]})


@bp.put("/<estudo_id>/checklist")
@requer_login
def salvar_checklist(estudo_id: str):
    corpo = request.get_json(silent=True) or {}
    dados = SalvarChecklistInput(uid=g.uid, estudo_id=estudo_id, itens=corpo.get("itens", []))
    _deps().gerenciar_checklist.salvar(dados)
    return "", 204


# ── Vínculo com matéria ──────────────────────────────────────────────────────

@bp.put("/<estudo_id>/materia")
@requer_login
def vincular_materia(estudo_id: str):
    corpo = request.get_json(silent=True) or {}
    dados = VincularEstudoInput(
        uid=g.uid,
        estudo_id=estudo_id,
        materia_id=corpo.get("materia_id"),   # None desvincula
    )
    _deps().gerenciar_materias.vincular_estudo(dados)
    return jsonify({"estudo_id": estudo_id, "materia_id": dados.materia_id})


# ── helpers ──────────────────────────────────────────────────────────────────

def _ler_paginacao() -> tuple[int, int]:
    try:
        limite = min(max(int(request.args.get("limite", 50)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        raise ValueError("Parâmetros 'limite' e 'offset' devem ser inteiros.")
    return limite, offset
