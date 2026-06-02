"""
Adapter de IA fake: FakeGeradorIA.

Implementa IGeradorIA sem chamar nenhuma API externa. No modo DEMO
permite exercitar todo o fluxo (gerar resumo, quiz, flashcard…) sem
GEMINI_API_KEY e sem custo nem latência.

A resposta é escolhida por uma frase distintiva presente no prompt de
cada Strategy (da mais específica para a mais genérica), devolvendo o
formato que aquela Strategy espera validar/renderizar.
"""
import json

from src.domain.ports.gerador_ia import IGeradorIA

_QUIZ_DEMO = json.dumps([{
    "pergunta": "[DEMO] Qual o objetivo deste material?",
    "alternativas": [
        "Demonstrar o fluxo do PrimeStudy",
        "Alternativa incorreta A",
        "Alternativa incorreta B",
        "Alternativa incorreta C",
    ],
    "correta": 0,
    "explicacao": "Resposta gerada em modo demonstração.",
}], ensure_ascii=False)


class FakeGeradorIA(IGeradorIA):
    """Gerador determinístico para desenvolvimento e demonstração."""

    def gerar(self, prompt: str) -> str:
        p = prompt.lower()

        if "múltipla escolha" in p:
            return _QUIZ_DEMO
        if "flashcards de estudo" in p:
            return "P: O que é o PrimeStudy?\nR: Plataforma de estudo a partir de PDFs.\n"
        if "mapa mental" in p:
            return "Tema principal (demo)\n  Subtema 1\n    Detalhe 1\n  Subtema 2"
        if "principais tópicos de estudo" in p:   # ChecklistTopicosStrategy (linhas puras)
            return "Introdução ao tema\nConceitos fundamentais\nAplicações práticas"
        if "tópicos principais" in p:              # TopicosStrategy (lista HTML)
            return "<ul><li>Tópico de demonstração 1</li><li>Tópico de demonstração 2</li></ul>"
        if "resumo" in p:                          # Resumo / ResumoMenor (HTML)
            return "<p>[DEMO] Resumo gerado em modo demonstração do material enviado.</p>"
        return "<p>[DEMO] Conteúdo gerado em modo demonstração.</p>"
