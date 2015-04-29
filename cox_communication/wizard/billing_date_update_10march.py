from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class billing_date_update(osv.osv_memory):
    _name='billing.date.update'
    _columns={
    'billing_date':fields.date('Billing Date',readonly=True),
    'minimum_date':fields.date('Minimum Date'),
    'partner_id':fields.many2one('res.partner','Customer',readonly=True),
    'active_service':fields.one2many('res.partner.policy.duplicate','wizard_id','Services')
    }
    def default_get(self, cr, uid, fields, context=None):
        created_ids,res=[],{}
        active_id=context.get('active_id',False)
        active_model=context.get('active_model',False)
        policy_obj=self.pool.get('res.partner.policy')
        if active_id and active_model=='res.partner':
            res.update({'partner_id':active_id})
            partner_obj=self.pool.get(active_model).browse(cr,uid,active_id)
            services=policy_obj.search(cr,uid,[('agmnt_partner','=',active_id),('active_service','=',True)])
            if services:
                billing_date=partner_obj.billing_date
                min_services = min(services)
                if billing_date:
                    res.update({'billing_date':billing_date})
                for service in policy_obj.browse(cr,uid,services):
                    service_id = service.id
                    if service_id in [min_services]:
                        res.update({'minimum_date':service.start_date})
                    vals={
                    'service_name':service.service_name,
                    'start_date':service.start_date,
                    'end_date':service.end_date,
                    'policy_id':service.id,
                    'sale_id':service.sale_id
                    }
                    created_ids.append(vals)
                if created_ids:
                    res.update({'active_service':created_ids})
        return res

    def update_date(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        active_id=context.get('active_id',False)
        active_model=context.get('active_model',False)
        partner_obj=self.pool.get(active_model)
        policy_object=self.pool.get('res.partner.policy')
        data_obj=self.browse(cr,uid,ids[0])
        services_wizard=data_obj.active_service
        policy_ids=[s.policy_id.id for s in services_wizard]
        if policy_ids:
            minimum_id=min(policy_ids)
#            sale_id=policy_object.browse(cr,uid,minimum_id).sale_id
#            same_order_ids=policy_object.search(cr,uid,[('sale_id','=',sale_id),('id','!=',minimum_id),('active_service','=','True')])
            cr.execute("select id from res_partner_policy where agmnt_partner=%s and active_service=True and id!=%s"%(active_id,minimum_id))
            same_order_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            #print same_order_ids
            for service in services_wizard:
                start_date=service.start_date
                if start_date!=service.policy_id.start_date:
                    start_date_strp=datetime.strptime(start_date, "%Y-%m-%d")
                    end_date=start_date_strp+relativedelta(months=24)
                    service.policy_id.write({'start_date':start_date,'end_date':end_date})
                    if len(same_order_ids)!=0 and minimum_id:
                        cr.execute('select min(start_date) from res_partner_policy where id in %s',(tuple(same_order_ids),))
                        start_date1=cr.fetchone()
                        start_date2=policy_object.browse(cr,uid,minimum_id).start_date
                        if start_date1 and start_date1[0]:
                            start_date_strp1=datetime.strptime(start_date1[0], "%Y-%m-%d")
                            start_date_strp2=datetime.strptime(start_date2, "%Y-%m-%d")
                            if start_date_strp1<start_date_strp2:
                                billing_date=start_date_strp1+relativedelta(months=1)
                                partner_obj.write(cr,uid,[active_id],{'billing_date':billing_date,'start_date':start_date1[0] })
                            else:
                                billing_date=start_date_strp2+relativedelta(months=1)
                                partner_obj.write(cr,uid,[active_id],{'billing_date':billing_date,'start_date':start_date2})
                    elif len(same_order_ids)==0 and service.policy_id.id==minimum_id:
                        billing_date=start_date_strp+relativedelta(months=1)
                        partner_obj.write(cr,uid,[active_id],{'billing_date':billing_date,'start_date':start_date})

        return {'type': 'ir.actions.act_window_close'}

billing_date_update()

class res_partner_policy_duplicate(osv.osv_memory):
    _name = "res.partner.policy.duplicate"
    _rec_name = 'service_name'
    _columns = {
    'service_name':fields.char(size=126,string='Service Name'),
    'start_date': fields.date('Start Date', select=True, help="Date on which service is created."),
    'end_date': fields.date('End Date', select=True, help="Date on which service is closed."),
    'wizard_id':fields.many2one('billing.date.update','Date Updates'),
    'sale_id':fields.many2one('sale.order','Sale Order'),
    'policy_id':fields.many2one('res.partner.policy','Date Updates')
    }
    def onchange_start_date(self,cr,uid,ids,start_date,policy_id,context):
        warning = {}
        if start_date:
            if context.get('minimum_date'):
                start_date_new = datetime.strptime(start_date, "%Y-%m-%d")
                minimum_date = datetime.strptime(context.get('minimum_date'), "%Y-%m-%d")
                if start_date_new < minimum_date:
#                    raise osv.except_osv(_('Error !'),_('Please Specify Address Location for'))
                    warning = {'title': _('Warning'),
                    'message': 'Start Date cannot less than First Service Start Date'}
                    if policy_id:
                        start_date = self.pool.get('res.partner.policy').browse(cr,uid,policy_id).start_date
        return {'warning': warning,'value':{'start_date':start_date}}

res_partner_policy_duplicate()
