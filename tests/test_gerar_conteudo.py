"""
Testes unitários — GerarConteudoUseCase.

DEMONSTRAÇÃO DE TESTABILIDADE:
Todos os testes rodam sem internet, sem GEMINI_API_KEY e sem Firebase.
Isso só é possível porque os use cases dependem de interfaces (ports),
não de implementações concretas — princípio DIP do SOLID.

As dependências externas são substituídas por Fakes (implementações
mínimas das interfaces) que retornam respostas controladas.
"""
import json
import pytest

from src.domain.entities.estudo import Estudo
from src.domain.entities.materia import Materia
from src.domain.ports.gerador_ia import IGeradorIA
from src.domain.ports.estudo_repository import IEstudoRepository
from src.domain.ports.pdf_parser import IPDFParser
from src.application.factories.conteudo_factory import ConteudoFactory
from src.application.use_cases.gerar_conteudo import GerarConteudoUseCase, GerarConteudoInput
from src.application.use_cases.processar_pdf import ProcessarPDFUseCase, ProcessarPDFInput
from src.application.use_cases.gerenciar_materias import GerenciarMateriasUseCase, CriarMateriaInput


# ── Fakes (implementações mínimas das interfaces, sem deps externas) ──────────

class FakeGeradorIA(IGeradorIA):
    """
    Substitui o Gemini nos testes.
    Retorna uma resposta fixa e registra o prompt recebido.
    """
    def __init__(self, resposta: str = "conteudo gerado pelo fake"):
        self.resposta = resposta
        self.prompts_recebidos: list[str] = []

    def gerar(self, prompt: str) -> str:
        self.prompts_recebidos.append(prompt)
        return self.resposta


class FakeEstudoRepository(IEstudoRepository):
    """
    Substitui o Firestore nos testes.
    Usa dicionários em memória como banco de dados.
    """
    def __init__(self):
        self._estudos: dict[str, Estudo] = {}
        self._materias: dict[str, Materia] = {}
        self._proximo_id = 1

    def _novo_id(self) -> str:
        id_ = str(self._proximo_id)
        self._proximo_id += 1
        return id_

    def salvar_estudo(self, uid: str, estudo: Estudo) -> str:
        id_ = self._novo_id()
        estudo.id = id_
        self._estudos[id_] = estudo
        return id_

    def buscar_estudo(self, uid: str, estudo_id: str):
        return self._estudos.get(estudo_id)

    def listar_estudos_recentes(self, uid: str, limite: int = 50):
        return list(self._estudos.values())[:limite]

    def atualizar_conteudo_estudo(self, uid: str, estudo_id: str, tipo: str, valor: str):
        if estudo_id in self._estudos:
            self._estudos[estudo_id].conteudo[tipo] = valor

    def atualizar_checklist(self, uid: str, estudo_id: str, itens):
        if estudo_id in self._estudos:
            self._estudos[estudo_id].checklist = itens

    def atualizar_materia_do_estudo(self, uid: str, estudo_id: str, materia_id):
        if estudo_id in self._estudos:
            self._estudos[estudo_id].materia_id = materia_id

    def renomear_estudo(self, uid: str, estudo_id: str, novo_nome: str):
        if estudo_id in self._estudos:
            self._estudos[estudo_id].nome = novo_nome

    def deletar_estudo(self, uid: str, estudo_id: str):
        self._estudos.pop(estudo_id, None)

    def listar_materias(self, uid: str):
        return list(self._materias.values())

    def criar_materia(self, uid: str, materia: Materia) -> str:
        id_ = self._novo_id()
        materia.id = id_
        self._materias[id_] = materia
        return id_

    def buscar_materia(self, uid: str, materia_id: str):
        return self._materias.get(materia_id)

    def listar_estudos_da_materia(self, uid: str, materia_id: str):
        return [e for e in self._estudos.values() if e.materia_id == materia_id]

    def deletar_materia(self, uid: str, materia_id: str):
        self._materias.pop(materia_id, None)


class FakePDFParser(IPDFParser):
    """Substitui o pdfplumber nos testes."""
    def __init__(self, texto: str = "texto extraído do pdf"):
        self.texto = texto

    def extrair_texto(self, conteudo_bytes: bytes) -> str:
        return self.texto


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def uid():
    return "usuario-teste-123"

@pytest.fixture
def repositorio():
    return FakeEstudoRepository()

@pytest.fixture
def gerador():
    return FakeGeradorIA()

@pytest.fixture
def factory(gerador):
    return ConteudoFactory(gerador)

@pytest.fixture
def estudo_salvo(repositorio, uid):
    """Insere um estudo no repositório fake e retorna seu ID."""
    estudo = Estudo(id="", nome="Cálculo I", texto="Texto do PDF sobre derivadas")
    id_ = repositorio.salvar_estudo(uid, estudo)
    return id_


# ── Testes: ConteudoFactory (GoF Factory Method) ──────────────────────────────

class TestConteudoFactory:

    def test_cria_strategy_de_resumo(self, factory):
        strategy = factory.criar("resumo")
        assert strategy is not None

    def test_cria_strategy_de_questoes(self, factory):
        strategy = factory.criar("questoes")
        assert strategy is not None

    def test_cria_strategy_de_flashcard_com_alias(self, factory):
        """O alias 'flashcards' deve funcionar igual a 'flashcard'."""
        s1 = factory.criar("flashcard")
        s2 = factory.criar("flashcards")
        assert type(s1) == type(s2)

    def test_levanta_erro_para_tipo_desconhecido(self, factory):
        with pytest.raises(ValueError, match="não reconhecido"):
            factory.criar("tipo_inexistente")

    def test_lista_tipos_suportados(self, factory):
        tipos = factory.tipos_suportados()
        assert "resumo" in tipos
        assert "questoes" in tipos
        assert "flashcard" in tipos
        assert "mapa" in tipos


# ── Testes: GerarConteudoUseCase ──────────────────────────────────────────────

class TestGerarConteudoUseCase:

    def test_gera_resumo_e_persiste_no_repositorio(self, repositorio, factory, uid, estudo_salvo):
        use_case = GerarConteudoUseCase(repositorio, factory)
        dados = GerarConteudoInput(uid=uid, estudo_id=estudo_salvo, tipo="resumo")

        output = use_case.executar(dados)

        assert output.conteudo == "conteudo gerado pelo fake"
        assert output.tipo_render == "resumo"
        estudo = repositorio.buscar_estudo(uid, estudo_salvo)
        assert estudo.conteudo.get("resumo") == "conteudo gerado pelo fake"

    def test_acao_mais_concatena_ao_conteudo_existente(self, repositorio, factory, uid, estudo_salvo):
        """Ação 'mais' deve acrescentar, não sobrescrever."""
        repositorio.atualizar_conteudo_estudo(uid, estudo_salvo, "resumo", "resumo antigo")

        use_case = GerarConteudoUseCase(repositorio, factory)
        dados = GerarConteudoInput(uid=uid, estudo_id=estudo_salvo, tipo="resumo", acao="mais")
        output = use_case.executar(dados)

        assert "resumo antigo" in output.conteudo
        assert "conteudo gerado pelo fake" in output.conteudo

    def test_levanta_erro_para_estudo_inexistente(self, repositorio, factory, uid):
        use_case = GerarConteudoUseCase(repositorio, factory)
        dados = GerarConteudoInput(uid=uid, estudo_id="id-que-nao-existe", tipo="resumo")

        with pytest.raises(ValueError, match="não encontrado"):
            use_case.executar(dados)

    def test_questoes_resumo_usa_resumo_como_base(self, repositorio, factory, gerador, uid, estudo_salvo):
        """questoes_resumo deve usar o resumo salvo, não o texto do PDF."""
        repositorio.atualizar_conteudo_estudo(uid, estudo_salvo, "resumo", "conteudo do resumo")

        questao_fake = json.dumps([{
            "pergunta": "Qual o tema?",
            "alternativas": ["A", "B", "C", "D"],
            "correta": 0,
            "explicacao": "É A."
        }])
        gerador.resposta = questao_fake

        use_case = GerarConteudoUseCase(repositorio, factory)
        dados = GerarConteudoInput(uid=uid, estudo_id=estudo_salvo, tipo="questoes_resumo")
        output = use_case.executar(dados)

        prompt_enviado = gerador.prompts_recebidos[-1]
        assert "conteudo do resumo" in prompt_enviado
        assert output.tipo_render == "questoes"

    def test_questoes_resumo_falha_sem_resumo_gerado(self, repositorio, factory, uid, estudo_salvo):
        use_case = GerarConteudoUseCase(repositorio, factory)
        dados = GerarConteudoInput(uid=uid, estudo_id=estudo_salvo, tipo="questoes_resumo")

        with pytest.raises(ValueError, match="Resumo"):
            use_case.executar(dados)


# ── Testes: ProcessarPDFUseCase ───────────────────────────────────────────────

class TestProcessarPDFUseCase:

    def test_salva_estudo_e_retorna_redirect(self, repositorio, uid):
        use_case = ProcessarPDFUseCase(FakePDFParser(), repositorio)
        dados = ProcessarPDFInput(uid=uid, conteudo_bytes=b"pdf", nome_arquivo="aula1.pdf")

        output = use_case.executar(dados)

        assert output.estudo_id is not None
        assert "/estudo/" in output.redirect_url
        estudo = repositorio.buscar_estudo(uid, output.estudo_id)
        assert estudo.nome == "aula1.pdf"
        assert estudo.texto == "texto extraído do pdf"

    def test_falha_com_pdf_sem_texto(self, repositorio, uid):
        parser_vazio = FakePDFParser(texto="   ")
        use_case = ProcessarPDFUseCase(parser_vazio, repositorio)
        dados = ProcessarPDFInput(uid=uid, conteudo_bytes=b"pdf", nome_arquivo="scan.pdf")

        with pytest.raises(ValueError, match="texto selecionável"):
            use_case.executar(dados)

    def test_vincula_materia_quando_informada(self, repositorio, uid):
        use_case = ProcessarPDFUseCase(FakePDFParser(), repositorio)
        dados = ProcessarPDFInput(uid=uid, conteudo_bytes=b"pdf", nome_arquivo="aula.pdf", materia_id="mat-001")

        output = use_case.executar(dados)

        estudo = repositorio.buscar_estudo(uid, output.estudo_id)
        assert estudo.materia_id == "mat-001"


# ── Testes: GerenciarMateriasUseCase ─────────────────────────────────────────

class TestGerenciarMateriasUseCase:

    def test_cria_materia_e_retorna_id(self, repositorio, uid):
        use_case = GerenciarMateriasUseCase(repositorio)
        dados = CriarMateriaInput(uid=uid, nome="Cálculo I", cor="c-blue")

        id_ = use_case.criar_materia(dados)

        assert id_ is not None
        materia = repositorio.buscar_materia(uid, id_)
        assert materia.nome == "Cálculo I"

    def test_rejeita_materia_com_nome_vazio(self, repositorio, uid):
        use_case = GerenciarMateriasUseCase(repositorio)
        dados = CriarMateriaInput(uid=uid, nome="", cor="c-blue")

        with pytest.raises(ValueError):
            use_case.criar_materia(dados)

    def test_lista_materias_do_usuario(self, repositorio, uid):
        use_case = GerenciarMateriasUseCase(repositorio)
        use_case.criar_materia(CriarMateriaInput(uid=uid, nome="Física"))
        use_case.criar_materia(CriarMateriaInput(uid=uid, nome="Química"))

        materias = use_case.listar_materias(uid)

        assert len(materias) == 2
