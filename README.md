# PrimeStudy

Plataforma que transforma PDFs de estudo em conteúdo gerado por IA — **resumo,
tópicos, flashcards, quiz interativo e mapa mental** — e organiza o material por
matérias, com checklist de tópicos por estudo.

Projeto da disciplina **12452 – Padrões e Arquitetura de Software** (PUC-Campinas).

---

## Sumário

1. [Visão geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Tecnologias](#tecnologias)
4. [Estrutura do projeto](#estrutura-do-projeto)
5. [Como executar](#como-executar)
6. [Como usar](#como-usar)
7. [Como testar](#como-testar)
8. [API](#api)
9. [Documentação](#documentação)
10. [Solução de problemas](#solução-de-problemas)
11. [Equipe](#equipe)

---

## Visão geral

**O problema:** estudar a partir de PDFs longos (slides, capítulos, artigos) é
lento — o estudante precisa reler tudo para extrair o essencial e montar seu
próprio material de revisão.

**A solução:** o PrimeStudy recebe o PDF, extrai o texto e gera sob demanda:

| Conteúdo | Descrição |
|---|---|
| **Resumo** (normal e curto) | Síntese organizada do material |
| **Tópicos** | Lista dos pontos principais |
| **Flashcards** | Cartões pergunta/resposta para revisão ativa |
| **Quiz** | Questões de múltipla escolha com explicação (validadas pelo domínio: sempre 4 alternativas) |
| **Mapa mental** | Estrutura hierárquica do conteúdo |
| **Checklist** | Tópicos de estudo marcáveis para acompanhar o progresso |

Os estudos são organizados por **matérias** e isolados **por usuário**.

É a evolução arquitetural do projeto do PI V: o monólito original (`app.py` de
435 linhas) foi refatorado para demonstrar Clean Architecture, SOLID, Clean
Code e padrões GoF — ver [`docs/introducao.md`](docs/introducao.md).

---

## Arquitetura

**Monolito modular** ([ADR-001](adrs/ADR-001.md)) organizado em **Clean
Architecture** ([ADR-002](adrs/ADR-002.md)): o domínio no centro, dependências
apontando sempre para dentro, infraestrutura e HTTP na borda.

```
┌───────────────────────────────────────────────────────────┐
│ interface/        Flask: rotas, auth, erros, UI estática  │  ← borda HTTP
├───────────────────────────────────────────────────────────┤
│ infrastructure/   Firestore, Gemini, pdfplumber (Adapters)│  ← implementa os ports
├───────────────────────────────────────────────────────────┤
│ application/      Use Cases, Strategies, Factory          │  ← orquestração
├───────────────────────────────────────────────────────────┤
│ domain/           Entidades + Ports (interfaces)          │  ← núcleo puro
└───────────────────────────────────────────────────────────┘
        a seta de dependência aponta sempre para BAIXO
```

Pontos-chave:

- **Ports & Adapters:** o núcleo define interfaces (`IEstudoRepository`,
  `IGeradorIA`, `IPDFParser`); a infraestrutura as implementa. Trocar o banco ou
  o modelo de IA não toca a regra de negócio.
- **Dois modos de operação** ([ADR-006](adrs/ADR-006.md)): com credenciais reais
  usa Firestore + Gemini; **sem credenciais sobe em modo demo** (repositório em
  memória + IA fake) — projetado para avaliação imediata.
- **Padrões GoF:** Strategy (um algoritmo de geração por tipo de conteúdo),
  Factory Method (`ConteudoFactory`), Adapter (`GeminiAdapter`, `PDFParser`) +
  Repository (Fowler). Detalhes em [`docs/padroes-gof.md`](docs/padroes-gof.md).
- **SOLID:** os cinco princípios com trechos reais do código em
  [`docs/solid.md`](docs/solid.md).

---

## Tecnologias

| Tecnologia | Papel |
|---|---|
| **Python 3.11+** / **Flask** | API REST (JSON) e servidor da UI de demonstração |
| **Google Firestore** (`firebase-admin`) | Banco NoSQL gerenciado ([ADR-003](adrs/ADR-003.md)) |
| **Google Gemini 2.5 Flash** (`google-genai`) | Geração de conteúdo ([ADR-004](adrs/ADR-004.md)) |
| **pdfplumber** | Extração de texto de PDFs |
| **pytest** | Testes automatizados (79 testes, sem rede) |
| **HTML/CSS/JS puro** | UI mínima de demonstração (arquivo único, sem build) |

---

## Estrutura do projeto

```
primestudy-architecture/
├── src/
│   ├── domain/           # Núcleo: entidades, exceções e ports — Python puro
│   ├── application/      # Use cases + Strategies (GoF) + Factory (GoF)
│   ├── infrastructure/   # Adapters: Firestore, Gemini, pdfplumber + impls de demo
│   └── interface/        # Flask: composition root, rotas, auth, erros, UI estática
├── tests/                # 79 testes (use cases, entidades, strategies, HTTP)
├── adrs/                 # 6 Registros de Decisão Arquitetural
├── diagrams/             # Diagramas Mermaid (C4, classes GoF, sequência)
├── docs/                 # OpenAPI, qualidade, SOLID, padrões GoF, introdução
├── requirements.txt
└── .env.example          # Modelo das variáveis de ambiente
```

Guia detalhado de cada camada: [`docs/estrutura-do-projeto.md`](docs/estrutura-do-projeto.md).

---

## Como executar

### 1. Pré-requisitos

- **Python 3.11 ou superior** — verifique com `python --version`
- `pip` (acompanha o Python)

### 2. Instalação

```bash
git clone https://github.com/lipeleoneli/primestudy-architecture
cd primestudy-architecture

# criar e ativar ambiente virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# instalar dependências
pip install -r requirements.txt
```

> **Windows:** se `python` não for reconhecido, use o caminho completo do
> executável (ex.: `& "C:\Program Files\Python312\python.exe" -m venv .venv`)
> ou instale pelo [python.org](https://www.python.org/downloads/) marcando
> **"Add Python to PATH"**.

### 3. Subir o servidor — modo DEMO (recomendado para avaliar)

Não precisa de nenhuma credencial:

```bash
python -m flask --app src.interface.app:create_app run
```

Saída esperada: `Running on http://127.0.0.1:5000`. **Deixe esse terminal
aberto** — o servidor só responde enquanto o processo estiver rodando.

No modo demo:
- a persistência é **em memória** (os dados somem ao reiniciar — esperado);
- a IA é **fake** (respostas determinísticas marcadas com `[DEMO]`);
- o login é dispensado (um usuário fixo é usado).

### 4. (Opcional) Modo REAL — Firestore + Gemini

Defina as variáveis de ambiente (modelo em [`.env.example`](.env.example)).
A presença de **ambas** as credenciais ativa o modo real automaticamente:

| Variável | Descrição |
|---|---|
| `GEMINI_API_KEY` | Chave da API Google Gemini ([AI Studio](https://aistudio.google.com)). |
| `FIREBASE_CREDENTIALS` | Caminho do JSON da service account do Firebase. |
| `SECRET_KEY` | Chave de assinatura da sessão Flask (use um valor forte). |
| `GEMINI_MODEL` | Opcional. Modelo de IA (padrão `gemini-2.5-flash`). |
| `PRIMESTUDY_MODE` | Opcional. Força `demo` ou `real`. |

```bash
# Linux/macOS                              # Windows (PowerShell)
export GEMINI_API_KEY="sua-chave"          $env:GEMINI_API_KEY="sua-chave"
export FIREBASE_CREDENTIALS="./sa.json"    $env:FIREBASE_CREDENTIALS=".\sa.json"
export SECRET_KEY="troque-isto"            $env:SECRET_KEY="troque-isto"
python -m flask --app src.interface.app:create_app run
```

> Credenciais estão no `.gitignore` e **nunca** devem ser versionadas.

---

## Como usar

### Pela interface web (mais simples)

Abra **http://localhost:5000** no navegador. A UI de demonstração permite o
fluxo completo:

1. **Criar matérias** no painel lateral (ex.: "Cálculo I").
2. **Enviar um PDF** (com texto selecionável — PDFs escaneados são rejeitados
   com mensagem clara), vinculando ou não a uma matéria.
3. Clicar no estudo e **gerar conteúdo**: Resumo, Resumo curto, Tópicos,
   Flashcards (com "mostrar resposta"), Quiz (interativo: clique na alternativa
   e veja acerto/erro com explicação) e Mapa mental.
4. **Checklist**: gera os tópicos do material, permite marcar os concluídos e
   salvar.

### Pela linha de comando

```bash
curl http://localhost:5000/api/health
# {"status":"ok","modo":"demo"}

# cria sessão (no modo demo o login é dispensado):
curl -c cookies.txt -X POST http://localhost:5000/api/sessao

# cria e lista matérias:
curl -b cookies.txt -X POST http://localhost:5000/api/materias \
     -H "Content-Type: application/json" -d '{"nome":"Cálculo I"}'
curl -b cookies.txt http://localhost:5000/api/materias

# cria um estudo a partir de um PDF:
curl -b cookies.txt -X POST http://localhost:5000/api/estudos \
     -F "arquivo=@caminho/do/material.pdf"

# gera um resumo para o estudo criado:
curl -b cookies.txt -X POST http://localhost:5000/api/estudos/<id>/conteudo \
     -H "Content-Type: application/json" -d '{"tipo":"resumo"}'
```

> No Windows PowerShell use `curl.exe` (o `curl` puro é alias de outro comando).

---

## Como testar

```bash
python -m pytest -q
```

Resultado esperado: **79 passed** em menos de um segundo. Os testes rodam
**sem internet, sem `GEMINI_API_KEY` e sem Firebase** — as dependências
externas são substituídas por fakes através dos ports (DIP na prática; ver
[`docs/quality.md`](docs/quality.md), seção Testabilidade).

Cobertura por área:

| Arquivo de teste | O que prova |
|---|---|
| `test_gerar_conteudo.py` | Use cases com fakes (geração, PDF, matérias) e Factory |
| `test_interface.py` | Contrato HTTP: status codes, erros 404/400/401, paginação, modo real exige sessão |
| `test_quiz_strategy.py` | Resposta malformada da IA nunca propaga exceção (Confiabilidade) |
| `test_gerenciar_checklist.py` | Cache: checklist existente não chama a IA (Desempenho) |
| `test_in_memory_repo.py` | Contrato do repositório (LSP) e isolamento por usuário (Segurança) |
| `test_entidades.py` | Invariantes de domínio (`Questao`, `Materia`, `Estudo`) |

---

## API

Especificação formal em [`docs/openapi.yaml`](docs/openapi.yaml) (**OpenAPI
3.0**, validada contra as rotas reais — 11 paths = 11 rotas). Para navegar,
abra o arquivo no [Swagger Editor](https://editor.swagger.io/) ou importe no
Postman/Insomnia.

Decisão de estilo (REST vs GraphQL/gRPC) justificada no [ADR-005](adrs/ADR-005.md).
Convenções: erros uniformes `{"erro", "codigo"}` (400/401/404/502/500),
paginação por `limite`/`offset`, versionamento por header `X-API-Version`.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | UI de demonstração (HTML). |
| `GET` | `/api` | Índice da API (JSON). |
| `GET` | `/api/health` | Verificação de saúde + modo atual. |
| `POST` | `/api/sessao` | Cria sessão (troca idToken por cookie). |
| `DELETE` | `/api/sessao` | Logout. |
| `POST` | `/api/estudos` | Cria estudo via upload de PDF. |
| `GET` | `/api/estudos` | Lista estudos (paginado). |
| `GET` | `/api/estudos/{id}` | Detalha um estudo (texto + conteúdos). |
| `PATCH` | `/api/estudos/{id}` | Renomeia. |
| `DELETE` | `/api/estudos/{id}` | Remove. |
| `POST` | `/api/estudos/{id}/conteudo` | Gera/amplia conteúdo via IA. |
| `GET`/`PUT` | `/api/estudos/{id}/checklist` | Obtém (gera na 1ª vez) / salva a checklist. |
| `PUT` | `/api/estudos/{id}/materia` | Vincula/desvincula de matéria. |
| `GET`/`POST` | `/api/materias` | Lista / cria matérias. |
| `DELETE` | `/api/materias/{id}` | Remove matéria (estudos são só desvinculados). |
| `GET` | `/api/materias/{id}/estudos` | Estudos de uma matéria. |

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/introducao.md`](docs/introducao.md) | Apresentação, justificativa, objetivos, público-alvo |
| [`docs/quality.md`](docs/quality.md) | Atributos de qualidade (ISO/IEC 25010) com métricas verificáveis |
| [`docs/solid.md`](docs/solid.md) | Os 5 princípios SOLID com trechos reais e benefícios |
| [`docs/padroes-gof.md`](docs/padroes-gof.md) | Strategy, Factory Method e Adapter: problema → solução → verificação |
| [`docs/estrutura-do-projeto.md`](docs/estrutura-do-projeto.md) | Guia detalhado das camadas e pastas |
| [`docs/openapi.yaml`](docs/openapi.yaml) | Contrato formal da API REST |
| [`adrs/`](adrs/) | 6 ADRs; o [ADR-004](adrs/ADR-004.md) documenta decisão **revisada** (Gemini 1.5 → 2.5) |
| [`diagrams/`](diagrams/) | C4 (containers/componentes), classes GoF e sequência — Mermaid, renderizam no GitHub |

---

## Solução de problemas

| Sintoma | Causa e solução |
|---|---|
| `localhost:5000` não responde | O servidor não está rodando. Suba-o e **mantenha o terminal aberto**. |
| Alterações no código "não aparecem" | Um processo antigo pode estar segurando a porta (no Windows, dois Flask sobem na 5000 sem erro e o **antigo** continua respondendo). Verifique com `Get-NetTCPConnection -LocalPort 5000 -State Listen`, encerre os processos `python` residuais e suba **um único** servidor. |
| `python`/`flask` não reconhecido | Python fora do PATH — use o caminho completo do executável ou reinstale marcando "Add Python to PATH". |
| Upload retorna 400 "texto selecionável" | O PDF é escaneado (só imagens). Envie um PDF com texto real. |
| Dados sumiram após reiniciar | Comportamento esperado do modo demo (memória volátil — [ADR-006](adrs/ADR-006.md)). Para persistir, use o modo real. |
| Conteúdo vem marcado `[DEMO]` | Você está no modo demo (IA fake). Configure `GEMINI_API_KEY` + `FIREBASE_CREDENTIALS` para gerar conteúdo real. |

---

## Equipe

| Integrante | RA |
|---|---|
| Anderson Lucas Gondin | 24787293 |
| Felipe Nonato Leoneli | 24021973 |
| Filipe Ribeiro Simões | 24007657 |
| Lucas Presendo Canhete | 23025535 |
| Rafael Roveri Pires | 24007131 |
