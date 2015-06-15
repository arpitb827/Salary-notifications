# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2015 OpenERP4you  (http://openerp4you.in). 
#    All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details, but reseller should inform 
#    or take permission from OpenERP4you before resell..
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#    
##############################################################################


import time
from tools import amount_to_text_en
from report import report_sxw
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta

class payslip_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(payslip_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'get_time':self.get_time,
            })
        
    def get_time(self):
        date1=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date1 = datetime.strptime(date1,"%Y-%m-%d %H:%M:%S")
        date1 = date1 + timedelta(hours=5,minutes=30)
        date1 = date1.strftime("%d-%m-%Y")
        return date1

    def convert(self, amount):
        amt_en = amount_to_text_en.amount_to_text(amount, 'en', "INR")
        return amt_en
    
    
        
    
report_sxw.report_sxw('report.payslip.report', 'employee.slip', 'addons/salary_payment/report/payslip.rml', parser=payslip_report, header="external")


class paybill_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(paybill_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'get_time':self.get_time,
            'convert_int':self.convert_int,
            })
        
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
    
    
        
    
report_sxw.report_sxw('report.paybill.report', 'salary.payment.line', 'addons/salary_payment/report/paybill.rml', parser=paybill_report, header="external")



class salary_sheet_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(salary_sheet_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'salary':self.salary,
            'get_time':self.get_time,
            'total_salary':self.total_salary,
            })
        
    def get_time(self):
        date1=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date1 = datetime.strptime(date1,"%Y-%m-%d %H:%M:%S")
        date1 = date1 + timedelta(hours=5,minutes=30)
        date1 = date1.strftime("%d-%m-%Y %H:%M:%S")
        
        return date1
    
        
        
    def salary(self, month, year, type):
        if month and year and type:
            qry = "select emp.sinid,res.name,desg.name,sal.basic::integer,sal.basic_part1::integer,sal.basic_part2::integer, " \
            "sal.days,sal.days_amount::integer,sal.over_time,sal.overtime_amount::integer, sal.day_amount::integer, " \
            "sal.day_remaining_amount::integer,sal.total_amount::integer,sal.previous_advance::integer,sal.current_loan::integer,sal.epf::integer,sal.kharcha::integer,(sal.loan::integer+sal.panalty::integer+sal.security::integer+sal.telephone::integer+sal.previous_advance::integer), "\
            "(sal.epf::integer+sal.kharcha::integer+sal.loan::integer+sal.panalty::integer+sal.security::integer+sal.telephone::integer+sal.previous_advance::integer),sal.rnd_grand_total::integer from salary_payment_line as sal left join hr_employee as emp on " \
            "(sal.employee_id=emp.id) left join resource_resource as res on (emp.resource_id=res.id) "\
            "left join  hr_designation as desg on (emp.designation_id=desg.id) where " \
            "month='"+str(month)+"' and year_id='"+str(year)+"' and emp.type='"+str(type)+"' order by emp.sinid"
            
            self.cr.execute(qry)
            temp = self.cr.fetchall()
            return temp
        
    
    def total_salary(self, month, year, type):
        if month and year and type:
            qry = "select sum(sal.days_amount::integer),sum(sal.overtime_amount::integer), sum(sal.day_amount::integer), " \
            "sum(sal.day_remaining_amount::integer),sum(sal.total_amount::integer),sum(sal.previous_advance::integer),sum(sal.current_loan::integer),sum(sal.epf::integer),sum(sal.kharcha::integer),sum(sal.loan::integer+sal.panalty::integer+sal.security::integer+sal.telephone::integer+sal.previous_advance::integer), "\
            "sum(sal.epf::integer+sal.kharcha::integer+sal.loan::integer+sal.panalty::integer+sal.security::integer+sal.telephone::integer+sal.previous_advance::integer),sum(sal.rnd_grand_total::integer) from salary_payment_line as sal left join hr_employee as emp on " \
            "(sal.employee_id=emp.id) left join resource_resource as res on (emp.resource_id=res.id) "\
            "left join  hr_designation as desg on (emp.designation_id=desg.id) where " \
            "month='"+str(month)+"' and year_id='"+str(year)+"' and emp.type='"+str(type)+"'"
            
            self.cr.execute(qry)
            temp = self.cr.fetchall()
            return temp
            
            
        
report_sxw.report_sxw('report.salary.sheet.report', "wiz.salary", 'addons/salary_payment/report/salary_sheet.rml', parser=salary_sheet_report, header="external")        
        
