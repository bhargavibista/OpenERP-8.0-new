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
import unicodedata
from datetime import datetime

class survey_print_answer(osv.osv_memory):
    _inherit = 'survey.print.answer'
    _columns = {
#     'survey_id': fields.many2one('survey','Survey'),
      'survey_id':fields.many2many('survey','id','answer_id','survey_answer_id', "Survey"),
    }
    def onchange_survey_id(self,cr,uid,ids,survey_id,context={}):
        res={}
        res['value'] = {}
        res['value']['response_ids'] = []
        return res
    def print_anwser_excel(self,cr,uid,ids,context):
        buf=cStringIO.StringIO()
        writer=csv.writer(buf, 'UNIX')
        quest_list = []
        index=0
        if ids:
            ids_brw = self.browse(cr,uid,ids[0])
            datas = []
            for each_id in ids_brw.survey_id:
                page_ids = each_id.page_ids
                if page_ids:
                    if not datas:
                        datas.append("StartDate")
                        datas.append("Representative's Name or Number")
                        datas.append("Type Of Survey")
                    for each_page in page_ids:
                        question_ids= each_page.question_ids
                        if question_ids:
                            for each_question in question_ids:
                                quest_list.append(each_question.id)
                                if each_question.question not in datas:
                                    datas.append((unicodedata.normalize('NFKD', each_question.question).encode('utf-8')))
            writer.writerow(datas)
            response_ids = self.browse(cr,uid,ids[0]).response_ids
            if response_ids:
                for each_resp in response_ids:
                    datas1=list(datas)
                    if each_resp.date_create:
                        date_create = each_resp.date_create.split('.')
                        date_create = datetime.strptime(date_create[0], "%Y-%m-%d %H:%M:%S")
                        date_create = date_create.strftime("%Y-%m-%d")
                    else:
                        date_create = ''
                    datas1[0]=date_create
                    datas1[1]=(each_resp.user_id.name if each_resp.user_id else '')
                    datas1[2]=(each_resp.survey_id.title if each_resp.survey_id else '')
                    for each_quest in quest_list:
                        ques_obj=self.pool.get('survey.question').browse(cr,uid,each_quest).question
                        ques_obj=unicodedata.normalize('NFKD', ques_obj).encode('ascii','ignore')
                        if ques_obj in datas:
                            index=datas.index(ques_obj)
                        sub_query = "(select id from survey_response_line where response_id = %s and question_id =  %s))"%(each_resp.id,each_quest)
                        cr.execute("""select answer from survey_answer where id in \
                                    (select answer_id from survey_response_answer where response_id in \
                                     """  + sub_query +"""order by question_id""")
                        answers = filter(None, map(lambda x:x[0], cr.fetchall()))
                        if answers:
                            answers=unicodedata.normalize('NFKD', answers[0]).encode('ascii','ignore')
                            datas1[index]=answers
                        else:
			    cr.execute("select comment from survey_response_line where response_id = %s and question_id =  %s"%(each_resp.id,each_quest))
                            comment = filter(None, map(lambda x:x[0], cr.fetchall()))
                            if comment:
                                 comment=unicodedata.normalize('NFKD', comment[0]).encode('ascii','ignore')
                                 datas1[index]=comment
                            else:
	                        cr.execute("select single_text from survey_response_line where response_id = %s and question_id =  %s"%(each_resp.id,each_quest))
                                single_text = filter(None, map(lambda x:x[0], cr.fetchall()))
	                        if single_text:
                                    single_text=unicodedata.normalize('NFKD', single_text[0]).encode('ascii','ignore')
                                    datas1[index]=single_text

                    for each_datas in datas:
                        for each_datas1 in datas1:
                            if each_datas==each_datas1:
                                datas1_index=datas1.index(each_datas)
                                datas1[datas1_index]=''
                    writer.writerow(datas1)
                    datas1=[]
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
#    def print_anwser_excel(self,cr,uid,ids,context):
#        if ids:
#            response_ids = self.browse(cr,uid,ids[0]).response_ids
#            if response_ids:
#                datas = []
#                datas.append("Entered Date of Customer Interaction")
#                datas.append("Representative's Name")
#                datas.append("Location")
#                datas.append("Type Of Survey")
#                datas.append("State")
#                buf=cStringIO.StringIO()
#                writer=csv.writer(buf, 'UNIX')
#                writer.writerow(datas)
#                datas = []
#                for each_resp in response_ids:
#                    if each_resp.date_create:
#                        date_create = each_resp.date_create.split('.')
#                        date_create = datetime.strptime(date_create[0], "%Y-%m-%d %H:%M:%S")
#                        date_create = date_create.strftime("%Y-%m-%d")
#                    else:
#                        date_create = ''
#                    datas.append(date_create)
#		    sub_query = "(select id from survey_response_line where response_id = %s and question_id in"%(each_resp.id)
#                    datas.append(each_resp.user_id.name if each_resp.user_id else '')
#		    cr.execute("""select answer from survey_answer where id in \
#                                (select answer_id from survey_response_answer where response_id in \
#                                 """ + sub_query + """(select id from survey_question where question ilike '%location%' )))""")
#                    location = filter(None, map(lambda x:x[0], cr.fetchall()))
#                    if location:
#                        location = ''.join(e for e in location[0] if e.isalnum())
#                        datas.append(location)
#                    else:
#                        datas.append('')
#                    datas.append(each_resp.survey_id.title if each_resp.survey_id else '')
#                    datas.append(each_resp.state.upper() if each_resp.state else '')
#                    writer.writerow(datas)
#                    datas = []
#                out=base64.encodestring(buf.getvalue())
#                buf.close()
#                wizard_id =self.pool.get('export.csv').create(cr, uid,{'csv_file':out,'name': 'Survey.csv'})
#                if wizard_id:
#                    return {
#                        'name':_("Survey Answers"),
#                        'view_mode': 'form',
#                        'view_id': False,
#                        'view_type': 'form',
#                        'res_model': 'export.csv',
#                        'res_id': int(wizard_id),
#                        'type': 'ir.actions.act_window',
#                        'nodestroy': True,
#                        'target': 'new',
#                        'context': context,
#                        }

survey_print_answer()
