from openerp.osv import fields, osv
from openerp.tools.translate import _

class purchase_order(osv.osv):
    _inherit='purchase.order'
    
#    def _invoiced(self, cursor, user, ids, name, arg, context=None):
#        print"coxxxxxxxxxxxxxxxxxxx"
#        res = {}
#        for purchase in self.browse(cursor, user, ids, context=context):
#            for line in purchase.order_line :
#                if line.state != 'cancel':
#                    res[purchase.id] = line.invoiced 
#        return res
#    
#    
#    _columns={
#    'invoiced': fields.function(_invoiced, string='Invoice Received', type='boolean', copy=False,
#                                    help="It indicates that an invoice has been validated"),
#                                    
#    }
#    
#    ###Function is inherited from Sales Avatax because to prevent tax calculation for
#    #ecommerce orders and also to calculate tax based on the retail and call center locations
#    def compute_tax(self, cr, uid, ids, context=None):
#        avatax_config_obj = self.pool.get('account.salestax.avatax')
#        account_tax_obj = self.pool.get('account.tax')
#        avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid)
#        for order in self.browse(cr, uid, ids):
#            print"order.location_id.",order.location_id
#            tax_amount = 0.0
#            if avatax_config and not avatax_config.disable_tax_calculation and \
#            avatax_config.default_tax_schedule_id.id == order.partner_id.tax_schedule_id.id:
#                address = (order.location_id.partner_id if order.location_id else False)
#                if not address:
#                    raise osv.except_osv(_('Error !'),_('Please Specify Address Location for %s')%(order.location_id.name))
#                else:
#                    address =  address.id
#                lines = self.create_lines(cr, uid, order.order_line)
#                if lines:
#                    if order.date_confirm:
#                        order_date = (order.date_confirm).split(' ')[0]
#                    else:
#                        order_date = (order.date_order).split(' ')[0]
#                    tax_amount = account_tax_obj._check_compute_tax(cr, uid, avatax_config, order_date,
#                                                                    order.name, 'SalesOrder', order.partner_id, address,
#                                                                    order.partner_invoice_id.id, lines, order.shipcharge, order.user_id,
#                                                                    context=context).TotalTax
#                self.write(cr, uid, [order.id], {'tax_amount': tax_amount, 'order_line': []})
#                    
#                    
#    def wkf_confirm_order(self, cr, uid, ids, context=None):
#        todo = []
#        for po in self.browse(cr, uid, ids, context=context):
#            if not any(line.state != 'cancel' for line in po.order_line):
#                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
#            if po.invoice_method == 'picking' and not any([l.product_id and l.product_id.type in ('product', 'consu') and l.state != 'cancel' for l in po.order_line]):
#                raise osv.except_osv(
#                    _('Error!'),
#                    _("You cannot confirm a purchase order with Invoice Control Method 'Based on incoming shipments' that doesn't contain any stockable item."))
#            for line in po.order_line:
#                if line.state=='draft':
#                    todo.append(line.id)      
#        self.compute_tax(cr, uid, ids, context=context)##Function to Get tax from the Avalara
#        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
#        for id in ids:
#            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})
#        return True
    
    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """Prepare the dict of values to create the new invoice for a
           purchase order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: purchase.order record to invoice
           :param list(int) line_ids: list of invoice line IDs that must be
                                      attached to the invoice
           :return: dict of value to create() the invoice
        """
        journal_ids = self.pool['account.journal'].search(
                            cr, uid, [('type', '=', 'purchase'),
                                      ('company_id', '=', order.company_id.id)],
                            limit=1)
        if not journal_ids:
            raise osv.except_osv(
                _('Error!'),
                _('Define purchase journal for this company: "%s" (id:%d).') % \
                    (order.company_id.name, order.company_id.id))
        return {
            'name': order.partner_ref or order.name,
            'reference': order.partner_ref or order.name,
            'account_id': order.partner_id.property_account_payable.id,
            'type': 'in_invoice',
            'partner_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, line_ids)],
            'origin': order.name,
            'fiscal_position': order.fiscal_position.id or False,
            'payment_term': order.payment_term_id.id or False,
            'company_id': order.company_id.id,
            'location_address_id':order.location_id.partner_id.id if order.location_id.partner_id else False
        }
        
        
    
        
purchase_order()