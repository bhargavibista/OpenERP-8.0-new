# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import urllib2
import urllib
from base64 import b64decode
import binascii
import socket

import shippingservice
from miscellaneous import Address

from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.services.track_service import FedexTrackRequest
from fedex.config import FedexConfig
import suds
from suds.client import Client

from openerp.tools.translate import _
from openerp import netsvc
#logger = netsvc.Logger()
import Image
import connection_osv as connection
import urlparse

import logging
_logger = logging.getLogger(__name__)

#class server_printer(osv.osv):
#   '''
#   This class store printer name and there server address with port number used in label printing in MO
#   '''
#   _name='server.printer'
#   _columns={
#           'name':fields.char('Printer Name',size=64),
#           'ip':fields.char('IP Address',size=64),
#           'port':fields.integer('Port No')
#           }
#
#server_printer()

#class label_data_print(osv.osv):
#    _name = 'label.data.print'
#    def label_name(self, cr, uid, context=None):
#        sequence_id = context.get('sequence_id')
#        name = 'Label'+str(sequence_id)
#        return name
#    _columns = {
#        'name' : fields.char('Label',size=64),
#        'print_data': fields.text('Label Data'),
#        'picking_id': fields.many2one('stock.picking.out','Pickings'),
#        'print_quantity': fields.integer('Number of Prints',size=64),
#    }
#    _defaults = {
#        'name': label_name,
#        'print_quantity':1,
#    }
#    def print_label(self,cr,uid,ids,context={}):
#        label_data = self.browse(cr,uid,ids[0])
#        stockpicking = label_data.picking_id
#        print_quantity = label_data.print_quantity
##        server_printer=stockpicking.printer_id
##        printername = server_printer.ip
##        RAW_PORT = server_printer.port
#        printoutput = label_data.print_data
#
#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        try:
#            s.connect((printername, RAW_PORT))
#        except:
#            raise osv.except_osv(_('Warning!'), _('Printer not connected.Please check address and port of printer !'))
##                        Printing Multiple Number of labels
#        for quantity in range(0,print_quantity):
#            s.send(printoutput)
#	s.close()
#        return True
#label_data_print()
#


def get_partner_details(firm_name, partneradd_lnk, context=None):
        result = {}
        if partneradd_lnk:
            result['name'] = partneradd_lnk.name
            result['firm'] = firm_name or partneradd_lnk.name
            result['add1'] = partneradd_lnk.street or ''
            result['add2'] = partneradd_lnk.street2 or ''
            result['city'] = partneradd_lnk.city or ''
            result['state_code'] = partneradd_lnk.state_id.code or ''
            result['zip5'] = ''
            result['zip4'] = ''
            if len(partneradd_lnk.zip.strip()) == 5:
                result['zip5'] = partneradd_lnk.zip
                result['zip4'] = ''
            elif len(partneradd_lnk.zip.strip()) == 4:
                result['zip4'] = partneradd_lnk.zip
                result['zip5'] = ''
            elif str(partneradd_lnk.zip).find('-'):
                zips = str(partneradd_lnk.zip).split('-')
                if len(zips[0]) == 5 and len(zips[1]) == 4:
                    result['zip5'] = zips[0]
                    result['zip4'] = zips[1]
                elif len(zips[0]) == 4 and len(zips[1]) == 5:
                    result['zip4'] = zips[0]
                    result['zip5'] = zips[1]
            else:
                result['zip4'] = result['zip5'] = ''

            result['email'] = partneradd_lnk.email or ''
            result['country_code'] = partneradd_lnk.country_id.code or ''
            result['phone'] = partneradd_lnk.phone or ''
        return result
class shipping_response(osv.osv):
    _name = 'shipping.response'

    def generate_tracking_no(self, cr, uid, ids, context={}, error=True):
        import os; _logger.info("server name: %s", os.uname()[1])
#        try:
        fedexTrackingNumber = []
        saleorder_obj = self.pool.get('sale.order')
        stockmove_obj = self.pool.get('stock.move')
        stockpicking_obj = self.pool.get('stock.picking')
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        type = shippingresp_lnk.picking_id.type
        pick_id = shippingresp_lnk.picking_id.id
        stockpicking = stockpicking_obj.browse(cr,uid,pick_id)
        use_mps = stockpicking.use_mps

        ### Shipper
        ### based on stock.pickings type
        tracking_ref=stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id).carrier_tracking_ref
        stockpicking_ob_browse = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id)
        dimension = stockpicking_ob_browse.package_dim
#            if not tracking_ref:
        if type == 'out':
             cust_address = shippingresp_lnk.picking_id.company_id
#            cust_address = shippingresp_lnk.picking_id.sale_id.shop_id.cust_address
#                print "cust_address",cust_address
        elif type == 'in':
            cust_address = shippingresp_lnk.picking_id.address_id
        if not cust_address:
            if error:
                raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
            else:
                return False

        if not (cust_address.name ):
            raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
        if not cust_address.city:
            raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
        if not cust_address.zip:
            raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
        if not cust_address.country_id.code:
            raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
        if not cust_address.email:
            raise osv.except_osv(_('Warning !'),_("You must enter Shipper email."))

        shipper = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
#            print "this is a tuple %s"%str((shipper,))

        ### Recipient
        if type == 'out':
            cust_address = shippingresp_lnk.picking_id.partner_id
        elif type == 'in':
            cust_address = shippingresp_lnk.picking_id.sale_id.shop_id.cust_address
        if not cust_address:
            if error:
                raise osv.except_osv(_('Error'), _('Shipper Address not defined!'),)
            else:
                return False

        if not (cust_address.name):
            raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
        if not cust_address.zip:
            raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
        if not cust_address.country_id.code:
            raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
        receipient = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)
        weight = shippingresp_lnk.weight
        rate = shippingresp_lnk.rate

        if shippingresp_lnk.type.lower() == 'usps' and not ('usps_active' in context.keys()):
            usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
            usps = shippingservice.USPSDeliveryConfirmationRequest(usps_info, shippingresp_lnk.name,weight,shipper,receipient)
            usps_response = usps.send()
#                ups_response.image_format='gif'
            context['attach_id'] = stockpicking_obj.create_attachment(cr,uid,[shippingresp_lnk.picking_id.id],usps_response,context)
            stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':usps_response.tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(usps_response.graphic_image))), 'shipping_rate': rate, 'label_recvd': True})
            self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':usps_response.tracking_number})

            context['track_success'] = True
            context['tracking_no'] = usps_response.tracking_number

        elif shippingresp_lnk.type.lower() == 'fedex':
            #raise osv.except_osv(_('Error'), _('FedEx shipment request under construction'))

            shippingfedex_obj = self.pool.get('shipping.fedex')
            shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
            if not shippingfedex_id:
                raise osv.except_osv(_('Error'), _('Default Fedex settings not defined'))
            else:
                shippingfedex_id = shippingfedex_id[0]

            shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
            account_no = shippingfedex_ptr.account_no
            key = shippingfedex_ptr.key
            password = shippingfedex_ptr.password
            meter_no = shippingfedex_ptr.meter_no
            is_test = shippingfedex_ptr.test
            CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)

            rate_check=[]
            master_tracking = False
            type = False
            count_package = 0
            print "count pacjakeeeeeeee....outside.......",count_package
            if not use_mps:
                stockpicking.similar_packages=[0]
#            print_label = stockpicking.print_label
#            if print_label:
#                server_printer=stockpicking.printer_id
#                printername = server_printer.ip
#                RAW_PORT = server_printer.port
#                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                try:
#                    s.connect((printername, RAW_PORT))
#                except:
#                    raise osv.except_osv(_('Warning!'),_('Printer not connected.Please check address and port of printer !'))
            for line in stockpicking.similar_packages:
                if use_mps:
                    packages = line.number_of_similar_packages+1
                else:
                    packages = 2
                for i in range(1,packages):
                    count_package += 1
                    print "count pacjakeeeeeeee....inssside.......",count_package
            # This is the object that will be handling our tracking request.
            # We're using the FedexConfig object from example_config.py in this dir.
                    shipment = FedexProcessShipmentRequest(CONFIG_OBJ)

            # This is very generalized, top-level information.
            # REGULAR_PICKUP, REQattachUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
                    fedex_servicedetails = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id)

                    shipment.RequestedShipment.DropoffType = fedex_servicedetails.dropoff_type_fedex #'REGULAR_PICKUP'
                    # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
                    # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
                    shipment.RequestedShipment.ServiceType = fedex_servicedetails.service_type_fedex #'PRIORITY_OVERNIGHT'
                    # What kind of package this will be shipped in.
                    # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
                    shipment.RequestedShipment.PackagingType = fedex_servicedetails.packaging_type_fedex  #'FEDEX_PAK'

                    # No idea what this is.
                    # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
                    shipment.RequestedShipment.PackageDetail = fedex_servicedetails.package_detail_fedex #'INDIVIDUAL_PACKAGES'
                    # Shipper contact info.
                    shipment.RequestedShipment.Shipper.Contact.PersonName = shipper.name #'Sender Name'
 #                   shipment.RequestedShipment.Shipper.Contact.CompanyName = shipper.company_name #'Some Company'
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
#                    shipment.RequestedShipment.Recipient.Contact.CompanyName = receipient.company_name #'Recipient Company'
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






#                    commodities_obj=shipment.create_wsdl_object_of_type('Commodity')
#                    print "commodities_obj",commodities_obj
#                    commodities_obj.NumberOfPieces='1'
#                    commodities_obj.Description='dgdf'
#                    commodities_obj.NumberOfPieces='1'
#                    commodities_obj.CountryOfManufacture='US'
#                    commodities_obj.Weight.Units=fedex_servicedetails.weight_unit
#                    commodities_obj.Weight.Value=fedex_servicedetails.weight_package
#                    commodities_obj.Quantity='1'
#                    commodities_obj.QuantityUnits='EA'
#                    commodities_obj.UnitPrice.Currency=fedex_servicedetails.currency_id.name
#                    commodities_obj.UnitPrice.Amount ='100'
#                    commodities_obj.CustomsValue.Currency=fedex_servicedetails.currency_id.name
#                    commodities_obj.CustomsValue.Amount=fedex_servicedetails.customsvalue
#                    shipment.RequestedShipment.CustomsClearanceDetail.Commodities=commodities_obj
                    if fedex_servicedetails.service_type_fedex in ['FEDEX_FREIGHT','FEDEX_NATIONAL_FREIGHT']:
                        shipment.RequestedShipment.FreightShipmentDetail.FedExFreightAccountNumber='510087020'
                        shipment.RequestedShipment.FreightShipmentDetail.FedExFreightBillingContactAndAddress.Contact.PersonName='Mohsin'
                        shipment.RequestedShipment.FreightShipmentDetail.FedExFreightBillingContactAndAddress.Contact.CompanyName='510087020'
                        shipment.RequestedShipment.FreightShipmentDetail.FedExFreightBillingContactAndAddress.Contact.PhoneNumber='510087020'

        #                _logger.info("Freight Shipment Detail: %s", shipment.RequestedShipment.FreightShipmentDetail)
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
                #As Package count is updated by +1 for every request its made 0 for each time
                    shipment.RequestedShipment.PackageCount = 0
                    if use_mps:
                        weight = line.package_dim.weight
                    else:
                        weight = dimension.weight

                    package1_weight = shipment.create_wsdl_object_of_type('Weight')
                    # Weight, in pounds.
                    package1_weight.Value = fedex_servicedetails.weight_package or fedex_servicedetails.weight#1.0
                    package1_weight.Units = "LB"
                    if use_mps:
                        pack_dim = line.package_dim
                        fed_length = pack_dim.length
                        fed_width = pack_dim.width
                        fed_height = pack_dim.height
                    else:
                        fed_length = dimension.length
                        fed_width = dimension.width
                        fed_height = dimension.height

                    package1_dimensions = shipment.create_wsdl_object_of_type('Dimensions')
        #                print"package1_dimensions",package1_dimensions
                    package1_dimensions.Length = int(fedex_servicedetails.pack_length)
                    package1_dimensions.Width = int(fedex_servicedetails.pack_width)
                    package1_dimensions.Height = int(fedex_servicedetails.pack_height)
                    package1_dimensions.Units = "IN"

                    package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                    package1.Weight = package1_weight
                    package1.Dimensions=package1_dimensions
                    package1.PhysicalPackaging = fedex_servicedetails.physical_packaging_fedex

                    _logger.info("Package Dimensions: %s", package1_dimensions)
                    # Un-comment this to see the other variables you may set on a package.

                    # This adds the RequestedPackageLineItem WSDL object to the shipment. It
                    # increments the package count and total weight of the shipment for you.
                    shipment.add_package(package1)
                    if use_mps:
                        print "countttttttttttttttttttttttttt111111111111",count_package
                        if count_package==1:
                            print "count22222222222222...........",count_package
                            shipment.RequestedShipment.TotalWeight.Value = stockpicking.total_weight
                            shipment.RequestedShipment.PackageCount = int(stockpicking.total_packages)
                            shipment.RequestedShipment.RequestedPackageLineItems[0].SequenceNumber=count_package
                        else:
                            shipment.RequestedShipment.RequestedPackageLineItems[0].SequenceNumber=count_package
                            shipment.RequestedShipment.MasterTrackingId.TrackingIdType = type
                            if master_tracking:
                                shipment.RequestedShipment.MasterTrackingId.TrackingNumber= int(master_tracking)

                    _logger.info("Requested Shipment: %s", shipment.RequestedShipment)

                    # If you'd like to see some documentation on the ship service WSDL, un-comment
                    # this line. (Spammy).
                    #print shipment.client

                    # Un-comment this to see your complete, ready-to-send request as it stands
                    # before it is actually sent. This is useful for seeing what values you can
                    # change.
                    #print shipment.RequestedShipment

                    # If you want to make sure that all of your entered details are valid, you
                    # can call this and parse it just like you would via send_request(). If
                    # shipment.response.HighestSeverity == "SUCCESS", your shipment is valid.
                    #shipment.send_validation_request()

                    # Fires off the request, sets the 'response' attribute on the object.
                    try:
                        shipment.send_request()
                    except Exception, e:
                        if error:
                            raise osv.except_osv(_('Error'), _('%s' % (e,)))

            # This will show the reply to your shipment being sent. You can access the
            # attributes through the response attribute on the request object. This is
            # good to un-comment to see the variables returned by the Fedex reply.
            #print shipment.response

            # Here is the overall end result of the query.
                    _logger.info("Highest Severity: %s", shipment.response.HighestSeverity)
                    if use_mps:
                        type = shipment.response.CompletedShipmentDetail.MasterTrackingId.TrackingIdType
                        master_tracking = shipment.response.CompletedShipmentDetail.MasterTrackingId.TrackingNumber
                    fedexTrackingNumber.append(shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber)

                    # Getting the tracking number from the new shipment.
        #                    fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                    _logger.info("Fedex Tracking No.: %s", fedexTrackingNumber)
                    # Net shipping costs.
                    if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
                    else:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
                    _logger.info("Net Shipping Cost (US$): %s", fedexshippingrate)

                    # Get the label image in ASCII format from the reply. Note the list indices
                    # we're using. You'll need to adjust or iterate through these if your shipment
                    # has multiple packages.
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
                    _logger.info("ASCII label data: %s", ascii_label_data)
                    # Convert the ASCII data to binary.

                    """
                    #This is an example of how to dump a label to a PNG file.
                    """
                    # This will be the file we write the label out to.

                    fedex_attachment_pool = self.pool.get('ir.attachment')
                    fedex_data_attach = {
                        'name': 'PackingList.png',
                        'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                        'description': 'Packing List',
                        'res_name': shippingresp_lnk.picking_id.name,
                        'res_model': 'stock.picking',
                        'res_id': shippingresp_lnk.picking_id.id,
        #                        'res_id': shippingresp_lnk.picking_id.id,
                    }
                    fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                    context['attach_id'] = fedex_attach_id

#                    fedex_attach_id = fedex_attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.picking_id.id),('res_name','=',shippingresp_lnk.picking_id.name)])
#                    if not fedex_attach_id:
#                        fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
#                        print"attachment_id",fedex_attach_id
#                    else:
#                        fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
#                        fedex_attach_id = fedex_attach_id[0]

#                    context['attach_id'] = fedex_attach_id
                    context['tracking_no'] = fedexTrackingNumber
                    if use_mps:
                        context['tracking_no'] = fedexTrackingNumber
                    else:
                        context['tracking_no'] = fedexTrackingNumber[0]
                    """
                    #This is an example of how to print the label to a serial printer. This will not
                    #work for all label printers, consult your printer's documentation for more
                    #details on what formats it can accept.
                    """

                    """
                    #This is a potential cross-platform solution using pySerial. This has not been
                    #tested in a long time and may or may not work. For Windows, Mac, and other
                    #platforms, you may want to go this route.
                    """
                    label_string ='"""'+str(b64decode(ascii_label_data))+'"""'

        #                    label_dataprint = self.pool.get('label.data.print')
        #                    label_data_attach = {
        #                        'print_data': label_string,
        #                        'picking_id' : pick_id,
        #                    }
        #                    context = {'sequence_id': count}
        #                    label_data_id = label_dataprint.create(cr, uid,label_data_attach,context=context)
        #                    if print_label:
        #                        if not s :
        #                            server_printer=stockpicking.printer_id
        #                            printername = server_printer.ip
        #                            RAW_PORT = server_printer.port
        #                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #                            try:
        #                                s.connect((printername, RAW_PORT))
        #                            except:
        #                                raise osv.except_osv(_('Warning!'),_('Printer not connected.Please check address and port of printer !'))
        #                        print_quantity = stockpicking.no_of_prints
        #                        printoutput = label_string
        #        #                        Printing Multiple Number of labels
        #                        for quantity in range(0,print_quantity):
        #                            if not s :
        #                                server_printer=stockpicking.printer_id
        #                                printername = server_printer.ip
        #                                RAW_PORT = server_printer.port
        #                                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #                                try:
        #                                    s.connect((printername, RAW_PORT))
        #                                except:
        #                                    raise osv.except_osv(_('Warning!'),_('Printer not connected.Please check address and port of printer !'))
        #                            s.send(printoutput)
        #                        if print_label:
        #                            s.close()
        #                    else:
        #                        raise osv.except_osv(_('Warning!'),_('Quotes have already been accepted'))
                    if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                        if shipment.response.CompletedShipmentDetail.ShipmentRating:
                            fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount

                    else:
                        fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount


#        except Exception,exc:
#            raise osv.except_osv(_('Error!'),_('%s' % (exc,)))

            if fedexTrackingNumber:
                stockpickingwrite_result = stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':fedexTrackingNumber[0], 'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))), 'shipping_rate': fedexshippingrate, 'label_recvd': True,'child_tracking_ids':fedexTrackingNumber,})
                if shippingresp_lnk.picking_id and shippingresp_lnk.picking_id.sale_id:
                    self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':fedexTrackingNumber})
                context['track_success'] = True
        elif shippingresp_lnk.type.lower() == 'ups':
            ####################Number of pack wise weight#################
            number_of_packages = shippingresp_lnk.picking_id.number_of_packages

            move_lines = shippingresp_lnk.picking_id.move_lines
            pack_weight_merge={}
            pack_id=[]
            for each_move_lines in move_lines:
                tracking_id=each_move_lines.pack_track_id

                if each_move_lines.weight <= 0.0:
                    raise osv.except_osv(_('Error'), _('Please assign weight to each order lines'),)
                else:
                    if tracking_id:
                        val=pack_weight_merge.get(tracking_id.id,False)
                        if val:
                            val = float(each_move_lines.weight) + float(val)
                            pack_weight_merge[tracking_id.id]=val
                        else:
                            pack_weight_merge[tracking_id.id]=each_move_lines.weight
                            pack_id.append(tracking_id)
                    else:
                        raise osv.except_osv(_('Error'), _('Please assign packs to order lines'),)
            _logger.info("Pack weight merge: %s", pack_weight_merge)
            ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)

            ####################For Each UPS seperate dimension#################
            tracking_lines = shippingresp_lnk.picking_id.tracking_ids
            length_merge=[]
            width_merge=[]
            height_merge=[]
            if tracking_lines:
                for each_tracking_lines in tracking_lines:
                    length_ups = each_tracking_lines.length_ups
                    length_merge.append(length_ups)
                    width_ups = each_tracking_lines.width_ups
                    width_merge.append(width_ups)
                    height_ups = each_tracking_lines.height_ups
                    height_merge.append(height_ups)
            else:
                    tracking_id=each_move_lines.tracking_id
    #                raise osv.except_osv(_('Warning'), _('Please assign the pack (%s) length,width,height in Shipping Info Tab!') %(tracking_id.name))
                    raise osv.except_osv(_('Warning'), _('Please assign the pack length,width,height in Shipping Info Tab!'),)

            stockpicking_obj = self.pool.get('stock.picking')
            pickup_type_ups = shippingresp_lnk.picking_id.pickup_type_ups
            service_type_ups = shippingresp_lnk.picking_id.service_type_ups
            packaging_type_ups = shippingresp_lnk.picking_id.packaging_type_ups
            ups = shippingservice.UPSShipmentConfirmRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient,length_merge,width_merge,height_merge,pack_weight_merge)
            ups_response = ups.send()
            ups = shippingservice.UPSShipmentAcceptRequest(ups_info, ups_response.shipment_digest)

            ups_response = ups.send()
            stockpicking_obj.create_attachment(cr,uid,[shippingresp_lnk.picking_id.id],ups_response,context)
            tracking_number=''
            all_tracking_number=''
            for i in range(0,ups_response.package_count):
                label_image = ups_response.graphic_image[i]
                tracking_number=ups_response.tracking_number[i]
                if i == 0:
                    all_tracking_number +=ups_response.tracking_number[i]
                else:
                    all_tracking_number +=',' + ups_response.tracking_number[i]
            stockpicking_obj.write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_tracking_ref':tracking_number,'shipping_label':binascii.b2a_base64(str(b64decode(label_image))), 'shipping_rate': rate, 'label_recvd': True})
            self.pool.get('sale.order').write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':all_tracking_number})

            context['track_success'] = True
            context['tracking_no'] = ups_response.tracking_number
#            else:
#                raise osv.except_osv(_('Warning !'),_("This shipping quotes has been already accepted"))

#        except Exception, exc:
#                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
#        ### Check Availability; Confirm; Validate : Automate Process Now step
        if context.get('track_success',False):
            ### Assign Carrier to Delivery carrier if user has not chosen
#            carrier_lnk = stockpicking_obj.browse(cr,uid,shippingresp_lnk.picking_id.id).carrier_id
#            if not carrier_lnk:
            type_fieldname = ''
            if shippingresp_lnk.type.lower() == 'usps':
                type_fieldname = 'is_usps'
            elif shippingresp_lnk.type.lower() == 'ups':
                type_fieldname = 'is_ups'
            elif shippingresp_lnk.type.lower() == 'fedex':
                type_fieldname = 'is_fedex'
            _logger.info("Shipping Name: %s", shippingresp_lnk.name)
            carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',shippingresp_lnk.name),(type_fieldname,'=',True)])

            if not carrier_ids:
                if error:
                    _logger.info("error: %s", error)
                    raise osv.except_osv(_('Error'), _('Shipping service output settings not defined'))
                return False
#            print "selected carrier ids: ",carrier_ids
            self.pool.get('stock.picking').write(cr,uid,shippingresp_lnk.picking_id.id,{'carrier_id':carrier_ids[0]})
            if shippingresp_lnk.picking_id and shippingresp_lnk.picking_id.sale_id:
                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{ 'carrier_id':carrier_ids[0]})


#            saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'tracking_no':context['tracking_no'], 'carrier_id':carrier_ids[0]})

            ### Write this shipping respnse is selected
            self.write(cr,uid,ids[0],{'selected':True})

            if context.get('batch_printing',False):
                return True

            return{
               'view_mode': 'form',
               'res_id': shippingresp_lnk.picking_id.id,
               'view_type': 'form',
               'res_model': 'stock.picking',
               'type': 'ir.actions.act_window',
               'nodestroy': True,
               'target': 'current',
               'domain': '[]',
               'context': context}
        else:
            return False
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
        'picking_id' : fields.many2one('stock.picking','Picking'),
        'sale_order_id':fields.many2one('sale.order','Order')
    }
    _defaults = {
        'sr_no': 9,
        'selected': False
    }
shipping_response()

def _get_shipping_type(self, cr, uid, context=None):
    return [
#        ('All','All'),
#        ('Canada Post','Canada Post'),
        ('Fedex','Fedex'),
#        ('UPS','UPS'),
#        ('USPS','USPS'),

    ]
def _get_service_type_usps(self, cr, uid, context=None):
    return [
        ('First Class', 'First Class'),
        ('First Class HFP Commercial', 'First Class HFP Commercial'),
        ('FirstClassMailInternational', 'First Class Mail International'),
        ('Priority', 'Priority'),
        ('Priority Commercial', 'Priority Commercial'),
        ('Priority HFP Commercial', 'Priority HFP Commercial'),
        ('PriorityMailInternational', 'Priority Mail International'),
        ('Express', 'Express'),
        ('Express Commercial', 'Express Commercial'),
        ('Express SH', 'Express SH'),
        ('Express SH Commercial', 'Express SH Commercial'),
        ('Express HFP', 'Express HFP'),
        ('Express HFP Commercial', 'Express HFP Commercial'),
        ('ExpressMailInternational', 'Express Mail International'),
        ('ParcelPost', 'Parcel Post'),
        ('ParcelSelect', 'Parcel Select'),
        ('StandardMail', 'Standard Mail'),
        ('CriticalMail', 'Critical Mail'),
        ('Media', 'Media'),
        ('Library', 'Library'),
        ('All', 'All'),
        ('Online', 'Online'),
    ]

def _get_first_class_mail_type_usps(self, cr, uid, context=None):
    return [
        ('Letter', 'Letter'),
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Postcard', 'Postcard'),
    ]

def _get_container_usps(self, cr, uid, context=None):
    return [
        ('Variable', 'Variable'),
        ('Card', 'Card'),
        ('Letter', 'Letter'),
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Large Parcel', 'Large Parcel'),
        ('Irregular Parcel', 'Irregular Parcel'),
        ('Oversized Parcel', 'Oversized Parcel'),
        ('Flat Rate Envelope', 'Flat Rate Envelope'),
        ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
        ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
        ('SM Flat Rate Envelope', 'SM Flat Rate Envelope'),
        ('Window Flat Rate Envelope', 'Window Flat Rate Envelope'),
        ('Gift Card Flat Rate Envelope', 'Gift Card Flat Rate Envelope'),
        ('Cardboard Flat Rate Envelope', 'Cardboard Flat Rate Envelope'),
        ('Flat Rate Box', 'Flat Rate Box'),
        ('SM Flat Rate Box', 'SM Flat Rate Box'),
        ('MD Flat Rate Box', 'MD Flat Rate Box'),
        ('LG Flat Rate Box', 'LG Flat Rate Box'),
        ('RegionalRateBoxA', 'RegionalRateBoxA'),
        ('RegionalRateBoxB', 'RegionalRateBoxB'),
        ('Rectangular', 'Rectangular'),
        ('Non-Rectangular', 'Non-Rectangular'),
     ]

def _get_size_usps(self, cr, uid, context=None):
    return [
        ('REGULAR', 'Regular'),
        ('LARGE', 'Large'),
     ]

class stock_picking_out(osv.osv):
#    _name = "stock.picking"
    _inherit = "stock.picking"
    def onchange_use_mps(self, cr, uid, ids, use_mps,context=None):
        if use_mps:
            return {'value':{'package_detail_fedex':'PACKAGE_GROUPS'}}
        else:
            return {'value':{'package_detail_fedex':'INDIVIDUAL_PACKAGES'}}
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
   

    def get_rates(self,cr,uid,ids,context={}):
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        total = ''
        gst =0.00
        hst =0.00
        pst =0.00
#        obj = self.pool.get('stock.picking')
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            name =  shipping_obj.browse(cr,uid,search_id[0]).name
            passwd =  shipping_obj.browse(cr,uid,search_id[0]).passwd
            environment = shipping_obj.browse(cr,uid,search_id[0]).environment
            co_no = shipping_obj.browse(cr,uid,search_id[0]).customer_num
            cana_wt = self.browse(cr,uid,ids[0]).weight_package
            cana_ln = self.browse(cr,uid,ids[0]).cana_length
            cana_wdth = self.browse(cr,uid,ids[0]).cana_width
            cana_ht = self.browse(cr,uid,ids[0]).cana_height
            service_code = self.browse(cr,uid,ids[0]).services
            zip_code_customer = self.browse(cr, uid, ids[0]).address_id.zip
            zip_code_supplier = shipping_obj.browse(cr, uid, search_id[0]).address.zip
            serv_code = service_code.service_code
            xml_request = """<?xml version="1.0" encoding="utf-8"?>
    <mailing-scenario xmlns="http://www.canadapost.ca/ws/ship/rate">
    <customer-number>%s</customer-number>
    <parcel-characteristics>
    <weight>%s</weight>
    <dimensions>
    <length>%s</length>
    <width>%s</width>
    <height>%s</height>
    </dimensions>
    </parcel-characteristics>
    <origin-postal-code>%s</origin-postal-code>
    <destination><domestic>
    <postal-code>%s</postal-code>
    </domestic>
    </destination>
    <services>
    <service-code>%s</service-code>
    </services>
    </mailing-scenario>

            """%(co_no,cana_wt,cana_ln,cana_wdth,cana_ht,zip_code_supplier,zip_code_customer,serv_code)
            _logger.info("xml request: %s", xml_request)
            result = connection.call(cr, uid, 'GetRates', name, passwd, environment,xml_request)
            _logger.info("result: %s", result)
            for each in result:
                if each.get('base',False):
                    base = each.get('base',False)
                    _logger.info("base: %s", base)
                if each.get('gst',False):
                    gst = each.get('gst',False)
                    _logger.info("gst: %s", gst)
                if each.get('pst',False):
                    pst = each.get('pst',False)
                    _logger.info("pst: %s", pst)
                if each.get('hst',False):
                    hst = each.get('hst',False)
                    _logger.info("hst: %s", hst)
                base = float(base)
                gst = float(gst)
                pst = float(pst)
                hst = float(hst)
                total = gst+pst+hst
                t1 = str(total)
                b1 = str(base)
                g1 = str(gst)
                p1 = str(pst)
                h1 = str(hst)
                shipping_rate = "Base Price : "+b1+"\n"+"Taxes : "+t1+"\n\t"+"gst : "+g1+"\n\t"+"pst : "+p1+"\n\t"+"hst : "+h1+"\n\t"
                _logger.info("Total: %s", total)
                _logger.info("Shipping Rate: %s", shipping_rate)
        cr.execute("UPDATE stock_picking SET rates='%s' where id=%d"%(shipping_rate,ids[0],))
        return True


    def cana_generate_shipping(self,cr,uid,ids,context={}):
        shipping_obj = self.pool.get('shipping.method')
        shipping_record = shipping_obj.search(cr,uid,[])
        if not shipping_record:
            raise osv.except_osv(_("Warning"), _("Shipping settings are not done. Go to Warehouse/Configuration/Canada Post/Configuration"))
        rt = self.browse(cr, uid, ids[0]).rates
        if not rt:
            raise osv.except_osv(_("Warning"), _("First Get Rates on clicking 'Get Rates' button"))
        shipping_obj = self.pool.get('shipping.method')
        search_id = shipping_obj.search(cr,uid,[])
        if search_id:
            name =  shipping_obj.browse(cr,uid,search_id[0]).name
            passwd =  shipping_obj.browse(cr,uid,search_id[0]).passwd
            environment = shipping_obj.browse(cr,uid,search_id[0]).environment
        service_code = self.browse(cr,uid,ids[0]).services
        serv_code = service_code.service_code
        comp_sender = shipping_obj.browse(cr, uid, search_id[0]).address.partner_id
        phone_no = shipping_obj.browse(cr, uid, search_id[0]).address.phone
        street_name = shipping_obj.browse(cr, uid, search_id[0]).address.street
        city_name = shipping_obj.browse(cr, uid, search_id[0]).address.city
        supplier_zip = shipping_obj.browse(cr, uid, search_id[0]).address.zip
        comp_rec = self.browse(cr, uid, ids[0]).address_id.partner_id
        rec_name = self.browse(cr, uid, ids[0]).address_id.partner_id
        rec_street = self.browse(cr, uid, ids[0]).address_id.street
        rec_city = self.browse(cr, uid, ids[0]).address_id.city
        rec_zip = self.browse(cr, uid, ids[0]).address_id.zip
        cana_wt = self.browse(cr,uid,ids[0]).weight_package
        cana_ln = self.browse(cr,uid,ids[0]).cana_length
        cana_wdth = self.browse(cr,uid,ids[0]).cana_width
        cana_ht = self.browse(cr,uid,ids[0]).cana_height
        xml_request = """<?xml version="1.0" encoding="utf-8"?>
<non-contract-shipment xmlns="http://www.canadapost.ca/ws/ncshipment">
<delivery-spec>
<service-code>%s</service-code>
<sender>
<company>%s</company>
<contact-phone>%s</contact-phone>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</sender>
<destination>
<name>%s</name>
<company>%s</company>
<address-details>
<address-line-1>%s</address-line-1>
<city>%s</city>
<prov-state>%s</prov-state>
<country-code>%s</country-code>
<postal-zip-code>%s</postal-zip-code>
</address-details>
</destination>
<parcel-characteristics>
<weight>%s</weight>
<dimensions>
<length>%s</length>
<width>%s</width>
<height>%s</height>
</dimensions>
</parcel-characteristics>
<preferences>
<show-packing-instructions>%s</show-packing-instructions>
</preferences>
</delivery-spec>
</non-contract-shipment>"""%(serv_code,comp_sender,phone_no,street_name,city_name,'ON',supplier_zip,rec_name,rec_name,rec_street,rec_city,'ON', 'CA',rec_zip,cana_wt,cana_ln,cana_wdth,cana_ht,'true',)
        _logger.info("xml request %s", xml_request)
        result = connection.call(cr, uid, 'GetShipping', name, passwd, environment, xml_request)
        _logger.info("result %s", result)
        track_num=result.get('tracking_no',False)
        _logger.info("track_num: %s", track_num)
        carrier_services = self.browse(cr, uid, ids[0]).services.name
        id1 = self.pool.get('delivery.carrier').search(cr, uid, [('name','=', carrier_services)])
        stock_origin = self.browse(cr, uid, ids[0]).origin
        sale_id = self.pool.get('sale.order').search(cr, uid, [('name', '=', stock_origin)])
        shippingresp_lnk = self.browse(cr,uid,ids[0])
        if id1 and track_num:
            cr.execute("UPDATE stock_picking SET carrier_tracking_ref='%s',carrier_id=%d,label_recvd=True where id=%d"%(track_num,id1[0],ids[0],))
            if sale_id:
                cr.execute("UPDATE sale_order SET tracking_no=%s,carrier_id=%d where id = %s"%(track_num, id1[0],sale_id[0]))
#                cr.execute("UPDATE sale_order SET carrier_id=%d where id = %s"%(id1[0],sale_id[0]))
#                cr.execute("UPDATE stock_picking SET note=%s where id = %s"%(track_num,sale_id[0]))
#                self.pool.get('stock.picking').write(cr,uid,shippingresp_lnk.id,{'note':track_num})

        link=result.get('link',False)
        if link:
            urldat = urlparse.urlparse(link)
            if urldat:
                link = urldat[2]
            _logger.info("link: %s", link)
            result_pdf = connection.call(cr, uid, 'Getartifact', name, passwd, environment, link)
            _logger.info("result_pdf: %s", result_pdf)
            self.create_attachment_can(cr,uid,ids,result_pdf)
        return True

    def create_attachment_can(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        data_attach = {
            'name': 'PackingList1.pdf' ,
            'datas': binascii.b2a_base64(vals),
            'description': 'Packing1 List',
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'stock.picking',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)
        else:
            attach_id = attach_id[0]
            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
        return attach_id

    def action_assign_new(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            if not move_ids:
                return False
            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
        return True

    def get_ups_servicetype_name(self, cr, uid, ids, code, mag_code=False):
        if code:
            if code == '01':
                return 'Next Day Air'
            elif code == '02':
                return 'Second Day Air'
            elif code == '03':
                return 'Ground'
            elif code == '07':
                return 'Worldwide Express'
            elif code == '08':
                return 'Worldwide Expedited'
            elif code == '11':
                return 'Standard'
            elif code == '12':
                return 'Three-Day Select'
            elif code == '13':
                return 'Next Day Air Saver'
            elif code == '14':
                return 'Next Day Air Early AM'
            elif code == '54':
                return 'Worldwide Express Plus'
            elif code == '59':
                return 'Second Day Air AM'
            elif code == '65':
                return 'Saver'
            else:
                return False
        elif mag_code:
            if mag_code == 'ups_3DS':
                return 'Three-Day Select'
            elif mag_code == 'ups_GND':
                return 'Ground'
            elif mag_code == 'ups_2DA':
                return 'Second Day Air'
            elif mag_code == 'ups_1DP':
                return 'Next Day Air Saver'
            elif mag_code == 'ups_1DA':
                return 'Next Day Air'
            elif mag_code == 'ups_1DM':
                return 'Next Day Air Early AM'
        else:
            return False

    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None,fed_length=None,fed_width=None,fed_height=None):
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

        stockpicking_lnk = self.browse(cr,uid,ids[0])

        # This is very generalized, top-level information.
        # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
        rate_request.RequestedShipment.DropoffType = dropoff_type_fedex

        # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
        # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
        rate_request.RequestedShipment.ServiceType = service_type_fedex

        # What kind of package this will be shipped in.
        # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
        rate_request.RequestedShipment.PackagingType = packaging_type_fedex

        # No idea what this is.
        # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
        rate_request.RequestedShipment.PackageDetail = package_detail_fedex

        rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
        rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
        rate_request.RequestedShipment.Shipper.Address.Residential = False

        rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
        rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
        # This is needed to ensure an accurate rate quote with the response.
        #rate_request.RequestedShipment.Recipient.Address.Residential = True
        #include estimated duties and taxes in rate quote, can be ALL or NONE
        rate_request.RequestedShipment.EdtRequestType = 'NONE'

        # Who pays for the rate_request?
        # RECIPIENT, SENDER or THIRD_PARTY
        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
#        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
#        rate_request.RequestedShipment.PackageCount = 1
        package1_weight = rate_request.create_wsdl_object_of_type('Weight')
        _logger.info("Package weight: %s", package1_weight)
        package1_weight.Value = weight
        package1_weight.Units = "LB"

        package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
        package1_dimensions.Length=int(fed_length)
        package1_dimensions.Width=int(fed_width)
        package1_dimensions.Height=int(fed_height)
        package1_dimensions.Units="IN"
        _logger.info("Package dimensions: %s", package1_dimensions)



#        package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
#        package1.Weight = package1_weight
#        package1.Dimensions = package1_dimensions
#
#        #can be other values this is probably the most common
#        package1.PhysicalPackaging = physical_packaging_fedex
#        # Un-comment this to see the other variables you may set on a package.
#        #print package1
#
#        # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
#        # increments the package count and total weight of the rate_request for you.
#        rate_request.add_package(package1)

        # If you'd like to see some documentation on the ship service WSDL, un-comment
        # this line. (Spammy).
        #print rate_request.client

        # Un-comment this to see your complete, ready-to-send request as it stands
        # before it is actually sent. This is useful for seeing what values you can
        # change.
        #print rate_request.RequestedShipment

        # Fires off the request, sets the 'response' attribute on the object.
#        saturday_delivery = stockpicking_lnk.saturday_delivery
#        if saturday_delivery:
#            date = stockpicking_lnk.saturday_date
#            format_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
#            rate_request.RequestedShipment.ShipTimestamp = format_date
#            rate_request.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes='SATURDAY_DELIVERY'

############## Rate Request for MULTIPLE PACKAGE SHIPMENT###############################
        total_packages = stockpicking_lnk.total_packages
        rate_request.RequestedShipment.PackageCount = int(total_packages)
        similar_packages = stockpicking_lnk.similar_packages
        use_mps = stockpicking_lnk.use_mps
        package_detail = stockpicking_lnk.package_detail_fedex
        if use_mps:
            rate_request.RequestedShipment.TotalWeight.Value = weight
        if use_mps and package_detail=="PACKAGE_GROUPS":
            
            line_count = 0
            group_count = 0
            print "line........346546.............",similar_packages
            for line in similar_packages:
                print "line.....................",line,similar_packages
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
                print "line.number_of_similar_packagesline.number_of_similar_packages222221111111112",line.number_of_similar_packages

                rate_request.RequestedShipment.RequestedPackageLineItems[line_count].GroupPackageCount = line.number_of_similar_packages
                print "line.number_of_similar_packagesline.number_of_similar_packages222222",line.number_of_similar_packages
                line_count += 1
                rate_request.RequestedShipment.PackageCount -= 1
        else:
            package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
            package1_weight = rate_request.create_wsdl_object_of_type('Weight')
            package_dim = stockpicking_lnk.package_dim
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
            package1.Weight = package1_weight
            package1.Dimensions = package1_dimensions
            package1.PhysicalPackaging = physical_packaging_fedex
            rate_request.add_package(package1)
        print "rate_request",rate_request.RequestedShipment
        try:
            rate_request.send_request()

        except Exception, e:
            if error:
                raise Exception('%s' % (e))
            return False

        # This will show the reply to your rate_request being sent. You can access the
        # attributes through the response attribute on the request object. This is
        # good to un-comment to see the variables returned by the FedEx reply.
        #print 'response: ', rate_request.response

        # Here is the overall end result of the query.
        #print "HighestSeverity:", rate_request.response.HighestSeverity

        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            for surcharge in detail.ShipmentRateDetail.Surcharges:
                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
                    _logger.info("ODA rate_request charge: %s", surcharge.Amount.Amount)

        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
            _logger.info("Net FedEx Charge: %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)

        sr_no = 9
        sys_default_value = False
        cust_default_value = False
        if sys_default:
            sys_default_vals = sys_default.split('/')
            #print "sys_default_vals: ",sys_default_vals
            if sys_default_vals[0] == 'FedEx':
                sys_default_value = True
                sr_no = 2

        if cust_default:
            cust_default_vals = cust_default.split('/')
            #print "sys_default_vals: ",sys_default_vals
            if cust_default_vals[0] == 'FedEx':
                cust_default_value = True
                sr_no = 1

        fedex_res_vals = {
            'name' : service_type_fedex,
            'type' : 'FedEx',
            'rate' : rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount,
            'picking_id' : ids[0], #Change the ids[0] when switch to create
            'weight' : weight,
            'sys_default' : sys_default_value,
            'cust_default' : cust_default_value,
            'sr_no' : sr_no
        }
        print "fedex_res_valsfedex_res_valsfedex_res_vals",fedex_res_vals
        fedex_res_id = self.pool.get('shipping.response').create(cr,uid,fedex_res_vals)
        #print "fedex_res_id: ",fedex_res_id
        if fedex_res_id:
            return True
        else:
            return False
    def generate_rate(self, cr, uid, ids, values, context={}):
        stockpicking = self.browse(cr,uid,ids[0])
        similar_packages_browse = stockpicking.similar_packages
        use_mps = stockpicking.use_mps
        package_detail = stockpicking.package_detail_fedex
        if use_mps:
            if not (use_mps and package_detail == "PACKAGE_GROUPS") :
                raise osv.except_osv(_('Warning !'),_("Please Select Package Detail as PACKAGE_GROUPS"))
        if not use_mps:
            if not (not use_mps and package_detail == "INDIVIDUAL_PACKAGES"):
                raise osv.except_osv(_('Warning !'),_("Please Select Package Detail as INDIVIDUAL_PACKAGES"))

        total_amount = 0
        count_package = 0
        context.update({'count_package':count_package})
        rate = self.generate_shipping( cr, uid, ids,context=context)
        service_type_fedex= rate['service_type_fedex']
        fedex_res_vals = {
            'name' : service_type_fedex,
            'type' : 'FedEx',
            'rate' : rate['rate'],
            'picking_id' : ids[0], #Change the ids[0] when switch to create
        }
        fedex_res_id = self.pool.get('shipping.response').create(cr,uid,fedex_res_vals)
        if fedex_res_id:
            return True
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
            logger.notifyChannel('init', netsvc.LOG_WARNING, 'res_id is %s'%(res_id,))
        if res_id:
            return True
        else:
            return False

#    def create_attachment(self, cr, uid, ids, vals, context={}):
#        attachment_pool = self.pool.get('ir.attachment')
#        data_attach = {
#            'name': 'PackingList.' + vals.image_format.lower() ,
#            'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image))),
#            'description': 'Packing List',
#            'res_name': self.browse(cr,uid,ids[0]).name,
#            'res_model': 'stock.picking',
#            'res_id': ids[0],
#        }
#        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
#        if not attach_id:
#            attach_id = attachment_pool.create(cr, uid, data_attach)
#            print "attach_id: ",attach_id
#        else:
#            attach_id = attach_id[0]
#            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
#            print "attach_result: ",attach_result
#        return attach_id

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
#        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
#        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)

#        else:
#            attach_id = attach_id[0]
#            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
#            print "attach_result: ",attach_result
#        print"pdf_attach5555555555555555555",pdf_attach224


        return attach_id


    ## This function is called when the button is clicked
    def generate_shipping(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        print "contextcontextcontext",context
#        count_package =context['count_package']
        for id in ids:
#            try:
            dimension = self.browse(cr,uid,id).package_dim
            stockpicking = self.browse(cr,uid,id)
            use_mps = stockpicking.use_mps
            print "stockpickingstockpickingstockpicking",stockpicking.state
            count_package= 0
            
            if stockpicking.state != 'done':
                raise osv.except_osv(_('Warning !'),_('You Generate Shipping Quotes only if Order is in Done State.'))
            shipping_type = stockpicking.shipping_type
            type = stockpicking.type
            weight = stockpicking.weight_package if stockpicking.weight_package else stockpicking.weight
#                weight_unit=stockpicking.weight_unit if stockpicking.weight_unit else 'LB'
            if use_mps:
                similar_package_brw = stockpicking.similar_packages[count_package]
                weight = stockpicking.total_weight
            else:
                weight = dimension.weight
            weight_unit='LB'
            if weight<=0.0:
                raise Exception('Package Weight Invalid!')


            ###based on stock.picking type
            if type == 'out':
                #shipper_address = stockpicking.sale_id and stockpicking.sale_id.shop_id.cust_address or False
                shipper_address = stockpicking.company_id
            elif type == 'in':
                shipper_address = stockpicking.address_id
            if not shipper_address:
                if 'error' not in context.keys() or context.get('error',False):
                    raise Exception('Shop Address not defined!')
                else:
                    return False
            if not (shipper_address.name or shipper_address.partner_id.name):
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
            shipper = Address(shipper_address.name or shipper_address.partner_id.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.partner_id.name)

            ### Recipient
            ###based on stock.picking type
            if type == 'out':
                cust_address = stockpicking.partner_id
            elif type == 'in':
                cust_address = stockpicking.sale_id and stockpicking.sale_id.shop_id.cust_address or False
            if not cust_address:
                if 'error' not in context.keys() or context.get('error',False):
                    raise Exception('Reciepient Address not defined!')
                else:
                    return False
            if not (cust_address.name or cust_address.name):
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
#                if not cust_address.street:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Street."))
            if not cust_address.city:
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
#                if not cust_address.state_id.code:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient State Code."))
            if not cust_address.zip:
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
            if not cust_address.country_id.code:
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
#                if not cust_address.email:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient email."))
            receipient = Address(cust_address.name , cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)

            # Deleting previous quotes
            shipping_res_obj = self.pool.get('shipping.response')
            shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
            if shipping_res_ids:
                shipping_res_obj.unlink(cr,uid,shipping_res_ids)

            saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',stockpicking.sale_id.id)])
            sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
            context['sys_default'] = sys_default
            cust_default= self._get_cust_default_shipping(cr,uid,stockpicking.carrier_id.id,context)
            context['cust_default'] = cust_default

            if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                service_type_usps = stockpicking.service_type_usps
                first_class_mail_type_usps = stockpicking.first_class_mail_type_usps or ''
                container_usps = stockpicking.container_usps or ''
                size_usps = stockpicking.size_usps
                width_usps = stockpicking.width_usps
                length_usps = stockpicking.length_usps
                height_usps = stockpicking.height_usps
                girth_usps = stockpicking.girth_usps
                usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default)
                usps_response = usps.send()
                context['type'] = 'USPS'
                self.create_quotes(cr,uid,ids,usps_response,context)

            if shipping_type == 'UPS' or shipping_type == 'All':
                ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                pickup_type_ups = stockpicking.pickup_type_ups
                service_type_ups = stockpicking.service_type_ups
                packaging_type_ups = stockpicking.packaging_type_ups
#                    print"shipper",shipper
                ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient, cust_default, sys_default)
                ups_response = ups.send()
                context['type'] = 'UPS'
                self.create_quotes(cr,uid,ids,ups_response,context)

            if shipping_type == 'Fedex' or shipping_type == 'All':
                dropoff_type_fedex = stockpicking.dropoff_type_fedex
                service_type_fedex = stockpicking.service_type_fedex
                packaging_type_fedex = stockpicking.packaging_type_fedex
                package_detail_fedex = stockpicking.package_detail_fedex
                payment_type_fedex = stockpicking.payment_type_fedex
                physical_packaging_fedex = stockpicking.physical_packaging_fedex
                shipper_postal_code = shipper.zip
                shipper_country_code = shipper.country_code
                customer_postal_code = receipient.zip
                customer_country_code = receipient.country_code
                fed_length = stockpicking.pack_length
                fed_width = stockpicking.pack_width
                fed_height = stockpicking.pack_height
                if use_mps:
                    pack_dim = similar_package_brw.package_dim
                    fed_length = pack_dim.length
                    fed_width = pack_dim.width
                    fed_height = pack_dim.height
                else:
                    fed_length = dimension.length
                    fed_width = dimension.width
                    fed_height = dimension.height
                error_required = True
                shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context,fed_length,fed_width,fed_height)
#            except Exception, exc:
#                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return True

    def _get_cust_default_shipping(self,cr,uid,carrier_id,context={}):
        if carrier_id:
            carrier_obj = self.pool.get('delivery.carrier')
            carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
            cust_default = ''
            if carrier_lnk.is_ups:
                cust_default = 'UPS'
                service_type_ups = carrier_lnk.service_code or '03'
                cust_default += '/' + service_type_ups
            elif carrier_lnk.is_fedex:
                cust_default = 'FedEx'
                service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                cust_default += '/' + service_type_fedex
            elif carrier_lnk.is_usps:
                cust_default = 'USPS'
                service_type_usps = carrier_lnk.service_code or 'All'
                cust_default += '/' + service_type_usps
        else:
            cust_default = False
        return cust_default

    def _get_sys_default_shipping(self,cr,uid,saleorderline_ids,weight,context={}):
        sys_default = False
        product_obj = self.pool.get('product.product')
        saleorderline_obj = self.pool.get('sale.order.line')
        product_shipping_obj = self.pool.get('product.product.shipping')
        product_categ_shipping_obj = self.pool.get('product.category.shipping')

        if len(saleorderline_ids) <= 2:
            product_id = False
            ### Making sure product is not Shipping and Handling
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue
                product_id = line.product_id.id

            if not product_id:
                return False

        else:
            ### Get the product id of the heaviest product
            weight = 0.0
            product_id = False
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue

                if line.product_id.product_tmpl_id.weight_net > weight:
                    product_id = line.product_id.id
                    weight = line.product_id.product_tmpl_id.weight_net

            if not product_id:
                return False

        product_shipping_ids = product_shipping_obj.search(cr,uid,[('product_id','=',product_id)])

        if not product_shipping_ids:
            categ_id = product_obj.browse(cr,uid,product_id).product_tmpl_id.categ_id.id
            product_categ_shipping_ids = product_categ_shipping_obj.search(cr,uid,[('product_categ_id','=',categ_id)])
            if not product_categ_shipping_ids:
                ### Assume the default
                if (weight*16) > 14.0:
                    sys_default = 'USPS/Priority/Parcel/REGULAR'
                else:
                    sys_default = 'USPS/First Class/Parcel/REGULAR'
                return sys_default

        if product_shipping_ids:
            cr.execute(
                'SELECT * '
                'FROM product_product_shipping '
                'WHERE weight <= %s ' +
                'and product_id=%s ' +
                'order by sequence desc limit 1',
                (weight,product_id))
        else:
            cr.execute(
                'SELECT * '
                'FROM product_category_shipping '
                'WHERE weight <= %s '+
                'and product_categ_id=%s '+
                'order by sequence desc limit 1',
                (weight,categ_id))
        res = cr.dictfetchall()
        ## res:  [{'create_uid': 1, 'create_date': '2011-06-28 01:43:49.017306', 'product_id': 187, 'weight': 3.0, 'sequence': 3, 'container_usps': u'Letter', 'service_type_usps': u'First Class', 'write_uid': None, 'first_class_mail_type_usps': u'Letter', 'size_usps': u'REGULAR', 'write_date': None, 'shipping_type': u'USPS', 'id': 14}]
        ### Format- USPS/First Class/Letter
        sys_default = res[0]['shipping_type'] + '/' + res[0]['service_type_usps'] + '/' + res[0]['container_usps'] + '/' + res[0]['size_usps']
        return sys_default


#    def picking_shipping_create(self, cr, uid, vals, context=None):
#
#        try:
#            vals['shipping_type'] = vals['shipping_type'] if vals.get('shipping_type', False) else ''
#            cust_default = False
#            saleorderline_obj = self.pool.get('sale.order.line')
#            ### Sys default applicable only for simple orders
#            sys_default = False
#            if vals.get('sale_id'):
#                saleorder_lnk = self.pool.get('sale.order') .browse(cr,uid,vals['sale_id'])
#                saleorderline_ids = saleorderline_obj.search(cr,uid,[('order_id','=',vals['sale_id'])])
#                weight = 0.0
#                for saleorderline_id in saleorderline_ids:
#                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)
#                    weight += (saleorderline_lnk.product_id.product_tmpl_id.weight_net * saleorderline_lnk.product_uom_qty)
#                vals['weight_net'] = weight
#
#                dropoff_type_fedex = vals['dropoff_type_fedex'] if vals.get('dropoff_type_fedex', False) else 'REGULAR_PICKUP'
#                service_type_fedex = vals['service_type_fedex'] if vals.get('service_type_fedex', False) else 'FEDEX_GROUND'
#                packaging_type_fedex = vals['packaging_type_fedex'] if vals.get('packaging_type_fedex', False) else 'YOUR_PACKAGING'
#                package_detail_fedex = vals['package_detail_fedex'] if vals.get('package_detail_fedex', False) else 'INDIVIDUAL_PACKAGES'
#                payment_type_fedex = vals['payment_type_fedex'] if vals.get('payment_type_fedex', False) else 'SENDER'
#                physical_packaging_fedex = vals['physical_packaging_fedex'] if vals.get('physical_packaging_fedex', False) else 'BOX'
#                vals['dropoff_type_fedex'] = dropoff_type_fedex
#                vals['service_type_fedex'] = service_type_fedex
#                vals['packaging_type_fedex'] = packaging_type_fedex
#                vals['package_detail_fedex'] = package_detail_fedex
#                vals['payment_type_fedex'] = payment_type_fedex
#                vals['physical_packaging_fedex'] = physical_packaging_fedex
#
#                pickup_type_ups = '01'
#                service_type_ups = '03'
#                packaging_type_ups = '02'
#                vals['pickup_type_ups'] = pickup_type_ups
#                vals['service_type_ups'] = service_type_ups
#                vals['packaging_type_ups'] = packaging_type_ups
#
#                carrier_id = saleorder_lnk.carrier_id and saleorder_lnk.carrier_id.id or False
#                if carrier_id:
#                    ## Find which carrier has been selected :- cust_default
#                    vals['carrier_id'] = carrier_id
#                    cust_default = self._get_cust_default_shipping(cr,uid,carrier_id,context)
#                    carrier_obj = self.pool.get('delivery.carrier')
#                    carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
#                    if carrier_lnk.is_ups:
#                        service_type_ups = carrier_lnk.service_code or '03'
#                        vals['service_type_ups'] = service_type_ups
#                    elif carrier_lnk.is_fedex:
#                        service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
#                        vals['service_type_fedex'] = service_type_fedex
#                    elif carrier_lnk.is_usps:
#                        service_type_usps = carrier_lnk.service_code or 'All'
#                        first_class_mail_type_usps = carrier_lnk.first_class_mail_type_usps or 'Parcel'
#                        container_usps = carrier_lnk.container_usps or 'Parcel'
#                        size_usps = carrier_lnk.size_usps or 'REGULAR'
#                        vals['service_type_usps'] = service_type_usps
#                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
#                        vals['container_usps'] = container_usps
#                        vals['size_usps'] = size_usps
#
#
##                if len(saleorderline_ids) <= 2:
#
#            ## We consider the Gross Weight
#
#                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
##                   Output: USPS/First Class/Letter/Reqular
##                   If the customer default is not there, ONLY then it goes for system default
#                if not (cust_default and cust_default.split("/")[0] == 'USPS') and sys_default and sys_default.split('/')[0] == 'USPS':
#                    vals['service_type_usps'] = sys_default.split('/')[1] or ''
##                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
#                    vals['container_usps'] = sys_default.split('/')[2] or ''
#                    vals['size_usps'] = sys_default.split('/')[3] or ''
#
#            services = vals.get('services','')
#            if services:
#                print"services",services
#                vals['services'] = services
#                services = vals['services']
##                    vals['services'] = services.id
##                    context['cust_default'] = cust_default
##                    context['sys_default'] = sys_default
##                    context['error'] = False
##            new_id = super(stock_picking, self).create(cr, uid, vals, context)
#            context['cust_default'] = cust_default
#            context['sys_default'] = sys_default
#            context['error'] = False
#        except Exception, e:
##                _logger.info("Exception: %s", e)
#            raise osv.except_osv(_('Error'), _('%s' % (e,)))
##                _logger.info("Exception: %s", e)
#            raise osv.except_osv(_('Error'), _("Exception: %s" %e))
#        return vals
#
#    def create(self, cr, uid, vals, context=None):
#        new_id = 0
#        #create vals:  {'origin': u'SO009', 'note': False, 'state': 'auto', 'name': u'OUT/00007', 'sale_id': 9, 'move_type': u'direct', 'type': 'out', 'address_id': 3, 'invoice_state': 'none', 'company_id': 1}
#        if context is None:
#            context={}
#        if vals.get('type',False) and vals['type'] == 'out':
#            print"Kuldeep"
#            print"val1111111111",vals
#            vals=self.picking_shipping_create(cr, uid, vals, context)
#            print"vals222222222",vals
#            new_id = super(stock_picking, self).create(cr, uid, vals, context)
#        else:
#            new_id = super(stock_picking, self).create(cr, uid, vals, context)
#        return new_id


    def _cal_weight_usps(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            weight_net = picking.weight_net or 0.00
            weight_net_usps = weight_net / 2.2


            res[picking.id] = {
                                'weight_net_usps': weight_net_usps,
                              }
        return res

    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()
   
    def _get_euro(self, cr, uid, context=None):
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False

    _columns = {
#        'total_boxes':fields.integer('Total Boxes'),
        'total_packages': fields.function(calc_total_pack,string='Total Packages',type = 'float',store= True),
        'total_weight': fields.function(calc_total_wt,string='Total Weight',type = 'float',store= True),
        'package_dim':fields.many2one('package.dimension','Package Dimension'),
        'similar_packages' : fields.one2many('similar.packages','picking_id','Group Packages'),
        'use_mps' : fields.boolean('Multiple Package Shipment'),
        'print_label' : fields.boolean('Print Label'),
        'child_tracking_ids':fields.text('Child Tracking Ids'),
        'use_shipping' : fields.boolean('Use Shipping'),
        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type'),
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'service_type_usps' : fields.selection(_get_service_type_usps, 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
        'container_usps' : fields.selection(_get_container_usps,'Container', size=100),
        'size_usps' : fields.selection(_get_size_usps,'Size'),
        'width_usps' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
        'length_usps' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
        'height_usps' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
        'girth_usps' : fields.float('Girth', digits_compute= dp.get_precision('Stock Weight')),
        #'machinable_usps' : fields.boolean('Machinable', domain=[('service_type_usps', 'in', ('first_class','parcel','all','online')), '|', ('first_class_mail_type_usps', 'in', ('letter','flat'))]),
        #'ship_date_usps' : fields.date('Ship Date', help="Date Package Will Be Mailed. Ship date may be today plus 0 to 3 days in advance."),
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
#		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
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
        'pickup_type_ups' : fields.selection([
                ('01','Daily Pickup'),
                ('03','Customer Counter'),
                ('06','One Time Pickup'),
                ('07','On Call Air'),
                ('11','Suggested Retail Rates'),
                ('19','Letter Center'),
                ('20','Air Service Center'),
            ],'Pickup Type'),
        'service_type_ups' : fields.selection([
                ('01','Next Day Air'),
                ('02','Second Day Air'),
                ('03','Ground'),
                ('07','Worldwide Express'),
                ('08','Worldwide Expedited'),
                ('11','Standard'),
                ('12','Three-Day Select'),
                ('13','Next Day Air Saver'),
                ('14','Next Day Air Early AM'),
                ('54','Worldwide Express Plus'),
                ('59','Second Day Air AM'),
                ('65','Saver'),
            ],'Service Type'),
        'packaging_type_ups' : fields.selection([
                ('00','Unknown'),
                ('01','Letter'),
                ('02','Package'),
                ('03','Tube'),
                ('04','Pack'),
                ('21','Express Box'),
                ('24','25Kg Box'),
                ('25','10Kg Box'),
                ('30','Pallet'),
                ('2a','Small Express Box'),
                ('2b','Medium Express Box'),
                ('2c','Large Express Box'),
            ],'Packaging Type'),
        'shipping_label' : fields.binary('Logo'),
        'shipping_rate': fields.float('Shipping Rate'),
        'response_usps_ids' : fields.one2many('shipping.response','picking_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
        'checkbox': fields.boolean('Canada Post'),
        'services': fields.many2one('service.name', 'Services'),
#        'cana_weight': fields.float('Weight', digits=(16,2)),
        'cana_length': fields.float('Length', digits=(16,2)),
        'cana_width': fields.float('Width', digits=(16,2)),
        'cana_height': fields.float('Height', digits=(16,2)),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'package_status': fields.char('Status',size = 64),
        'customsvalue':fields.float('Custom Values'),
#        'picking_id':fields.many2one('stock.picking','Picking'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
   }

    _defaults = {
        'print_label' : 1,
        'use_shipping' : True,
        'shipping_type' : 'Fedex',
        'service_type_usps' : 'All',
        'size_usps' : 'REGULAR',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'packaging_type_fedex' : 'YOUR_PACKAGING',
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pickup_type_ups' : '01',
        'service_type_ups' : '03',
        'packaging_type_ups' : '02',
        'pack_length' : 0,
        'pack_width' : 0,
        'pack_height' : 0,
        'weight_unit':'LB',
        'currency_id':_get_euro,
#        'package_dim': 1,

    }

#    Function to genrate tracking status of single package shipment or multiple package shipment
    def tracking_status(self, cr, uid, ids, context={}):

        stockpicking = self.pool.get('stock.picking').browse(cr, uid, ids[0])
        shippingfedex_obj = self.pool.get('shipping.fedex')
        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
        if not shippingfedex_id:
            raise osv.except_osv(_('Error'), _('Default Fedex settings not defined'))
        else:
            shippingfedex_id = shippingfedex_id[0]

        shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
        account_no = shippingfedex_ptr.account_no
        key = shippingfedex_ptr.key
        password = shippingfedex_ptr.password
        meter_no = shippingfedex_ptr.meter_no
        is_test = shippingfedex_ptr.test
        CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)

        # This is the object that will be handling our tracking status request.
        # We're using the FedexConfig object from example_config.py in this dir.
        trackingRequest = FedexTrackRequest(CONFIG_OBJ)

        stockpicking = self.browse(cr,uid,ids[0])
        use_mps = stockpicking.use_mps
#        When using multiple shipment Package identifier type must be STANDARD_MPS or GROUP_MPS
#        By Default the Package identifier type is TRACKING_NUMBER_OR_DOORTAG
        if use_mps:
            trackingRequest.TrackPackageIdentifier.Type = 'STANDARD_MPS'
        trackingRequest.TrackPackageIdentifier.Value = stockpicking.carrier_tracking_ref
        try:
            trackingRequest.send_request()
            status = trackingRequest.response.TrackDetails[0].StatusDescription
        except Exception, e:
            raise osv.except_osv(_('Error!'), _('%s')%e)
        return self.write(cr,uid,ids[0],{'package_status':status})

    def onchange_number_of_packages(self, cr, uid, ids, number_of_pack,context=None):
#        print"idssssssssssssssss",ids
        tracking_ids=self.browse(cr,uid,ids[0]).tracking_ids
        obj_pack_track = self.pool.get('pack.track')


        for each_tracking_id in tracking_ids:
            obj_pack_track.unlink(cr, uid, each_tracking_id.id)
            tracking_ids= []

        number_of_pack=number_of_pack
        res={}

        pack_track_obj=self.pool.get('pack.track')
        move_records = []
        packages = []
        new_pack = None
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
#            width = 0
            delete_att_vals = []
            if response_usps_ids != []:
                for res_id in response_usps_ids:
                    cr.execute('delete from shipping_response where id=%s',(res_id[1],))
                    cr.commit()



            ### Assign Carrier to Delivery carrier if user has not selected
            carrier_ids=''
            if shipping_type:
                if shipping_type.lower() == 'usps':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_usps','=',True)])
                elif shipping_type.lower() == 'ups':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_code','=',service_type),('is_ups','=',True)])
                elif shipping_type.lower() == 'fedex':
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',service_type),('is_fedex','=',True)])
                elif shipping_type.lower() == 'canada post':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('name','=',canada_service_type),('is_canadapost','=',True)])
                elif shipping_type.lower() == 'all':
                    canada_service_type=self.pool.get('service.name').browse(cr,uid,service_type).name
                    if canada_service_type:
                        service_type=canada_service_type
                    carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,['|','|',('service_output','=',service_type),('name','=',service_type),('service_code','=',service_type)])

                if not carrier_ids:
                    raise osv.except_osv(_('Error'), _('Delivery Method is not defined for selected service type'))



                ### Write this shipping respnse is selected
            vals = {'response_usps_ids' : delete_att_vals,
                    'pack_length' : width,
                    'pack_width' : width,
                    'pack_height' : width,
                    'carrier_id':carrier_ids and carrier_ids[0] or ''
                    }
            return {'value':vals}
        return {'value':{}}

stock_picking_out()
class pack_track(osv.osv):
    _name='pack.track'
    _columns = {
#        'tracking_id':fields.many2one('stock.tracking','Pack'),
        'name':fields.char('Pack Name',size=120),
        'width_ups' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
        'length_ups' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
        'height_ups' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
        'picking_id' : fields.many2one('stock.picking','Picking')
    }
pack_track()

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _cal_move_weight_new(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for move in self.browse(cr, uid, ids, context=context):
            weight = weight_net = 0.00

            converted_qty = move.product_qty
            if move.product_uom.id <> move.product_id.uom_id.id:
                converted_qty = uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)

            if move.product_id.weight > 0.00:
                weight = (converted_qty * move.product_id.weight)

            if move.product_id.weight_net > 0.00:
                    weight_net = (converted_qty * move.product_id.weight_net)

            res[move.id] =  {
                            'weight': weight,
                            'weight_net': weight_net,
                            }
        return res

    _columns = {
        'weight': fields.function(_cal_move_weight_new, method=True, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight',
                  store={
                 'stock.move': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                 }),
        'weight_net': fields.function(_cal_move_weight_new, method=True, type='float', string='Net weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight',
                  store={
                 'stock.move': (lambda self, cr, uid, ids, c=None: ids, ['product_id', 'product_qty', 'product_uom'], 20),
                 }),
        'pack_track_id':fields.many2one('pack.track','Pack Assign'),
        }

stock_move()
class similar_packages(osv.osv):
    _name = 'similar.packages'
    _columns = {
        'number_of_similar_packages' : fields.integer('Similar Packages'),
        'package_dim': fields.many2one('package.dimension','Package Dimension'),
#        'picking_id':fields.many2one('stock.picking.out','Picking id'),
        'picking_id':fields.many2one('shipping.order.processing','Picking id'),
    }
similar_packages()

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
        'length': 0,
        'width': 0,
        'height':0,
        'weight':0,
    }
package_dimension()


class stock_picking(osv.osv):
    _inherit='stock.picking'

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
    
    def onchange_use_mps(self, cr, uid, ids, use_mps,context=None):
        if use_mps:
            return {'value':{'package_detail_fedex':'PACKAGE_GROUPS'}}
        else:
            print "in onchangeeeeeeeeeeee", use_mps
            return {'value':{'package_detail_fedex':'INDIVIDUAL_PACKAGES'}}

    def _get_cust_default_shipping(self,cr,uid,carrier_id,context={}):
        if carrier_id:
            carrier_obj = self.pool.get('delivery.carrier')
            carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
            cust_default = ''
            if carrier_lnk.is_ups:
                cust_default = 'UPS'
                service_type_ups = carrier_lnk.service_code or '03'
                cust_default += '/' + service_type_ups
            elif carrier_lnk.is_fedex:
                cust_default = 'FedEx'
                service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                cust_default += '/' + service_type_fedex
            elif carrier_lnk.is_usps:
                cust_default = 'USPS'
                service_type_usps = carrier_lnk.service_code or 'All'
                cust_default += '/' + service_type_usps
        else:
            cust_default = False
        return cust_default

    def _get_sys_default_shipping(self,cr,uid,saleorderline_ids,weight,context={}):
        sys_default = False
        product_obj = self.pool.get('product.product')
        saleorderline_obj = self.pool.get('sale.order.line')
        product_shipping_obj = self.pool.get('product.product.shipping')
        product_categ_shipping_obj = self.pool.get('product.category.shipping')

        if len(saleorderline_ids) <= 2:
            product_id = False
            ### Making sure product is not Shipping and Handling
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue
                product_id = line.product_id.id

            if not product_id:
                return False

        else:
            ### Get the product id of the heaviest product
            weight = 0.0
            product_id = False
            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
                if line.product_id.type == 'service':
                    continue

                if line.product_id.product_tmpl_id.weight_net > weight:
                    product_id = line.product_id.id
                    weight = line.product_id.product_tmpl_id.weight_net

            if not product_id:
                return False

        product_shipping_ids = product_shipping_obj.search(cr,uid,[('product_id','=',product_id)])

        if not product_shipping_ids:
            categ_id = product_obj.browse(cr,uid,product_id).product_tmpl_id.categ_id.id
            product_categ_shipping_ids = product_categ_shipping_obj.search(cr,uid,[('product_categ_id','=',categ_id)])
            if not product_categ_shipping_ids:
                ### Assume the default
                if (weight*16) > 14.0:
                    sys_default = 'USPS/Priority/Parcel/REGULAR'
                else:
                    sys_default = 'USPS/First Class/Parcel/REGULAR'
                return sys_default

        if product_shipping_ids:
            cr.execute(
                'SELECT * '
                'FROM product_product_shipping '
                'WHERE weight <= %s ' +
                'and product_id=%s ' +
                'order by sequence desc limit 1',
                (weight,product_id))
        else:
            cr.execute(
                'SELECT * '
                'FROM product_category_shipping '
                'WHERE weight <= %s '+
                'and product_categ_id=%s '+
                'order by sequence desc limit 1',
                (weight,categ_id))
        res = cr.dictfetchall()
        ## res:  [{'create_uid': 1, 'create_date': '2011-06-28 01:43:49.017306', 'product_id': 187, 'weight': 3.0, 'sequence': 3, 'container_usps': u'Letter', 'service_type_usps': u'First Class', 'write_uid': None, 'first_class_mail_type_usps': u'Letter', 'size_usps': u'REGULAR', 'write_date': None, 'shipping_type': u'USPS', 'id': 14}]
        ### Format- USPS/First Class/Letter
        sys_default = res[0]['shipping_type'] + '/' + res[0]['service_type_usps'] + '/' + res[0]['container_usps'] + '/' + res[0]['size_usps']
        return sys_default


    def _get_euro(self, cr, uid, context=None):
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False
    _columns={
        'total_packages': fields.function(calc_total_pack,string='Total Packages',type = 'float',store= True),
        'total_weight': fields.function(calc_total_wt,string='Total Weight',type = 'float',store= True),
        'package_dim':fields.many2one('package.dimension','Package Dimension'),
        'similar_packages' : fields.one2many('similar.packages','picking_id','Group Packages'),
        'print_label' : fields.boolean('Print Label'),
        'use_shipping' : fields.boolean('Use Shipping'),
        'child_tracking_ids':fields.text('Child Tracking Ids'),
        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type'),
        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds"),
        'service_type_usps' : fields.selection(_get_service_type_usps, 'Service Type', size=100),
        'first_class_mail_type_usps' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
        'container_usps' : fields.selection(_get_container_usps,'Container', size=100),
        'size_usps' : fields.selection(_get_size_usps,'Size'),
        'width_usps' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight')),
        'length_usps' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight')),
        'height_usps' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight')),
        'girth_usps' : fields.float('Girth', digits_compute= dp.get_precision('Stock Weight')),
        #'machinable_usps' : fields.boolean('Machinable', domain=[('service_type_usps', 'in', ('first_class','parcel','all','online')), '|', ('first_class_mail_type_usps', 'in', ('letter','flat'))]),
        #'ship_date_usps' : fields.date('Ship Date', help="Date Package Will Be Mailed. Ship date may be today plus 0 to 3 days in advance."),
        'dropoff_type_fedex' : fields.selection([
                ('REGULAR_PICKUP','REGULAR PICKUP'),
                ('REQUEST_COURIER','REQUEST COURIER'),
                ('DROP_BOX','DROP BOX'),
                ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
                ('STATION','STATION'),
            ],'Dropoff Type'),
        'package_status': fields.char('Status',size = 64),
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
#		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
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
        'pickup_type_ups' : fields.selection([
                ('01','Daily Pickup'),
                ('03','Customer Counter'),
                ('06','One Time Pickup'),
                ('07','On Call Air'),
                ('11','Suggested Retail Rates'),
                ('19','Letter Center'),
                ('20','Air Service Center'),
            ],'Pickup Type'),
        'service_type_ups' : fields.selection([
                ('01','Next Day Air'),
                ('02','Second Day Air'),
                ('03','Ground'),
                ('07','Worldwide Express'),
                ('08','Worldwide Expedited'),
                ('11','Standard'),
                ('12','Three-Day Select'),
                ('13','Next Day Air Saver'),
                ('14','Next Day Air Early AM'),
                ('54','Worldwide Express Plus'),
                ('59','Second Day Air AM'),
                ('65','Saver'),
            ],'Service Type'),
        'packaging_type_ups' : fields.selection([
                ('00','Unknown'),
                ('01','Letter'),
                ('02','Package'),
                ('03','Tube'),
                ('04','Pack'),
                ('21','Express Box'),
                ('24','25Kg Box'),
                ('25','10Kg Box'),
                ('30','Pallet'),
                ('2a','Small Express Box'),
                ('2b','Medium Express Box'),
                ('2c','Large Express Box'),
            ],'Packaging Type'),
        'shipping_label' : fields.binary('Logo'),
        'shipping_rate': fields.float('Shipping Rate'),
        'response_usps_ids' : fields.one2many('shipping.response','picking_id','Shipping Response'),
        'label_recvd': fields.boolean('Shipping Label', readonly=True),
        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
        'pack_length': fields.integer('Length', required=True),
        'pack_width': fields.integer('Width', required=True),
        'pack_height': fields.integer('Height', required=True),
        'checkbox': fields.boolean('Canada Post'),
        'services': fields.many2one('service.name', 'Services'),
#        'cana_weight': fields.float('Weight', digits=(16,2)),
        'cana_length': fields.float('Length', digits=(16,2)),
        'cana_width': fields.float('Width', digits=(16,2)),
        'cana_height': fields.float('Height', digits=(16,2)),
        'rates': fields.text('Rates', size=1000),
        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits'),
        'customsvalue':fields.float('Custom Values'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'use_mps' : fields.boolean('Multiple Package Shipment'),
   }

    _defaults = {
        'print_label' : 1,
        'use_shipping' : True,
#        'shipping_type' : 'All',
        'service_type_usps' : 'All',
        'size_usps' : 'REGULAR',
        'dropoff_type_fedex' : 'REGULAR_PICKUP',
        'service_type_fedex' : 'FEDEX_GROUND',
        'packaging_type_fedex' : 'YOUR_PACKAGING',
        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
        'payment_type_fedex' : 'SENDER',
        'physical_packaging_fedex' : 'BOX',
        'pickup_type_ups' : '01',
        'service_type_ups' : '03',
        'packaging_type_ups' : '02',
        'pack_length' : 0,
        'pack_width' : 0,
        'pack_height' : 0,
        'weight_unit':'LB',
        'currency_id':_get_euro,
#        'package_dim': 1,


    }

    def generate_shipping(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        for id in ids:
            try:
#                dimension = self.browse(cr,uid,id).package_dim
                stockpicking = self.browse(cr,uid,id)
		if stockpicking.state != 'done':
                    raise osv.except_osv(_('Warning !'),_('You Generate Shipping Quotes only if Order is in Done State.'))
                shipping_type = stockpicking.shipping_type
                type = stockpicking.type
                weight = stockpicking.weight_package if stockpicking.weight_package else stockpicking.weight
#                weight_unit=stockpicking.weight_unit if stockpicking.weight_unit else 'LB'
                weight_unit='LB'
                if weight<=0.0:
                    raise Exception('Package Weight Invalid!')


                ###based on stock.picking type
                if type == 'out':
                    #shipper_address = stockpicking.sale_id and stockpicking.sale_id.shop_id.cust_address or False
		    shipper_address = stockpicking.company_id
                elif type == 'in':
                    shipper_address = stockpicking.address_id
                if not shipper_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise Exception('Shop Address not defined!')
                    else:
                        return False
                if not (shipper_address.name or shipper_address.partner_id.name):
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
                shipper = Address(shipper_address.name or shipper_address.partner_id.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.partner_id.name)

                ### Recipient
                ###based on stock.picking type
                if type == 'out':
                    cust_address = stockpicking.partner_id
                elif type == 'in':
                    cust_address = stockpicking.sale_id and stockpicking.sale_id.shop_id.cust_address or False
                if not cust_address:
                    if 'error' not in context.keys() or context.get('error',False):
                        raise Exception('Reciepient Address not defined!')
                    else:
                        return False
                if not (cust_address.name or cust_address.name):
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
#                if not cust_address.street:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Street."))
                if not cust_address.city:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
#                if not cust_address.state_id.code:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient State Code."))
                if not cust_address.zip:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
                if not cust_address.country_id.code:
                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
#                if not cust_address.email:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient email."))
                receipient = Address(cust_address.name , cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.name)

                # Deleting previous quotes
                shipping_res_obj = self.pool.get('shipping.response')
                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',ids[0])])
#                shipping_res_ids = shipping_res_obj.search(cr,uid,[('picking_id','=',11387)])
                if shipping_res_ids:
                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)

                saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',stockpicking.sale_id.id)])
                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                context['sys_default'] = sys_default
                cust_default= self._get_cust_default_shipping(cr,uid,stockpicking.carrier_id.id,context)
                context['cust_default'] = cust_default

                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                    usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                    service_type_usps = stockpicking.service_type_usps
                    first_class_mail_type_usps = stockpicking.first_class_mail_type_usps or ''
                    container_usps = stockpicking.container_usps or ''
                    size_usps = stockpicking.size_usps
                    width_usps = stockpicking.width_usps
                    length_usps = stockpicking.length_usps
                    height_usps = stockpicking.height_usps
                    girth_usps = stockpicking.girth_usps
                    usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default)
                    usps_response = usps.send()
                    context['type'] = 'USPS'
                    self.create_quotes(cr,uid,ids,usps_response,context)

                if shipping_type == 'UPS' or shipping_type == 'All':
                    ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                    pickup_type_ups = stockpicking.pickup_type_ups
                    service_type_ups = stockpicking.service_type_ups
                    packaging_type_ups = stockpicking.packaging_type_ups
#                    print"shipper",shipper
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient, cust_default, sys_default)
                    ups_response = ups.send()
                    context['type'] = 'UPS'
                    self.create_quotes(cr,uid,ids,ups_response,context)

                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = stockpicking.dropoff_type_fedex
                    service_type_fedex = stockpicking.service_type_fedex
                    packaging_type_fedex = stockpicking.packaging_type_fedex
                    package_detail_fedex = stockpicking.package_detail_fedex
                    payment_type_fedex = stockpicking.payment_type_fedex
                    physical_packaging_fedex = stockpicking.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    fed_length = stockpicking.pack_length
                    fed_width = stockpicking.pack_width
                    fed_height = stockpicking.pack_height
                    error_required = True
                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context,fed_length,fed_width,fed_height)
            except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
            return True


stock_picking()
