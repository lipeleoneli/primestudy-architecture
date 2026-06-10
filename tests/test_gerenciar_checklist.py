"""
Testes unitários — GerenciarChecklistUseCase.

Provam o comportamento de cache descrito em docs/quality.md (Eficiência de
Desempenho): se a checklist já existe, a IA NÃO é chamada de novo.
"""
import pytest

from src.application.factories.conteudo_factory import ConteudoFactory
from src.application.use_cases.gerenciar_checklist import (
    GerenciarChecklistUseCase,
    SalvarChecklistInput,
)
from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.exceptions import RecursoNaoEncontradoError
from src.infrastructure.in_memory_estudo_repo import InMemoryEstudoRepo
from tests.test_gerar_conteudo import FakeGeradorIA

UID = "usuario-teste"


@pytest.fixture
def repositorio():
    return InMemoryEstudoRepo()


@pytest.fixture
def gerador():
    return FakeGeradorIA(resposta="Tópico um\nTópico dois\nTópico três")


@pytest.fixture
def use_case(repositorio, gerador):
    return GerenciarChecklistUseCase(repositorio, ConteudoFactory(gerador))


def _salvar_estudo(repositorio, **kwargs) -> str:
    padrao = {"id": "", "nome": "Aula", "texto": "texto do pdf"}
    return repositorio.salvar_estudo(UID, Estudo(**{**padrao, **kwargs}))


def test_gera_checklist_na_primeira_vez_e_persiste(use_case, repositorio, gerador):
    estudo_id = _salvar_estudo(repositorio)

    itens = use_case.obter_ou_gerar(UID, estudo_id)

    assert [i.texto for i in itens] == ["Tópico um", "Tópico dois", "Tópico três"]
    assert len(gerador.prompts_recebidos) == 1
    assert repositorio.buscar_estudo(UID, estudo_id).checklist == itens


def test_checklist_existente_nao_chama_a_ia(use_case, repositorio, gerador):
    estudo_id = _salvar_estudo(repositorio)
    existente = [ItemChecklist(texto="Já gerado", feito=True)]
    repositorio.atualizar_checklist(UID, estudo_id, existente)

    itens = use_case.obter_ou_gerar(UID, estudo_id)

    assert itens == existente
    assert gerador.prompts_recebidos == []   # IA não foi acionada


def test_estudo_sem_texto_nao_gera(use_case, repositorio):
    estudo_id = _salvar_estudo(repositorio, texto="")
    with pytest.raises(ValueError, match="material"):
        use_case.obter_ou_gerar(UID, estudo_id)


def test_estudo_inexistente_lanca_nao_encontrado(use_case):
    with pytest.raises(RecursoNaoEncontradoError):
        use_case.obter_ou_gerar(UID, "nao-existe")


def test_salvar_normaliza_itens_brutos(use_case, repositorio):
    estudo_id = _salvar_estudo(repositorio)
    brutos = [
        {"texto": "Válido", "feito": True},
        {"feito": True},                     # sem texto → descartado
        "não é dict",                        # tipo errado → descartado
    ]

    use_case.salvar(SalvarChecklistInput(uid=UID, estudo_id=estudo_id, itens=brutos))

    salvos = repositorio.buscar_estudo(UID, estudo_id).checklist
    assert salvos == [ItemChecklist(texto="Válido", feito=True)]
