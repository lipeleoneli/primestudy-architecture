"""
Configuração da aplicação a partir de variáveis de ambiente.

Decide entre dois modos de operação:
  - REAL:  usa Firestore + Gemini (exige credenciais).
  - DEMO:  usa repositório em memória + IA fake (sobe sem credenciais).

O modo é escolhido automaticamente: se as credenciais necessárias não
estão presentes, cai para DEMO. Pode ser forçado via PRIMESTUDY_MODE.

Clean Code: uma única fonte de verdade para configuração; nenhuma outra
camada lê os.environ diretamente.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Configuração imutável resolvida no boot da aplicação."""

    modo: str                       # 'real' | 'demo'
    secret_key: str                 # chave de assinatura da sessão Flask
    gemini_api_key: str             # chave da API Gemini (vazia em demo)
    gemini_model: str               # modelo de IA a usar
    firebase_credentials: str       # caminho do service-account JSON (vazio em demo)
    demo_uid: str                   # uid fixo usado quando o login é dispensado

    @property
    def eh_demo(self) -> bool:
        return self.modo == "demo"

    @classmethod
    def carregar(cls) -> "AppConfig":
        """Lê o ambiente e resolve o modo de operação."""
        modo_forcado = os.environ.get("PRIMESTUDY_MODE", "").strip().lower()
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        firebase_cred = os.environ.get("FIREBASE_CREDENTIALS", "").strip()

        modo = modo_forcado or cls._inferir_modo(gemini_key, firebase_cred)

        return cls(
            modo=modo,
            secret_key=os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao"),
            gemini_api_key=gemini_key,
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            firebase_credentials=firebase_cred,
            demo_uid=os.environ.get("DEMO_UID", "demo-user"),
        )

    @staticmethod
    def _inferir_modo(gemini_key: str, firebase_cred: str) -> str:
        """Sem ambas as credenciais reais, opera em modo demo."""
        if gemini_key and firebase_cred:
            return "real"
        return "demo"
