"""
Tratamento de erros centralizado da camada HTTP.

Traduz exceções do domínio/aplicação em respostas JSON com o status
adequado — as rotas não repetem try/except (Clean Code: sem duplicação).

Convenção de erro: { "erro": <mensagem>, "codigo": <slug> }.
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from src.domain.exceptions import RecursoNaoEncontradoError


def registrar_tratadores_de_erro(app: Flask) -> None:
    """Registra os handlers globais de erro na aplicação."""

    @app.errorhandler(RecursoNaoEncontradoError)
    def _recurso_nao_encontrado(exc: RecursoNaoEncontradoError):
        # recurso inexistente para este usuário → 404
        return jsonify({"erro": str(exc), "codigo": "NAO_ENCONTRADO"}), 404

    @app.errorhandler(ValueError)
    def _erro_de_validacao(exc: ValueError):
        # regra de negócio violada ou entrada inválida → 400
        return jsonify({"erro": str(exc), "codigo": "REQUISICAO_INVALIDA"}), 400

    @app.errorhandler(RuntimeError)
    def _erro_de_dependencia(exc: RuntimeError):
        # falha em serviço externo (IA, PDF) → 502
        return jsonify({"erro": str(exc), "codigo": "FALHA_DEPENDENCIA"}), 502

    @app.errorhandler(HTTPException)
    def _erro_http(exc: HTTPException):
        return jsonify({"erro": exc.description, "codigo": exc.name}), exc.code

    @app.errorhandler(Exception)
    def _erro_inesperado(exc: Exception):
        return jsonify({"erro": "Erro interno do servidor.", "codigo": "ERRO_INTERNO"}), 500
