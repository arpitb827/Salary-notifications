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
from osv import osv, fields
from tools.translate import _
import decimal_precision as dp
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import os
import base64, urllib
import netsvc
import cStringIO
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf


class department_budget_report(osv.osv_memory):
    _name="department.budget.report"
    
    _columns={
              'date':fields.datetime('Creation Date',readonly=True),
              'dept_id':fields.many2one('hr.department','Department Name'),
              'filename':fields.char('File Name',size=250,readonly=True),
              'export_data':fields.binary('File',readonly=True),
              'month':fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
              ('8','August'),('9','September'),('10','October'),('11','November'),('12','December'),],'Month',required=True),
              'year_id':fields.many2one('holiday.year','Year',required=True),
              'case':fields.selection([('All','All'),('Management','Management')])
              }
    
    _defaults = {
                 'date':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 }
    
    def report_get(self,cr,uid,ids,context=None):
  
        this=self.browse(cr,uid,ids[0])
        year = this.year_id.name
        year_id = this.year_id.id
        month = this.month
        if month == '1':
            month_name = 'January'
        elif month == '2':
            month_name = 'February'
        elif month == '3':
            month_name = 'March'
        elif month == '4':
            month_name = 'April'
        elif month == '5':
            month_name = 'May'
        elif month == '6':
            month_name = 'June'
        elif month == '7':
            month_name = 'July'
        elif month == '8':
            month_name = 'August'
        elif month == '9':
            month_name = 'September'
        elif month == '10':
            month_name = 'October'
        elif month == '11':
            month_name = 'November'
        elif month == '12':
            month_name = 'December'
        else:
            raise osv.except_osv(_('Warning !'),_("Specify month correctly. "))
        
        #Define the font attributes for header
        fnt = Font()
        fnt.name = 'Arial'
        fnt.height= 275
        
        #Define the font attributes for header
        content_fnt = Font()
        content_fnt.name ='Arial'
        content_fnt.height =220
        align_content = Alignment()
        align_content.horz= Alignment.HORZ_CENTER
     
        borders = Borders()
        borders.left = 0x02
        borders.right = 0x02
        borders.top = 0x02
        borders.bottom = 0x02
        
        #The text should be centrally aligned
        align = Alignment()
        align.horz = Alignment.HORZ_CENTER
        align.vert = Alignment.VERT_CENTER
        
        #We set the backgroundcolour here
        pattern = Pattern()
        pattern.pattern = Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour =  0x1F

        #apply the above settings to the row(0) header
        style_header= XFStyle()
        style_header.font= fnt
        style_header.pattern= pattern
        style_header.borders = borders
        style_header.alignment=align    
        
        #Define the font attributes for header
        fnt1 = Font()
        fnt1.name = 'Arial'
        fnt1.height= 275
        
        #Define the font attributes for header
        content_fnt1 = Font()
        content_fnt1.name ='Arial'
        content_fnt1.height =220
        align_content1 = Alignment()
        align_content1.horz= Alignment.HORZ_CENTER
     
        borders1 = Borders()
        borders1.left = 0x02
        borders1.right = 0x02
        borders1.top = 0x02
        borders1.bottom = 0x02
        
        #The text should be centrally aligned
        align1 = Alignment()
        align1.horz = Alignment.HORZ_CENTER
        align1.vert = Alignment.VERT_CENTER
        
        #We set the backgroundcolour here
        pattern1 = Pattern()
        pattern1.pattern = Pattern.SOLID_PATTERN
        pattern1.pattern_fore_colour =  0x32

        #apply the above settings to the row(0) header
        style_header1= XFStyle()
        style_header1.font= fnt1
        style_header1.pattern= pattern1
        style_header1.borders = borders1
        style_header1.alignment=align1   
        
        
        style_content= XFStyle()
        style_content.alignment = align_content 
        style_content.font = content_fnt
        month_name = 'Payment ('+str(month_name)+')'
        wb = Workbook()
        ws = wb.add_sheet('Budget')
        ws.row(0).height=500
        ws.write(0,0,'Department Name',style_header)
        ws.col(0).width = 8000
        ws.write(0,1,'Department HoD',style_header)
        ws.col(1).width = 8000
        ws.write(0,2,'Employee Name',style_header)
        ws.col(2).width = 8000
        ws.write(0,3,'Salary Amount',style_header)
        ws.col(3).width = 5000
        ws.write(0,4,month_name,style_header)
        ws.col(4).width = 8000
#        ws.write(0,5,'O.T. Amount',style_header)
#        ws.col(5).width = 4400
#        ws.write(0,6,'Total Amount',style_header)
#        ws.col(6).width = 4400
#        ws.write(0,7,'Insentive Amount',style_header)
#        ws.col(7).width = 4400
#        ws.write(0,8,'Deduction Amount',style_header)
#        ws.col(8).width = 5000
#        ws.write(0,9,'Percentage',style_header)
#        ws.col(9).width = 4400
        emp_ids = []
        daily_obj=self.pool.get('budget.salary.line')
        emp_obj=self.pool.get('hr.employee')
        pay_obj=self.pool.get('salary.payment.line')
        if this.dept_id:
            cr.execute("select id from budget_salary_line where department_id = " \
             "'"+str(this.dept_id.id)+"' and month = '"+str(month)+"' and year_id = '"+str(year_id)+"' " \
             "order by department_id")
            temp = cr.fetchall()
            for data in temp:
                if len(data)>0 and data[0] != None:
                    emp_ids.append(data[0])
            
        else:
            cr.execute("select id from budget_salary_line where month = '"+str(month)+"' and year_id = '"+str(year_id)+"' " \
             "order by department_id")
            temp = cr.fetchall()
            for data in temp:
                if len(data)>0 and data[0] != None:
                    emp_ids.append(data[0])
                    
        holiday_obj = self.pool.get('holiday.list')
        
        if int(month) in [1,3,5,7,8,10,12]:
            month = 31
        if int(month) in [4,6,9,11]:
            month = 30
        if int(month) in [2]:
            if int(year) % 4 == 0:
                month = 29
            else:
                month = 28
        off_day = working_day = 0
        holiday_ids = holiday_obj.search(cr, uid, [('month','=',this.month),('year_id','=',year_id)])
        for line in holiday_obj.browse(cr, uid, holiday_ids):
            off_day = line.holiday
        working_day = month - off_day
               
        i=0
        dept_dict = {}
        grand = total = pay_total = pay_grand = budget = 0.0
        pay_data = False
        flag = True
        for each in daily_obj.browse(cr, uid, emp_ids):
            pay_ids = pay_obj.search(cr, uid, [('employee_id','=',each.employee_id.id),('month','=',this.month),('year_id','=',this.year_id.id)])
            if pay_ids:
                pay_data = pay_obj.browse(cr, uid, pay_ids[0])
            
            i+=1
            if dept_dict.has_key(str(each.department_id.id)):
                if each.department_id:
                    salary = 0.0
                    dept = '[' + str(each.department_id.dept_code) +'] '+ str(each.department_id.name)
                    ws.write(i,0, dept)
                
                    ws.write(i,1, each.department_id.manager_id and each.department_id.manager_id.name or '')
                    name = '[' + str(each.employee_id.sinid) +'] '+ str(each.employee_id.name)
                    ws.write(i,2, name)
                    if each.employee_id.daily:
                        salary = each.employee_id.salary * working_day
                    else:
                        salary = each.employee_id.salary
                    ws.write(i,3, salary)
                    if each.total_amount:
                        ws.write(i,4,each.total_amount or 0.0)
                    else:
                        ws.write(i,4, 0.0)
                    total += salary
                    grand +=  salary
                    if each.total_amount:
                        pay_total += each.total_amount or 0.0
                        pay_grand += each.total_amount or 0.0
                    else:
                        pay_total += 0.0
                        pay_grand += 0.0
                        
            elif not each.department_id:
                salary = 0.0
                if flag:
                    ws.write(i,0, 'Allocated Budget',style_header)
                    ws.write(i,1, 0.0,style_header)
                    ws.write(i,2, 'Total',style_header)
                    ws.write(i,3, total,style_header)
                    if pay_total:
                        ws.write(i,4,pay_total,style_header)
                    else:
                        ws.write(i,4, 0.0,style_header)
                    if budget:
                        diff = pay_total - float(budget)
                    else:
                        diff = pay_total
                        
                    ws.write(i,5, diff,style_header1)
                    flag = False
                    i += 2
                    total = pay_total = budget = 0.0
                name = '[' + str(each.employee_id.sinid) +'] '+ str(each.employee_id.name)
                
                ws.write(i,0, 'X Department')                
                ws.write(i,1,'X Reporting Officer')
                ws.write(i,2, name)
                
                if each.employee_id.daily:
                    salary = each.employee_id.salary * working_day
                else:
                    salary = each.employee_id.salary
                ws.write(i,3, salary)
                if each.total_amount:
                    ws.write(i,4,each.total_amount or 0.0)
                else:
                    ws.write(i,4, 0.0)
                total += salary
                grand +=  salary
                if each.total_amount:
                    pay_total += each.total_amount or 0.0
                    pay_grand +=  each.total_amount or 0.0
                else:
                    pay_total += 0.0
                    pay_grand += 0.0
                        
            else:
                dept_dict[str(each.department_id.id)] = ''
                if i != 1:
                    ws.write(i,0, 'Allocated Budget',style_header)
                    if budget:
                        ws.write(i,1, budget,style_header)
                    else:
                        budget = 0.0
                        ws.write(i,1,budget,style_header)
                    ws.write(i,2, 'Total',style_header)
                    ws.write(i,3, total,style_header)
                    if pay_total:
                        ws.write(i,4,pay_total,style_header)
                    else:
                        ws.write(i,4, 0.0,style_header)
                    if budget:
                        print("=======pay_total=========",pay_total,budget)
                        diff = pay_total - float(budget)
                    else:
                        diff = pay_total
                        
                    ws.write(i,5, diff,style_header1)
                    i += 2
                total = pay_total = budget = 0.0
                if each.department_id:
                    salary = 0.0
                    budget = each.department_id.dept_budget
                    dept = '[' + str(each.department_id.dept_code) +'] '+ str(each.department_id.name)
                    ws.write(i,0, dept)
                
                    ws.write(i,1, each.department_id.manager_id and each.department_id.manager_id.name or '')
                    name = '[' + str(each.employee_id.sinid) +'] '+ str(each.employee_id.name)
                    ws.write(i,2, name)
                    if each.employee_id.daily:
                        salary = each.employee_id.salary * working_day
                    else:
                        salary = each.employee_id.salary
                    ws.write(i,3, salary)
                    if each.total_amount:
                        ws.write(i,4,each.total_amount or 0.0)
                    else:
                        ws.write(i,4, 0.0)
                    total += salary
                    grand +=  salary
                    if each.total_amount:
                        pay_total += each.total_amount or 0.0
                        pay_grand +=  each.total_amount or 0.0
                    else:
                        pay_total += 0.0
                        pay_grand += 0.0
                        
            
                    
        i += 1
                    
        ws.write(i+1,2, 'Total',style_header)
        ws.write(i+1,3, total,style_header)
        ws.write(i+3,2, 'Grand Total',style_header)
        ws.write(i+3,3, grand,style_header)
        
        ws.write(i+1,4, pay_total,style_header)
        ws.write(i+3,4, pay_grand,style_header)
        
        diff_pay = pay_total - total
        diff_grand = pay_grand - grand
        
        ws.write(i+1,5, diff_pay,style_header1)
        ws.write(i+3,5, diff_grand,style_header1)
        f = cStringIO.StringIO()
        wb.save(f)
        out=base64.encodestring(f.getvalue())
               
               
               
        return self.write(cr, uid, ids, {'export_data':out, 'filename':'export.xls'}, context=context)
    


class daily_salary(osv.osv):
    _name = 'daily.salary'
    
    def _calculate_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for val in self.browse(cr, uid, ids):
            res[val.id] = val.month and val.month.name or False
        return res
    
    def _create_emp_lines(self, val):
        return  {
                   'employee_id':val.id,
                   'department_id':val.department_id and val.department_id.id or False,
                   'basic':val.salary,
               }
    
    def _get_all_employee(self, cr, uid, context=None):
        
        res = {}
        lines = []
        emp_obj = self.pool.get('hr.employee')
        emp_ids = emp_obj.search(cr, uid, [('active','=',True)])
        for val in emp_obj.browse(cr, uid, emp_ids):
            lines.append(self._create_emp_lines(val))
        return lines
    
    def calculate_opening_balance(self, cr, uid, ids, context=None):
        salary_obj=self.browse(cr ,uid ,ids[0])
        emp_obj = self.pool.get('hr.employee')
        payment_obj= self.pool.get('payment.management.done')
        adjust_obj=self.pool.get('payment.management.previous.advance')
        month=salary_obj.month.month
        grand_total=0.0
        paid=0.0
        diff=0.0
        state = 'Done'
        for line1 in self.browse(cr, uid, ids):
            for line in line1.salary_payment_line:
                emp_id=line.employee_id
                month1=int(line.month)
                if len(str(month1)) == 1:
                    month1 = '0'+str(month1)
                year_id=line.year_id
                grand_total=line.rnd_grand_total
                cr.execute("select sum(paid) from payment_management_done  where month='"+str(line.month)+"' and year_id='"+str(line.year_id.id)+"' and employee_id = '"+str(line.employee_id.id)+"'")
                temp = cr.fetchall()
                for data in temp:
                    if data and data[0] != None:
                        paid = data[0]
                if paid == 0:
                    state = 'Exception'
                diff = grand_total - paid
#                print "year_id.............",year_id.name,type(year_id.name)
                date1=str(year_id.name) +"-"+ str(month1) +"-"+ "01"
                date2=datetime.strptime(date1,'%Y-%m-%d')
                newdate = (date2+ relativedelta(months = +1)).strftime('%Y-%m-%d')
                cr.execute("delete from payment_management_previous_advance where advance_date='"+str(newdate)+"' and employee_id='"+str(emp_id.id)+"' and paid='"+str(diff)+"'")
                result=adjust_obj.create(cr, uid, {'advance_date':newdate,'employee_id':emp_id.id,'paid':diff,'state':state})
        return True
            
    _columns = {
                'name':fields.function(_calculate_name,method=True,store=True,string='Name',type='char',size=64),
                'month':fields.many2one('holiday.list','Month',required=True),
                'year_id':fields.many2one('holiday.year','Year',required=True),
                'daily_salary_line':fields.one2many('daily.salary.line','salary_id','Salary Lines'),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT'),
                
                }
    
    _defaults = {
                 'salary_type':'Salary',
                 }

    _sql_constraints = [('unique_month_year','unique(month,year_id,salary_type)','Month for this Year is already define.')]
    
    def onchange_month(self, cr, uid, ids, month, context=None):
        res = {}
        if not month:
            res['value'] = {'year_id':False}
            return res
        month_obj = self.pool.get('holiday.list')
        month_data = month_obj.browse(cr, uid, month)
        if not month_data.year_id:
            res['warning'] = {'title': _('Warning'), 'message': _('Unable to process request, year is not selected in month.')}
        res['value'] = {'year_id':month_data.year_id and month_data.year_id.id or False}
        return res
    
    def calculate_department_salary(self, cr, uid, ids, context=None):
        res = {}
        salary_obj = self.pool.get('budget.salary.line')
        for each in self.browse(cr, uid, ids):
            cr.execute("select line.department_id, line.employee_id, dept.manager_id, sum(line.days), " \
            " sum(line.total_amount)  from daily_salary_line as line left join hr_department as dept " \
            " on (line.department_id=dept.id) where line.month = '"+str(each.month.month)+"' and line.year_id = " \
            "'"+str(each.year_id.id)+"' group by line.department_id, line.employee_id, dept.manager_id order by department_id")
            temp = cr.fetchall()
            
            cr.execute("delete from budget_salary_line where month = '"+str(each.month.month)+"' and year_id = " \
            "'"+str(each.year_id.id)+"'")
            
            for data in temp:
                
                ser_id = salary_obj.create(cr, uid, {'employee_id':data[1],'department_id':data[0],'manager_id':data[2],'days':data[3],'total_amount':data[4],
                            'month':each.month.month,'year_id':each.year_id and each.year_id.id or False})
                print("====================   NEW DATA IS CREATED   ================",ser_id)
            
            
            
            
        
    
    def calculate_payment(self, cr, uid, ids, context=None):
        res = {}
        lines = []
        emp_obj = self.pool.get('hr.employee')
        shift_obj = self.pool.get('hr.shift.line')
        dept_obj = self.pool.get('department.attendance.line')
        att_obj = self.pool.get('attendance.timing')
        salline_obj = self.pool.get('daily.salary.line')
        
        month = off_day = sunday = 0
        for line in self.browse(cr, uid, ids):
            if line.type:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('type','=',line.type)])
            else:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False)])
            if int(line.month.month) in [1,3,5,7,8,10,12]:
                month = 31
            if int(line.month.month) in [4,6,9,11]:
                month = 30
            if int(line.month.month) in [2]:
                if int(line.year_id.name) % 4 == 0:
                    month = 29
                else:
                    month = 28
            
            start_date = end_date = str(line.year_id.name)+'-'+str(line.month.month)+'-01'
            cr.execute("select max(name) from attendance_timing where DATE_PART('MONTH',name)='"+str(line.month.month)+"'") 
            temp_day = cr.fetchall()
            for dval in temp_day:
                if dval and dval[0] != None:
                    end_date = dval[0]
            new_wk_day = wk_day = 0
            
            if datetime.strptime(end_date,"%Y-%m-%d").date() >= datetime.strptime(start_date,"%Y-%m-%d").date():
                new_wk_day = datetime.strptime(end_date,"%Y-%m-%d").date() - datetime.strptime(start_date,"%Y-%m-%d").date() 
                new_wk_day = new_wk_day.days
                if new_wk_day >= 28:
                    new_wk_day = new_wk_day + 1 
            if line.salary_type == 'Kharcha':
                new_wk_day = 15
                end_date = str(line.year_id.name)+'-'+str(line.month.month)+'-15'
            next_date = datetime.strptime(start_date,"%Y-%m-%d")
            for i in range(new_wk_day):
                next_date1 = next_date.strftime('%Y-%m-%d')
                tm_tuple2 = datetime.strptime(next_date1,'%Y-%m-%d').timetuple()
                for sun in line.month.holiday_lines:
                    if datetime.strptime(next_date1,"%Y-%m-%d").date() == datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                        if sun.week == 'Sunday':
                            sunday += 1 
                        else:
                            off_day += 1
                next_date += timedelta(days=1)
                wk_day += 1
            
            working_day = wk_day - off_day - sunday
            working_day1 = working_day
            off_day1 = off_day
            sunday1 = sunday
            holiday_date = []
            
            for leave in line.month.holiday_lines:
                holiday_date.append(leave.leave_date)
                
            for val in emp_obj.browse(cr, uid, emp_ids):
                hrs = 0
                att_list = []
                
                working_day = working_day1
                off_day = off_day1
                sunday = sunday1
                emp_sunday = sunday
                joining = val.joining_date
                if joining and datetime.strptime(joining,"%Y-%m-%d").date() > datetime.strptime(start_date,"%Y-%m-%d").date():
                    working_day = 0
                    cur_wk_day = datetime.strptime(end_date,"%Y-%m-%d").date() - datetime.strptime(joining,"%Y-%m-%d").date()
                    working_day = cur_wk_day.days + 1
                    off_day = sunday = 0
                    for sun in line.month.holiday_lines:
                        if datetime.strptime(joining,"%Y-%m-%d").date() > datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                            if sun.week == 'Sunday':
                                sunday += 1 
                            else:
                                off_day += 1
                                
                
                day_remaining_amount = basic_part1 = basic_part2 = hrs = daily = OT_amt = 0.0
                total_amount = daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                salary = days = total_days = day = penalty = over_time = day_sal = total_OT = total_OT1 = over_time_amt = over_time_amt1 = daily_amt = 0.0
                
                prev_shift_ids = shift_obj.search(cr, uid, [('employee_id', '=', val.id)], limit=1, order='name DESC')
                if prev_shift_ids:
                    shift_data = shift_obj.browse(cr, uid, prev_shift_ids)[0]
                    for line1 in shift_data.shift_id.shift_line:
                        hrs = line1.shift_id.shift_line[0].working_time
                        if not hrs:
                            raise osv.except_osv(_('Warning !'),_("Working hours in not define in shift time of employee. "))
                else:
                    if val.shift_id and val.shift_id.shift_line:
                        hrs = val.shift_id.shift_line[0].working_time
                    if not hrs:
                        raise osv.except_osv(_('Warning !'),_("Working hours in not define in shift time of employee. "))
                        
                if val.monthly:
                    if val.salary > 4250:
                        basic_part2 = round(0.0329 * val.salary,0)
                        basic_part1 = val.salary - basic_part2
                        daily = basic_part1 / month
                        OT_amt = basic_part1 / (month * 8)
                    elif val.salary > 0:
                        basic_part1 = round(val.salary, 0)
                        daily = basic_part1 / month
                        OT_amt = basic_part1 / (month * 8)
                        
                        
                if val.daily:
                    if val.salary > 177:
                        basic_part2 = round(val.salary / working_day,0)
                        basic_part1 = val.salary - basic_part2
                        daily = basic_part1
                        OT_amt = basic_part1 / 8
                    elif val.salary > 0:
                        basic_part1 = round(val.salary, 0)
                        daily = basic_part1
                        OT_amt = basic_part1 / 8
                      
                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and (status is null or status in ('A_OK','B_Reduced','C_Dept_Absent'))")
                temp = cr.fetchall()
                for data in temp:
                    att_list.append(data[0])
                
                
                for att in att_obj.browse(cr, uid, att_list):
                    if att.working == 'P':
                        days = 1
                        day = 1
                        total_days = 1
                    elif att.working == 'HD':
                        days = 0.5
                        day = 0.5
                        total_days = 1
                    elif att.working == 'L':
                        days = 0
                        day = 0
                        total_days = 0
                    else:
                        days = 0
                        day = 0
                        total_days = 1
                
                    if val.salary > 0 and not val.daily and not val.monthly:
                        raise osv.except_osv(_('Warning !'), _('Tick daily or month for Pcard %s having salary greater than zero.') % (val.sinid))
                    
                    
                    daily_amt = round(days * daily,0)
                    salary = days * daily
                    TOTAL_PENALTY = TOTAL_SAL = CUTT_OFF = ALLOW_HR = DAILY_AMT = AMT_HR =  WORK_OT = SUN_OT = HALF_OT = HALF_OT_HR = TOTAL_OT = ACTUAL_OT = 0.0
                    
                    if att.name in holiday_date:
                        SUN_OT += att.over_time
                    else:
                        WORK_OT += att.over_time
                    TOTAL_PENALTY += att.penalty 
                    SUN_OT = round(SUN_OT,1)
                    WORK_OT = round(WORK_OT - TOTAL_PENALTY,1)
                    
                    
                    if val.monthly:
                        DAILY_AMT = round((val.salary / month) * days, 0)
                        AMT_HR = round(val.salary / (month * 8), 2) 
                    elif val.daily:
                        DAILY_AMT = round(val.salary  * days, 0)
                        AMT_HR = round(val.salary / 8, 2)
                    
                    TOTAL_SAL = daily_amt + (WORK_OT * OT_amt)  + (SUN_OT * OT_amt) + day_amount + day_remaining_amount 
                    
                    if val.salary >= 9000:
                        if (WORK_OT + SUN_OT) > 0:
                            WORK_OT = WORK_OT / 2
                    else:
                        if TOTAL_SAL > 9000:
                            if (WORK_OT + SUN_OT) > 0:
                                if DAILY_AMT > 9000:
                                     TOTAL_OT = WORK_OT / 2
                                     ACTUAL_OT = TOTAL_OT + SUN_OT
                                else:
                                    CUTT_OFF = 9000 - DAILY_AMT
                                    if CUTT_OFF > 0:
                                        ALLOW_HR = round(CUTT_OFF / AMT_HR,1)
                                    if ALLOW_HR:
                                        HALF_OT = round(WORK_OT - ALLOW_HR,1)
                                        HALF_OT_HR = round(HALF_OT / 2,1)
                                    ACTUAL_OT = round(SUN_OT + ALLOW_HR + HALF_OT_HR , 1)
                            else:        
                                ACTUAL_OT = WORK_OT + SUN_OT
                        
                    
                    
                    ACTUAL_OT = WORK_OT + SUN_OT
                    over_time = ACTUAL_OT
                    over_time_hr = divmod(over_time,1)[0]
                    over_time_min = round(divmod(over_time ,1)[1],2)
                    if over_time_min > 0.0 and over_time_min <= 0.25:
                         over_time_min = 0.0
                    elif over_time_min > 0.26 and over_time_min <= 0.50:
                         over_time_min = 0.50
                    elif over_time_min >= 0.50 and over_time_min <= 0.75:
                         over_time_min = 0.50
                    elif over_time_min > 0.75 and over_time_min <= 0.99:
                         over_time_min = 0.0
                         over_time_hr = over_time_hr + 1
                         
                    over_time = over_time_hr + over_time_min
                    ACTUAL_OT_AMT = over_time * OT_amt
                    over_time_amt = round(ACTUAL_OT_AMT,0)
                    
    
                    if days == 0:
                        total_amount = daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                        continue
                    department = False
                    count = total_timing_hr = 0
                    for dept1 in dept_obj.browse(cr, uid, dept_obj.search(cr, uid, [('att_date','=',att.name),('employee_id','=',val.id)])):
                        if dept1.out_datetime and dept1.in_datetime and datetime.strptime(str(dept1.out_datetime),'%Y-%m-%d %H:%M:%S') > datetime.strptime(str(dept1.in_datetime),'%Y-%m-%d %H:%M:%S'):
                            timing1 = datetime.strptime(str(dept1.out_datetime),'%Y-%m-%d %H:%M:%S') - datetime.strptime(str(dept1.in_datetime),'%Y-%m-%d %H:%M:%S')
                            if timing1.total_seconds() > 0:
                                timing_hr1 = timing1.total_seconds() / 3600
                            count += 1
                            total_timing_hr = total_timing_hr + timing_hr1
                    
                    for dept in dept_obj.browse(cr, uid, dept_obj.search(cr, uid, [('att_date','=',att.name),('employee_id','=',val.id)])):
                        timing = timing_hr = 0
                        department = dept.department_id and dept.department_id.id or False
                        if department and count > 1:
                            department = dept.department_id and dept.department_id.id or False
                            if datetime.strptime(str(dept.out_datetime),'%Y-%m-%d %H:%M:%S') > datetime.strptime(str(dept.in_datetime),'%Y-%m-%d %H:%M:%S'):
                                timing = datetime.strptime(str(dept.out_datetime),'%Y-%m-%d %H:%M:%S') - datetime.strptime(str(dept.in_datetime),'%Y-%m-%d %H:%M:%S')
                                if timing.total_seconds() > 0:
                                    timing_hr = timing.total_seconds() / 3600
                        else:
                            department = dept.department_id and dept.department_id.id or False
                        
                        daily_amt1 =  daily_amt
                        over_time_amt1 = over_time_amt
                        day_amount1 = day_amount
                        day_remaining_amount1 = day_remaining_amount
                        
                        daily_amt2 =  0.0
                        over_time_amt2 = 0.0
                        day_amount2 = 0.0
                        day_remaining_amount2 = 0.0
                        
                        if timing_hr > 0 and total_timing_hr > 0 and count > 1:
                            div_factor = (timing_hr / total_timing_hr)
                            daily_amt2 =  daily_amt1*div_factor
                            over_time_amt2 = over_time_amt1*div_factor
                            day_amount2 = day_amount1*div_factor
                            day_remaining_amount2 = day_remaining_amount1*div_factor
                        
                        
                        if daily_amt2 > 0:
                            total_amount = daily_amt2 + over_time_amt2 + day_amount2 + day_remaining_amount2
                            cr.execute("delete from daily_salary_line where employee_id ='"+str(val.id)+"' and month = '"+str(line.month.month)+"' and salary_id = '"+str(line.id)+"' and name = '"+str(att.name)+"' and department_id = '"+str(department)+"' and att_type = '"+str(dept.type)+"'")
                            salline_obj.create(cr, uid, {'name':att.name,'department_id':department,'salary_id':line.id,'year_id':line.year_id.id,'employee_id':val.id,'basic':val.salary,'basic_part1':basic_part1,
                            'basic_part2':basic_part2,'days':days,'days_amount':daily_amt2,'over_time':over_time,'overtime_amount':over_time_amt2,
                            'total_amount':total_amount,'month':line.month.month,'state':'Draft','salary_type':line.salary_type,'att_type':dept.type})
                            print "<----------------------------SALARY CALCULATED TRANSFER----------------------------------->",total_amount
                        else:    
                            total_amount = daily_amt + over_time_amt + day_amount + day_remaining_amount
                            cr.execute("delete from daily_salary_line where employee_id ='"+str(val.id)+"' and month = '"+str(line.month.month)+"' and salary_id = '"+str(line.id)+"' and name = '"+str(att.name)+"' and department_id = '"+str(department)+"' and att_type = '"+str(dept.type)+"'")
                            salline_obj.create(cr, uid, {'name':att.name,'department_id':department,'salary_id':line.id,'year_id':line.year_id.id,'employee_id':val.id,'basic':val.salary,'basic_part1':basic_part1,
                            'basic_part2':basic_part2,'days':days,'days_amount':daily_amt,'over_time':over_time,'overtime_amount':over_time_amt,
                            'total_amount':total_amount,'month':line.month.month,'state':'Draft','salary_type':line.salary_type,'att_type':dept.type})
                            print "<----------------------------SALARY CALCULATED----------------------------------->",total_amount
        return res
    
    def get_paid_salary(self, cr, uid, ids, context=None):
        res = {}
        tds_obj = self.pool.get('payment.management.tds')
        panalty_obj = self.pool.get('payment.management.panalty')
        advance_obj = self.pool.get('payment.management.advance')
        loan_obj = self.pool.get('payment.management.loan')
        line_obj = self.pool.get('salary.payment.line')
        for each in self.browse(cr, uid, ids):
            for val in each.salary_payment_line:
                rnd_grand_total = grand_total = tds = penalty = advance = loan = security = telephone = previous_advance = current_loan = 0.0 
                if each.salary_type == 'Salary':
                    cr.execute("select sum(tds) from payment_management_tds  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            tds = data[0]
                if each.salary_type == 'Salary':
                    cr.execute("select sum(amount) from payment_management_panalty  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            penalty = data[0]
                            
                if each.salary_type in ['Salary','Kharcha']:
                    cr.execute("select sum(total_amount) from payment_management_advance  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            advance = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(amount_emi) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            loan = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(paid) from payment_management_previous_advance  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            previous_advance = data[0]
                
                
                if each.salary_type == 'Salary':
                    cr.execute("select sum(balance_amount) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            current_loan = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(security) from payment_management_security  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            security = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(telephone) from payment_management_telephone  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            telephone = data[0]
               
                total=val.total_amount
                get_advance=advance
                get_penalty=penalty
                get_epf=tds
                get_loan=loan
                get_security=security
                get_telephone=telephone
                get_curr_loan=current_loan
                get_previous_advance=previous_advance
                if val.employee_id.salary > 0:
                    if get_curr_loan < 0:
                        raise osv.except_osv(_('Warning !'), _('Current loan can not be negative'))
                    if get_advance < 0:
                        raise osv.except_osv(_('Warning !'), _('Kharcha can not be negative'))
                    if get_penalty < 0:
                        raise osv.except_osv(_('Warning !'), _('Penalty can not be negative'))
                    if get_epf < 0:
                        raise osv.except_osv(_('Warning !'), _('EPF can not be negative'))
                    if get_loan < 0:
                        raise osv.except_osv(_('Warning !'), _('Loan amount can not be negative'))
                    if get_security < 0:
                        raise osv.except_osv(_('Warning !'), _('Security amount can not be negative'))
                    if get_telephone < 0:
                        raise osv.except_osv(_('Warning !'), _('Telephone amount can not be negative'))
                    grand_total=total - get_penalty - get_epf - get_advance - get_loan - get_security - get_telephone - previous_advance
                    rnd_grand_total = grand_total
                    rnd = grand_total % 10
                    if rnd > 0 and rnd < 3:
                        rnd_grand_total = grand_total - rnd
                    elif rnd > 2 and rnd < 5:
                        if rnd == 3:
                            rnd = 2
                        elif rnd == 4:
                            rnd = 1 
                        rnd_grand_total = grand_total + rnd
                    elif rnd > 5 and rnd < 8:
                        if rnd == 6:
                            rnd = 1
                        elif rnd == 7:
                            rnd = 2
                        rnd_grand_total = grand_total - rnd
                    elif rnd > 7:
                        if rnd == 8:
                            rnd = 2
                        elif rnd == 9:
                            rnd = 1 
                        rnd_grand_total = grand_total + rnd
                        
                    vals = { 
                             'previous_advance':previous_advance,   
                             'current_loan':current_loan,
                             'panalty':penalty,
                             'kharcha':advance,
                             'security':security,
                             'telephone':telephone,
                             'epf':tds,
                             'tds':0.0,
                             'loan':loan,
                             'grand_total':grand_total,
                             'rnd_grand_total':rnd_grand_total,
                             }
                    
                    line_obj.write(cr, uid, [val.id],vals)
                    
        return True

class daily_salary_line(osv.osv):
    _name = 'daily.salary.line'
    _order = 'employee_id,name'
    



    _columns = {
                'name':fields.date('Attendance Date',readonly=True),
                'salary_id':fields.many2one('daily.salary','Salary',ondelete="cascade"),
                'employee_id':fields.many2one('hr.employee','Employee',required=True,readonly=True),
                'department_id':fields.many2one('hr.department','Department',required=True,readonly=True),
                'basic':fields.float('Basic',digits_compute= dp.get_precision('Account'),readonly=True),
                'basic_part1':fields.float('Part 1',digits_compute= dp.get_precision('Account'),readonly=True),
                'basic_part2':fields.float('Part 2',digits_compute= dp.get_precision('Account'),readonly=True),
                'days':fields.float('Days',digits_compute= dp.get_precision('Account'),readonly=True),
                'days_amount':fields.float('Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'over_time':fields.float('O.T',digits_compute= dp.get_precision('Account'),readonly=True),
                'overtime_amount':fields.float('Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                
                'total_amount':fields.float('T Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'month':fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                ('8','August'),('9','September'),('10','October'),('11','November'),('12','December'),],'Month',readonly=True),
                'year_id':fields.many2one('holiday.year','Year',readonly=True),
                'state':fields.selection([('Draft','Draft'),('Paid','Paid')],'Status',readonly=True),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia')],string='Type',type="selection",readonly=True),
                'employee_type':fields.related('employee_id','employee_type',selection=[('employee','Employees'), ('artisian','Artisian'),('contractor','Inhouse Contractors')],string='Employee Type',type="selection",readonly=True),
                'att_type':fields.selection([('Departmental','Departmental'),('Transfered','Transfered')],'Type',required=True),
                }
    
    _defaults = {
                 'state':'Draft',
                 }

    _sql_constraints = [('unique_employee_month_year','unique(name,employee_id,department_id,month,year_id,att_type)','Employee salary line for this month and year is already exist.')]
    
    
    def unlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for line in order:
            if line['state'] in ['Draft']:
                unlink_ids.append(line['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete Paid Salary.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class budget_salary_line(osv.osv):
    _name = 'budget.salary.line'
    _order = 'employee_id,department_id'
    



    _columns = {
                
                'employee_id':fields.many2one('hr.employee','Employee',required=True,readonly=True),
                'department_id':fields.many2one('hr.department','Department',required=True,readonly=True),
                'manager_id':fields.many2one('hr.employee','Reporting Officer',required=True,readonly=True),
                'days':fields.float('Days',digits_compute= dp.get_precision('Account'),readonly=True),
                'total_amount':fields.float('T Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'month':fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                ('8','August'),('9','September'),('10','October'),('11','November'),('12','December'),],'Month',readonly=True),
                'year_id':fields.many2one('holiday.year','Year',readonly=True),
                'state':fields.selection([('Draft','Draft'),('Paid','Paid')],'Status',readonly=True),
                'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia')],string='Type',type="selection",readonly=True),
                'employee_type':fields.related('employee_id','employee_type',selection=[('employee','Employees'), ('artisian','Artisian'),('contractor','Inhouse Contractors')],string='Employee Type',type="selection",readonly=True),
                
                }
    
    _defaults = {
                 'state':'Draft',
                 }

    _sql_constraints = [('unique_employee_month_year','unique(employee_id,department_id,month,year_id)','Employee salary line for this month and year is already exist.')]
    
    
    def unlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for line in order:
            if line['state'] in ['Draft']:
                unlink_ids.append(line['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete Paid Salary.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
