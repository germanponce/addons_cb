# -*- coding: utf-8 -*-

{
    'name': 'Reportes Casa Baltazar',
    'version': '1.0',
    'category': 'CasaBaltasar',
    'description': """
        Módulo para la Gestion de Reportes Casa Baltazar
	* Cheques
	* Etiquetas de producto
	* Factura
    """,
    'author': 'Esther Flores',
    'website': 'http://www.argil.mx',
    'depends': ['jasper_reports','account_voucher','sale'],
    'data': [
        "report_cb.xml",
    ],
    'installable': True,
    'auto_install': False,
}

