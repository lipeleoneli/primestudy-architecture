"""
Entidade de domínio: Estudo.

Representa um material de estudo criado a partir de um PDF.
Não depende de nenhuma biblioteca externa — é Python puro.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ItemChecklist:
    """Representa um tópico de estudo na checklist."""
    texto: str
    feito: bool = False


@dataclass
class Estudo:
    """
    Entidade central do domínio PrimeStudy.

    Encapsula o material bruto extraído do PDF e todo o conteúdo
    gerado pela IA (resumo, quiz, flashcards etc.).

    Clean Code: nomes expressivos, sem abreviações; dataclass evita
    getters/setters boilerplate, mantendo a classe coesa.
    """
    id: str
    nome: str
    texto: str                              # Texto bruto extraído do PDF
    conteudo: dict = field(default_factory=dict)   # {'resumo': '...', 'questoes': '[...]', ...}
    materia_id: Optional[str] = None
    criado_em: Optional[datetime] = None
    checklist: list[ItemChecklist] = field(default_factory=list)

    def conteudo_do_tipo(self, tipo: str) -> str:
        """Retorna o conteúdo gerado para um tipo específico, ou string vazia."""
        return self.conteudo.get(tipo, "")

    def tem_conteudo(self, tipo: str) -> bool:
        """Indica se o conteúdo de um tipo já foi gerado e salvo."""
        return bool(self.conteudo.get(tipo))

    def atualizar_conteudo(self, tipo: str, valor: str) -> None:
        """Armazena o resultado gerado pela IA para um tipo de conteúdo."""
        self.conteudo[tipo] = valor

    def marcar_item_checklist(self, indice: int, feito: bool) -> None:
        """Atualiza o estado de conclusão de um item da checklist."""
        if 0 <= indice < len(self.checklist):
            self.checklist[indice].feito = feito
