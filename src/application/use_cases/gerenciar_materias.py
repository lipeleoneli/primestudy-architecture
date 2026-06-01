"""
Caso de uso: GerenciarMaterias.

SOLID — SRP: responsável apenas pelas operações de CRUD de matérias
             e vinculação de estudos a elas.
SOLID — DIP: depende de IEstudoRepository, não do Firestore diretamente.

Clean Code: métodos pequenos e com nomes que revelam intenção;
            sem lógica de HTTP aqui — só regras de negócio.
"""
from dataclasses import dataclass
from typing import Optional

from src.domain.entities.materia import Materia
from src.domain.entities.estudo import Estudo
from src.domain.ports.estudo_repository import IEstudoRepository


@dataclass
class CriarMateriaInput:
    uid: str
    nome: str
    cor: str = "c-blue"


@dataclass
class VincularEstudoInput:
    uid: str
    estudo_id: str
    materia_id: Optional[str]   # None = desvincular


class GerenciarMateriasUseCase:
    """
    Gerencia o ciclo de vida das matérias e sua relação com estudos.

    Operações disponíveis:
    - listar_materias
    - criar_materia
    - deletar_materia
    - vincular_estudo / desvincular_estudo
    - listar_estudos_da_materia
    """

    def __init__(self, repositorio: IEstudoRepository) -> None:
        self._repositorio = repositorio

    def listar_materias(self, uid: str) -> list[Materia]:
        """Retorna todas as matérias do usuário."""
        return self._repositorio.listar_materias(uid)

    def criar_materia(self, dados: CriarMateriaInput) -> str:
        """Valida e persiste uma nova matéria, retornando seu ID."""
        materia = Materia(id="", nome=dados.nome, cor=dados.cor)
        return self._repositorio.criar_materia(dados.uid, materia)

    def deletar_materia(self, uid: str, materia_id: str) -> None:
        """Remove a matéria. Não remove os estudos vinculados — apenas desvincula."""
        self._repositorio.deletar_materia(uid, materia_id)

    def vincular_estudo(self, dados: VincularEstudoInput) -> None:
        """Vincula ou desvincula um estudo de uma matéria."""
        self._repositorio.atualizar_materia_do_estudo(
            dados.uid, dados.estudo_id, dados.materia_id
        )

    def listar_estudos_da_materia(self, uid: str, materia_id: str) -> list[Estudo]:
        """Retorna todos os estudos vinculados à matéria."""
        self._garantir_materia_existe(uid, materia_id)
        return self._repositorio.listar_estudos_da_materia(uid, materia_id)

    # ── helpers privados ─────────────────────────────────────────────────────

    def _garantir_materia_existe(self, uid: str, materia_id: str) -> None:
        if self._repositorio.buscar_materia(uid, materia_id) is None:
            raise ValueError(f"Matéria '{materia_id}' não encontrada.")
