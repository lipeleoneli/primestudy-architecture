"""
Adapter de IA real: GeminiAdapter.

PADRÃO GoF — Adapter (Estrutural).
PROBLEMA: a camada de aplicação fala a interface IGeradorIA.gerar(prompt)->str,
mas a SDK do Google (google.genai) expõe outra interface
(client.models.generate_content(...) com objetos de resposta próprios).
SOLUÇÃO: este adapter converte a interface da SDK para o contrato IGeradorIA.
Trocar o Gemini por OpenAI = escrever outro adapter; nada mais muda.

A SDK só é importada dentro do __init__ para que o modo DEMO não precise
da biblioteca/credencial configurada.
"""
from src.domain.ports.gerador_ia import IGeradorIA


class GeminiAdapter(IGeradorIA):
    """Adapta a SDK google.genai ao contrato IGeradorIA do domínio."""

    def __init__(self, api_key: str, modelo: str = "gemini-2.5-flash") -> None:
        if not api_key:
            raise ValueError("GeminiAdapter exige uma api_key não vazia.")
        from google import genai  # import tardio: só no modo real

        self._cliente = genai.Client(api_key=api_key)
        self._modelo = modelo

    def gerar(self, prompt: str) -> str:
        """Envia o prompt ao Gemini e devolve o texto, traduzindo falhas."""
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=prompt,
            )
        except Exception as exc:  # falha de rede/SDK → contrato do port
            raise RuntimeError(f"Falha ao chamar o Gemini: {exc}") from exc

        texto = getattr(resposta, "text", None)
        if not texto:
            raise RuntimeError("O Gemini retornou uma resposta vazia.")
        return texto
