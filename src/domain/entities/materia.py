"""
Entidade de domínio: Materia.

Representa uma disciplina criada pelo usuário para organizar seus estudos.
"""
from dataclasses import dataclass, field


@dataclass
class Materia:
    """
    Agrupa estudos sob uma disciplina (ex.: 'Cálculo', 'Arquitetura de Software').

    Clean Code: classe pequena e focada — só carrega dados e uma regra
    de validação simples, sem lógica de persistência embutida.
    """
    id: str
    nome: str
    cor: str = "c-blue"
    total_estudos: int = 0

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("O nome da matéria não pode ser vazio.")
