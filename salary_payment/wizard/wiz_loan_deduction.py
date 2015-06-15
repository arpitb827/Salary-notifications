from osv import osv, fields
from tools.translate import _

class wiz_loan_deducation(osv.osv_memory):
    _name="wiz.loan.deducation"
    _columns={
              'employee_id':fields.many2one('hr.employee','P_Card',required = True),
              'year_id':fields.many2one('holiday.year','Year', required = True),
             
              }
    
    
    def print_report(self,cr,uid,ids,context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        datas = {'ids' : ids}
        wiz_loan_dedu_id = self.pool.get('wiz.loan.deducation').browse(cr,uid,ids[0])
        loan_deduction_ids = self.pool.get('loan.deduction').search(cr,uid,[('emp_id','=',wiz_loan_dedu_id.employee_id.id),('year_id','=',wiz_loan_dedu_id.year_id.id)])
        if len(loan_deduction_ids) < 1:
            raise osv.except_osv(_('Warning !'), _('The given employee have no loan. !'))
        rpt_id =  report_obj.search(cr, uid, [('model','=','wiz.loan.deducation')])
        if not rpt_id:
            raise osv.except_osv(_('Invalid action !'), _('Report for this name order no exist.'))
        rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])[0]
        return {
           'type' : 'ir.actions.report.xml',
           'report_name':str(rpt_type['report_name']),
           'datas' : datas,
           'nodestroy':True,
        }
        
          
            
   
        