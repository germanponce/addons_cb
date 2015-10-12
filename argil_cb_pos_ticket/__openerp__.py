# -*- encoding: utf-8 -*-
###########################################################################
#    Copyright (c) 2015 Argil Consulting - http://www.argil.mx
#    info Argil Consulting (info@argil.mx)
############################################################################
#    Coded by: Israel Cruz (israel.cruz@argil.mx)
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "POS Ticket - Casa Baltasar",
    "version": "1.0", 
    "author": "Argil", 
    "category": "POS", 
    "description": """
POS Ticket - Casa Baltasar
==========================

Este módulo tiene la configuración del ticket del POS de Casa Baltazar para Web y Server.

Otro punto de este modulo es que agrega el monto en letra en el pedido de venta generado por el POS.

    """, 
    "website": "http://www.argil.mx", 
    "depends" : ["point_of_sale"],
    "data": [
            "pos_ticket_template.xml",
            "pos.xml",
            "report_receipt.xml"],
            
    "qweb" : [
        'static/src/xml/pos_cb.xml',
    ], 
    "installable": True, 
    "active": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
