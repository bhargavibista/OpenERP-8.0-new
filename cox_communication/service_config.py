from openerp.osv import fields, osv

class service_configuration(osv.osv):
    _name='service.configuration'
    _columns={
    'no_days':fields.integer('Interval'),
    'scheduler_type':fields.selection([
                    ('cancel_service_not_paid','Cancellation of Services for Payment Exception'),
                    ('recurring_payment_reminder','Recurring Payment Reminder'),
                    ('expiry_credit_card_check_14_days','Check Credit Card Expiry Before 14 Days'),
                    ('expiry_credit_card_check_7_days','Check Credit Card Expiry Before 7 Days'),
    ],'Scheduler')
    }
service_configuration()

