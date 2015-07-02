# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from calendar import monthrange
from datetime import date, datetime, timedelta
import calendar
from openerp import netsvc

class sale_order_line(osv.osv):
    _inherit ="sale.order.line"
    def _prepare_invoice_line_cox(self, cr, uid, line, account_id=False,vals={}, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sale order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).
           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        
        def _get_line_qty(line):
            if line.product_uos:
                return line.product_uos_qty or 0.0
            return line.product_uom_qty

        def _get_line_uom(line):
            if line.product_uos:
                return line.product_uos.id
            return line.product_uom.id
#        def _get_line_qty(line):
#            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
#                if line.product_uos:
#                    return line.product_uos_qty or 0.0
#                return line.product_uom_qty
#            else:
#                return self.pool.get('procurement.order').quantity_get(cr, uid,
#                        line.procurement_id.id, context=context)
#
#        def _get_line_uom(line):
#            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
#                if line.product_uos:
#                    return line.product_uos.id
#                return line.product_uom.id
#            else:
#                return self.pool.get('procurement.order').uom_get(cr, uid,
#                        line.procurement_id.id, context=context)
        if not account_id:
            if context.get('new_pacakge_id'):
                product_id_brw = context.get('new_pacakge_id')
            else:
                product_id_brw = line.product_id
            if product_id_brw:
                account_id = product_id_brw.product_tmpl_id.property_account_income.id
                if not account_id:
                    account_id = product_id_brw.categ_id.property_account_income_categ.id
                if not account_id:
                    raise osv.except_osv(_('Error !'),
                            _('There is no income account defined for this product: "%s" (id:%d)') % \
                                (product_id_brw.name, product_id_brw.id,))
            else:
                prop = self.pool.get('ir.property').get(cr, uid,
                        'property_account_income_categ', 'product.category',
                        context=context)
                account_id = prop and prop.id or False
        uosqty = _get_line_qty(line)
        uos_id = _get_line_uom(line)
        fpos = line.order_id.fiscal_position or False
        account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
        if context.get('giftcard',False):
	    product_id_brw=line.product_id
        if not account_id:
            raise osv.except_osv(_('Error !'),
                        _('There is no income category account defined in default Properties for Product Category or Fiscal Position is not defined !'))
        if product_id_brw:
            vals.update({
            'origin': (line.order_id.name if line.order_id else line.so_id.name),
            'account_id': account_id,
            'quantity': uosqty,
            'uos_id': uos_id,
            'product_id': (product_id_brw.id or False),
            })
        return vals

sale_order_line()
class sale_order(osv.osv):
    _inherit='sale.order'
    def action_invoice_merge(self, cr, uid,maerge_invoice_data, date_inv, nextmonth, service_start_date,customer_profile_id=False, context=None):
        returnval,res,invoice_lines,sale_ids,invoice_ref,invoice_vals= False,False,[],[],'',{}
	invoice = self.pool.get('account.invoice')
        policy_obj=self.pool.get('res.partner.policy')
        invoice_line_obj = self.pool.get('account.invoice.line')
        obj_sale_order_line = self.pool.get('sale.order.line')
        partner_obj = self.pool.get('res.partner')
        partner_id_obj = context.get('partner_id_obj',False)
        if partner_id_obj:
            journal_ids = self.pool.get('account.journal').search(cr, uid,
                [('type', '=', 'sale'), ('company_id', '=', partner_id_obj.company_id.id)],limit=1)
            for service_data in maerge_invoice_data:
                vals={}
#		if context.get('new_pacakge_id',False):
#		    context.pop('new_pacakge_id')
                policy_brw = service_data.get('policy_id_brw',False)
                line=obj_sale_order_line.browse(cr,uid,service_data.get('line_id',False))
                ###### changes for recurring price by yogita
                if line:
                    res_so_id=policy_obj.browse(cr,uid,service_data.get('policy_id',False))
                    if (res_so_id.recurring_price)>0.0:
                       product_price=res_so_id.recurring_price
                    else:
                       product_price=line.product_id.list_price
                 ###########
#                product_price = policy_brw.product_id.list_price
                unit_price = product_price
                if context.get('giftcard',False):
                    unit_price=context.get('facevalue',False)
                if policy_brw.up_down_service and policy_brw.extra_days:
                    invoice_lines+= policy_obj.service_tier_calculation(cr,uid,policy_brw,unit_price,date_inv,context)
                    cr.execute("update res_partner_policy set adv_paid=False,extra_days=0,next_billing_date= '%s' where id =%s"%(nextmonth,policy_brw.id))
		    cr.commit()
                else:
                    context['new_pacakge_id'] = policy_brw.product_id
		    print"contextttttttttttttttttttttttttt",context
                    data = {'name': policy_brw.product_id.name,
                            'discount':0.0,
                            'invoice_line_tax_id':[],
                            'line_id': policy_brw.sale_line_id
                            }
                    data.update({'price_unit':unit_price})
                    if service_data.get('extra_days', 0)>0  and not context.get('giftcard',False):
                        extra_days=service_data.get('extra_days')
                        days=calendar.monthrange(date_inv.year,date_inv.month)[1]
#                        days=366 if calendar.isleap(date_inv.year) else 365
#                        partial_price=(unit_price*12/days)*int(extra_days)
                        partial_price=(unit_price/days)*int(extra_days)
                        data.update({'price_unit':partial_price})
                        policy_obj.write(cr,uid,service_data['policy_id'],{'extra_days':0,'adv_paid':True})
                    if context.get('giftcard',False):
                        account_id=context.get('account_id',False)
                        print "account_idaccount_idaccount_id546t457578678",account_id
                    else:
                        account_id=False
                    vals = obj_sale_order_line._prepare_invoice_line_cox(cr, uid, line, account_id, data, context)
                    if vals:
                        last_amount_charged=vals.get('price_unit',False)
                        print"last_amount_chargedlast_amount_chargedlast_amount_charged",last_amount_charged
                        cr.execute("update res_partner_policy set adv_paid=False,next_billing_date= '%s',last_amount_charged=%s where id =%s"%(nextmonth,last_amount_charged,policy_brw.id))
                        invoice_lines+=[vals]
                invoice_ref+= 'RB'+ service_data.get('order_name','') + '|'
                if not service_data.get('sale_id',False) in sale_ids:
                       sale_ids.append(service_data.get('sale_id',False))
            if invoice_lines:
                address = False
                com_obj = self.pool.get('res.company')
                search_company = com_obj.search(cr,uid,[])
                if search_company:
                    search_company_id = com_obj.browse(cr,uid,search_company[0])
                    address = partner_obj.address_get(cr, uid, [search_company_id.partner_id.id], ['default'])
                    if address:
                        address = address.get('default',False)
		current_date = datetime.today()
                invoice_vals.update({
                    'origin': str(invoice_ref[:-1]),
                    'name': (partner_id_obj.ref if partner_id_obj.ref else invoice_ref[:-1]),
                    'type': 'out_invoice',
                    'reference': invoice_ref[:-1],
                    'account_id': partner_id_obj.property_account_receivable.id,
                    'partner_id': partner_id_obj.id,
                    'journal_id': journal_ids[0],
                    'currency_id':  partner_id_obj.company_id.currency_id.id,
                    'company_id': partner_id_obj.company_id.id,
                    'date_invoice':str(current_date),
                    'auth_transaction_id':False,
                    'authorization_code':False,
                    'customer_payment_profile_id':customer_profile_id,
                    'auth_transaction_type':'profileTransAuthCapture',
                    'cc_number':context.get('cc_number'),
                    'auth_respmsg':False,
                    'location_address_id': address,
                    'next_billing_date':str(nextmonth),
                    'recurring':True,
                })
                res=invoice.create(cr,uid,invoice_vals)
		print"ressssssssssssssssssss",res
                if res:
                    for invoice_line in invoice_lines:
                        sale_line_id=invoice_line.get('line_id',False)
                        del invoice_line['line_id']
                        invoice_line.update({'invoice_id':res})
                        inv_line_id=invoice_line_obj.create(cr,uid,invoice_line,context)
                        if inv_line_id:
                            cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%s,%s)', (sale_line_id, inv_line_id))
                    context['customer_profile_id'] = partner_id_obj.customer_profile_id
		    check_trans=""
                    check_trans = self.pool.get("authorize.net.config").check_authorize_net(cr,uid,'account.invoice',res,context)
                    if not context.get('giftcard',False) and not check_trans:
                        returnval=invoice.charge_customer_recurring_or_etf(cr,uid,[res],context)
                    else:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'account.invoice', res, 'invoice_open', cr)
                        returnval = invoice.make_payment_of_invoice(cr, uid, [res], context=context)
                        invoice.write(cr,uid,res,{'procesesd_by':'giftcard'})
                for sale_id in sale_ids:
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (sale_id, res))
            if returnval:
                if res:
                    return res
            else:
                return False
        return False
sale_order()
