# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from fedex.config import FedexConfig
from fedex.services.track_service import FedexTrackRequest

class track_shipping(osv.osv_memory):
    _name = "track.shipping"
    _columns={
    'tracking_number': fields.char('Tracking Number', size=256),
    'response_message':fields.text('Tracking Response')
    }
    def default_get(self, cr, uid, fields, context=None):
        res={}
        print "Context",context
        active_id,active_model=context.get('active_id'),context.get('active_model')
        if active_model=='stock.picking':
            tracking_number=self.pool.get(active_model).browse(cr,uid,active_id).carrier_tracking_ref
            if tracking_number:
                res['tracking_number']=tracking_number
            else:
                raise osv.except_osv(_("Warning"), _("Tracking Number is not generated for this Delivery Order"))
        return res
#        res={}
#        if context.get('invoice_ids',False):
#            invoice_ids=context.get('invoice_ids')
#            res.update({'invoice_ids':invoice_ids})
        return res

    def track_service(self,cr,uid,ids,context={}):
        print "ids",ids
        tracking_obj=self.browse(cr,uid,ids[0])
        tracking_number=tracking_obj.tracking_number
        print "tracking_number",tracking_number
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
        #Create an object of FedEx traking
        track = FedexTrackRequest(CONFIG_OBJ)
        track.TrackPackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
#        track.TrackPackageIdentifier.Value = '798114182456'

        track.TrackPackageIdentifier.Value = tracking_number

        try:
            track.send_request()
#            print track.response()
        except Exception, e:
            raise osv.except_osv(_('Error'), _('%s' % (e,)))
        message=''
        for match in track.response.TrackDetails:
            print "track.response.TrackDetails",match.Notification.Severity
            if match.Notification.Severity=='SUCCESS':
                message+='Tracking #: '+match.TrackingNumber+'\n'
                message+='StatusDescription: '+match.StatusDescription+'\n'
                message+='StatusCode: '+match.StatusCode+'\n'
                message+='ServiceInfo: '+match.ServiceInfo+'\n'
                message+='PackageWeight: '+str(match.PackageWeight.Value)+' '+str(match.PackageWeight.Units)+'\n'
                message+='Packaging: '+match.Packaging+'\n'
    #            message+='TotalTransitDistance: '+str(match.TotalTransitDistance.Value)+' '+str(match.TotalTransitDistance.MI)+'\n'
    #            message+='DistanceToDestination: '+str(match.DistanceToDestination.Value)+' '+str(match.DistanceToDestination.MI)+'\n'
                message+='ShipTimestamp: '+str(match.ShipTimestamp)+'\n'
    #            message+='EstimatedPickupTimestamp: '+str(match.EstimatedPickupTimestamp)+'\n'
                message+='EstimatedDeliveryTimestamp: '+str(match.EstimatedDeliveryTimestamp)+'\n'
                envets=match.Events
                print "envets",envets
                for event in envets:
                    message+='*****Event Activity*****'+'\n'
                    message+='\tTimestamp: '+str(event.Timestamp)+'\n'
                    message+='\tEventDescription: '+event.EventDescription+'\n'
#                    message+='\tStatusExceptionCode: '+event.StatusExceptionCode+'\n'
 #                   message+='\tStatusExceptionDescription: '+event.StatusExceptionDescription+'\n'
                    message+='\tLocation: '+event.Address.City+'\n'
                    message+='\tStateOrProvinceCode: '+event.Address.StateOrProvinceCode+'\n'
                    message+='\tPostalCode: '+event.Address.PostalCode+'\n'
        tracking_obj.write({'response_message':message})
        return True

    def close_button(self,cr,uid,ids,context={}):
        return {'type': 'ir.actions.act_window_close'}
            
track_shipping()
