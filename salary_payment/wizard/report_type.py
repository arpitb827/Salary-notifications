from osv import osv, fields
from tools.translate import _

class salary_report_type(osv.osv_memory):
    _name="salary.report.type"
    
    _columns={
              'name':fields.selection([('payslip','Payslip'),('paybill','Paybill')],'Type',required=True),
              }
    
    def get_report(self,cr,uid,ids,context=None):
        res={}
        data=self.browse(cr,uid,ids)
        choice=data[0].name
        report_obj = self.pool.get('ir.actions.report.xml')
        active_ids = context.get('active_ids',[])
        datas = {'ids' : active_ids}
        if choice =='payslip':
            rpt_id =  report_obj.search(cr, uid, [('report_name','=','payslip.report')])[0]
        else:
            rpt_id =  report_obj.search(cr, uid, [('report_name','=','paybill.report')])[0]
        if not rpt_id:
            raise osv.except_osv(_('Invalid action !'), _('Report for this name does not exists.'))
        rpt_type = report_obj.read(cr, uid, rpt_id, ['report_name'])
        return {
                
           'type' : 'ir.actions.report.xml',
           'report_name':str(rpt_type['report_name']),
           'datas' : datas,
           'nodestroy':True,
        }
        
   
    
   