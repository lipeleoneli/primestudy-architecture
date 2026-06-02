"""
Testes da camada de interface (HTTP) em modo DEMO.

Sobem a aplicação real via create_app() com config forçada em demo —
sem Firebase, sem Gemini, sem rede. Verificam o contrato HTTP: status
codes, formato de erro, paginação e o fluxo de geração de conteúdo.
"""
import io

import pytest

from src.domain.entities.estudo import Estudo
from src.infrastructure.config import AppConfig
from src.interface.app import create_app


@pytest.fixture
def app():
    config = AppConfig(
        modo="demo",
        secret_key="teste",
        gemini_api_key="",
        gemini_model="fake",
        firebase_credentials="",
        demo_uid="demo-user",
    )
    return create_app(config)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def estudo_id(app):
    """Semeia um estudo direto no repositório e devolve seu id."""
    repo = app.extensions["primestudy"].repositorio
    return repo.salvar_estudo("demo-user", Estudo(id="", nome="Aula 1", texto="texto"))


# ── Saúde e versionamento ─────────────────────────────────────────────────────

def test_health_reporta_modo_demo(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["modo"] == "demo"

def test_resposta_carimba_versao_da_api(client):
    resp = client.get("/api/health")
    assert resp.headers["X-API-Version"] == "v1"


# ── Matérias ──────────────────────────────────────────────────────────────────

def test_cria_e_lista_materia(client):
    criar = client.post("/api/materias", json={"nome": "Cálculo I"})
    assert criar.status_code == 201
    materia_id = criar.get_json()["materia_id"]

    listar = client.get("/api/materias").get_json()
    assert any(m["id"] == materia_id for m in listar["materias"])

def test_materia_com_nome_vazio_retorna_400(client):
    resp = client.post("/api/materias", json={"nome": ""})
    assert resp.status_code == 400
    assert resp.get_json()["codigo"] == "REQUISICAO_INVALIDA"


# ── Estudos e conteúdo ────────────────────────────────────────────────────────

@pytest.mark.parametrize("tipo", ["resumo", "topicos", "flashcard", "questoes", "mapa"])
def test_gera_cada_tipo_de_conteudo(client, estudo_id, tipo):
    resp = client.post(f"/api/estudos/{estudo_id}/conteudo", json={"tipo": tipo})
    assert resp.status_code == 200
    assert resp.get_json()["conteudo"]

def test_gerar_conteudo_sem_tipo_retorna_400(client, estudo_id):
    resp = client.post(f"/api/estudos/{estudo_id}/conteudo", json={})
    assert resp.status_code == 400

def test_obter_estudo_inexistente_retorna_404(client):
    resp = client.get("/api/estudos/nao-existe")
    assert resp.status_code == 404

def test_renomeia_estudo(client, estudo_id):
    resp = client.patch(f"/api/estudos/{estudo_id}", json={"nome": "Novo Nome"})
    assert resp.status_code == 200
    assert resp.get_json()["nome"] == "Novo Nome"

def test_checklist_gera_e_salva(client, estudo_id):
    obtido = client.get(f"/api/estudos/{estudo_id}/checklist")
    assert obtido.status_code == 200
    assert len(obtido.get_json()["itens"]) > 0

    salvar = client.put(
        f"/api/estudos/{estudo_id}/checklist",
        json={"itens": [{"texto": "T1", "feito": True}]},
    )
    assert salvar.status_code == 204


# ── Upload e paginação ────────────────────────────────────────────────────────

def test_upload_sem_arquivo_retorna_400(client):
    assert client.post("/api/estudos").status_code == 400

def test_upload_pdf_invalido_retorna_502(client):
    resp = client.post(
        "/api/estudos",
        data={"arquivo": (io.BytesIO(b"isto nao e pdf"), "x.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 502
    assert resp.get_json()["codigo"] == "FALHA_DEPENDENCIA"

def test_paginacao_respeita_limite(client, app):
    repo = app.extensions["primestudy"].repositorio
    for i in range(5):
        repo.salvar_estudo("demo-user", Estudo(id="", nome=f"E{i}", texto="t"))
    resp = client.get("/api/estudos?limite=2&offset=0").get_json()
    assert resp["limite"] == 2
    assert resp["total_retornado"] == 2
