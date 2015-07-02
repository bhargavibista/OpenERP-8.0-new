# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from base64 import b64decode
import binascii
from openerp.addons.bista_shipping.miscellaneous import Address
from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.config import FedexConfig
import suds
from suds.client import Client
from openerp.tools.translate import _
import openerp.netsvc
import Image
import urlparse
import logging
_logger = logging.getLogger(__name__)

class shipping_response_returns(osv.osv):
    _name = 'shipping.response.returns'

    def generate_tracking_no(self, cr, uid, ids, context={}, error=True):
        import os; _logger.info("server name: %s", os.uname()[1])
        try:
            ids_obj = self.browse(cr,uid,ids[0])
            return_obj=ids_obj.return_id.sales_return_id
            shippingresp_lnk = self.browse(cr,uid,ids[0])
            return_order_obj=self.pool.get('return.order')
            ref=return_order_obj.browse(cr,uid,return_obj.id).name
            linked_sale_order=return_order_obj.browse(cr,uid,return_obj.id).linked_sale_order.name
            ### based on stock.pickings type
            if return_obj.linked_sale_order:
                so_state = return_obj.linked_sale_order.state
                if so_state != 'done':
                    raise osv.except_osv(_('Warning!'),_('Products are not Deliverd yet.You can\'t send shipping label for exchange before delivering Product'))
#            tracking_ref=return_obj.carrier_tracking_ref
            if ids_obj:
                cust_address = return_obj.partner_shipping_id
                if not cust_address:
                    if error:
                        raise osv.except_osv(_('Error'), _('Customer Address not defined!'),)
                    else:
                        return False
                if not (cust_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Customer Name."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Customer City."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Customer Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Customer Country."))
                shipper = Address(cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                ### Recipient
#                warehouse_address = return_obj.source_location.address_id
                warehouse_address = ids_obj.return_id.warehouse_location_id
                if not warehouse_address:
                    if error:
                        raise osv.except_osv(_('Error'), _('Shipper Address not defined!'),)
                    else:
                        return False
                if not (warehouse_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Location Name."))
                if not warehouse_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Location Zip."))
                if not warehouse_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Location Country."))
                receipient = Address(warehouse_address.name, warehouse_address.street, warehouse_address.city, warehouse_address.state_id.code or '', warehouse_address.zip, warehouse_address.country_id.code, warehouse_address.street2 or '', warehouse_address.phone or '', warehouse_address.email, warehouse_address.name)
                if shippingresp_lnk.type.lower() == 'fedex':
                    shippingfedex_obj = self.pool.get('shipping.fedex')
                    shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
                    if not shippingfedex_id:
                        raise osv.except_osv(_('Error'), _('Default Fedex settings not defined'))
                    else:
                        shippingfedex_id = shippingfedex_id[0]
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',shippingresp_lnk.name),('is_fedex','=',True)])
                    if not carrier_ids:
                        if error:
                            raise osv.except_osv(_('Error'), _('Shipping service output settings not defined'))
                        return False
                    print"refref",type(ref)
                    shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
                    account_no = shippingfedex_ptr.account_no
                    key = shippingfedex_ptr.key
                    password = shippingfedex_ptr.password
                    meter_no = shippingfedex_ptr.meter_no
                    is_test = shippingfedex_ptr.test
                    CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
                    # This is the object that will be handling our tracking request.
                    # We're using the FedexConfig object from example_config.py in this dir.
                    shipment = FedexProcessShipmentRequest(CONFIG_OBJ)
                    # This is very generalized, top-level information.
                    # REGULAR_PICKUP, REQattachUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
                    fedex_servicedetails = shippingresp_lnk.return_id
                    shipment.RequestedShipment.DropoffType = fedex_servicedetails.dropoff_type_fedex #'REGULAR_PICKUP'
                    # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
                    # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
                    shipment.RequestedShipment.ServiceType = fedex_servicedetails.service_type_fedex #'PRIORITY_OVERNIGHT'
                    # What kind of package this will be shipped in.
                    # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
                    shipment.RequestedShipment.PackagingType = fedex_servicedetails.packaging_type_fedex  #'FEDEX_PAK'
                    # No idea what this is.
                    # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
#                    shipment.RequestedShipment.PackageDetail = fedex_servicedetails.package_detail_fedex #'INDIVIDUAL_PACKAGES'
                    # Shipper contact info.
                    shipment.RequestedShipment.Shipper.Contact.PersonName = shipper.name #'Sender Name'
                    shipment.RequestedShipment.Shipper.Contact.CompanyName = shipper.company_name #'Some Company'
                    shipment.RequestedShipment.Shipper.Contact.PhoneNumber = shipper.phone #'9012638716'
                    # Shipper address.
                    shipment.RequestedShipment.Shipper.Address.StreetLines = shipper.address1 #['Address Line 1']
                    shipment.RequestedShipment.Shipper.Address.City =  shipper.city #'Herndon'
                    shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = shipper.state_code #'VA'
                    shipment.RequestedShipment.Shipper.Address.PostalCode = shipper.zip #'20171'
                    shipment.RequestedShipment.Shipper.Address.CountryCode = shipper.country_code #'US'
                    shipment.RequestedShipment.Shipper.Address.Residential = False
                    # Recipient contact info.
                    shipment.RequestedShipment.Recipient.Contact.PersonName = receipient.name #'Recipient Name'
                    shipment.RequestedShipment.Recipient.Contact.CompanyName = receipient.company_name #'Recipient Company'
                    shipment.RequestedShipment.Recipient.Contact.PhoneNumber = receipient.phone #'9012637906'
                    # Recipient address
                    shipment.RequestedShipment.Recipient.Address.StreetLines = receipient.address1 #['Address Line 1']
                    shipment.RequestedShipment.Recipient.Address.City = receipient.city #'Herndon'
                    shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = receipient.state_code #'VA'
                    shipment.RequestedShipment.Recipient.Address.PostalCode = receipient.zip #'20171'
                    shipment.RequestedShipment.Recipient.Address.CountryCode = receipient.country_code #'US'
                    # This is needed to ensure an accurate rate quote with the response.
                    shipment.RequestedShipment.Recipient.Address.Residential = False
                    # Who pays for the shipment?
                    # RECIPIENT, SENDER or THIRD_PARTY
                    shipment.RequestedShipment.ShippingChargesPayment.PaymentType = fedex_servicedetails.payment_type_fedex #'SENDER'
                    shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = shippingfedex_ptr.account_no #####cox gen2 changes saziya
                    shipment.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes = 'RETURN_SHIPMENT'
                    shipment.RequestedShipment.SpecialServicesRequested.ReturnShipmentDetail.ReturnType = 'PRINT_RETURN_LABEL'
#                    shipment.RequestedShipment.SpecialServicesRequested.ReturnShipmentDetail.Rma.Number = ref  ##cox gen2 type number is removed from wsdl
                    if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType ='SENDER'
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.AccountNumber =shippingfedex_ptr.account_no
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.CountryCode =shipper.country_code
                        shipment.RequestedShipment.CustomsClearanceDetail.DocumentContent ='NON_DOCUMENTS'
                        shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount =fedex_servicedetails.customsvalue
                        shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency =fedex_servicedetails.currency_id.name
                        move_ids=stockmove_obj.search(cr,uid,[('picking_id','=',shippingresp_lnk.picking_id.id)])
                        if move_ids:
                            for move in move_ids:
                                move_line=stockmove_obj.browse(cr,uid,move)
                                commodities_obj=shipment.create_wsdl_object_of_type('Commodity')
                                commodities_obj.NumberOfPieces=int(move_line.product_uos_qty)
                                commodities_obj.Description=move_line.name
                                commodities_obj.CountryOfManufacture='US'
                                commodities_obj.Weight.Units=fedex_servicedetails.weight_unit
                                commodities_obj.Weight.Value= str(move_line.product_id.weight)
                                commodities_obj.Quantity=int(move_line.product_qty)
                                commodities_obj.QuantityUnits='EA'
                                commodities_obj.UnitPrice.Currency=fedex_servicedetails.currency_id.name
                                commodities_obj.UnitPrice.Amount =str(move_line.product_id.price_extra)
                                commodities_obj.CustomsValue.Currency=fedex_servicedetails.currency_id.name
                                commodities_obj.CustomsValue.Amount=str(fedex_servicedetails.customsvalue)
                                shipment.RequestedShipment.CustomsClearanceDetail.Commodities=commodities_obj
                    # Specifies the label type to be returned.
                    # LABEL_DATA_ONLY or COMMON2D
                    shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
                    # Specifies which format the label file will be sent to you in.
                    # DPL, EPL2, PDF, PNG, ZPLII
                    shipment.RequestedShipment.LabelSpecification.ImageType = 'PNG'
                    # To use doctab stocks, you must change ImageType above to one of the
                    # label printer formats (ZPLII, EPL2, DPL).
                    # See documentation for paper types, there quite a few.
                    shipment.RequestedShipment.LabelSpecification.LabelStockType = 'PAPER_4X6'
                    # This indicates if the top or bottom of the label comes out of the
                    # printer first.
                    # BOTTOM_EDGE_OF_TEXT_FIRST or TOP_EDGE_OF_TEXT_FIRST
                    shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'BOTTOM_EDGE_OF_TEXT_FIRST'
                    package1_weight = shipment.create_wsdl_object_of_type('Weight')
                    # Weight, in pounds.
                    package1_weight.Value = fedex_servicedetails.weight_package #1.0
                    package1_weight.Units = "LB"
                    package1_dimensions = shipment.create_wsdl_object_of_type('Dimensions')
                    package1_dimensions.Length = int(fedex_servicedetails.pack_length)
                    package1_dimensions.Width = int(fedex_servicedetails.pack_width)
                    package1_dimensions.Height = int(fedex_servicedetails.pack_height)
                    package1_dimensions.Units = "IN"
                    package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                    package1.Weight = package1_weight
                    package1.Dimensions=package1_dimensions
                    package1.PhysicalPackaging = fedex_servicedetails.physical_packaging_fedex
                    shipment.add_package(package1)
                    print"shipment",shipment
#                    try:
                    shipment.send_request()
#                    except Exception, e:
#                        if error:
#                            raise osv.except_osv(_('Error'), _('%s' % (e,)))
                    fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
		    label_package_barcode = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].OperationalDetail.Barcodes.StringBarcodes[0].Value	 ##cox gen2 added new element OperationalDetail
#                    # Net shipping costs.
                    if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
                    else:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
#                    # This will be the file we write the label out to.
                    fedex_attachment_pool = self.pool.get('ir.attachment')
                    fedex_data_attach = {
                        'name': 'FedexLabel.png',
                        'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                        'description': 'Label',
                        'res_name': return_obj.name,
                        'res_model':'return.order' ,
                        'res_id': return_obj.id,
                    }
                    fedex_attach_id = fedex_attachment_pool.search(cr,uid,[('res_id','=',return_obj.id),('res_name','=',return_obj.name)])
                    if not fedex_attach_id:
                        fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                    else:
                        fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
                        fedex_attach_id = fedex_attach_id[0]
                    if fedexTrackingNumber:
                        note=''
                        note+='Dimension : '+str(fedex_servicedetails.pack_length)+'X'+str(fedex_servicedetails.pack_width)+'X'+str(fedex_servicedetails.pack_height)+'\n'\
                            +'Trcking Number : '+str(fedexTrackingNumber)+'\n'\
                            + 'Rate : '+  str(fedexshippingrate)
                        write_result = return_obj.write({'carrier_tracking_ref':fedexTrackingNumber, 'shipping_info': note,'label_package_barcode':label_package_barcode})
            else:
               raise osv.except_osv(_('Warning !'),_("This shipping quotes has been already accepted"))
        except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        self.write(cr,uid,ids[0],{'selected':True})
        if context.get('call_from','') == 'wizard':
            return{
                    'name':_("Sales Return"),
                    'view_mode': 'form',
                    'res_id': return_obj.id,
                    'view_type': 'form',
                    'res_model': 'return.order',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'domain': '[]',
                    'context': context,}
        else:
            context['active_id'] = return_obj.id
            context['active_ids'] = [return_obj.id]
            context['active_model'] = 'return.order'
	    context['internal']	 = True
            return{
                    'name':_("Send Email"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'send.mail.manual',
                    'nodestroy': True,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'domain': '[]',
                    'context': context,}
            
    _order = 'sr_no'
    _columns = {
        'name': fields.char('Service Type', size=100, readonly=True),
        'type': fields.char('Shipping Type', size=64, readonly=True),
        'rate': fields.char('Rate', size=64, readonly=True),
        'weight' : fields.float('Weight'),
        'cust_default' : fields.boolean('Customer Default'),
        'sys_default' : fields.boolean('System Default'),
        'sr_no' : fields.integer('Sr. No'),
        'selected' : fields.boolean('Selected'),
        'return_id' : fields.many2one('shipping.returns','Shipping Returns'),
    }
    _defaults = {
        'sr_no': 9,
        'selected': False
    }
shipping_response_returns()

class shipping_returns(osv.osv):
    _name = "shipping.returns"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',context=None, toolbar=False, submenu=False):
        res = super(shipping_returns, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context is None:
           context={}
        active_id = context.get('active_id',False)
        if active_id:
            return_id_obj = self.pool.get('return.order').browse(cr,uid,active_id)
#            if return_id_obj.return_type != 'exchange':
#                raise osv.except_osv(_('Error'), _('You can Generate Label if Return Type is Exchange'))
            if return_id_obj.state == 'done':
                raise osv.except_osv(_('Error'), _('You cannot Generate Label Because state is Done'))
            if not return_id_obj.order_line:
                raise osv.except_osv(_('Error'), _('No Order Line is Defined'))
        return res

    def default_get(self, cr, uid, fields, context=None):
        active_id=context.get('active_id',False)
        prod_obj = self.pool.get('product.product')
        res = super(shipping_returns, self).default_get(cr, uid, fields, context=context)
        print"res",res
        if active_id:
            weight = 0.0
            return_id_obj = self.pool.get('return.order').browse(cr,uid,active_id)
            type = return_id_obj.return_type
            for each_line in return_id_obj.order_line:
                if type == 'exchange':
                    weight += float(each_line.product_id.weight_net) * float(each_line.product_uom_qty)
                    if not res.get('pack_length',0.0) and (each_line.product_id.prod_length):
                       res.update({'pack_length': each_line.product_id.prod_length})
                    if not res.get('pack_width',0.0) and (each_line.product_id.prod_width):
                       res.update({'pack_width': each_line.product_id.prod_width})
                    if not res.get('pack_height',0.0) and (each_line.product_id.prod_height):
                       res.update({'pack_height': each_line.product_id.prod_height})
                else:
                    cr.execute('select product_id from sale_order_line where parent_so_line_id=%s'%(each_line.sale_line_id.id))
                    product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if product_ids:
                        for prod_brw in prod_obj.browse(cr,uid,product_ids):
                            if prod_brw.type == 'product':
                                weight += float(prod_brw.weight_net)
                                if not res.get('pack_length',0.0) and (prod_brw.prod_length):
                                   res.update({'pack_length': prod_brw.prod_length})
                                if not res.get('pack_width',0.0) and (prod_brw.prod_width):
                                   res.update({'pack_width': prod_brw.prod_width})
                                if not res.get('pack_height',0.0) and (prod_brw.prod_height):
                                   res.update({'pack_height': prod_brw.prod_height})
                    else:
                        if each_line.product_id.type == 'product':
                            weight += float(each_line.product_id.weight_net) * float(each_line.product_uom_qty)
                            if not res.get('pack_length',0.0) and (each_line.product_id.prod_length):
                               res.update({'pack_length': each_line.product_id.prod_length})
                            if not res.get('pack_width',0.0) and (each_line.product_id.prod_width):
                               res.update({'pack_width': each_line.product_id.prod_width})
                            if not res.get('pack_height',0.0) and (each_line.product_id.prod_height):
                               res.update({'pack_height': each_line.product_id.prod_height})
            if weight == 0:
                weight=1
            res.update({'sales_return_id':active_id,'weight_package':weight})
            if not res.get('shipping_type'):
                return res
            shipping_id=self.generate_shipping_new(cr,uid,res,context)
            if shipping_id:
                res.update({'response_usps_ids':[(4,shipping_id)]})
                cr.commit()
        return res

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, error=True,fed_length=None,fed_width=None,fed_height=None, context=None):
        if 'fedex_active' in context.keys() and context['fedex_active'] == False:
            return True
        shippingfedex_obj = self.pool.get('shipping.fedex')
        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
        if not shippingfedex_id:
            if error:
                raise osv.except_osv(_('Error'), _('Default FedEx settings not defined'))
            else:
                return False
        else:
            shippingfedex_id = shippingfedex_id[0]
        shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
        account_no = shippingfedex_ptr.account_no
        key = shippingfedex_ptr.key
        password = shippingfedex_ptr.password
        meter_no = shippingfedex_ptr.meter_no
        is_test = shippingfedex_ptr.test
        CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
        rate_request = FedexRateServiceRequest(CONFIG_OBJ)
        rate_request.RequestedShipment.DropoffType = dropoff_type_fedex
        rate_request.RequestedShipment.ServiceType = service_type_fedex
        rate_request.RequestedShipment.PackagingType = packaging_type_fedex
#        rate_request.RequestedShipment.PackageDetail = package_detail_fedex
        rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
        rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
        rate_request.RequestedShipment.Shipper.Address.Residential = False
        rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
        rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
        rate_request.RequestedShipment.EdtRequestType = 'NONE'
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
        package1_weight = rate_request.create_wsdl_object_of_type('Weight')
        package1_weight.Value = weight
        package1_weight.Units = "LB"
        package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
        package1_dimensions.Length=int(fed_length)
        package1_dimensions.Width=int(fed_width)
        package1_dimensions.Height=int(fed_height)
        package1_dimensions.Units="IN"
        package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
        package1.Weight = package1_weight
        package1.Dimensions = package1_dimensions
        package1.PhysicalPackaging = physical_packaging_fedex
        rate_request.add_package(package1)
        rate_request.RequestedShipment.RequestedPackageLineItems[0].GroupPackageCount = 1 ##cox gen2 packageCaount should be atleast 1
        try:
            rate_request.send_request()
        except Exception, e:
            if error:
                raise Exception('%s' % (e))
            return False
        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            for surcharge in detail.ShipmentRateDetail.Surcharges:
                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
                    _logger.info("ODA rate_request charge: %s", surcharge.Amount.Amount)
        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            _logger.info("Net FedEx Charge: %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)
        fedex_res_vals = {
            'name' : service_type_fedex,
            'type' : 'FedEx',
            'rate' : rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount,
            'return_id' :ids[0], #Change the ids[0] when switch to create
            'weight' : weight,
#            'picking_id':ids[0][0],
            'sr_no' : 9
        }
        fedex_res_id = self.pool.get('shipping.response.returns').create(cr,uid,fedex_res_vals)
        if fedex_res_id:
            return fedex_res_id
        else:
            return False

    def create_quotes(self, cr, uid, ids, values, context={}):
        res_id = 0
        for vals in values.postage:
            quotes_vals = {
                'name' : vals['Service'],
                'type' : context['type'],
                'rate' : vals['Rate'],
                'picking_id' : ids[0], #Change the ids[0] when switch to create
                'weight' : values.weight,
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : vals['sr_no'],
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
        if res_id:
            return True
        else:
            return False

    def create_attachment(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        pdf_attach=[]
        for i in range(0,vals.package_count):
            data_attach = {
                    'name': 'UpsLabel_'+str(i+1)+'.'+ vals.image_format.lower() ,
                    'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image[i]))),
                    'description': 'Packing List',
                    'res_name': self.browse(cr,uid,ids[0]).name,
                    'res_model': 'stock.picking',
                    'res_id': ids[0],
                }
            datas=data_attach['datas']
            pdf_attach.append(datas)
            attach_id = attachment_pool.create(cr, uid, data_attach)
        return attach_id

    def generate_shipping_new(self, cr, uid, new, context={}):
        if context is None:
            context = {}
        try:
	        active_model=context.get('active_model',False)
        	active_id=context.get('active_id',False)
	        return_data=self.pool.get(active_model).browse(cr,uid,active_id)
        	return_obj=new
                print"new",new
                print"new['warehouse_location_id']",new['warehouse_location_id']
	        shipping_type = return_obj['shipping_type']
	        weight = return_obj['weight_package']
        	if weight<=0.0:
	            raise Exception('Package Weight Invalid!')
        ###based on stock.picking type
        	shipper_address = return_data.partner_shipping_id
	        if not shipper_address:
        	    if 'error' not in context.keys() or context.get('error',False):
	                raise Exception('Shop Address not defined!')
        	    else:
	                return False
        	if not (shipper_address.name):
	            raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
        	if not shipper_address.street:
	            raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
	        if not shipper_address.city:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
	        if not shipper_address.state_id.code:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
	        if not shipper_address.zip:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
	        if not shipper_address.country_id.code:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
	        shipper = Address(shipper_address.name , shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.name)
        ### Recipient
        ###based on stock.picking type
        	cust_address=self.pool.get('res.partner').browse(cr,uid,new['warehouse_location_id'])
        	if not cust_address:
	            if 'error' not in context.keys() or context.get('error',False):
        	        raise Exception('Reciepient Address not defined!')
	            else:
        	        return False
	        if not (cust_address.name):
        	    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
	        if not cust_address.city:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
	        if not cust_address.zip:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
	        if not cust_address.country_id.code:
        	    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
	        receipient = Address(cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
        	# Deleting previous quotes
	        shipping_res_obj = self.pool.get('shipping.response.returns')
        	shipping_res_ids = shipping_res_obj.search(cr,uid,[('return_id','=',new['sales_return_id'])])
	        if shipping_res_ids:
        	    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
	        if shipping_type == 'Fedex' or shipping_type == 'All':
        	    dropoff_type_fedex = new['dropoff_type_fedex']
	            service_type_fedex = new['service_type_fedex']
        	    packaging_type_fedex = new['packaging_type_fedex']
	            package_detail_fedex = new['package_detail_fedex']
        	    payment_type_fedex = new['payment_type_fedex']
	            physical_packaging_fedex =new['physical_packaging_fedex']
        	    shipper_postal_code = shipper.zip
	            shipper_country_code = shipper.country_code
        	    customer_postal_code = receipient.zip
	            customer_country_code = receipient.country_code
        	    fed_length = new['pack_length']
	            fed_width = new['pack_width']
        	    fed_height = new['pack_height']
	            error_required = True
        	    view_id_out=self.create(cr,uid,{})
	            cr.commit()
        	    shipping_res = self.generate_fedex_shipping(cr,uid,[view_id_out],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,error_required,fed_length,fed_width,fed_height,context)
	        if shipping_res:
        	    return shipping_res
	        else:
        	    return False
	except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))

    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        for id in ids:
            try:
                active_model=context.get('active_model',False)
                active_id=context.get('active_id',False)
                return_wizard = self.pool.get('shipping.returns').browse(cr,uid,id)
                return_obj=self.pool.get(active_model).browse(cr,uid,active_id)
                shipping_type = return_wizard.shipping_type
                weight = return_wizard.weight_package
                if weight<=0.0:
                    raise Exception('Package Weight Invalid!')
                ###based on stock.picking type
                shipper_address = return_obj.partner_shipping_id
                if not shipper_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise Exception('Shop Address not defined!')
                    else:
                        return False
                if not (shipper_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
                if not shipper_address.street:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
                if not shipper_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
                if not shipper_address.state_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
                if not shipper_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
                if not shipper_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
                shipper = Address(shipper_address.name , shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.name)
                ### Recipient
                ###based on stock.picking type
#                cust_address = return_obj.source_location and return_obj.source_location.address_id or False
                cust_address = return_wizard.warehouse_location_id
                if not cust_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise Exception('Reciepient Address not defined!')
                    else:
                        return False
                if not (cust_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
                receipient = Address(cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response.returns')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('return_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = return_wizard.dropoff_type_fedex
                    service_type_fedex = return_wizard.service_type_fedex
                    packaging_type_fedex = return_wizard.packaging_type_fedex
                    package_detail_fedex = return_wizard.package_detail_fedex
                    payment_type_fedex = return_wizard.payment_type_fedex
                    physical_packaging_fedex = return_wizard.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    fed_length = return_wizard.pack_length
                    fed_width = return_wizard.pack_width
                    fed_height = return_wizard.pack_height
                    error_required = True
                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,error_required,fed_length,fed_width,fed_height,context)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return {
                'name':_("Shipping Returns"),
                'view_mode': 'form',
                'res_id': ids[0],
                'view_type': 'form',
                'res_model': 'shipping.returns',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,}
    
    def _get_usd(self, cr, uid, context=None):
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False
    def get_return_location(self, cr, uid, context=None):
        #Initial Code
#        address_id =  False
#        location_obj = self.pool.get('stock.location')
#        search_return_location = location_obj.search(cr, uid, [('return_location','=',True)])
#        if search_return_location:
#            address_id = location_obj.browse(cr,uid,search_return_location[0]).partner_id
#            if address_id:
#                address_id = address_id.id
#                return address_id
        source_location_addr_id = False
        if context is None: context ={}
        if context and context.get('active_model','') =='return.order' and context.get('active_id',False):
            return_id_brw = self.pool.get('return.order').browse(cr,uid,context.get('active_id',False))
            source_location_addr_id = return_id_brw.source_location.partner_id
            if source_location_addr_id:
                source_location_addr_id = source_location_addr_id.id
        return source_location_addr_id

    _columns = {
        'use_shipping' : fields.boolean('Use Shipping'),
        'shipping_type' : fields.selection([('Fedex','Fedex')],'Shipping Type'),
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'dropoff_type_fedex' : fields.selection([
                ('REGULAR_PICKUP','REGULAR PICKUP'),
                ('REQUEST_COURIER','REQUEST COURIER'),
                ('DROP_BOX','DROP BOX'),
                ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
                ('STATION','STATION'),
            ],'Dropoff Type'),
        'service_type_fedex' : fields.selection([
#                ('EUROPE_FIRST_INTERNATIONAL_PRIORITY','EUROPE_FIRST_INTERNATIONAL_PRIORITY'),
                ('FEDEX_1_DAY_FREIGHT','FEDEX_1_DAY_FREIGHT'),
                ('FEDEX_2_DAY','FEDEX_2_DAY'),
                ('FEDEX_2_DAY_FREIGHT','FEDEX_2_DAY_FREIGHT'),
                ('FEDEX_3_DAY_FREIGHT','FEDEX_3_DAY_FREIGHT'),
                ('FEDEX_EXPRESS_SAVER','FEDEX_EXPRESS_SAVER'),
                ('STANDARD_OVERNIGHT','STANDARD_OVERNIGHT'),
                ('PRIORITY_OVERNIGHT','PRIORITY_OVERNIGHT'),
                ('FEDEX_GROUND','FEDEX_GROUND'),
		('FIRST_OVERNIGHT','FIRST_OVERNIGHT'),
		('GROUND_HOME_DELIVERY','GROUND_HOME_DELIVERY'),
#		('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY'),
#		('INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_ECONOMY_FREIGHT'),
#		('INTERNATIONAL_FIRST','INTERNATIONAL_FIRST'),
#		('INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY'),
#		('INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_PRIORITY_FREIGHT'),
#		('PRIORITY_OVERNIGHT','PRIORITY_OVERNIGHT'),
#		('SMART_POST','SMART_POST'),
#		('STANDARD_OVERNIGHT','STANDARD_OVERNIGHT'),
#		('FEDEX_FREIGHT','FEDEX_FREIGHT'),
#		('FEDEX_NATIONAL_FREIGHT','FEDEX_NATIONAL_FREIGHT'),
		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
           ],'Service Type'),
        'packaging_type_fedex' : fields.selection([
                ('FEDEX_BOX','FEDEX BOX'),
                ('FEDEX_PAK','FEDEX PAK'),
                ('FEDEX_TUBE','FEDEX_TUBE'),
                ('YOUR_PACKAGING','YOUR_PACKAGING'),
            ],'Packaging Type', help="What kind of package this will be shipped in"),
        'package_detail_fedex' : fields.selection([
                ('INDIVIDUAL_PACKAGES','INDIVIDUAL_PACKAGES'),
                ('PACKAGE_GROUPS','PACKAGE_GROUPS'),
                ('PACKAGE_SUMMARY','PACKAGE_SUMMARY'),
            ],'Package Detail'),
        'payment_type_fedex' : fields.selection([
                ('RECIPIENT','RECIPIENT'),
                ('SENDER','SENDER'),
                ('THIRD_PARTY','THIRD_PARTY'),
            ],'Payment Type', help="Who pays for the rate_request?"),
        'physical_packaging_fedex' : fields.selection([
                ('BAG','BAG'),
                ('BARREL','BARREL'),
                ('BOX','BOX'),
                ('BUCKET','BUCKET'),
                ('BUNDLE','BUNDLE'),
                ('CARTON','CARTON'),
                ('TANK','TANK'),
                ('TUBE','TUBE'),
            ],'Physical Packaging'),
        'shipping_label' : fields.binary('Logo'),
        'shipping_rate': fields.float('Shipping Rate'),
        'response_usps_ids' : fields.one2many('shipping.response.returns','return_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
        'checkbox': fields.boolean('Canada Post'),
#        'services': fields.many2one('service.name', 'Services'),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'customsvalue':fields.float('Custom Values'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'sales_return_id':fields.many2one('return.order'),
        'warehouse_location_id':fields.many2one('res.partner','Location Address'),
   }
    _defaults = {
        'use_shipping' : True,
        'shipping_type' : 'Fedex',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'packaging_type_fedex' : 'YOUR_PACKAGING',
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pack_length' : 0,
        'pack_width' : 0,
        'pack_height' : 0,
        'weight_unit':'LB',
        'currency_id':_get_usd,
        'warehouse_location_id':get_return_location,
    }
    def onchange_number_of_packages(self, cr, uid, ids, number_of_pack,context=None):
        tracking_ids=self.browse(cr,uid,ids[0]).tracking_ids
        obj_pack_track = self.pool.get('pack.track')
        for each_tracking_id in tracking_ids:
            obj_pack_track.unlink(cr, uid, each_tracking_id.id)
            tracking_ids= []
        number_of_pack=number_of_pack
        pack_track_obj=self.pool.get('pack.track')
        move_records,packages = [],[]
        if not tracking_ids:
            for i in range(0,number_of_pack):
                values = {
                'name':'Pack '+str(i+1),
                'picking_id':ids[0]
                }
                pack_id=pack_track_obj.create(cr,uid,values)
                packages.append(pack_id)
            for move_id in self.browse(cr,uid,ids[0]).move_lines:
                if number_of_pack==1:
                    move_records.append([1,move_id.id,{'pack_track_id':pack_id}])
                else:
                    move_records.append([1,move_id.id,{'pack_track_id':False}])
        return {'value':{'tracking_ids':packages,'move_lines':move_records}}

    def onchange_shipping_rates(self, cr, uid, ids, service_type,response_usps_ids,shipping_type,context=None):
        if ids:
            width = self.browse(cr,uid,ids[0]).pack_width
            delete_att_vals = []
            if response_usps_ids != []:
                for res_id in response_usps_ids:
                    cr.execute("delete from shipping_response where id=%s",(res_id[1],))
                    cr.commit()
            ### Assign Carrier to Delivery carrier if user has not selected
            carrier_ids=''
            if shipping_type:
                if shipping_type.lower() == 'fedex':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_fedex','=',True)])
                elif shipping_type.lower() == 'all':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    if canada_service_type:
                        service_type=canada_service_type
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,['|','|',('service_output','=',service_type),('name','=',service_type),('service_code','=',service_type)])
                ### Write this shipping respnse is selected
            vals = {'response_usps_ids' : delete_att_vals,
                    'pack_length' : width,
                    'pack_width' : width,
                    'pack_height' : width,
                    'carrier_id':carrier_ids and carrier_ids[0] or ''
                    }
            return {'value':vals}
        return {'value':{}}
shipping_returns()
