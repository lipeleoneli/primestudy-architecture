"""
Testes unitários — entidades de domínio.

As entidades são Python puro: estes testes provam as invariantes de domínio
(estado inválido é impossível de construir) sem nenhuma dependência externa.
"""
import pytest

from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.entities.materia import Materia
from src.domain.entities.questao import Questao


# ── Questao: invariantes no __post_init__ ────────────────────────────────────

class TestQuestao:

    def test_questao_valida_e_construida(self):
        q = Questao(
            pergunta="Qual o tema?",
            alternativas=["A", "B", "C", "D"],
            correta=2,
            explicacao="Porque sim.",
        )
        assert q.alternativa_correta == "C"

    def test_rejeita_pergunta_vazia(self):
        with pytest.raises(ValueError, match="pergunta"):
            Questao(pergunta="  ", alternativas=["A", "B", "C", "D"], correta=0, explicacao="")

    @pytest.mark.parametrize("alternativas", [[], ["A"], ["A", "B"], ["A", "B", "C", "D", "E"]])
    def test_rejeita_numero_errado_de_alternativas(self, alternativas):
        with pytest.raises(ValueError, match="4 alternativas"):
            Questao(pergunta="P?", alternativas=alternativas, correta=0, explicacao="")

    @pytest.mark.parametrize("correta", [-1, 4, 99])
    def test_rejeita_indice_da_correta_fora_do_intervalo(self, correta):
        with pytest.raises(ValueError, match="entre 0 e 3"):
            Questao(pergunta="P?", alternativas=["A", "B", "C", "D"], correta=correta, explicacao="")


# ── Materia: validação de nome ───────────────────────────────────────────────

class TestMateria:

    def test_materia_valida(self):
        m = Materia(id="m1", nome="Cálculo I")
        assert m.cor == "c-blue"
        assert m.total_estudos == 0

    @pytest.mark.parametrize("nome", ["", "   "])
    def test_rejeita_nome_vazio(self, nome):
        with pytest.raises(ValueError, match="vazio"):
            Materia(id="m1", nome=nome)


# ── Estudo: comportamento do agregado ────────────────────────────────────────

class TestEstudo:

    def test_tem_conteudo_e_conteudo_do_tipo(self):
        estudo = Estudo(id="e1", nome="Aula", texto="t")
        assert not estudo.tem_conteudo("resumo")
        assert estudo.conteudo_do_tipo("resumo") == ""

        estudo.atualizar_conteudo("resumo", "<p>resumo</p>")
        assert estudo.tem_conteudo("resumo")
        assert estudo.conteudo_do_tipo("resumo") == "<p>resumo</p>"

    def test_conteudo_vazio_nao_conta_como_gerado(self):
        estudo = Estudo(id="e1", nome="Aula", texto="t", conteudo={"resumo": ""})
        assert not estudo.tem_conteudo("resumo")

    def test_checklist_inicia_vazia(self):
        estudo = Estudo(id="e1", nome="Aula", texto="t")
        assert estudo.checklist == []
        estudo.checklist.append(ItemChecklist(texto="Tópico 1"))
        assert estudo.checklist[0].feito is False
