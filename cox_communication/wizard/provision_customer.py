# -*- coding: utf-8 -*-
from openerp.osv  import fields, osv
import xlwt
from openerp.tools.translate import _

class unprovision_customer(osv.osv_memory):
    _name="unprovision.customer"
    _columns={
        'send_email_at': fields.char('Send Email at',size=36),
    }
    def generate_unprov_cust_report(self, cr, uid, ids,context=None):
#        self_browse=self.browse(cr,uid,ids[0])
        cr.execute('''select distinct spl.name as serial_no, rp.name,rp.emailid as email, (select phone from res_partner_address rpa where rpa.id=so.partner_order_id) as phone, so.name as SO_NO, so.date_order as Order_Date, UPPER(so.prov_by_fanha) as Not_Provisioned
		from sale_order as so
        	join stock_picking sp
		on so.id = sp.sale_id
		join stock_move sm
		on sm.picking_id = sp.id
		join stock_move_lot sml
		on sm.id = sml.stock_move_id
		join stock_production_lot spl
		on sml.production_lot = spl.id
		join res_partner rp
		on so.partner_id = rp.id
		where so.prov_by_fanha ='no' ''')
        no_prov_details = cr.fetchall()
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet("Sheet 1")
        sheet1.write(0, 0, "Customer Name")
        sheet1.write(0, 1, "Customer Email")
        sheet1.write(0, 2, "Customer Phone")
        sheet1.write(0, 3, "Serial No.")
        sheet1.write(0, 4, "Sale Order")
        sheet1.write(0, 5, "Order Date")
        sheet1.write(0, 6, "Provisioned")
        i=0
        for no_prov_detail in no_prov_details:
            i = i+1
            sheet1.write(i, 0, no_prov_detail[1])
            sheet1.write(i, 1, no_prov_detail[2])
            sheet1.write(i, 2, no_prov_detail[3])
            sheet1.write(i, 3, no_prov_detail[0])
            sheet1.write(i, 4, no_prov_detail[4])
            sheet1.write(i, 5, no_prov_detail[5])
            sheet1.write(i, 6, no_prov_detail[6])
        new_attachment =[]
        attachment = '/tmp/Non_Provision_list.xls'
        new_attachment.append(attachment)
        book.save(attachment)
        return True
    def sch_for_unprovision_list(self,cr,uid,context={}):
        if context is None:
            context = {}
        new_id = self.create(cr,uid,{},context)
        if new_id:
            context['email_id'] = 'abdul.mohsin@bistasolutions.com'
            self.mail_unprovision_order(cr,uid,[new_id],context)
    def mail_unprovision_order(self, cr, uid, ids,context=None):
        if context is None:
            context = {}
        self_browse=self.browse(cr,uid,ids[0])
        cr.execute('''select distinct spl.name as serial_no, rp.name,rp.emailid as email, (select phone from res_partner_address rpa where rpa.id=so.partner_order_id) as phone, so.name as SO_NO, so.date_order as Order_Date, UPPER(so.prov_by_fanha) as Not_Provisioned
		from sale_order as so
        	join stock_picking sp
		on so.id = sp.sale_id
		join stock_move sm
		on sm.picking_id = sp.id
		join stock_move_lot sml
		on sm.id = sml.stock_move_id
		join stock_production_lot spl
		on sml.production_lot = spl.id
		join res_partner rp
		on so.partner_id = rp.id
		where so.prov_by_fanha ='no' ''')
        no_prov_details = cr.fetchall()
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet("Sheet 1")
        sheet1.write(0, 0, "Customer Name")
        sheet1.write(0, 1, "Customer Email")
        sheet1.write(0, 2, "Customer Phone")
        sheet1.write(0, 3, "Serial No.")
        sheet1.write(0, 4, "Sale Order")
        sheet1.write(0, 5, "Order Date")
        sheet1.write(0, 6, "Provisioned")
        i=0
        for no_prov_detail in no_prov_details:
            i = i+1
            sheet1.write(i, 0, no_prov_detail[1])
            sheet1.write(i, 1, no_prov_detail[2])
            sheet1.write(i, 2, no_prov_detail[3])
            sheet1.write(i, 3, no_prov_detail[0])
            sheet1.write(i, 4, no_prov_detail[4])
            sheet1.write(i, 5, no_prov_detail[5])
            sheet1.write(i, 6, no_prov_detail[6])
        new_attachment =[]
        attachment = '/tmp/Non_Provision_list.xls'
        new_attachment.append(attachment)
        book.save(attachment)
        subject='Non Provisioned Customer List'
        content = 'Hi, Please find the Non Provisioned Customer List in the Attachment.'
        context.update({'subject':subject,'body':content})
        p = pooler.get_pool(cr.dbname)
        
        ##cox gen2 
#        account_smtpserver_id = self.pool.get('email.smtpclient').search(cr, uid, [('type','=','account'),('state','=','confirm'),('active','=',True)], context=False)
#        if not account_smtpserver_id:
#            default_smtpserver_id = p.get('email.smtpclient').search(cr, uid, [('type','=','default'),('state','=','confirm'),('active','=',True)], context=False)
#        smtpserver_id = account_smtpserver_id or default_smtpserver_id
#        if smtpserver_id:
#            smtpserver_id = smtpserver_id[0]
#        else:
#            raise osv.except_osv(_('Error'), _('No SMTP Server has been defined!'))

        mail_server_id = self.pool.get('ir.mail_server').search(cr,uid,[])
        if mail_server_id:
            mail_server_id = mail_server_id[0]
        else:
            raise osv.except_osv(_('Error'), _('No Outgoing Mail Server has been defined!'))
        if not context.get('email_id'):
            email_id = self_browse.send_email_at
        else:
            email_id = context.get('email_id')
        context.get({'email_to':email_id})
#        state1 = self.pool.get('email.smtpclient').send_email(cr, uid, smtpserver_id, email_id, subject, content, new_attachment)  cox gen2
        state1 = self.pool.get('email.template').send_mail(cr,uid,False,ids[0],'True','False',context)
        return {'type': 'ir.actions.act_window_close'}
unprovision_customer()