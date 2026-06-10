# Princípios SOLID no PrimeStudy

Cada princípio é demonstrado com **trecho real do código**, a explicação técnica
e o benefício concreto obtido. Os caminhos apontam para os arquivos em `src/`.

---

## 1. SRP — Single Responsibility Principle

> Uma classe deve ter um único motivo para mudar.

**Onde:** `src/application/use_cases/processar_pdf.py`

```python
class ProcessarPDFUseCase:
    """
    Processa o upload de um PDF: extrai o texto e persiste o estudo.
    """
    def executar(self, dados: ProcessarPDFInput) -> ProcessarPDFOutput:
        texto = self._extrair_texto_ou_falhar(dados.conteudo_bytes)
        estudo = self._montar_estudo(dados, texto)
        estudo_id = self._repositorio.salvar_estudo(dados.uid, estudo)
        return ProcessarPDFOutput(estudo_id=estudo_id, redirect_url=f"/estudo/{estudo_id}")
```

**Explicação:** no PI V, a rota Flask de upload fazia *tudo*: lia o `request`,
chamava o pdfplumber, montava o documento e escrevia no Firestore. Hoje cada
responsabilidade tem seu lugar: a rota (`estudo_routes.criar_estudo`) só traduz
HTTP; o use case só orquestra a regra ("PDF sem texto legível é erro de
negócio"); a extração é do `IPDFParser`; a persistência, do `IEstudoRepository`.
O único motivo para `ProcessarPDFUseCase` mudar é uma mudança na *regra de
criação de estudos* — nunca uma troca de framework, banco ou biblioteca de PDF.

**Benefício obtido:** a regra de negócio é testada em `tests/test_gerar_conteudo.py`
(classe `TestProcessarPDFUseCase`) sem Flask, sem rede e sem PDF real.

---

## 2. OCP — Open/Closed Principle

> Aberto para extensão, fechado para modificação.

**Onde:** `src/application/strategies/` + `src/application/factories/conteudo_factory.py`

```python
class ConteudoFactory:
    _REGISTRO: dict[str, type[ConteudoStrategy]] = {
        "resumo":             ResumoStrategy,
        "resumo_menor":       ResumoMenorStrategy,
        "topicos":            TopicosStrategy,
        "checklist_topicos":  ChecklistTopicosStrategy,
        "flashcard":          FlashcardStrategy,
        "questoes":           QuizStrategy,
        "mapa":               MapaMentalStrategy,
    }
```

**Explicação:** o `gerar_conteudo()` original tinha mais de 120 linhas de
`if/elif` — cada tipo novo de conteúdo exigia editar (e arriscar quebrar) a
função inteira. Com Strategy + Factory, adicionar um tipo "Podcast Script"
significa **criar um arquivo novo** (`PodcastScriptStrategy`) e **uma linha de
registro** no dicionário acima. `GerarConteudoUseCase`, as rotas e as demais
Strategies permanecem intocados — o código existente está *fechado* para
modificação, e o sistema *aberto* para extensão.

**Benefício obtido:** a métrica de Manutenibilidade do `docs/quality.md`
(1 arquivo novo + 1 linha de registro por tipo novo) é cumprida na prática.

---

## 3. LSP — Liskov Substitution Principle

> Subtipos devem poder substituir seus tipos base sem alterar o comportamento
> esperado pelo cliente.

**Onde:** `src/domain/ports/estudo_repository.py` e suas duas implementações.

O contrato do port especifica o comportamento observável — inclusive para o
caso de erro:

```python
@abstractmethod
def renomear_estudo(self, uid: str, estudo_id: str, novo_nome: str) -> None:
    """
    Atualiza o nome de um estudo.

    Raises:
        RecursoNaoEncontradoError: Se o estudo não existir.
    """
```

E as duas implementações honram o mesmo contrato por caminhos diferentes —
`InMemoryEstudoRepo` verifica o dicionário; `FirestoreEstudoRepo` **traduz** a
exceção do SDK do Google para a exceção do domínio:

```python
def _atualizar_estudo(self, uid: str, estudo_id: str, campos: dict) -> None:
    """Aplica update traduzindo o NotFound do SDK para a exceção do port (LSP)."""
    from google.api_core import exceptions as gexc
    try:
        self._col_estudos(uid).document(estudo_id).update(campos)
    except gexc.NotFound as exc:
        raise RecursoNaoEncontradoError(f"Estudo '{estudo_id}' não encontrado.") from exc
```

**Explicação:** sem essa tradução, trocar o repositório de memória pelo
Firestore mudaria o comportamento visível da API (400/404 viraria 500), violando
LSP — o cliente (use case) seria surpreendido pelo subtipo. Com o contrato
documentado e as duas implementações alinhadas, qualquer `IEstudoRepository` é
substituível por outro. O mesmo vale para `IGeradorIA`: `GeminiAdapter` e
`FakeGeradorIA` são intercambiáveis (é exatamente o que o modo demo faz).

**Benefício obtido:** `tests/test_in_memory_repo.py` fixa o contrato em testes;
o modo demo (ADR-006) e os testes funcionam com as mesmas regras do modo real.

---

## 4. ISP — Interface Segregation Principle

> Clientes não devem ser forçados a depender de métodos que não usam.

**Onde:** `src/domain/ports/gerador_ia.py` e `src/domain/ports/pdf_parser.py`

```python
class IGeradorIA(ABC):
    @abstractmethod
    def gerar(self, prompt: str) -> str: ...

class IPDFParser(ABC):
    @abstractmethod
    def extrair_texto(self, conteudo_bytes: bytes) -> str: ...
```

**Explicação:** os ports de serviço são deliberadamente **mínimos** — um método
cada. Uma alternativa ruim seria um `IServicosExternos` único com `gerar()`,
`extrair_texto()` e `verificar_token()`: todo fake de teste seria obrigado a
implementar métodos irrelevantes para o caso testado. Com interfaces segregadas,
`ProcessarPDFUseCase` depende só de `IPDFParser` + `IEstudoRepository`, e
`GerarConteudoUseCase` nem fica sabendo que PDFs existem.

`IEstudoRepository` é a interface mais ampla do projeto por cobrir dois
agregados próximos (Estudo e Matéria) — o trade-off está documentado no próprio
arquivo do port: se a parte de matérias crescer, o caminho natural é extrair um
`IMateriaRepository`.

**Benefício obtido:** os fakes de teste (`FakePDFParser`, `FakeGeradorIA`) têm
~5 linhas cada — implementar o contrato inteiro é trivial.

---

## 5. DIP — Dependency Inversion Principle

> Módulos de alto nível não devem depender de módulos de baixo nível;
> ambos devem depender de abstrações.

**Onde:** `src/interface/app.py` (composition root)

```python
if config.eh_demo:
    repositorio: IEstudoRepository = InMemoryEstudoRepo()
    gerador: IGeradorIA = FakeGeradorIA()
else:
    firebase_auth = FirebaseAuth(config.firebase_credentials)
    repositorio = FirestoreEstudoRepo(firebase_auth.firestore_client())
    gerador = GeminiAdapter(config.gemini_api_key, config.gemini_model)
...
gerar_conteudo=GerarConteudoUseCase(repositorio, factory),
```

**Explicação:** a regra de negócio (`application/`) declara *do que precisa*
via ports (`domain/ports/`); a infraestrutura *implementa* esses ports; e o
**único** lugar do sistema que conhece classes concretas é o composition root
`create_app()`. A seta de dependência do código-fonte aponta sempre para dentro
(`infrastructure → domain`), o inverso da seta de controle em tempo de execução.

**Benefício obtido:** dois resultados diretos e verificáveis —
1. o **modo demo** (ADR-006): a aplicação inteira sobe sem credenciais trocando
   as implementações em um único ponto;
2. a troca de modelo Gemini 1.5 → 2.5 (ADR-004) não tocou nenhuma linha de
   `application/` ou `domain/`.

---

## Resumo

| Princípio | Evidência principal | Teste que comprova |
|---|---|---|
| SRP | Use cases com uma responsabilidade cada | `tests/test_gerar_conteudo.py` |
| OCP | Strategy + registro na `ConteudoFactory` | `TestConteudoFactory` |
| LSP | Contrato de erro do `IEstudoRepository` honrado pelas 2 implementações | `tests/test_in_memory_repo.py` |
| ISP | Ports de um método (`IGeradorIA`, `IPDFParser`) | fakes de ~5 linhas em `tests/` |
| DIP | Composition root único; camadas internas só veem abstrações | `tests/test_interface.py` (app real com fakes) |
