# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
import re
import math
import urllib
from urllib2 import Request, urlopen, URLError, quote
import xml.etree.ElementTree as etree
from xml.dom.minidom import parse, parseString
from openerp.osv import fields, osv
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

ups_service_type = {
    '01': 'Next Day Air',
    'ups_1DA': 'Next Day Air',
    '02': 'Second Day Air',
    'ups_2DA': 'Second Day Air',
    '03': 'Ground',
    'ups_GND': 'Ground',
    '07': 'Worldwide Express',
    '08': 'Worldwide Expedited',
    '11': 'Standard',
    '12': 'Three-Day Select',
    'ups_3DS': 'Three-Day Select',
    '13': 'Next Day Air Saver',
    'ups_1DP': 'Next Day Air Saver',
    '14': 'Next Day Air Early AM',
    'ups_1DM': 'Next Day Air Early AM',
    '54': 'Worldwide Express Plus',
    '59': 'Second Day Air AM',
    '65': 'Saver',
}

class Error(object):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        _logger.info("%s", self.message)
        raise

class Shipping(object):
    def __init__(self, weight, shipper,receipient):
        self.weight = weight
        self.shipper = shipper
        self.receipient = receipient

class UPSShipping(Shipping):
    def __init__(self, weight, shipper,receipient):
        super(UPSShipping, self).__init__(weight,shipper,receipient)

    def send(self,):
        datas = self._get_data()
        data = datas[0]
        api_url = datas[1]
        try:
            request = Request(api_url, data)
            response_text = urlopen(request).read()
            _logger.info("ups response_text: %s", response_text)
            response = self.__parse_response(response_text)
        except URLError, e:
            if hasattr(e, 'reason'):
                _logger.exception("Could not reach the server, reason: %s", e.reason)
            elif hasattr(e, 'code'):
                _logger.exception("Could not fulfill the request, code: %d", e.code)
            raise
        return response

    def __parse_response(self, response_text):
        root = etree.fromstring(response_text)
        status_code = root.findtext('Response/ResponseStatusCode')
        if status_code != '1':
            raise Exception('UPS: %s' % (root.findtext('Response/Error/ErrorDescription')))
        else:
            response = self._parse_response_body(root)
        return response

class UPSRateRequest(UPSShipping):

    def __init__(self, ups_info, pickup_type_ups, service_type_ups, packaging_type_ups, weight, shipper,receipient, cust_default, sys_default):
        self.type = 'UPS'
        self.ups_info = ups_info
        self.pickup_type_ups = pickup_type_ups
        self.service_type_ups = service_type_ups
        self.packaging_type_ups = packaging_type_ups
        self.cust_default = cust_default
        self.sys_default = sys_default
        super(UPSRateRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []
        data.append("""<?xml version=\"1.0\"?>
        <AccessRequest xml:lang=\"en-US\">
            <AccessLicenseNumber>%s</AccessLicenseNumber>
            <UserId>%s</UserId>
            <Password>%s</Password>
        </AccessRequest>
        <?xml version=\"1.0\"?>
        <RatingServiceSelectionRequest xml:lang=\"en-US\">
            <Request>
                <TransactionReference>
                    <CustomerContext>Rating and Service</CustomerContext>
                    <XpciVersion>1.0001</XpciVersion>
                </TransactionReference>
                <RequestAction>Rate</RequestAction>
                <RequestOption>Rate</RequestOption>
            </Request>
        <PickupType>
            <Code>%s</Code>
        </PickupType>
        <Shipment>
            <Shipper>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                </Address>
            <ShipperNumber>%s</ShipperNumber>
            </Shipper>
            <ShipTo>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                <ResidentialAddressIndicator/>
                </Address>
            </ShipTo>
            <ShipFrom>
                <Address>
                    <PostalCode>%s</PostalCode>
                    <CountryCode>%s</CountryCode>
                </Address>
            </ShipFrom>
            <Service>
                <Code>%s</Code>
            </Service>
            <Package>
                <PackagingType>
                    <Code>%s</Code>
                </PackagingType>
                <PackageWeight>
                    <UnitOfMeasurement>
                        <Code>LBS</Code>
                    </UnitOfMeasurement>
                    <Weight>%s</Weight>
                </PackageWeight>
            </Package>
        </Shipment>
        </RatingServiceSelectionRequest>""" % (self.ups_info.access_license_no,self.ups_info.user_id,self.ups_info.password,self.pickup_type_ups,self.shipper.zip,self.shipper.country_code,self.ups_info.shipper_no,self.receipient.zip,self.receipient.country_code,self.shipper.zip,self.shipper.country_code,self.service_type_ups,self.packaging_type_ups,self.weight))
        data.append('https://wwwcie.ups.com/ups.app/xml/Rate' if self.ups_info.test else 'https://onlinetools.ups.com/ups.app/xml/Rate')
        _logger.info("Response data %s", data)
        return data

    def _parse_response_body(self, root):
        return UPSRateResponse(root, self.weight, self.cust_default, self.sys_default)


class UPSRateResponse(object):
    def __init__(self, root, weight, cust_default, sys_default):
        self.root = root
        self.type = 'UPS'
        mail_service = ups_service_type[root.findtext('RatedShipment/Service/Code')]
        sr_no = 1 if cust_default and cust_default.split('/')[0] == self.type and cust_default.split('/')[1] == mail_service else 9
        sr_no = 2 if sr_no == 9 and sys_default and sys_default.split('/')[0] == self.type and sys_default.split('/')[1] == mail_service else sr_no
        self.postage = [{'Rate': root.findtext('RatedShipment/TotalCharges/MonetaryValue'), 'Service': mail_service, 'sr_no': sr_no}]
        self.weight = weight

    def __repr__(self):
        return (self.service_type, self.rate, self.weight, self.sr_no)
        

class UPSShipmentConfirmRequest(UPSShipping):
    def __init__(self, ups_info, pickup_type_ups, service_type_ups, packaging_type_ups,weight, shipper,receipient,length_merge,width_merge,height_merge,pack_weight_merge=None):
        self.type = 'UPS'
        self.ups_info = ups_info
        self.pickup_type_ups = pickup_type_ups
        self.service_type_ups = service_type_ups
        self.packaging_type_ups = packaging_type_ups
        self.length_ups = length_merge
        self.width_ups = width_merge
        self.height_ups = height_merge
        self.pack_weight_merge = pack_weight_merge
        super(UPSShipmentConfirmRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []
        package_data=''
        pack_weight_merge=[]
        dim_len=len(self.length_ups)
        for each_pack in self.pack_weight_merge:
            pack_weight_merge.append(self.pack_weight_merge[each_pack])
        for i in range(0,dim_len):
            length_ups=self.length_ups[i]
            width_ups=self.width_ups[i]
            height_ups=self.height_ups[i]
            weight=pack_weight_merge[i]
            package_data += """<Package>
                        <PackagingType>
                            <Code>%s</Code>
                        </PackagingType>
                        <PackageWeight>
                            <Weight>%s</Weight>
                        </PackageWeight>
                        <Dimensions>
                            <UnitOfMeasurement>
                                <Code>IN</Code>
                            </UnitOfMeasurement>
                                <Length>%s</Length>
                                <Width>%s</Width>
                                <Height>%s</Height>
                        </Dimensions>
                    </Package>""" % (self.packaging_type_ups, weight, length_ups, width_ups, height_ups)########3(self.packaging_type_ups, weight, length_ups, width_ups, height_ups, self.ref1,self.ref2)


        xml_data="""<?xml version="1.0" ?>
            <AccessRequest xml:lang='en-US'>
                <AccessLicenseNumber>%s</AccessLicenseNumber>
                <UserId>%s</UserId>
                <Password>%s</Password>
            </AccessRequest>
            <?xml version="1.0" ?>
            <ShipmentConfirmRequest>
                <Request>
                     <TransactionReference>
                          <CustomerContext>guidlikesubstance</CustomerContext>
                          <XpciVersion>1.0001</XpciVersion>
                     </TransactionReference>
                     <RequestAction>ShipConfirm</RequestAction>
                     <RequestOption>nonvalidate</RequestOption>
                </Request>
                <Shipment>
                     <Shipper>
                  <Name>%s</Name>
                  <AttentionName>%s</AttentionName>
                  <PhoneNumber>%s</PhoneNumber>
                  <ShipperNumber>%s</ShipperNumber>
                  <Address>
                       <AddressLine1>%s</AddressLine1>
                       <AddressLine2>%s</AddressLine2>
                       <City>%s</City>
                       <StateProvinceCode>%s</StateProvinceCode>
                       <CountryCode>%s</CountryCode>
                       <PostalCode>%s</PostalCode>
                  </Address>
             </Shipper>
             <ShipTo>
                  <CompanyName>%s</CompanyName>
                  <AttentionName>%s</AttentionName>
                  <PhoneNumber>%s</PhoneNumber>
                  <Address>
                       <AddressLine2>%s</AddressLine2>
                       <AddressLine1>%s</AddressLine1>
                       <City>%s</City>
                       <StateProvinceCode>%s</StateProvinceCode>
                       <CountryCode>%s</CountryCode>
                       <PostalCode>%s</PostalCode>
                       <ResidentialAddress />
                  </Address>
             </ShipTo>
             <Service>
                  <Code>%s</Code>
                  <Description>%s</Description>
             </Service>
             <PaymentInformation>
                    <Prepaid>
                    <BillShipper>
                         <CreditCard>
                             <Type>06</Type>
                             <Number>4111111111111111</Number>
                             <ExpirationDate>121999</ExpirationDate>
                         </CreditCard>
                    </BillShipper>
                </Prepaid>
             </PaymentInformation>"""% (self.ups_info.access_license_no,self.ups_info.user_id,self.ups_info.password, self.shipper.company_name, self.shipper.name, self.shipper.phone, self.ups_info.shipper_no, self.shipper.address1,self.shipper.address2, self.shipper.city, self.shipper.state_code, self.shipper.country_code, self.shipper.zip, self.receipient.company_name, self.receipient.name, self.receipient.phone, self.receipient.address2, self.receipient.address1,self.receipient.city, self.receipient.state_code, self.receipient.country_code, self.receipient.zip, self.service_type_ups, ups_service_type[self.service_type_ups])
        label_data= """
            </Shipment>
            <LabelSpecification>
                <LabelPrintMethod>
                    <Code>GIF</Code>
                </LabelPrintMethod>
                <LabelImageFormat>
                    <Code>GIF</Code>
                </LabelImageFormat>
            </LabelSpecification>
        </ShipmentConfirmRequest>"""
        shipment_data=xml_data+package_data+label_data
        _logger.info("Shipment data: %s", shipment_data)
        data.append(shipment_data)
        
        data.append('https://wwwcie.ups.com/ups.app/xml/ShipConfirm' if self.ups_info.test else 'https://onlinetools.ups.com/ups.app/xml/ShipConfirm')
        _logger.info("data: %s", data)
        return data

    def _parse_response_body(self, root):
        return UPSShipmentConfirmResponse(root)
        

class UPSShipmentConfirmResponse(object):
    def __init__(self, root):
        self.root = root
        self.shipment_digest = root.findtext('ShipmentDigest')

    def __repr__(self):
        return (self.shipment_digest)

class UPSShipmentAcceptRequest(UPSShipping):
    def __init__(self, ups_info, shipment_digest):
        self.ups_info = ups_info
        self.shipment_digest = shipment_digest

    def _get_data(self):
        data = []
        data.append("""
<?xml version="1.0" ?>
<AccessRequest xml:lang='en-US'>
    <AccessLicenseNumber>%s</AccessLicenseNumber>
    <UserId>%s</UserId>
    <Password>%s</Password>
</AccessRequest>
<?xml version="1.0" ?>
<ShipmentAcceptRequest>
    <Request>
        <RequestAction>ShipAccept</RequestAction>
    </Request>
    <ShipmentDigest>%s</ShipmentDigest>
</ShipmentAcceptRequest>""" % (self.ups_info.access_license_no,self.ups_info.user_id,self.ups_info.password,self.shipment_digest))
        data.append('https://wwwcie.ups.com/ups.app/xml/ShipAccept' if self.ups_info.test else 'https://onlinetools.ups.com/ups.app/xml/ShipAccept')
        return data

    def _parse_response_body(self, root):
        return UPSShipmentAcceptResponse(root)

class UPSShipmentAcceptResponse(object):
    def __init__(self, root):
        self.root = root
        tracking_number_list =[]
        graphic_image_list=[]
        image=[]
        html_image_list=[]
        iter_array=root.getiterator('PackageResults')
        for i in iter_array:
            children = i.getchildren()
            tracking = children[0]
            image = children[2]
            tracking_number_list.append(tracking.text)
            graphic_image_list.append(image.getchildren()[1].text)
            html_image_list.append(image.getchildren()[2].text)
        image_format_list = root.findtext('ShipmentResults/PackageResults/LabelImage/LabelImageFormat/Code')
        self.image_format  = image_format_list
        self.tracking_number = tracking_number_list
        self.graphic_image = graphic_image_list
        self.html_image = html_image_list
        self.package_count = len(iter_array)

    def __repr__(self):
        return (self.tracking_number, self.image_format, self.graphic_image)

class USPSShipping(Shipping):
    def __init__(self, weight, shipper,receipient):
        super(USPSShipping, self).__init__(weight,shipper,receipient)

    def send(self,):
        datas = self._get_data()
        data = datas[0]
        api_url = datas[1]
        values = {}
        values['XML'] = data
        api_url = api_url + urllib.urlencode(values)
        try:
            request = urlopen(api_url)
            response_text = request.read()
            response = self.__parse_response(response_text)
        except URLError, e:
            if hasattr(e, 'reason'):
                _logger.exception("Could not reach the server, reason: %s", e.reason)
            elif hasattr(e, 'code'):
                _logger.exception("Could not fulfill the request, code: %d", e.code)
            raise
        return response

    def __parse_response(self, response_text):
        responseDOM = parseString(response_text)
        root = etree.fromstring(response_text)
        desc_error = ''
        for each in  responseDOM.getElementsByTagName('Error'):
            descp = each.getElementsByTagName('Description')[0].toxml()
            descData=descp.replace('<Description>','').replace('</Description>','')
            desc_error +=descData+' '
            raise Exception('USPS %s' % (desc_error))
        response = self._parse_response_body(root)
        return response

class USPSRateRequest(USPSShipping):
    def __init__(self, usps_info, service_type_usps, first_class_mail_type_usps, container_usps, size_usps, width_usps, length_usps, height_usps, girth_usps, weight, shipper, receipient, cust_default=False, sys_default=False):
        self.type = 'USPS'
        self.usps_info = usps_info
        self.service_type_usps = service_type_usps
        self.first_class_mail_type_usps = first_class_mail_type_usps
        self.container_usps = container_usps
        self.size_usps = size_usps
        self.width_usps = width_usps
        self.length_usps = length_usps
        self.height_usps = height_usps
        self.girth_usps = girth_usps
        self.cust_default = cust_default
        self.sys_default = sys_default
        super(USPSRateRequest, self).__init__(weight,shipper,receipient)

    def _get_data(self):
        data = []

        service_type = '<Service>' + self.service_type_usps + '</Service>'

        if self.service_type_usps == 'First Class':
            service_type += '<FirstClassMailType>' + self.first_class_mail_type_usps + '</FirstClassMailType>'

        weight = math.modf(self.weight)
        pounds = int(weight[1])
        ounces = round(weight[0],2) * 16

        container = self.container_usps and '<Container>' + self.container_usps + '</Container>' or '<Container/>'

        size = '<Size>' + str(self.size_usps) + '</Size>'
        if self.size_usps == 'LARGE':
            size += '<Width>' + str(self.width_usps) + '</Width>'
            size += '<Length>' + str(self.length_usps) + '</Length>'
            size += '<Height>' + str(self.height_usps) + '</Height>'

#            if stockpicking_lnk.container_usps == 'Non-Rectangular' or stockpicking_lnk.container_usps == 'Variable' or stockpicking_lnk.container_usps == '':
            if self.container_usps == 'Non-Rectangular' or self.container_usps == 'Variable' or self.container_usps == '':
                size += '<Girth>' + str(self.girth_usps) + '</Girth>'

        data.append('<RateV4Request USERID="' + self.usps_info.user_id + '"><Revision/><Package ID="1ST">' + service_type + '<ZipOrigination>' + self.shipper.zip + '</ZipOrigination><ZipDestination>' + self.receipient.zip + '</ZipDestination><Pounds>' + str(pounds) + '</Pounds><Ounces>' + str(ounces) + '</Ounces>' + container + size + '<Machinable>true</Machinable></Package></RateV4Request>')
            
        data.append("http://production.shippingapis.com/ShippingAPI.dll?API=RateV4&")
        return data

    def _parse_response_body(self, root):
        return USPSRateResponse(root, self.weight, self.cust_default, self.sys_default)
    
class USPSRateResponse(object):
    def __init__(self, root, weight, cust_default, sys_default):
        self.root = root
        self.type = 'USPS'
        self.postage = []
        self.service_type = []
        postages = root.findall("Package/Postage")
        cust_default = "USPS/Priority Mail"
        for postage in postages:
            mail_service = postage.findtext('MailService').replace("&lt;sup&gt;&amp;reg;&lt;/sup&gt;","")
            sr_no = 1 if cust_default and cust_default.split('/')[0] == self.type and cust_default.split('/')[1] == mail_service else 9
            sr_no = 2 if sr_no == 9 and sys_default and sys_default.split('/')[0] == self.type and sys_default.split('/')[1] == mail_service else sr_no
            self.postage.append({'Rate':postage.findtext('Rate'), 'Service':mail_service, 'sr_no': sr_no})

        self.weight = weight

    def __repr__(self):
        return (self.service_type, self.rate, self.weight, self.sr_no)

class USPSDeliveryConfirmationRequest(USPSShipping):
    def __init__(self, usps_info, service_type_usps, weight, shipper, receipient):
        self.usps_info = usps_info
        self.service_type_usps = service_type_usps
        super(USPSDeliveryConfirmationRequest, self).__init__(weight,shipper,receipient)

    def _get_usps_servicename(self, service):
            if 'First-Class' in service:
                return 'First Class'
            elif 'Express Mail' in service:
                return 'Express Mail'
            elif 'Priority Mail' in service:
                return 'Priority Mail'
            elif 'Library Mail' in service:
                return 'Library Mail'
            elif 'Parcel Post' in service:
                return 'Parcel Post'
            elif 'Media Mail' in service:
                return 'Media Mail'

    def _get_data(self):
        data = []
        data.append('<DeliveryConfirmationV3.0Request USERID="' + self.usps_info.user_id + '"><Option>1</Option><ImageParameters></ImageParameters><FromName>' + self.shipper.name + '</FromName><FromFirm>' + self.shipper.company_name + '</FromFirm><FromAddress1>' + self.shipper.address2 + '</FromAddress1><FromAddress2>' + self.shipper.address1 + '</FromAddress2><FromCity>' + self.shipper.city + '</FromCity><FromState>' + self.shipper.state_code + '</FromState><FromZip5>' + self.shipper.zip + '</FromZip5><FromZip4></FromZip4><ToName>' + self.receipient.name + '</ToName><ToFirm>' + self.receipient.company_name + '</ToFirm><ToAddress1>' + self.receipient.address2 + '</ToAddress1><ToAddress2>' + self.receipient.address1 + '</ToAddress2><ToCity>' + self.receipient.city + '</ToCity><ToState>' + self.receipient.state_code + '</ToState><ToZip5>' + self.receipient.zip + '</ToZip5><ToZip4></ToZip4><WeightInOunces>' + str(self.weight*16) + '</WeightInOunces><ServiceType>' + self._get_usps_servicename(self.service_type_usps) + '</ServiceType><SeparateReceiptPage>TRUE</SeparateReceiptPage><POZipCode></POZipCode><ImageType>TIF</ImageType><LabelDate></LabelDate><CustomerRefNo></CustomerRefNo><AddressServiceRequested></AddressServiceRequested><SenderName></SenderName><SenderEMail></SenderEMail><RecipientName></RecipientName><RecipientEMail></RecipientEMail></DeliveryConfirmationV3.0Request>')
        data.append("https://testing.shippingapis.com/ShippingAPITest.dll?API=DeliveryConfirmationV3&" if self.usps_info.test else "https://secure.shippingapis.com/ShippingAPI.dll?API=DeliveryConfirmationV3&")
        return data

    def _parse_response_body(self, root):
        return USPSDeliveryConfirmationResponse(root)

class USPSDeliveryConfirmationResponse(object):
    def __init__(self, root):
        self.root = root
        self.tracking_number = root.findtext('DeliveryConfirmationNumber')
        self.image_format = 'TIF'
        self.graphic_image = root.findtext('DeliveryConfirmationLabel')

    def __repr__(self):
        return (self.tracking_number, self.image_format, self.graphic_image)