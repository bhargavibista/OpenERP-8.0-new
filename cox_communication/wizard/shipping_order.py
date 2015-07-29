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
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

#new class
class package_dimension(osv.osv):
    _name = 'package.dimension'
    _columns = {
        'name' : fields.char('Name' , required = True),
        'length': fields.float('Length',required = True),
        'width': fields.float('Width',required = True),
        'height': fields.float('Height',required = True),
        'weight': fields.float('Weight',required = True),
    }
    _defaults = {
        'length': 20,
        'width': 20,
        'height':6,
        'weight':1,
    }
package_dimension()
#new class
class similar_packages(osv.osv):
    _name = 'similar.packages'

    def _get_dimension_data(self, cr, uid, context=None):
        print"contexttttt0",context
        package_obj=self.pool.get('package.dimension')
        package_dim_id=package_obj.search(cr,uid,[])
        print"package_dim_idpackage_dim_id",package_dim_id
        return package_dim_id and package_dim_id[0] or False

    _columns = {
        'number_of_similar_packages' : fields.integer('Similar Packages'),
        'package_dim': fields.many2one('package.dimension','Package Dimension'),
        'picking_id':fields.many2one('shipping.order.processing','Picking id'),
    }

    _defaults = {
       'package_dim':_get_dimension_data,
       }
similar_packages()

class pre_shipping_process(osv.osv):
    _name = "pre.shipping.process"

    def process_shipping(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if ids:
            ids_obj =self.browse(cr,uid,ids[0])
#            context = dict(context, active_ids=ids, active_model='stock.picking')
            context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'))
            picking_id= context.get('active_ids')
            picking_obj=self.pool.get('stock.picking').browse(cr,uid,picking_id)
            vals={'picking_id':picking_id[0],  ##cox gen2
#                'weight_package':picking_obj.weight_net,
                'weight_package':1.4,
                'pack_length':9,
                'pack_width':6,
                'pack_height':3}
            shipping_process = self.pool.get("shipping.order.processing").create(cr, uid, vals, context=context)
            return {
                    'name':_("Generate Shipping Quotes"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'shipping.order.processing',
                    'res_id': shipping_process,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                }

    def donot_process_shipping(self,cr, uid, ids, context=None):
        if context is None: context = {}
        context = dict(context, active_ids=context.get('active_ids'), active_model=context.get('active_model'))
        picking_id=context.get('active_ids')
        picking_obj = self.pool.get('stock.picking')
        skip_barcode=picking_obj.browse(cr, uid, picking_id[0]).skip_barcode
        print"skip_barcode",skip_barcode
#        changes done for stock_partial
        partial_id = self.pool.get("stock.transfer_details").create(cr, uid, {'picking_id':picking_id[0]}, context=context)
        if skip_barcode:
            
            return {
                'name':_("Products to Process"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'stock.transfer_details',
                'res_id': partial_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
            }
        else:
            context.update({'partial_id':partial_id})
            picking_obj.make_picking_done(cr,uid,picking_id,context)
            return {
#                'name':_("Products to Process"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'stock.picking',
                'res_id': picking_id[0],
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': context,
            }
pre_shipping_process()

class shipping_response_processing(osv.osv):
    _name = 'shipping.response.processing'
    def generate_tracking_no(self, cr, uid, ids, context={}, error=True):
        import os; _logger.info("server name: %s", os.uname()[1])
#        try:
        rate=0.00
        boxes_total=''
        no_of_prints=0
        product_qty=0
        stockmove_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        fedexTrackingNumber = []
        shipment_date=''
        product_obj=self.pool.get('product.product')
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        ship_id=shippingresp_lnk.shipment_id
        print"ship_id",ship_id
        picking=shippingresp_lnk.shipment_id.picking_id
        cust_address = picking.partner_id
        use_mps=ship_id.use_mps
        picking_date=picking.min_date
        sale_id=picking.sale_id
        ship_product_id=product_obj.search(cr,uid,[('default_code','=','SHIP AND HANDLE')])
        if sale_id:
            for each in sale_id.order_line:
                product_id=each.product_id.id
                if (each.product_id.type=='product'):
                    product_qty=product_qty+each.product_uom_qty
                if (product_id==ship_product_id[0]):
                    rate=each.product_id.list_price
        else:
            for each in picking.move_lines:
                print each.product_qty
                product_qty += each.product_qty

        if picking_date:
            date_format=datetime.strptime(picking_date,"%Y-%m-%d %H:%M:%S")
            shipment_date=datetime.strftime(date_format,"%A-%B-%d-%Y")
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
        receipient = Address(cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
        weight = shippingresp_lnk.weight
        boxes_total=ship_id.total_packages
        ### Recipient
#                warehouse_address = return_obj.source_location.address_id
        warehouse_address = ship_id.warehouse_location_id
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
        shipper = Address(warehouse_address.name, warehouse_address.street, warehouse_address.city, warehouse_address.state_id.code or '', warehouse_address.zip, warehouse_address.country_id.code, warehouse_address.street2 or '', warehouse_address.phone or '', warehouse_address.email, warehouse_address.name)
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
            shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
            account_no = shippingfedex_ptr.account_no
            key = shippingfedex_ptr.key
            password = shippingfedex_ptr.password
            meter_no = shippingfedex_ptr.meter_no
            is_test = shippingfedex_ptr.test
            CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
#                new lines added
            master_tracking = False
            type = False
            count_package = 0
            ##cox gen2 changed the below condition
            if not use_mps:
                similar_packages = [0]
            else:
                similar_packages = ship_id.similar_packages
            ###
            for line in similar_packages:
                if use_mps:
                    packages = line.number_of_similar_packages+1
                else:
                    packages = 2
                for i in range(1,packages):
                    count_package += 1
#             new lines added
            # This is the object that will be handling our tracking request.
            # We're using the FedexConfig object from example_config.py in this dir.
                    shipment = FedexProcessShipmentRequest(CONFIG_OBJ)
                    # This is very generalized, top-level information.
                    # REGULAR_PICKUP, REQattachUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
                    shipment.RequestedShipment.DropoffType = ship_id.dropoff_type_fedex #'REGULAR_PICKUP'
#                        print "ship_id.dropoff_type_fedex",ship_id.service_type_fedex
                    # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
                    # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
                    shipment.RequestedShipment.ServiceType = ship_id.service_type_fedex #'PRIORITY_OVERNIGHT'
                    # What kind of package this will be shipped in.
                    # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
                    shipment.RequestedShipment.PackagingType = ship_id.packaging_type_fedex  #'FEDEX_PAK'
                    # No idea what this is.
                    # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
    #                    shipment.RequestedShipment.PackageDetail = ship_id.package_detail_fedex #'INDIVIDUAL_PACKAGES'
                    # Shipper contact info.
                    "shipper.name shipper.name ",shipper.name
                    if picking.picking_type_id.code=='internal' or picking.picking_type_id.code=='outgoing':
                        shipment.RequestedShipment.Shipper.Contact.PersonName = 'COX COMMUNICATIONS'#'Sender Name'
                        shipment.RequestedShipment.Shipper.Contact.CompanyName = 'Flareplay Warehouse' #'Some Company'
                    else:
                        shipment.RequestedShipment.Shipper.Contact.CompanyName = shipper.name #'Some Company'
                    shipment.RequestedShipment.Shipper.Contact.PhoneNumber = shipper.phone #'9012638716'
                    # Shipper address.
                    shipment.RequestedShipment.Shipper.Address.StreetLines = shipper.address1#['Address Line 1']
                    shipment.RequestedShipment.Shipper.Address.City =  shipper.city #'Herndon'
                    shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = shipper.state_code #'VA'
                    shipment.RequestedShipment.Shipper.Address.PostalCode = shipper.zip #'20171'
                    shipment.RequestedShipment.Shipper.Address.CountryCode = shipper.country_code #'US'
                    shipment.RequestedShipment.Shipper.Address.Residential = False
                    # Recipient contact info.
#                        shipment.RequestedShipment.Recipient.Contact.PersonName = receipient.name #'Recipient Name'
                    if picking.picking_type_id.code=='internal':
                        shipment.RequestedShipment.Recipient.Contact.PersonName = receipient.name #'Recipient Name'
                        shipment.RequestedShipment.Recipient.Contact.CompanyName = 'COX SOLUTIONS STORE'
                    else:
                        shipment.RequestedShipment.Recipient.Contact.CompanyName =receipient.company_name
                    #'Recipient Company'
                    shipment.RequestedShipment.Recipient.Contact.PhoneNumber = receipient.phone #'9012637906'
                    # Recipient address
                    shipment.RequestedShipment.Recipient.Address.StreetLines = receipient.address1 + ' ,' + receipient.address2 #['Address Line 1']
                    shipment.RequestedShipment.Recipient.Address.City = receipient.city #'Herndon'
                    shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = receipient.state_code #'VA'
                    shipment.RequestedShipment.Recipient.Address.PostalCode = receipient.zip #'20171'
                    shipment.RequestedShipment.Recipient.Address.CountryCode = receipient.country_code #'US'
                    # This is needed to ensure an accurate rate quote with the response.
                    shipment.RequestedShipment.Recipient.Address.Residential = False
                    # Who pays for the shipment?
                    # RECIPIENT, SENDER or THIRD_PARTY
                    print"shippingfedex_ptr.account_no",shippingfedex_ptr.account_no
                    shipment.RequestedShipment.ShippingChargesPayment.PaymentType = ship_id.payment_type_fedex #'SENDER'
                    shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = shippingfedex_ptr.account_no #####cox gen2 changes saziya
                    if ship_id.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType ='SENDER'
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.AccountNumber =shippingfedex_ptr.account_no
                        shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.CountryCode =shipper.country_code
                        shipment.RequestedShipment.CustomsClearanceDetail.DocumentContent ='NON_DOCUMENTS'
                        shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount =ship_id.customsvalue
                        shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency =ship_id.currency_id.name
                        move_ids=stockmove_obj.search(cr,uid,[('picking_id','=',shippingresp_lnk.picking_id.id)])
                        if move_ids:
                            for move in move_ids:
                                move_line=stockmove_obj.browse(cr,uid,move)
                                commodities_obj=shipment.create_wsdl_object_of_type('Commodity')
                                commodities_obj.NumberOfPieces=int(move_line.product_uos_qty)
                                commodities_obj.Description=move_line.name
                                commodities_obj.CountryOfManufacture='US'
                                commodities_obj.Weight.Units=ship_id.weight_unit
                                commodities_obj.Weight.Value= str(move_line.product_id.weight)
                                commodities_obj.Quantity=int(move_line.product_qty)
                                commodities_obj.QuantityUnits='EA'
                                commodities_obj.UnitPrice.Currency=ship_id.currency_id.name
                                commodities_obj.UnitPrice.Amount =str(move_line.product_id.price_extra)
                                commodities_obj.CustomsValue.Currency=ship_id.currency_id.name
                                commodities_obj.CustomsValue.Amount=str(ship_id.customsvalue)
                                shipment.RequestedShipment.CustomsClearanceDetail.Commodities=commodities_obj
                    # Specifies the label type to be returned.
                    # LABEL_DATA_ONLY or COMMON2D
                    shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
                    # Specifies which format the label file will be sent to you in.
                    # DPL, EPL2, PDF, PNG, ZPLII
#                        Image format
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
#                        # Weight, in pounds.
#                        package1_weight.Value = ship_id.weight_package #1.0
#                        package1_weight.Units = "LB"
            #As Package count is updated by +1 for every request its made 0 for each time
                    shipment.RequestedShipment.PackageCount = 0
                    package1_weight = shipment.create_wsdl_object_of_type('Weight')
                    # Weight, in pounds.
                    package1_weight.Units = "LB"
                    if use_mps:
                        package1_weight.Value = line.package_dim.weight
                        pack_dim = line.package_dim
                        fed_length = pack_dim.length
                        fed_width = pack_dim.width
                        fed_height = pack_dim.height
                        fed_weight= pack_dim.weight
                    else:
                        package1_weight.Value=ship_id.weight_package#1.0
                        fed_length = ship_id.pack_length
                        fed_width = ship_id.pack_width
                        fed_height = ship_id.pack_height

                    package1_dimensions = shipment.create_wsdl_object_of_type('Dimensions')
                    package1_dimensions.Length = int(fed_length)
                    package1_dimensions.Width = int(fed_width)
                    package1_dimensions.Height = int(fed_height)
                    package1_dimensions.Units = "IN"
                    package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                    package1.Weight = package1_weight
                    package1.Dimensions=package1_dimensions
                    package1.PhysicalPackaging = ship_id.physical_packaging_fedex
                    _logger.info("Package Dimensions: %s", package1_dimensions)
                    shipment.add_package(package1)
                    if use_mps:
                        if count_package==1:
                            shipment.RequestedShipment.TotalWeight.Value = ship_id.total_weight
                            shipment.RequestedShipment.PackageCount = int(ship_id.total_packages)
                            shipment.RequestedShipment.RequestedPackageLineItems[0].SequenceNumber=count_package
                        else:
                            shipment.RequestedShipment.RequestedPackageLineItems[0].SequenceNumber=count_package
                            shipment.RequestedShipment.MasterTrackingId.TrackingIdType = type
                            if master_tracking:
                                shipment.RequestedShipment.MasterTrackingId.TrackingNumber= int(master_tracking)
                    _logger.info("Requested Shipment: %s", shipment.RequestedShipment)
                    try:
                        shipment.send_request()
                    except Exception, e:
                        if error:
                            raise osv.except_osv(_('Error'), _('%s' % (e,)))
                    if use_mps:
                        type = shipment.response.CompletedShipmentDetail.MasterTrackingId.TrackingIdType
                        master_tracking = shipment.response.CompletedShipmentDetail.MasterTrackingId.TrackingNumber
                    fedexTrackingNumber.append(shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber)
                    # Net shipping costs.
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
                # This will be the file we write the label out to.
                    fedex_attachment_pool = self.pool.get('ir.attachment')
                    fedex_data_attach = {
                        'name': picking.name+'PickingLabel.png',
                        'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                        'description': 'Label',
                        'res_name': picking.name,
        #                    'res_model':'stock.picking.out' ,
                        'res_model':'stock.picking' if picking.picking_type_id.code=="outgoing" else 'stock.picking',
                        'res_id': picking.id,
                    }
#                        if not fedex_attach_id:
                    fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                    context['attach_id'] = int(fedex_attach_id)
                    context['tracking_no'] = fedexTrackingNumber
#                        else:
#                                fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
#                                fedex_attach_id = fedex_attach_id[0]
        if ship_id.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
            if shipment.response.CompletedShipmentDetail.ShipmentRating:
                fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
        else:
                fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount

        if fedexTrackingNumber:
            cnt_list=0
            cnt_list=len(fedexTrackingNumber)
            vals={}

            vals={
                'shipping_type':ship_id.shipping_type,
                'weight_package':ship_id.weight_package,
                'dropoff_type_fedex':ship_id.dropoff_type_fedex,
                'service_type_fedex':ship_id.service_type_fedex,
                'packaging_type_fedex':ship_id.packaging_type_fedex,
                'package_detail_fedex':ship_id.package_detail_fedex,
                'payment_type_fedex':ship_id.payment_type_fedex,
                'physical_packaging_fedex':ship_id.physical_packaging_fedex,
                'pack_length':ship_id.pack_length,
                'pack_width':ship_id.pack_width,
                'pack_height':ship_id.pack_height,
                'carrier_tracking_ref':fedexTrackingNumber[0],
                'shipping_rate':rate,
                'ship_date':shipment_date,
                'total_boxes':boxes_total,
                'label_recvd': True,
                'child_tracking_ids':fedexTrackingNumber,
                'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))),
                'no_of_prints':cnt_list,
                'no_of_prdct_units':product_qty,
                'print_label':True,
                }

            write_result = picking_obj.write(cr,uid,picking.id,vals)
            context.update({'active_id':picking.id, 'active_ids':[picking.id],'active_model':'stock.picking' if picking.picking_type_id.code=="outgoing" else 'stock.picking'})
            print"contextcontextcontextcontext",context
#                label_string ='"""'+str(b64decode(ascii_label_data))+'"""'
# printing label after creating attacjments
#                print_label=vals.get('print_label')
#                if (print_label==True):
#                    if (picking.type=="out"):
#                        self.pool.get('stock.picking.out').print_label(cr,uid,[picking.id],context)
#                    else:
#                        self.pool.get('stock.picking').print_label(cr,uid,[picking.id],context)
        else:
            raise osv.except_osv(_('Warning !'),_("This shipping quotes has been already accepted"))
#        except Exception, exc:
#                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        self.write(cr,uid,ids[0],{'selected':True})
#        return {'type': 'ir.actions.act_window_close'}
        return{
                'name':_("Mail Option"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'send.mail.option',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,}
#        return{
#                'name':_("Delivery Order"),
#                'view_mode': 'form',
#                'res_id': picking.id,
#                'view_type': 'form',
#                'res_model': 'stock.picking.out',
#                'type': 'ir.actions.act_window',
#                'nodestroy': True,
#                'target': 'current',
#                'domain': '[]',
#                'context': context,}
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
        'shipment_id' : fields.many2one('shipping.order.processing','Shipping Returns'),
    }
    _defaults = {
        'sr_no': 9,
        'selected': False
    }
shipping_response_processing()

class shipping_order_processing(osv.osv):
    _name = "shipping.order.processing"

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, error=True,fed_length=None,fed_width=None,fed_height=None, context=None):
        
        if 'fedex_active' in context.keys() and context['fedex_active'] == False:
            return True
        shippingfedex_obj = self.pool.get('shipping.fedex')
        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
        stockpicking_lnk = self.browse(cr,uid,ids[0])
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
#        rate_request.RequestedShipment.PackageDetailType = package_detail_fedex  ##cox gen2 changes
        rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
        rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
        rate_request.RequestedShipment.Shipper.Address.Residential = False
        rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
        rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
        rate_request.RequestedShipment.EdtRequestType = 'NONE'
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
#        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
        ############## Rate Request for MULTIPLE PACKAGE SHIPMENT###############################
        total_packages = stockpicking_lnk.total_packages
        print"total_packages",total_packages
        if total_packages:
            rate_request.RequestedShipment.PackageCount = int(total_packages)
        similar_packages = stockpicking_lnk.similar_packages
        use_mps = stockpicking_lnk.use_mps
        if use_mps:
            rate_request.RequestedShipment.TotalWeight.Value = weight
        if use_mps and package_detail_fedex=="PACKAGE_GROUPS":
            
            line_count = 0
            group_count = 0
            for line in similar_packages:
                group_count += 1
                package_dim = line.package_dim
                package1_weight = rate_request.create_wsdl_object_of_type('Weight')
                package1_weight.Value = package_dim.weight
                package1_weight.Units = "LB"
                _logger.info("Package weight: %s", package1_weight)
                package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
                package1_dimensions.Length=int(package_dim.length)
                package1_dimensions.Width=int(package_dim.width)
                package1_dimensions.Height=int(package_dim.height)
                package1_dimensions.Units="IN"
                _logger.info("Package dimensions: %s", package1_dimensions)
                package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
                package1.Weight = package1_weight
                package1.Dimensions = package1_dimensions
                #can be other values this is probably the most common
                package1.PhysicalPackaging = physical_packaging_fedex
                # Un-comment this to see the other variables you may set on a package.
                #print package1
                # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
                # increments the package count and total weight of the rate_request for you.
                rate_request.add_package(package1)
                rate_request.RequestedShipment.RequestedPackageLineItems[line_count].GroupNumber = group_count
                rate_request.RequestedShipment.RequestedPackageLineItems[line_count].GroupPackageCount = line.number_of_similar_packages
                line_count += 1
                rate_request.RequestedShipment.PackageCount -= 1
        else:
            package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
            package1_weight = rate_request.create_wsdl_object_of_type('Weight')
            package1_weight.Value = stockpicking_lnk.weight_package
            package1_weight.Units = "LB"
            _logger.info("Package weight: %s", package1_weight)
            package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
            package1_dimensions.Length=int(stockpicking_lnk.pack_length)
            package1_dimensions.Width=int(stockpicking_lnk.pack_width)
            package1_dimensions.Height=int(stockpicking_lnk.pack_height)
            package1_dimensions.Units="IN"
            _logger.info("Package dimensions: %s", package1_dimensions)
            package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
            package1.Weight = package1_weight
            package1.Dimensions = package1_dimensions
            package1.Weight = package1_weight
            package1.Dimensions = package1_dimensions
            package1.PhysicalPackaging = physical_packaging_fedex
            rate_request.add_package(package1)
            print"rate_request.RequestedShipment.RequestedPackageLineItems",rate_request.RequestedShipment.RequestedPackageLineItems
            rate_request.RequestedShipment.RequestedPackageLineItems[0].GroupPackageCount = 1 ##cox gen2 packageCaount should be atleast 1
        print "rate_request...............",rate_request.RequestedShipment
#new lines added
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
            'shipment_id' :ids[0], #Change the ids[0] when switch to create
            'weight' : weight,
#            'picking_id':ids[0][0],
            'sr_no' : 9
        }
        fedex_res_id = self.pool.get('shipping.response.processing').create(cr,uid,fedex_res_vals)
        if fedex_res_id:
            return fedex_res_id
        else:
            return False

#    def create_quotes(self, cr, uid, ids, values, context={}):
#        res_id = 0
#        for vals in values.postage:
#            quotes_vals = {
#                'name' : vals['Service'],
#                'type' : context['type'],
#                'rate' : vals['Rate'],
#                'picking_id' : ids[0], #Change the ids[0] when switch to create
#                'weight' : values.weight,
#                'sys_default' : False,
#                'cust_default' : False,
#                'sr_no' : vals['sr_no'],
#            }
#            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
#        if res_id:
#            return True
#        else:
#            return False
#
#    def create_attachment(self, cr, uid, ids, vals, context={}):
#        attachment_pool = self.pool.get('ir.attachment')
#        pdf_attach=[]
#        for i in range(0,vals.package_count):
#            data_attach = {
#                    'name': 'UpsLabel_'+str(i+1)+'.'+ vals.image_format.lower() ,
#                    'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image[i]))),
#                    'description': 'Packing List',
#                    'res_name': self.browse(cr,uid,ids[0]).name,
#                    'res_model': 'stock.picking',
#                    'res_id': ids[0],
#                }
#            datas=data_attach['datas']
#            pdf_attach.append(datas)
#            attach_id = attachment_pool.create(cr, uid, data_attach)
#        return attach_id


    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        for id in ids:
            try:
                active_model=context.get('active_model',False)
                active_id=context.get('active_id',False)
                shipping_wizard = self.browse(cr,uid,id)
                picking_obj=self.pool.get(active_model).browse(cr,uid,active_id)
                shipping_type = shipping_wizard.shipping_type
                weight = shipping_wizard.weight_package
                use_mps = shipping_wizard.use_mps
                count_package= 0
                if use_mps:
                    similar_package_brw = shipping_wizard.similar_packages[count_package]
                    weight = shipping_wizard.total_weight
                else:
                    weight = shipping_wizard.weight_package
                if weight<=0.0:
                    raise Exception('Package Weight Invalid!')
                ###based on stock.picking type
                shipper_address = picking_obj.move_lines[0].location_id.partner_id
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
                cust_address = picking_obj.partner_id
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
                shipping_res_obj = self.pool.get('shipping.response.processing')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('shipment_id','=',ids[0])])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = shipping_wizard.dropoff_type_fedex
                    service_type_fedex = shipping_wizard.service_type_fedex
                    packaging_type_fedex = shipping_wizard.packaging_type_fedex
                    package_detail_fedex = shipping_wizard.package_detail_fedex
                    payment_type_fedex = shipping_wizard.payment_type_fedex
                    physical_packaging_fedex = shipping_wizard.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    fed_length = shipping_wizard.pack_length
                    fed_width = shipping_wizard.pack_width
                    fed_height = shipping_wizard.pack_height
                    error_required = True
                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,error_required,fed_length,fed_width,fed_height,context)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            context.update({'picking_id':active_id})
            return {
                'name':_("Generate Shipping Quotes"),
                'view_mode': 'form',
                'res_id': ids[0],
                'view_type': 'form',
                'res_model': 'shipping.order.processing',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,}

#new function added
    def calc_total_wt(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        package_groups = self.pool.get('similar.packages')
        stockpicking = self.browse(cr, uid, ids, context=context)[0]
        group_brw = stockpicking.similar_packages
        total = 0
        for each in group_brw :
            number=each.number_of_similar_packages
            wt = each.package_dim.weight
            total = total + (number*wt)
        result[stockpicking.id] = total
        return result
#new function added
    def calc_total_pack(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        package_groups = self.pool.get('similar.packages')
        stockpicking = self.browse(cr, uid, ids, context=context)[0]
        group_brw = stockpicking.similar_packages
        total = 0
        for each in group_brw :
            total += each.number_of_similar_packages
        result[stockpicking.id] = total
        return result
    #new function added
    def onchange_use_mps(self, cr, uid, ids, use_mps,context=None):
        if use_mps:
            return {'value':{'package_detail_fedex':'PACKAGE_GROUPS'}}
        else:
            return {'value':{'package_detail_fedex':'INDIVIDUAL_PACKAGES'}}

    def _get_usd(self, cr, uid, context=None):
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False
    def get_shiping_location(self, cr, uid, context=None):
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
        active_model=context.get('active_model',False)
        active_id=context.get('active_id',False)
        picking_obj=self.pool.get(active_model).browse(cr,uid,active_id)
        shipper_address = picking_obj.move_lines[0].location_id.partner_id.id

        return shipper_address

    _columns = {
#        'package_status': fields.char('Status',size = 64),
#        'printer_id' : fields.many2one('server.printer','Printer'),
#        'print_label' : fields.boolean('Print Label'),
#        'no_of_prints' : fields.integer('Label Quantity',size = 32, help = 'Number of prints per label '),
#        'label_print' : fields.one2many('label.data.print','picking_id','Labels'),
        'use_mps' : fields.boolean('Multiple Package Shipment'),
        'child_tracking_ids':fields.text('Child Tracking Ids'),
        'total_packages': fields.function(calc_total_pack,string='Total Packages',type = 'float',store= True),
        'total_weight': fields.function(calc_total_wt,string='Total Weight',type = 'float',store= True),
        'package_dim':fields.many2one('package.dimension','Package Dimension'),
        'similar_packages' : fields.one2many('similar.packages','picking_id','Group Packages'),
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
        'response_usps_ids' : fields.one2many('shipping.response.processing','shipment_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
#        'checkbox': fields.boolean('Canada Post'),
#        'services': fields.many2one('service.name', 'Services'),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'customsvalue':fields.float('Custom Values'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'sales_return_id':fields.many2one('return.order'),
        'warehouse_location_id':fields.many2one('res.partner','Location Address'),
        'picking_id':fields.many2one('stock.picking','Picking'),
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
        'warehouse_location_id':get_shiping_location,
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
#                    'pack_length' : width,
#                    'pack_width' : width,
#                    'pack_height' : width,
                    'carrier_id':carrier_ids and carrier_ids[0] or ''
                    }
            return {'value':vals}
        return {'value':{}}
shipping_order_processing()
