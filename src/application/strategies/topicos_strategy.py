"""Strategy concreta: geração de Tópicos principais."""
from src.application.strategies.conteudo_strategy import ConteudoStrategy


class TopicosStrategy(ConteudoStrategy):
    """Extrai os tópicos principais do material como lista HTML."""

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            self._aviso_historico(historico)
            + "Liste os TÓPICOS PRINCIPAIS do texto abaixo.\n"
            "Regras OBRIGATÓRIAS:\n"
            "- Retorne APENAS uma lista HTML usando <ul> e <li>.\n"
            "- Cada <li> deve ser curto: máximo 10 palavras.\n"
            "- NÃO use <p>, <h3>, <b>, <br> nem nenhuma outra tag HTML.\n"
            "- NÃO adicione introdução, conclusão ou texto fora da lista.\n"
            "- Entre 5 e 15 tópicos.\n\n"
            f"Texto:\n{texto}"
        )
        return self._gerador.gerar(prompt)


class ChecklistTopicosStrategy(ConteudoStrategy):
    """Extrai tópicos no formato checklist (texto puro, um por linha)."""

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            "Extraia os principais tópicos de estudo do texto abaixo.\n"
            "Regras OBRIGATÓRIAS:\n"
            "- Um tópico por linha.\n"
            "- Tópicos curtos e diretos (máximo ~8 palavras).\n"
            "- SEM numeração, SEM marcadores, SEM hífens, SEM HTML, SEM markdown.\n"
            "- Entre 5 e 15 tópicos.\n"
            "- NÃO adicione nenhum texto fora da lista.\n\n"
            f"Texto:\n{texto}"
        )
        return self._gerador.gerar(prompt)
