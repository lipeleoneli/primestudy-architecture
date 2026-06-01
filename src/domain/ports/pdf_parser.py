"""
Port (interface): IPDFParser.

Abstrai qualquer biblioteca de extração de texto de PDF
(pdfplumber, PyMuPDF, Tesseract OCR…).

SOLID — DIP: o caso de uso ProcessarPDF depende desta interface,
não da biblioteca pdfplumber diretamente.
"""
from abc import ABC, abstractmethod


class IPDFParser(ABC):
    """Contrato para extração de texto de arquivos PDF."""

    @abstractmethod
    def extrair_texto(self, conteudo_bytes: bytes) -> str:
        """
        Extrai todo o texto legível de um PDF.

        Args:
            conteudo_bytes: Conteúdo bruto do arquivo PDF.

        Returns:
            Texto extraído concatenado de todas as páginas.

        Raises:
            ValueError: Se o PDF não contiver texto selecionável.
            RuntimeError: Se ocorrer erro durante o processamento.
        """
