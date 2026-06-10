"""
Interface base para geração de conteúdo via IA.

Cada tipo de conteúdo (resumo, quiz, flashcard…) é uma subclasse que
monta o prompt adequado e delega a chamada ao IGeradorIA injetado.
"""
from abc import ABC, abstractmethod

from src.domain.ports.gerador_ia import IGeradorIA


class ConteudoStrategy(ABC):
    """
    Interface da Strategy de geração de conteúdo.

    Cada subclasse monta o prompt específico do seu tipo e delega
    a chamada de IA ao IGeradorIA injetado.
    """

    def __init__(self, gerador: IGeradorIA) -> None:
        self._gerador = gerador

    @abstractmethod
    def gerar(self, texto: str, historico: str = "") -> str:
        """
        Gera o conteúdo a partir do texto do PDF.

        Args:
            texto:     Texto bruto extraído do PDF.
            historico: Conteúdo já gerado anteriormente (para ação 'mais').

        Returns:
            String com o conteúdo gerado (HTML, JSON ou texto puro).
        """

    # ── helpers compartilhados ───────────────────────────────────────────────

    @staticmethod
    def _regra_html() -> str:
        return (
            "IMPORTANTE: Retorne APENAS o conteúdo usando tags HTML básicas "
            "(<b>, <ul>, <li>, <br>, <p>, <h3>). "
            "NÃO inclua blocos de código markdown, NÃO inclua tags <style>. "
            "Retorne APENAS o HTML puro do conteúdo.\n\n"
        )

    @staticmethod
    def _aviso_historico(historico: str) -> str:
        if not historico:
            return ""
        return (
            "ATENÇÃO: O utilizador solicitou MAIS itens. Você DEVE gerar conteúdo "
            f"INÉDITO, diferente destes que já existem:\n{historico}\n\n"
        )
