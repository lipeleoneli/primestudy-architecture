"""Strategy concreta: geração de Flashcards."""
from src.application.strategies.conteudo_strategy import ConteudoStrategy


class FlashcardStrategy(ConteudoStrategy):
    """
    Gera flashcards no formato P: / R: para revisão ativa.

    Retorna texto puro (sem HTML) porque o frontend renderiza
    os cards em formato próprio via JavaScript.
    """

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            self._aviso_historico(historico)
            + "Crie entre 5 e 10 flashcards de estudo com os conceitos "
            "mais importantes do texto.\n"
            "Use EXATAMENTE este formato (sem HTML, sem markdown):\n"
            "P: pergunta\n"
            "R: resposta\n\n"
            f"Texto:\n{texto}"
        )
        return self._gerador.gerar(prompt)
