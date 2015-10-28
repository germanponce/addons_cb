# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from openerp import models, fields, api, _
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from datetime import time, datetime
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import osv, fields, expression
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import base64

import pytz

class pos_stock_inventory_categ(osv.osv):
    _name = 'pos.stock.inventory.categ'
    _description = 'Reporte Inventario por Categoria'
    _columns = {
        'report_lines': fields.one2many('pos.stock.inventory.categ.line','report_id','Lineas del Inventario'),
        'company_id': fields.many2one('res.company', 'Compañia'),
        'date': fields.datetime('Fecha Consulta'),
        'name': fields.char('Descripcion del Inventario', size=128),
        'location_id': fields.many2one('stock.location', 'Ubicacion Inventariada'),
        'user_id': fields.many2one('res.users', 'Usuario Audito'),
    }

    def _get_company(self, cr, uid, context=None):
        user_br = self.pool.get('res.users').browse(cr, uid, uid, context)
        company_id = user_br.company_id.id
        return company_id

    def _get_date(self, cr, uid, context=None):
        date = datetime.now().strftime('%Y-%m-%d')
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return date_now
        # start = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
        # user = self.pool.get('res.users').browse(cr, uid, uid)
        # tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        # start = pytz.utc.localize(start).astimezone(tz)     # convert start in user's timezone
        # tz_date = start.strftime("%Y-%m-%d %H:%M:%S")
        # return tz_date
    def _get_uid(self, cr, uid, context=None):
        return uid

    _defaults = {  
        'company_id': _get_company,
        'date': _get_date, 
        'user_id': _get_uid,

        }

    _order = 'id desc' 

class pos_stock_inventory_categ_line(osv.osv):
    _name = 'pos.stock.inventory.categ.line'
    _description = ' Reporte Inventario Lineas de Categoria'
    _rec_name = 'detail_id' 
    _columns = {
        'report_id': fields.many2one('pos.stock.inventory.categ', 'ID Ref'),
        'detail_id': fields.many2one('pos.stock.inventory.categ.detail','Inventario por Categoria'),

    }
    _defaults = {  
        }

class pos_stock_inventory_categ_detail(osv.osv):
    _name = 'pos.stock.inventory.categ.detail'
    _description = 'Inventario por Categoria'
    _rec_name = 'product_category' 
    _columns = {
    'ref_id': fields.many2one('pos.stock.inventory.categ.line', 'ID Ref'),
    'product_category': fields.many2one('product.category', 'Categoria'),
    'detail_line': fields.one2many('pos.stock.inventory.categ.detail.line', 'ref_id', 'Productos'),
    }
    _defaults = {  
        }
    _order = 'id' 

class pos_stock_inventory_categ_detail_line(osv.osv):
    _name = 'pos.stock.inventory.categ.detail.line'
    _description = 'Detalle del Inventario por Categoria'
    _rec_name = 'product_id' 
    _columns = {
        'ref_id': fields.many2one('pos.stock.inventory.categ.detail', 'ID Ref'),

        'location_id': fields.many2one('stock.location', 'Ubicacion',),
        'product_id': fields.many2one('product.product', 'Producto'),
        'product_uom_id': fields.many2one('product.uom', 'Unidad Base',),
        'product_qty': fields.float('Cantidad', digits=(14,2)),
        'default_code': fields.related('product_id', 'default_code', type='char', string='Codigo Interno', readonly=True),

    }
    _defaults = {  
        }
    _order = 'id' 

class stock_inventory_line(osv.osv):
    _name = 'stock.inventory.line'
    _inherit ='stock.inventory.line'
    _columns = {
        'product_category': fields.related('product_id', 'categ_id', 
            type="many2one", relation="product.category", string='Categoria', store=True),
        }

    _defaults = {
        }

class stock_inventory(osv.osv_memory):
    _name = 'stock.inventory'
    _inherit ='stock.inventory'
    _columns = {
    }

    _defaults = {
        }

    def print_report(self, cr, uid, ids, context=None):
        pos_report_obj = self.pool.get('pos.stock.inventory.categ')
        inventory_line_obj = self.pool.get('stock.inventory.line')
        user_obj = self.pool.get('res.users')
        for rec in self.browse(cr, uid, ids, context):
            cr.execute("""
                delete from pos_stock_inventory_categ;
                """)
            cr.execute("""
                delete from pos_stock_inventory_categ_line;
                """)
            cr.execute("""
                delete from pos_stock_inventory_categ_detail;
                """)
            cr.execute("""
                delete from pos_stock_inventory_categ_detail_line;
                """)
            ####### PRIMERO A CONSTRUIR LAS CATEGORIAS Y SUS DETALLES ######
            cr.execute("""
                select product_category from stock_inventory_line
                where inventory_id = %s group by product_category;
                """ % rec.id)
            cr_res = cr.fetchall()
            category_ids = [x[0] for x in cr_res if x]

            inventory_categ_detail = self.pool.get('pos.stock.inventory.categ.detail')
            inventory_categ_detail_ids = []
            for category in category_ids:
                detail_lines = []
                cr.execute("""
                    select id from stock_inventory_line where inventory_id = %s
                    and product_category = %s ;
                    """ % (rec.id, category, ))
                cr_res = cr.fetchall()
                inventory_line_ids = [x[0] for x in cr_res]
                cr.execute("""
                    select location_id,
                            product_id,
                            product_uom_id,
                            product_qty
                            from stock_inventory_line where id in %s ;
                    """, (tuple(inventory_line_ids),))
                detail_lines = cr.dictfetchall()
                vals_d = {
                'product_category': category,
                'detail_line': [(0,0,x) for x in detail_lines],
                }
                inv_categ_detail_id = inventory_categ_detail.create(cr, uid, vals_d, context)
                inventory_categ_detail_ids.append(inv_categ_detail_id)
            categ_report_obj = self.pool.get('pos.stock.inventory.categ')
            ####### Al final el reporte #########
            vals = {
                'name': rec.name,
                'location_id': rec.location_id.id,
                'report_lines': [(0,0,{'detail_id':x}) for x in inventory_categ_detail_ids] ,
            }
            report_id = self.pool.get('pos.stock.inventory.categ').create(cr, uid, vals, context)
            report = {
            'type': 'ir.actions.report.xml',
            'report_name': 'Detalle-Inventario',
            'datas': {
                        'model' : 'pos.stock.inventory.categ',
                        'ids'   : [report_id],
                        }
                    }
            return report
        return True

