 # -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.addons.decimal_precision import decimal_precision as dp
import openerp.netsvc as netsvc

class return_order(osv.osv):
    _name = "return.order"

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'shipped': False,
            'invoice_ids': [],
            'picking_ids': [],
            'date_confirm': False,
            'name': self.pool.get('ir.sequence').get(cr, uid, 'return.order'),
            'incoming_exchange': False,
            'outgoing_exchange': False,
        })
        return super(return_order, self).copy(cr, uid, id, default, context=context)

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def onchange_partner_id(self, cr, uid, ids, part):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False, 'fiscal_position': False, 'customer_name':False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['delivery', 'invoice', 'contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        property_payment_term = part.property_payment_term.id
        val = {
            'partner_invoice_id': addr['invoice'],
#            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'customer_name': part.name,
            'payment_term' : property_payment_term or '',
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}

#    def onchange_partner_order_id(self, cr, uid, ids, order_id, invoice_id=False, shipping_id=False, context={}):
#        if not order_id:
#            return {}
#        val = {}
#        if not invoice_id:
#            val['partner_invoice_id'] = order_id
#        if not shipping_id:
#            val['partner_shipping_id'] = order_id
#        return {'value': val}

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context={}):
        if (not pricelist_id) or (not order_lines):
            return {}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'value': {'pricelist_id':pricelist_id}}

    ##cox gen2 
#    def onchange_shop_id(self, cr, uid, ids, shop_id):
#        v = {}
#        if shop_id:
#            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
#            v['project_id'] = shop.project_id.id
#            # Que faire si le client a une pricelist a lui ?
#            if shop.pricelist_id.id:
#                v['pricelist_id'] = shop.pricelist_id.id
#        return {'value': v}


    # This is False
#    def _picked_rate(self, cr, uid, ids, name, arg, context=None):
#        if not ids:
#            return {}
#        res = {}
#        tmp = {}
#        for id in ids:
#            tmp[id] = {'picked': 0.0, 'total': 0.0}
#        cr.execute('''SELECT
#                p.sale_id as sale_order_id, sum(m.product_qty) as nbr, mp.state as procurement_state, m.state as move_state, p.type as picking_type
#            FROM
#                stock_move m
#            LEFT JOIN
#                stock_picking p on (p.id=m.picking_id)
#            LEFT JOIN
#                procurement_order mp on (mp.move_id=m.id)
#            WHERE
#                p.sale_id IN %s GROUP BY m.state, mp.state, p.sale_id, p.type''', (tuple(ids),))
#
#        for item in cr.dictfetchall():
#            if item['move_state'] == 'cancel':
#                continue
#
#            if item['picking_type'] == 'in':#this is a returned picking
#                tmp[item['sale_order_id']]['total'] -= item['nbr'] or 0.0 # Deducting the return picking qty
#                if item['procurement_state'] == 'done' or item['move_state'] == 'done':
#                    tmp[item['sale_order_id']]['picked'] -= item['nbr'] or 0.0
#            else:
#                tmp[item['sale_order_id']]['total'] += item['nbr'] or 0.0
#                if item['procurement_state'] == 'done' or item['move_state'] == 'done':
#                    tmp[item['sale_order_id']]['picked'] += item['nbr'] or 0.0
#
#        for order in self.browse(cr, uid, ids, context=context):
#            if order.shipped:
#                res[order.id] = 100.0
#            else:
#                res[order.id] = tmp[order.id]['total'] and (100.0 * tmp[order.id]['picked'] / tmp[order.id]['total']) or 0.0
#        return res

#    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
#        res = {}
#        for sale in self.browse(cursor, user, ids, context=context):
#            if sale.invoiced:
#                res[sale.id] = 100.0
#                continue
#            tot = 0.0
#            for invoice in sale.invoice_ids:
#                if invoice.state not in ('draft', 'cancel'):
#                    tot += invoice.amount_untaxed
#            if tot:
#                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_untaxed or 1.00))
#            else:
#                res[sale.id] = 0.0
#        return res

#    def _invoiced(self, cursor, user, ids, name, arg, context=None):
#        res = {}
#        for sale in self.browse(cursor, user, ids, context=context):
#            res[sale.id] = True
#            invoice_existence = False
#            for invoice in sale.invoice_ids:
#                if invoice.state!='cancel':
#                    invoice_existence = True
#                    if invoice.state != 'paid':
#                        res[sale.id] = False
#                        break
#            if not invoice_existence:
#                res[sale.id] = False
#        return res

#    def _invoiced_search(self, cursor, user, obj, name, args, context=None):
#        if not len(args):
#            return []
#        clause = ''
#        sale_clause = ''
#        no_invoiced = False
#        for arg in args:
#            if arg[1] == '=':
#                if arg[2]:
#                    clause += 'AND inv.state = \'paid\''
#                else:
#                    clause += 'AND inv.state != \'cancel\' AND sale.state != \'cancel\'  AND inv.state <> \'paid\'  AND rel.order_id = sale.id '
#                    sale_clause = ',  sale_order AS sale '
#                    no_invoiced = True
#
#        cursor.execute('SELECT rel.order_id ' \
#                'FROM sale_order_invoice_rel AS rel, account_invoice AS inv '+ sale_clause + \
#                'WHERE rel.invoice_id = inv.id ' + clause)
#        res = cursor.fetchall()
#        if no_invoiced:
#            cursor.execute('SELECT sale.id ' \
#                    'FROM sale_order AS sale ' \
#                    'WHERE sale.id NOT IN ' \
#                        '(SELECT rel.order_id ' \
#                        'FROM sale_order_invoice_rel AS rel) and sale.state != \'cancel\'')
#            res.extend(cursor.fetchall())
#        if not res:
#            return [('id', '=', 0)]
#        return [('id', 'in', [x[0] for x in res])]

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('return.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

#####Customized Function

#    def _invoice_visible(self,cr,uid,ids,name,arg,context=None):
#        print"ids",ids
#        res = {}
#        obj = self.browse(cr,uid,ids[0])
#        mrp_repair_obj = self.pool.get('mrp.repair')
##        return_id = obj.id
##        print"return_id",return_id
#        if len(ids):
#            mrp_repair_id = mrp_repair_obj.search(cr,uid,[('sale_return_id','=',ids[0])])
#            print"mrp_repair_id",mrp_repair_id
#            if len(mrp_repair_id):
#                curr_state = mrp_repair_obj.browse(cr,uid,mrp_repair_id[0]).state
#                if curr_state=='2binvoiced':
#                    res[ids[0]]=True
#                    return res
#            else:
#                res[ids[0]]=False
#                print"res",res
#                return res
#
#        else:
#            res[ids[0]]=False
#            return res

    def recieve_confirm(self,cr,uid,ids,context=None):
        raise osv.except_osv(_('Error !'),_('Under development'))
        return True
    def check_return_line_qty(self,cr,uid,ids,context={}):
        if ids:
            id_obj = self.browse(cr,uid,ids[0])
            for return_line in id_obj.order_line:
                if return_line.sale_line_id:
                    cr.execute("select product_qty from stock_move where sale_line_id=%d and state!='done'"%(return_line.sale_line_id.id))
                    move_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if move_qty:
                        if return_line.product_uom_qty > move_qty[0]:
                            raise osv.except_osv(_('Warning!'),_('Please Change Quantity for %s because you cannot return more quantity than delivered quantity'%(return_line.product_id.name)))
    def return_confirm(self,cr,uid,ids,context=None):
        return_obj = self.browse(cr,uid,ids[0])
        linked_order = return_obj.linked_sale_order
        if linked_order:
#            duplicate_return = self.search(cr,uid,[('linked_sale_order','=',linked_order.id),('state','in',('progress','done')),('id','not in',ids)])
#            if duplicate_return:
#                raise osv.except_osv(_('Warning!'),_('Returns is Already Processed for %s')%(linked_order.name))
            self.check_return_line_qty(cr,uid,ids,context)
            if return_obj.amount_total > linked_order.amount_total:
                raise osv.except_osv(_('Warning!'),_('Total Of Return Order Cannot Be Greater than %s Total')%(linked_order.name))
            return {
                    'name': ('Receiving Of Goods'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'receive.goods',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                     'context': context
                }
    def change_delivery_qty(self,cr,uid,ids,context={}):
        cr.execute("select id,sale_line_id,product_qty from stock_move where sale_line_id in (select sale_line_id from return_order_line where order_id=%s) order by id desc"%(ids[0]))
        stock_mv_data = cr.dictfetchall()
        move_obj = self.pool.get('stock.move')
        id_obj = self.browse(cr,uid,ids[0])
        delivered_qty = 0.0
        existing_return = self.search(cr,uid,[('linked_sale_order','=',id_obj.linked_sale_order.id),('state','in',('progress','done')),('id','not in',ids)])
        if stock_mv_data:
            for each_move in stock_mv_data:
                if each_move.get('id'):
                    move_id_obj = move_obj.browse(cr,uid,each_move.get('id'))
                    if move_id_obj.picking_id.state == 'done':
                        delivered_qty += move_id_obj.product_qty
                    else:
                        move_ids  = []
                        sale_line_id = each_move.get('sale_line_id')
                        if sale_line_id:
                            move_ids.append(each_move.get('id'))
                            ##Sale Order Line Qty
                            cr.execute('select product_uom_qty from sale_order_line where id=%d'%(sale_line_id))
                            so_line_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if so_line_qty:
                                so_line_qty = so_line_qty[0]
                            ##Return Order Line qty
                            cr.execute('select product_uom_qty from return_order_line where sale_line_id=%d'%(sale_line_id))
                            return_line_qty = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if return_line_qty:
                                return_line_qty = return_line_qty[0]
                            if existing_return:
                                so_line_qty = each_move.get('product_qty')
                            #Final Qty
                            if so_line_qty and return_line_qty:
                                mv_qty = so_line_qty - return_line_qty
                                if delivered_qty > 0.0:
                                    mv_qty  = mv_qty - delivered_qty
                                cr.execute('select id from stock_move where parent_stock_mv_id = %d'%(each_move.get('id')))
                                child_move = filter(None, map(lambda x:x[0], cr.fetchall()))
                                if child_move:
                                    move_ids = move_ids + child_move
                                if move_ids:
                                    if mv_qty == 0.0:
                                        move_obj.action_cancel(cr,uid,move_ids,context)
                                    else:
                                        move_obj.write(cr,uid,move_ids,{'product_qty':abs(mv_qty)})
######End of Customized function
    _columns = {
        'name': fields.char('Return No', size=64, required=True,
            readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', readonly=True,required=True, states={'draft': [('readonly', False)]}),   ###cox gen2
#        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True,required=True, states={'draft': [('readonly', False)]}),   ###cox gen2
        'sale_id': fields.char('Sale ID', size=128),
        'cust_po': fields.char('Customer PO', size=128),
        'origin': fields.char('Source Document', size=64, help="Reference of the document that generated this sales order request."),
        'client_order_ref': fields.char('Customer Reference', size=64),
        'state': fields.selection([
            ('draft', 'Quotation'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'To Invoice'),
            ('progress', 'In Progress'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ], 'Order State', readonly=True, help="Gives the state of the quotation or sales order. \nThe exception state is automatically set when a cancel operation occurs in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception). \nThe 'Waiting Schedule' state is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
        'date_order': fields.date('Date', required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True, help="Date on which sales order is created."),
        'date_confirm': fields.date('Confirmation Date', readonly=True, select=True, help="Date on which sales order is confirmed."),
        'user_id': fields.many2one('res.users', 'Salesman', states={'draft': [('readonly', False)]}, select=True),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)]},change_default=True, select=True),
#        'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True, states={'draft': [('readonly', False)]}, help="Invoice address for current sales order."),
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, states={'draft': [('readonly', False)]}, help="Invoice address for current sales order."),
#        'partner_order_id': fields.many2one('res.partner.address', 'Ordering Contact', readonly=True,  states={'draft': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
        'partner_order_id': fields.many2one('res.partner', 'Ordering Contact', readonly=True,  states={'draft': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
#        'partner_shipping_id': fields.many2one('res.partner.address', 'Shipping Address', readonly=True, states={'draft': [('readonly', False)]}, help="Shipping address for current sales order."),
        'partner_shipping_id': fields.many2one('res.partner', 'Shipping Address', readonly=True, states={'draft': [('readonly', False)]}, help="Shipping address for current sales order."),
        'carrier_id':fields.many2one("delivery.carrier", "Shipping Methods", states={'draft': [('readonly', False)]}, help="Complete this field if you plan to invoice the shipping based on picking."),
#        'incoterm': fields.many2one('stock.incoterms', 'Incoterm', help="Incoterm which stands for 'International Commercial terms' implies its a series of sales terms which are used in the commercial transaction."),
        'picking_policy': fields.selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
            'Picking Policy', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="""If you don't have enough stock available to deliver all at once, do you accept partial shipments or not?"""),
        'order_policy': fields.selection([
            ('prepaid', 'Pay before delivery'),
            ('manual', 'Deliver & invoice on demand'),
            ('picking', 'Invoice based on deliveries'),
            ('postpaid', 'Invoice on order after delivery'),
        ], 'Invoice Policy', required=True, readonly=True, states={'draft': [('readonly', False)]},
                    help="""The Invoice Policy is used to synchronise invoice and delivery operations.
  - The 'Pay before delivery' choice will first generate the invoice and then generate the picking order after the payment of this invoice.
  - The 'Deliver & Invoice on demand' will create the picking order directly and wait for the user to manually click on the 'Invoice' button to generate the draft invoice based on the sale order or the sale order lines.
  - The 'Invoice on order after delivery' choice will generate the draft invoice based on sales order after all picking lists have been finished.
  - The 'Invoice based on deliveries' choice is used to create an invoice during the picking process."""),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True, states={'draft': [('readonly', False)]}, help="Pricelist for current sales order."),
#        'project_id': fields.many2one('account.analytic.account', 'Contract/Analytic Account', readonly=True, states={'draft': [('readonly', False)]}, help="The analytic account related to a sales order."),
        'order_line': fields.one2many('return.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'invoice_ids': fields.many2many('account.invoice', 'return_order_invoice_rel', 'order_id', 'invoice_id', 'Invoices', readonly=True,states={'draft': [('readonly', False)]},help="This is the list of invoices that have been generated for this sales order. The same sales order may have been invoiced in several times (by line for example)."),
        'picking_ids': fields.one2many('stock.picking', 'return_id', 'Related Picking', readonly=True, help="This is a list of picking that has been generated for this sales order."),
        'shipped': fields.boolean('Delivered', readonly=True, help="It indicates that the sales order has been delivered. This field is updated only after the scheduler(s) have been launched."),
#        'picked_rate': fields.function(_picked_rate, string='Picked', type='float'),
#        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
#        'invoiced': fields.function(_invoiced, string='Paid',
#            fnct_search=_invoiced_search, type='boolean', help="It indicates that an invoice has been paid."),
        'note': fields.text('Notes'),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'return.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'return.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'invoice_quantity': fields.selection([('order', 'Ordered Quantities'), ('procurement', 'Shipped Quantities')], 'Invoice on', help="The sale order will automatically create the invoice proposition (draft invoice). Ordered and delivered quantities may not be the same. You have to choose if you want your invoice based on ordered or shipped quantities. If the product is a service, shipped quantities means hours spent on the associated tasks.", required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term'),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'company_id': fields.related('warehouse_id','company_id',type='many2one',relation='res.company',string='Company',store=True,readonly=True),
        ####Return modified fields
#        'return_type': fields.selection([('warranty','Warranty'),('non-warranty','Non-Warranty'),('exchange', 'Exchange'),('car_return', 'Credit Return'),('30_day', '30 Days'),('destroy','Destroy')], 'Return Type', required=True),
        'return_type': fields.selection([('exchange', 'Exchange'),('car_return', 'Credit or cancel')], 'Return Type', required=True),
        'linked_sale_order':fields.many2one('sale.order','Sale Reference',select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'actual_linked_order':fields.many2one('sale.order','Actual Reference'),
#        'mrp_repair_ids': fields.one2many('mrp.repair', 'sale_return_id', 'Related Repair', readonly=True),
        'do_both_move' : fields.boolean('Create Incoming and Outgoing'),
        'manual_invoice_invisible' : fields.boolean('Create Manual Invoice'),
        'receive': fields.boolean('Receive'),
        'linked_serial_no' : fields.char('Serial No.',size=24),
#        'linked_serial_no':fields.many2one('stock.production.lot','Serial No.'),
#        'invoice_method':fields.selection([
#            ("b4repair","Before Repair"),
#            ("after_repair","After Repair")
#           ], "Invoice Method",
#            states={'draft':[('readonly',False)]}, readonly=True, help='This field allow you to change the workflow of the repair order. If value selected is different from \'No Invoice\', it also allow you to select the pricelist and invoicing address.'),
       'user_id': fields.many2one('res.users', 'Order Taker', readonly=True,states={'draft': [('readonly', False)]}, select=True),
       'customer_name': fields.char("Customer's Name",size=256, readonly=True, states={'draft': [('readonly', False)]}),
       'source_location': fields.many2one('stock.location','Source Location',readonly=True, states={'draft': [('readonly', False)]}),
       'incoming_exchange' : fields.boolean('Incoming Exchange'),
       'outgoing_exchange' : fields.boolean('Outgoing Exchange'),
       'ship_exchange_selection' : fields.selection([
            ("ship_before","Ship Before Receipt"),
            ("ship_after","Ship After return")
        ],"Ship Selection",
        states={'draft':[('readonly',False)]}, readonly=True, help='This field allows you to do the selection for shipping the return product before Incoming or after..'),
#        'exp_order_taker': fields.char('Expandables Order Taker', size=128),
#        'exp_job_id': fields.char('Expandables Job ID', size=128),
        'tax':fields.char('Tax', size=128)
#        'is_invoice_visible': fields.function(_invoice_visible, method=True, type='boolean', string='Invoice Visible'),
        #####complete
    }
    _defaults = {
        'picking_policy': 'direct',
        #'shop_id': 1,
        'warehouse_id': 1,
        'return_type':'car_return',
        'date_order': fields.date.context_today,
        'order_policy': 'manual',
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'return.order'),
        'invoice_quantity': 'order',
        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
#        'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and  self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['contact'])['contact'],
        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
#        'source_location' : _get_default_location,
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ]
    _order = 'name desc'
####Onchange customized function
    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def refresh_page(self,cr,uid,ids,context=None):
        return_line_ids = self.pool.get('return.order').browse(cr,uid,ids[0]).order_line
        if return_line_ids:
            line_ids_deleted = []
            for return_line_id in return_line_ids:
                line_ids_deleted.append(return_line_id.id)
            if line_ids_deleted:
                self.pool.get('return.order.line').unlink(cr, uid, line_ids_deleted, context=context)
        self.write(cr,uid,ids,{
            'linked_sale_order':False,
            'linked_serial_no':False,
            'partner_id':False,
            'customer_name':False,
                'partner_invoice_id': False,
                'partner_shipping_id':False,
#                'pricelist_id':False,
        'actual_linked_order':False})
        return True

    def onchange_serial_no(self, cr, uid, ids, linked_serial_no, name, linked_sale_order,actual_linked_order):
       obj_sale_order = self.pool.get('sale.order')
       line_obj = self.pool.get('sale.order.line')
       stock_move_obj = self.pool.get('stock.move')
       obj_stock_picking = self.pool.get('stock.picking')
       vals = {}
       if linked_serial_no:
           cr.execute("select id from stock_production_lot where name='%s'"%(linked_serial_no))
           serial_data = cr.dictfetchone()
           if not serial_data:
                vals['order_line'] = []
                vals['linked_sale_order'] = False
                vals['linked_serial_no'] = False
                vals['partner_id'] = False
                vals['partner_invoice_id'] = False
                vals['partner_order_id'] = False
                vals['partner_shipping_id'] = False
                vals['pricelist_id'] = False
                vals['actual_linked_order'] = False
                warning = { 'title': _('Warning!'),
                'message' : _('Serial Number is not Found') }
                return {'value': vals,'warning': warning}
           else:
                linked_serial_no_id = serial_data.get('id')
                cr.execute("select stock_move_id from stock_move_lot where production_lot=%s"%(linked_serial_no_id))
                stock_moves_val = cr.dictfetchone()
                if not stock_moves_val:
                    raise osv.except_osv(_('No delivery!'),_('This serial no is not assigned to any Move'))
                move_id = stock_moves_val.get('stock_move_id')
                if move_id:
                    stock_moves_ids = stock_move_obj.browse(cr, uid ,move_id)
                    if not stock_moves_ids:
                        return {'value': vals}
                    picking_out_id,picking_out_id_obj = False,False
                    picking_id = stock_moves_ids.picking_id
                    if picking_id.type=='out':
                        picking_out_id = picking_id.id
                    if not picking_out_id:
                        warn_msg = _("No delivery for this serial no.")
                        warning = {
                                'title': _('Alert !'),
                                'message': warn_msg }
                        res = {}
                        res['linked_serial_no'] = ''
                        return {'value': res, 'warning': warning}
                    picking_out_id_obj = obj_stock_picking.browse(cr,uid,picking_out_id)
#                    state_res = picking_out_id_obj.state
#                    if state_res!='done':
#                        warn_msg = _("Delivery is not yet done for the selected sale order")
#                        warning = {
#                                'title': _('Alert !'),
#                                'message': warn_msg }
#                        res = {}
#                        res['linked_serial_no'] = ''
#                        return {'value': res, 'warning': warning}
                    sale_id = picking_out_id_obj.sale_id.id
                    obj_sale_link_order = obj_sale_order.browse(cr, uid, sale_id)
                    if actual_linked_order:
                        linked_sale = picking_out_id_obj.sale_id.id
                        if actual_linked_order != linked_sale:
                            warn_msg = _("Selected Serial No. doesn\'t belong to the Sales Reference")
                            warning = {
                                'title': _('Alert !'),
                                'message': warn_msg }
                            res = {}
                            res['linked_serial_no'] = ''
                            return {'value': res, 'warning': warning}
                    vals = {
                        'name' : name,
                        'partner_id' : obj_sale_link_order.partner_id.id,
                        'partner_invoice_id' : obj_sale_link_order.partner_invoice_id.id,
    #                    'partner_order_id' : obj_sale_link_order.partner_order_id.id,
                        'partner_shipping_id' : obj_sale_link_order.partner_shipping_id.id,
                        'pricelist_id' : obj_sale_link_order.pricelist_id.id,
                        'linked_sale_order':obj_sale_link_order.id,
                        'actual_linked_order':obj_sale_link_order.id,
                    }
                    if obj_sale_link_order and stock_moves_ids:
                        if picking_out_id_obj.type == 'out':
                            product_obj = stock_moves_ids.product_id
                            limit = datetime.strptime(stock_moves_ids.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(product_obj.warranty))
                            limitless = limit.strftime('%Y-%m-%d')
                            cr.execute(''' select sol.*
                                            from sale_order_line sol,stock_move sm
                                            where sol.id = sm.sale_line_id and sm.id=%s
                                    '''%(stock_moves_ids.id))
                            order_line_val = cr.dictfetchone()
                            print "order_line_vals",order_line_val
                            if order_line_val:
                                order_line_vals = []
                                line_id_obj = line_obj.browse(cr,uid,order_line_val.get('id',False))
                                tax_ids = [c.id for c in line_id_obj.tax_id]
                                order_line_vals.append({'product_id':order_line_val.get('product_id',False),
                                        'name':order_line_val.get('name',''),
                                        'product_uom':order_line_val.get('product_uom',False),
                                        'product_uom_qty':order_line_val.get('product_uom_qty',False),
                                        'price_unit':order_line_val.get('price_unit',0.0),
                                        'discount':order_line_val.get('discount',0.0),
#                                        'order_id':ids[0],
                                        'serial_no':linked_serial_no,
                                        'tax_id':[(6, 0,tax_ids)],
                                        'state':'draft',
#                                        'type': order_line_val.get('type',''),
                                        'sale_line_id':order_line_val.get('id',False),
                                        'guarantee_limit_ro':limitless})
                                vals['order_line'] = order_line_vals

                return {'value': vals}
       else:
            vals['order_line'] = []
            vals['linked_sale_order'] = False
            vals['partner_id'] = False
            vals['partner_invoice_id'] = False
#            vals['partner_order_id'] = False
            vals['partner_shipping_id'] = False
            vals['pricelist_id'] = False
            vals['actual_linked_order'] = False
            return {'value': vals}
    def onchange_sale_order(self, cr, uid, ids, linked_sale_id,serial_no,line_ids):
       obj_sale_order = self.pool.get('sale.order')
       vals = {}
       if linked_sale_id:
           obj_sale_link_order = obj_sale_order.browse(cr, uid, linked_sale_id)
           vals = {
               'partner_id' : obj_sale_link_order.partner_id.id,
               'partner_invoice_id' : obj_sale_link_order.partner_invoice_id.id,
#               'partner_order_id' : obj_sale_link_order.partner_order_id.id,
               'partner_shipping_id' : obj_sale_link_order.partner_shipping_id.id,
               'pricelist_id' : obj_sale_link_order.pricelist_id.id,
               'payment_term' : obj_sale_link_order.payment_term.id,
               'linked_sale_order': linked_sale_id
           }
           if vals and obj_sale_link_order:
               order_line_vals = []
               for each_line in obj_sale_link_order.order_line:
                        tax_ids = [c.id for c in each_line.tax_id]
                        order_line_vals.append({'product_id':each_line.product_id.id,
                                    'name':each_line.name,
                                    'product_uom':(each_line.product_uom.id if each_line.product_uom else False),
                                    'product_uom_qty':each_line.product_uom_qty,
                                    'price_unit':each_line.price_unit,
                                    'discount':each_line.discount,
                                    'tax_id':[(6, 0,tax_ids)],
                                    'state':'draft',
#                                     'type': each_line.type,
                                     'sale_line_id':each_line.id
                                    })
               if order_line_vals:
                       vals['order_line'] = order_line_vals
           return {'value': vals}
       else:
           vals['order_line'] = []
           vals['linked_sale_order'] = False
           vals['partner_id'] = False
           vals['partner_invoice_id'] = False
#           vals['partner_order_id'] = False
           vals['partner_shipping_id'] = False
           vals['pricelist_id'] = False
           return {'value': vals}
    def unlink(self, cr, uid, ids, context=None):
        return_orders = self.read(cr, uid, ids, ['state','name'], context=context)
        unlink_ids = []
        for s in return_orders:
            if s.get('state'):
                if s['state'] in ['draft']:
                    unlink_ids.append(s['id'])
                else:
                    raise osv.except_osv(_('Invalid action !'), _('You cannot Delete Return orders whose state is not In Draft'))
        return super(return_order, self).unlink(cr, uid, unlink_ids, context)
    def insert_return_lines(self,cr,uid,ids,context=None):
        discount = 0
        return_obj = self.pool.get('return.order')
        return_order_line_obj = self.pool.get('return.order.line')
        stock_move_obj = self.pool.get('stock.move')
        stock_picking = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        return_id_obj = return_obj.browse(cr, uid, ids[0])
        linked_sale_obj = return_id_obj.linked_sale_order
        serial_no = return_id_obj.linked_serial_no
        cr.execute("select * from stock_production_lot where name='%s'"%(serial_no))
        serial_prod_lot_data = cr.dictfetchone()
        if (not serial_prod_lot_data) and not linked_sale_obj:
            raise osv.except_osv(_('Error!'),  _('Please Enter Proper Serial No Or Sales Order No'))
        if serial_prod_lot_data:
            cr.execute("select stock_move_id from stock_move_lot where production_lot=%s"%(serial_prod_lot_data['id']))
            stock_move = cr.dictfetchone()
            if stock_move:
                stock_move_id = stock_move.get('stock_move_id',False)
                if stock_move_id:
                    serial_move_obj = stock_move_obj.browse(cr, uid, stock_move_id)
                    product_obj = serial_move_obj.product_id
                    if serial_move_obj.picking_id:
                        if serial_move_obj.picking_id.type == 'out':
                            limit = datetime.strptime(serial_move_obj.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(product_obj.warranty))
                            limitless = limit.strftime('%Y-%m-%d')
                            cr.execute(''' select sol.*
                                    from sale_order_line sol,stock_move sm
                                    where sol.id = sm.sale_line_id and sm.id=%s
                            '''%(stock_move_id))
                            order_line_val = cr.dictfetchone()
                            return_order_line_obj.create(cr,uid,{
                                'product_id':order_line_val['product_id'],
                                'name':order_line_val['name'],
                                'product_uom':order_line_val['product_uom'],
                                'price_unit':order_line_val['price_unit'],
                                'discount':order_line_val['discount'],
                                'order_id':ids[0],
                                'serial_no':serial_no,
                                'guarantee_limit_ro':limitless,
                            })
        else:
            return_line_ids = return_id_obj.order_line
            actual_sale_id = return_id_obj.linked_sale_order.id
            if return_line_ids:
                for return_line_id in return_line_ids:
                    return_order_line_obj.unlink(cr, uid, [return_line_id.id], context=context)
            self.write(cr,uid,ids,{'actual_linked_order':actual_sale_id})
            reference_sale_id = linked_sale_obj.id
            current_picking = stock_picking.search(cr, uid, [('sale_id','=',reference_sale_id),('type','=','out')])
            if current_picking:
                for each_move_line in stock_picking.browse(cr, uid, current_picking[0]).move_lines:
                    limit = datetime.strptime(each_move_line.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(each_move_line.product_id.warranty))
                    limitless = limit.strftime('%Y-%m-%d')
                    serial_no = False
                    discount = 0
                    for each_sale_line in linked_sale_obj.order_line:
                        if each_sale_line.product_id.id == each_move_line.product_id.id:
                            discount = each_sale_line.discount
                            return_order_line_obj.create(cr,uid,{
                                'product_id':each_move_line.product_id.id,
                                'name':each_move_line.product_id.name,
                                'product_uom':each_move_line.product_uom.id,
                                'price_unit':each_sale_line.price_unit,
                                'discount':discount,
                                'order_id':ids[0],
                                'serial_no':serial_no,
                                'guarantee_limit_ro':limitless })
        return True

    def manual_invoice_return(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        return_obj = self.browse(cr,uid,ids[0])
        if not return_obj.order_line:
            raise osv.except_osv(_('Error!'),  _('Please Insert Return Order lines'))
        linked_order=return_obj.linked_sale_order
        if linked_order:
#            duplicate_return = self.search(cr,uid,[('linked_sale_order','=',linked_order.id),('state','in',('progress','done')),('id','not in',ids)])
#            if duplicate_return:
#                raise osv.except_osv(_('Warning!'),_('Returns is Already Processed for %s')%(linked_order.name))
            self.check_return_line_qty(cr,uid,ids,context)
            if return_obj.amount_total > linked_order.amount_total:
                raise osv.except_osv(_('Warning!'),_('Total Of Return Order Cannot Be Greater than %s Total')%(linked_order.name))
            if linked_order.auth_transaction_id:
                context['auth_transaction_id'] = linked_order.auth_transaction_id
                context['cc_number'] = linked_order.cc_number
                return {
                'name': ('Refund Payment'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'refund.customer.payment',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
            }
            else:
                journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                account_refund = self.pool.get('account.invoice')
                refund_invoice_id = account_refund.create(cr,uid,
                            {'partner_id':return_obj.partner_id.id,
#                            'address_invoice_id':return_obj.partner_invoice_id.id,
                            'currency_id':return_obj.pricelist_id.currency_id.id,
                            'account_id':return_obj.partner_id.property_account_receivable.id,
                            'name':return_obj.name,
#                            'address_contact_id':return_obj.partner_shipping_id.id,
                            'user_id':uid,
                            'journal_id':journal_id[0],
                            'type':'out_refund',
                            'return_id':ids[0],
                            'origin':return_obj.name,
                            'return_ref':return_obj.name+'/Credit_Return'
                })
                acc_invoice_line_obj = self.pool.get('account.invoice.line')
                for each_order_line in return_obj.order_line:
                    if each_order_line.account_id:
                        account_id = each_order_line.account_id.id
                    else:
                        if each_order_line.product_id.property_account_income.id:
                            account_id = each_order_line.product_id.property_account_income.id
                        else:
                            account_id = each_order_line.product_id.categ_id.property_account_income_categ.id
                    account_invoice_line = acc_invoice_line_obj.create(cr,uid,
                    {'product_id':each_order_line.product_id.id,
                     'name':each_order_line.name,
                     'quantity':each_order_line.product_uom_qty,
                     'price_unit':each_order_line.price_unit,
                     'uos_id':each_order_line.product_uom.id,
                     'account_id':account_id,
                     'discount':each_order_line.discount,
                     'invoice_id':refund_invoice_id,
                     'origin': return_obj.name,
                     'invoice_line_tax_id': [(6, 0, [x.id for x in each_order_line.tax_id])],
                    'note': each_order_line.notes,
                    })
                if refund_invoice_id:
                    netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                    account_refund.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
                    ###Code to Change Delivery Qty
                    
                    cr.execute("select id from stock_picking where group_id=%d and state != 'done'"%(return_obj.linked_sale_order.procurement_group_id.id))
                    picking_id=filter(None, map(lambda x:x[0], cr.fetchall()))
                    print"picking_idpicking_iddhpicking_id",picking_id
                    if picking_id:
                        self.change_delivery_qty(cr,uid,[return_obj.id],context)
                cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(ids[0],refund_invoice_id))
                if return_obj.receive:
                    state = 'done'
                else:
                    state = 'progress'
                self.write(cr,uid,[return_obj.id],{'manual_invoice_invisible': True,'state':state},context)
#####End of Onchange Customized function

return_order()

class return_order_line(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    def _number_packages(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            try:
                res[line.id] = int((line.product_uom_qty+line.product_packaging.qty-0.0001) / line.product_packaging.qty)
            except:
                res[line.id] = 1
        return res

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    _name = 'return.order.line'
    _description = 'Return Order Line'
    _columns = {
        'order_id': fields.many2one('return.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'name': fields.char('Description', size=256, required=True, select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'delay': fields.float('Delivery Lead Time', required=True, help="Number of days between the order confirmation the shipping of the products to the customer", readonly=True, states={'draft': [('readonly', False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
        'invoice_lines': fields.many2many('account.invoice.line', 'return_order_line_invoice_rel', 'order_line_id', 'invoice_id', 'Invoice Lines'),
        'invoiced': fields.boolean('Invoiced', readonly=True),
        'procurement_id': fields.many2one('procurement.order', 'Procurement'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price'), readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Sale Price')),
        'tax_id': fields.many2many('account.tax', 'return_order_tax', 'order_line_id', 'tax_id', 'Taxes', readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection([('make_to_stock', 'from stock'), ('make_to_order', 'on order')], 'Procurement Method', required=True, readonly=True, states={'draft': [('readonly', False)]},
            help="If 'on order', it triggers a procurement when the sale order is confirmed to create a task, purchase order or manufacturing order linked to this sale order line."),
#        'property_ids': fields.many2many('mrp.property', 'return_order_line_property_rel', 'order_id', 'property_id', 'Properties', readonly=True, states={'draft': [('readonly', False)]}),
#        'address_allotment_id': fields.many2one('res.partner.address', 'Allotment Partner'),
#        'address_allotment_id': fields.many2one('res.partner', 'Allotment Partner'),
        'product_uom_qty': fields.float('Quantity (UoM)', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS'), readonly=True, states={'draft': [('readonly', False)]}),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'product_packaging': fields.many2one('product.packaging', 'Packaging'),
        #'move_ids': fields.one2many('stock.move', 'sale_line_id', 'Inventory Moves', readonly=True),
        'discount': fields.float('Discount (%)', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)]}),
        'number_packages': fields.function(_number_packages, type='integer', string='Number Packages'),
        'notes': fields.text('Notes'),
        'th_weight': fields.float('Weight', readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')], 'State', required=True, readonly=True,
                help='* The \'Draft\' state is set when the related sales order in draft state. \
                    \n* The \'Confirmed\' state is set when the related sales order is confirmed. \
                    \n* The \'Exception\' state is set when the related sales order is set as exception. \
                    \n* The \'Done\' state is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' state is set when a user cancel the sales order related.'),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
        'salesman_id':fields.related('order_id', 'user_id', type='many2one', relation='res.users', store=True, string='Salesman'),
        'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'guarantee_limit_ro': fields.date('Guarantee limit', help="The guarantee limit is computed as: last move date + warranty defined on selected product. If the current date is below the guarantee limit, each operation and fee you will add will be set as 'not to invoiced' by default. Note that you can change manually afterwards."),
#        'description_reasons': fields.many2one('return.description', 'Return Reason'),
        'account_id': fields.many2one('account.account', 'Account', domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The income or expense account related to the selected product."),
#        'serial_no':fields.many2one('stock.production.lot','Serial No'),
        'serial_no' : fields.char('Serial No',size=15),
        'scheduled_ship_date': fields.date('Scheduled Ship Date'),
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Line ID'),
        'tax':fields.char('Tax', size=128),
    }
    _order = 'sequence, id'
    _defaults = {
        'product_uom' : _get_uom_id,
        'discount': 0.0,
        'delay': 0.0,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'sequence': 10,
        'invoiced': 0,
        'state': 'draft',
        'type': 'make_to_stock',
        'product_packaging': False,
        'price_unit': 0.0,
    }


    def product_packaging_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False,
                                   partner_id=False, packaging=False, flag=False, context=None):
        if not product:
            return {'value': {'product_packaging': False}}
        product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        pack_obj = self.pool.get('product.packaging')
        warning = {}
        result = {}
        warning_msgs = ''
        if flag:
            res = self.product_id_change(cr, uid, ids, pricelist=pricelist,
                    product=product, qty=qty, uom=uom, partner_id=partner_id,
                    packaging=packaging, flag=False, context=context)
            warning_msgs = res.get('warning') and res['warning']['message']

        products = product_obj.browse(cr, uid, product, context=context)
        if not products.packaging:
            packaging = result['product_packaging'] = False
        elif not packaging and products.packaging and not flag:
            packaging = products.packaging[0].id
            result['product_packaging'] = packaging

        if packaging:
            default_uom = products.uom_id and products.uom_id.id
            pack = pack_obj.browse(cr, uid, packaging, context=context)
            q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
#            qty = qty - qty % q + q
            if qty and (q and not (qty % q) == 0):
                ean = pack.ean or _('(n/a)')
                qty_pack = pack.qty
                type_ul = pack.ul
                if not warning_msgs:
                    warn_msg = _("You selected a quantity of %d Units.\n"
                                "But it's not compatible with the selected packaging.\n"
                                "Here is a proposition of quantities according to the packaging:\n"
                                "EAN: %s Quantity: %s Type of ul: %s") % \
                                    (qty, ean, qty_pack, type_ul.name)
                    warning_msgs += _("Picking Information ! : ") + warn_msg + "\n\n"
                warning = {
                       'title': _('Configuration Error !'),
                       'message': warning_msgs
                }
            result['product_uom_qty'] = qty

        return {'value': result, 'warning': warning}

    def product_id_change(self, cr, uid, ids, pricelist, product,linked_id=False,qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        warning = {}
        lang = lang or context.get('lang',False)
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('You have to select a customer in the sales form !\nPlease set one customer before choosing a product.'))
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}

        if not product:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty,'name':False,'description_reasons':False,'gaurantee_limit_ro':False}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')

        res = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
        result = res.get('value', {})
        warning_msgs = res.get('warning') and res['warning']['message'] or ''
        product_obj = product_obj.browse(cr, uid, product, context=context)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        if product_obj.description_sale:
            result['notes'] = product_obj.description_sale
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['delay'] = (product_obj.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
            result.update({'type': product_obj.procure_method})

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}

        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        compare_qty = float_compare(product_obj.virtual_available * uom2.factor, qty * product_obj.uom_id.factor, precision_rounding=product_obj.uom_id.rounding)
#        if (product_obj.type=='product') and int(compare_qty) == -1 \
#          and (product_obj.procure_method=='make_to_stock'):
#            warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
#                    (qty, uom2 and uom2.name or product_obj.uom_id.name,
#                     max(0,product_obj.virtual_available), product_obj.uom_id.name,
#                     max(0,product_obj.qty_available), product_obj.uom_id.name)
#            warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warn_msg = _("Couldn't find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }
        if linked_id:
#            print"linked_id",linked_id
#            print"product",product
            picking_id = self.pool.get('stock.picking').search(cr,uid,[('sale_id','=',linked_id)])
            move_ids = self.pool.get('stock.move').search(cr,uid,[('picking_id','=',picking_id),('product_id','=',product)])
#            date_exp = self.pool.get('stock.move').browse(cr,uid,move_id[0]).date_expected
            if len(move_ids):
                move = self.pool.get('stock.move').browse(cr, uid, move_ids[0])
                product = self.pool.get('product.product').browse(cr, uid, product)
                limit = datetime.strptime(move.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(product.warranty))
                result['guarantee_limit_ro'] = limit.strftime('%Y-%m-%d')
        return {'value': result, 'domain': domain, 'warning': warning}

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        res = self.product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, context=context)
        if 'product_uom' in res['value']:
            del res['value']['product_uom']
        if not uom:
            res['value']['price_unit'] = 0.0
        return res
    def unlink(self, cr, uid, ids, context=None):
#        print"ids",ids
        if context is None:
            context = {}
        """Allows to delete sales order lines in draft,cancel states"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['draft', 'cancel']:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sales order line which is in state \'%s\'!') %(rec.state,))
        return super(return_order_line, self).unlink(cr, uid, ids, context=context)
return_order_line()

#class return_description(osv.osv):
#    _name = 'return.description'
#    _columns = {
#        'name': fields.char('Reason Code', size=64),
#        'return_reason':fields.char('Return Reason',size=512),
#    }
#return_description()
#
#class failure_analysis(osv.osv):
#    _name='failure.analysis'
#    _columns={
#        'name': fields.char('FA Reason', size=64),
#        'code': fields.char('FA Code', size=512),
#    }
#failure_analysis()
 
