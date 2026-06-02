"""
Adapter de extração de PDF: PDFParser.

PADRÃO GoF — Adapter (Estrutural).
PROBLEMA: o use case ProcessarPDF fala IPDFParser.extrair_texto(bytes)->str,
mas a biblioteca pdfplumber abre arquivos/streams e itera páginas com sua
própria API. SOLUÇÃO: este adapter traduz pdfplumber para o contrato do port.
Trocar por PyMuPDF = outro adapter; o use case não muda.
"""
import io

from src.domain.ports.pdf_parser import IPDFParser


class PDFParser(IPDFParser):
    """Adapta a biblioteca pdfplumber ao contrato IPDFParser."""

    def extrair_texto(self, conteudo_bytes: bytes) -> str:
        import pdfplumber  # import tardio: mantém o domínio livre da dependência

        try:
            with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
                paginas = [pagina.extract_text() or "" for pagina in pdf.pages]
        except Exception as exc:
            raise RuntimeError(f"Falha ao processar o PDF: {exc}") from exc

        texto = "\n".join(paginas).strip()
        if not texto:
            raise ValueError(
                "Este PDF não contém texto selecionável (provavelmente é escaneado)."
            )
        return texto
