"""Parsing de XML de NF-e (estrutura simplificada e robusta)."""

from __future__ import annotations

from typing import Dict, List, Tuple, Any

from lxml import etree


def qname_localname(element: etree._Element) -> str:
    return etree.QName(element).localname


def first_descendant(root: etree._Element, name: str) -> etree._Element | None:
    for el in root.iter():
        if qname_localname(el) == name:
            return el
    return None


def all_descendants(root: etree._Element, name: str) -> List[etree._Element]:
    return [el for el in root.iter() if qname_localname(el) == name]


def text_of(node: Any, tag_name: str) -> str | None:
    if node is None:
        return None
    for child in node:
        if qname_localname(child) == tag_name:
            if child.text is None:
                return None
            return child.text.strip()
    return None


def parse_nfe_xml(xml_bytes: bytes) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    root = etree.fromstring(xml_bytes)

    inf_nfe = first_descendant(root, 'infNFe')
    chave = None
    if inf_nfe is not None and 'Id' in inf_nfe.attrib:
        chave = inf_nfe.attrib.get('Id', '').replace('NFe', '')

    ide = first_descendant(root, 'ide')
    serie = text_of(ide, 'serie') if ide is not None else None
    numero = text_of(ide, 'nNF') if ide is not None else None
    data_emissao = text_of(ide, 'dhEmi') or text_of(ide, 'dEmi') if ide is not None else None

    emit = first_descendant(root, 'emit')
    dest = first_descendant(root, 'dest')
    emit_cnpj = text_of(emit, 'CNPJ') or text_of(emit, 'CPF') if emit is not None else None
    emit_xNome = text_of(emit, 'xNome') if emit is not None else None
    dest_cnpj = text_of(dest, 'CNPJ') or text_of(dest, 'CPF') if dest is not None else None

    invoice = {
        'chave': chave,
        'serie': serie,
        'numero': numero,
        'data_emissao': data_emissao,
        'emit_cnpj': emit_cnpj,
        'emit_xNome': emit_xNome,
        'dest_cnpj': dest_cnpj,
    }

    items: List[Dict[str, Any]] = []
    dets = all_descendants(root, 'det')

    for det in dets:
        prod = first_descendant(det, 'prod')
        imposto = first_descendant(det, 'imposto')

        item: Dict[str, Any] = {
            'nItem': det.attrib.get('nItem'),
            'cProd': None,
            'xProd': None,
            'NCM': None,
            'CFOP': None,
            'qCom': None,
            'vUn': None,
            'vProd': None,
            'base_icms': None,
            'pICMS': None,
            'vICMS': None,
            'vBCST': None,
            'pST': None,
            'vICMSST': None,
            'vPIS': None,
            'vCOFINS': None,
        }

        if prod is not None:
            item['cProd'] = text_of(prod, 'cProd')
            item['xProd'] = text_of(prod, 'xProd')
            item['NCM'] = text_of(prod, 'NCM')
            item['CFOP'] = text_of(prod, 'CFOP')
            item['qCom'] = text_of(prod, 'qCom')
            item['vUn'] = text_of(prod, 'vUn')
            item['vProd'] = text_of(prod, 'vProd')

        if imposto is not None:
            # ICMS
            for child in imposto:
                tag_name = qname_localname(child)
                if tag_name.startswith('ICMS'):
                    item['base_icms'] = text_of(child, 'vBC') or item['base_icms']
                    item['pICMS'] = text_of(child, 'pICMS') or item['pICMS']
                    item['vICMS'] = text_of(child, 'vICMS') or item['vICMS']
                    item['vBCST'] = text_of(child, 'vBCST') or item['vBCST']
                    item['pST'] = text_of(child, 'pST') or item['pST']
                    item['vICMSST'] = text_of(child, 'vICMSST') or item['vICMSST']

            pis = first_descendant(imposto, 'PIS')
            if pis is not None:
                for pchild in pis:
                    ptag = qname_localname(pchild)
                    if ptag in {'PISAliq', 'PISQtde', 'PISOutr'}:
                        item['vPIS'] = text_of(pchild, 'vPIS') or item['vPIS']

            cofins = first_descendant(imposto, 'COFINS')
            if cofins is not None:
                for cchild in cofins:
                    ctag = qname_localname(cchild)
                    if ctag in {'COFINSAliq', 'COFINSQtde', 'COFINSOutr'}:
                        item['vCOFINS'] = text_of(cchild, 'vCOFINS') or item['vCOFINS']

        items.append(item)

    return invoice, items
