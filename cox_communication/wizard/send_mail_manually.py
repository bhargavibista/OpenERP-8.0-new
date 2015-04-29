# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
class send_mail_manual(osv.osv_memory):
    _name = "send.mail.manual"
    _rec_name='email_to'
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        attachment_ids,emailid=[],''
        res = super(send_mail_manual, self).default_get(cr, uid, fields, context=context)
#        smtp_server_id = self.pool.get('email.smtpclient').search(cr,uid,[])
        mail_server_id = self.pool.get('ir.mail_server').search(cr,uid,[])  ##cox gen2 
        attach_obj=self.pool.get('ir.attachment')
        if mail_server_id:
            res.update({'mail_server_id': mail_server_id[0]})
        if context.get('active_model') and context.get('active_id'):
            active_model = context.get('active_model',False)
            active_id = context.get('active_id',False)
            id_obj = self.pool.get(active_model).browse(cr,uid,active_id)
            if id_obj:
                if context.get('active_model') == 'res.partner':
                    emailid = id_obj.emailid
                elif active_model=='vista.report':
                    attachment_ids.append((0, 0,{'name':id_obj.name,'data':id_obj.datas}))
                else:
                    emailid = (id_obj.partner_id.emailid if id_obj.partner_id and id_obj.partner_id.emailid else id_obj.partner_id.parent_id.emailid if id_obj.partner_id.parent_id else '')
                attach_ids=attach_obj.search(cr,uid,[('res_model','=',active_model),('res_id','=',active_id)])
		if active_model != 'stock.picking':
			if attach_ids:
			    for each in attach_obj.browse(cr,uid,attach_ids):
				attachment_ids.append((0, 0,{'name':each.name,'data':each.datas}))
                res.update({'email_to': emailid,'attachments':attachment_ids})
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',context=None, toolbar=False, submenu=False):
        
        res = super(send_mail_manual, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context is None: context={}
        if context.get('active_model'):
            active_model = context.get('active_model',False)
#            active_id = context.get('active_id',False)
            if context.get('active_ids',[]):
                if len(context.get('active_ids')) > 1:
                    raise osv.except_osv(_('Error !'),_('You can able to select only one Record at a time'))
 #           if active_model == 'partner.payment.error':
  #              invoice_id = self.pool.get(active_model).browse(cr,uid,active_id).invoice_id
   #             if invoice_id:
    #                context['active_model'] = 'account.invoice'
     #               context['active_ids'] = [invoice_id.id]
      #              context['active_id'] = [invoice_id]
            model_id = self.pool.get('ir.model').search(cr,uid,[('model','=',active_model)])
            template_id = self.pool.get('email.template').search(cr,uid,[('model_id','in',model_id)])
#            if template_id:
            if res:
            	if res.get('fields').get('template'):
                	res['fields']['template']['domain'] = [('id', 'in', template_id)]
        return res
    def onchange_template(self, cr, uid, ids,template, context):
        body,subject = '',''
        if template:
            message_obj = self.pool.get('mail.compose.message')
            template_obj = self.pool.get('email.template')
            if context.get('active_model') and context.get('active_id'):
        #        if context.get('active_model') == 'partner.payment.error':
       #             context['active_model'] = 'account.invoice'
         #           invoice_id = self.pool.get('partner.payment.error').browse(cr,uid,context.get('active_id')).invoice_id
          #          if invoice_id:
           #             context['active_model'] = 'account.invoice'
            #            context['active_id'] = invoice_id.id
                template_id_obj = template_obj.browse(cr,uid,template)
                subject = template_id_obj.subject
                body_template = template_id_obj.body_html
                if subject:
                    subject = message_obj.render_template(cr, uid, subject, context.get('active_model'), context.get('active_id'))
                    body = message_obj.render_template(cr, uid, body_template, context.get('active_model'), context.get('active_id'))
        return {'value': {'notes': body,'subject':subject}}
    def mail_send(self,cr,uid,ids,context={}):
        attachements_data = []
        smtp_obj = self.pool.get('email.smtpclient')
        ids_obj = self.browse(cr,uid,ids[0])
        mail_server_id = ids_obj.mail_server_id  ##cox gen2
#        smtpserver_id = ids_obj.smtp_server 
        email_to = ids_obj.email_to
        subject = ids_obj.subject
        content = ids_obj.notes
        template = ids_obj.template.id  ##cox gen2
        active_model = context.get('active_model',False)
        active_id = context.get('active_id',False)
	internal_param = context.get('internal',False)
        search_incoming_shipment=[]
        if (not subject):
            raise osv.except_osv(_('Error !'),_('Please Enter Subject'))
        elif (not content):
            raise osv.except_osv(_('Error !'),_('Please Specify Content'))
        for each in ids_obj.attachments:
                attachements_data.append({'name':each.name,'data':each.data})
        print"attachements_data",attachements_data
        context['my_attachments']=attachements_data
        emailto=[e.strip() for e in email_to.split(';') if '@' in e]
        context.update({'email_to':emailto})
        if mail_server_id:
            self.pool.get('email.template').send_mail(cr,uid,template,active_id,'True',False,context)
#        if smtpserver_id:
#            queue_id = smtp_obj.send_email(cr, uid, smtpserver_id.id, emailto, subject, content,[],context=context)
#            if queue_id:
#                result=smtp_obj._my_check_queue(cr,uid,queue_id) #function to send them imediately
#            if result and active_id and active_model=='return.order' and internal_param: #
            if active_id and active_model=='return.order' and internal_param: #
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                final_date = str(datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")+relativedelta(days=14))
                self.pool.get(active_model).write(cr,uid,active_id,{'email_sent':True,'email_send_2_week':final_date,'state':'email_sent'})
                #Extra code to create Incoming shipment in the draft state
                context['active_id'] = active_id
                context['active_ids'] = [active_id]
                context['active_model'] = 'return.order'
                context['incoming_shipment'] = True
                search_shipment = self.pool.get('stock.picking').search(cr,uid,[('return_id','=',active_id),('state','=','draft')])	
                print"search_shipment",search_shipment
                if search_shipment:
                    for each in self.pool.get('stock.picking').browse(cr,uid,search_shipment):
                        print"each",each
                        if each.picking_type_id.code=='incoming':
                            search_incoming_shipment.append(each.id)
                if not search_incoming_shipment:	
                        self.pool.get('receive.goods').receive_goods_wizard(cr,uid,ids,context)
                    #code ends here
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': active_id,
                'res_model': active_model,
                'type': 'ir.actions.act_window',
                'context': context	

                        }
        return {'type': 'ir.actions.act_window_close'}
    _columns={
    'email_to':fields.char('Email To',size=256,),
#    'smtp_server':fields.many2one('email.smtpclient','SMTP Server',),
    'mail_server_id':fields.many2one('ir.mail_server', 'Outgoing Mail Server', readonly=False, required=True,
                                          help="Optional preferred server for outgoing mails. If not set, the highest "
                                               "priority one will be used."),
    'subject':fields.char('Subject',size=640),
    'template':fields.many2one('email.template','Template'),
    'attachments':fields.one2many('send.shipping.label','attachment_id','Attachments',nolabel=True),
    'notes':fields.text('Email Body'),
    }
send_mail_manual


class send_shipping_label(osv.osv_memory):
    _name= 'send.shipping.label'
    _columns={
        'name':fields.char('Attachment Name',size=60),
        'attachment_id':fields.many2one('send.mail.manual','Attachments',nolabel=True),
        'data':fields.binary('Attachment')
            }
send_shipping_label()
