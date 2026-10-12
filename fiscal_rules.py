"""Mecanismo de regras tributárias para NF-e e oportunidades de recuperação."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

# Tabela inicial de NCMs com alíquotas esperadas e regra de ST.
NCM_TABLE = {
    '87082900': {'icms': Decimal('12.00'), 'expect_st': False},
    '84099900': {'icms': Decimal('18.00'), 'expect_st': True},
    '39269099': {'icms': Decimal('18.00'), 'expect_st': False},
    '73079900': {'icms': Decimal('12.00'), 'expect_st': False},
    '85365000': {'icms': Decimal('18.00'), 'expect_st': False},
}

CFOP_INCOMPATIVEIS = {
    '5102': {'prefixes': ('8708', '8409')},
    '6102': {'prefixes': ('8708', '8409')},
}


def to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None


def apply_rules_to_invoice(invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for idx, item in enumerate(items, start=1):
        ncm = (item.get('NCM') or '').strip()
        cfop = (item.get('CFOP') or '').strip()
        vprod = to_decimal(item.get('vProd')) or Decimal('0.00')
        base_icms = to_decimal(item.get('base_icms')) or vprod
        p_icms = to_decimal(item.get('pICMS'))
        v_icms = to_decimal(item.get('vICMS'))
        pis = to_decimal(item.get('vPIS'))
        cofins = to_decimal(item.get('vCOFINS'))

        # Regra 1: incompatibilidade básica de CFOP/NCM
        if cfop in CFOP_INCOMPATIVEIS:
            for prefix, meta in CFOP_INCOMPATIVEIS[cfop].items():
                if ncm.startswith(prefix):
                    results.append({
                        'rule_id': 'CFOP_NCM_INCOMPATIVEL',
                        'severity': 'MÉDIA',
                        'description': f'Item {idx}: CFOP {cfop} é incompatível com NCM {ncm}.',
                        'suggested_recovery': 0.0,
                    })

        # Regra 2: NCM com alíquota esperada e divergência no ICMS
        if ncm in NCM_TABLE:
            expected_icms = NCM_TABLE[ncm]['icms']
            if p_icms is None:
                results.append({
                    'rule_id': 'ICMS_ALIQUOTA_AUSENTE',
                    'severity': 'MÉDIA',
                    'description': f'Item {idx}: NCM {ncm} espera ICMS {expected_icms}%, mas pICMS não foi informado.',
                    'suggested_recovery': 0.0,
                })
            elif abs(p_icms - expected_icms) > Decimal('0.01'):
                diff = expected_icms - p_icms
                recovery = (diff / Decimal('100')) * base_icms
                results.append({
                    'rule_id': 'ICMS_ALIQUOTA_MISMATCH',
                    'severity': 'ALTA',
                    'description': f'Item {idx}: ICMS {p_icms}% divergente do esperado {expected_icms}% para NCM {ncm}.',
                    'suggested_recovery': float(recovery.quantize(Decimal('0.01'))),
                })

            # Regra 3: ICMS-ST esperado e não informado
            if NCM_TABLE[ncm].get('expect_st') and not item.get('vICMSST'):
                results.append({
                    'rule_id': 'ICMS_ST_MISSING',
                    'severity': 'ALTA',
                    'description': f'Item {idx}: NCM {ncm} sugere ICMS-ST, mas valor não foi declarado.',
                    'suggested_recovery': 0.0,
                })

        # Regra 4: valores de PIS/COFINS suspeitos
        if pis is not None and vprod > 0 and pis > vprod:
            results.append({
                'rule_id': 'PIS_VALOR_SUSPEITO',
                'severity': 'MÉDIA',
                'description': f'Item {idx}: vPIS ({pis}) maior que valor do produto ({vprod}).',
                'suggested_recovery': 0.0,
            })

        if cofins is not None and vprod > 0 and cofins > vprod:
            results.append({
                'rule_id': 'COFINS_VALOR_SUSPEITO',
                'severity': 'MÉDIA',
                'description': f'Item {idx}: vCOFINS ({cofins}) maior que valor do produto ({vprod}).',
                'suggested_recovery': 0.0,
            })

        # Regra 5: ICMS informado no XML mas sem base de cálculo
        if p_icms is not None and base_icms is None:
            results.append({
                'rule_id': 'BASE_ICMS_AUSENTE',
                'severity': 'MÉDIA',
                'description': f'Item {idx}: pICMS informado sem base de cálculo (vBC).',
                'suggested_recovery': 0.0,
            })

        # Regra 6: valor de ICMS informado parece inválido se maior que valor do produto
        if v_icms is not None and vprod > 0 and v_icms > vprod:
            results.append({
                'rule_id': 'ICMS_VALOR_SUSPEITO',
                'severity': 'ALTA',
                'description': f'Item {idx}: vICMS ({v_icms}) maior que valor do produto ({vprod}).',
                'suggested_recovery': 0.0,
            })

    return results
