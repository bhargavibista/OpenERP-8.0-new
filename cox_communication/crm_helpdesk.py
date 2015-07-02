# -*- coding: utf-8 -*-
from openerp.addons.crm import crm
from openerp.osv import fields, osv
from datetime import datetime
from dateutil import relativedelta
from openerp.tools.translate import _
import time

##cox gen2 start
#from openerp.addons.base_status.base_state import base_state
#from openerp.addons.base_status.base_stage import base_stage
#class crm_helpdesk(base_state, base_stage, osv.osv):
#***** end
class crm_helpdesk(osv.osv):
    """ Helpdesk Cases """
    _inherit = 'crm.helpdesk'
    def remind_user(self, cr, uid, ids, context=None, attach=False, destination=True):
        smtp_obj =  self.pool.get('email.smtpclient')
        smtp_server_obj = False
        account_smtpserver_id = smtp_obj.search(cr, uid, [('type','=','account'),('state','=','confirm'),('active','=',True)], context=False)
        if not account_smtpserver_id:
            default_smtpserver_id = smtp_obj.search(cr, uid, [('type','=','default'),('state','=','confirm'),('active','=',True)], context=False)
        smtpserver_id = account_smtpserver_id or default_smtpserver_id
        if smtpserver_id:
            smtpserver_id = smtpserver_id[0]
            smtp_server_obj = smtp_obj.browse(cr,uid,smtpserver_id)
        else:
            raise osv.except_osv(_('Error'), _('No SMTP Server has been defined!'))
        case = self.browse(cr,uid,ids[0])
        src = (case.user_id.user_email if case.user_id else '' )
        if not case.email_from:
            raise osv.except_osv(_('Error'), _('Please Enter Email Address!'))
        dest = case.email_from
        body = case.description or ""
        if body and case.user_id.signature:
            if body:
                body += '\n\n%s' % (case.user_id.signature)
            else:
                body = '\n\n%s' % (case.user_id.signature)
        for message in case.message_ids:
            if message.email_from and message.body_text:
                body = message.body_text
                break
        body = self.format_body(body)
#        if attach:
        attach_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_model', '=', self._name), ('res_id', '=', case.id)])
        if attach_ids:
            attach_to_send = self.pool.get('ir.attachment').read(cr, uid, attach_ids, ['datas_fname', 'datas'])
            attach_to_send = dict(map(lambda x: (x['datas_fname'], base64.decodestring(x['datas'])), attach_to_send))
        else:
            attach_to_send = []
        subject = "Reminder: [%s] %s" % (str(case.id), case.name, )
        state1 = self.pool.get('email.smtpclient').send_email(cr, uid, smtpserver_id, dest, subject, body, attach_to_send)
        #To create record in the history tab which is nothing but mail.message
        msg_vals = {
                'subject': subject,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': uid,
                'model': 'crm.helpdesk',
                'res_id': ids[0],
                'body_text': body,
                'body_html': body,
                'email_from': smtp_server_obj.from_email,
                'email_to': dest
            }
        email_msg_id = self.pool.get('mail.message').create(cr, uid, msg_vals, context)
        return email_msg_id
    def _get_default_channel(self, cr, uid, context =None):
        channel_name = 'Phone'
        cr.execute("select id from crm_case_channel where name ='%s'"%(channel_name))
        channel_phone = cr.fetchall()
        if channel_phone:
            return channel_phone[0]
        else:
            return False
        
    _columns = {
            'categ_id': fields.many2one('crm.case.categ', 'Category', \
            domain="[('object_id.model', '=', 'crm.helpdesk')]"),
            'vendor_ticket_nos': fields.char('Vendor Ticket No',size=36),
            'date_deadline': fields.date('Deadline'),
            'product_id': fields.many2one('product.product', 'Product'),
            'reasons': fields.many2one('reasons.title','Reason'),
            'name': fields.char('Name',size=36),
                }
    _defaults={
    'channel_id':_get_default_channel,
    'date_deadline': lambda *a: str(datetime.now() + relativedelta.relativedelta(days=1)),
    }
crm_helpdesk()

class crm_case_categ(osv.osv):
    """ Category of Case """
    _inherit = "crm.case.categ"
    def _find_object_id(self, cr, uid, context=None):
        """Finds id for case object"""
        object_id = context and context.get('object_id', False) or False
        ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', object_id)])
        return ids and ids[0] or False

    _defaults = {
        'object_id' : _find_object_id
    }
crm_case_categ()