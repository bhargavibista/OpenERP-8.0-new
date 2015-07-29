# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
{
    'name': 'COX',
    'version': '1.0',
    'category': 'Sales',
    'complexity': "easy",
    'description': """
This module is built to handle requirements of Cox Communication.
    """,
    
#    'magentoerpconnect','bista_ecommerce',
    'author': 'BistaSolutions',
    'depends': ['base','account_voucher','bista_authorize_net','crm_helpdesk','sale_bundle_product','bista_order_returns','barcode_scanning','sub_product_combination','bista_shipping','account_salestax_avatax',
    'sale_negotiated_shipping','sale_stock','survey','mrp'],#bista_ecommerce is inherited to hide emailid field
    'data': [],
    'data': [
	'wizard/shipping_order_view.xml',
	'wizard/shipping_returns_view.xml',
        
        'security/departments_security.xml',
        'security/new_cox_security.xml',
        
        'security/ir.model.access.csv',  ##cox gen2
        'wizard/active_recurring_billing_view.xml',
        'wizard/pre_requisites.xml',
        'sale_view.xml',
#        'survey_view.xml',  ##cox gen2
        'board_sale_view.xml', ##cox gen2
        'board_purchase_view.xml',   ##cox gen2 added
        'board_crm_view.xml', ##cox gen2 added
        'board_account_view.xml',  ##cox gen2 added
        'board_project_view.xml', ##cox gen2 added
        'board_warehouse_view.xml', ##cox gen2 added
        'board_view.xml',  ##cox gen2
        'partner_policy_view.xml',
        'invoice_view.xml',
        'res_partner_view.xml',
         'product_view.xml',
        'crm_helpdesk.xml',
        'reasons_view.xml',
        'returns_view.xml',
        'wizard/agreement_view.xml',
        'wizard/picking_scanning_view.xml', 
#        'wizard/provision_customer.xml',    cox gen2 not needed
        'wizard/retail_delivery_view.xml',
        'wizard/in_store_pickup.xml',
        'wizard/export_csv.xml',
        'wizard/partner_individual_payment.xml',
        'wizard/credit_service_refund.xml',
        'wizard/refund_against_invoice.xml',
#        'wizard/magento_data_export_view.xml', cox gen2 not needed
        'wizard/send_mail_manually.xml',
        'wizard/pre_picking_scanning.xml',
        'wizard/deliver_goods.xml',
        'wizard/recurring_billing.xml',
        'wizard/flarewatch_customer.xml',
#	'wizard/demo_account_setup.xml',  ##cox gen2 not needed
	'wizard/serial_stock_move.xml',
	'wizard/deactivate_service_refund_view.xml',
#	'wizard/survey_print_answer.xml', ###cox gen2
	'wizard/charge_termination_fees.xml',
	'wizard/returns_refund_cancellation.xml',
	'wizard/return_shipment_label.xml',
#        'wizard/order_confirmation_view.xml',
#        'settings/1.5.0.0/external.mappinglines.template.csv', cox gen2 not needed
        'stock_data.xml',
        'schedular.xml',
        'stock_view.xml',
        'email_template.xml',
#        'report/sale_report.xml',##cox gen2 not needed
#        'credit_service_view.xml',
        'credit_service_sequence.xml',
#        'report/sales_returns_analysis.xml',##cox gen2 not needed
#        'board_sale_view.xml',

#        'report/report_stock_move.xml', ##cox gen2 not needed
        'custom_reporting/board_churn_view.xml',
        'custom_reporting/report_avg_customer_lifetime_view.xml',
        'custom_reporting/month_to_month_sales.xml',
        'custom_reporting/board_sales_2weeks.xml',
        'custom_reporting/report_inventory_analysis_view.xml',
	'custom_reporting/report_sales_churn_ending_subs_view.xml',        
	'custom_reporting/export_inventory_analysis_report_csv.xml',
        'credit_service_view.xml',
        'transaction_wizard.xml',
        'wizard/billing_date_update.xml',
        'vista_delivery_view.xml',
#        'wizard/vista_report_wizard.xml',
#	'wizard/reset_password_oe.xml',   ##cox gen2
	'wizard/scan_label_devices.xml',
        'wizard/shipping_send_mail_view.xml',
	'wizard/export_customer_history_view.xml',
#	'wizard/procurement_wizard_view.xml',
	
	'sale_import_view.xml',
        'mrp_view.xml',
        'service_config_view.xml',
        'wizard/import_serials.xml',
        'wizard/procurement_wizard_view.xml',
        'wizard/warning_view.xml',
    ],
    'demo_xml': [],
    'js':['static/src/js/*.js'],
    'test': [],
    'installable': True,
    'auto_install': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
