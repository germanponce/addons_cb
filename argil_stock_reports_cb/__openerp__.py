# -*- coding: utf-8 -*-

{
    'name': 'Reportes de Inventario Casa Baltazar',
    'version': '1.0',
    'category': 'CasaBaltasar',
    'description': """
        Módulo para la Gestion de Reportes para Inventarios
    """,
    'author': 'German Ponce Dominguez',
    'website': 'http://www.argil.mx',
    'depends': ['jasper_reports','stock','sale_stock'],
    'data': [
        "report_cb.xml",
        "stock.xml",
        "security/ir.model.access.csv"
    ],
    'installable': True,
    'auto_install': False,
}

