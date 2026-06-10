"""
Testes unitários — QuizStrategy.

Provam a alegação de Confiabilidade do docs/quality.md: respostas
malformadas do modelo NUNCA propagam exceção — a Strategy degrada para
uma questão de erro válida. Também provam que a invariante da entidade
Questao (4 alternativas, pergunta não vazia) é aplicada na prática.
"""
import json

from src.application.strategies.quiz_strategy import QuizStrategy
from src.domain.ports.gerador_ia import IGeradorIA


class GeradorComResposta(IGeradorIA):
    """Fake que devolve uma resposta fixa configurável."""

    def __init__(self, resposta: str):
        self.resposta = resposta

    def gerar(self, prompt: str) -> str:
        return self.resposta


def _gerar_quiz(resposta_do_modelo: str) -> list[dict]:
    strategy = QuizStrategy(GeradorComResposta(resposta_do_modelo))
    return json.loads(strategy.gerar("texto do pdf"))


QUESTAO_OK = {
    "pergunta": "Qual o tema?",
    "alternativas": ["A", "B", "C", "D"],
    "correta": 1,
    "explicacao": "É B.",
}


def test_resposta_valida_passa_integra():
    questoes = _gerar_quiz(json.dumps([QUESTAO_OK]))
    assert questoes == [QUESTAO_OK]


def test_remove_cerca_de_codigo_markdown():
    """O modelo às vezes embrulha o JSON em ```json ... ``` — deve ser limpo."""
    questoes = _gerar_quiz("```json\n" + json.dumps([QUESTAO_OK]) + "\n```")
    assert questoes[0]["pergunta"] == "Qual o tema?"


def test_json_invalido_degrada_para_questao_de_erro():
    questoes = _gerar_quiz("isto não é json {{{")
    assert len(questoes) == 1
    assert "Erro" in questoes[0]["pergunta"]
    assert len(questoes[0]["alternativas"]) == 4


def test_questao_sem_4_alternativas_e_descartada():
    """Invariante da entidade Questao aplicada: != 4 alternativas é inválido."""
    invalida = dict(QUESTAO_OK, alternativas=["A", "B"])
    questoes = _gerar_quiz(json.dumps([invalida, QUESTAO_OK]))
    assert len(questoes) == 1
    assert questoes[0]["correta"] == 1


def test_correta_fora_do_intervalo_descarta_a_questao():
    """Melhor descartar do que marcar uma alternativa arbitrária como certa."""
    fora = dict(QUESTAO_OK, correta=9)
    questoes = _gerar_quiz(json.dumps([fora, QUESTAO_OK]))
    assert len(questoes) == 1
    assert questoes[0]["correta"] == 1


def test_lista_vazia_degrada_para_questao_de_erro():
    questoes = _gerar_quiz("[]")
    assert "Erro" in questoes[0]["pergunta"]
