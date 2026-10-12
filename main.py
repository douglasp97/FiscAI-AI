#!/usr/bin/env python3
"""FiscAI-AI MVP desktop application for NF-e XML auditing."""

import os
import sys
import traceback
from typing import List, Dict, Any

import PySimpleGUI as sg

from parser import parse_nfe_xml
from validators import validate_xml_structure, validate_required_fields
from fiscal_rules import apply_rules_to_invoice
from exporters import export_csv, export_xlsx, export_pdf

sg.theme('LightBlue2')


def process_files(filepaths: List[str]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    invoices = []
    results = []

    for path in filepaths:
        try:
            with open(path, 'rb') as fh:
                xml_bytes = fh.read()

            invoice, items = parse_nfe_xml(xml_bytes)
            validation_errors = validate_xml_structure(xml_bytes)
            required_missing = validate_required_fields(invoice, items)
            all_issues = validation_errors + required_missing
            audit = apply_rules_to_invoice(invoice, items)

            # Merge issues from validations into the result set.
            for issue in all_issues:
                audit.append({
                    'rule_id': issue['rule_id'],
                    'severity': issue['severity'],
                    'description': issue['description'],
                    'suggested_recovery': 0.0,
                    'is_validation': True,
                })

            invoices.append({
                'path': path,
                'invoice': invoice,
                'items': items,
                'audit': audit,
            })

            for audit_item in audit:
                results.append({
                    'chave': invoice.get('chave', '-'),
                    'numero': invoice.get('numero', '-'),
                    'fornecedor': invoice.get('emit_xNome') or invoice.get('emit_cnpj') or '-',
                    'rule': audit_item.get('rule_id', 'UNKNOWN'),
                    'severity': audit_item.get('severity', 'BAIXA'),
                    'description': audit_item.get('description', ''),
                    'suggested_recovery': float(audit_item.get('suggested_recovery', 0.0) or 0.0),
                })

        except Exception as exc:
            results.append({
                'chave': '-',
                'numero': '-',
                'fornecedor': '-',
                'rule': 'PROCESS_ERROR',
                'severity': 'ALTA',
                'description': f'Erro ao processar arquivo: {str(exc)}',
                'suggested_recovery': 0.0,
            })

    return invoices, results


layout = [
    [sg.Text('FiscAI-AI - Auditoria Fiscal de NF-e', font=('Arial', 14, 'bold'))],
    [sg.Text('Arquivos XML:'), sg.Input(key='-FILES-', enable_events=True), sg.FilesBrowse('Selecionar XML', file_types=(('XML Files', '*.xml'),))],
    [sg.Button('Processar'), sg.Button('Exportar CSV'), sg.Button('Exportar XLSX'), sg.Button('Exportar PDF'), sg.Button('Sair')],
    [sg.Text('Resultado:'), sg.Text('0', key='-COUNT-')],
    [sg.Table(
        values=[],
        headings=['chave', 'numero', 'fornecedor', 'rule', 'severity', 'description', 'suggested_recovery'],
        auto_size_columns=True,
        row_height=28,
        num_rows=18,
        key='-TABLE-',
        expand_x=True,
        expand_y=True,
        justification='left',
    )],
]

window = sg.Window('FiscAI-AI', layout, resizable=True, finalize=True)
window.set_min_size((1000, 620))

invoices_cache = []
results_cache = []

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Sair'):
        break

    if event == 'Processar':
        filepaths = [p for p in values['-FILES-'].split(';') if p.strip()]
        if not filepaths:
            sg.popup('Selecione pelo menos um arquivo XML.')
            continue

        try:
            invoices_cache, results_cache = process_files(filepaths)
            table_rows = [[
                r.get('chave', '-'),
                r.get('numero', '-'),
                r.get('fornecedor', '-'),
                r.get('rule', '-'),
                r.get('severity', 'BAIXA'),
                r.get('description', ''),
                f"{float(r.get('suggested_recovery', 0.0) or 0.0):.2f}",
            ] for r in results_cache]

            window['-TABLE-'].update(values=table_rows)
            window['-COUNT-'].update(str(len(table_rows)))
            sg.popup(f'{len(table_rows)} registros processados com sucesso.')
        except Exception as exc:
            traceback.print_exc()
            sg.popup(f'Erro inesperado: {exc}')

    if event == 'Exportar CSV':
        if not results_cache:
            sg.popup('Primeiro processe algum XML.')
            continue
        save_path = sg.popup_get_file('Salvar CSV', save_as=True, default_extension='.csv', file_types=(('CSV Files', '*.csv'),))
        if save_path:
            try:
                export_csv(results_cache, save_path)
                sg.popup(f'Arquivo CSV salvo em: {save_path}')
            except Exception as exc:
                sg.popup(f'Erro ao exportar CSV: {exc}')

    if event == 'Exportar XLSX':
        if not results_cache:
            sg.popup('Primeiro processe algum XML.')
            continue
        save_path = sg.popup_get_file('Salvar XLSX', save_as=True, default_extension='.xlsx', file_types=(('XLSX Files', '*.xlsx'),))
        if save_path:
            try:
                export_xlsx(results_cache, save_path)
                sg.popup(f'Arquivo XLSX salvo em: {save_path}')
            except Exception as exc:
                sg.popup(f'Erro ao exportar XLSX: {exc}')

    if event == 'Exportar PDF':
        if not invoices_cache:
            sg.popup('Primeiro processe algum XML.')
            continue
        save_path = sg.popup_get_file('Salvar PDF', save_as=True, default_extension='.pdf', file_types=(('PDF Files', '*.pdf'),))
        if save_path:
            try:
                export_pdf(invoices_cache, save_path)
                sg.popup(f'Arquivo PDF salvo em: {save_path}')
            except Exception as exc:
                sg.popup(f'Erro ao exportar PDF: {exc}')

window.close()
