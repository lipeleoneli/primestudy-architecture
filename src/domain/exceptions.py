"""
Exceções de domínio.

Pertencem ao núcleo (Python puro) para que qualquer camada possa lançá-las
e a borda HTTP possa traduzi-las em status codes adequados sem que o
domínio conheça HTTP.

Herda de ValueError para manter compatibilidade com chamadores que tratam
erros de negócio de forma genérica — um RecursoNaoEncontradoError *é* um
caso particular de entrada inválida, mas a interface o traduz em 404 em
vez de 400 (ver src/interface/errors.py e docs/openapi.yaml).
"""


class RecursoNaoEncontradoError(ValueError):
    """Recurso (estudo, matéria…) inexistente para o usuário autenticado."""
