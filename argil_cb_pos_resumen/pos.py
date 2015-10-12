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

class pos_order_report_jasper(osv.osv):
    _name = 'pos.order.report.jasper'
    _description = 'Reporte Detallado de Ventas'
    _columns = {
        'sale_order_ids': fields.one2many('pos.order.report.jasper.line','report_id','Pedidos de Venta Relacionados'),
        'sale_journal_ids': fields.one2many('pos.order.report.journal.line','report_id','Metodos de Pago'),
        'sale_tax_ids': fields.one2many('pos.order.report.tax.line','report_id','Impuestos'),
        'user_ids': fields.many2many('res.users', 'pos_details_report_user_rel2', 'user_id', 'report_id', 'Usuarios'),
        'date_start': fields.date('Date Start', required=True),
        'date_end': fields.date('Date End', required=True),
        'company_id': fields.many2one('res.company', 'Compañia'),
        'name': fields.char('Referencia', size=256),
        'date': fields.datetime('Fecha Consulta'),
        'total_invoiced': fields.float('Total Facturado', digits=(14,2)),
        'total_discount': fields.float('Descuento Total', digits=(14,2)),
        'total_of_the_day': fields.float('Total del dia', digits=(14,2)),
        'total_paid': fields.float('Total Pagado', digits=(14,2)),
        'total_qty': fields.float('Cantidad de Producto', digits=(14,2)),
        'total_sale': fields.float('Total de Ventas', digits=(14,2)),
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

    _defaults = {  
        'company_id': _get_company,
        'date': _get_date,  

        }

    _order = 'id desc' 

class pos_order_report_jasper_line(osv.osv):
    _name = 'pos.order.report.jasper.line'
    _description = 'Pedidos de Venta Origen'
    _rec_name = 'order_id' 
    _columns = {
        'report_id': fields.many2one('pos.order.report.jasper', 'ID Ref'),
        'order_id': fields.many2one('pos.order','Pedido de Venta (POS)'),

    }
    _defaults = {  
        }



class pos_order_report_journal_line(osv.osv):
    _name = 'pos.order.report.journal.line'
    _description = 'Pagos del Reporte'
    _columns = {
        'report_id': fields.many2one('pos.order.report.jasper', 'ID Ref'),
        'name': fields.char('Descripcion', size=128),
        'sum': fields.float('Total', digits=(14,2)),

    }
    _defaults = {  
        }


class pos_order_report_tax_line(osv.osv):
    _name = 'pos.order.report.tax.line'
    _description = 'Impuestos del Reporte'
    _columns = {
        'report_id': fields.many2one('pos.order.report.jasper', 'ID Ref'),
        'name': fields.char('Descripcion', size=128),
        'amount': fields.float('Total', digits=(14,2)),

    }
    _defaults = {  
        }


class pos_details(osv.osv_memory):
    _name = 'pos.details'
    _inherit ='pos.details'
    _columns = {
    }

    _defaults = {
        }

    def print_report(self, cr, uid, ids, context=None):
        pos_report_obj = self.pool.get('pos.order.report.jasper')
        user_obj = self.pool.get('res.users')
        for rec in self.browse(cr, uid, ids, context):
            pos_order = self.pool.get('pos.order')
            user_list_ids = [x.id for x in rec.user_ids]
            company_id = user_obj.browse(cr, uid, uid).company_id.id
            company_id_name = user_obj.browse(cr, uid, uid).company_id.name
            if not user_list_ids:
                pos_usr_ids = pos_order.search(cr, uid, 
                [('date_order','>=',rec.date_start + ' 00:00:00'),
                ('date_order','<=',rec.date_end + ' 23:59:59'),
                ('state','in',('done','paid','invoiced')),
                ('company_id','=',company_id),
                ])
                if not pos_usr_ids:
                    raise except_orm(_('Error!'), 
                    _("No existen Pedidos Relacionados con el Rango seleccionado."))
                    return True
                cr.execute("""select user_id from pos_order
                    where id in %s group by user_id;
                    """,(tuple(pos_usr_ids),))
                cr_res = cr.fetchall()
                user_list_ids = [x[0] for x in cr_res if x]
            pos_order_ids = pos_order.search(cr, uid, 
                [('date_order','>=',rec.date_start + ' 00:00:00'),
                ('date_order','<=',rec.date_end + ' 23:59:59'),
                ('user_id','in',tuple(user_list_ids)),
                ('state','in',('done','paid','invoiced')),
                ('company_id','=',company_id),
                ])
            # pos_order_ids = pos_order.search(cr, uid, 
            #     [('date_order','>=',rec.date_start),('date_order','<=',rec.date_end),
            #     ('user_id','in',tuple(user_list_ids))])
            line_list = []
            if pos_order_ids:
                for pos in pos_order_ids:
                    xline = (0,0,{
                        'order_id': pos,
                        })
                    line_list.append(xline)
            vals = {
                'sale_order_ids': line_list ,
                'user_ids': [(6,0,user_list_ids)],
                'date_start': rec.date_start,
                'date_end': rec.date_end,
                'name': rec.date_start+"/"+rec.date_end+" "+company_id_name
                }

            #### TOTALES ###
            total_invoiced = 0.0
            total_discount = 0.0
            pos_ids = pos_order_ids
            total_lines = 0.0
            total_of_the_day = 0.0
            total_qty = 0.0
            for pos in pos_order.browse(cr, uid, pos_ids):
                for pol in pos.lines:
                    total_discount += ((pol.price_unit * pol.qty) * (pol.discount / 100))
                    total_lines += (pol.price_unit * pol.qty * (1 - (pol.discount) / 100.0))
                    total_qty += pol.qty

            pos_inv_ids = pos_order.search(cr, uid, 
                [('date_order','>=',rec.date_start + ' 00:00:00'),
                ('date_order','<=',rec.date_end + ' 23:59:59'),
                ('user_id','in',tuple(user_list_ids)),
                ('state','in',('done','paid','invoiced')),
                ('company_id','=',company_id),
                ('invoice_id','<>',False)])
            for pos in pos_order.browse(cr, uid, pos_inv_ids):
                for pol in pos.lines:
                    total_invoiced += (pol.price_unit * pol.qty * (1 - (pol.discount) / 100.0))

            if total_lines:
                 if total_lines == total_invoiced:
                    total_of_the_day = total_lines
                 else:
                    total_of_the_day = ((total_lines or 0.00) - (total_invoiced or 0.00))
            else:
                total_of_the_day = 0.0

            vals.update({'total_invoiced': total_invoiced,
                         'total_discount': total_discount,
                         'total_of_the_day': total_of_the_day,
                         'total_paid': total_of_the_day,
                         'total_qty': total_qty,
                         'total_sale': total_lines,
                          })
            report_id = pos_report_obj.create(cr, uid, vals, context)
            ######### RESUMEN DE LOS PAGOS ############
            statement_line_obj = self.pool.get("account.bank.statement.line")
            if pos_ids:
                print "## SI POS IDS"
                st_line_ids = statement_line_obj.search(cr, uid, [('pos_statement_id', 'in', pos_ids)])
                print "########## ST LINE IDS >>>> ", st_line_ids
                if st_line_ids:
                    st_id = statement_line_obj.browse(cr, uid, st_line_ids)
                    a_l=[]
                    for r in st_id:
                        a_l.append(r['id'])
                    cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                    "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                    "group by aj.name ",(tuple(a_l),))

                    data = cr.dictfetchall()
                    report_journal = self.pool.get('pos.order.report.journal.line')
                    for d in data:
                        d.update({'report_id': report_id})
                        journal_mov = report_journal.create(cr, uid, d, context)
            #### IMPUESTOS ####
            tax_report_obj  = self.pool.get('pos.order.report.tax.line')
            account_tax_obj = self.pool.get('account.tax')
            taxes = {}
            for order in pos_order.browse(cr, uid, pos_ids):
                for line in order.lines:
                    line_taxes = account_tax_obj.compute_all(cr, uid, line.product_id.taxes_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'amount':0.0})
                        taxes[tax['id']]['amount'] += tax['amount']
            taxes_vals = taxes.values()
            if taxes_vals:
                for tx in taxes_vals:
                    tx.update({'report_id': report_id})
                    tax_mov_r = tax_report_obj.create(cr, uid, tx, context)

            report = {
            'type': 'ir.actions.report.xml',
            'report_name': 'Detalle-Ventas',
            'datas': {
                        'model' : 'pos.order.report.jasper',
                        'ids'   : [report_id],
                        }
                    }
            return report
        return True

