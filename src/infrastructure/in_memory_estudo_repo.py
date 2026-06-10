"""
Adapter de persistência em memória: InMemoryEstudoRepo.

Implementação de IEstudoRepository que guarda tudo em dicionários.
Usada no modo DEMO — permite subir e explorar a API sem Firestore.

Demonstra o valor do port IEstudoRepository (DIP): trocar Firestore por
memória não exige nenhuma mudança nos use cases. É o mesmo contrato.

Padrão Repository (Fowler/PoEAA): abstrai a coleção de agregados como se
fosse uma coleção em memória — aqui literalmente é.
"""
from datetime import datetime, timezone
from typing import Optional

from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.entities.materia import Materia
from src.domain.exceptions import RecursoNaoEncontradoError
from src.domain.ports.estudo_repository import IEstudoRepository


class InMemoryEstudoRepo(IEstudoRepository):
    """Persistência volátil por usuário, para desenvolvimento e demonstração."""

    def __init__(self) -> None:
        # estrutura espelha o Firestore: dados isolados por uid
        self._estudos: dict[str, dict[str, Estudo]] = {}
        self._materias: dict[str, dict[str, Materia]] = {}
        self._sequencia = 0

    def _proximo_id(self, prefixo: str) -> str:
        self._sequencia += 1
        return f"{prefixo}-{self._sequencia}"

    # ── Estudos ─────────────────────────────────────────────────────────────

    def salvar_estudo(self, uid: str, estudo: Estudo) -> str:
        estudo.id = self._proximo_id("estudo")
        # mesmo comportamento do FirestoreEstudoRepo (LSP): carimba a criação
        estudo.criado_em = estudo.criado_em or datetime.now(timezone.utc)
        self._estudos.setdefault(uid, {})[estudo.id] = estudo
        self._recontar_materias(uid)
        return estudo.id

    def buscar_estudo(self, uid: str, estudo_id: str) -> Optional[Estudo]:
        return self._estudos.get(uid, {}).get(estudo_id)

    def listar_estudos_recentes(self, uid: str, limite: int = 50) -> list[Estudo]:
        inicio_dos_tempos = datetime.min.replace(tzinfo=timezone.utc)
        estudos = list(self._estudos.get(uid, {}).values())
        estudos.sort(key=lambda e: e.criado_em or inicio_dos_tempos, reverse=True)
        return estudos[:limite]

    def atualizar_conteudo_estudo(self, uid: str, estudo_id: str, tipo: str, valor: str) -> None:
        estudo = self._exigir_estudo(uid, estudo_id)
        estudo.atualizar_conteudo(tipo, valor)

    def atualizar_checklist(self, uid: str, estudo_id: str, itens: list[ItemChecklist]) -> None:
        estudo = self._exigir_estudo(uid, estudo_id)
        estudo.checklist = list(itens)

    def atualizar_materia_do_estudo(self, uid: str, estudo_id: str, materia_id: Optional[str]) -> None:
        estudo = self._exigir_estudo(uid, estudo_id)
        estudo.materia_id = materia_id
        self._recontar_materias(uid)

    def renomear_estudo(self, uid: str, estudo_id: str, novo_nome: str) -> None:
        self._exigir_estudo(uid, estudo_id).nome = novo_nome

    def deletar_estudo(self, uid: str, estudo_id: str) -> None:
        self._estudos.get(uid, {}).pop(estudo_id, None)
        self._recontar_materias(uid)

    # ── Materias ─────────────────────────────────────────────────────────────

    def listar_materias(self, uid: str) -> list[Materia]:
        return list(self._materias.get(uid, {}).values())

    def criar_materia(self, uid: str, materia: Materia) -> str:
        materia.id = self._proximo_id("materia")
        self._materias.setdefault(uid, {})[materia.id] = materia
        return materia.id

    def buscar_materia(self, uid: str, materia_id: str) -> Optional[Materia]:
        return self._materias.get(uid, {}).get(materia_id)

    def listar_estudos_da_materia(self, uid: str, materia_id: str) -> list[Estudo]:
        return [
            e for e in self._estudos.get(uid, {}).values()
            if e.materia_id == materia_id
        ]

    def deletar_materia(self, uid: str, materia_id: str) -> None:
        self._materias.get(uid, {}).pop(materia_id, None)
        # estudos vinculados são apenas desvinculados, não removidos
        for estudo in self._estudos.get(uid, {}).values():
            if estudo.materia_id == materia_id:
                estudo.materia_id = None

    # ── helpers privados ─────────────────────────────────────────────────────

    def _exigir_estudo(self, uid: str, estudo_id: str) -> Estudo:
        estudo = self.buscar_estudo(uid, estudo_id)
        if estudo is None:
            raise RecursoNaoEncontradoError(f"Estudo '{estudo_id}' não encontrado.")
        return estudo

    def _recontar_materias(self, uid: str) -> None:
        """Mantém Materia.total_estudos coerente após mudanças."""
        contagem: dict[str, int] = {}
        for estudo in self._estudos.get(uid, {}).values():
            if estudo.materia_id:
                contagem[estudo.materia_id] = contagem.get(estudo.materia_id, 0) + 1
        for materia in self._materias.get(uid, {}).values():
            materia.total_estudos = contagem.get(materia.id, 0)
