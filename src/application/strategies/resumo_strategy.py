"""Strategy concreta: geração de Resumo."""
from src.application.strategies.conteudo_strategy import ConteudoStrategy


class ResumoStrategy(ConteudoStrategy):
    """Gera um resumo detalhado e organizado do material."""

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            self._regra_html()
            + self._aviso_historico(historico)
            + f"Faça um resumo detalhado e organizado do seguinte texto:\n\n{texto}"
        )
        return self._gerador.gerar(prompt)


class ResumoMenorStrategy(ConteudoStrategy):
    """Gera um resumo curto e altamente sintetizado."""

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            self._regra_html()
            + "Faça um resumo MUITO CURTO, direto ao ponto e altamente "
            f"sintetizado do texto abaixo:\n\n{texto}"
        )
        return self._gerador.gerar(prompt)
