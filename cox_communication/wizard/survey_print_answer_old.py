# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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
import csv
import cStringIO
import base64
from datetime import datetime

class survey_print_answer(osv.osv_memory):
    _inherit = 'survey.print.answer'
    _columns = {
    }
    def print_anwser_excel(self,cr,uid,ids,context):
        if ids:
            response_ids = self.browse(cr,uid,ids[0]).response_ids
            if response_ids:
                datas = []
                datas.append("Entered Date of Customer Interaction")
                datas.append("Representative's Name")
                datas.append("Location")
                datas.append("Type Of Survey")
                datas.append("State")
                buf=cStringIO.StringIO()
                writer=csv.writer(buf, 'UNIX')
                writer.writerow(datas)
                datas = []
                for each_resp in response_ids:
                    if each_resp.date_create:
                        date_create = each_resp.date_create.split('.')
                        date_create = datetime.strptime(date_create[0], "%Y-%m-%d %H:%M:%S")
                        date_create = date_create.strftime("%Y-%m-%d")
                    else:
                        date_create = ''
                    datas.append(date_create)
		    sub_query = "(select id from survey_response_line where response_id = %s and question_id in"%(each_resp.id)
                    datas.append(each_resp.user_id.name if each_resp.user_id else '')
		    cr.execute("""select answer from survey_answer where id in \
                                (select answer_id from survey_response_answer where response_id in \
                                 """ + sub_query + """(select id from survey_question where question ilike '%location%' )))""") 
                    location = filter(None, map(lambda x:x[0], cr.fetchall()))
                    if location:
                        location = ''.join(e for e in location[0] if e.isalnum())
                        datas.append(location)
                    else:
                        datas.append('')
                    datas.append(each_resp.survey_id.title if each_resp.survey_id else '')
                    datas.append(each_resp.state.upper() if each_resp.state else '')
                    writer.writerow(datas)
                    datas = []
                out=base64.encodestring(buf.getvalue())
                buf.close()
                wizard_id =self.pool.get('export.csv').create(cr, uid,{'csv_file':out,'name': 'Survey.csv'})
                if wizard_id:
                    return {
                        'name':_("Survey Answers"),
                        'view_mode': 'form',
                        'view_id': False,
                        'view_type': 'form',
                        'res_model': 'export.csv',
                        'res_id': int(wizard_id),
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'context': context,
                        }
survey_print_answer()
