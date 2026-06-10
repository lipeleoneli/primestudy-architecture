"""
Caso de uso: GerenciarChecklist.

SOLID — SRP: responsável apenas pela lógica de obtenção e persistência
             da checklist de tópicos de um estudo.

Separa a geração inicial (quando não existe checklist) da
simples leitura (quando já existe) — evitando chamadas desnecessárias à IA.
"""
from dataclasses import dataclass

from src.application.factories.conteudo_factory import ConteudoFactory
from src.domain.entities.estudo import ItemChecklist
from src.domain.exceptions import RecursoNaoEncontradoError
from src.domain.ports.estudo_repository import IEstudoRepository


@dataclass
class SalvarChecklistInput:
    uid: str
    estudo_id: str
    itens: list[dict]   # [{'texto': str, 'feito': bool}]


class GerenciarChecklistUseCase:
    """
    Obtém ou gera a checklist de tópicos de um estudo.

    Se a checklist já existe no repositório, retorna direto.
    Se não existe, usa a Strategy de checklist_topicos para gerá-la.
    """

    def __init__(
        self,
        repositorio: IEstudoRepository,
        factory: ConteudoFactory,
    ) -> None:
        self._repositorio = repositorio
        self._factory = factory

    def obter_ou_gerar(self, uid: str, estudo_id: str) -> list[ItemChecklist]:
        """Retorna checklist existente ou gera uma nova via IA."""
        estudo = self._buscar_ou_falhar(uid, estudo_id)

        if estudo.checklist:
            return estudo.checklist

        if not estudo.texto:
            raise ValueError("Este estudo não tem material para gerar a checklist.")

        return self._gerar_e_persistir(uid, estudo_id, estudo.texto)

    def salvar(self, dados: SalvarChecklistInput) -> None:
        """Persiste o estado atualizado (itens marcados) da checklist."""
        itens = self._normalizar_itens(dados.itens)
        self._repositorio.atualizar_checklist(dados.uid, dados.estudo_id, itens)

    # ── helpers privados ─────────────────────────────────────────────────────

    def _buscar_ou_falhar(self, uid: str, estudo_id: str):
        estudo = self._repositorio.buscar_estudo(uid, estudo_id)
        if estudo is None:
            raise RecursoNaoEncontradoError(f"Estudo '{estudo_id}' não encontrado.")
        return estudo

    def _gerar_e_persistir(self, uid: str, estudo_id: str, texto: str) -> list[ItemChecklist]:
        strategy = self._factory.criar("checklist_topicos")
        resultado = strategy.gerar(texto)
        itens = self._parsear_linhas(resultado)
        if not itens:
            raise RuntimeError("Não foi possível gerar a checklist.")
        self._repositorio.atualizar_checklist(uid, estudo_id, itens)
        return itens

    @staticmethod
    def _parsear_linhas(texto: str) -> list[ItemChecklist]:
        itens = []
        for linha in texto.split("\n"):
            topico = linha.strip().lstrip("-*•0123456789.) ").strip()
            if topico:
                itens.append(ItemChecklist(texto=topico, feito=False))
        return itens

    @staticmethod
    def _normalizar_itens(brutos: list[dict]) -> list[ItemChecklist]:
        return [
            ItemChecklist(texto=str(it["texto"]), feito=bool(it.get("feito")))
            for it in brutos
            if isinstance(it, dict) and it.get("texto")
        ]
