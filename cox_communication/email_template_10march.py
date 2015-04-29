# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import openerp.tools as tools
import time
from datetime import datetime
from datetime import timedelta
import os
import socket
from openerp import release
import base64
from email import Encoders
import openerp.netsvc
#logger = Logger() # commented logger statement 


class email_template(osv.osv):
    _inherit='email.template'
    _columns = {
    'email_type':fields.selection([
            ('welcome_email', 'Welcome Email'),
	    ('welcome_email_pop', 'Welcome Email For Game POP'),
            ('payment_confirmation', 'Payment Confirmation'),
            ('service_credit', 'Service Credit'),
            ('cancel_order', 'Cancel Order'),
            ('eula_reminder', 'Eula Reminder'),
            ('payment_exception', 'Payment Exception'),
            ('email_change', 'Email Changed'),
            ('forgot_password', 'Forgot Password'),
            ('return_confirmation', 'Return Confirmation'),
	    ('shipment_confirmation', 'Shipment Confirmation'),
            ('account_set_up', 'Account Set Up'),
            ('cancel_service', 'Cancel Service')],'Email Type'),}
email_template()

class smtpclient(osv.osv):
    _inherit='email.smtpclient'
#Function is inherited because want to send to_addrs array in correctly.	
    def _send_emails(self, cr, uid, ids, context={}):
        queue = self.pool.get('email.smtpclient.queue')
        history = self.pool.get('email.smtpclient.history')
        queue.write(cr, uid, ids, {'state':'sending'})
        sent = []
        remove = []
        open_server = []
        for email in queue.browse(cr, uid, ids):
            if not email.server_id.id in open_server:
                open_server.append(email.server_id.id)
                self.open_connection(cr, uid, ids, email.server_id.id)

            try:
                #Extra Code Starts here
                to_addrs = []
                if email.to:
                    to_addrs.append(email.to)
                if email.cc:
                    to_addrs.append(email.cc)
                if email.bcc:
                    to_addrs.append(email.bcc)
                self.smtpServer[email.server_id.id].sendmail(email.server_id.email, to_addrs, tools.ustr(email.serialized_message))
                #Ends here
#                message = "message sent successfully to %s from %s server" % (email.to, email.server_id.name)

#                logger.notifyChannel('smtp', netsvc.LOG_INFO, message)
            except Exception, e:
                queue.write(cr, uid, [email.id], {'error':e, 'state':'error'})
                continue

            history.create(cr, uid, {
                'name':email.body,
                'user_id':uid,
                'server_id': email.server_id.id,
                'email':email.to
            })
            if email.server_id.delete_queue == 'after_send':
                remove.append(email.id)
            else:
                sent.append(email.id)

        queue.unlink(cr, uid, remove)
        queue.write(cr, uid, sent, {'state':'send'})
        return True
	
    def send_email(self, cr, uid, server_id, emailto, subject, body='', attachments=[], reports=[], ir_attach=[], charset='utf-8', headers={}, context={}):
        queue_id=[]
#        emailto = 'poonam.dafal@bistasolutions.com'
        if not emailto:
            raise osv.except_osv(_('SMTP Data Error !'), _('Email TO Address not Defined !'))
        if not context:
            context = {}
        def createReport(cr, uid, report, ids, name=False):
            files = []
            for id in ids:
                try:
                    service = netsvc.LocalService(report)
                    (result, format) = service.create(cr, uid, [id], {}, {})
                    if not name:
                        report_file = '/tmp/reports'+ str(id) + '.pdf'
                    else:
                        report_file = name
                    fp = open(report_file,'wb+')
                    fp.write(result);
                    fp.close();
                    files += [report_file]
                except Exception,e:
                    continue
            return files
        smtp_server = self.browse(cr, uid, server_id)
        if smtp_server.state != 'confirm':
            raise osv.except_osv(_('SMTP Server Error !'), _('Server is not Verified, Please Verify the Server !'))
        if not subject:
            subject = "OpenERP Email: [Unknown Subject]"
        try:
            subject = subject.encode(charset)
        except:
            subject = subject.decode()
        #attachment from Reports
        for rpt in reports:
            if len(rpt) == 3:
                rpt_file = createReport(cr, uid, rpt[0], rpt[1], rpt[2])
            elif len(rpt) == 2:
                rpt_file = createReport(cr, uid, rpt[0], rpt[1])
            attachments += rpt_file
        if isinstance(emailto, str) or isinstance(emailto, unicode):
            emailto = [emailto]
        ir_pool = self.pool.get('ir.attachment')
        for to in emailto:
            msg = MIMEMultipart()
            msg['Subject'] = tools.ustr(subject)
            msg['To'] =  to
            msg['From'] = context.get('email_from', smtp_server.from_email)
            if body == False:
                body = ''
            if smtp_server.disclaimers:
                body = body + "\n" + smtp_server.disclaimers
            try:
                msg.attach(MIMEText(body.encode(charset) or '', _charset=charset, _subtype="html"))
            except:
                msg.attach(MIMEText(body or '', _charset=charset, _subtype="html"))
            #add custom headers to email
            for hk in headers.keys():
                msg[hk] = headers[hk]
            for hk in smtp_server.header_ids:
                msg[hk.key] = hk.value
            context_headers = context.get('headers', [])
            for hk in context_headers:
                msg[hk] = context_headers[hk]
            # Add OpenERP Server information
            msg['X-Generated-By'] = 'OpenERP (http://www.openerp.com)'
            msg['X-OpenERP-Server-Host'] = socket.gethostname()
            msg['X-OpenERP-Server-Version'] = release.version
            msg['Message-Id'] = "<%s-openerp-@%s>" % (time.time(), socket.gethostname())
            if smtp_server.cc_to:
                msg['Cc'] = smtp_server.cc_to
            if smtp_server.bcc_to:
                msg['Bcc'] = smtp_server.bcc_to
            #attach files from disc
            for file in attachments:
                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(file,"rb").read())
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))
                msg.attach(part)
            #attach files from ir_attachments
            for ath in ir_attach:
                ath = ir_pool.browse(cr, uid, ath)
                part = MIMEBase('application', "octet-stream")
#                print ath
                datas = base64.decodestring(ath.datas)
                part.set_payload(datas)
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' %(ath.name))
                msg.attach(part)
            if context !=None:
                if context.get('my_attachments'):
                    for my_attach in context.get('my_attachments'):
                        part = MIMEBase('application', "octet-stream")
                        datas = base64.decodestring(my_attach.get('data'))
                        part.set_payload(datas)
                        Encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment; filename="%s"' %(my_attach.get('name')))
                        msg.attach(part)
            message = msg.as_string()
            data = {
                'to':to,
                'server_id':server_id,
                'cc':smtp_server.cc_to or False,
                'bcc':smtp_server.bcc_to or False,
                'name':subject,
                'body':body,
                'serialized_message':message,
                'priority':smtp_server.priority,
            }
            queue_id.append(self.create_queue_enrty(cr, uid, data, context))
        return queue_id
    def _my_check_queue(self, cr, uid, ids):
        message = ""
        if ids:
            smtp_message_queue = self.pool.get('email.smtpclient.queue')
            message = "sending %s emails from message queue !" % (len(ids))
#            logger.notifyChannel('smtp', netsvc.LOG_INFO, message)
            self. _send_emails(cr, uid, ids, {})
            for queue_brw in smtp_message_queue.browse(cr,uid,ids):
                state = queue_brw.state
                if state in ('error','sending'):
                    queue_brw.write({'state':'draft'})
        return True
    #Function is inherited because want to modify search condition
    def _check_queue(self, cr, uid, ids=False):
        queue = self.pool.get('email.smtpclient.queue')
        sids = []
        #if not ids:
         #   sids = queue.search(cr, uid, [('state','not in',['send']), ('type','=','system')], order="priority", limit=30)
          #  ids =[]
        #else:
        sids = queue.search(cr, uid, [('state','not in',['send']), ('server_id','!=',False)], order="priority", limit=30)
        if len(sids) > 0:
        #    message = "sending %s emails from message queue !" % (len(sids))
#            logger.notifyChannel('smtp', netsvc.LOG_INFO, message)
        	result = self. _send_emails(cr, uid, sids, {})
	        return result
smtpclient()
class message_queue(osv.osv):
    _inherit = 'email.smtpclient.queue'
    def send_queue_mail(self,cr,uid,ids,context={}):
        self.pool.get('email.smtpclient')._send_emails(cr,uid,ids,context)
    def update_status(self,cr,uid,ids,context={}):
        self.write(cr,uid,ids,{'state':'send'})
message_queue()
