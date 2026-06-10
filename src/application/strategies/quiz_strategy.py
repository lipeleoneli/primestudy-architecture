"""Strategy concreta: geração de Quiz (questões de múltipla escolha)."""
import json
from dataclasses import asdict
from typing import Optional

from src.application.strategies.conteudo_strategy import ConteudoStrategy
from src.domain.entities.questao import Questao


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

    A resposta bruta do modelo é validada contra a entidade de domínio
    Questao (invariantes: pergunta não vazia, exatamente 4 alternativas,
    índice da correta entre 0 e 3). Questões que violam a invariante são
    descartadas — só JSON garantidamente válido chega ao frontend.
    """

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
            questoes = [self._montar_questao(q) for q in dados]
            questoes_validas = [asdict(q) for q in questoes if q is not None]
            if not questoes_validas:
                raise ValueError("Nenhuma questão válida retornada pelo modelo.")
            return json.dumps(questoes_validas, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError, ValueError):
            return _QUESTAO_VAZIA

    @staticmethod
    def _montar_questao(bruto: dict) -> Optional[Questao]:
        """Converte o dict do modelo na entidade Questao; None se inválida."""
        if not isinstance(bruto, dict):
            return None
        alternativas = [str(a) for a in (bruto.get("alternativas") or [])]
        correta = bruto.get("correta", 0)
        if not isinstance(correta, int):
            correta = 0
        try:
            return Questao(
                pergunta=str(bruto.get("pergunta") or ""),
                alternativas=alternativas,
                correta=correta,
                explicacao=str(bruto.get("explicacao") or ""),
            )
        except ValueError:
            # invariante de domínio violada (ex.: nº de alternativas != 4)
            return None
