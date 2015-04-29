# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.netsvc
import datetime
from dateutil.relativedelta import relativedelta
import calendar
class credit_service_refund(osv.osv_memory):
    _name = "credit.service.refund"
    _columns={
    }
    def cancel_service(self,cr,uid,ids,context={}):
#        today=datetime.date.today()
        active_id=context.get('active_id')
        active_model=context.get('active_model')
        if active_model=='credit.service':
            credit_object=self.pool.get(active_model).browse(cr,uid,active_id)
            order_lines=credit_object.order_line
            if len(order_lines)!=0:
                cancel_service = self.pool.get('cancel.service')
                for line in order_lines:
#                    cr.execute("update res_partner_policy set active_service=False where id=%s"%(line.service_id.id))
#                    credit_object.write({'state':'done'})
                    result = cancel_service.cancel_service(cr,uid,line.service_id,credit_object.partner_id.billling_date,line,context)
                    if result and result.get('state'):
                        credit_object.write({'state':result.get('state')})
        return {'type': 'ir.actions.act_window_close'}

    def refund_cancel_service(self,cr,uid,ids,context={}):
        active_id=context.get('active_id')
        active_model=context.get('active_model')
#        invoice_obj= self.pool.get('account.invoice')
#        today=datetime.date.today()
        if active_model=='credit.service' and active_id:
            credit_object=self.pool.get(active_model).browse(cr,uid,active_id)
            partner_id=credit_object.partner_id
            order_lines=credit_object.order_line
            service_to_deactivate,invoice_line_ids=[],{}
            for line in order_lines:
                sale_line_id=line.service_id.sale_line_id
                cr.execute("select max(a.id) "
                           "from account_invoice a "
                           "join account_invoice_line l on (a.id=l.invoice_id) "
                           "right outer join sale_order_line_invoice_rel sl on (l.id=sl.invoice_id) "
                           "and a.state='paid' and sl.order_line_id=%s and a.partner_id=%s"%(str(sale_line_id),str(partner_id.id)))
                invoice_id=list(cr.fetchone())
#                print "line.service_id.sale_order",line.service_id.sale_order
                if (invoice_id and (not invoice_id[0])):
                    cr.execute("select max(id) "
                           "from account_invoice where origin=%s"%(line.service_id.sale_order))
                    invoice_id=list(cr.fetchone())
                if invoice_id and invoice_id[0]:
                    if invoice_id[0] in invoice_line_ids:
                        invoice_line_ids[invoice_id[0]]+=[line.id]
                    else:
                        invoice_line_ids[invoice_id[0]]=[line.id]
                    service_to_deactivate+=[line.service_id.id]
            if invoice_line_ids:
                context.update({'invoice_line_ids':invoice_line_ids,'service_to_deactivate':service_to_deactivate})
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
            else:
                raise osv.except_osv(_("Error"),
                        _(("No Inovice exist for customer %s. Please check sale order of selected service"))%(partner_id.name))
        return {'type': 'ir.actions.act_window_close'}
credit_service_refund()
