# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

class retail_agreement(osv.osv_memory):
    _name='retail.agreement'
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(retail_agreement, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        active_id = context.get('active_id',False)
        if active_id:
            sale_id_obj = self.pool.get('sale.order').browse(cr,uid,active_id)
            if not sale_id_obj.order_line:
                raise osv.except_osv(_('Error'), _('No Order Line is Defined'))
        return res
    def get_flare_watch_tou_agmt(self,cr,uid,context):
        text = ''
        if context.get('default_order_type'):
            company_obj = self.pool.get('res.company')
            company_id = company_obj.search(cr,uid,[])
            if company_id:
                text=company_obj.browse(cr,uid,company_id[0]).flare_watch_tou_agmt
        return text
    def get_fanhanttan_toa_agmt(self,cr,uid,context):
        text = ''
        if context.get('default_order_type'):
            company_obj = self.pool.get('res.company')
            company_id = company_obj.search(cr,uid,[])
            if company_id:
                text=company_obj.browse(cr,uid,company_id[0]).fanhanttan_toa_agmt
        return text
    def get_privacy_policy_agmt(self,cr,uid,context):
        text = ''
        if context.get('default_order_type'):
            company_obj = self.pool.get('res.company')
            company_id = company_obj.search(cr,uid,[])
            if company_id:
                text=company_obj.browse(cr,uid,company_id[0]).privacy_policy_agmt
        return text
    def get_fanhanttan_privacy_policy_agmt(self,cr,uid,context):
        text = ''
        if context.get('default_order_type'):
            company_obj = self.pool.get('res.company')
            company_id = company_obj.search(cr,uid,[])
            if company_id:
                text=company_obj.browse(cr,uid,company_id[0]).fanhanttan_privacy_policy_agmt
        return text
    _columns={
    'flare_watch_tou_agmt': fields.text('Agreement'),
     'flare_watch_agmt_chk': fields.boolean('Agreee'),

     'fanhanttan_toa_agmt': fields.text('Agreement'),
     'fanhanttan_toa_agmt_chk': fields.boolean('Agree'),

     'privacy_policy_agmt': fields.text('Agreement'),
     'privacy_policy_agm_chk': fields.boolean('Agree'),

     'fanhanttan_privacy_policy_agmt': fields.text('Agreement'),
     'fanhanttan_privacy_policy_agmt_chk': fields.boolean('Agree'),
    }
    _defaults={
    'flare_watch_tou_agmt':get_flare_watch_tou_agmt,
    'fanhanttan_toa_agmt':get_fanhanttan_toa_agmt,
    'privacy_policy_agmt':get_privacy_policy_agmt,
    'fanhanttan_privacy_policy_agmt':get_fanhanttan_privacy_policy_agmt
    }
    def accept_agreement(self,cr,uid,ids,context):
        if context.get('active_id'):
            mod_obj = self.pool.get('ir.model.data')
            result = mod_obj.get_object_reference(cr, uid, 'cox_communication', 'view_order_form_inherit_cox_fields')
            id = result and result[1] or False
            current_obj = self.browse(cr,uid,ids[0])
#            array = [current_obj.flare_watch_agmt_chk,current_obj.fanhanttan_toa_agmt_chk,current_obj.privacy_policy_agm_chk,current_obj.fanhanttan_privacy_policy_agmt_chk]
            array = [current_obj.flare_watch_agmt_chk]
            if False in array:
#                raise osv.except_osv(_('Error'), _('Please Accept All Agreements'))
                raise osv.except_osv(_('Error'), _('Please Accept Play Agreements'))
            cr.execute("update sale_order set agreement_approved = True where id = %d"%(context.get('active_id')))
#            return {'type': 'ir.actions.act_window_close'}
	    return{
               'name':_("Sales Order"),
               'view_mode': 'form',
               'res_id': context.get('active_id'),
               'view_type': 'form',
               'view_id': id,
               'res_model': 'sale.order',
               'type': 'ir.actions.act_window',
               'nodestroy': True,
               'target': 'current',
               'domain': '[]',
               'context': context,} 	
        
    def reject_agreement(self,cr,uid,ids,context):
	return{
               'name':_("Sales Order"),
               'view_mode': 'form',
               'res_id': context.get('active_id'),
               'view_type': 'form',
               'res_model': 'sale.order',
               'type': 'ir.actions.act_window',
               'nodestroy': True,
               'target': 'current',
               'domain': '[]',
               'context': context,}
#         return {'type': 'ir.actions.act_window_close'}
        
retail_agreement()
