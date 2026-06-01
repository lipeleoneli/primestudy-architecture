"""
Caso de uso: ProcessarPDF.

SOLID — SRP: esta classe faz uma única coisa — receber o bytes de um PDF,
             extrair o texto e salvar o novo estudo no repositório.
SOLID — DIP: depende de IPDFParser e IEstudoRepository (abstrações),
             não de pdfplumber nem Firestore.

Clean Code: nome do método diz o que ele faz; sem comentário desnecessário;
            cada passo do fluxo cabe em uma linha descritiva.
"""
from dataclasses import dataclass
from typing import Optional

from src.domain.entities.estudo import Estudo
from src.domain.ports.pdf_parser import IPDFParser
from src.domain.ports.estudo_repository import IEstudoRepository


@dataclass
class ProcessarPDFInput:
    """Dados de entrada para o caso de uso ProcessarPDF."""
    uid: str
    conteudo_bytes: bytes
    nome_arquivo: str
    materia_id: Optional[str] = None


@dataclass
class ProcessarPDFOutput:
    """Resultado do caso de uso ProcessarPDF."""
    estudo_id: str
    redirect_url: str


class ProcessarPDFUseCase:
    """
    Processa o upload de um PDF: extrai o texto e persiste o estudo.

    Não conhece Flask, Firestore nem pdfplumber —
    apenas as interfaces que eles implementam.
    """

    def __init__(
        self,
        parser: IPDFParser,
        repositorio: IEstudoRepository,
    ) -> None:
        self._parser = parser
        self._repositorio = repositorio

    def executar(self, dados: ProcessarPDFInput) -> ProcessarPDFOutput:
        texto = self._extrair_texto_ou_falhar(dados.conteudo_bytes)
        estudo = self._montar_estudo(dados, texto)
        estudo_id = self._repositorio.salvar_estudo(dados.uid, estudo)
        return ProcessarPDFOutput(
            estudo_id=estudo_id,
            redirect_url=f"/estudo/{estudo_id}",
        )

    # ── helpers privados ─────────────────────────────────────────────────────

    def _extrair_texto_ou_falhar(self, conteudo_bytes: bytes) -> str:
        texto = self._parser.extrair_texto(conteudo_bytes)
        if not texto.strip():
            raise ValueError(
                "Este PDF contém imagens escaneadas e não possui texto legível. "
                "Por favor, envie um PDF com texto selecionável."
            )
        return texto

    @staticmethod
    def _montar_estudo(dados: ProcessarPDFInput, texto: str) -> Estudo:
        return Estudo(
            id="",                    # preenchido pelo repositório após persistir
            nome=dados.nome_arquivo,
            texto=texto,
            materia_id=dados.materia_id,
        )
