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
    'name': 'Picking Scan',
    'version': '1.0',
    'category': 'Generic Modules/Inventory Control',
    'description': """
    Module enables to do inward and outward scanning. Also it manages the validation process in delivery order.

    """,
    'author': 'Bista Solutions',
    'website': 'http://www.openerp.com',
    'depends': ["tr_barcode" ,"delivery"],
    'init_xml': [],
    'data': [
                
                'wizard/picking_scanning_view.xml',
                'wizard/shipping_process_view.xml',
#                'stock_view_barcode.xml',
                'tr_barcode_view.xml',
                'stock_view.xml',
                'stock_serial_lot_view.xml'
    ],
    'demo_xml': [],
    'test': [
        
    ],
    'installable': True,
    'active': False,
    #'certificate': ,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
