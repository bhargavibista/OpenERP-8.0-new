# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.netsvc as netsvc

class pre_requisites_wizard(osv.osv_memory):
    _name = "pre.requisites.wizard"
    def accept(self, cr, uid,ids,context):
        if context is None: context = {}
        if context and context.get('sales_channel') == 'amazon' or context.get('sales_channel') == 'tru': #Preeti made this change
            sale_id = context.get('sale_id',False)
            if sale_id:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'sale.order', sale_id, 'order_confirm', cr)
                cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(sale_id))
                invoice_id=cr.fetchone()
                if invoice_id:
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
                    context['journal_type'] = 'cash'
                    returnval = self.pool.get('account.invoice').make_payment_of_invoice(cr, uid, invoice_id, context=context)
        else:
            context['action_to_do'] = 'new_payment_profile'
            context['call_from'] = 'function'
            return {
                'name': ('New Customer and Payment Profile'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'profile.transaction',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                 'context': context
                    }
    
    def create(self, cr, uid, vals, context=None):
        for key in vals:
            if not vals[key]:
                raise osv.except_osv(_('Warning !'),_('You cannot Move Forward without Accepting all Requisites'))
        return super(pre_requisites_wizard, self).create(cr, uid, vals,context)
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        fields_list,categ_id,i = {},[],1
        so_obj = self.pool.get('sale.order')
        if context is None:
            context = {}
        result = super(pre_requisites_wizard, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type=='form':
            arch = """<form string="Pre Requisites">"""
            if context and context.get('active_id') and context.get('active_model') == 'sale.order':
                sale_id_obj = so_obj.browse(cr,uid,context.get('active_id'))
                for line in sale_id_obj.order_line:
                    pre_requisites = line.product_id.categ_id.pre_requisites
                    if pre_requisites:
                        if line.product_id.categ_id.id not in categ_id:
                            categ_id.append(line.product_id.categ_id.id)
                            if len(categ_id) == 1:
                                arch += """<label string='Does the Customer has Following Requisites:' colspan="8"/> """
                            arch += """<separator string="%s" colspan="8"/>"""%(line.product_id.categ_id.name)
                            for each_requisites in pre_requisites:
                                arch += """<field name="%s"/><newline/>""" % (str(i)+'_requisites')
                                fields_list.update({str(i)+'_requisites':{
                                    'string' : each_requisites.name,
                                    'type' : 'boolean'}})
                                i = i + 1
            if not categ_id:
                arch += """<separator string="No Requisites are Defined"/>"""
            arch += """<newline/><button name="accept" string="Next"
                        colspan="1" type="object" icon="gtk-go-forward" /></form>"""
            result['arch'] = arch
            result['fields'] = fields_list
        return result
    
pre_requisites_wizard()
