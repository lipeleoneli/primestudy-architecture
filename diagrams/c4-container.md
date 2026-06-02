# C4 — Containers e Componentes

> Reflete o código real: monolito modular (ADR-001) em Clean Architecture
> (ADR-002), API JSON Flask sobre Firestore (ADR-003) e Gemini 2.5 Flash (ADR-004).

## Nível 2 — Containers

A aplicação é **uma** unidade implantável (o processo Flask). As camadas internas
são componentes desse mesmo container, não serviços separados.

```mermaid
C4Container
    title PrimeStudy — Diagrama de Containers

    Person(usuario, "Estudante", "Consome a API via cliente HTTP / frontend web")

    System_Boundary(primestudy, "PrimeStudy") {
        Container(api, "PrimeStudy API", "Python, Flask", "Monolito modular em Clean Architecture. Expõe endpoints REST sob /api e orquestra os casos de uso.")
    }

    System_Ext(firestore, "Google Firestore", "Banco NoSQL gerenciado — dados isolados por usuário")
    System_Ext(gemini, "Google Gemini 2.5 Flash", "LLM para geração de conteúdo de estudo")

    Rel(usuario, api, "REST / JSON, cookie de sessão", "HTTPS")
    Rel(api, firestore, "lê/escreve usuarios/{uid}/...", "firebase-admin")
    Rel(api, gemini, "envia prompt, recebe texto", "google-genai")
```

## Nível 3 — Componentes (dentro do container API)

```mermaid
C4Component
    title PrimeStudy API — Componentes (camadas)

    Container_Boundary(api, "PrimeStudy API") {
        Component(interface, "interface/", "Flask blueprints, guard, errors, serializers", "Traduz HTTP ⇄ casos de uso. create_app() é o composition root.")
        Component(application, "application/", "Use cases, Strategies, Factory", "Regra de orquestração. GoF Strategy + Factory.")
        Component(domain, "domain/", "Entities + Ports", "Núcleo puro: Estudo, Materia, Questao e interfaces (IEstudoRepository, IGeradorIA, IPDFParser).")
        Component(infrastructure, "infrastructure/", "Adapters", "Implementa os ports: Firestore, Gemini, pdfplumber (GoF Adapter). Impls de demo: in-memory, fake IA.")
    }

    System_Ext(firestore, "Firestore", "NoSQL")
    System_Ext(gemini, "Gemini 2.5 Flash", "LLM")

    Rel(interface, application, "invoca", "chamada Python")
    Rel(application, domain, "usa entidades e ports")
    Rel(infrastructure, domain, "implementa os ports (DIP)")
    Rel(application, infrastructure, "depende de abstrações; impl injetada no boot")
    Rel(infrastructure, firestore, "firebase-admin")
    Rel(infrastructure, gemini, "google-genai")
```
