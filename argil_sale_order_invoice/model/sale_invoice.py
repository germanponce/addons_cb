# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Cidog de German Ponce Dominguez ( german.ponce@argil.mx )
#    Skype: german_442
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
from datetime import datetime, date
import pytz
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import netsvc, workflow


class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    _columns = {
    'invoiced_control': fields.boolean('Control de Facturacion'),
    }


    _defaults = {
    }


    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'invoiced_control': False,
            })
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

class sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    _columns = {
    'send_ok': fields.boolean('Enviado'),
    'invoiced_control': fields.boolean('Control de Facturacion'),
    'invoiced_mark': fields.boolean('Facturado'),
    }


    _defaults = {
    }


    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'send_ok': False,
            'invoiced_control': False,
            'invoiced_mark': False,
            })
        return super(sale_order_line, self).copy_data(cr, uid, id, default, context=context)


class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    
    
    _columns = {
        'invoice_2_general_public': fields.boolean('Publico en General', help="Activa este campo para Facturar como Publico en General."),
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'invoice_2_general_public': False,
            })
        return super(sale_order, self).copy(cr, uid, id, default, context=context)

    def get_customer_id_for_general_public(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        partner_id = partner_obj.search(cr, uid, [('use_as_general_public','=',1)], limit=1, context=context)
        if not partner_id:
            raise osv.except_osv(_('Error!'), _('Por favor Configura un Cliente para ser usado como Publico en General.'))    

        addr = partner_obj.address_get(cr, uid, partner_id, ['delivery', 'invoice', 'contact'])
        partner_id = partner_obj.browse(cr, uid, addr['invoice'])[0].id
        return partner_id


    def get_customer_for_general_public(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        partner_id = partner_obj.search(cr, uid, [('use_as_general_public','=',1)], limit=1, context=context)
        if not partner_id:
            raise osv.except_osv(_('Error!'), _('Por favor Configura un Cliente para ser usado como Publico en General.'))    

        addr = partner_obj.address_get(cr, uid, partner_id, ['delivery', 'invoice', 'contact'])
        partner_id = partner_obj.browse(cr, uid, addr['invoice'])[0]
        return partner_id

    def action_invoice3(self, cr, uid, ids, date, journal_id=False, context=None):
        print "###################### INVOICE 3 "
        if context is None: context = {}        
        inv_ref = self.pool.get('account.invoice')
        acc_tax_obj = self.pool.get('account.tax')
        inv_line_ref = self.pool.get('account.invoice.line')
        product_obj = self.pool.get('product.product')
        sales_order_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        picking_obj = self.pool.get('stock.picking')
        # bsl_obj = self.pool.get('account.bank.statement.line')
        print "################# JOURNAL ID ", journal_id
        partner = self.get_customer_for_general_public(cr, uid, ids, context)
        
        inv_ids = []
        po_ids = []
        lines = {}
        for order in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
            print "#################### ORDER NAME ", order.name
            if order.invoiced:
                for fac in order.invoice_ids:
                    inv_ids.append(fac.id)
                continue
            if not order.invoice_2_general_public:
                res = self.manual_invoice(cr, uid, [order.id], context)
                # res = self.action_invoice2(cr, uid, order, journal_id, context=context)
                print "################### RES ", res
                inv_ids.append(res['res_id'])
            else:
                # if order.state in ('progress','manual'):
                #     bsl_ids = [x.id for x in order.statement_ids]
                #     bsl_obj.write(cr, uid, bsl_ids, {'partner_id': partner.id}, context=context)
                po_ids.append(order.id)
                for line in order.order_line:
                    ## Agrupamos las líneas según el impuesto
                    xval = 0.0
                    for tax in acc_tax_obj.browse(cr, uid, [x.id for x in line.product_id.taxes_id]):
                        xval += (tax.price_include and tax.amount or 0.0)

                    tax_names = ", ".join([x.name for x in line.product_id.taxes_id])
                    val={
                        'tax_names'           : ", ".join([x.name for x in line.product_id.taxes_id]),
                        'taxes_id'            : ",".join([str(x.id) for x in line.product_id.taxes_id]),
                        'price_subtotal'      : line.price_subtotal * (1.0 + xval),
                        'price_subtotal_incl' : line.price_subtotal,
                        }
                    key = (val['tax_names'],val['taxes_id'])
                    if not key in lines:
                        lines[key] = val
                        lines[key]['price_subtotal'] = val['price_subtotal']
                        lines[key]['price_subtotal_incl'] = val['price_subtotal_incl']

                    else:
                        lines[key]['price_subtotal'] += val['price_subtotal']
                        lines[key]['price_subtotal_incl'] += val['price_subtotal_incl']

        if po_ids:

            uom_obj = self.pool.get('product.uom')
            uom_id = uom_obj.search(cr, uid, [('use_4_invoice_general_public','=',1)], limit=1, context=context)
            if not uom_id:
                raise osv.except_osv(_('Error!'), _('Please configure an Unit of Measure as default for use as UoM in Invoice Lines.'))    
            
            acc = partner.property_account_receivable.id
            print "###########################  journal_id", journal_id
            inv = {
                'name'      : _('From POS Orders'),
                'origin'    : _('POS Orders from %s' % (date[8:10]+'/'+date[5:7]+'/'+date[0:4])),
                'account_id': acc,
                'journal_id': journal_id or order.sale_journal.id,
                'type'      : 'out_invoice',
                'reference' : order.name,
                'partner_id': partner.id,
                'comment'   : _('Invoice created from POS Orders'),
                'currency_id': order.pricelist_id.currency_id.id, # considering partner's sale pricelist's currency
            }
            inv.update(inv_ref.onchange_partner_id(cr, uid, [], 'out_invoice', partner.id)['value'])
            if not inv.get('account_id', None):
                inv['account_id'] = acc
            inv_id = inv_ref.create(cr, uid, inv, context=context)
            
            # self.write(cr, uid, po_ids, {'invoice_id': inv_id, 'state': 'invoiced'}, context=context)
            self.write(cr, uid, po_ids, { 'invoiced': True }, context=context)
        
            ### VALIDANDO LOS WORKFLOW ###
            for so in po_ids:
                cr.execute('INSERT INTO sale_order_invoice_rel \
                        (order_id,invoice_id) values (%s,%s)', (so, inv_id))
                flag = True
                data_sale = sales_order_obj.browse(cr, uid, so, context=context)
                for line in data_sale.order_line:
                    if not line.invoiced:
                        flag = False
                        break
                if flag:
                    wf_service.trg_validate(uid, 'sale.order', so, 'manual_invoice', cr)
                
                # if data_sale.order_policy == 'picking':
                print "########### si entra en esta parte ???? Validaciones finales"
                picking_obj.write(cr, uid, map(lambda x: x.id, data_sale.picking_ids), {'invoice_state': 'invoiced'})
                sales_order_obj.write(cr, uid, [so], {'state': 'progress'})
                sales_order_obj.signal_workflow(cr, uid, [so], 'manual_invoice')
                for delinv in data_sale.invoice_ids:
                    if delinv.id != inv_id:
                        self.pool.get('account.invoice').unlink(cr, uid, [delinv.id], context=None)
                sales_order_obj.signal_workflow(cr, uid, [so], 'invoice_corrected')
                # wf_service.trg_validate(uid, 'sale.order', so, 'manual_invoice', cr)
                # wf_service.trg_validate(uid, 'sale.order', so, 'invoice_corrected', cr)
            inv_ids.append(inv_id)
            for key, line in lines.iteritems():
                tax_name = ''
                inv_line = {
                    'invoice_id': inv_id,
                    'product_id': False,
                    'name'      : ('VENTA AL PUBLICO EN GENERAL DEL DIA %s DEL ALMACEN %s' % (date[8:10]+'/'+date[5:7]+'/'+date[0:4], order.warehouse_id.name)) +
                                   (line['tax_names'] and (' CON %s' % line['tax_names']) or ''),
                    'quantity'  : 1,
                    'account_id': order.order_line[0].product_id.property_account_income.id or order.order_line[0].product_id.categ_id.property_account_income_categ.id,
                    'uos_id'    : uom_id[0],
                    'price_unit': line['price_subtotal'],
                    'discount'  : 0,
                    'invoice_line_tax_id' : [(6, 0, line['taxes_id'].split(','))] if line['taxes_id'] else False,
                }

                inv_line_id = inv_line_ref.create(cr, uid, inv_line, context=context)
                print "################# INV LINE ID ",inv_line_id
                print "################# INV LINE ID ",inv_line_ref
                order_line_obj.write(cr, uid, [x.id for x in order.order_line], 
                                             {'invoice_lines': [(4, inv_line_id)],'invoiced': True}, context=context) 

            inv_ref.button_reset_taxes(cr, uid, [inv_id], context=context)
            self.signal_workflow(cr, uid, po_ids, 'invoice')
            inv_ref.signal_workflow(cr, uid, [inv_id], 'validate')

        if not inv_ids: return {}
        
        # ir_model_data = self.pool.get('ir.model.data')
        # act_obj = self.pool.get('ir.actions.act_window')
        # result = ir_model_data.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
        # id = result and result[1] or False
        # context.update({'type':'out_invoice'})
        # result = act_obj.read(cr, uid, [id], context=context)[0]
        # result['domain'] = "[('id','in', [" + ','.join(map(str, inv_ids)) + "])]"
        # return result

        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'domain': "[('id','in', ["+','.join(map(str,inv_ids))+"])]",
            'name': _('Facturas Publico en General / Clientes'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': {'type': 'out_invoice'},
            }
        

class sale_make_invoice(osv.osv_memory):
    _name = "sale.make.invoice"
    _inherit = "sale.make.invoice"

    def default_get(self, cr, uid, fields, context=None):
        #print "context: ", context
        if context is None: context = {}
        #print "context: ", context
        res = super(sale_make_invoice, self).default_get(cr, uid, fields, context=context)
        record_ids = context.get('active_ids', [])
        sale_order_obj = self.pool.get('sale.order')
        if not record_ids:
            return {}
        tickets = []
        
        partner_id = sale_order_obj.get_customer_id_for_general_public(cr, uid, record_ids, context)

        for ticket in sale_order_obj.browse(cr, uid, record_ids, context):

            if ticket.state in ('invoiced','cancel') and bool(ticket.invoice_id):
                continue
            tickets.append({
                    'order_id'     : ticket.id,
                    'date_order'    :  ticket.date_order,
                    'order_id': ticket.id,
                    'name' :  ticket.client_order_ref,
                    'user_id'       :  ticket.user_id.id,
                    'partner_id'    :  ticket.partner_id and ticket.partner_id.id or False,
                    'amount_total'  :  ticket.amount_total,
                    #'invoice_2_general_public' : (ticket.partner_id.invoice_2_general_public or ticket.partner_id.id == partner_id) if ticket.partner_id else True,
                    'invoice_2_general_public' : True,
                    })
        res.update(order_ids=tickets)
        #print "res: ", res
        return res


    _columns = {
       'invoice_2_general_public': fields.boolean('Facturar a Publico en General'),
       'period_id'  : fields.many2one('account.period', 'Force period', required=True),
       'journal_id' : fields.many2one('account.journal', 'Invoice Journal', help='You can select here the journal to use for the Invoice that will be created.', required=True),
       'order_ids' : fields.one2many('sale.order.invoice_wizard.line','wiz_id','Pedidos a Facturar', required=True),

        }

    def _get_date(self, cr, uid, context=None):
        tz_date = False
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
        user = self.pool.get('res.users').browse(cr, uid, uid, context=None)
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        start = pytz.utc.localize(start).astimezone(tz)     
        tz_date = start.strftime("%Y-%m-%d %H:%M:%S")
        return tz_date

    def _get_journal(self, cr, uid, context=None):
        obj_journal = self.pool.get('account.journal')
        user_obj = self.pool.get('res.users')
        if context is None:
            context = {}
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        journal = obj_journal.search(cr, uid, [('type', '=', 'sale'), ('company_id','=',company_id)], limit=1, context=context)
        return journal and journal[0] or False

    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        res = {}
        cr.execute("""SELECT p.id
                      FROM account_period p
                      where p.date_start <= NOW()
                      and p.date_stop >= NOW()
                      AND p.special = false
                      AND p.company_id = %s
                      LIMIT 1
            """ % (self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id))
        data = cr.fetchall()
        period = data and data[0] or False
        return period

    _defaults = {
        'journal_id': _get_journal,
        'period_id': _get_period,
        'invoice_date': _get_date,
        }


    def make_invoices(self, cr, uid, ids, context=None):
        self_br = self.browse(cr, uid, ids, context=None)[0]
        sale_order_obj = self.pool.get('sale.order')
        active_ids = context and context.get('active_ids', False)
        cr.execute("""
            select name from sale_order where id in %s and order_policy = 'picking';
            """, (tuple(active_ids),))
        cr_res = cr.fetchall()
        order_name_rest = [str(x[0]) for x in cr_res]
        order_name_rest = list(set(order_name_rest))
        if order_name_rest:
            raise except_orm(
                           _('Error !'),
                           _('No puedes Facturar pedidos a Facturar desde Albaran.\n %s' % str(order_name_rest)))

        cr.execute("""select name from sale_order where state not in ('progress','manual')
            and id in %s;""", (tuple(ids),))
        cr_res = cr.fetchall()
        validate_list = [str(x[0]) for x in cr_res if x[0]]
        if validate_list:
            raise except_orm(
            _('Error !'),
            _('Los siguientes pedidos no se pueden Facturar debido al Estado del registro.\n %s' % (str(validate_list),)))
        
        invoice_2_general_public_list = [x.id for x in self_br.order_ids if x.invoice_2_general_public]
        if not invoice_2_general_public_list and self_br.invoice_2_general_public:
            if order_name_rest:
                raise except_orm(
                               _('Error !'),
                               _('Tienes Activada la Opcion de Facturar a Publico en General, pero ningun registro esta Activado con la misma Opcion.\n %s' % str(order_name_rest)))
        print "#################### INVOICE 2 GENERAL PUBLIC LIST ", invoice_2_general_public_list
        if self_br.invoice_2_general_public:
            cr.execute("""SELECT p.id
                          FROM account_period p
                          where p.date_start <= '%s'
                          and p.date_stop >= '%s'
                          AND p.special = false
                          AND p.company_id = %s
                          LIMIT 1
                """ % (self_br.invoice_date, self_br.invoice_date, self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id))
            data = cr.fetchall()
            period = data[0][0] if data else False
            if not period:
                raise except_orm(
                       _('Error !'),
                       _('Crea un Periodo para la Fecha que intentas Facturar [ %s ]' % self_br.invoice_date))
            ids_to_set_as_general_public, ids_to_invoice = [], []

            res = {}
            for rec in self.browse(cr, uid, ids, context):
                for line in rec.order_ids:
                    ids_to_invoice.append(line.order_id.id)
                    if line.invoice_2_general_public:
                        ids_to_set_as_general_public.append(line.order_id.id)
            if ids_to_set_as_general_public:
                cr.execute("update sale_order set invoice_2_general_public=true where id IN %s",(tuple(ids_to_set_as_general_public),))                
            if ids_to_invoice:
                # res = sale_order_obj.manual_invoice(cr, uid, ids_to_set_as_general_public, context=None )
                res = self.pool.get('sale.order').action_invoice3(cr, uid, ids_to_invoice, rec.invoice_date, rec.journal_id.id)
                return res
            
            return result

        res = super(sale_make_invoice, self).make_invoices(cr, uid, ids, context)
        return res

    def make_invoices_grouped(self, cr, uid, ids, active_ids, context=None):

        invoice_create_ids = []
        invoice_obj = self.pool.get('account.invoice')
        sale_order_obj = self.pool.get('sale.order')
        invoice_line_obj = self.pool.get('account.invoice.line')
        sale_order_line = self.pool.get('sale.order.line')
        active_ids = active_ids
        wf_service = netsvc.LocalService("workflow")

        ################ INTERRUPCION DEL FLUJO PYTHON ############################
        raise except_orm(_('Interrupcion del Flujo!'), 
                            _('Debugeando el Codigo de Creacion de Factura desde lineas de Venta') )
        
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'domain': "[('id','in', ["+','.join(map(str,invoice_create_ids))+"])]",
            'name': _('Facturas'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': {'type': 'out_invoice'},
            }

class sale_order_invoice_wizard_line(osv.osv_memory):
    _name = "sale.order.invoice_wizard.line"
    _description = "Asistente para Crear Factura Publico en General"

    """
    """
        
    _columns = {
        'wiz_id'        : fields.many2one('sale.make.invoice','Ref ID'),        
        'order_id'     : fields.many2one('sale.order', 'Pedido de Venta'),
        'date_order'    : fields.related('order_id', 'date_order', type="datetime", string="Fecha", readonly=True),
        'name' : fields.related('order_id', 'name', type="char", size=64, string="Referencia", readonly=True),
        'user_id'       : fields.related('order_id', 'user_id', type="many2one", relation="res.users", string="Vendedor", readonly=True),
        'amount_total'  : fields.related('order_id', 'amount_total', type="float", string="Total", readonly=True),
        'partner_id'    : fields.related('order_id', 'partner_id', type="many2one", relation="res.partner", string="Cliente", readonly=True),
        'invoice_2_general_public': fields.boolean('Publico en General'),
        
    }
