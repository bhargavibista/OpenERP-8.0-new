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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from wizard.suds_client import AvaTaxService 

class tax_schedule(osv.osv):
    _name = "tax.schedule"
    _description = "Tax Schedule"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=32),
        'jurisdiction_code_ids': fields.one2many('jurisdiction.code', 'tax_schedule_id', 'Jurisdiction Codes'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True),
    }
    _defaults = {
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'tax.schedule', context=c),
    }

tax_schedule()

class jurisdiction_code(osv.osv):
    _name = "jurisdiction.code"
    _description = "Jurisdiction Code"
    _columns = {
        'name': fields.char('Description', size=32, required=True),
        'type': fields.selection([('country', 'Country'), ('composite', 'Composite'), ('state', 'State'),
                          ('county', 'County'), ('city', 'City'), ('special', 'Special')], 'Type', required=True,
                          help="Type of tax jurisdiction"),
        'state_id': fields.many2one('res.country.state', 'State', required=True, help="State for which the tax jurisdiction is defined"),
        'code':fields.char('Code', size=32),
        'tax_schedule_id': fields.many2one('tax.schedule', 'Tax Schedule'),
        #'account_collected_id':fields.many2one('account.account', 'Invoice Tax Account', required=True, help="Use this tax account for Invoices"),
        'account_collected_id':fields.property(
            type='many2one',
            relation='account.account',
            string="Invoice Tax Account",
            required=True, help="Use this tax account for Invoices"),  ###cox gen2 removed account.account parameter and view_load=True
        #'account_paid_id':fields.many2one('account.account', 'Refund Tax Account', required=True, help="Use this tax account for Refunds"),
        'account_paid_id':fields.property(
            type='many2one',
            relation='account.account',
            string="Refund Tax Account ",required=True, help="Use this tax account for Refunds",
            ), ###cox gen2 removed account.account parameter
        'base_code_id': fields.many2one('account.tax.code', 'Account Base Code', help="Use this base code for the Invoices"),
        'tax_code_id': fields.many2one('account.tax.code', 'Account Tax Code', help="Use this tax code for the Invoices"),
        'base_sign': fields.float('Base Code Sign', help="Usually 1 or -1"),
        'tax_sign': fields.float('Tax Code Sign', help="Usually 1 or -1"),
        'ref_base_code_id': fields.many2one('account.tax.code', 'Refund Base Code', help="Use this base code for the Refunds"),
        'ref_tax_code_id': fields.many2one('account.tax.code', 'Refund Tax Code', help="Use this tax code for the Refunds"),
        'ref_base_sign': fields.float('Base Code Sign', help="Usually 1 or -1"),
        'ref_tax_sign': fields.float('Tax Code Sign', help="Usually 1 or -1"),
    }
    _defaults = {
        'ref_tax_sign': 1,
        'ref_base_sign': 1,
        'tax_sign': 1,
        'base_sign': 1,
    }

    def create(self,cr,uid,val,context=None):
        print"creeeeeeeeeeeeeeee",val
        res = super(jurisdiction_code,self).create(cr,uid,val,context)
        print"ressssssss jurisdiction_code createeeeeeee",res,val
#        kdfsfgk
        return res

jurisdiction_code()

class exemption_code(osv.osv):
    _name = 'exemption.code'
    _description = 'Exemption Code'
    _columns = {
        'name': fields.char('Name', size=64),
        'code': fields.char('Code', size=2)
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = '(' + record['code'] + ')' + ' ' + name
            res.append((record['id'], name))
        return res

exemption_code()

class account_salestax_avatax(osv.osv):
    _name = 'account.salestax.avatax'
    _description = 'AvaTax Configuration'
    __rec_name = 'account_number'

    def _get_avatax_supported_countries(self, cr, uid, context=None):
        """ Returns the countries supported by AvaTax Address Validation Service."""

        country_pool = self.pool.get('res.country')
        return country_pool.search(cr, uid, [('code', 'in', ['US', 'CA'])], context=context)

    _columns = {
        'account_number':fields.char('Account Number', size=64, required=True, help="Account Number provided by AvaTax"),
        'license_key': fields.char('License Key', size=64, required=True, help="License Key provided by AvaTax"),
        'service_url': fields.char('Service URL', size=64, required=True, help="The url to connect with"),
        'date_expiration': fields.date('Service Expiration Date', readonly=True, help="The expiration date of the service"),
        'request_timeout': fields.integer('Request Timeout', help="Defines AvaTax request time out length, AvaTax best practices prescribes default setting of 300 seconds"),
        'company_code': fields.char('Company Code', size=64, required=True, help="The company code as defined in the Admin Console of AvaTax"),
        'logging': fields.boolean('Enable Logging', help="Enables detailed AvaTax transaction logging within application"),
        'address_validation': fields.boolean('Disable Address Validation', help="Check to disable address validation"),
        'result_in_uppercase': fields.boolean('Results in Upper Case', help="Check is address validation results desired to be in upper case"),
        'validation_on_save': fields.boolean('Address Validation on Save', help="Check if each address when saved should be validated"),
        'force_address_validation': fields.boolean('Force Address Validation', help="Check if address validation should be done before tax calculation"),
        'disable_tax_calculation': fields.boolean('Disable Tax Calculation', help="Check to disable tax calculation"),
        'default_tax_schedule_id': fields.many2one('tax.schedule', 'Default Tax Schedule', help="Identifies customers using AVATAX. Only customers with AVATAX designation triggers tax calculation from Avatax otherwise it will follow the normal tax calculation that OpenERP provides"),
        'default_shipping_code_id': fields.many2one('product.tax.code', 'Default Shipping Code', help="The default shipping code which will be passed to Avalara"),
        'country_ids': fields.many2many('res.country', 'account_salestax_avatax_country_rel', 'account_salestax_avatax_id', 'country_id', 'Countries', help="Countries where address validation will be used"),
        'active': fields.boolean('Active', help="Uncheck the active field to hide the record"),
        'company_id': fields.many2one('res.company', 'Company', required=True, help="Company which has subscribed to the AvaTax service"),
    }
    _defaults = {
        'active': True,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.salestax.avatax', context=c),
        'request_timeout': 300,
        'country_ids': _get_avatax_supported_countries
    }

    _sql_constraints = [
        ('code_company_uniq', 'unique (company_code)', 'The code of the company must be unique!'),
        ('account_number_company_uniq', 'unique (account_number, company_id)', 'The account number must be unique per company!'),
    ]

    def _get_avatax_config_company(self, cr, uid, context=None):
        """ Returns the AvaTax configuration for the user company """

        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        avatax_config_ids = self.search(cr, uid, [('company_id', '=', user.company_id.id)], context=context)
        return avatax_config_ids and self.browse(cr, uid, avatax_config_ids[0], context=context) or False
    
    def ping(self, cr, uid, ids, context=None):
        """ Call the Avatax's Ping Service to test the connection. """
        print "context",context
        
        if context is None:
            context = {}

        for avatax_config in self.browse(cr,uid,ids):
#            avatax_pool = self.pool.get('account.salestax.avatax')
#            avatax_config = avatax_pool.browse(cr, uid, context['active_id'], context=context)
            avapoint = AvaTaxService(avatax_config.account_number, avatax_config.license_key,
                                      avatax_config.service_url, avatax_config.request_timeout, avatax_config.logging)
            taxSvc = avapoint.create_tax_service().taxSvc     # Create 'tax' service for Ping and is_authorized calls
            avapoint.ping()
            result = avapoint.is_authorized()
            self.write(cr, uid, avatax_config.id, {'date_expiration': result.Expires})
        return True

account_salestax_avatax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: