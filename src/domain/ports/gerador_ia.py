"""
Port (interface): IGeradorIA.

Abstrai qualquer provedor de IA generativa (Gemini, OpenAI, mock…).
O domínio nunca importa 'google.genai' diretamente.

SOLID — DIP: a camada de aplicação usa IGeradorIA; qual modelo é usado
em produção é decisão da infraestrutura, não do domínio.
SOLID — LSP: qualquer implementação pode substituir outra sem alterar
o comportamento esperado pelos casos de uso.
"""
from abc import ABC, abstractmethod


class IGeradorIA(ABC):
    """Contrato para geração de conteúdo via IA."""

    @abstractmethod
    def gerar(self, prompt: str) -> str:
        """
        Envia um prompt ao modelo e retorna a resposta em texto.

        Args:
            prompt: Instrução completa para o modelo.

        Returns:
            Texto gerado pelo modelo.

        Raises:
            RuntimeError: Se a chamada à API falhar.
        """
