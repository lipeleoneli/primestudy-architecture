"""
Exceção de domínio: ErroAutenticacao.

Levantada pela infraestrutura de autenticação quando um token é
inválido ou expirado. Tipada de forma diferente de ValueError para
que o handler HTTP possa mapeá-la corretamente para 401 — não 400.

SOLID — ISP: arquivo dedicado evita que quem importa apenas autenticação
             precise carregar os ports de IA ou PDF.
"""


class ErroAutenticacao(Exception):
    """Token de autenticação inválido, expirado ou ausente."""
