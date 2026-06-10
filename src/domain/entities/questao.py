"""
Entidade de domínio: Questao.

Representa uma questão de múltipla escolha gerada pela IA.
"""
from dataclasses import dataclass


@dataclass
class Questao:
    """
    Questão de múltipla escolha com exatamente 4 alternativas.

    Clean Code: validações no __post_init__ evitam estados inválidos —
    um objeto Questao que existe já é garantidamente válido (invariante de domínio).
    """
    pergunta: str
    alternativas: list[str]
    correta: int          # índice 0-3 da alternativa correta
    explicacao: str

    def __post_init__(self) -> None:
        if not self.pergunta or not self.pergunta.strip():
            raise ValueError("A pergunta não pode ser vazia.")
        if len(self.alternativas) != 4:
            raise ValueError("Uma questão deve ter exatamente 4 alternativas.")
        if not (0 <= self.correta <= 3):
            raise ValueError("O índice da alternativa correta deve ser entre 0 e 3.")

    @property
    def alternativa_correta(self) -> str:
        """Retorna o texto da alternativa correta."""
        return self.alternativas[self.correta]
