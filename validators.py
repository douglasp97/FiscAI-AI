"""Validação estrutural e dos campos obrigatórios da NF-e."""

from __future__ import annotations

from typing import Any, Dict, List

from lxml import etree


def validate_xml_structure(xml_bytes: bytes) -> List[Dict[str, Any]]:
    """Validação básica da estrutura do XML. Sem XSD, apenas checagem de campos críticos."""
    issues: List[Dict[str, Any]] = []

    try:
        root = etree.fromstring(xml_bytes)
    except Exception as exc:
        return [{
            'rule_id': 'XML_INVÁLIDO',
            'severity': 'ALTA',
            'description': f'XML inválido: {exc}',
        }]

    # Bloco principal
    if root.tag is None:
        issues.append({
            'rule_id': 'XML_SEM_TAG',
            'severity': 'ALTA',
            'description': 'XML sem tag principal identificável.',
        })

    # Campos estruturais essenciais
    required_paths = ['infNFe', 'ide', 'emit', 'dest', 'det']
    for name in required_paths:
        if root.xpath(f'.//*[local-name()="{name}"]'):
            continue
        issues.append({
            'rule_id': f'{name.upper()}_AUSENTE',
            'severity': 'ALTA',
            'description': f'Bloco {name} não foi encontrado no XML.',
        })

    return issues


def validate_required_fields(invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    if not invoice.get('chave'):
        issues.append({
            'rule_id': 'CHAVE_AUSENTE',
            'severity': 'ALTA',
            'description': 'Chave da NF-e ausente.',
        })
    if not invoice.get('numero'):
        issues.append({
            'rule_id': 'NUMERO_AUSENTE',
            'severity': 'MÉDIA',
            'description': 'Número da NF-e ausente.',
        })
    if not invoice.get('emit_cnpj'):
        issues.append({
            'rule_id': 'EMITENTE_CNPJ_AUSENTE',
            'severity': 'ALTA',
            'description': 'CNPJ/CPF do emitente ausente.',
        })

    if not items:
        issues.append({
            'rule_id': 'ITEMS_AUSENTES',
            'severity': 'ALTA',
            'description': 'Nenhum item foi encontrado no XML.',
        })
        return issues

    for idx, item in enumerate(items, start=1):
        if not item.get('NCM'):
            issues.append({
                'rule_id': 'NCM_AUSENTE',
                'severity': 'MÉDIA',
                'description': f'Item {idx} sem NCM informado.',
            })
        if not item.get('CFOP'):
            issues.append({
                'rule_id': 'CFOP_AUSENTE',
                'severity': 'MÉDIA',
                'description': f'Item {idx} sem CFOP informado.',
            })
        if not item.get('vProd'):
            issues.append({
                'rule_id': 'VALOR_PRODUTO_AUSENTE',
                'severity': 'BAIXA',
                'description': f'Item {idx} sem valor do produto.',
            })

    return issues
