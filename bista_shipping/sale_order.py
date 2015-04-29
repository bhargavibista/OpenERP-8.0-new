# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

import urllib2
import urllib
from base64 import b64decode
import binascii
import openerp.addons.decimal_precision as dp
import socket

import shippingservice
from miscellaneous import Address

from fedex.services.rate_service import FedexRateServiceRequest
from fedex.services.ship_service import FedexProcessShipmentRequest
from fedex.config import FedexConfig
import suds
from suds.client import Client

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
#logger = netsvc.Logger()
import Image

import connection_osv as connection
import math

import logging
_logger = logging.getLogger(__name__)



def _get_shipping_type(self, cr, uid, context=None):
    return [
        ('Fedex','Fedex'),
#        ('UPS','UPS'),
#        ('USPS','USPS'),
#        ('All','All'),
#        ('Canada Post','Canada Post'),
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
#        ('Card', 'Card'),
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
#        ('Flat Rate Box', 'Flat Rate Box'),
        ('SM Flat Rate Box', 'SM Flat Rate Box'),
        ('MD Flat Rate Box', 'MD Flat Rate Box'),
        ('LG Flat Rate Box', 'LG Flat Rate Box'),
        ('RegionalRateBoxA', 'RegionalRateBoxA'),
        ('RegionalRateBoxB', 'RegionalRateBoxB'),
#        ('Rectangular', 'Rectangular'),
#        ('Non-Rectangular', 'Non-Rectangular'),
     ]

def _get_size_usps(self, cr, uid, context=None):
    return [
        ('REGULAR', 'Regular'),
        ('LARGE', 'Large'),
     ]


class sale_order(osv.osv):
#    _name = "sale.order"
    _inherit = "sale.order"
#    def create(self, cr, uid, vals, context=None):
#        #print "Shipping sale create called: ",vals
#        partneraddr_obj = self.pool.get('res.partner.address')
#        vals['invalid_addr'] = True
#        if partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).address_checked == True:
#            vals['invalid_addr'] = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).invalid_addr
#            id = super(sale_order, self).create(cr, uid, vals, context=context)
#            return id
#
#        ### Add shipping code here ####
#        try:
#            shippingups_obj = self.pool.get('shipping.ups')
#            shippingups_id = shippingups_obj.search(cr,uid,[('active','=',True)])
#            print "shippingups_id: ",shippingups_id
#            if not shippingups_id:
#                vals['invalid_addr'] = True
#            else:
#                shippingups_id = shippingups_id[0]
#
#                shippingups_ptr = shippingups_obj.browse(cr,uid,shippingups_id)
#                access_license_no = shippingups_ptr.access_license_no
#                user_id = shippingups_ptr.user_id
#                password = shippingups_ptr.password
#                shipper_no = shippingups_ptr.shipper_no
#
#                ### Get Address from sale order
#                street = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).street or ''
#
#                street2 = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).street2 or ''
#
#                city = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).city or ''
#
#                state_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).state_id.code or ''
#
#                country_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).country_id.code or ''
#
#                postal_code = partneraddr_obj.browse(cr,uid,vals['partner_shipping_id']).zip or ''
#
#                data = """<?xml version=\"1.0\"?>
#        <AccessRequest xml:lang=\"en-US\">
#            <AccessLicenseNumber>%s</AccessLicenseNumber>
#            <UserId>%s</UserId>
#            <Password>%s</Password>
#        </AccessRequest>
#        <?xml version="1.0"?>
#        <AddressValidationRequest xml:lang="en-US">
#           <Request>
#              <TransactionReference>
#                 <CustomerContext>Customer Data</CustomerContext>
#                 <XpciVersion>1.0001</XpciVersion>
#              </TransactionReference>
#              <RequestAction>AV</RequestAction>
#           </Request>
#           <Address>
#              <City>%s</City>
#              <StateProvinceCode>%s</StateProvinceCode>
#              <CountryCode>%s</CountryCode>
#              <PostalCode>%s</PostalCode>
#           </Address>
#        </AddressValidationRequest>
#        """ % (access_license_no,user_id,password,city,state_code,country_code,postal_code)
#
#            if shippingups_ptr.test:
#                api_url = 'https://wwwcie.ups.com/ups.app/xml/AV'
#            else:
#                api_url = 'https://onlinetools.ups.com/ups.app/xml/AV'
#
#
#                webf = urllib.urlopen(api_url, data)
#                response = webf.read()
#
#                sIndex = response.find('<ResponseStatusDescription>')
#                eIndex = response.find('</ResponseStatusDescription>')
#                status = response[sIndex+27:eIndex]
#
#                if status != 'Success':
#                    vals['invalid_addr'] = True
#
#                else:
#                    sIndex = eIndex = i = 0
#
#                    sIndex = response.find('<City>',i)
#                    eIndex = response.find('</City>',i)
#                    city_resp = response[sIndex+6:eIndex]
#
#                    i = eIndex + 7
#
#                    sIndex = response.find('<StateProvinceCode>',i)
#                    eIndex = response.find('</StateProvinceCode>',i)
#                    state_code_resp = response[sIndex+19:eIndex]
#                    i = eIndex + 20
#
#                    sIndex = response.find('<PostalCodeLowEnd>',i)
#                    eIndex = response.find('</PostalCodeLowEnd>',i)
#                    postal_code_lowend_resp = response[sIndex+18:eIndex]
#                    i = eIndex + 19
#
#                    sIndex = response.find('<PostalCodeHighEnd>',i)
#                    eIndex = response.find('</PostalCodeHighEnd>',i)
#                    postal_code_highend_resp = response[sIndex+19:eIndex]
#                    i = eIndex + 20
#
#                    vals['invalid_addr'] = True
#                    while (sIndex != -1):
#                        if city.upper() == city_resp and state_code.upper() == state_code_resp and (int(postal_code) >= int(postal_code_lowend_resp) and int(postal_code) <= int(postal_code_highend_resp)):
#                            vals['invalid_addr'] = False
#                            break
#
#                        sIndex = response.find('<City>',i)
#                        if sIndex == -1:
#                            break
#                        eIndex = response.find('</City>',i)
#                        city_resp = response[sIndex+6:eIndex]
#
#                        sIndex = response.find('<StateProvinceCode>',i)
#                        eIndex = response.find('</StateProvinceCode>',i)
#                        state_code_resp = response[sIndex+19:eIndex]
#
#                        sIndex = response.find('<PostalCodeLowEnd>',i)
#                        eIndex = response.find('</PostalCodeLowEnd>',i)
#                        postal_code_lowend_resp = response[sIndex+18:eIndex]
#
#                        sIndex = response.find('<PostalCodeHighEnd>',i)
#                        eIndex = response.find('</PostalCodeHighEnd>',i)
#                        postal_code_highend_resp = response[sIndex+19:eIndex]
#                        i = eIndex + 20
#        except:
#            vals['invalid_addr'] = True
#
#        id = super(sale_order, self).create(cr, uid, vals, context=context)
#        partneraddr_obj.write(cr,uid,vals['partner_shipping_id'],{'address_checked':True,'invalid_addr':vals['invalid_addr']})
#        return id

    def _default_journal(self, cr, uid, context={}):
        accountjournal_obj = self.pool.get('account.journal')
        accountjournal_ids = accountjournal_obj.search(cr,uid,[('name','=','Sales Journal')])
        if accountjournal_ids:
            return accountjournal_ids[0]
        else:
            return False
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
            zip_code_customer = self.browse(cr, uid, ids[0]).partner_order_id.zip
            zip_code_supplier = self.browse(cr, uid, ids[0]).shop_id.cust_address.zip
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
                _logger.info("total: %s", total)
                _logger.info("shipping_rate: %s", shipping_rate)
        cr.execute("UPDATE sale_order SET rates='%s' where id=%d"%(shipping_rate,ids[0],))
        return True

    def prepare_shipping_response(self, cr, uid, order, context=None):
        shipping = self.pool.get('shipping.response')
        response = shipping.search(cr,uid,[('sale_order_id', '=', order.id)])
        return response

#    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
#        res = super(sale_order, self)._create_pickings_and_procurements(cr, uid, order, order_lines, picking_id=False, context=None)
#        return res
#    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
#        """Create the required procurements to supply sale order lines, also connecting
#        the procurements to appropriate stock moves in order to bring the goods to the
#        sale order's requested location.
#
#        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
#        a standard outgoing picking will be created to wrap the stock moves, as returned
#        by :meth:`~._prepare_order_picking`.
#
#        Modules that wish to customize the procurements or partition the stock moves over
#        multiple stock pickings may override this method and call ``super()`` with
#        different subsets of ``order_lines`` and/or preset ``picking_id`` values.
#
#        :param browse_record order: sale order to which the order lines belong
#        :param list(browse_record) order_lines: sale order line records to procure
#        :param int picking_id: optional ID of a stock picking to which the created stock moves
#                               will be added. A new picking will be created if ommitted.
#        :return: True
#        """
#        print "create pickings of sale order in shipping bista"
#        move_obj = self.pool.get('stock.move')
#        picking_obj = self.pool.get('stock.picking')
#        procurement_obj = self.pool.get('procurement.order')
#        attach_obj=self.pool.get('ir.attachment')
#        proc_ids = []
#        attach_id = 0
#
#        for line in order_lines:
#            if line.state == 'done':
#                continue
#
#            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
#
#            if line.product_id:
#                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
#                    if not picking_id:
##                         picking_id=super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)
#                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
##                        carrier_track_numer=self.pool.get('stock.picking').browse(cr,uid,picking_id).carrier_tracking_ref
##                        if carrier_track_numer:
##                            attach_id = attach_obj.search(cr,uid,[('res_id', '=', order.id),('name','like','Shipping')])
##                            if attach_id:
##                                attach_id=attach_obj.copy(cr,uid,attach_id[0],{'res_model':'stock.picking','res_id':picking_id})
#                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
#                else:
#                    # a service has no stock move
#                    move_id = False
#
#                if line.product_id.product_tmpl_id.type in ('product', 'consu'):
#                    proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
#                    proc_ids.append(proc_id)
#                    line.write({'procurement_id': proc_id})
#                    self.ship_recreate(cr, uid, order, line, move_id, proc_id)
#                # Create shipping response
#                #if attach_id != 0:
#                self.prepare_shipping_response(cr, uid, order, picking_id, context=context)
#        wf_service = netsvc.LocalService("workflow")
#        if picking_id:
#            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
#
#        for proc_id in proc_ids:
#            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
#
#        val = {}
#        if order.state == 'shipping_except':
#            val['state'] = 'progress'
#            val['shipped'] = False
#
#            if (order.order_policy == 'manual'):
#                for line in order.order_line:
#                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
#                        val['state'] = 'manual'
#                        break
#        order.write(val)
#        return True
#
#
#
#    def action_assign_new(self, cr, uid, ids, *args):
#        """ Changes state of picking to available if all moves are confirmed.
#        @return: True
#        """
#        for pick in self.browse(cr, uid, ids):
#            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
#            if not move_ids:
#                return False
#            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
#        return True

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

##############saziya

#    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None,fed_length=None,fed_width=None,fed_height=None):
#    def generate_fedex_shipping(self, cr, uid, ids, dropoff_type_fedex, service_type_fedex, packaging_type_fedex, package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight, shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code, sys_default=False,cust_default=False, error=True, context=None,fed_length=None,fed_width=None,fed_height=None):
#        if 'fedex_active' in context.keys() and context['fedex_active'] == False:
#            return True
#        shippingfedex_obj = self.pool.get('shipping.fedex')
#        shippingfedex_id = shippingfedex_obj.search(cr,uid,[('active','=',True)])
#        if not shippingfedex_id:
#            if error:
#                raise osv.except_osv(_('Error'), _('Default FedEx settings not defined'))
#            else:
#                return False
#        else:
#            shippingfedex_id = shippingfedex_id[0]
#
#        shippingfedex_ptr = shippingfedex_obj.browse(cr,uid,shippingfedex_id)
#        account_no = shippingfedex_ptr.account_no
#        key = shippingfedex_ptr.key
#        password = shippingfedex_ptr.password
#        meter_no = shippingfedex_ptr.meter_no
#        is_test = shippingfedex_ptr.test
#        CONFIG_OBJ = FedexConfig(key=key, password=password, account_number=account_no, meter_number=meter_no, use_test_server=is_test)
#        rate_request = FedexRateServiceRequest(CONFIG_OBJ)
#
#        stockpicking_lnk = self.browse(cr,uid,ids[0])
#
#
#        # This is very generalized, top-level information.
#        # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
#        rate_request.RequestedShipment.DropoffType = dropoff_type_fedex
#
#        # See page 355 in WS_ShipService.pdf for a full list. Here are the common ones:
#        # STANDARD_OVERNIGHT, PRIORITY_OVERNIGHT, FEDEX_GROUND, FEDEX_EXPRESS_SAVER
#        rate_request.RequestedShipment.ServiceType = service_type_fedex
#
#        # What kind of package this will be shipped in.
#        # FEDEX_BOX, FEDEX_PAK, FEDEX_TUBE, YOUR_PACKAGING
#        rate_request.RequestedShipment.PackagingType = packaging_type_fedex
#
#        # No idea what this is.
#        # INDIVIDUAL_PACKAGES, PACKAGE_GROUPS, PACKAGE_SUMMARY
#        rate_request.RequestedShipment.PackageDetail = package_detail_fedex
#
#        rate_request.RequestedShipment.Shipper.Address.PostalCode = shipper_postal_code
#        rate_request.RequestedShipment.Shipper.Address.CountryCode = shipper_country_code
#        rate_request.RequestedShipment.Shipper.Address.Residential = False
#
#        rate_request.RequestedShipment.Recipient.Address.PostalCode = customer_postal_code
#        rate_request.RequestedShipment.Recipient.Address.CountryCode = customer_country_code
#        # This is needed to ensure an accurate rate quote with the response.
#        #rate_request.RequestedShipment.Recipient.Address.Residential = True
#        #include estimated duties and taxes in rate quote, can be ALL or NONE
#        rate_request.RequestedShipment.EdtRequestType = 'NONE'
#
#        # Who pays for the rate_request?
#        # RECIPIENT, SENDER or THIRD_PARTY
#        rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type_fedex
#
#        package1_weight = rate_request.create_wsdl_object_of_type('Weight')
#        package1_weight.Value = weight
#        package1_weight.Units = "LB"
#
#        package1_dimensions=rate_request.create_wsdl_object_of_type('Dimensions')
#        package1_dimensions.Length=int(fed_length)
#        package1_dimensions.Width=int(fed_width)
#        package1_dimensions.Height=int(fed_height)
#        package1_dimensions.Units="IN"
#        _logger.info("Package Dimensions %s", package1_dimensions)
#        package1 = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
#        package1.Weight = package1_weight
#        package1.Dimensions = package1_dimensions
#        #can be other values this is probably the most common
#        package1.PhysicalPackaging = physical_packaging_fedex
#        # Un-comment this to see the other variables you may set on a package.
#        #print package1
#
#        # This adds the RequestedPackageLineItem WSDL object to the rate_request. It
#        # increments the package count and total weight of the rate_request for you.
#        rate_request.add_package(package1)
#
#        # If you'd like to see some documentation on the ship service WSDL, un-comment
#        # this line. (Spammy).
#        #print rate_request.client
#
#        # Un-comment this to see your complete, ready-to-send request as it stands
#        # before it is actually sent. This is useful for seeing what values you can
#        # change.
#        #print rate_request.RequestedShipment
#
#        # Fires off the request, sets the 'response' attribute on the object.
#        try:
#            rate_request.send_request()
#
#        except Exception, e:
#            if error:
#                raise Exception('%s' % (e))
#            return False
#
#        # This will show the reply to your rate_request being sent. You can access the
#        # attributes through the response attribute on the request object. This is
#        # good to un-comment to see the variables returned by the FedEx reply.
#        #print 'response: ', rate_request.response
#
#        # Here is the overall end result of the query.
#        _logger.info("Highest Severity %s", rate_request.response.HighestSeverity)
#
#        for detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            for surcharge in detail.ShipmentRateDetail.Surcharges:
#                if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
#                    _logger.info("ODA rate_request charge %s", surcharge.Amount.Amount)
#
#        for rate_detail in rate_request.response.RateReplyDetails[0].RatedShipmentDetails:
#            _logger.info("Net FedEx Charge %s %s", rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount)
#
#        sr_no = 9
#        sys_default_value = False
#        cust_default_value = False
#        if sys_default:
#            sys_default_vals = sys_default.split('/')
#            if sys_default_vals[0] == 'FedEx':
#                sys_default_value = True
#                sr_no = 2
#
#        if cust_default:
#            cust_default_vals = cust_default.split('/')
#            if cust_default_vals[0] == 'FedEx':
#                cust_default_value = True
#                sr_no = 1
#
#        fedex_res_vals = {
#            'name' : service_type_fedex,
#            'type' : 'FedEx',
#            'rate' : rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Amount,
#            'sale_order_id' : ids[0], #Change the ids[0] when switch to create
#            'weight' : weight,
#            'sys_default' : sys_default_value,
#            'cust_default' : cust_default_value,
#            'sr_no' : sr_no
#        }
#        fedex_res_id = self.pool.get('shipping.response').create(cr,uid,fedex_res_vals)
#        if fedex_res_id:
#            return True
#        else:
#            return False
###################################saziya
    def create_quotes(self, cr, uid, ids, values, context={}):
        res_id = 0
        for vals in values.postage:
            quotes_vals = {
                'name' : vals['Service'],
                'type' : context['type'],
                'rate' : vals['Rate'],
                'sale_order_id' : ids[0], #Change the ids[0] when switch to create
                'weight' : values.weight,
                'sys_default' : False,
                'cust_default' : False,
                'sr_no' : vals['sr_no'],
            }
            res_id = self.pool.get('shipping.response').create(cr,uid,quotes_vals)
#            logger.notifyChannel('init', netsvc.LOG_WARNING, 'res_id is %s'%(res_id,))
        if res_id:
            return True
        else:
            return False

    def create_attachment(self, cr, uid, ids, vals, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        data_attach = {
            'name': 'ShippingLabel.' + vals.image_format.lower() ,
            'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image))),
            'description': 'Packing List',
            'res_name': self.browse(cr,uid,ids[0]).name,
            'res_model': 'sale.order',
            'res_id': ids[0],
        }
        attach_id = attachment_pool.search(cr,uid,[('res_id','=',ids[0]),('res_name','=',self.browse(cr,uid,ids[0]).name)])
        if not attach_id:
            attach_id = attachment_pool.create(cr, uid, data_attach)
        else:
            attach_id = attach_id[0]
            attach_result = attachment_pool.write(cr, uid, attach_id, data_attach)
        return attach_id

###########################saziya
    ## This function is called when generate shipping quotes button is clicked
#    def generate_shipping(self, cr, uid, ids, context={}):
#        order_line_obj=self.pool.get('sale.order.line')
#        if context is None:
#            context = {}
##        logger.notifyChannel('init', netsvc.LOG_WARNING, 'inside generate_shipping context: %s'%(context,))
#        for id in ids:
#            try:
#                saleorder = self.browse(cr,uid,id)
#                line_items=order_line_obj.search(cr,uid,[('order_id','=',id)])
#                if len(line_items)==0:
#                    raise osv.except_osv(_('Warning !'),_("Please Enter Line Item to Sale Order"))
#                shipping_type = saleorder.shipping_type
##                type='out'
#                weight = saleorder.weight_package
#                weight_unit='LB'
#                if weight<=0.0:
#                    raise osv.except_osv(_('Warning !'),_("Package Weight Invalid"))
#
#                ###based on stock.picking type
##                if type == 'out':
##                    shipper_address = saleorder.shop_id and saleorder.shop_id.cust_address or False
##                elif type == 'in':
##                    shipper_address = saleorder.address_id
#                shipper_address = saleorder.shop_id and saleorder.shop_id.cust_address or False
#                if not shipper_address:
#                    if 'error' not in context.keys() or context.get('error',False):
#                        raise Exception('Shop Address not defined!')
#                    else:
#                        return False
#                if not (shipper_address.name or shipper_address.partner_id.name):
#                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
##                if not shipper_address.street:
##                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
#                if not shipper_address.city:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
##                if not shipper_address.state_id.code:
##                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
#                if not shipper_address.zip:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
#                if not shipper_address.country_id.code:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
#                shipper = Address(shipper_address.name or shipper_address.partner_id.name, shipper_address.street, shipper_address.city, shipper_address.state_id.code or '', shipper_address.zip, shipper_address.country_id.code, shipper_address.street2 or '', shipper_address.phone or '', shipper_address.email, shipper_address.partner_id.name)
#
#
##                if type == 'out':
##                    cust_address = saleorder.partner_shipping_id
##                elif type == 'in':
##                    cust_address = saleorder.sale_id and saleorder.sale_id.shop_id.cust_address or False
#                cust_address = saleorder.partner_shipping_id
#                if not cust_address:
#                    if 'error' not in context.keys() or context.get('error',False):
#                        raise Exception('Reciepient Address not defined!')
#                    else:
#                        return False
#                if not (cust_address.name or cust_address.partner_id.name):
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
##                if not cust_address.street:
##                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Street."))
#                if not cust_address.city:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
##                if not cust_address.state_id.code:
##                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient State Code."))
#                if not cust_address.zip:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
#                if not cust_address.country_id.code:
#                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
##                if not cust_address.email:
##                    raise osv.except_osv(_('Warning !'),_("You must enter Reciepient email."))
#                receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)
#                shipping_res_obj = self.pool.get('shipping.response')
#                shipping_res_ids = shipping_res_obj.search(cr,uid,[('sale_order_id','=',ids[0])])
#                if shipping_res_ids:
#                    shipping_res_obj.unlink(cr,uid,shipping_res_ids)
#
#                saleorderline_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',saleorder.id)])
#                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
#                context['sys_default'] = sys_default
#                cust_default= self._get_cust_default_shipping(cr,uid,saleorder.carrier_id.id,context)
#                context['cust_default'] = cust_default
#
#                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
#                    usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
#                    service_type_usps = saleorder.service_type_usps
#                    first_class_mail_type_usps = saleorder.first_class_mail_type_usps or ''
#                    container_usps = saleorder.container_usps or ''
#                    size_usps = saleorder.size_usps
#                    width_usps = saleorder.width_usps
#                    length_usps = saleorder.length_usps
#                    height_usps = saleorder.height_usps
#                    girth_usps = saleorder.girth_usps
#                    usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default, sys_default)
#                    usps_response = usps.send()
#                    context['type'] = 'USPS'
#                    self.create_quotes(cr,uid,ids,usps_response,context)
#
#                if shipping_type == 'UPS' or shipping_type == 'All':
#                    ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
#                    pickup_type_ups = saleorder.pickup_type_ups
#                    service_type_ups = saleorder.service_type_ups
#                    packaging_type_ups = saleorder.packaging_type_ups
#                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient, cust_default, sys_default)
#                    ups_response = ups.send()
#                    context['type'] = 'UPS'
#                    self.create_quotes(cr,uid,ids,ups_response,context)
#
#                if shipping_type == 'Fedex' or shipping_type == 'All':
#                    dropoff_type_fedex = saleorder.dropoff_type_fedex
#                    service_type_fedex = saleorder.service_type_fedex
#                    packaging_type_fedex = saleorder.packaging_type_fedex
#                    package_detail_fedex = saleorder.package_detail_fedex
#                    payment_type_fedex = saleorder.payment_type_fedex
#                    physical_packaging_fedex = saleorder.physical_packaging_fedex
#                    shipper_postal_code = shipper.zip
#                    shipper_country_code = shipper.country_code
#                    customer_postal_code = receipient.zip
#                    customer_country_code = receipient.country_code
#                    fed_length = saleorder.pack_length
#                    fed_width = saleorder.pack_width
#                    fed_height = saleorder.pack_height
#                    error_required = True
#                    shipping_res = self.generate_fedex_shipping(cr,uid,[id],dropoff_type_fedex,service_type_fedex,packaging_type_fedex,package_detail_fedex,payment_type_fedex,physical_packaging_fedex,weight,shipper_postal_code,shipper_country_code,customer_postal_code,customer_country_code,sys_default,cust_default,error_required,context,fed_length,fed_width,fed_height)
#            except Exception, exc:
#                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
#            return True
#
#    def _get_cust_default_shipping(self,cr,uid,carrier_id,context={}):
#        if carrier_id:
#            carrier_obj = self.pool.get('delivery.carrier')
#            carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
#            cust_default = ''
#            if carrier_lnk.is_ups:
#                cust_default = 'UPS'
#                service_type_ups = carrier_lnk.service_code or '03'
#                cust_default += '/' + service_type_ups
#            elif carrier_lnk.is_fedex:
#                cust_default = 'FedEx'
#                service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
#                cust_default += '/' + service_type_fedex
#            elif carrier_lnk.is_usps:
#                cust_default = 'USPS'
#                service_type_usps = carrier_lnk.service_code or 'All'
#                cust_default += '/' + service_type_usps
#        else:
#            cust_default = False
#        return cust_default
#
#    def _get_sys_default_shipping(self,cr,uid,saleorderline_ids,weight,context={}):
#        sys_default = False
#        product_obj = self.pool.get('product.product')
#        saleorderline_obj = self.pool.get('sale.order.line')
#        product_shipping_obj = self.pool.get('product.product.shipping')
#        product_categ_shipping_obj = self.pool.get('product.category.shipping')
#
#        if len(saleorderline_ids) <= 2:
#            product_id = False
#            ### Making sure product is not Shipping and Handling
#            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
#                if line.product_id.type == 'service':
#                    continue
#                product_id = line.product_id.id
#
#            if not product_id:
#                return False
#
#        else:
#            ### Get the product id of the heaviest product
#            weight = 0.0
#            product_id = False
#            for line in saleorderline_obj.browse(cr,uid,saleorderline_ids):
#                if line.product_id.type == 'service':
#                    continue
#
#                if line.product_id.product_tmpl_id.weight_net > weight:
#                    product_id = line.product_id.id
#                    weight = line.product_id.product_tmpl_id.weight_net
#
#            if not product_id:
#                return False
#
#        product_shipping_ids = product_shipping_obj.search(cr,uid,[('product_id','=',product_id)])
#
#        if not product_shipping_ids:
#            categ_id = product_obj.browse(cr,uid,product_id).product_tmpl_id.categ_id.id
#            product_categ_shipping_ids = product_categ_shipping_obj.search(cr,uid,[('product_categ_id','=',categ_id)])
#            if not product_categ_shipping_ids:
#                ### Assume the default
#                if (weight*16) > 14.0:
#                    sys_default = 'USPS/Priority/Parcel/REGULAR'
#                else:
#                    sys_default = 'USPS/First Class/Parcel/REGULAR'
#                return sys_default
#
#        if product_shipping_ids:
#            cr.execute(
#                'SELECT * '
#                'FROM product_product_shipping '
#                'WHERE weight <= %s ' +
#                'and product_id=%s ' +
#                'order by sequence desc limit 1',
#                (weight,product_id))
#        else:
#            cr.execute(
#                'SELECT * '
#                'FROM product_category_shipping '
#                'WHERE weight <= %s '+
#                'and product_categ_id=%s '+
#                'order by sequence desc limit 1',
#                (weight,categ_id))
#        res = cr.dictfetchall()
#        ## res:  [{'create_uid': 1, 'create_date': '2011-06-28 01:43:49.017306', 'product_id': 187, 'weight': 3.0, 'sequence': 3, 'container_usps': u'Letter', 'service_type_usps': u'First Class', 'write_uid': None, 'first_class_mail_type_usps': u'Letter', 'size_usps': u'REGULAR', 'write_date': None, 'shipping_type': u'USPS', 'id': 14}]
#        ### Format- USPS/First Class/Letter
#        sys_default = res[0]['shipping_type'] + '/' + res[0]['service_type_usps'] + '/' + res[0]['container_usps'] + '/' + res[0]['size_usps']
#        return sys_default
###################################saziya

    def create(self, cr, uid, vals, context=None):
        #new_id = 0
        #create vals:  {'origin': u'SO009', 'note': False, 'state': 'auto', 'name': u'OUT/00007', 'sale_id': 9, 'move_type': u'direct', 'type': 'out', 'address_id': 3, 'invoice_state': 'none', 'company_id': 1}
        if context is None:
            context={}
        if vals.get('type',False) and vals['type'] == 'out':
            try:
                vals['shipping_type'] = 'All'
                cust_default = False
                saleorder_lnk = self.pool.get('sale.order') .browse(cr,uid,vals['sale_id'])
                saleorderline_obj = self.pool.get('sale.order.line')
                saleorderline_ids = saleorderline_obj.search(cr,uid,[('order_id','=',vals['sale_id'])])
                #logger.notifyChannel('init', netsvc.LOG_WARNING, 'saleorderline_ids is %s'%(saleorderline_ids),)
                weight = 0.0
                for saleorderline_id in saleorderline_ids:
                    saleorderline_lnk = saleorderline_obj.browse(cr,uid,saleorderline_id)
                    weight += (saleorderline_lnk.product_id.product_tmpl_id.weight_net * saleorderline_lnk.product_uom_qty)
                vals['weight_net'] = weight

                dropoff_type_fedex = vals['dropoff_type_fedex'] if vals.get('dropoff_type_fedex', False) else 'REGULAR_PICKUP'
                service_type_fedex = vals['service_type_fedex'] if vals.get('service_type_fedex', False) else 'FEDEX_GROUND'
                packaging_type_fedex = vals['packaging_type_fedex'] if vals.get('packaging_type_fedex', False) else 'YOUR_PACKAGING'
                package_detail_fedex = vals['package_detail_fedex'] if vals.get('package_detail_fedex', False) else 'INDIVIDUAL_PACKAGES'
                payment_type_fedex = vals['payment_type_fedex'] if vals.get('payment_type_fedex', False) else 'SENDER'
                physical_packaging_fedex = vals['physical_packaging_fedex'] if vals.get('physical_packaging_fedex', False) else 'BOX'
                vals['dropoff_type_fedex'] = dropoff_type_fedex
                vals['service_type_fedex'] = service_type_fedex
                vals['packaging_type_fedex'] = packaging_type_fedex
                vals['package_detail_fedex'] = package_detail_fedex
                vals['payment_type_fedex'] = payment_type_fedex
                vals['physical_packaging_fedex'] = physical_packaging_fedex

                pickup_type_ups = '01'
                service_type_ups = '03'
                packaging_type_ups = '02'
                vals['pickup_type_ups'] = pickup_type_ups
                vals['service_type_ups'] = service_type_ups
                vals['packaging_type_ups'] = packaging_type_ups

                carrier_id = saleorder_lnk.carrier_id and saleorder_lnk.carrier_id.id or False
                if carrier_id:
                    ## Find which carrier has been selected :- cust_default
                    vals['carrier_id'] = carrier_id
                    cust_default = self._get_cust_default_shipping(cr,uid,carrier_id,context)
                    carrier_obj = self.pool.get('delivery.carrier')
                    carrier_lnk = carrier_obj.browse(cr,uid,carrier_id)
                    if carrier_lnk.is_ups:
                        service_type_ups = carrier_lnk.service_code or '03'
                        vals['service_type_ups'] = service_type_ups
                    elif carrier_lnk.is_fedex:
                        service_type_fedex = carrier_lnk.service_code or 'FEDEX_GROUND'
                        vals['service_type_fedex'] = service_type_fedex
                    elif carrier_lnk.is_usps:
                        service_type_usps = carrier_lnk.service_code or 'All'
                        first_class_mail_type_usps = carrier_lnk.first_class_mail_type_usps or 'Parcel'
                        container_usps = carrier_lnk.container_usps or 'Parcel'
                        size_usps = carrier_lnk.size_usps or 'REGULAR'
                        vals['service_type_usps'] = service_type_usps
                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                        vals['container_usps'] = container_usps
                        vals['size_usps'] = size_usps
                ### Sys default applicable only for simple orders
                sys_default = False
#                if len(saleorderline_ids) <= 2:

                ## We consider the Gross Weight

                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
                if not (cust_default and cust_default.split("/")[0] == 'USPS') and sys_default and sys_default.split('/')[0] == 'USPS':
                    vals['service_type_usps'] = sys_default.split('/')[1] or ''
#                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
                    vals['container_usps'] = sys_default.split('/')[2] or ''
                    vals['size_usps'] = sys_default.split('/')[3] or ''
#
#                ### Sys default applicable only for simple orders
#                sys_default = False
##                if len(saleorderline_ids) <= 2:
#
#                ## We consider the Gross Weight
#
#                sys_default = self._get_sys_default_shipping(cr,uid,saleorderline_ids,weight,context)
#                if not (cust_default and cust_default.split("/")[0] == 'USPS') and sys_default and sys_default.split('/')[0] == 'USPS':
#                    vals['service_type_usps'] = sys_default.split('/')[1] or ''
##                        vals['first_class_mail_type_usps'] = first_class_mail_type_usps
#                    vals['container_usps'] = sys_default.split('/')[2] or ''
#                    vals['size_usps'] = sys_default.split('/')[3] or ''
#
                new_id = super(sale_order, self).create(cr, uid, vals, context)
#                error_required = False
#
                context['cust_default'] = cust_default
                context['sys_default'] = sys_default
                context['error'] = False
                res = self.generate_shipping(cr,uid,[new_id],context)

            except Exception, e:
                _logger.exception("Exception: %s", e)
                new_id = super(stock_picking, self).create(cr, uid, vals, context)
        else:
            new_id = super(sale_order, self).create(cr, uid, vals, context)
        return new_id


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

    def dummy_fun(self, cr, uid, ids, context=None):
        res = self._cal_weight(cr, uid, ids, context)
        return True

    def _cal_weight(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            order_line_obj=self.pool.get('sale.order.line')
            line_items=order_line_obj.search(cr, uid, [('order_id','=',sale.id)])
            total_weight = 0.00
            for move in line_items:
                weight=order_line_obj.browse(cr,uid,move).product_id.weight
                product_type=order_line_obj.browse(cr,uid,move).product_id.type
                if weight<=0.00 and product_type != 'service':
                    raise osv.except_osv(_('Warning'), _('Weight not defined for %s' % order_line_obj.browse(cr,uid,move).product_id.name))
                else:
                    total_weight += weight * order_line_obj.browse(cr,uid,move).product_uom_qty or 0.0
            self.write(cr,uid,sale.id,{'weight_package':total_weight})
        return True
    def _get_euro(self, cr, uid, context=None):
        try:
            return self.pool.get('res.currency').search(cr, uid, [('name','=','USD')])[0]
        except:
            return False



    _columns = {
#        'use_shipping' : fields.boolean('Use Shipping',readonly=True, states={'draft': [('readonly', False)]}),
#        'shipping_type' : fields.selection(_get_shipping_type,'Shipping Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'weight_package' : fields.float('Package Weight', digits_compute= dp.get_precision('Stock Weight'), help="Package weight which comes from weighinig machine in pounds",readonly=True, states={'draft': [('readonly', False)]}),
#        'service_type_usps' : fields.selection(_get_service_type_usps, 'Service Type', size=100,readonly=True, states={'draft': [('readonly', False)]}),
#        'first_class_mail_type_usps' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50,readonly=True, states={'draft': [('readonly', False)]}),
#        'container_usps' : fields.selection(_get_container_usps,'Container', size=100,readonly=True, states={'draft': [('readonly', False)]}),
#        'size_usps' : fields.selection(_get_size_usps,'Size',readonly=True, states={'draft': [('readonly', False)]}),
#        'width_usps' : fields.float('Width', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
#        'length_usps' : fields.float('Length', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
#        'height_usps' : fields.float('Height', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
#        'girth_usps' : fields.float('Girth', digits_compute= dp.get_precision('Stock Weight'),readonly=True, states={'draft': [('readonly', False)]}),
#        #'machinable_usps' : fields.boolean('Machinable', domain=[('service_type_usps', 'in', ('first_class','parcel','all','online')), '|', ('first_class_mail_type_usps', 'in', ('letter','flat'))]),
#        #'ship_date_usps' : fields.date('Ship Date', help="Date Package Will Be Mailed. Ship date may be today plus 0 to 3 days in advance."),
#        'dropoff_type_fedex' : fields.selection([
#                ('REGULAR_PICKUP','REGULAR PICKUP'),
#                ('REQUEST_COURIER','REQUEST COURIER'),
#                ('DROP_BOX','DROP BOX'),
#                ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
#                ('STATION','STATION'),
#            ],'Dropoff Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'service_type_fedex' : fields.selection([
#                ('EUROPE_FIRST_INTERNATIONAL_PRIORITY','EUROPE_FIRST_INTERNATIONAL_PRIORITY'),
#                ('FEDEX_1_DAY_FREIGHT','FEDEX_1_DAY_FREIGHT'),
#                ('FEDEX_2_DAY','FEDEX_2_DAY'),
#                ('FEDEX_2_DAY_FREIGHT','FEDEX_2_DAY_FREIGHT'),
#                ('FEDEX_3_DAY_FREIGHT','FEDEX_3_DAY_FREIGHT'),
#                ('FEDEX_EXPRESS_SAVER','FEDEX_EXPRESS_SAVER'),
#                ('STANDARD_OVERNIGHT','STANDARD_OVERNIGHT'),
#                ('PRIORITY_OVERNIGHT','PRIORITY_OVERNIGHT'),
#                ('FEDEX_GROUND','FEDEX_GROUND'),
#		('FIRST_OVERNIGHT','FIRST_OVERNIGHT'),
#		('GROUND_HOME_DELIVERY','GROUND_HOME_DELIVERY'),
#		('INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY'),
#		('INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_ECONOMY_FREIGHT'),
#		('INTERNATIONAL_FIRST','INTERNATIONAL_FIRST'),
#		('INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY'),
#		('INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_PRIORITY_FREIGHT'),
##		('SMART_POST','SMART_POST'),
##		('FEDEX_FREIGHT','FEDEX_FREIGHT'),
##		('FEDEX_NATIONAL_FREIGHT','FEDEX_NATIONAL_FREIGHT'),
#		('INTERNATIONAL_GROUND','INTERNATIONAL_GROUND'),
#           ],'Service Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'packaging_type_fedex' : fields.selection([
#                ('YOUR_PACKAGING','YOUR_PACKAGING'),
#                ('FEDEX_BOX','FEDEX BOX'),
#                ('FEDEX_PAK','FEDEX PAK'),
#                ('FEDEX_TUBE','FEDEX_TUBE'),
#                ('FEDEX_10KG_BOX','FEDEX 10KG BOX'),
#                ('FEDEX_25KG_BOX','FEDEX 25KG BOX'),
#                ('FEDEX_ENVELOPE','FEDEX ENVELOPE'),
#            ],'Packaging Type', help="What kind of package this will be shipped in",readonly=True, states={'draft': [('readonly', False)]}),
#        'package_detail_fedex' : fields.selection([
#                ('INDIVIDUAL_PACKAGES','INDIVIDUAL_PACKAGES'),
#                ('PACKAGE_GROUPS','PACKAGE_GROUPS'),
#                ('PACKAGE_SUMMARY','PACKAGE_SUMMARY'),
#            ],'Package Detail',readonly=True, states={'draft': [('readonly', False)]}),
#        'payment_type_fedex' : fields.selection([
#                ('RECIPIENT','RECIPIENT'),
#                ('SENDER','SENDER'),
#                ('THIRD_PARTY','THIRD_PARTY'),
#            ],'Payment Type', help="Who pays for the rate_request?",readonly=True, states={'draft': [('readonly', False)]}),
#        'physical_packaging_fedex' : fields.selection([
#                ('OTHER','OTHER'),
#                ('BAG','BAG'),
#                ('BARREL','BARREL'),
#                ('BOX','BOX'),
#                ('BUCKET','BUCKET'),
#                ('BUNDLE','BUNDLE'),
#                ('CARTON','CARTON'),
#                ('TANK','TANK'),
#                ('TUBE','TUBE'),
#                ('BASKET','BASKET'),
#                ('CASE','CASE'),
#                ('CONTAINER','CONTAINER'),
#                ('CRATE','CRATE'),
#                ('CYLINDER','CYLINDER'),
#                ('DRUM','DRUM'),
#                ('ENVELOPE','ENVELOPE'),
#                ('HAMPER','HAMPER'),
#                ('PAIL','PAIL'),
#                ('PALLET','PALLET'),
#                ('PIECE','PIECE'),
#                ('REEL','REEL'),
#                ('ROLL','ROLL'),
#                ('SKID','SKID'),
#                ('TANK','TANK'),
#            ],'Physical Packaging',readonly=True, states={'draft': [('readonly', False)]}),
#        'pickup_type_ups' : fields.selection([
#                ('01','Daily Pickup'),
#                ('03','Customer Counter'),
#                ('06','One Time Pickup'),
#                ('07','On Call Air'),
#                ('11','Suggested Retail Rates'),
#                ('19','Letter Center'),
#                ('20','Air Service Center'),
#            ],'Pickup Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'service_type_ups' : fields.selection([
#                ('01','Next Day Air'),
#                ('02','Second Day Air'),
#                ('03','Ground'),
#                ('07','Worldwide Express'),
#                ('08','Worldwide Expedited'),
#                ('11','Standard'),
#                ('12','Three-Day Select'),
#                ('13','Next Day Air Saver'),
#                ('14','Next Day Air Early AM'),
#                ('54','Worldwide Express Plus'),
#                ('59','Second Day Air AM'),
#                ('65','Saver'),
#            ],'Service Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'packaging_type_ups' : fields.selection([
#                ('00','Unknown'),
#                ('01','Letter'),
#                ('02','Package'),
#                ('03','Tube'),
#                ('04','Pack'),
#                ('21','Express Box'),
#                ('24','25Kg Box'),
#                ('25','10Kg Box'),
#                ('30','Pallet'),
#                ('2a','Small Express Box'),
#                ('2b','Medium Express Box'),
#                ('2c','Large Express Box'),
#            ],'Packaging Type',readonly=True, states={'draft': [('readonly', False)]}),
#        'shipping_label' : fields.binary('Logo',readonly=True, states={'draft': [('readonly', False)]}),
#        'shipping_rate': fields.float('Shipping Rate',readonly=True, states={'draft': [('readonly', False)]}),
##        'weight_package': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
#        'response_usps_ids' : fields.one2many('shipping.response','sale_order_id','Order Response',readonly=True, states={'draft': [('readonly', False)]}),
#        'tracking_ids' : fields.one2many('pack.track','picking_id','Tracking Details'),
#        #removed required from pack_width and pack_height and pack_length
#        'pack_length': fields.integer('Length', readonly=True, states={'draft': [('readonly', False)]}),
#        'pack_width': fields.integer('Width',readonly=True, states={'draft': [('readonly', False)]}),
#        'pack_height': fields.integer('Height',readonly=True, states={'draft': [('readonly', False)]}),
#        'services': fields.many2one('service.name', 'Services',readonly=True, states={'draft': [('readonly', False)]}),
##        'cana_weight': fields.float('Weight', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
#        'cana_length': fields.float('Length', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
#        'cana_width': fields.float('Width', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
#        'cana_height': fields.float('Height', digits=(16,2),readonly=True, states={'draft': [('readonly', False)]}),
#        'rates': fields.text('Rates', size=1000),
#         'invalid_addr': fields.boolean('Invalid Address',readonly=True),
        'tracking_no': fields.char('Tracking Number', size=64),
#        'journal_id': fields.many2one('account.journal', 'Journal',readonly=True),
##        'weight_unit':fields.selection([('LB','LBS'),('KG','KGS')],'WeightUnits',readonly=True, states={'draft': [('readonly', False)]}),
#        'customsvalue':fields.float('Amount',readonly=True, states={'draft': [('readonly', False)]}),
#        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True,states={'draft': [('readonly', False)]}),

    }

    _defaults = {
#        'use_shipping' : True,
##        'shipping_type' : 'All',
#        'service_type_usps' : 'All',
#        'container_usps':'Parcel',
#        'size_usps' : 'REGULAR',
#        'dropoff_type_fedex' : 'REGULAR_PICKUP',
#        'service_type_fedex' : 'FEDEX_GROUND',
#        'packaging_type_fedex' : 'YOUR_PACKAGING',
#        'package_detail_fedex' : 'INDIVIDUAL_PACKAGES',
#        'payment_type_fedex' : 'SENDER',
#        'physical_packaging_fedex' : 'BOX',
#        'pickup_type_ups' : '01',
#        'service_type_ups' : '03',
#        'packaging_type_ups' : '02',
##        'services' : 1,
#        'journal_id': _default_journal,
##        'carrier_tracking_ref' : '0',
##        'weight_unit':'LB',
#        'currency_id':_get_euro,

    }

    def _prepare_order_picking(self, cr, uid, order, context=None):        
        res=super(sale_order, self)._prepare_order_picking(cr, uid, order, context)
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
#        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        res.update( {
            'name': pick_name,
            'origin': order.name,
            'date': order.date_order,
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'address_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
            'carrier_id':order.carrier_id.id,
            'carrier_tracking_ref':order.tracking_no,
#            'use_shipping' : order.use_shipping,
#            'shipping_type' : order.shipping_type,
#            'weight_package' : order.weight_package,
#            'service_type_usps' : order.service_type_usps,
#            'first_class_mail_type_usps' : order.first_class_mail_type_usps,
#            'container_usps' : order.container_usps,
#            'size_usps' : order.size_usps,
#            'width_usps' : order.width_usps,
#            'length_usps' : order.length_usps,
#            'height_usps' : order.height_usps,
#            'girth_usps' : order.girth_usps,
#            'shipping_rate':order.shipping_rate,
#            'shipping_label':order.shipping_label,
#            'services' : order.services.id,
##            'cana_weight' : order.cana_weight,
#            'cana_length' : order.cana_length,
#            'cana_width' : order.cana_width,
#            'cana_height' : order.cana_height,
#            'dropoff_type_fedex' : order.dropoff_type_fedex,
#            'service_type_fedex' : order.service_type_fedex,
#            'packaging_type_fedex' : order.packaging_type_fedex,
#            'package_detail_fedex' : order.package_detail_fedex,
#            'payment_type_fedex' : order.payment_type_fedex,
#            'physical_packaging_fedex' : order.physical_packaging_fedex,
#            'pack_length' : order.pack_length,
#            'pack_height' : order.pack_height,
#            'pack_width' : order.pack_width,
#            'rates' : order.rates,
#            'pickup_type_ups' : order.pickup_type_ups,
#            'service_type_ups' : order.service_type_ups,
#            'packaging_type_ups' : order.packaging_type_ups,
#            'customsvalue' : order.customsvalue,
#            'response_usps_ids': [(6,0,self.prepare_shipping_response(cr, uid, order, context=context))]
        })                
        return res
    
    def onchange_shipping_rates(self, cr, uid, ids, service_type,response_usps_ids,shipping_type,context=None):
#        width = self.browse(cr,uid,ids[0]).pack_width
        width = 0
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
            
	vals = {'response_usps_ids' : delete_att_vals,
                'pack_length' : width,
                'pack_width' : width,
                'pack_height' : width,
                'carrier_tracking_ref': '',
                'carrier_id':carrier_ids and carrier_ids[0] or ''
                }
        return {'value':vals}


sale_order()

#class sale_shop(osv.osv):
#  _inherit = "sale.shop"
#
#  _columns = {
#      'suffix': fields.char('Suffix', size=64),
#      'cust_address': fields.many2one('res.partner', 'Address'),
#
#  }
#
#sale_shop()


class shipping_response(osv.osv):
    _name = 'shipping.response'
    _inherit = "shipping.response"

    def generate_tracking_sale(self, cr, uid, ids, context={}, error=True):
        import os; _logger.info("server name: %s", os.uname()[1])
        try:
            saleorder_obj = self.pool.get('sale.order')
            stockmove_obj = self.pool.get('stock.move')
            stockpicking_obj = self.pool.get('stock.picking')
            shippingresp_lnk = self.browse(cr,uid,ids[0])
            #Notice :- This is only for sale order
#            type = shippingresp_lnk.picking_id.type
            type='out'
#            move_ids = stockmove_obj.search(cr,uid,[('picking_id','=',shippingresp_lnk.picking_id.id)])
#
#            move_lines = stockmove_obj.browse(cr,uid,move_ids)
#            for move_line in move_lines:
#                real_stock  = move_line.product_id.qty_available
#                print "real_stock: ",real_stock
#                res = self.pool.get('stock.location')._product_reserve(cr, uid, [move_line.location_id.id], move_line.product_id.id, move_line.product_qty, {'uom': move_line.product_uom.id}, lock=True)
    #            if not res:
    #                saleorder_obj.write(cr,uid,shippingresp_lnk.picking_id.sale_id.id,{'state':'shipping_except'})
    #                if error:
    #                    raise osv.except_osv(_('Error'), _('Not enough stock in inventory'))
    #                return False

            ### Shipper
            ### based on stock.pickings type
            if type == 'out':
                cust_address = shippingresp_lnk.sale_order_id.shop_id.cust_address
            elif type == 'in':
                cust_address = shippingresp_lnk.sale_order_id.partner_shipping_id
            if not cust_address:
                if error:
                    raise osv.except_osv(_('Error'), _('Shop Address not defined!'),)
                else:
                    return False

            if not (cust_address.name or cust_address.partner_id.name):
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper Name."))
            if not cust_address.street:
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper Street."))
            if not cust_address.city:
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper City."))
            if not cust_address.state_id.code:
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper State Code."))
            if not cust_address.zip:
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper Zip."))
            if not cust_address.country_id.code:
                raise osv.except_osv(_('Warning !'),_("You must enter Shipper Country."))
#            if not cust_address.email:
#                raise osv.except_osv(_('Warning !'),_("You must enter Shipper email."))

            shipper = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)


            ### Recipient
            if type == 'out':
                cust_address = shippingresp_lnk.sale_order_id.partner_shipping_id
            elif type == 'in':
                cust_address = shippingresp_lnk.sale_order_id.shop_id.cust_address
            if not cust_address:
                if error:
                    raise osv.except_osv(_('Error'), _('Shipper Address not defined!'),)
                else:
                    return False


            if not (cust_address.name or cust_address.partner_id.name):
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Name."))
#            if not cust_address.street:
#                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Street."))
#            if not cust_address.city:
#                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient City."))
#            if not cust_address.state_id.code:
#                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient State Code."))
            if not cust_address.zip:
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Zip."))
            if not cust_address.country_id.code:
                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient Country."))
#            if not cust_address.email:
#                raise osv.except_osv(_('Warning !'),_("You must enter Reciepient email."))
            receipient = Address(cust_address.name or cust_address.partner_id.name, cust_address.street, cust_address.city, cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code, cust_address.street2 or '', cust_address.phone or '', cust_address.email, cust_address.partner_id.name)
            weight = shippingresp_lnk.weight
            rate = shippingresp_lnk.rate

            if shippingresp_lnk.type.lower() == 'usps' and not ('usps_active' in context.keys()):
                usps_info = self.pool.get('shipping.usps').get_usps_info(cr,uid,context)
                usps = shippingservice.USPSDeliveryConfirmationRequest(usps_info, shippingresp_lnk.name,weight,shipper,receipient)
                usps_response = usps.send()
                context['attach_id'] = saleorder_obj.create_attachment(cr,uid,[shippingresp_lnk.sale_order_id.id],usps_response,context)
                saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'carrier_tracking_ref':usps_response.tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(usps_response.graphic_image))), 'shipping_rate': rate})
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

                # This is the object that will be handling our tracking request.
                # We're using the FedexConfig object from example_config.py in this dir.
                shipment = FedexProcessShipmentRequest(CONFIG_OBJ)

                # This is very generalized, top-level information.
                # REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER or STATION
    #            print "DROPOFF TYPE: ",shippingresp_lnk.dropoff_type_fedex
                fedex_servicedetails = saleorder_obj.browse(cr,uid,shippingresp_lnk.sale_order_id.id)

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

#                if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
#                    shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType ='SENDER'
#                    shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.AccountNumber =shippingfedex_ptr.account_no
#                    shipment.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor.CountryCode =shipper.country_code
#                    shipment.RequestedShipment.CustomsClearanceDetail.DocumentContent ='NON_DOCUMENTS'
#
#                    shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount =fedex_servicedetails.customsvalue
#                    shipment.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency =fedex_servicedetails.currency_id.name
#
#                    commodities_obj=shipment.create_wsdl_object_of_type('Commodity')
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

                _logger.info("Freight Shipment Detail %s", shipment.RequestedShipment.FreightShipmentDetail)
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
                package1_weight.Value = fedex_servicedetails.weight_package or fedex_servicedetails.weight #1.0
#                package1_weight.Units = fedex_servicedetails.weight_unit
                package1_weight.Units = 'KG'

                package1 = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                package1.Weight = package1_weight
#                if fedex_servicedetails.fedex_dimension:
                package1_dimension = shipment.create_wsdl_object_of_type('Dimensions')
                package1_dimension.Length=fedex_servicedetails.pack_length
                package1_dimension.Width=fedex_servicedetails.pack_width
                package1_dimension.Height=fedex_servicedetails.pack_height
                package1_dimension.Units='IN'
                package1.Dimensions=package1_dimension
                # Un-comment this to see the other variables you may set on a package.
                #print package1

                # This adds the RequestedPackageLineItem WSDL object to the shipment. It
                # increments the package count and total weight of the shipment for you.
                shipment.add_package(package1)

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
#                        if e.reason:#.strerror == 'Name or service not known':
#                            if e.reason.strerror == 'Name or service not known':
#                                errormessage = "Connection Error: Please check your internet connection!"
#                        else:
                        errormessage = e
                        raise osv.except_osv(_('Error'), _('%s' % (errormessage,)))

                # This will show the reply to your shipment being sent. You can access the
                # attributes through the response attribute on the request object. This is
                # good to un-comment to see the variables returned by the Fedex reply.
                #print shipment.response

                # Here is the overall end result of the query.
                # Getting the tracking number from the new shipment.
                fedexTrackingNumber = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                # Net shipping costs.
                if fedex_servicedetails.service_type_fedex in ['INTERNATIONAL_ECONOMY','INTERNATIONAL_ECONOMY_FREIGHT','INTERNATIONAL_FIRST','INTERNATIONAL_PRIORITY','INTERNATIONAL_PRIORITY_FREIGHT','INTERNATIONAL_GROUND','EUROPE_FIRST_INTERNATIONAL_PRIORITY']:
                    fedexshippingrate = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount
                else:
                    fedexshippingrate = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount

                # Get the label image in ASCII format from the reply. Note the list indices
                # we're using. You'll need to adjust or iterate through these if your shipment
                # has multiple packages.
                ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
#                print"ascii_label_data",ascii_label_data
                # Convert the ASCII data to binary.
    #            label_binary_data = binascii.a2b_base64(ascii_label_data)
    #            print"LABEL: ",label_binary_data
                """
                #This is an example of how to dump a label to a PNG file.
                """
                # This will be the file we write the label out to.
    #            png_file = open('example_shipment_label.png', 'wb')
    #            png_file.write(b64decode(label_binary_data))
    #            png_file.close()


                fedex_attachment_pool = self.pool.get('ir.attachment')
                fedex_data_attach = {
                    'name': 'ShippingLabel.png',
                    'datas': binascii.b2a_base64(str(b64decode(ascii_label_data))),
                    'description': 'Packing List',
                    'res_name': shippingresp_lnk.sale_order_id.name,
                    'res_model': 'sale.order',
                    'res_id': shippingresp_lnk.sale_order_id.id,
                }

                fedex_attach_id = fedex_attachment_pool.search(cr,uid,[('res_id','=',shippingresp_lnk.sale_order_id.id),('res_name','=',shippingresp_lnk.sale_order_id.name)])
                if not fedex_attach_id:
                    fedex_attach_id = fedex_attachment_pool.create(cr, uid, fedex_data_attach)
                else:
                    fedex_attach_result = fedex_attachment_pool.write(cr, uid, fedex_attach_id, fedex_data_attach)
                    fedex_attach_id = fedex_attach_id[0]

                context['attach_id'] = fedex_attach_id
                context['tracking_no'] = fedexTrackingNumber
                """
                #This is an example of how to print the label to a serial printer. This will not
                #work for all label printers, consult your printer's documentation for more
                #details on what formats it can accept.
                """
                # Pipe the binary directly to the label printer. Works under Linux
                # without requiring PySerial. This WILL NOT work on other platforms.
                #label_printer = open("/dev/ttyS0", "w")
                #label_printer.write(label_binary_data)
                #label_printer.close()

                """
                #This is a potential cross-platform solution using pySerial. This has not been
                #tested in a long time and may or may not work. For Windows, Mac, and other
                #platforms, you may want to go this route.
                """
                #import serial
                #label_printer = serial.Serial(0)
                #print "SELECTED SERIAL PORT: "+ label_printer.portstr
                #label_printer.write(label_binary_data)
                #label_printer.close()
    #
    #            if shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber:
    #                track_success = True
                if fedexTrackingNumber:
                    stockpickingwrite_result = saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'carrier_tracking_ref':fedexTrackingNumber, 'shipping_label':binascii.b2a_base64(str(b64decode(ascii_label_data))), 'shipping_rate': fedexshippingrate})
                    context['track_success'] = True
            elif shippingresp_lnk.type.lower() == 'ups':
                ups_info = self.pool.get('shipping.ups').get_ups_info(cr,uid,context)
                stockpicking_obj = self.pool.get('stock.picking')
                pickup_type_ups = shippingresp_lnk.sale_order_id.pickup_type_ups
                service_type_ups = shippingresp_lnk.sale_order_id.service_type_ups
                packaging_type_ups = shippingresp_lnk.sale_order_id.packaging_type_ups
                ups = shippingservice.UPSShipmentConfirmRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper, receipient)
                ups_response = ups.send()
                ups = shippingservice.UPSShipmentAcceptRequest(ups_info, ups_response.shipment_digest)
                ups_response = ups.send()
                context['attach_id'] = saleorder_obj.create_attachment(cr,uid,[shippingresp_lnk.sale_order_id.id],ups_response,context)
                saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'carrier_tracking_ref':ups_response.tracking_number, 'shipping_label':binascii.b2a_base64(str(b64decode(ups_response.graphic_image))), 'shipping_rate': rate})
                context['track_success'] = True
                context['tracking_no'] = ups_response.tracking_number
        except Exception, exc:
                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))
        ### Check Availability; Confirm; Validate : Automate Process Now step
        if context.get('track_success',False):
            ### Assign Carrier to Delivery carrier if user has not chosen
            type_fieldname = ''
            if shippingresp_lnk.type.lower() == 'usps':
                type_fieldname = 'is_usps'
            elif shippingresp_lnk.type.lower() == 'ups':
                type_fieldname = 'is_ups'
            elif shippingresp_lnk.type.lower() == 'fedex':
                type_fieldname = 'is_fedex'
            carrier_ids = self.pool.get('delivery.carrier').search(cr,uid,[('service_output','=',shippingresp_lnk.name),(type_fieldname,'=',True)])
            if not carrier_ids:
                if error:
                    raise osv.except_osv(_('Error'), _('Shipping service output settings not defined'))
                return False
            saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'carrier_id':carrier_ids[0]})
            saleorder_obj.write(cr,uid,shippingresp_lnk.sale_order_id.id,{'tracking_no':context['tracking_no'], 'carrier_id':carrier_ids[0]})

            ### Write this shipping response is selected
            self.write(cr,uid,ids[0],{'selected':True})

            if context.get('batch_printing',False):
                return True
            return True
        else:
            return False

shipping_response()

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




