# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date, datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
import datetime as dt
import calendar
from openerp import netsvc
import string
import openerp.addons.decimal_precision as dp
import random
from dateutil.relativedelta import relativedelta
from openerp.addons.base_external_referentials.external_osv import ExternalSession
import pytz
from openerp.osv import osv, fields
import base64
import csv
from openerp.tools.translate import _



#class sale_order(osv.osv):
#    _inherit='sale.order'
#
##    def import_sale_order(self,cr,uid,):
#
#sale_order()


class sale_report_wizard(osv.osv_memory):
    _name = "sale.report.wizard"
    _description = "Import CSV"
    _columns = {
        'date_create' : fields.date('Date'),
        'option':fields.selection([('import_sale','Import Sale Orders')],'Import Options'),
        'csv_file': fields.binary('Attachment'),
#        'date':fields.date
    }
    def create_report(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        report_obj=self.browse(cr,uid,ids[0])
        vista_report_obj=self.pool.get('vista.report')
        create_date=report_obj.date_create
        if create_date:
            context.update({'date_create':create_date})
            new_record = vista_report_obj.create_delivery_report(cr,uid,context)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': new_record,
                'res_model': 'vista.report',
                'type': 'ir.actions.act_window'
                    }
        return {'type': 'ir.actions.act_window_close'}

    def import_report(self,cr,uid,ids,context={}):
        if context is None:
            context={}
        report_obj = self.browse(cr,uid,ids[0])
        pick_obj = self.pool.get('stock.picking')
        partner_obj=self.pool.get('res.partner')
        shop_obj = self.pool.get('sale.shop')
        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        line_obj = self.pool.get('sale.order.line')
        invoice_obj = self.pool.get('account.invoice')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        user_obj = self.pool.get('res.users')
        order = self.pool.get('sale.order')
        wf_service = netsvc.LocalService("workflow")
        csv_file=report_obj.csv_file
        if not csv_file:
            raise osv.except_osv(_('CSV Error !'), _('Please select a .csv file'))
        val = base64.decodestring(csv_file)
        stock_data = val.split("\n")
        if stock_data:
            stock_data.pop(0)
            file_Reader = csv.reader(stock_data)
        for i in file_Reader:
            if i and len(i) > 0:
                Date = i[9]
                if Date == '7/30/2014':
#                    print"Start Date:",datetime.now()
                    Sale_No = i[0]
                    Customer_Name = i[1]
                    Customer_No = i[2]
                    Street = i[3]
                    City = i[4]
                    State = i[5]
                    Zip = i[6]
                    Email_ID = i[7]
                    Phone_Number = i[8]
                    Order_State = i[10]
                    Promo_Code = i[11]
                    Sales_Channel = i[12]
                    Location_Name = i[13]
                    Product_Name = i[14]
                    Quantity = i[15]
                    Revenue = i[16]
                    Sales_Tax = i[17]
                    User = i[18]
                    Return_No = i[19]
                    Return_Order_Date = i[20]
                    Return_Product_Name = i[21]
                    Return_Quantity = i[22]
                    Return_Amount = i[23]
                    Return_Tax = i[24]
                    Return_Reason = i[25]
                    Active_Inactive = i[26]
                    Cancel_Return_Date = i[27]
                    transaction_id = i[28]
                    customer_profile = i[29]
                    payment_profile = i[30]
                    cc_number = i[31]
                    Magento_Increment_id = i[32]
                    Magento_DB_Id = i[33]
                    Magento_So_Id = i[34]
#                    print"transaction_id",transaction_id,"customer_profile",customer_profile,"payment_profile",payment_profile,"cc_number",cc_number,"Magento_Increment_id",Magento_Increment_id
#                    print"Magento_DB_Id",Magento_DB_Id,"Magento_So_Id",Magento_So_Id
#                    errorororo
                    state_id = state_obj.search(cr,uid,[('name','=',State)])
                    country_id = country_obj.search(cr,uid,[('name','=','United States')])
                    user_id = user_obj.search(cr,uid,[('name','=',User)])
#                    print"DateDateDateDate",Date
#                    if Date == '7/30/2014':
                    res_partner = {
                        'name':Customer_Name,
                        'ref':Customer_No,
                        'street':Street,
                        'city':City,
                        'state_id': state_id and state_id[0] or False,
                        'country_id': country_id and country_id[0] or False,
                        'zip':Zip,
                        'emailid':Email_ID,
                        'phone':Phone_Number,
                        'user_id':user_id and user_id[0] or 1,
                        'customer_profile_id':customer_profile,

                    }
                    part = partner_obj.search(cr,uid,[('emailid','ilike',Email_ID)])
                    if not part:
                        partner = partner_obj.create(cr,uid,res_partner)
                    else:
                        partner = part[0]
    #                print"partner88888",partner
                    profile = self.pool.get('custmer.payment.profile').create(cr,uid,{
                        'profile_id':payment_profile,
                        'customer_profile_id':customer_profile,
                        'credit_card_no':cc_number,
                        'active_payment_profile':True,
                        })
                    cr.execute("INSERT INTO partner_profile_ids \
                        (partner_id,profile_id) values (%s,%s)", (partner, profile))
                    shop = shop_obj.search(cr,uid,[('name','ilike','Play')])
                    location_id = location_obj.search(cr,uid,[('name','=',Location_Name)])
    #                print"Product_Name222222",Product_Name
                    if Product_Name.find('[free device + 9.99 service]') > 0:
                       Product_Name = string.replace(Product_Name, ' [free device + 9.99 service]', '', 1)
                    product_id = product_obj.search(cr,uid,[('name','ilike',Product_Name)])
    #                print"product_idproduct_id*****",product_id,Quantity

                    context={'partner_id':partner, 'quantity':int(Quantity), 'pricelist':1, 'shop':shop[0], 'uom':False}
                    if product_id:
                        line = line_obj.product_id_change(cr, uid, ids, 1, product_id[0], int(Quantity),
                            False, 0, False, '', partner,False, True, False, False, False, False, context)
#                        print "line",line
                        sale_line = line['value']
                        sale_line['product_id'] = product_id[0]
#                        print"sale_line********",sale_line
#                        error
                        sale_order = {
                            'name':Sale_No,
                            'date_order':Date,
                            'shop_id':shop and shop[0] or False,
                            'pricelist_id':1,
                            'partner_id':partner,
                            'partner_shipping_id':partner,
                            'partner_invoice_id':partner,
                            'user_id':user_id and user_id[0] or uid,
                            'company_id':1,
                            'order_policy':'prepaid',
                            'location_id':location_id and location_id[0] or False,
                            'cox_sales_channels':'retail',
                            'picking_policy':'direct',
                            'order_line':[[0,0,sale_line]],
                            'magento_incrementid':Magento_Increment_id,
                            'magento_so_id':Magento_So_Id,
                            'magento_db_id':Magento_DB_Id,
                            'auth_transaction_id':transaction_id,
                            'order_type':True,
                            'agreement_approved':True
                        }
                        order_id = order.search(cr,uid,[('name','=',Sale_No)])
                        if len(order_id)==0:
                            orderid = order.create(cr,uid,sale_order)
    #                    print"orderid*****",orderid
#                            print"Order_StateOrder_State",Order_State
                            if Order_State == 'done':
                                sale_object=order.browse(cr,uid,orderid)
                                wf_service.trg_validate(uid, 'sale.order', orderid, 'order_confirm', cr)

                                if sale_object.cox_sales_channels in ('retail','ecommerce'):
#                                    invoice_ids = sale_object.invoice_ids
        #                            print"invoice_idsinvoice_ids",invoice_ids
                                    cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(orderid))
                                    invoice_id=cr.fetchone()
        #                            print"invoice_idinvoice_id",invoice_id
                                    if invoice_id:
                                        wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
#                                        print"after confirm"
                                        returnval = invoice_obj.make_payment_of_invoice(cr, uid, invoice_id, context=context)
                                picking_ids = sale_object.picking_ids
        #                        print"picking_ids",picking_ids
                                for picking in picking_ids:
                                    wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_confirm', cr)
                                    pick_obj.action_move(cr, uid, [picking.id], context=context)
                                    wf_service.trg_validate(uid, 'stock.picking', picking.id, 'button_done', cr)
#                                print"End Date:",datetime.now()
#                                break
#                print"whole dale lines iffdfdfs",sale_line
#                lineid = line_obj.create(cr,uid,sale_line)
#                print"lineidlineidlineid",lineid
#                print"orderid",orderid
#                break
#                error
        return {'type': 'ir.actions.act_window_close'}

    def process_order(self,cr,uid,ids,context={}):
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order',3824, 'order_confirm', cr)

       
        cr.execute('select invoice_id from sale_order_invoice_rel where order_id=%s'%(3824))
        invoice_id=cr.fetchone()
        if invoice_id:
            print"payyyyyyyyyyyyyyyyyy",invoice_id
            wf_service.trg_validate(uid, 'account.invoice', invoice_id[0], 'invoice_open', cr)
            returnval = self.pool.get("account.invoice").make_payment_of_invoice(cr, uid, invoice_id, context=context)
        return {'type': 'ir.actions.act_window_close'}
sale_report_wizard()
