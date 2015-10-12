# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015
#    All Rights Reserved.
#    info skype: german_442 email: (german.ponce@outlook.com)
############################################################################

{
    'name': 'Modificacion y Extension del Reporte de Facturacion Electronica',
    'version': '1',
    "author" : "German Ponce Dominguez",
    "category" : "Facturae",
    'description': """

Este modulo reemplaza el reporte de factura electronica del modulo l10n_mx_facturae_report.

    """,
    "website" : "http://www.argil.mx",
    "license" : "AGPL-3",
    "depends" : ["l10n_mx_facturae_report"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    "report.xml",
                    ],
    "installable" : True,
    "active" : False,
}
