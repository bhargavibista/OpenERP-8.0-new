from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime
from dateutil.relativedelta import relativedelta

class active_recurring_billing(osv.osv_memory):
    _name='active.recurring.billing'
#    _rec_name='policy_id'
    _columns={
    'active_policy_id':fields.one2many('res.partner.policy.duplicate','active_recurring_ids','Partner Policy')
    }

    def default_get(self, cr, uid, fields, context=None):
        created_ids,res=[],{}
        print"contextcontextcontext",context
        active_id=context.get('active_id',False)
        active_model=context.get('active_model',False)
        policy_obj=self.pool.get('res.partner.policy')
        if active_id and active_model=='res.partner':
            services=policy_obj.search(cr,uid,[('agmnt_partner','=',active_id),('active_service','=',True),('no_recurring','=',True)])
            if services:
                for service in policy_obj.browse(cr,uid,services):
                    vals={
                    'service_name':service.service_name,
                    'start_date':service.start_date,
                    'no_recurring':service.no_recurring,
                    'end_date':service.end_date,
                    'policy_id':service.id,
                    'sale_line_id':service.sale_line_id
                    }
                    created_ids.append(vals)
                if created_ids:
                    res.update({'active_policy_id':created_ids})
#                print"ressssssssssssssssssss",res
        return res
    def active_recurring_billing(self,cr,uid,ids,context=None):
        policy_obj=self.pool.get('res.partner.policy')
        partner_obj=self.pool.get('res.partner')
        rb_activation_obj=self.pool.get('recurring.billing.activation')
        if context and context.get('active_model')=='res.partner':
            data_obj=self.browse(cr,uid,ids[0]).active_policy_id
#            print"data_objdata_objdata_obj",data_obj
#            policy_ids=[s.policy_id.id for s in data_obj]
#            print"policy_idspolicy_idspolicy_ids",policy_ids
            if data_obj:
                for each_policy in data_obj:
                    no_recurring=each_policy.no_recurring
                    if no_recurring==False:
                        policy_brw=policy_obj.browse(cr,uid,each_policy.policy_id.id)
                        start_date=datetime.datetime.strptime(str(policy_brw.free_trial_date), "%Y-%m-%d").date()+relativedelta(days=1)
                        if policy_brw.no_recurring==True:
                            if policy_brw.cancel_date:
                                result=policy_obj.create(cr,uid,{
                                'service_name':policy_brw.service_name,
                                'active_service':True,
                                'sale_id': policy_brw.sale_id,
                                'start_date': start_date,
                                'agmnt_partner':policy_brw.agmnt_partner.id,
                                'product_id': policy_brw.product_id.id,
                                'from_package_id':policy_brw.id,
                                'free_trial_date': start_date,
                                'sale_line_id':policy_brw.sale_line_id,
                                'sale_order':policy_brw.sale_order,
                                'no_recurring':False,
                                })
                            policy_brw.write({'no_recurring':False})
                            partner_obj.next_billing_amount(cr,uid,policy_brw.agmnt_partner.id)
                            today=datetime.datetime.today()
                            res=rb_activation_obj.create(cr,uid,{'partner_id':policy_brw.agmnt_partner.id,'policy_id':policy_brw.id,'user_id':uid,'rb_activation_date':today.date()})
        return True
    
    def deactivate_recurring_billing(self,cr,uid,ids,context=None):
        policy_obj=self.pool.get('res.partner.policy')
        partner_obj=self.pool.get('res.partner')
        if context and context.get('active_model')=='res.partner':
            data_obj=self.browse(cr,uid,ids[0]).active_policy_id
            if data_obj:
                for each_policy in data_obj:
                    no_recurring=each_policy.no_recurring
                    if no_recurring==True:
                        policy_brw=policy_obj.browse(cr,uid,each_policy.policy_id.id)
                        print"policy_brwpolicy_brwpolicy_brw",policy_brw.id
                        if policy_brw.no_recurring==False:
                            cr.execute("update res_partner_policy set no_recurring=True where id=%d"%policy_brw.id)
                            partner_obj.next_billing_amount(cr,uid,policy_brw.agmnt_partner.id)
        return True


active_recurring_billing()
