"""
Verificação de identidade via Firebase Authentication (ADR-003).

Inicializa o app firebase_admin uma única vez e oferece:
  - verify_id_token: valida o JWT vindo do frontend e devolve o uid.
  - firestore_client: o cliente Firestore para o repositório real.

Segurança: o backend NUNCA confia em uid enviado pelo cliente — só no uid
extraído de um idToken verificado pelo Google.
"""
import firebase_admin
from firebase_admin import auth, credentials, firestore


class FirebaseAuth:
    """Encapsula a inicialização e a verificação de tokens do Firebase."""

    def __init__(self, caminho_credenciais: str) -> None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(caminho_credenciais)
            firebase_admin.initialize_app(cred)
        self._db = firestore.client()

    def verificar_id_token(self, id_token: str) -> str:
        """Valida o idToken e retorna o uid. Lança ValueError se inválido."""
        try:
            decodificado = auth.verify_id_token(id_token)
        except Exception as exc:
            raise ValueError("idToken inválido ou expirado.") from exc

        uid = decodificado.get("uid")
        if not uid:
            raise ValueError("Token sem uid.")
        return uid

    def firestore_client(self):
        return self._db
