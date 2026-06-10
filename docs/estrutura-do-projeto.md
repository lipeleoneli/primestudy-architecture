# Estrutura do Projeto

Este projeto segue **Clean Architecture** (Robert C. Martin) com influência
**Hexagonal** (ports & adapters). A regra de dependência aponta sempre para
dentro: `interface → application → domain` e `infrastructure → domain`.
O núcleo (`domain`) não conhece Flask, Firestore nem Gemini.

Ver `adrs/ADR-001.md` (monolito modular) e `adrs/ADR-002.md` (Clean Architecture).

## Mapa de pastas

```
primestudy-architecture/
│
├── src/
│   ├── __init__.py
│   │
│   ├── domain/                      # Núcleo — Python puro, sem dependências externas
│   │   ├── entities/                # Entidades de domínio
│   │   │   ├── estudo.py            # Estudo + ItemChecklist
│   │   │   ├── materia.py           # Materia (valida nome no __post_init__)
│   │   │   └── questao.py           # Questao (invariantes: 4 alternativas, usada pela QuizStrategy)
│   │   ├── exceptions.py            # RecursoNaoEncontradoError (→ 404 na borda HTTP)
│   │   └── ports/                   # Interfaces (contratos) — abstrações ABC
│   │       ├── estudo_repository.py # IEstudoRepository (contrato de erro especificado — LSP)
│   │       ├── gerador_ia.py        # IGeradorIA  — gerar(prompt) -> str
│   │       └── pdf_parser.py        # IPDFParser  — extrair_texto(bytes) -> str
│   │
│   ├── application/                 # Casos de uso — orquestra domain (não sabe de HTTP)
│   │   ├── use_cases/
│   │   │   ├── gerar_conteudo.py        # GerarConteudoUseCase
│   │   │   ├── processar_pdf.py         # ProcessarPDFUseCase
│   │   │   ├── gerenciar_materias.py    # GerenciarMateriasUseCase
│   │   │   └── gerenciar_checklist.py   # GerenciarChecklistUseCase
│   │   ├── strategies/              # GoF Strategy — uma classe por tipo de conteúdo
│   │   │   ├── conteudo_strategy.py # ConteudoStrategy (base abstrata)
│   │   │   ├── resumo_strategy.py   # ResumoStrategy, ResumoMenorStrategy
│   │   │   ├── topicos_strategy.py  # TopicosStrategy, ChecklistTopicosStrategy
│   │   │   ├── flashcard_strategy.py
│   │   │   ├── quiz_strategy.py     # QuizStrategy (valida JSON)
│   │   │   └── mapa_strategy.py     # MapaMentalStrategy
│   │   └── factories/
│   │       └── conteudo_factory.py  # GoF Factory Method — cria a Strategy por tipo
│   │
│   ├── infrastructure/              # Implementações concretas dos ports (adapters)
│   │   ├── config.py                # AppConfig — resolve modo demo/real por env
│   │   ├── firestore_estudo_repo.py # Adapter Firestore (Repository/Fowler)
│   │   ├── gemini_adapter.py        # GoF Adapter — google-genai -> IGeradorIA
│   │   ├── pdf_parser.py            # GoF Adapter — pdfplumber -> IPDFParser
│   │   ├── in_memory_estudo_repo.py # Repositório em memória (modo demo)
│   │   ├── fake_gerador_ia.py       # IA fake determinística (modo demo)
│   │   └── firebase_auth.py         # Verificação de idToken (Firebase Auth)
│   │
│   └── interface/                   # Entrada do sistema — Flask e HTTP
│       ├── app.py                   # create_app(): composition root + blueprints
│       ├── auth_routes.py           # /api/sessao (login/logout)
│       ├── estudo_routes.py         # /api/estudos/... (CRUD, conteúdo, checklist)
│       ├── materia_routes.py        # /api/materias/...
│       ├── auth_guard.py            # @requer_login (sessão; bypass no demo)
│       ├── errors.py                # Handlers de erro HTTP padronizados
│       └── serializers.py           # Entidade -> JSON
│
├── adrs/                            # Decisões arquiteturais (ADR-001 a ADR-006)
├── diagrams/                        # Diagramas em Mermaid (C4, classes GoF, sequência)
├── docs/                            # openapi.yaml, quality.md, solid.md, padroes-gof.md, este arquivo
├── tests/                           # 77 testes: use cases, entidades, strategies,
│                                    #   contrato do repositório e camada HTTP
│
├── .gitignore
├── .env.example                     # Variáveis de ambiente necessárias
├── requirements.txt                 # Dependências Python
└── README.md
```

## Como rodar

Não há `run.py`: o ponto de entrada é a *application factory* `create_app()`.

```bash
flask --app src.interface.app:create_app run
```

Sem credenciais, sobe em **modo demo** (repositório em memória + IA fake).
Detalhes no `README.md`.

## Por que essa estrutura?

Cada camada tem responsabilidade única:

- `domain/` não sabe que existe Firestore, Gemini ou Flask.
- `application/` não sabe que existe HTTP.
- `infrastructure/` implementa os contratos definidos em `domain/ports/`.
- `interface/` apenas traduz HTTP em chamadas para `application/`.

Isso permite trocar o banco, a IA ou o framework sem reescrever a regra de
negócio. Exemplo real: a troca de modelo Gemini 1.5 → 2.5 (ADR-004) não tocou
nenhum caso de uso — só a configuração do adapter.
