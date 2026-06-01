"""Strategy concreta: geração de Quiz (questões de múltipla escolha)."""
import json

from src.application.strategies.conteudo_strategy import ConteudoStrategy
from src.domain.ports.gerador_ia import IGeradorIA


_INSTRUCAO_SISTEMA = (
    "Você é um professor especialista em elaborar avaliações de múltipla escolha. "
    "Gere as questões em português do Brasil, baseadas ESTRITAMENTE no texto fornecido — "
    "nunca invente fatos que não estejam no texto.\n"
    "Regras de qualidade:\n"
    "1. Cada questão deve testar COMPREENSÃO e raciocínio, não apenas memorização literal.\n"
    "2. Exatamente UMA alternativa correta; as outras 3 devem ser plausíveis.\n"
    "3. Varie a posição da alternativa correta entre as questões.\n"
    "4. Não use 'todas as anteriores' nem 'nenhuma das anteriores'.\n"
    "5. Enunciados claros e autossuficientes.\n"
    "6. Aborde partes diferentes do texto.\n"
    "7. Sempre exatamente 4 alternativas por questão.\n"
    "8. 'correta' é o índice (0 a 3) da alternativa certa.\n"
    "9. 'explicacao' é 1 ou 2 frases justificando a resposta correta."
)

_QUESTAO_VAZIA = (
    '[{"pergunta": "Erro ao gerar questões.", '
    '"alternativas": ["-", "-", "-", "-"], "correta": 0, "explicacao": ""}]'
)


class QuizStrategy(ConteudoStrategy):
    """
    Gera questões de múltipla escolha em JSON estruturado.

    Retorna uma string JSON com a lista de questões validadas,
    pronta para ser parseada pelo frontend do quiz interativo.
    """

    def __init__(self, gerador: IGeradorIA) -> None:
        super().__init__(gerador)

    def gerar(self, texto: str, historico: str = "") -> str:
        prompt = (
            _INSTRUCAO_SISTEMA + "\n\n"
            + self._aviso_historico(historico)
            + f"Crie 5 questões de múltipla escolha sobre o texto a seguir.\n\n"
            f"Texto:\n{texto}"
        )
        resultado_bruto = self._gerador.gerar(prompt)
        return self._validar_e_limpar(resultado_bruto)

    # ── helpers privados ─────────────────────────────────────────────────────

    def _validar_e_limpar(self, resultado_bruto: str) -> str:
        """Garante que o JSON retornado é válido antes de persistir."""
        texto_limpo = resultado_bruto.replace("```json", "").replace("```", "").strip()
        try:
            dados = json.loads(texto_limpo)
            questoes_validas = [
                self._normalizar_questao(q)
                for q in dados
                if self._questao_valida(q)
            ]
            if not questoes_validas:
                raise ValueError("Nenhuma questão válida retornada pelo modelo.")
            return json.dumps(questoes_validas, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            return _QUESTAO_VAZIA

    @staticmethod
    def _questao_valida(q: dict) -> bool:
        alternativas = q.get("alternativas") or []
        return bool(q.get("pergunta")) and len(alternativas) >= 2

    @staticmethod
    def _normalizar_questao(q: dict) -> dict:
        alternativas = q.get("alternativas", [])
        correta = q.get("correta", 0)
        if not isinstance(correta, int) or not (0 <= correta < len(alternativas)):
            correta = 0
        return {
            "pergunta":     q.get("pergunta", ""),
            "alternativas": alternativas,
            "correta":      correta,
            "explicacao":   q.get("explicacao", ""),
        }
