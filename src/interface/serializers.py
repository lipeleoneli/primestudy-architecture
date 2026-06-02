"""
Serialização entidade de domínio → dict JSON.

Mantém a conversão para a borda HTTP fora das entidades — o domínio
não conhece o formato de transporte (separação de responsabilidades).
"""
from src.domain.entities.estudo import Estudo, ItemChecklist
from src.domain.entities.materia import Materia


def estudo_para_json(estudo: Estudo, incluir_texto: bool = False) -> dict:
    dados = {
        "id": estudo.id,
        "nome": estudo.nome,
        "materia_id": estudo.materia_id,
        "criado_em": estudo.criado_em.isoformat() if estudo.criado_em else None,
        "tipos_gerados": sorted(estudo.conteudo.keys()),
        "checklist": [item_checklist_para_json(i) for i in estudo.checklist],
    }
    if incluir_texto:
        dados["texto"] = estudo.texto
        dados["conteudo"] = estudo.conteudo
    return dados


def item_checklist_para_json(item: ItemChecklist) -> dict:
    return {"texto": item.texto, "feito": item.feito}


def materia_para_json(materia: Materia) -> dict:
    return {
        "id": materia.id,
        "nome": materia.nome,
        "cor": materia.cor,
        "total_estudos": materia.total_estudos,
    }
