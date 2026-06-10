"""
Testes do contrato de IEstudoRepository sobre o InMemoryEstudoRepo.

SOLID — LSP: o port especifica que métodos de atualização lançam
RecursoNaoEncontradoError para estudo inexistente. Estes testes fixam esse
contrato na implementação de memória; o FirestoreEstudoRepo traduz o
NotFound do SDK para a mesma exceção (ver _atualizar_estudo), de modo que
as duas implementações são intercambiáveis sem mudança de comportamento.
"""
import pytest

from src.domain.entities.estudo import Estudo
from src.domain.entities.materia import Materia
from src.domain.exceptions import RecursoNaoEncontradoError
from src.infrastructure.in_memory_estudo_repo import InMemoryEstudoRepo

UID = "usuario-teste"


@pytest.fixture
def repo():
    return InMemoryEstudoRepo()


def test_salvar_estudo_carimba_criado_em(repo):
    """Mesmo comportamento do Firestore: a data de criação nunca fica nula."""
    estudo_id = repo.salvar_estudo(UID, Estudo(id="", nome="Aula", texto="t"))
    assert repo.buscar_estudo(UID, estudo_id).criado_em is not None


def test_listar_recentes_ordena_do_mais_novo_para_o_mais_antigo(repo):
    primeiro = repo.salvar_estudo(UID, Estudo(id="", nome="Antigo", texto="t"))
    segundo = repo.salvar_estudo(UID, Estudo(id="", nome="Novo", texto="t"))

    # garante ordem distinguível mesmo com timestamps quase iguais
    estudo_antigo = repo.buscar_estudo(UID, primeiro)
    estudo_antigo.criado_em = estudo_antigo.criado_em.replace(year=2000)

    recentes = repo.listar_estudos_recentes(UID)
    assert [e.id for e in recentes] == [segundo, primeiro]


@pytest.mark.parametrize("operacao", [
    lambda r: r.atualizar_conteudo_estudo(UID, "x", "resumo", "v"),
    lambda r: r.atualizar_checklist(UID, "x", []),
    lambda r: r.atualizar_materia_do_estudo(UID, "x", None),
    lambda r: r.renomear_estudo(UID, "x", "Novo"),
])
def test_atualizacoes_em_estudo_inexistente_lancam_nao_encontrado(repo, operacao):
    with pytest.raises(RecursoNaoEncontradoError):
        operacao(repo)


def test_dados_sao_isolados_por_usuario(repo):
    """Invariante de Segurança (quality.md): um uid nunca enxerga outro."""
    estudo_id = repo.salvar_estudo("usuario-a", Estudo(id="", nome="Aula", texto="t"))
    assert repo.buscar_estudo("usuario-b", estudo_id) is None
    assert repo.listar_estudos_recentes("usuario-b") == []


def test_deletar_materia_apenas_desvincula_estudos(repo):
    materia_id = repo.criar_materia(UID, Materia(id="", nome="Cálculo"))
    estudo_id = repo.salvar_estudo(
        UID, Estudo(id="", nome="Aula", texto="t", materia_id=materia_id)
    )

    repo.deletar_materia(UID, materia_id)

    estudo = repo.buscar_estudo(UID, estudo_id)
    assert estudo is not None          # o estudo sobrevive
    assert estudo.materia_id is None   # apenas o vínculo é removido
