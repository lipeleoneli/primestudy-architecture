"""Strategy concreta: geração de Mapa Mental."""
from src.application.strategies.conteudo_strategy import ConteudoStrategy


class MapaMentalStrategy(ConteudoStrategy):
    """Gera um mapa mental em texto indentado para renderização no frontend."""

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            self._aviso_historico(historico)
            + "Gere um mapa mental do texto abaixo em formato de TEXTO INDENTADO "
            "com 2 espaços por nível.\n\n"
            "Regras OBRIGATÓRIAS:\n"
            "- Primeira linha: o tema principal (sem indentação).\n"
            "- Subtemas: indentados com 2 espaços.\n"
            "- Detalhes: indentados com 4 espaços.\n"
            "- Mantenha acentos e português correto.\n"
            "- NÃO use marcadores, hífens, asteriscos, numeração ou HTML.\n"
            "- NÃO adicione nenhum texto fora da estrutura.\n"
            "- Máximo de 6 subtemas e 3 detalhes por subtema.\n\n"
            f"Texto:\n{texto}"
        )
        return self._gerador.gerar(prompt)
