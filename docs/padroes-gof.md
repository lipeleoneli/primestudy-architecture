# Padrões de Projeto (GoF) no PrimeStudy

Três padrões GoF aplicados a problemas reais do projeto — não inseridos por
obrigação. Para cada um: o problema que motivou, a solução, onde está no código
e como é verificado. O diagrama de classes correspondente está em
[`diagrams/classes-gof.md`](../diagrams/classes-gof.md).

---

## 1. Strategy (comportamental)

**Problema real:** o `gemini_services.py` do PI V tinha uma função
`gerar_conteudo()` com mais de 120 linhas e 8 `elif` — um para cada tipo de
conteúdo (resumo, quiz, flashcard…). Toda mudança em um tipo arriscava os
outros sete; adicionar um tipo novo exigia entender a função inteira.

**Solução:** cada tipo de conteúdo é uma classe que encapsula seu algoritmo de
geração (o prompt + o pós-processamento), todas sob o mesmo contrato:

```python
class ConteudoStrategy(ABC):
    def __init__(self, gerador: IGeradorIA) -> None:
        self._gerador = gerador

    @abstractmethod
    def gerar(self, texto: str, historico: str = "") -> str: ...
```

**Onde:** `src/application/strategies/` — `ResumoStrategy`,
`ResumoMenorStrategy`, `TopicosStrategy`, `ChecklistTopicosStrategy`,
`FlashcardStrategy`, `QuizStrategy`, `MapaMentalStrategy`.

**Detalhe relevante:** as Strategies não são "burras" — `QuizStrategy` valida a
resposta do modelo contra a entidade de domínio `Questao` (4 alternativas,
pergunta não vazia) e degrada para uma questão de erro válida se o JSON vier
malformado. É o ponto de tolerância a falhas citado em `docs/quality.md`.

**Verificação:** `tests/test_quiz_strategy.py` e
`test_gera_cada_tipo_de_conteudo` em `tests/test_interface.py`.

---

## 2. Factory Method (criacional) — variante parametrizada

**Problema real:** sem um ponto central de criação, `GerarConteudoUseCase`
precisaria importar e instanciar as 7 classes concretas de Strategy — o
acoplamento que o Strategy eliminou voltaria pela porta dos fundos.

**Solução:** `ConteudoFactory.criar(tipo)` é um *parameterized factory method*
(GoF, cap. 3: "o método fábrica recebe um parâmetro que identifica o tipo de
objeto a criar"). O use case pede "questoes" e recebe um `ConteudoStrategy`
pronto — nunca vê uma classe concreta:

```python
def criar(self, tipo: str) -> ConteudoStrategy:
    classe = self._REGISTRO.get(tipo)
    if classe is None:
        raise ValueError(f"Tipo de conteúdo '{tipo}' não reconhecido. ...")
    return classe(self._gerador)
```

**Onde:** `src/application/factories/conteudo_factory.py`.

**Consequência (OCP):** registrar um tipo novo é uma linha no dicionário
`_REGISTRO`; nenhum consumidor muda.

**Verificação:** `TestConteudoFactory` em `tests/test_gerar_conteudo.py`
(criação por tipo, alias, erro para tipo desconhecido).

---

## 3. Adapter (estrutural)

**Problema real:** a camada de aplicação fala os contratos do domínio
(`IGeradorIA.gerar(prompt) -> str`, `IPDFParser.extrair_texto(bytes) -> str`),
mas as bibliotecas externas têm interfaces próprias e incompatíveis:
`google-genai` expõe `client.models.generate_content(...)` com objetos de
resposta; `pdfplumber` abre streams e itera páginas.

**Solução:** um adapter por biblioteca converte a interface externa para o
contrato do port — inclusive o contrato de erro:

```python
class GeminiAdapter(IGeradorIA):
    def gerar(self, prompt: str) -> str:
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo, contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(f"Falha ao chamar o Gemini: {exc}") from exc
        ...
```

**Onde:** `src/infrastructure/gemini_adapter.py` (google-genai → `IGeradorIA`)
e `src/infrastructure/pdf_parser.py` (pdfplumber → `IPDFParser`).

**Consequência comprovada:** a troca do modelo Gemini 1.5 → 2.5 (ADR-004) não
alterou nenhum use case; trocar de provedor (ex.: OpenAI) seria um arquivo novo.

**Verificação:** os testes inteiros rodam com adapters substituídos por fakes —
a prova de que a aplicação só conhece o contrato, não a biblioteca.

---

## Bônus — Repository (Fowler, PoEAA)

Não é GoF, mas completa o conjunto: `FirestoreEstudoRepo` e `InMemoryEstudoRepo`
implementam `IEstudoRepository`, expondo os agregados Estudo/Matéria como uma
coleção em memória e escondendo toda a API do Firestore. O contrato — inclusive
`RecursoNaoEncontradoError` para atualização de estudo inexistente — é o mesmo
nas duas implementações (ver LSP em [`docs/solid.md`](solid.md)).

---

## Como os três padrões cooperam

No fluxo central (`POST /api/estudos/{id}/conteudo` — ver
[`diagrams/sequence-gerar-conteudo.md`](../diagrams/sequence-gerar-conteudo.md)):

1. o use case pede a Strategy à **Factory** (`factory.criar(tipo)`);
2. a **Strategy** monta o prompt e delega ao `IGeradorIA`;
3. o **Adapter** traduz a chamada para a SDK do Gemini (ou o fake responde, no
   modo demo);
4. o resultado é persistido via **Repository**.
