# -*- coding: utf-8 -*-
{
    'name': 'COX Incomm',
    'version': '1.0',
    'category': 'COX Incomm',
    'complexity': "easy",
    'description': """
This module is built to handle requirements of Cox Communication Incomm Gift Cards.
    """,
    'author': 'BistaSolutions',
    'depends': ['base','cox_communication',],#bista_ecommerce is inherited to hide emailid field
    'update_xml': [
    'incomm_cred_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
