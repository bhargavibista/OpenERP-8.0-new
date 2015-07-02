# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
#import openerp.netsvc
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import time
from openerp import netsvc

class refund_against_invoice(osv.osv_memory):
    _name = "refund.against.invoice"
    _columns={
    'invoice_ids': fields.many2many('account.invoice', 'service_credit_invoice_rel', 'credit_id', 'invoice_id', 'Invoices',readonly=True),
    }
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res={}
        if context.get('invoice_line_ids',[]):
            invoice_ids=[]
            invoice_lines=context.get('invoice_line_ids',[])
            for invoice in invoice_lines:
                invoice_ids+=[int(invoice)]
            res.update({'invoice_ids':invoice_ids})
        return res
    
    def cancel_service(self,cr,uid,ids,context={}):
        active_id=ids[0]
#	print"context",context
        active_model='return.order'
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        final_dict = {}
        partner_obj=self.pool.get('res.partner')
#        if active_model=='return.order':
        return_object=self.pool.get(active_model).browse(cr,uid,active_id)
        so_obj = self.pool.get('sale.order')
        policy_obj = self.pool.get('res.partner.policy')
        order_lines=return_object.order_line
        if len(order_lines)!=0:
            cancel_service = self.pool.get('cancel.service')                
            if not return_object.return_reason:
                raise osv.except_osv(_('Error !'),_('Please Specify Reason for Cancellation in Return Order Line'))
                for line in order_lines:
                    if not line.notes:
                        raise osv.except_osv(_('Error !'),_('Please Specify Reason for Cancellation in Credit Service Line'))
                    need_to_update_data = []
                result = cancel_service.cancel_service(cr,uid,ids,return_object.service_id,return_object.partner_id.billing_date,line,context)
                if return_object.partner_id.ref:
                    sale_id_obj = sale_obj.browse(cr,uid,return_object.service_id.sale_id)
                    if sale_id_obj.magento_so_id:
                        data = {'customer_id':return_object.partner_id.ref,'order_id':sale_id_obj.magento_so_id}
                        if 'mag' not in sale_id_obj.name:
                            data.update({'product_id': sale_line_obj.browse(cr,uid,line.service_id.sale_line_id).product_id.magento_product_id})
                        need_to_update_data.append(data)
                        if not sale_id_obj.shop_id.referential_id.id in final_dict.iterkeys():
                            final_dict[sale_id_obj.shop_id.referential_id.id] = need_to_update_data
                        else:
                            value = final_dict[sale_id_obj.shop_id.referential_id.id]
                            new_value = value + need_to_update_data
                            final_dict[sale_id_obj.shop_id.referential_id.id] = new_value
                        if result and result.get('state'):
				return_object.write({'state':result.get('state')})
                        if context.get('deactivate_service')==True:
                            return_object.write({'cancellation_type':'credits_cancel'})
                        elif context.get('immediate_cancel')=='yes':
                            return_object.write({'cancellation_type':'cancel_immediately'})
                        else:
                            return_object.write({'cancellation_type':'cancel'})
#                cox gen2
#                if final_dict:
#                    referential_obj = self.pool.get('external.referential')
#                    for each_key in final_dict.iterkeys():
#                        value = final_dict[each_key]
#                        referential_id_obj = referential_obj.browse(cr,uid,each_key)
#                        attr_conn = referential_id_obj.external_connection(True)
#                        deactived_services = attr_conn.call('sales_order.recurring_services', ['update',value,''])            
        return True
    
    def refund_cancel_service(self,cr,uid,ids,context={}):
        if context is None: context={}
        credit_object=self.pool.get('return.order').browse(cr,uid,ids[0])
        if not credit_object.return_reason:
        #if active_model=='credit.service':
         #   credit_object=self.pool.get(active_model).browse(cr,uid,active_id)
          #  order_lines=credit_object.order_line
           # if len(order_lines)!=0:
            #    for line in order_lines:
             #       if not line.notes:
		raise osv.except_osv(_('Error !'),_('Please Specify Reason for Cancellation in Credit Service Line'))
        context.update({'deactivate_service':True,'refund_cancel_service':True})
        self.refund_service(cr,uid,ids,context=context)
        return True

    def refund_service(self,cr,uid,ids,context={}):
        self.return_confirm(cr,uid,ids,context)
        if context is None: context={}
        active_model='return.order'
        invoice_lines=context.get('invoice_line_ids')
        authorize_obj = self.pool.get('authorize.net.config')
        #active_id=context.get('active_id')
        #active_model=context.get('active_model')
        partner_obj = self.pool.get('res.partner')
        return_line_obj = self.pool.get('return.order.line')
        service_line_obj=self.pool.get('credit.service.line')
        cancel_service = self.pool.get('cancel.service')
        account_refund = self.pool.get('account.invoice')
        credit_object=self.pool.get('return.order').browse(cr,uid,ids[0])
        print"credit_object",credit_object
        config_ids = authorize_obj.search(cr,uid,[])
        for invoice in invoice_lines:
            total_amount=0.0
            lines=invoice_lines[invoice]
            for line in return_line_obj.browse(cr,uid,lines):
                print"line",line
                sub_total= line.price_subtotal
                total_amount+=sub_total
            if total_amount == 0.0:
                    raise osv.except_osv(_('Warning !'),_('Total Cannot be 0.0 for %s')%(line.name))
            cr.execute("select number,auth_transaction_id from account_invoice where id=%s"%(int(invoice)))
            payment_profile_data=cr.dictfetchall()
            cr.execute("select profile_id,credit_card_no,customer_profile_id from custmer_payment_profile where customer_profile_id='%s' and active_payment_profile=True"%(str(credit_object.partner_id.customer_profile_id)))
            profile_data=cr.dictfetchall()
            if payment_profile_data and profile_data:
#                context['linked_refund'] = True
                payment_profile_data = payment_profile_data[0]
                cust_payment_profile_id=profile_data[0].get('profile_id','')
                auth_transaction_id=payment_profile_data.get('auth_transaction_id','')
                cc_number=profile_data[0].get('credit_card_no','')
                cust_profile_id=profile_data[0].get('customer_profile_id','')
                invoice_number=payment_profile_data.get('number','')
                if not cust_profile_id:
                    cust_profile_id=credit_object.partner_id.customer_profile_id
                if cc_number and len(cc_number)==4:
                    cc_number='XXXX'+''+str(cc_number)
                config_obj = authorize_obj.browse(cr,uid,config_ids[0])
                api_call = False
#                try:
                if payment_profile_data.get('auth_transaction_id'):
                    transaction_status = authorize_obj.call(cr,uid,config_obj,'getTransactionDetailsRequest',auth_transaction_id)
#                        print "transaction_status",transaction_status
                    if (transaction_status) and (transaction_status.get('transactionStatus') == 'settledSuccessfully'):
                        api_call =self.pool.get('authorize.net.config').check_authorize_net(cr,uid,'return.order',credit_object.id,context)
			if not api_call:
                            ccv=''
                            api_call =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',credit_object.id,'profileTransRefund',total_amount,cust_profile_id,cust_payment_profile_id,auth_transaction_id,ccv,active_model,cc_number,context)
                            if api_call:
                                credit_object.api_response(api_call,cust_profile_id,cust_payment_profile_id,cc_number)  ##cox gen2 removed the parameter context
#                        api_call =authorize_obj.call(cr,uid,config_obj,'CreateCustomerProfileTransaction',credit_object.id,'profileTransRefund',total_amount,cust_profile_id,cust_payment_profile_id,auth_transaction_id,active_model,cc_number,context)
                    else:
                        raise osv.except_osv(_('Error !'),_('Payment Transaction of Invoice %s is not Settled yet'%(invoice_number)))
                    if api_call:
 #                       credit_object.api_response(api_call,cust_profile_id,cust_payment_profile_id,cc_number,context)
                        context['customer_profile_id'] = cust_profile_id
                        context['cc_number'] = cc_number
           #             account_refund.api_response(cr,uid,refund_invoice_id,api_call,cust_payment_profile_id,'profileTransRefund',context)
                        journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
                        address = False
                        address = partner_obj.address_get(cr, uid, [credit_object.company_id.partner_id.id], ['default'])
                        if address:
                            address = address.get('default',False)
                            refund_invoice_id = account_refund.create(cr,uid,
                                        {'partner_id':credit_object.partner_id.id,
            #                            'address_invoice_id':credit_object.partner_invoice_id.id,
                                        'currency_id':credit_object.pricelist_id.currency_id.id,
                                        'account_id':credit_object.partner_id.property_account_receivable.id,
                                        'name':credit_object.name,
            #                            'address_contact_id':credit_object.partner_shipping_id.id,
                                        'location_address_id': address,
                                        'user_id':uid,
                                        'journal_id':journal_id[0],
                                        'type':'out_refund',
                                        'return_id':credit_object.id,
                                        'origin':credit_object.name,
                                        'return_ref':credit_object.name+'/Service_Return' #field is present in bista_order_returns
                            })
                            acc_invoice_line_obj = self.pool.get('account.invoice.line')
                            #for each_order_line in service_line_obj.browse(cr,uid,lines):
                            for each_order_line in return_line_obj.browse(cr,uid,lines):                      
                                if each_order_line.account_id:
                                    account_id = each_order_line.account_id.id
                                else:
                                    if each_order_line.product_id.property_account_income.id:
                                        account_id = each_order_line.product_id.property_account_income.id
                                    else:
                                        account_id = each_order_line.product_id.categ_id.property_account_income_categ.id
                                account_invoice_line = acc_invoice_line_obj.create(cr,uid,
                                {'product_id':each_order_line.product_id.id,
                                 'name':each_order_line.product_id.name,
                                 'quantity':each_order_line.product_uom_qty,
                                 'price_unit':each_order_line.price_unit,
                                 'uos_id':each_order_line.product_uom.id,
                                 'account_id':account_id,
                                 'discount':each_order_line.discount,
                                 'invoice_id':refund_invoice_id,
                                 'origin': credit_object.name,
                                'invoice_line_tax_id': [(6, 0, [x.id for x in each_order_line.tax_id])],
                                'note': each_order_line.notes,

                                })
			    account_refund.api_response(cr,uid,refund_invoice_id,api_call,cust_payment_profile_id,'profileTransRefund',context) 	
                            print"credit_object.idcredit_object.id",credit_object.id
                            cr.execute("insert into return_order_invoice_rel (order_id,invoice_id) values(%s,%s)",(credit_object.id,refund_invoice_id))
                            netsvc.LocalService("workflow").trg_validate(uid, 'account.invoice', refund_invoice_id, 'invoice_open', cr)
                            account_refund.make_payment_of_invoice(cr, uid, [refund_invoice_id], context=context)
                            #To write refund_generated as True in main Recurring invoice
                            cr.execute("update account_invoice set refund_generated=True where id=%s"%(invoice))
                            email_to = credit_object.partner_id.emailid
                            refund_invoice_obj = account_refund.browse(cr,uid,refund_invoice_id)
                            self.pool.get('sale.order').email_to_customer(cr, uid, refund_invoice_obj,'account.invoice','service_credit',email_to,context)
                            return_line_obj.write(cr,uid,lines,{'state':'done'})
                            credit_object.write({'state':'done'})
                            #To Deactivate the Services
                            if context.get('deactivate_service',False):
			    	self.cancel_service(cr,uid,ids,context)
#                                if len(context.get('service_to_deactivate'))!=0:
 #                                   for policy_brw in policy_obj.browse(cr,uid,context.get('service_to_deactivate')):
  #                                          cancel_service.cancel_service(cr,uid,policy_brw,policy_brw.agmnt_partner.billing_date,False,context)
			    else:
                                credit_object.write({'cancellation_type':'credits'})
            else:
                raise osv.except_osv(_('Warning!'),_('Payment profile not found'))
        return True
    def return_confirm(self,cr,uid,ids,context={}):
        if ids:
            return_object=self.pool.get('return.order').browse(cr,uid,ids[0])
            policy_obj = self.pool.get('res.partner.policy')
            sale_obj = self.pool.get('sale.order')
#             search_policy_id = policy_obj.search(cr,uid,[('product_id','=',return_object.service_id),('agmnt_partner','=',return_object.partner_id.id)])
            print"service======>",return_object.service_id
            
#             policy_so = policy_obj.browse(cr,uid,return_object.partner_id.id)
            sale_name = sale_obj.browse(cr,uid,return_object.service_id.sale_id)
            print"name===>",sale_name.name
            partner_id=return_object.partner_id
            order_lines=return_object.order_line
            invoice_id,service_to_deactivate,invoice_line_ids=[],[],{}
            

            for line in order_lines:
                sale_line_id=return_object.service_id.sale_line_id
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
    #                     cr.execute("select max(id) "
    #                            "from account_invoice where origin='%s'"%(line.service_id.sale_order))
                    cr.execute("select max(id) "
                                "from account_invoice where origin='%s'"%(sale_name.name))
                    invoice_id=list(cr.fetchone())
                if invoice_id and invoice_id[0]:
                    if invoice_id[0] in invoice_line_ids:
                        invoice_line_ids[invoice_id[0]]+=[line.id]
                    else:
                        invoice_line_ids[invoice_id[0]]=[line.id]
    #                    service_to_deactivate+=[line.service_id.id]
                    service_to_deactivate=return_object.service_id.product_id                
    #            if invoice_line_ids:
#                 context.update({'active_ids':ids,'active_mlodel':'refund.against.invoice','active_id':ids[0],'invoice_line_ids':invoice_line_ids,'service_to_deactivate':service_to_deactivate})
            context.update({'active_ids':ids[0],'active_mlodel':'refund.against.invoice','active_id':ids,'invoice_line_ids':invoice_line_ids,'service_to_deactivate':service_to_deactivate})
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
#End code Preeti for RMA
refund_against_invoice()
