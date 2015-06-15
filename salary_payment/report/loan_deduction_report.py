from report import report_sxw
import time


class loan_deducation_report(report_sxw.rml_parse):
    glob_loan_amount = 0.00

    def __init__(self, cr, uid, name, context):
        super(loan_deducation_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_employee_loan_deducation_line':self.get_employee_loan_deducation_line,
            'get_amount':self.get_amount,
            'get_convert_int_value':self.get_convert_int_value
              })
        
        
    def get_employee_loan_deducation_line(self,employee_id,year_id):
        l=[]
        loan_deduction_ids =[]
        emp_loan_deduction_line  = []
        loan_deduction_ids = self.pool.get('loan.deduction').search(self.cr,self.uid,[('emp_id','=',employee_id.id),('year_id','=',year_id.id)])
        for val in loan_deduction_ids:
            emp_loan_deduction_line.append(self.pool.get('loan.deduction').browse(self.cr,self.uid,val))
        return emp_loan_deduction_line
    
    def get_amount(self,loan_amt):
        self.glob_loan_amount = loan_amt + self.glob_loan_amount
        return int(self.glob_loan_amount)
    
    def get_convert_int_value(self,value):
        val2 = int(value)
        return val2
        
report_sxw.report_sxw('report.loan.deducation.report', 'wiz.loan.deducation', 'addons/hr_designco/report/loan_deducation_report.rml', parser=loan_deducation_report,header='external')
