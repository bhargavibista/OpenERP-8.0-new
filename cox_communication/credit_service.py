
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class credit_service(osv.osv):
    _name = 'credit.service'
    def unlink(self, cr, uid, ids, context=None):
        credit_orders = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in credit_orders:
            if s.get('state'):
                if s['state'] in ['draft']:
                    unlink_ids.append(s['id'])
                else:
                    raise osv.except_osv(_('Invalid action !'), _('You cannot Delete Done Orders'))
        return super(credit_service, self).unlink(cr, uid, unlink_ids, context)
	
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
#                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('credit.service.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'name': fields.char('Credit No', size=64, required=True,
            readonly=True, states={'draft': [('readonly', False)]}, select=True),
        'warehouse_id':fields.many2one('stock.warehouse','Warehouse',readonly=True,required=True,states={'draft': [('readonly', False)]}),
#        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True,required=True, states={'draft': [('readonly', False)]}),
        'sale_id': fields.char('Sale ID', size=128),
        'date_order': fields.date('Date', required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True, help="Date on which sales order is created."),
        'date_confirm': fields.date('Confirmation Date', readonly=True, select=True, help="Date on which sales order is confirmed."),
        'user_id': fields.many2one('res.users', 'Salesman', states={'draft': [('readonly', False)]}, select=True),
        'partner_id':fields.many2one('res.partner','Customer', readonly=True, states={'draft':[('readonly',False)]}),
##        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, states={'draft': [('readonly', False)]}, help="Invoice address for current sales order."),
        'partner_order_id': fields.many2one('res.partner', 'Ordering Contact', readonly=True,  states={'draft': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
        'partner_shipping_id': fields.many2one('res.partner', 'Shipping Address', readonly=True, states={'draft': [('readonly', False)]}, help="Shipping address for current sales order."),
        'order_line': fields.one2many('credit.service.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.related('warehouse_id','company_id',type='many2one',relation='res.company',string='Company',store=True,readonly=True),
        'invoice_ids': fields.many2many('account.invoice', 'credit_service_invoice_rel', 'order_id', 'invoice_id', 'Invoices', readonly=True,states={'draft': [('readonly', False)]},help="This is the list of invoices that have been generated for this sales order. The same sales order may have been invoiced in several times (by line for example)."),
        'state': fields.selection([
            ('draft', 'Quotation'),
            ('done', 'Done'),
            ], 'Order State', readonly=True, help="Gives the state of service order.", select=True),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'credit.service': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'credit.service.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'credit.service': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'credit.service.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'credit.service': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'credit.service.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True, states={'draft': [('readonly', False)]}, help="Pricelist for current sales order."),
        'user_id': fields.many2one('res.users', 'Order Taker', readonly=True,states={'draft': [('readonly', False)]}, select=True),
        'customer_name': fields.char("Customer's Name",size=256, readonly=True, states={'draft': [('readonly', False)]}),
        'cc_number':fields.char('CC Number',size=64,readonly=True),
        'auth_transaction_id' :fields.char('Transaction ID', size=40,readonly=True),
        'auth_respmsg' :fields.text('Response Message',readonly=True),
        'customer_profile': fields.char('Customer Profile',size=64,readonly=True),
        'customer_payment_profile_id': fields.char('Payment Profile ID',size=64,readonly=True),
        'note': fields.text('Notes'),
	'cancellation_type':fields.selection([('credits','Credits Only'),('cancel','Cancel Only'),('credits_cancel','Credit and Cancel')],'Cancellation Type'),

    }
    _defaults = {
        'name':lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'credit.service'),
        'warehouse_id': 1,
        'state':'draft',
        'date_order': fields.date.context_today,
        'user_id': lambda obj, cr, uid, context: uid,
#        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'credit.service'),
#        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
#        'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and  self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['contact'])['contact'],
#        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
#        'source_location' : _get_default_location,
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ]
    _order = 'name desc'
####Onchange customized function
    def button_dummy(self, cr, uid, ids, context=None):
        return True

#    def onchange_shop_id(self, cr, uid, ids, shop_id):
#        v = {}
#        if shop_id:
#            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id)
#            v['project_id'] = shop.project_id.id
#            # Que faire si le client a une pricelist a lui ?
#            if shop.pricelist_id.id:
#                v['pricelist_id'] = shop.pricelist_id.id
#        return {'value': v}

    def onchange_partner_id(self, cr, uid, ids, part):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'partner_order_id': False, 'payment_term': False, 'fiscal_position': False, 'customer_name':False}}
	if ids and part:
            cr.execute("select id from credit_service_line where order_id=%s"%(ids[0]))
            search_credit_line =filter(None, map(lambda x:x[0], cr.fetchall()))
            if search_credit_line:
                self.pool.get('credit.service.line').unlink(cr,uid,search_credit_line,{})
        partner_obj = self.pool.get('res.partner')
        addr = partner_obj.address_get(cr, uid, [part], ['delivery', 'invoice', 'contact'])
        part = partner_obj.browse(cr, uid, part)
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
#        payment_term = part.property_payment_term and part.property_payment_term.id or False
#        fiscal_position = part.property_account_position and part.property_account_position.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
#        property_payment_term = part.property_payment_term.id
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
#            'payment_term': payment_term,
#            'fiscal_position': fiscal_position,
            'user_id': dedicated_salesman,
            'customer_name': part.name,
            'order_line':[]
#            'payment_term' : property_payment_term or '',
        }
        if pricelist:
            val['pricelist_id'] = pricelist
            val['order_line'] = []
            val['amount_untaxed'] = 0.00
            val['amount_tax'] = 0.00
            val['amount_total'] = 0.00
        return {'value': val}

    def api_response(self,cr,uid,ids,response,customer_profile,payment_profile_id,cc_number,context={}):
        split = response.split(',')
        transaction_id = split[6]
        transaction_message = split[3]
        vals = {}
        if transaction_message:
            vals.update({'auth_respmsg':transaction_message})
        if transaction_id:
            vals.update({'auth_transaction_id':transaction_id})
        if customer_profile:
            vals.update({'customer_profile':customer_profile})
        if payment_profile_id:
            vals.update({'customer_payment_profile_id':payment_profile_id})
        if cc_number:
            vals.update({'cc_number':cc_number})
        if vals:
            self.write(cr,uid,ids,vals)

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context={}):
        if (not pricelist_id) or (not order_lines):
            return {}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning}

    def return_confirm(self,cr,uid,ids,context={}):
        if ids:
            credit_object=self.browse(cr,uid,ids[0])
            partner_id=credit_object.partner_id
            order_lines=credit_object.order_line
            invoice_id,service_to_deactivate,invoice_line_ids=[],[],{}
            for line in order_lines:
                sale_line_id=line.service_id.sale_line_id
                #Code to search recurring invoice
                cr.execute("""select max(a.id),a.state
                           from account_invoice a 
                           join account_invoice_line l on (a.id=l.invoice_id)
                           join sale_order_line_invoice_rel sl on (l.id=sl.invoice_id)
                           and sl.order_line_id=%s and a.partner_id=%s group by a.state"""%(str(sale_line_id),str(partner_id.id)))
                result=cr.fetchone()
                if result:
                    if result[1] == 'paid':
                        invoice_id = [result[0]]
                #Code to search main invoice:
		else:
                    cr.execute("select max(id) "
                           "from account_invoice where origin='%s'"%(line.service_id.sale_order))
                    invoice_id=list(cr.fetchone())
                if invoice_id and invoice_id[0]:
                    if invoice_id[0] in invoice_line_ids:
                        invoice_line_ids[invoice_id[0]]+=[line.id]
                    else:
                        invoice_line_ids[invoice_id[0]]=[line.id]
                    service_to_deactivate+=[line.service_id.id]
#            if invoice_line_ids:
            context.update({'active_ids':ids,'active_model':'credit.service','active_id':ids[0],'invoice_line_ids':invoice_line_ids,'service_to_deactivate':service_to_deactivate})
            return {'name':_("Invoice Refund"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'refund.against.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,}
#            else:
#                raise osv.except_osv(_("Error"),
#                        _(("No Inovice exist for customer %s. Please check sale order of selected service"))%(partner_id.name))
        return {'type': 'ir.actions.act_window_close'}

credit_service()

class credit_service_line(osv.osv):
    _name = 'credit.service.line'
    _description = 'Credit Service Line'

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

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False
    def onchange_return_reason(self,cr,uid,ids,return_reason,context={}):
        res = {}
        if return_reason:
            title = self.pool.get('reasons.title').browse(cr,uid,return_reason)
            res['notes'] = title.name
        return {'value':res}  

    _columns = {
        'order_id': fields.many2one('credit.service', 'Credit Reference', required=True, ondelete='cascade', select=True),
        'name': fields.char('Description', size=256, required=True, select=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'product_id': fields.many2one('product.product', 'Part ID', domain=[('sale_ok', '=', True)], change_default=True),
#        'invoice_lines': fields.many2many('account.invoice.line', 'credit_service_line_invoice_rel', 'order_line_id', 'invoice_id', 'Invoice Lines'),
#        'invoiced': fields.boolean('Invoiced', readonly=True),
        'service_id':fields.many2one('res.partner.policy','Active Service'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Sale Price')),
        'tax_id': fields.many2many('account.tax', 'credit_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'product_uom_qty': fields.float('Quantity (UoM)', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'discount': fields.float('Discount (%)', digits=(16, 2)),
        'state': fields.selection([('draft', 'Draft'),('done', 'Done')], 'State', required=True, readonly=True,
                help='* The \'Draft\' state is set when the related sales order in draft state. \
                    \n* The \'Done\' state is set when the sales order line has been picked.'),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
        'salesman_id':fields.related('order_id', 'user_id', type='many2one', relation='res.users', store=True, string='Salesman'),
        'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'start_date': fields.date('Started At'),
        'account_id': fields.many2one('account.account', 'Account', domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The income or expense account related to the selected product."),
        'notes': fields.text('Cancellation/Credit Reason'),
	'return_reason': fields.many2one('reasons.title','Cancellation/Credit Reason'),
    }
    _order = 'sequence, id'
    _defaults = {
        'product_uom' : _get_uom_id,
        'discount': 0.0,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'sequence': 10,
        'state': 'draft',
        'price_unit': 0.0,
    }
    def onchange_price_unit(self,cr,uid,ids,price_unit,service_id,partner_id,context={}):
        res,count = {},0
        res['value'] = {}
        if service_id and price_unit:
            acc_obj=self.pool.get('account.invoice')
            service_id_obj=self.pool.get('res.partner.policy').browse(cr,uid,service_id)
         #   last_amount_charged= service_id_obj.last_amount_charged
            acct_no=acc_obj.search(cr,uid,[('partner_id','=',partner_id),('origin','ilike',service_id_obj.sale_order)])
            if acct_no:
                for acc_data in acc_obj.browse(cr,uid,acct_no):
                    for acc_data_new in acc_data.invoice_line:
			if acc_data_new.origin:
	                        if 'RB' in acc_data_new.origin:
        	                        if acc_data_new.product_id.id == service_id_obj.product_id.id:
                	                    count+=acc_data_new.price_subtotal
	                        else:
        	                        count += acc_data.amount_total
            if price_unit > count:
                warning = {
                'title': _('Warning!'),
                'message' : _('Please correct the Entered Price.')
                    }
                res['warning'] =  warning
                res['value']['price_unit'] = 0.0
        return res
    def onchange_service_id(self,cr,uid,ids,service_id,context={}):
        res,credit_service_lines,selected_service_id={},{},[]
        res['value'] = {}
        warning,warning_mesg = {'title': _('Warning!')},''
        policy_object=self.pool.get('res.partner.policy')
        service_line_obj=self.pool.get('credit.service.line')
        if service_id:
            policy_object=policy_object.browse(cr,uid,service_id)
#            if (policy_object.cancel_date) and (not policy_object.active_service):
            if (not policy_object.active_service) and (policy_object.cancel_date or policy_object.return_date or policy_object.suspension_date):
                warning_mesg += _('Service is already cancelled for %s.'%(policy_object.sale_order)) + "\n\n"
            for each_line in context.get('order_line'):
                if each_line[0] == 0:
                    selected_service_id.append(each_line[2].get('service_id'))
                else:
                    selected_service_id.append(service_line_obj.browse(cr,uid,each_line[1]).service_id.id)
            if service_id in selected_service_id:
                warning_mesg += _('Service is already Selected.') + "\n\n"
                res['value']['service_id'] = False
                res['value']['name'] = False
                res['value']['price_unit'] = 0.0
                res['value']['product_id'] = False
                res['value']['product_uom_qty'] = 0.0
            else:
                credit_service_lines={
                    'product_id':policy_object.product_id.id,
                    'name':(policy_object.sale_order if policy_object.sale_order else '')+'|'+(policy_object.product_id.name if policy_object.product_id else ''),
                    'product_uom':(policy_object.product_id.uom_id.id if policy_object.product_id.uom_id.id else False),
                    'price_unit':policy_object.product_id.list_price,
                    'state':'draft',
                    'product_uom_qty':1,
                    'start_date':policy_object.start_date
                    }
                res['value'].update(credit_service_lines)
            if warning_mesg:
                warning.update({'message' : warning_mesg})
                res['warning'] =  warning
        return res
credit_service_line()
