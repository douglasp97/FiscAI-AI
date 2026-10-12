"""Funções utilitárias para exportar relatórios e resultados."""

from __future__ import annotations

import csv
from typing import Any, Dict, List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export_csv(results: List[Dict[str, Any]], path: str) -> None:
    fieldnames = ['chave', 'numero', 'fornecedor', 'rule', 'severity', 'description', 'suggested_recovery']
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({
                'chave': row.get('chave', ''),
                'numero': row.get('numero', ''),
                'fornecedor': row.get('fornecedor', ''),
                'rule': row.get('rule', ''),
                'severity': row.get('severity', ''),
                'description': row.get('description', ''),
                'suggested_recovery': row.get('suggested_recovery', 0.0),
            })


def export_xlsx(results: List[Dict[str, Any]], path: str) -> None:
    df = pd.DataFrame(results)
    df.to_excel(path, index=False)


def export_pdf(invoices_cache: List[Dict[str, Any]], path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph('Relatório FiscAI-AI - NF-e', styles['Title']),
        Spacer(1, 12),
    ]

    for entry in invoices_cache:
        invoice = entry.get('invoice', {})
        audit = entry.get('audit', [])
        title = (
            f"NF-e {invoice.get('numero', '-')} | Chave {invoice.get('chave', '-')} | "
            f"Emitente {invoice.get('emit_xNome') or invoice.get('emit_cnpj') or '-'}"
        )
        elements.append(Paragraph(title, styles['Heading2']))

        if not audit:
            elements.append(Paragraph('Sem inconsistências fiscais detectadas.', styles['Normal']))
            elements.append(Spacer(1, 12))
            continue

        data = [['Regra', 'Severidade', 'Descrição', 'Recuperação']]
        for item in audit:
            data.append([
                item.get('rule_id', '-'),
                item.get('severity', 'BAIXA'),
                item.get('description', ''),
                f"{float(item.get('suggested_recovery', 0.0) or 0.0):.2f}",
            ])

        table = Table(data, colWidths=[80, 70, 260, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    doc.build(elements)
