# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

from wizard.suds_client import AvaTaxService, BaseAddress 

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'exemption_number': fields.char('Exemption Number', size=64, help="Indicates if the customer is exempt or not"),
        'exemption_code_id': fields.many2one('exemption.code', 'Exemption Code', help="Indicates the type of exemption the customer may have"),
        'tax_schedule_id': fields.many2one('tax.schedule', 'Tax Schedule', help="Identifies customers using AVATAX. Only customers with AVATAX designation triggers tax calculation from Avatax otherwise it will follow the normal tax calculation that OpenERP provides"),

        'date_validation': fields.date('Last Validation Date', readonly=True,help="The date the address was last validated by AvaTax and accepted"),
        'validation_method': fields.selection([('avatax', 'AVATAX'), ('usps', 'USPS'), ('other', 'Other')], 'Address Validation Method', readonly=True ,help="It gets populated when the address is validated by the method"),
        'latitude': fields.char('Latitude', size=32),
        'longitude': fields.char('Longitude', size=32),
        'validated_on_save': fields.boolean('Validated On Save', help="Indicates if the address is already validated on save before calling the wizard")
    }

    def check_avatax_support(self, cr, uid, avatax_config, country_id, context=None):
        """ Checks if address validation pre-condition meets. """

        if avatax_config.address_validation:
            raise osv.except_osv(_('Address Validation is Disabled'), _("The AvaTax Address Validation Service is disabled by the administrator. Please make sure it's enabled for the address validation"))
        if country_id and country_id not in [x.id for x in avatax_config.country_ids]:
            raise osv.except_osv(_('Address Validation not Supported for this country'), _("The AvaTax Address Validation Service does not support this country in the configuration, please continue with your normal process."))
        return True

    def get_state_id(self, cr, uid, code, context=None):
        """ Returns the id of the state from the code. """

        state_obj = self.pool.get('res.country.state')
        return state_obj.search(cr, uid, [('code', '=', code)], context=context)[0]

    def get_country_id(self, cr, uid, code, context=None):
        """ Returns the id of the country from the code. """

        country_obj = self.pool.get('res.country')
        return country_obj.search(cr, uid, [('code', '=', code)], context=context)[0]

    def get_state_code(self, cr, uid, state_id, context=None):
        """ Returns the code from the id of the state. """

        state_obj = self.pool.get('res.country.state')
        return state_id and state_obj.browse(cr, uid, state_id, context=context).code

    def get_country_code(self, cr, uid, country_id, context=None):
        """ Returns the code from the id of the country. """

        country_obj = self.pool.get('res.country')
        return country_id and country_obj.browse(cr, uid, country_id, context=context).code

    def _validate_address(self, cr, uid, address, avatax_config=False, context=None):
        """ Returns the valid address from the AvaTax Address Validation Service. """

        avatax_config_obj= self.pool.get('account.salestax.avatax')
        if context is None:
            context = {}

        if not avatax_config:
            avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid, context=context)

        # Create the AvaTax Address service with the configuration parameters set for the instance
        avapoint = AvaTaxService(avatax_config.account_number, avatax_config.license_key,
                        avatax_config.service_url, avatax_config.request_timeout, avatax_config.logging)
        addSvc = avapoint.create_address_service().addressSvc

        # Obtain the state code & country code and create a BaseAddress Object
        state_code = address.get('state_id') and self.get_state_code(cr, uid, address['state_id'], context=context)
        country_code = address.get('country_id') and self.get_country_code(cr, uid, address['country_id'], context=context)
        baseaddress = BaseAddress(addSvc, address.get('street') or None, address.get('street2') or None,
                         address.get('city'), address.get('zip'), state_code, country_code, 0).data
        result = avapoint.validate_address(baseaddress, avatax_config.result_in_uppercase and 'Upper' or 'Default')
        valid_address = result.ValidAddresses[0][0]
        return valid_address

    def update_address(self, cr, uid, vals, ids=None, from_write=False, context=None):
        """ Updates the vals dictionary with the valid address as returned from the AvaTax Address Validation. """

        address = vals
        if isinstance(vals,dict):
            if (vals.get('street') or vals.get('street2') or vals.get('zip') or vals.get('city') or \
                vals.get('country_id') or vals.get('state_id')):

                address_obj = self.pool.get('res.partner')
                avatax_config_obj= self.pool.get('account.salestax.avatax')
                avatax_config = avatax_config_obj._get_avatax_config_company(cr, uid, context=context)

                if avatax_config and avatax_config.validation_on_save:
                    # It implies that there is AvaTax configuration existing for the user company with
                    # option 'Address Validation when a address is saved'
                    # Check if the other conditions are met
                    self.check_avatax_support(cr, uid, avatax_config, address.get('country_id'), context=context)

                    # If this method is called from the 'write' method then we also need to pass
                    # the previous address along with the modifications in the vals dictionary
                    if from_write:
                        fields_to_read = filter(lambda x: x not in vals, ['street', 'street2', 'city', 'state_id', 'zip', 'country_id'])
                        address = fields_to_read and address_obj.read(cr, uid, ids, fields_to_read, context=context)[0] or {}
                        address['state_id'] = address.get('state_id') and address['state_id'][0]
                        address['country_id'] = address.get('country_id') and address['country_id'][0]
                        address.update(vals)

                    valid_address = self._validate_address(cr, uid, address, avatax_config, context=context)
                    vals.update({
                        'street': valid_address.Line1,
                        'street2': valid_address.Line2,
                        'city': valid_address.City,
                        'state_id': self.get_state_id(cr, uid, valid_address.Region, context=context),
                        'zip': valid_address.PostalCode,
                        'country_id': self.get_country_id(cr, uid, valid_address.Country, context=context),
                        'latitude': valid_address.Latitude,
                        'longitude': valid_address.Longitude,
                        'date_validation': time.strftime('%Y-%m-%d'),
                        'validation_method': 'avatax',
                        'validated_on_save': True
                    })
        return vals


    def create(self, cr, uid, vals, context=None):
        if not vals.get('auto_import'):
            vals = self.update_address(cr, uid, vals, context=context)
        return super(res_partner, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        # Follow the normal write process if it's a write operation from the wizard
#        if context.get('from_validate_button', False):
#            return super(res_partner_address, self).write(cr, uid, ids, vals, context)
#
#        if context.get('active_id', False):
        if not vals.get('auto_import'):
            vals = self.update_address(cr, uid, vals, ids, True, context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context)

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: