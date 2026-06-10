"""
Composition root da aplicação PrimeStudy.

Único lugar que conhece implementações concretas. As dependências são
montadas conforme o modo (demo/real) e injetadas nos use cases.
"""
from dataclasses import dataclass
from typing import Optional

from flask import Flask

from src.application.factories.conteudo_factory import ConteudoFactory
from src.application.use_cases.gerar_conteudo import GerarConteudoUseCase
from src.application.use_cases.gerenciar_checklist import GerenciarChecklistUseCase
from src.application.use_cases.gerenciar_materias import GerenciarMateriasUseCase
from src.application.use_cases.processar_pdf import ProcessarPDFUseCase
from src.domain.ports.estudo_repository import IEstudoRepository
from src.domain.ports.gerador_ia import IGeradorIA
from src.domain.ports.pdf_parser import IPDFParser
from src.infrastructure.config import AppConfig
from src.interface.errors import registrar_tratadores_de_erro


@dataclass
class Dependencias:
    """Conjunto de objetos montados no boot e usados pelas rotas."""
    config: AppConfig
    repositorio: IEstudoRepository
    parser: IPDFParser
    gerador: IGeradorIA
    factory: ConteudoFactory
    processar_pdf: ProcessarPDFUseCase
    gerar_conteudo: GerarConteudoUseCase
    gerenciar_materias: GerenciarMateriasUseCase
    gerenciar_checklist: GerenciarChecklistUseCase
    firebase_auth: Optional[object] = None   # FirebaseAuth no modo real; None em demo


def _montar_dependencias(config: AppConfig) -> Dependencias:
    """Seleciona implementações conforme o modo e fia os use cases."""
    firebase_auth = None

    if config.eh_demo:
        from src.infrastructure.in_memory_estudo_repo import InMemoryEstudoRepo
        from src.infrastructure.fake_gerador_ia import FakeGeradorIA
        repositorio: IEstudoRepository = InMemoryEstudoRepo()
        gerador: IGeradorIA = FakeGeradorIA()
    else:
        from src.infrastructure.firebase_auth import FirebaseAuth
        from src.infrastructure.firestore_estudo_repo import FirestoreEstudoRepo
        from src.infrastructure.gemini_adapter import GeminiAdapter
        firebase_auth = FirebaseAuth(config.firebase_credentials)
        repositorio = FirestoreEstudoRepo(firebase_auth.firestore_client())
        gerador = GeminiAdapter(config.gemini_api_key, config.gemini_model)

    from src.infrastructure.pdf_parser import PDFParser
    parser: IPDFParser = PDFParser()
    factory = ConteudoFactory(gerador)

    return Dependencias(
        config=config,
        repositorio=repositorio,
        parser=parser,
        gerador=gerador,
        factory=factory,
        processar_pdf=ProcessarPDFUseCase(parser, repositorio),
        gerar_conteudo=GerarConteudoUseCase(repositorio, factory),
        gerenciar_materias=GerenciarMateriasUseCase(repositorio),
        gerenciar_checklist=GerenciarChecklistUseCase(repositorio, factory),
        firebase_auth=firebase_auth,
    )


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Cria e configura a aplicação Flask com todas as dependências montadas."""
    config = config or AppConfig.carregar()
    app = Flask(__name__)
    app.secret_key = config.secret_key

    app.extensions["primestudy"] = _montar_dependencias(config)

    # blueprints (import tardio evita ciclo com este módulo)
    from src.interface.auth_routes import bp as auth_bp
    from src.interface.estudo_routes import bp as estudo_bp
    from src.interface.materia_routes import bp as materia_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(estudo_bp)
    app.register_blueprint(materia_bp)

    registrar_tratadores_de_erro(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "modo": config.modo}

    @app.after_request
    def _carimbar_versao(resposta):
        # Versionamento por header (ver docs/openapi.yaml, seção 7)
        resposta.headers["X-API-Version"] = "v1"
        return resposta

    return app
