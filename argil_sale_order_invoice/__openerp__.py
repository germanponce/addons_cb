# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Cidog de German Ponce Dominguez ( german.ponce@argil.mx )
#    Skype: german_442
##############################################################################

{
    "name": "Facturación Publico en General (Pedidos de Venta)", 
    "version": "1.1", 
    "author": "Argil Consulting", 
    "category": "Sale", 
    "description": """
Facturación Publico en General
==============================

Este modulo permite Generar la Facturación de Publico en General para todos los Pedidos de Venta.

    """, 
    "website": "http://www.argil.mx", 
    "license": "AGPL-3", 
    "depends": ["base_setup", 
                "product", 
		        "account",
                "sale",
                "argil_pos_invoice",
                "sale_stock",
            ], 
    "data": [
        "view/sale_invoice_view.xml",
        # "view/account_view.xml"
    ], 
    "test": [], 
    "js": [], 
    "css": [], 
    "qweb": [], 
    "installable": True, 
    "auto_install": False, 
    "active": False
}