import time
from tools import amount_to_text_en
from report import report_sxw
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta


class new_paybill_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(new_paybill_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'get_time':self.get_time,
            'convert_int':self.convert_int,
            'order_by':self.order_by,
            'get_month':self.get_month,
            'get_bill_date':self.get_bill_date,
            })
    def get_bill_date(self,month,year):
        holiday_list_id = []
        start_date=''
        start_date1=''
        if int(month) in range(0,10):
            month = int(month) + 1
            month = '0'+ str(month)
        elif int(month) == '11':
            month = int(month) + 1
            month = str(month)
        elif int(month)== '12' :
            month = 1
            month = '0'+ str(month)
            year=int(year) +1
            year=str(year)
        start_date = str(year + '-' + month + '-' +'01')
        start_date1 = str(year + '-' + month + '-' +'02')
        holiday_list_id = self.pool.get('holiday.list.lines').search(self.cr,self.uid,[('leave_date','=',start_date)])
        if holiday_list_id:
            return start_date1
        else:
            return start_date
            
    def get_month(self,m_id):
        if m_id=='1':
            return 'Jan'
        if m_id=='2':
            return 'Feb'
        if m_id=='3':
            return 'Mar'
        if m_id=='4':
            return 'Apr'
        if m_id=='5':
            return 'May'
        if m_id=='6':
            return 'Jun'
        if m_id=='7':
            return 'Jul'
        if m_id=='8':
            return 'Aug'
        if m_id=='9':
            return 'Sep'
        if m_id=='10':
            return 'Oct'
        if m_id=='11':
            return 'Nov'
        if m_id=='12':
            return 'Dec'
        
    def get_time(self):
        date1=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date1 = datetime.strptime(date1,"%Y-%m-%d %H:%M:%S")
        date1 = date1 + timedelta(hours=5,minutes=30)
        date1 = date1.strftime("%d-%m-%Y")
        return date1

    def convert_int(self, amount):
        amount = int(amount)
        return amount

    def convert(self, amount):
        amt_en = amount_to_text_en.amount_to_text(amount, 'en', "INR")
        return amt_en
    
    def order_by(self, line):
        emp_ids = []
        if line:
            for val in line:
                emp_ids.append(val.id)
        if emp_ids:
            emp_ids = list(set(emp_ids))
            if len(emp_ids) == 1:
                emp_ids.append(emp_ids[0])
                
            emp_list = tuple(emp_ids)
            qry = "select emp.sinid,res.name,sal.basic::integer,sal.basic_part1::integer,sal.basic_part2::integer, " \
            "sal.days,sal.days_amount::integer,sal.over_time,sal.overtime_amount::integer, sal.day_amount::integer, " \
            "sal.day_remaining_amount::integer,sal.total_amount::integer,sal.previous_advance::integer,sal.kharcha::integer, "\
            "sal.current_loan::integer,sal.loan::integer,sal.epf::integer,sal.tds::integer,sal.panalty::integer,sal.telephone::integer,sal.security::integer, " \
            "sal.conveyance::integer,(sal.epf::integer+sal.tds::integer+sal.kharcha::integer+sal.loan::integer+sal.panalty::integer+sal.security::integer+sal.telephone::integer+ " \
            "sal.previous_advance::integer-sal.conveyance::integer),sal.rnd_grand_total::integer,emp.type,sal.salary_type,sal.month,hy.name ,emp.home_address from salary_payment_line as sal left join hr_employee as emp on " \
            "(sal.employee_id=emp.id) left join resource_resource as res on (emp.resource_id=res.id) "\
            "left join  hr_designation as desg on (emp.designation_id=desg.id)  " \
            "left join holiday_year as hy on (sal.year_id=hy.id)"\
            "where sal.id in "+str(emp_list)+" order by (substring(emp.sinid, '^[0-9]+'))::int ,substring(emp.sinid, '[^0-9_].*$')"
             

            self.cr.execute(qry)
            temp = self.cr.fetchall()
            return temp
    
    
        
    
report_sxw.report_sxw('report.new.paybill.report', 'employee.slip', 
                      'addons/salary_payment/report/new_paybill.rml', parser=new_paybill_report, header=False)

