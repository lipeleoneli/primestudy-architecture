"""
Port (interface): IEstudoRepository.

Define o contrato que qualquer implementação de persistência de estudos
deve satisfazer. O domínio conhece apenas esta interface — jamais o Firestore.

SOLID — DIP: casos de uso dependem desta abstração, não da implementação concreta.

Nota sobre ISP: este é o contrato do *Repository* (padrão de Fowler) para a
fronteira de persistência. Por agregar dois agregados próximos (Estudo e
Materia), é uma interface ampla — cada caso de uso usa apenas o subconjunto de
métodos que precisa. A segregação de interface (ISP) fica evidente nos ports de
serviço, deliberadamente mínimos: IGeradorIA e IPDFParser têm um único método
cada. Caso a parte de Materia cresça, o caminho natural é extrair um
IMateriaRepository.
"""
from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.entities.materia import Materia


class IEstudoRepository(ABC):
    """Contrato de persistência para Estudos e Materias."""

    # ── Estudos ─────────────────────────────────────────────────────────────

    @abstractmethod
    def salvar_estudo(self, uid: str, estudo: Estudo) -> str:
        """Persiste um novo estudo e retorna o ID gerado."""

    @abstractmethod
    def buscar_estudo(self, uid: str, estudo_id: str) -> Optional[Estudo]:
        """Retorna o estudo pelo ID ou None se não existir."""

    @abstractmethod
    def listar_estudos_recentes(self, uid: str, limite: int = 50) -> list[Estudo]:
        """Retorna os estudos mais recentes do usuário."""

    @abstractmethod
    def atualizar_conteudo_estudo(self, uid: str, estudo_id: str, tipo: str, valor: str) -> None:
        """Persiste o conteúdo gerado (resumo, quiz etc.) em um estudo existente."""

    @abstractmethod
    def atualizar_checklist(self, uid: str, estudo_id: str, itens: list[ItemChecklist]) -> None:
        """Persiste o estado atualizado da checklist de um estudo."""

    @abstractmethod
    def atualizar_materia_do_estudo(self, uid: str, estudo_id: str, materia_id: Optional[str]) -> None:
        """Vincula ou desvincula um estudo de uma matéria (None = desvincular)."""

    @abstractmethod
    def renomear_estudo(self, uid: str, estudo_id: str, novo_nome: str) -> None:
        """Atualiza o nome de um estudo."""

    @abstractmethod
    def deletar_estudo(self, uid: str, estudo_id: str) -> None:
        """Remove um estudo permanentemente."""

    # ── Materias ─────────────────────────────────────────────────────────────

    @abstractmethod
    def listar_materias(self, uid: str) -> list[Materia]:
        """Retorna todas as matérias do usuário com contagem de estudos."""

    @abstractmethod
    def criar_materia(self, uid: str, materia: Materia) -> str:
        """Persiste uma nova matéria e retorna o ID gerado."""

    @abstractmethod
    def buscar_materia(self, uid: str, materia_id: str) -> Optional[Materia]:
        """Retorna uma matéria pelo ID ou None se não existir."""

    @abstractmethod
    def listar_estudos_da_materia(self, uid: str, materia_id: str) -> list[Estudo]:
        """Retorna todos os estudos vinculados a uma matéria."""

    @abstractmethod
    def deletar_materia(self, uid: str, materia_id: str) -> None:
        """Remove uma matéria permanentemente."""
