"""
Caso de uso: GerarConteudo.

Orquestra a geração de um tipo de conteúdo para um estudo existente,
usando a Strategy selecionada pela ConteudoFactory.
"""
import json
from dataclasses import dataclass

from src.application.factories.conteudo_factory import ConteudoFactory
from src.domain.ports.estudo_repository import IEstudoRepository


@dataclass
class GerarConteudoInput:
    """Dados de entrada para o caso de uso GerarConteudo."""
    uid: str
    estudo_id: str
    tipo: str           # 'resumo', 'questoes', 'flashcard'…
    acao: str = "novo"  # 'novo' | 'mais'


@dataclass
class GerarConteudoOutput:
    """Resultado do caso de uso GerarConteudo."""
    conteudo: str       # conteúdo final (HTML, JSON ou texto puro)
    tipo_render: str    # tipo que o frontend usa para renderizar


class GerarConteudoUseCase:
    """
    Gera (ou amplia) o conteúdo de um estudo usando a Strategy correta.

    Fluxo:
      1. Busca o estudo no repositório.
      2. Resolve o tipo de IA e de persistência (lida com alias 'questoes_resumo').
      3. Obtém a Strategy via Factory.
      4. Chama strategy.gerar(texto, historico).
      5. Mescla com conteúdo existente se ação == 'mais'.
      6. Persiste o resultado e retorna.
    """

    def __init__(
        self,
        repositorio: IEstudoRepository,
        factory: ConteudoFactory,
    ) -> None:
        self._repositorio = repositorio
        self._factory = factory

    def executar(self, dados: GerarConteudoInput) -> GerarConteudoOutput:
        estudo = self._buscar_ou_falhar(dados.uid, dados.estudo_id)
        tipo_ia, tipo_salvar, texto_base = self._resolver_texto_base(dados.tipo, estudo)
        historico = estudo.conteudo_do_tipo(tipo_salvar) if dados.acao == "mais" else ""

        strategy = self._factory.criar(tipo_ia)
        resultado = strategy.gerar(texto_base, historico)

        conteudo_final = self._mesclar(resultado, historico, tipo_salvar)
        self._repositorio.atualizar_conteudo_estudo(dados.uid, dados.estudo_id, tipo_salvar, conteudo_final)

        return GerarConteudoOutput(conteudo=conteudo_final, tipo_render=tipo_salvar)

    # ── helpers privados ─────────────────────────────────────────────────────

    def _buscar_ou_falhar(self, uid: str, estudo_id: str):
        estudo = self._repositorio.buscar_estudo(uid, estudo_id)
        if estudo is None:
            raise ValueError(f"Estudo '{estudo_id}' não encontrado.")
        return estudo

    @staticmethod
    def _resolver_texto_base(tipo: str, estudo) -> tuple[str, str, str]:
        """
        Resolve alias e devolve (tipo_ia, tipo_salvar, texto_base).

        'questoes_resumo' gera questões baseadas no resumo já salvo,
        não no texto bruto do PDF — por isso tem tratamento especial.
        """
        if tipo == "questoes_resumo":
            resumo = estudo.conteudo_do_tipo("resumo")
            if not resumo:
                raise ValueError("Gere um Resumo antes de criar questões do resumo.")
            return "questoes", "questoes", resumo
        return tipo, tipo, estudo.texto

    @staticmethod
    def _mesclar(novo: str, historico: str, tipo: str) -> str:
        """Concatena conteúdo novo ao existente para a ação 'mais'."""
        if not historico:
            return novo
        if tipo == "questoes":
            return _mesclar_json(historico, novo)
        return historico + "\n\n" + novo


def _mesclar_json(antigo: str, novo: str) -> str:
    """Une duas listas JSON de questões em uma só."""
    try:
        return json.dumps(json.loads(antigo) + json.loads(novo), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return novo
