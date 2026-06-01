"""
Padrão GoF — Factory Method (Criação).

PROBLEMA RESOLVIDO: sem a factory, o GerarConteudoUseCase precisaria
conhecer todas as classes concretas de Strategy e instanciá-las
diretamente — acoplamento alto e violação de OCP.

SOLUÇÃO: A ConteudoFactory centraliza a criação de Strategies. Adicionar
um novo tipo de conteúdo exige apenas registrar a nova classe aqui,
sem tocar nos casos de uso.

SOLID — OCP: novos tipos de conteúdo = novo registro no dicionário,
             zero modificação em GerarConteudoUseCase.
SOLID — DIP: o caso de uso recebe a factory, não instancia diretamente.
"""
from src.application.strategies.conteudo_strategy import ConteudoStrategy
from src.application.strategies.resumo_strategy import ResumoStrategy, ResumoMenorStrategy
from src.application.strategies.topicos_strategy import TopicosStrategy, ChecklistTopicosStrategy
from src.application.strategies.flashcard_strategy import FlashcardStrategy
from src.application.strategies.quiz_strategy import QuizStrategy
from src.application.strategies.mapa_strategy import MapaMentalStrategy
from src.domain.ports.gerador_ia import IGeradorIA


class ConteudoFactory:
    """
    Factory que mapeia tipos de conteúdo às suas Strategies concretas.

    Uso:
        factory = ConteudoFactory(gerador_ia)
        strategy = factory.criar("resumo")
        resultado = strategy.gerar(texto)
    """

    # Registro central: tipo → classe concreta da Strategy
    # Para adicionar um novo tipo: basta incluir uma linha aqui.
    _REGISTRO: dict[str, type[ConteudoStrategy]] = {
        "resumo":             ResumoStrategy,
        "resumo_menor":       ResumoMenorStrategy,
        "topicos":            TopicosStrategy,
        "checklist_topicos":  ChecklistTopicosStrategy,
        "flashcard":          FlashcardStrategy,
        "flashcards":         FlashcardStrategy,   # alias aceito
        "questoes":           QuizStrategy,
        "mapa":               MapaMentalStrategy,
    }

    def __init__(self, gerador: IGeradorIA) -> None:
        # DIP: recebe a abstração do gerador, não o Gemini diretamente
        self._gerador = gerador

    def criar(self, tipo: str) -> ConteudoStrategy:
        """
        Instancia e retorna a Strategy adequada para o tipo solicitado.

        Args:
            tipo: Identificador do tipo de conteúdo (ex.: 'resumo', 'questoes').

        Returns:
            Instância concreta de ConteudoStrategy pronta para uso.

        Raises:
            ValueError: Se o tipo não estiver registrado na factory.
        """
        classe = self._REGISTRO.get(tipo)
        if classe is None:
            tipos_validos = ", ".join(sorted(self._REGISTRO))
            raise ValueError(
                f"Tipo de conteúdo '{tipo}' não reconhecido. "
                f"Tipos válidos: {tipos_validos}."
            )
        return classe(self._gerador)

    def tipos_suportados(self) -> list[str]:
        """Retorna a lista de tipos de conteúdo disponíveis."""
        return sorted(set(self._REGISTRO.keys()))
