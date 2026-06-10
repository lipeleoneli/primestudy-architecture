"""
Adapter entre a SDK google.genai e o contrato IGeradorIA.

A SDK expõe client.models.generate_content() com objeto de resposta próprio;
este adapter converte isso para gerar(prompt) -> str.
A SDK é importada dentro do __init__ para não quebrar o modo demo.
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
