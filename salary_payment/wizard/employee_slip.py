from osv import osv, fields
import time
from datetime import datetime, timedelta
from tools.translate import _
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class employee_slip(osv.osv_memory):
    _name="employee.slip"
    
    
    def _code_get(self, cr, uid, context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        ids = report_obj.search(cr, uid, [('model','=','employee.slip')])
        res = report_obj.read(cr, uid, ids, ['name'], context)
        return [(r['name'], r['name']) for r in res]
    
    _columns={
              'employee_ids':fields.many2many('salary.payment.line','employee_slip_rel','employee_id','slip_id','Employee',required=True),
              'report_type':fields.selection(_code_get,'Report',required=True),
              }
    
    
    def get_pdf(self,cr,uid,ids,context=None):
        res={}
       
        report_obj = self.pool.get('ir.actions.report.xml')
        datas = {'ids' : ids}
        type_inv = self.read(cr, uid, ids, ['report_type'])[0]
        rpt_id =  report_obj.search(cr, uid, [('name','=',type_inv['report_type'])])[0]
        if not rpt_id:
            raise osv.except_osv(('Invalid action !'),('Report for this name does not exists.'))
        rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])
       
        return {
                
           'type' : 'ir.actions.report.xml',
           'report_name':str(rpt_type['report_name']),
           'datas' : datas,
           'nodestroy':True,
        }
        