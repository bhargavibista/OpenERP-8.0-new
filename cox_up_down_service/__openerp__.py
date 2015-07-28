# -*- coding: utf-8 -*-
{
    'name': 'COX Upgrade/Downgrade of Service',
    'version': '1.0',
    'category': 'Service Upgrade/Downgrade',
    'complexity': "easy",
    'description': """
This module is built to handle requirements of Cox Communication Service Upgradation/Downgradation.
    """,
    'author': 'BistaSolutions',
    'depends': ['base','cox_communication',],
    'update_xml': [
    'up_down_view.xml',
    'up_down_sequence.xml',
    'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'certificate': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
