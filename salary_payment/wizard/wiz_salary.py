import time
from tools import amount_to_text_en
from report import report_sxw
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from osv import osv, fields

class wiz_salary(osv.TransientModel):
    _name = 'wiz.salary'
    
    _columns = {
                'name':fields.datetime('Creation Date',readonly=True),
                'month':fields.many2one('holiday.list','Month',required=True),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT',required=True),
               
                }
    _defaults = {
                 'name':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 }
    
    def print_report(self,cr,uid,ids,context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        datas = {'ids' : ids}
        rpt_id =  report_obj.search(cr, uid, [('model','=','wiz.salary')])
        if not rpt_id:
            raise osv.except_osv(_('Invalid action !'), _('Report for this model does not exist.'))
        rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])[0]
        return {
           'type' : 'ir.actions.report.xml',
           'report_name':str(rpt_type['report_name']),
           'datas' : datas,
           'nodestroy':True,
        }
     
        return res
     
    