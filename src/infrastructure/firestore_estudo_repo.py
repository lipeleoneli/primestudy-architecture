"""
Adapter de persistência real: FirestoreEstudoRepo.

Implementa IEstudoRepository sobre o Cloud Firestore (ADR-003).

Padrão Repository (Fowler/PoEAA): expõe a coleção de agregados Estudo/Materia
ao domínio como se fosse uma coleção em memória, escondendo totalmente a API
do Firestore. Os use cases não sabem que existe Firestore.

Isolamento por usuário (Segurança — quality.md): toda referência parte de
`usuarios/{uid}/...`. Nenhuma query cruza dados entre usuários.

A SDK firebase_admin é importada tardiamente para não exigir credenciais no
modo DEMO.
"""
from datetime import datetime, timezone
from typing import Optional

from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.entities.materia import Materia
from src.domain.exceptions import RecursoNaoEncontradoError
from src.domain.ports.estudo_repository import IEstudoRepository


class FirestoreEstudoRepo(IEstudoRepository):
    """Persistência de Estudos e Materias no Cloud Firestore."""

    def __init__(self, client) -> None:
        # recebe o cliente já inicializado (injeção) — não cria global
        self._db = client

    # ── helpers de referência (isolamento por uid) ───────────────────────────

    def _col_estudos(self, uid: str):
        return self._db.collection("usuarios").document(uid).collection("estudos")

    def _col_materias(self, uid: str):
        return self._db.collection("usuarios").document(uid).collection("materias")

    def _atualizar_estudo(self, uid: str, estudo_id: str, campos: dict) -> None:
        """Aplica update traduzindo o NotFound do SDK para a exceção do port (LSP)."""
        from google.api_core import exceptions as gexc  # import tardio: só no modo real

        try:
            self._col_estudos(uid).document(estudo_id).update(campos)
        except gexc.NotFound as exc:
            raise RecursoNaoEncontradoError(f"Estudo '{estudo_id}' não encontrado.") from exc

    # ── Estudos ─────────────────────────────────────────────────────────────

    def salvar_estudo(self, uid: str, estudo: Estudo) -> str:
        ref = self._col_estudos(uid).document()
        estudo.id = ref.id
        estudo.criado_em = estudo.criado_em or datetime.now(timezone.utc)
        ref.set(self._estudo_para_doc(estudo))
        return ref.id

    def buscar_estudo(self, uid: str, estudo_id: str) -> Optional[Estudo]:
        snap = self._col_estudos(uid).document(estudo_id).get()
        if not snap.exists:
            return None
        return self._doc_para_estudo(snap.id, snap.to_dict())

    def listar_estudos_recentes(self, uid: str, limite: int = 50) -> list[Estudo]:
        from firebase_admin import firestore
        query = (
            self._col_estudos(uid)
            .order_by("criado_em", direction=firestore.Query.DESCENDING)
            .limit(limite)
        )
        return [self._doc_para_estudo(d.id, d.to_dict()) for d in query.stream()]

    def atualizar_conteudo_estudo(self, uid: str, estudo_id: str, tipo: str, valor: str) -> None:
        self._atualizar_estudo(uid, estudo_id, {f"conteudo.{tipo}": valor})

    def atualizar_checklist(self, uid: str, estudo_id: str, itens: list[ItemChecklist]) -> None:
        payload = [{"texto": i.texto, "feito": i.feito} for i in itens]
        self._atualizar_estudo(uid, estudo_id, {"checklist": payload})

    def atualizar_materia_do_estudo(self, uid: str, estudo_id: str, materia_id: Optional[str]) -> None:
        self._atualizar_estudo(uid, estudo_id, {"materia_id": materia_id})

    def renomear_estudo(self, uid: str, estudo_id: str, novo_nome: str) -> None:
        self._atualizar_estudo(uid, estudo_id, {"nome": novo_nome})

    def deletar_estudo(self, uid: str, estudo_id: str) -> None:
        self._col_estudos(uid).document(estudo_id).delete()

    # ── Materias ─────────────────────────────────────────────────────────────

    def listar_materias(self, uid: str) -> list[Materia]:
        materias = []
        for snap in self._col_materias(uid).stream():
            dados = snap.to_dict()
            total = self._col_estudos(uid).where("materia_id", "==", snap.id).count().get()
            materias.append(Materia(
                id=snap.id,
                nome=dados.get("nome", ""),
                cor=dados.get("cor", "c-blue"),
                total_estudos=int(total[0][0].value) if total else 0,
            ))
        return materias

    def criar_materia(self, uid: str, materia: Materia) -> str:
        ref = self._col_materias(uid).document()
        materia.id = ref.id
        ref.set({"nome": materia.nome, "cor": materia.cor})
        return ref.id

    def buscar_materia(self, uid: str, materia_id: str) -> Optional[Materia]:
        snap = self._col_materias(uid).document(materia_id).get()
        if not snap.exists:
            return None
        dados = snap.to_dict()
        return Materia(id=snap.id, nome=dados.get("nome", ""), cor=dados.get("cor", "c-blue"))

    def listar_estudos_da_materia(self, uid: str, materia_id: str) -> list[Estudo]:
        query = self._col_estudos(uid).where("materia_id", "==", materia_id)
        return [self._doc_para_estudo(d.id, d.to_dict()) for d in query.stream()]

    def deletar_materia(self, uid: str, materia_id: str) -> None:
        self._col_materias(uid).document(materia_id).delete()

    # ── mapeamento documento ↔ entidade ──────────────────────────────────────

    @staticmethod
    def _estudo_para_doc(estudo: Estudo) -> dict:
        return {
            "nome": estudo.nome,
            "texto": estudo.texto,
            "conteudo": estudo.conteudo,
            "materia_id": estudo.materia_id,
            "criado_em": estudo.criado_em,
            "checklist": [{"texto": i.texto, "feito": i.feito} for i in estudo.checklist],
        }

    @staticmethod
    def _doc_para_estudo(estudo_id: str, dados: dict) -> Estudo:
        checklist = [
            ItemChecklist(texto=i.get("texto", ""), feito=bool(i.get("feito")))
            for i in dados.get("checklist", [])
        ]
        return Estudo(
            id=estudo_id,
            nome=dados.get("nome", ""),
            texto=dados.get("texto", ""),
            conteudo=dados.get("conteudo", {}) or {},
            materia_id=dados.get("materia_id"),
            criado_em=dados.get("criado_em"),
            checklist=checklist,
        )
