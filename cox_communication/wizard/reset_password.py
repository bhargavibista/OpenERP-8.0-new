# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import random
import string
from datetime import date, datetime, timedelta
import uuid
import md5
import hashlib
import logging
_logger = logging.getLogger(__name__)

class reset_password_oe(osv.osv_memory):
    _name="reset.password.oe"
#    _rec_name = 'emailid'
    _columns={
    'password': fields.char('Passsword To be Set up',size=215),
    'emailid': fields.char('Email ID',size=215),
    'email_subject': fields.char('Subject',size=215),
    'email_body': fields.text('Email Body'),
    'magento_location': fields.many2one('external.referential','Magento Website'),
    'send_email': fields.boolean('Send Email')
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                       context=None, toolbar=False, submenu=False):
       res = super(reset_password_oe, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
       if context and context.get('active_id'):
           partner_brw = self.pool.get('res.partner').browse(cr,uid,context.get('active_id'))
           if not partner_brw.ref:
               raise osv.except_osv(_('Warning !'),_('Cannot able to Reset the Password'))
       return res
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(reset_password_oe, self).default_get(cr, uid, fields, context=context)
        if context and context.get('active_id'):
            emailid = self.pool.get('res.partner').browse(cr,uid,context.get('active_id')).emailid
            if emailid:
                res.update({'emailid':emailid})
            search_referential = self.pool.get('external.referential').search(cr,uid,[])
            if search_referential:
                res.update({'magento_location':search_referential})
        return res
    def onchange_password(self,cr,uid,ids,password,context):
        res= {}
        warning = {'title': _('Warning!')}
        if password:
            if len(password) <= 5:
                warning.update({'message' : _('Password should be Greater than 5 Characters')})
        if warning and warning.get('message'):
            res['value'] = {}
            res['value']['password'] = False
            res['warning'] = warning
        return res
    def onchange_send_email(self,cr,uid,ids,send_email,context):
        res  = {}
        if send_email:
            template_obj=self.pool.get('email.template')
            template_search = template_obj.search(cr,uid,[('model','=','res.partner'),('email_type','=','forgot_password')])
            if template_search:
                template_id_obj = template_obj.browse(cr,uid,template_search[0])
                content = template_id_obj.body_html
                subject= template_id_obj.subject
                res['email_body'] = content
                res['email_subject'] = subject
                res
        return {'value':res}
    def reset_password(self,cr,uid,ids,context):
        if context and context.get('active_id'):
            ids_brw = self.browse(cr,uid,ids[0])
            password = ids_brw.password
            partner_obj = self.pool.get('res.partner')
            partner_brw = partner_obj.browse(cr,uid,context.get('active_id'))
            if partner_brw:
                if password !=  partner_brw.magento_pwd:
                    if not password:
                        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                    salt = uuid.uuid4()
    #                hash_string = hashlib.sha256(str(salt)[:2]+password).hexdigest()
                    hash_string = md5.md5(str(salt)[:2]+password).hexdigest()
                    password_hash = hash_string + ':' + str(salt)[:2]
                    try:
                        conn = ids_brw.magento_location.external_connection(True)
                        if conn:
                            data = {'password_hash': password_hash}
                            conn.call('customer.update',[partner_brw.ref,data])
                            cr.execute("update res_partner set magento_pwd = '%s' where id=%d"%(password,partner_brw.id))
                            cr.commit()
                            if ids_brw.send_email:
                                message_obj = self.pool.get('mail.compose.message')
                                smtp_obj = self.pool.get('email.smtpclient')
                                smtpserver_id = smtp_obj.search(cr,uid,[('pstate','=','running'),('active','=',True)])
                                if smtpserver_id:
                                    content = message_obj.render_template(cr, uid, ids_brw.email_body, 'res.partner', partner_brw.id)
                                    subject=message_obj.render_template(cr, uid, ids_brw.email_subject, 'res.partner', partner_brw.id)
                                    queue_id = smtp_obj.send_email(cr, uid, smtpserver_id[0], ids_brw.emailid, subject, content,[])
                                    if queue_id:
                                        result=smtp_obj._my_check_queue(cr,uid,queue_id)
                    except Exception, e:
                        _logger.info("Exception %s",e)
        return True
reset_password_oe()
