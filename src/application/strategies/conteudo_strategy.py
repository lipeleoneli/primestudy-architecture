"""
Padrão GoF — Strategy (Comportamento).

PROBLEMA RESOLVIDO: O gemini_services.py original tinha uma função
gerar_conteudo() com 120+ linhas de if/elif encadeados para cada tipo
de conteúdo (resumo, quiz, flashcard…). Adicionar um novo tipo exigia
editar essa função — violando OCP.

SOLUÇÃO: Cada tipo de conteúdo vira uma classe concreta de Strategy.
Adicionar 'mapas de calor' no futuro = criar MapaCalorStrategy, sem
tocar em nenhuma classe existente.

SOLID — OCP: aberto para extensão, fechado para modificação.
SOLID — SRP: cada Strategy é responsável por um único tipo de geração.
SOLID — LSP: qualquer Strategy pode ser substituída por outra sem
             alterar o comportamento do GerarConteudoUseCase.
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
        # DIP: recebe a abstração, não a implementação concreta (Gemini, mock…)
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
