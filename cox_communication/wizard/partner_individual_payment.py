from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime

class partner_individual_payment(osv.osv_memory):
    _name='partner.individual.payment'
#    _rec_name = 'product_ids'
    _columns={
    'billing_date':fields.date('Billing Date',readonly=True),
    'partner_id':fields.many2one('res.partner','Customer',readonly=True)
    }

    def default_get(self, cr, uid, fields, context=None):
        res={}
        active_id=context.get('active_id',False)
        if active_id:
            res.update({'partner_id':active_id})
	    billing_date  = self.pool.get('res.partner').browse(cr,uid,active_id).billing_date
            if billing_date:	
                res.update({'billing_date':billing_date})
        return res
    
    def capture_payment(self,cr,uid,ids,context=None):
        data_obj=self.browse(cr,uid,ids[0])
        billing_date=data_obj.billing_date
        partner_id=data_obj.partner_id.id
        context.update({'billing_date':billing_date,'partner_ids':[partner_id]})
        self.pool.get('res.partner').recurring_billing(cr,uid,context)
        return {'type': 'ir.actions.act_window_close'}

partner_individual_payment()
