# PrimeStudy

Plataforma que transforma PDFs de estudo em conteúdo gerado por IA — **resumo,
tópicos, flashcards, quiz e mapa mental** — e organiza o material por matérias,
com checklist de tópicos por estudo.

Projeto da disciplina **12452 – Padrões e Arquitetura de Software** (PUC-Campinas).
A arquitetura, decisões e padrões estão documentados em [`docs/`](docs/) e [`adrs/`](adrs/).

---

## Tecnologias utilizadas

- **Python 3.11+** + **Flask** — API REST (JSON)
- **Google Firestore** (`firebase-admin`) — banco NoSQL gerenciado (ADR-003)
- **Google Gemini 2.5 Flash** (`google-genai`) — geração de conteúdo (ADR-004)
- **pdfplumber** — extração de texto de PDFs
- **pytest** — testes automatizados

---

## Arquitetura em uma frase

Monolito modular (ADR-001) organizado em **Clean Architecture** (ADR-002): o
domínio no centro, dependências apontando para dentro, infraestrutura e HTTP na
borda. As decisões estão registradas como ADRs em [`adrs/`](adrs/) e a
API em [`docs/openapi.yaml`](docs/openapi.yaml).

```
src/
  domain/          entidades + ports (interfaces) — Python puro, sem dependências
  application/     casos de uso, Strategies (GoF), Factory (GoF)
  infrastructure/  adapters: Firestore, Gemini, pdfplumber (GoF Adapter) + impls de demo
  interface/       Flask: composition root, blueprints, guard de auth, erros
tests/             testes unitários (rodam sem rede)
adrs/              Registros de Decisão Arquitetural (ADR-001 a 006)
diagrams/          diagramas Mermaid (C4, classes GoF, sequência)
docs/              OpenAPI, atributos de qualidade, guia da estrutura
```

---

## Pré-requisitos

- Python **3.11+** (desenvolvido em 3.14)
- `pip`

---

## Instalação

```bash
git clone <url-do-repositorio>
cd primestudy-architecture
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Execução

A aplicação opera em dois modos. O modo é escolhido automaticamente: **sem
credenciais reais, sobe em modo demo.**

### Modo DEMO (sem credenciais) — recomendado para avaliar

Usa um repositório **em memória** e uma **IA fake** (respostas determinísticas).
Não precisa de Firebase nem chave do Gemini. Sobe na hora:

```bash
flask --app src.interface.app:create_app run
# ou:
python -c "from src.interface.app import create_app; create_app().run(debug=True)"
```

Servidor em `http://localhost:5000`. Teste:

```bash
curl http://localhost:5000/api/health
# {"status":"ok","modo":"demo"}

# No modo demo o login é dispensado (um usuário fixo é usado):
curl -c cookies.txt -X POST http://localhost:5000/api/sessao
curl -b cookies.txt -X POST http://localhost:5000/api/materias \
     -H "Content-Type: application/json" -d '{"nome":"Cálculo I"}'
curl -b cookies.txt http://localhost:5000/api/materias
```

### Modo REAL (Firestore + Gemini)

Defina as variáveis de ambiente. A presença de **ambas** as credenciais ativa o
modo real automaticamente:

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da API Google Gemini. |
| `FIREBASE_CREDENTIALS` | Caminho do JSON da service account do Firebase. |
| `GEMINI_MODEL` | Opcional. Modelo de IA (padrão `gemini-2.5-flash`). |
| `SECRET_KEY` | Chave de assinatura da sessão Flask (use um valor forte). |
| `PRIMESTUDY_MODE` | Opcional. Força `demo` ou `real`. |

```bash
# Linux/macOS
export GEMINI_API_KEY="sua-chave"
export FIREBASE_CREDENTIALS="./serviceAccountKey.json"
export SECRET_KEY="troque-isto"
flask --app src.interface.app:create_app run
```

No modo real, o frontend deve autenticar via Firebase e enviar o `idToken`:

```bash
curl -c cookies.txt -X POST http://localhost:5000/api/sessao \
     -H "Content-Type: application/json" -d '{"idToken":"<idToken-do-firebase>"}'
```

> Os arquivos de credenciais estão no `.gitignore` e **nunca** devem ser
> versionados.

---

## Testes

```bash
pytest -q
```

Os testes rodam **sem internet, sem `GEMINI_API_KEY` e sem Firebase** — as
dependências externas são substituídas por fakes via os ports (demonstração de
testabilidade; ver `docs/quality.md`).

---

## API

Especificação completa em [`docs/openapi.yaml`](docs/openapi.yaml) (OpenAPI 3.0,
validada contra as rotas reais). Abra em [Swagger Editor](https://editor.swagger.io/)
ou Redoc.

Resumo dos endpoints (todos sob `/api`, autenticados por cookie de sessão):

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/sessao` | Cria sessão (troca idToken por cookie). |
| `DELETE` | `/api/sessao` | Logout. |
| `POST` | `/api/estudos` | Cria estudo via upload de PDF. |
| `GET` | `/api/estudos` | Lista estudos (paginado). |
| `GET` | `/api/estudos/{id}` | Detalha um estudo. |
| `PATCH` | `/api/estudos/{id}` | Renomeia. |
| `DELETE` | `/api/estudos/{id}` | Remove. |
| `POST` | `/api/estudos/{id}/conteudo` | Gera/amplia conteúdo via IA. |
| `GET`/`PUT` | `/api/estudos/{id}/checklist` | Obtém / salva a checklist. |
| `PUT` | `/api/estudos/{id}/materia` | Vincula/desvincula de matéria. |
| `GET`/`POST` | `/api/materias` | Lista / cria matérias. |
| `DELETE` | `/api/materias/{id}` | Remove matéria. |
| `GET` | `/api/materias/{id}/estudos` | Estudos de uma matéria. |

---

## Documentação do projeto

- [`docs/introducao.md`](docs/introducao.md) — apresentação, objetivos e público-alvo.
- [`adrs/`](adrs/) — Registros de Decisão Arquitetural (ADR-001 a 006; o ADR-004
  documenta uma decisão revisada — Gemini 1.5 → 2.5).
- [`diagrams/`](diagrams/) — diagramas Mermaid (C4, classes GoF, sequência);
  renderizam direto no GitHub ou em [mermaid.live](https://mermaid.live).
- [`docs/openapi.yaml`](docs/openapi.yaml) — especificação da API REST; abra em
  [Swagger Editor](https://editor.swagger.io/) ou Redoc para navegar.
- [`docs/quality.md`](docs/quality.md) — atributos de qualidade (ISO/IEC 25010).
- [`docs/solid.md`](docs/solid.md) — os 5 princípios SOLID com trechos reais do código.
- [`docs/padroes-gof.md`](docs/padroes-gof.md) — padrões GoF: problema, solução e verificação.
- [`docs/estrutura-do-projeto.md`](docs/estrutura-do-projeto.md) — guia das camadas.

### Padrões aplicados
- **GoF Strategy** — uma classe por tipo de conteúdo (`application/strategies/`).
- **GoF Factory Method** — `ConteudoFactory` instancia a Strategy certa.
- **GoF Adapter** — `GeminiAdapter`, `PDFParser` adaptam libs externas aos ports.
- **Repository (Fowler)** — `FirestoreEstudoRepo` / `InMemoryEstudoRepo`.

Detalhes, motivação e verificação de cada padrão em [`docs/padroes-gof.md`](docs/padroes-gof.md).

---

## Equipe

| Integrante | RA |
|---|---|
| _Nome do integrante 1_ | _RA_ |
| _Nome do integrante 2_ | _RA_ |
| _Nome do integrante 3_ | _RA_ |
| _Nome do integrante 4_ | _RA_ |
| _Nome do integrante 5_ | _RA_ |
| _Nome do integrante 6_ | _RA_ |

> Preencha com os nomes e RAs dos 6 integrantes antes da entrega.
