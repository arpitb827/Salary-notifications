
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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
import base64, urllib
import csv
import cStringIO
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf

class salary_payment(osv.osv):
    _name = 'salary.payment'
    
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
        
        lines = []
        emp_obj = self.pool.get('hr.employee')
        emp_ids = emp_obj.search(cr, uid, [('active','=',True)])
        for val in emp_obj.browse(cr, uid, emp_ids):
            lines.append(self._create_emp_lines(val))
        return lines
    
    def calculate_opening_balance(self, cr, uid, ids, context=None):
        adjust_obj=self.pool.get('payment.management.previous.advance')
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
                cr.execute("select sum(paid) from payment_management_done  where month='"+str(line.month)+"' and year_id='"+str(line.month.year_id.id)+"' and employee_id = '"+str(line.employee_id.id)+"'")
                temp = cr.fetchall()
                for data in temp:
                    if data and data[0] != None:
                        paid = data[0]
                if paid == 0:
                    state = 'Exception'
                diff = grand_total - paid
                date1=str(year_id.name) +"-"+ str(month1) +"-"+ "01"
                date2=datetime.strptime(date1,'%Y-%m-%d')
                newdate = (date2+ relativedelta(months = +1)).strftime('%Y-%m-%d')
                cr.execute("delete from payment_management_previous_advance where advance_date='"+str(newdate)+"' and employee_id='"+str(emp_id.id)+"' and paid='"+str(diff)+"'")
                adjust_obj.create(cr, uid, {'advance_date':newdate,'employee_id':emp_id.id,'paid':diff,'state':state})
        return True
    
    def calculate_loan_balance(self, cr, uid, ids, context=None):
        sal_line_obj=self.pool.get('salary.payment.line')
        loan_line_obj=self.pool.get('loan.deduction.line')
        for each in self.browse(cr, uid, ids):
            month = int(each.month.month)
            year = int(each.month.year_id.name)
            if month == 12:
                year += 1
                month = 0
            month += 1
            check_date = str(year)+'-'+str(month)+'-20'
            if datetime.strptime(check_date,'%Y-%m-%d') < datetime.strptime(time.strftime(DEFAULT_SERVER_DATE_FORMAT),'%Y-%m-%d'):
                for line in each.salary_payment_line:
                    if line.salary_type == 'Salary':
                        cr.execute("select line.id from loan_deduction_line as line left join loan_deduction as " \
                                   "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                                   "where holi.month='"+str(each.month.month)+"' and holi.year_id='"+str(each.month.year_id.id)+"' and loan.emp_id='"+str(line.employee_id.id)+"' and line.state='not_paid'")

                        temp = cr.fetchall()
                        for data in temp:
                            if data and data[0] != None:
                                print "<------------------- EMI CALCULATION FOR EMPLOYEE ------------->",line.employee_id.name
                                loan_line_obj.balance_paid(cr, uid, [data[0]], context)
                                sal_line_obj.write(cr, uid, [line.id], {'state':'Paid'})
                                
                    
            else:
                raise osv.except_osv(_('Warning !'),_("You cannot deduct loan EMI, to do so please wait till date 20."))
        return True
    
    def _calculate_no_of_employee(self, cr, uid, ids, name, args, context=None):
         
        res = {}
        for val in self.browse(cr, uid, ids):
            count = 0
            for val1 in val.salary_payment_line:
                count = count + 1
            res[val.id] = count
        return res
    
    def _calculate_total_amt(self, cr, uid, ids, name, args, context=None):
         
        res = {}
        for val in self.browse(cr, uid, ids):
            total = 0
            for val1 in val.salary_payment_line:
                total = total + val1.total_amount
            res[val.id] = total
            
        return res
            
    _columns = {
                'name':fields.function(_calculate_name,method=True,store=True,string='Name',type='char',size=64),
                'month':fields.many2one('holiday.list','Month',required=True),
                'year_id':fields.many2one('holiday.year','Year',required=True),
                'salary_payment_line':fields.one2many('salary.payment.line','salary_id','Holiday Lines'),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT'),
                'employee_id':fields.many2one('hr.employee','Employee'),
                'not_sheet':fields.boolean('Not In Sheet'),
                'no_of_employee':fields.function(_calculate_no_of_employee,method=True,string='No. of Employee',type='char',size=64,store=True),
                'total_amt':fields.function(_calculate_total_amt,method=True,string='Total Amount',type='float',store=True),
                }
    
    _defaults = {
                 'salary_type':'Salary',
                 'not_sheet':False,
                 }

    _sql_constraints = [('unique_month_year','unique(month,year_id,salary_type,type)','Salary payment for this month, year and work at is already define.')]
    
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
    
    def calculate_payment(self, cr, uid, ids, context=None):
        res = {}
        emp_obj = self.pool.get('hr.employee')
        shift_obj = self.pool.get('hr.shift.line')
        att_obj = self.pool.get('attendance.timing')
        salline_obj = self.pool.get('salary.payment.line')
        counter = 1
        
        month = off_day = sunday = off_day1 = sunday1 = 0
        for line in self.browse(cr, uid, ids):
            not_sheet = False
            if line.type and line.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('type','=',line.type),('id','=',line.employee_id.id)])
            elif line.type and not line.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('type','=',line.type)])
            elif not line.type and line.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('id','=',line.employee_id.id)])
            elif line.not_sheet:
                if not line.employee_id:
                    raise osv.except_osv(_('Warning !'),_("Not In Sheet option work only with employee, please select employee. "))
                not_sheet = True
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('id','=',line.employee_id.id)])
            else:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False)])
            if int(line.month.month) in [1,3,5,7,8,10,12]:
                month = 31
            if int(line.month.month) in [4,6,9,11]:
                month = 30
            if int(line.month.month) in [2]:
                if int(line.month.year_id.name) % 4 == 0:
                    month = 29
                else:
                    month = 28
            start_date = end_date = str(line.month.year_id.name)+'-'+str(line.month.month)+'-01'
            cr.execute("select max(name) from attendance_timing where DATE_PART('MONTH',name)='"+str(line.month.month)+"' and DATE_PART('YEAR',name)='"+str(line.month.year_id.name)+"'") 
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
            
            next_date = datetime.strptime(start_date,"%Y-%m-%d")
            for i in range(month):
                next_date1 = next_date.strftime('%Y-%m-%d')
                for sun in line.month.holiday_lines:
                    if datetime.strptime(next_date1,"%Y-%m-%d").date() == datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                        if sun.week == 'Sunday':
                            sunday += 1 
                        else:
                            off_day += 1
                next_date += timedelta(days=1)
                wk_day += 1 
            daily_part =  month - off_day - sunday
            next_date = datetime.strptime(start_date,"%Y-%m-%d")
            if line.salary_type == 'Kharcha':
                off_day = sunday = wk_day = 0
                new_wk_day = 15
                end_date = str(line.month.year_id.name)+'-'+str(line.month.month)+'-15'
            
                for i in range(new_wk_day):
                    next_date1 = next_date.strftime('%Y-%m-%d')
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
            tot_hol=0.0
            for leave in line.month.holiday_lines:
                holiday_date.append(leave.leave_date)
            tot_hol=len(holiday_date)    
#            inc_obj=self.pool.get('employee.salary')
            for val in emp_obj.browse(cr, uid, emp_ids):
                    total_wk_days=0.0
                    month1=0.0
#                inc_ids=inc_obj.search(cr, uid, [('employee_id','=',val.id),('increment_date','>=','2014-05-31'),('state','=','done')])
#                if inc_ids:
                    working_day = working_day1
                    if val.monthly:
                        off_day = off_day1
                        sunday = sunday1
                        emp_sunday = sunday
                        joining = val.joining_date
                        if joining and datetime.strptime(joining,"%Y-%m-%d").date() > datetime.strptime(start_date,"%Y-%m-%d").date():
                            working_day = 0
                            cur_wk_day = datetime.strptime(end_date,"%Y-%m-%d").date() - datetime.strptime(joining,"%Y-%m-%d").date()
                            if cur_wk_day:
                                working_day = cur_wk_day.days + 1
                                off_day = sunday = 0
                                for sun in line.month.holiday_lines:
                                    if datetime.strptime(joining,"%Y-%m-%d").date() < datetime.strptime(sun.leave_date,"%Y-%m-%d").date() and datetime.strptime(end_date,"%Y-%m-%d").date() >= datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                                        if sun.week == 'Sunday':
                                            sunday += 1 
                                        else:
                                            off_day += 1
                                working_day = working_day - off_day - sunday
                            else:
                                continue
                        if emp_sunday <> sunday:
                            emp_sunday = sunday
                     
                    hrs = 0
                    att_list = []
                    
                    day_remaining_amount = basic_part1 = basic_part2 = hrs = daily = OT_amt = 0.0
                    total_amount = daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                    salary = days = total_days = over_time = over_time_amt = daily_amt = 0.0
                    
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
                            if daily_part > 0:
                                basic_part2 = round(val.salary / daily_part,0)
                                basic_part1 = val.salary - basic_part2
                                daily = basic_part1
                                OT_amt = basic_part1 / 8
                        elif val.salary > 0:
                            basic_part1 = round(val.salary, 0)
                            daily = basic_part1
                            OT_amt = basic_part1 / 8
                            
                    
    #                salary = days = total_days = day = penalty = over_time = day_sal = total_OT = total_OT1 = over_time_amt = over_time_amt1 = daily_amt = 0.0
                            
    #                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and status <> 'D_Miss_Punch'")
                    
                    if line.salary_type == 'Kharcha':
                        if val.type in ['Wood','Metal']:
                            if val.id in [9654,9658,11244,9700,9695,9679,9853,10817,10150,20825]:
                                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"'  and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                            else:    
                                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced')) and dept_status='OK' ")
                                
                        else:
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                    else:
                        if val.type in ['Wood','Metal']:
                            if val.id in [9654,9658,11244,9700,9695,9679,9853,10817,15951,10150,20825]:
                                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                            else:    
                                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced')) and dept_status='OK' ")
                                
                        else:
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
    #                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        att_list.append(data[0])
                    
    #                 tick = False
    #                 for rec in att_obj.browse(cr, uid, att_list):
    #                     if rec.employee_id.type in ['Wood','Metal']:
    #                         if datetime.strptime(rec.name,'%Y-%m-%d') == datetime.strptime('2013-05-13','%Y-%m-%d'):
    #                             days = 0
    #                             tick = False
    #                             total_days = 0
    #                             break
    #                         else:
    #                             days = 1
    #                             total_days = 1
    #                             tick = True
                    
                    
                    for rec in att_obj.browse(cr, uid, att_list):
                        
                        if rec.working == 'P':
                            days += 1
                            total_days += 1
                        elif rec.working == 'HD':
                            days += 0.5
                            total_days += 1
                        elif rec.working == 'L':
                            days += 0
                            total_days += 0
                        else:
                            days += 0
                            total_days += 1
                    if val.salary > 0 and not val.daily and not val.monthly:
                        raise osv.except_osv(_('Warning !'), _('Tick daily or month for Pcard %s having salary greater than zero.') % (val.sinid))
                    
                    
                    if line.salary_type == 'Kharcha':
                    
                        day_amount = 0.0
                        day_remaining_amount = 0.0
                                 
                        
                        if val.monthly:
                            if emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 24:
                                emp_sunday = emp_sunday - 6
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 20:
                                emp_sunday = emp_sunday - 5
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 16:
                                emp_sunday = emp_sunday - 4
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 12:
                                emp_sunday = emp_sunday - 3
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 8:
                                emp_sunday = emp_sunday - 2
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 4:
                                emp_sunday = emp_sunday - 1
                            
                            
                            if days < 0:
                                days = 0
                                
                            if days > 0:
                                days = days + off_day + emp_sunday
                    else:
                        if val.daily:
                            if basic_part2:
                                if days >= 22:
                                    day_amount = basic_part1
                                else:
                                    day_amount = 0.0
                            else:
                                day_amount = 0.0
                            
                            if days >= working_day:
                                day_remaining_amount = basic_part1
                            else:
                                day_remaining_amount = 0.0
                                
                                 
                        if val.monthly:
                            if emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 24:
                                emp_sunday = emp_sunday - 6
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 20:
                                emp_sunday = emp_sunday - 5
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 16:
                                emp_sunday = emp_sunday - 4
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 12:
                                emp_sunday = emp_sunday - 3
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 8:
                                emp_sunday = emp_sunday - 2
                            elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 4:
                                emp_sunday = emp_sunday - 1
                            
                            
                            if days < 0:
                                days = 0
                                
                            if days > 0:
                                days = days + off_day + emp_sunday
                            if basic_part2:
                                if days >= 22:
                                    day_amount = basic_part2
                                else:
                                    day_amount = 0.0
                            else:
                                day_amount = 0.0
                            
                            if days >= month:
                                if basic_part2:
                                    day_remaining_amount = basic_part2
                                else:
                                    day_remaining_amount = round(daily,0)
                            else:
                                day_remaining_amount = 0.0
                                
                        if days >= month:
                            days = month
                            day_remaining_amount = day_remaining_amount
                            
            
                        
    #                 if tick:
    #                     days -= 1
                
                    daily_amt = round(days * daily,0)
                    salary = days * daily
                    TOTAL_PENALTY = TOTAL_SAL = CUTT_OFF = ALLOW_HR = DAILY_AMT = AMT_HR =  WORK_OT = SUN_OT = HALF_OT = HALF_OT_HR = TOTAL_OT = ACTUAL_OT = 0.0
                    for rec in att_obj.browse(cr, uid, att_list):
                        if rec.name in holiday_date:
                            SUN_OT += rec.over_time
                        else:
                            WORK_OT += rec.over_time
                        TOTAL_PENALTY += rec.penalty
                    SUN_OT = round(SUN_OT,1)
                    WORK_OT = round(WORK_OT - TOTAL_PENALTY,1)
                    if val.category5 == 'A':
                        if WORK_OT > 0 :  
                            WORK_OT = WORK_OT/2
                        else:
                            WORK_OT = WORK_OT
                    else:    
                        WORK_OT = WORK_OT 
                    if val.monthly:
                        DAILY_AMT = daily_amt
                        AMT_HR = OT_amt
                    elif val.daily:
                        DAILY_AMT = daily_amt
                        AMT_HR = OT_amt
                    
                    TOTAL_SAL = daily_amt + (WORK_OT * OT_amt)  + (SUN_OT * OT_amt) + day_amount + day_remaining_amount 
                    if val.category7:
                        if val.salary >= 9000:
                            if (WORK_OT) > 0:
                                WORK_OT = WORK_OT
                            ACTUAL_OT = WORK_OT + SUN_OT
                        else:
                            if TOTAL_SAL > 9000:
                                if (WORK_OT) > 0:
                                    if DAILY_AMT > 9000:
                                        TOTAL_OT = WORK_OT
                                        ACTUAL_OT = TOTAL_OT + SUN_OT
                                    else:
                                        CUTT_OFF = 9000 - DAILY_AMT
                                        if CUTT_OFF > 0:
                                            ALLOW_HR = round(CUTT_OFF / AMT_HR,1)
                                        if ALLOW_HR and WORK_OT > ALLOW_HR:
                                            HALF_OT = round(WORK_OT - ALLOW_HR,1)
                                            HALF_OT_HR = round(HALF_OT,1)
                                            ACTUAL_OT = round(SUN_OT + ALLOW_HR + HALF_OT_HR , 1)
                                        else:
                                            ACTUAL_OT = round(SUN_OT + WORK_OT, 1)
                                        
                                else:        
                                    ACTUAL_OT = WORK_OT + SUN_OT
                            
                        
                            else:
                                ACTUAL_OT = WORK_OT + SUN_OT
                    else:
                        if val.salary >= 9000:
                            if (WORK_OT) > 0:
                                WORK_OT = WORK_OT / 2
                            ACTUAL_OT = WORK_OT + SUN_OT
                        else:
                            if TOTAL_SAL > 9000:
                                if (WORK_OT) > 0:
                                    if DAILY_AMT > 9000:
                                        TOTAL_OT = WORK_OT / 2
                                        ACTUAL_OT = TOTAL_OT + SUN_OT
                                    else:
                                        CUTT_OFF = 9000 - DAILY_AMT
                                        if CUTT_OFF > 0:
                                            ALLOW_HR = round(CUTT_OFF / AMT_HR,1)
                                        if ALLOW_HR and WORK_OT > ALLOW_HR:
                                            HALF_OT = round(WORK_OT - ALLOW_HR,1)
                                            HALF_OT_HR = round(HALF_OT / 2,1)
                                            ACTUAL_OT = round(SUN_OT + ALLOW_HR + HALF_OT_HR , 1)
                                        else:
                                            ACTUAL_OT = round(SUN_OT + WORK_OT, 1)
                                        
                                else:        
                                    ACTUAL_OT = WORK_OT + SUN_OT
                            
                        
                            else:
                                ACTUAL_OT = WORK_OT + SUN_OT
    #                    elif salary < 9000:
    #                        total_OT = OT_amt * (rec.over_time - rec.penalty)
    #                        over_time = over_time + rec.over_time - rec.penalty
    #                        salary = salary  + total_OT
    #                        over_time_amt += total_OT
    #                        
    #                    else:
    #                        total_OT = OT_amt  * (rec.over_time/2 - rec.penalty)
    #                        over_time = over_time + rec.over_time/2 - rec.penalty
    #                        salary = salary  + total_OT
    #                        over_time_amt += total_OT
                            
                            
    #                if salary > 9000 and val.monthly and hrs == 10.0:
    #                    over_time_amt +=  OT_amt
    #                    over_time += 1
    #                if salary > 0 and salary < 9000 and val.monthly and hrs == 10.0:
    #                over_time += total_OT1
    #                over_time_amt += over_time_amt1
                    
                    extra_over_time = 0.0
                    if line.salary_type == 'Salary':
                        if salary > 0 and val.monthly and hrs == 10.0:
                            extra_over_time = 2
                            
                    over_time = ACTUAL_OT + extra_over_time
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
                    
    #                if basic_part1 == 0:
    #                    total_amount = daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                    
                    if days <= 0:
                        total_amount = daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                        
                    if val.daily:
                        month1=month-tot_hol
                        total_wk_days=days
                    else:
                        month1=month 
                        total_wk_days= days-tot_hol  
                    total_amount = daily_amt + over_time_amt + day_amount + day_remaining_amount
                    if not_sheet:
                        if val.id:
                            raise osv.except_osv(_('Warning !'), _('Employee salary line already exist, invalid option selected Not In Sheet.'))
                        salline_obj.create(cr, uid, {'salary_id':line.id,'year_id':line.month.year_id.id,'employee_id':val.id,'basic':val.salary,'basic_part1':basic_part1,
                        'basic_part2':basic_part2,'total_day':month1,'total_wk_day':total_wk_days,'holiday':tot_hol,'leaves':(month1-days),'days':days,'days_amount':daily_amt,'over_time':over_time,'overtime_amount':over_time_amt,'reason':'Punch not present in JBS','not_sheet':line.not_sheet,
                        'day_amount':day_amount,'day_remaining_amount':day_remaining_amount,'total_amount':total_amount,'month':line.month.month,'state':'Draft','salary_type':line.salary_type,'year':line.month.year_id.name,'curr_department':val.department_id.id})
                        print "<----------------------------SALARY CALCULATED----------------------------------->",counter,total_amount
                    else:
                        cr.execute("delete from salary_payment_line where employee_id ='"+str(val.id)+"' and month = '"+str(line.month.month)+"' and salary_id = '"+str(line.id)+"'")
                        salline_obj.create(cr, uid, {'salary_id':line.id,'year_id':line.month.year_id.id,'employee_id':val.id,'basic':val.salary,'basic_part1':basic_part1,
                        'basic_part2':basic_part2,'days':days,'total_day':month1,'total_wk_day':total_wk_days,'holiday':tot_hol,'leaves':(month1-days),'days_amount':daily_amt,'over_time':over_time,'overtime_amount':over_time_amt,
                        'day_amount':day_amount,'day_remaining_amount':day_remaining_amount,'total_amount':total_amount,'month':line.month.month,'state':'Draft','salary_type':line.salary_type,'year':line.month.year_id.name,'curr_department':val.department_id.id})
                        print "<----------------------------SALARY CALCULATED----------------------------------->",counter,total_amount
                    counter += 1
        return res
    
    def get_paid_salary(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('salary.payment.line')
        emp_obj = self.pool.get('hr.employee')
        counter = 1
        loan12 = ''
        for each in self.browse(cr, uid, ids):
            if each.type and each.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('type','=',each.type),('id','=',each.employee_id.id)])
            elif each.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('id','=',each.employee_id.id)])
            elif each.type:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False),('type','=',each.type)])
            else:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('shift_lines','!=',False)])
            for val in line_obj.browse(cr, uid, line_obj.search(cr, uid, [('employee_id','in',emp_ids),('salary_id','=',each.id)])):
                rnd_grand_total = grand_total = tds = epf = chk = conveyance = penalty = advance = loan = security = telephone = previous_advance = current_loan = 0.0 
                if each.salary_type == 'Salary':
                    cr.execute("select sum(conveyance) from payment_management_conveyance  where employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            conveyance = data[0]
                
                if each.salary_type == 'Salary':
                    cr.execute("select sum(tds) from payment_management_tds  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            tds = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(epf) from payment_management_epf  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            epf = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(check_amt) from employee_check_deduction  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            chk = data[0]            
                            
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
                    cr.execute("select max(line.loan_line_amt) from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(each.month.month)+"' and holi.year_id='"+str(val.year_id.id)+"' and loan.emp_id='"+str(val.employee_id.id)+"' and loan.state='done'")
#                    cr.execute("select max(amount_emi) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            loan = data[0]
                            
                if each.salary_type == 'Salary':
                    cr.execute("select line.state from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(each.month.month)+"' and holi.year_id='"+str(val.year_id.id)+"' and loan.emp_id='"+str(val.employee_id.id)+"' and loan.state='done'")
#                    cr.execute("select max(amount_emi) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            loan12 = data[0]
                            
                            
                if each.salary_type == 'Salary':
                    cr.execute("select sum(paid) from payment_management_previous_advance  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            previous_advance = data[0]
                
                
                if each.salary_type == 'Salary':
                    cr.execute("select sum(loan.balance) from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(each.month.month)+"' and holi.year_id='"+str(val.year_id.id)+"' and loan.emp_id='"+str(val.employee_id.id)+"' and loan.state='done'")
#                    cr.execute("select sum(balance_amount) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
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
                get_epf=epf
                get_chk=chk
                get_tds=tds
                get_loan=loan
                get_conveyance=conveyance
                get_security=security
                get_telephone=telephone
                get_curr_loan=current_loan
                get_previous_advance=previous_advance
                if val.days <= 0 and not (get_advance or get_penalty or get_epf or get_chk or get_tds or get_loan or get_conveyance or get_security or get_telephone or get_curr_loan or get_previous_advance):   
                    cr.execute("delete from salary_payment_line where id = '"+str(val.id)+"'")
                    continue
                if get_curr_loan < 0:
                    raise osv.except_osv(_('Warning !'), _('Current loan can not be negative'))
                if get_advance < 0:
                    raise osv.except_osv(_('Warning !'), _('Kharcha can not be negative'))
                if get_penalty < 0:
                    raise osv.except_osv(_('Warning !'), _('Penalty can not be negative'))
                if get_tds < 0:
                    raise osv.except_osv(_('Warning !'), _('TDS can not be negative'))
                if get_conveyance < 0:
                    raise osv.except_osv(_('Warning !'), _('Conveyance can not be negative'))
                if get_epf < 0:
                    raise osv.except_osv(_('Warning !'), _('EPF can not be negative'))
                if get_chk < 0:
                    raise osv.except_osv(_('Warning !'), _('Chk amt can not be negative'))
                if get_loan < 0:
                    raise osv.except_osv(_('Warning !'), _('Loan amount can not be negative'))
                if get_security < 0:
                    raise osv.except_osv(_('Warning !'), _('Security amount can not be negative'))
                if get_telephone < 0:
                    raise osv.except_osv(_('Warning !'), _('Telephone amount can not be negative'))
                if loan12 == 'stop':
                    grand_total=total - get_penalty - get_tds - get_epf - get_chk + get_conveyance - get_advance - get_security - get_telephone - previous_advance
                else:    
                    grand_total=total - get_penalty - get_tds - get_epf - get_chk + get_conveyance - get_advance - get_loan - get_security - get_telephone - previous_advance
                rnd_grand_total = grand_total
                rnd = grand_total % 10
                if rnd >= 0 and rnd < 3:
                    rnd_grand_total = grand_total - rnd
                elif rnd > 2 and rnd < 6:
                    if rnd == 3:
                        rnd = 2
                    elif rnd == 4:
                        rnd = 1 
                    else:
                        rnd = 0
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
                    
                if each.salary_type == 'Kharcha':
                    rnd_grand_total = int(math.ceil(rnd_grand_total / 100.0)) * 100
                if loan12 == 'stop':  
                    vals = { 
                             'previous_advance':previous_advance,   
                             'panalty':penalty,
                             'kharcha':advance,
                             'security':security,
                             'telephone':telephone,
                             'conveyance':conveyance,
                             'epf':epf,
                             'chk_amt':chk,
                             'tds':tds,
                             'grand_total':grand_total,
                             'rnd_grand_total':rnd_grand_total,
                             }
                else:     
                    vals = { 
                             'previous_advance':previous_advance,   
                             'current_loan':current_loan,
                             'panalty':penalty,
                             'kharcha':advance,
                             'security':security,
                             'telephone':telephone,
                             'conveyance':conveyance,
                             'epf':epf,
                             'chk_amt':chk,
                             'tds':tds,
                             'loan':loan,
                             'grand_total':grand_total,
                             'rnd_grand_total':rnd_grand_total,
                             }
                
                line_obj.write(cr, uid, [val.id],vals)
                print "<--------------------------------PROCESSING---------------------------------->",counter,val.employee_id.sinid
                counter += 1
        return True

class salary_payment_line(osv.osv):
    _name = 'salary.payment.line'
    _order = 'employee_id'
    



    _columns = {
                'salary_id':fields.many2one('salary.payment','Salary',ondelete="cascade"),
                'wiz_salary_id':fields.many2one('wiz.salary.payment','Salary'),
                'employee_id':fields.many2one('hr.employee','Employee',required=True,readonly=True),
#                 'department_id':fields.related('employee_id','department_id',relation='hr.department',string='Department',type="many2one",readonly=True),
                'curr_department':fields.many2one('hr.department',string='Department'),               
                'basic':fields.float('Basic',digits_compute= dp.get_precision('Account'),readonly=True),
                'basic_part1':fields.float('Part 1',digits_compute= dp.get_precision('Account'),readonly=True),
                'basic_part2':fields.float('Part 2',digits_compute= dp.get_precision('Account'),readonly=True),
                'days':fields.float('Days',digits_compute= dp.get_precision('Account'),readonly=True),
                'days_amount':fields.float('Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'over_time':fields.float('O.T',digits_compute= dp.get_precision('Account'),readonly=True),
                'overtime_amount':fields.float('Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'day_amount':fields.float('1 Day Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'day_remaining_amount':fields.float('1 Day R.Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'total_amount':fields.float('T Amt',digits_compute= dp.get_precision('Account'),readonly=True),
                'month':fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                ('8','August'),('9','September'),('10','October'),('11','November'),('12','December'),],'Month',readonly=True),
                'year_id':fields.many2one('holiday.year','Year',readonly=True),
                
                'previous_advance':fields.float('Prev. Adv.',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'current_loan':fields.float('Curr. Loan',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                                
                'panalty':fields.float('Penalty',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'security':fields.float('Security',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'telephone':fields.float('Telephone',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'loan':fields.float('Loan EMI',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'kharcha':fields.float('Kharcha',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'epf':fields.float('EPF',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'tds':fields.float('TDS',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'conveyance':fields.float('Conv. Ded.',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'reward':fields.float('Reward',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'grand_total':fields.float('Grd Total',digits_compute= dp.get_precision('Account'),readonly=True),
                'rnd_grand_total':fields.float('Rnd Grd Total',digits_compute= dp.get_precision('Account'), readonly=True),
                'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True,store=True),
                'employee_type':fields.related('employee_id','employee_type',selection=[('employee','Employees'), ('artisian','Artisian'),('contractor','Inhouse Contractors')],string='Employee Type',type="selection",readonly=True,store=True),
                'difference':fields.integer('Difference',digits_compute= dp.get_precision('Account'),readonly=True,states={'Ready':[('readonly',False)]}),
                'reason':fields.char('Reason',size=255,readonly=True,states={'Ready':[('readonly',False)]}),
                'state':fields.selection([('Draft','Draft'),('Ready','Ready'),('Paid','Paid')],'Status',readonly=True),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'complaince':fields.related('employee_id','complaince',type="boolean",string='Type Of Employee', select=True,store=True),
                'not_sheet':fields.boolean('Not In Sheet',readonly=True),
                'salary_editted':fields.boolean('Salary Editted',readonly=True),
                'religion_id':fields.related('employee_id','religion',type="selection",selection=[('hindu', 'Hindu'),('muslim', 'Muslim'),('sikh', 'Sikh'),('isai', 'Isai'),('other', 'Other')],string='Religion', select=True,store=False),
                'total_day':fields.float('Total Days'),
                'total_wk_day':fields.float('Total Working Days'),
                'holiday':fields.float('Holiday'),
                'leaves':fields.float('Leaves'),
                'chk_amt':fields.float('CHK AMT'),
                'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
                }
    
    _defaults = {
                 'state':'Draft',
                 'panalty':0.0,
                 'kharcha':0.0,
                 'epf':0.0,
                 'tds':0.0,
                 'loan':0.0,
                 'reward':0.0,
                 'previous_advance':0.0,
                 'current_loan':0.0,
                 'conveyance':0.0,
                 'not_sheet':False,
                 'salary_editted':False,
                 'year':time.strftime('%Y')
                 }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id,salary_type)','Employee salary line for this month and year is already exist.')]
    
    
    def unlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for line in order:
            if line['state'] in ['Draft']:
                unlink_ids.append(line['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete Salary Line.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def payment_done(self, cr, uid, ids, context=None):
        loan_line_obj = self.pool.get('loan.deduction.line')
        adv_obj = self.pool.get('payment.management.previous.advance')
        for each in self.browse(cr, uid, ids):
            if each.salary_type == 'Salary':
                
                    
                if not each.difference:
                    raise osv.except_osv(_('Invalid action !'), _('You cannot paid zero entry, please enter valid amount.!'))
                else:
                    cr.execute("select line.id from loan_deduction_line as line left join loan_deduction as " \
                           "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                           "where line.loan_line_amt='"+str(each.loan)+"' and holi.month='"+str(each.month)+"'" \
                           "and holi.year_id='"+str(each.year_id.id)+"' and loan.emp_id='"+str(each.employee_id.id)+"' and line.state='not_paid' limit 1")

                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            loan_line_obj.balance_paid(cr, uid, [data[0]], context)
              
                    
                    if each.rnd_grand_total > each.difference:
                        total = each.rnd_grand_total - each.difference
                        adv = {
                          'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                          'advance_date':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                          'employee_id':each.employee_id.id,
                          'month':each.month,
                          'year_id':each.employee_id.id,
                          'paid':total,
                          'user_id':uid,
                          'state':'done',
                          }
                        adv_obj.create(cr, uid, adv)
                        
                    if each.rnd_grand_total < each.difference:
                        total = each.difference - each.rnd_grand_total 
                        adv = {
                          'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                          'advance_date':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                          'employee_id':each.employee_id.id,
                          'month':each.month,
                          'year_id':each.employee_id.id,
                          'paid':-total,
                          'user_id':uid,
                          'state':'done',
                          }
                        adv_obj.create(cr, uid, adv)
                        
                        
                        
                    self.write(cr, uid, ids, {'state':'Paid'})
        return True
    
    
    def payment_reset(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Draft'})
        return True
    
class payment_management_advance(osv.osv):
    _name='payment.management.advance'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'advance_date' in vals and vals['advance_date']:
            tm_tuple = datetime.strptime(vals['advance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_advance, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'advance_date' in vals and vals['advance_date']:
            tm_tuple = datetime.strptime(vals['advance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_advance, self).write(cr, uid, ids, vals, context)
        return res
    
    
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.advance_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.advance_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
        
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'advance_date':fields.date('Advance Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'total_amount':fields.float('Advance',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'remark':fields.char('Remark',size=512, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    _defaults={
               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
               'user_id': lambda obj, cr, uid, context: uid,
               'state':'draft',
               'year':time.strftime('%Y')
               }
    
    _sql_constraints = [('unique_name_employee_advance_date','unique(employee_id,advance_date)','Advance line is already created for this date and employee.')]
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select advance_date from payment_management_advance order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'advance_date':date1}
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    


class payment_management_loan(osv.osv):
    _name='payment.management.loan'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.loan_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.loan_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
   
        
        
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'loan_date':fields.date('Loan Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'total_amount':fields.float('Loan',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'balance_amount':fields.float('Balance',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'amount_emi':fields.float('EMI',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              }
    _defaults={
               'user_id': lambda obj, cr, uid, context: uid,
               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
               }
    
    _sql_constraints = [('unique_name_employee_loan_date','unique(employee_id,loan_date)','Loan line is already created for this date and employee.')]

    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select loan_date from payment_management_loan order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'loan_date':date1}
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'done'
        res = super(payment_management_loan, self).create(cr, uid, vals, context)
        
        return res
    
class payment_management_panalty(osv.osv):
    _name='payment.management.panalty'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'penalty_date' in vals and vals['penalty_date']:
            tm_tuple = datetime.strptime(vals['penalty_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_panalty, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'penalty_date' in vals and vals['penalty_date']:
            tm_tuple = datetime.strptime(vals['penalty_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_panalty, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.penalty_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.penalty_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
        
        
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'penalty_date':fields.date('Penalty Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'amount':fields.float('Amount',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'remark':fields.char('Remark',size=512,required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    _defaults={
               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
               'remark':'Provide By Audit',
               'user_id': lambda obj, cr, uid, context: uid,
               'state':'draft',
               'year':time.strftime('%Y'),
               }
    
    _sql_constraints = [('unique_name_employee_penalty_date','unique(employee_id,penalty_date)','Penalty line is already created for this date and employee.')]
    

    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class payment_management_tds(osv.osv):
    _name='payment.management.tds'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'tds_date' in vals and vals['tds_date']:
            tm_tuple = datetime.strptime(vals['tds_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_tds, self).create(cr, uid, vals, context)
        return res
          
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'tds_date' in vals and vals['tds_date']:
            tm_tuple = datetime.strptime(vals['tds_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_tds, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.tds_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.tds_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'tds_date':fields.date('TDS Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'tds':fields.float('TDS',required=True,digits_compute= dp.get_precision('Account'), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    _defaults={
               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
               'user_id': lambda obj, cr, uid, context: uid,
               'state':'draft',
               'year':time.strftime('%Y'),
               }
    _sql_constraints = [('unique_name_employee_month_year','unique(employee_id,month,year_id)','Payment line is already created for this date, employee, month and year.')]

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
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select tds_date from payment_management_tds order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'tds_date':date1}
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class payment_management_epf(osv.osv):
    _name='payment.management.epf'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'epf_date' in vals and vals['epf_date']:
            tm_tuple = datetime.strptime(vals['epf_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_epf, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'epf_date' in vals and vals['epf_date']:
            tm_tuple = datetime.strptime(vals['epf_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_epf, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.epf_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.epf_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'epf_date':fields.date('EPF Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'epf':fields.float('EPF',required=True,digits_compute= dp.get_precision('Account'), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    _defaults={
               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
               'user_id': lambda obj, cr, uid, context: uid,
               'state':'draft',
               'year':time.strftime('%Y'),
               }
    _sql_constraints = [('unique_name_employee_month_year','unique(employee_id,month,year_id)','Payment line is already created for this date, employee, month and year.')]

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
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select epf_date from payment_management_epf order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'epf_date':date1}
        return res

    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    
#class payment_management_reward(osv.osv):
#    _name='payment.management.reward'
#    
#    def _calculate_month(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for each in self.browse(cr, uid, ids):
#            tm_tuple = datetime.strptime(each.reward_date,'%Y-%m-%d').timetuple()
#            month = tm_tuple.tm_mon
#            res[each.id] = month     
#        return res
#    
#    def _calculate_year(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for each in self.browse(cr, uid, ids):
#            tm_tuple = datetime.strptime(each.reward_date,'%Y-%m-%d').timetuple()
#            year = tm_tuple.tm_year
#            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
#            if year_id:
#                res[each.id] = year_id[0]  
#            else:
#                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
#        return res
#    
#   
#        
#        
#    _columns={
#              'name':fields.date('Create Date',readonly=True),
#              'reward_date':fields.date('Reward Date',required=True),
#              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
#              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
#              'employee_id':fields.many2one('hr.employee','Employee',required=True),
#              'amount':fields.float('Amount',required=True),
#              'remark':fields.char('Remark',size=512,required=True),
#              'user_id':fields.many2one('res.users','Created By',readonly=True),
#              }
#    _defaults={
#               'user_id': lambda obj, cr, uid, context: uid,
#               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
#               }
#    
#    _sql_constraints = [('unique_name_employee_reward_date','unique(name,employee_id,reward_date)','Reward line is already created for this date and employee.')]
#    
#
#
#    
class payment_management_done(osv.osv):
    _name='payment.management.done'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.done_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.done_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'done_date':fields.date('Payment Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'paid':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,done_date,year_id)','Duplicate entry for the same employee and date.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select done_date from payment_management_done order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'done_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'done'
        res = super(payment_management_done, self).create(cr, uid, vals, context)
        
        return res 
    
# class payment_management_adjust(osv.osv):
#     _name='payment.management.adjust'
#     
#     def _calculate_month(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         for each in self.browse(cr, uid, ids):
#             tm_tuple = datetime.strptime(each.adjust_date,'%Y-%m-%d').timetuple()
#             month = tm_tuple.tm_mon
#             res[each.id] = month     
#         return res
#     
#     def _calculate_year(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         for each in self.browse(cr, uid, ids):
#             tm_tuple = datetime.strptime(each.adjust_date,'%Y-%m-%d').timetuple()
#             year = tm_tuple.tm_year
#             year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
#             if year_id:
#                 res[each.id] = year_id[0]  
#             else:
#                 raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
#         return res
#     
#     
#     _columns={
#               'name':fields.date('Create Date',readonly=True),
#               'adjust_date':fields.date('Adjustment Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
#               'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
#               'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
#               'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
#               'adjust':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
#               'user_id':fields.many2one('res.users','Created By',readonly=True),
#               'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
#               'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
#               }
#     
#     _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month')]
#     
#     _defaults={
#            'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
#            'user_id': lambda obj, cr, uid, context: uid,
#            'state':'draft',
#            }
#     
#     def onchange_employee(self, cr, uid, ids, employee, context=None):
#         res = {}
#         if not employee:
#             return res
#         cr.execute("select adjust_date from payment_management_adjust order by id desc limit 1") 
#         temp = cr.fetchall()
#         for data in temp:
#             if data and len(data) > 0 and data[0] != None:
#                 date1 = data[0]
#                 res['value'] = {'adjust_date':date1}
#         return res
#     
#     def onchange_month(self, cr, uid, ids, month, context=None):
#         res = {}
#         if not month:
#             res['value'] = {'year_id':False}
#             return res
#         month_obj = self.pool.get('holiday.list')
#         month_data = month_obj.browse(cr, uid, month)
#         if not month_data.year_id:
#             res['warning'] = {'title': _('Warning'), 'message': _('Unable to process request, year is not selected in month.')}
#         res['value'] = {'year_id':month_data.year_id and month_data.year_id.id or False}
#         return res
#     
#     def unlink(self, cr, uid, ids, context=None):
#         
#         unlink_ids = []
#         for line in self.browse(cr, uid, ids, context):
#             if line.state in ['draft']:
#                 unlink_ids.append(line.id)
#             else:
#                 raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))
# 
#         return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
#     
#     def create(self, cr, uid, vals, context=None):
#         vals['state'] = 'done'       
#         res = super(payment_management_adjust, self).create(cr, uid, vals, context)
#         
#         return res 
    
class payment_management_bonus(osv.osv):
    _name='payment.management.bonus'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'employee_id':fields.many2one('hr.employee','Employee'),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'bonus_from':fields.date('Bonus From',required=True),
              'bonus_till':fields.date('Bonus Till',required=True),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT'),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'bonus_line':fields.one2many('payment.management.bonus.line','bonus_id','Bonus line'),
              'current_advance':fields.float('Current Advance'),
              'basic':fields.float('Basic'),
              'daily':fields.float('Daily'),
              'apr':fields.float('APR'),
              'may':fields.float('MAY'),
              'june':fields.float('JUNE'),
              'july':fields.float('JULY'),
              'aug':fields.float('AUG'),
              'sep':fields.float('SEP'),
              'oct':fields.float('OCT'),
              'nov':fields.float('NOV'),
              'dec':fields.float('DEC'),
              'jan':fields.float('JAN'),
              'feb':fields.float('FEB'),
              'mar':fields.float('MAR'),
              't_days':fields.float('T.DAYS'),
              'advance_month':fields.selection([('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),
                ('8','August'),('9','September'),('10','October'),('11','November'),('12','December'),],'Advance Month',required=True),
              'advance_year_id':fields.many2one('holiday.year','Advance Year',required=True),
              'export_data':fields.binary('File',readonly=True),
              'filename':fields.char('File Name',size=250,readonly=True),
              'seq_from':fields.integer('From Seq.'),
              'seq_to':fields.integer('To Seq.'),
              }
    
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           }
    
    def onchange_employee(self, cr, uid, ids, employee, name, context=None):
        res = {}
        if not employee and name:
            return res
        for data in self.pool.get('hr.employee').browse(cr, uid, [employee]):
            tm_tuple = datetime.strptime(name,'%Y-%m-%d').timetuple()
            new_date = str(tm_tuple.tm_year) + '-04' + '-01'
            res['value'] = {'bonus_from':new_date}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if 'bonus_from' in vals and vals['bonus_from'] and 'bonus_till' in vals and vals['bonus_till']:
            if datetime.strptime(vals['bonus_from'],'%Y-%m-%d') >= datetime.strptime(vals['bonus_till'],'%Y-%m-%d'):
                raise osv.except_osv(_('Invalid action !'), _('Bonus from cannot be greater than or equals to Bonus till.'))
        res = super(payment_management_bonus, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        for each in self.browse(cr, uid, ids):
            bonus_from = each.bonus_from
            bonus_till = each.bonus_till
        
        if 'bonus_from' in vals and vals['bonus_from'] and 'bonus_till' in vals and vals['bonus_till']:
            if datetime.strptime(vals['bonus_from'],'%Y-%m-%d') >= datetime.strptime(vals['bonus_till'],'%Y-%m-%d'):
                raise osv.except_osv(_('Invalid action !'), _('Bonus from cannot be greater than or equals to Bonus till.'))
        
        elif 'bonus_from' in vals and vals['bonus_from'] and 'bonus_till' not in vals:
            if datetime.strptime(vals['bonus_from'],'%Y-%m-%d') >= datetime.strptime(bonus_till,'%Y-%m-%d'):
                raise osv.except_osv(_('Invalid action !'), _('Bonus from cannot be greater than or equals to Bonus till.'))
        
        elif 'bonus_from' not in vals and 'bonus_till' in vals and vals['bonus_till']:
            if datetime.strptime(bonus_from,'%Y-%m-%d') >= datetime.strptime(vals['bonus_till'],'%Y-%m-%d'):
                raise osv.except_osv(_('Invalid action !'), _('Bonus from cannot be greater than or equals to Bonus till.'))
            
        res = super(payment_management_bonus, self).write(cr, uid, ids, vals, context) 
        return res
            
    def last_day_of_month(self,date):
        if date.month == 12:
            return date.replace(day=31)
        return date.replace(month=date.month+1, day=1) - timedelta(days=1)
            
    def compute_bonus(self, cr, uid, ids, context=None):
        sal_obj = self.pool.get('salary.payment.line')
        emp_obj = self.pool.get('hr.employee')
        year_obj = self.pool.get('emp.year')
        count = 0
        for each in self.browse(cr, uid, ids):
            if each.type and each.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('type','=',each.type),('id','=',each.employee_id.id)])
            elif each.type and not each.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('type','=',each.type)])
                if len(emp_ids)>500:
                    if each.seq_to==0 or each.seq_from==0:
                        raise osv.except_osv(_('Warning !'), _('More then 500 employees work on this Location So, Please Enter Sequence.'))
                    emp_ids.sort()
                    emp_ids=emp_ids[int(each.seq_from-1):each.seq_to]
                
            elif not each.type and each.employee_id:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True),('id','=',each.employee_id.id)])
            else:
                emp_ids = emp_obj.search(cr, uid, [('active','=',True)])
            for line in emp_obj.browse(cr, uid, emp_ids):
                print"-------------------name----------",line.name,line.id
                jan = feb = mar = apr = may = jun = jul = aug = sep = oct = nov = dec =0
                total_days1 = 0
                curr_loan = 0.0
                curr_loan_lst = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',each.advance_month),('year_id','=',each.advance_year_id.id),('salary_type','=','Salary')])
                if curr_loan_lst:
                    curr_loan = sal_obj.browse(cr, uid, curr_loan_lst[0]).current_loan
                joining_date = line.joining_date
                if not line.salary or line.salary < 1:
                    continue
                if not joining_date:
                    raise osv.except_osv(_('Invalid action !'), _('Joining date is missing for Employee %s.')%(line.sinid,))
                if not line.daily and not line.monthly:
                    raise osv.except_osv(_('Invalid action !'), _('Please tick either daily or monthly for Employee %s.')%(line.sinid,))
                bonus_start = datetime.strptime(joining_date,'%Y-%m-%d')
                bonus_start = bonus_start + relativedelta(months=+6)
                bonus_start = datetime.strptime(joining_date,'%Y-%m-%d')
                joining_date = datetime.strptime(joining_date,'%Y-%m-%d')
                bonus_from = datetime.strptime(each.bonus_from,'%Y-%m-%d')
                tm_tuple_from = datetime.strptime(bonus_from.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                tm_tuple_join = datetime.strptime(joining_date.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                if (int(tm_tuple_join.tm_year) >= (int(tm_tuple_from.tm_year))-1):
                    if tm_tuple_join.tm_mday>15:
#                         if (int(tm_tuple_join.tm_mon)+7) < (int(tm_tuple_from.tm_mon)):
                        bonus_start = bonus_start + relativedelta(months=+7)
                    else:
#                         if (int(tm_tuple_join.tm_mon)+6) < (int(tm_tuple_from.tm_mon)):
                        bonus_start = bonus_start + relativedelta(months=+6)
                else:
                    bonus_start = joining_date
#                     bonus_start = datetime.strptime(str(joining_date),'%Y-%m-%d')
                bonus_start = bonus_start.strftime('%Y-%m-%d')                
#                 bonus_start = bonus_start.strftime('%Y-%m-%d')
                bonus_from = each.bonus_from
                bonus_till = each.bonus_till
                bonus_data = {}
                total_day = 0
                rnd_total_pay = total_pay = 0
                starting_date = False
                day_sal = 0
                month_count=0
                day_sal1 = day_sal2 = day_sal4 = 0
                march_sal=0.0
                if datetime.strptime(bonus_start,'%Y-%m-%d') > datetime.strptime(bonus_from,'%Y-%m-%d'):

                    month = 0
                    starting_date = bonus_from
                    bonus_from = datetime.strptime(bonus_start,'%Y-%m-%d')
                    # bonus_till = datetime.strptime(bonus_till,'%Y-%m-%d')
                    jan=feb=0.0
                    while (bonus_from <= datetime.strptime(bonus_till,'%Y-%m-%d')):
                        bonus_till_to = datetime.strptime(bonus_till,'%Y-%m-%d')
                        month += 1
                        tm_tuple = datetime.strptime(bonus_from.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                        emp_month = tm_tuple.tm_mon
                        emp_year = tm_tuple.tm_year
                        tm_tuple_to = datetime.strptime(bonus_till_to.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                        emp_month_to = tm_tuple_to.tm_mon
                        emp_year_to = tm_tuple_to.tm_year
                        year_id = year_obj.search(cr, uid, [('name','=',emp_year_to)])
                        salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to),])
                        salary_id1 = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=', 3),('year_id.name','=',emp_year_to),('salary_type','=','Salary')])
                        if salary_id1:
                            march_sal = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2                     
                            if march_sal<=700:
                                day_sal2 = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2
                            else:
                                day_sal4 = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2

                        
                        if sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-1)),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-1)),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-2)),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-2)),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+8)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+8)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+7)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+7)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+6)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+6)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+5)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+5)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+4)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+4)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+3)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+3)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+2)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+2)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+1)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+1)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)])
                        else:
                            salary_id=[]

                        if salary_id:

                            if (sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2)<=700:
                                day_sal = sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2
                            else:
                                day_sal = ((sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2) * 12) / 365
                            for val in sal_obj.browse(cr, uid, sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)])):
                                
                                if emp_month in [4,5,6] and emp_year==2013:
                                    month_count+=1
                                    total_pay += (day_sal * val.days) * 0.0833
                                    if emp_month==4:
                                        apr=val.days
                                    elif emp_month==5:
                                        may=val.days
                                    elif emp_month==6:
                                        jun=val.days
                                else:
                                    
                                    if val.salary_type=='Salary':
                                        total_pay += (day_sal * val.days) * 0.0833
                                        month_count+=1
                                        if emp_month==4:
                                            apr=val.days
                                        elif emp_month==5:
                                            may=val.days
                                        elif emp_month==6:
                                            jun=val.days                                        
                                        elif emp_month==7:
                                            jul=val.days
                                        elif emp_month==8:
                                            aug=val.days
                                        elif emp_month==9:
                                            sep=val.days
                                        elif emp_month==10:
                                            oct=val.days
                                        elif emp_month==11:
                                            nov=val.days
                                        elif emp_month==12:
                                            dec=val.days
                                        elif emp_month==1:
                                            jan=val.days
                                        elif emp_month==2:
                                            feb=val.days
                                        elif emp_month==3:
                                            mar=val.days
                                        
                                        total_days1 = (jan + feb + mar + apr + may + jun + jul + aug + sep + oct + nov + dec)
                                        
                            bonus_from = bonus_from + relativedelta(months=+1)
                        
                else:
                    month = 0
                    bonus_from = datetime.strptime(bonus_from,'%Y-%m-%d')
                    starting_date = bonus_from
                    while (bonus_from <= datetime.strptime(bonus_till,'%Y-%m-%d')):
                        bonus_till_to = datetime.strptime(bonus_till,'%Y-%m-%d')
                        month += 1
                        tm_tuple = datetime.strptime(bonus_from.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                        emp_month = tm_tuple.tm_mon
                        emp_year = tm_tuple.tm_year
                        tm_tuple_to = datetime.strptime(bonus_till_to.strftime('%Y-%m-%d'),'%Y-%m-%d').timetuple()
                        emp_month_to = tm_tuple_to.tm_mon
                        emp_year_to = tm_tuple_to.tm_year
                        year_id = year_obj.search(cr, uid, [('name','=',emp_year_to)])
                        salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to)])
                        salary_id1 = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to),('salary_type','=','Salary')])
                        if salary_id1:    
                            march_sal = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2                     
                            if march_sal<=700:                                         
                                day_sal2 = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2
                            else:
                                day_sal4 = sal_obj.browse(cr,uid, salary_id1[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id1[0]).basic_part2
                        
                        if sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month_to),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-1)),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-1)),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-2)),('year_id.name','=',emp_year_to)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month_to)-2)),('year_id.name','=',emp_year_to)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+8)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+8)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+7)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+7)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+6)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+6)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+5)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+5)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+4)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+4)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+3)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+3)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+2)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+2)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+1)),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',(int(emp_month)+1)),('year_id.name','=',emp_year)])
                        elif sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)]):
                            salary_id = sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)])
                        else:
                            salary_id=[] 
                        if salary_id:
                            if (sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2)<=700:
                                day_sal = sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2
                            else:
                                day_sal = ((sal_obj.browse(cr,uid, salary_id[0]).basic_part1 + sal_obj.browse(cr,uid, salary_id[0]).basic_part2) * 12) / 365
                        # if line.daily:
                        #     day_sal = line.salary
                        # else:
                        #     day_sal = (line.salary * 12) / 365
                        for val in sal_obj.browse(cr, uid, sal_obj.search(cr, uid, [('employee_id','=',line.id),('month','=',emp_month),('year_id.name','=',emp_year)])):
                            if emp_month in [4,5,6] and emp_year==2013:
                                month_count+=1
                                total_pay += (day_sal * val.days) * 0.0833
                                if emp_month==4:
                                        apr=val.days
                                elif emp_month==5:
                                        may=val.days
                                elif emp_month==6:
                                        jun=val.days
                            else:
                                if val.salary_type=='Salary':
                                    month_count+=1
                                    total_pay += (day_sal * val.days) * 0.0833
                                    if emp_month==4:
                                            apr=val.days
                                    elif emp_month==5:
                                            may=val.days
                                    elif emp_month==6:
                                            jun=val.days
                                    elif emp_month==7:
                                            jul=val.days
                                    elif emp_month==8:
                                            aug=val.days
                                    elif emp_month==9:
                                            sep=val.days
                                    elif emp_month==10:
                                            oct=val.days
                                    elif emp_month==11:
                                            nov=val.days
                                    elif emp_month==12:
                                            dec=val.days
                                    elif emp_month==1:
                                            jan=val.days
                                    elif emp_month==2:
                                            feb=val.days
                                    elif emp_month==3:
                                            mar=val.days

                        total_days1 = (jan + feb + mar + apr + may + jun + jul + aug + sep + oct + nov + dec)

                        bonus_from = bonus_from + relativedelta(months=+1)
                
                if month < 0:
                    continue                
                total_pay = int(total_pay)
                rnd = total_pay % 10
                if rnd >= 0 and rnd < 3:
                    rnd_total_pay = total_pay - rnd
                elif rnd > 2 and rnd < 6:
                    if rnd == 3:
                        rnd = 2
                    elif rnd == 4:
                        rnd = 1 
                    rnd_total_pay = total_pay + rnd
                elif rnd > 5 and rnd < 8:
                    if rnd == 6:
                        rnd = 1
                    elif rnd == 7:
                        rnd = 2
                    rnd_total_pay = total_pay - rnd
                elif rnd > 7:
                    if rnd == 8:
                        rnd = 2
                    elif rnd == 9:
                        rnd = 1 
                    rnd_total_pay = total_pay + rnd
                line_dict = {
                              'name':each.name,
                              'joining_date':line.joining_date,
                              'employee_id':line.id,
                              'month':each.month,
                              'year_id':each.year_id.id,
                              'bonus_from':starting_date,
                              'bonus_till':each.bonus_till,
                              'bonus_month':str(month_count) + ' month',
                              'bonus':rnd_total_pay,
                              'user_id':uid,
                              'type':line.type,
                              'state':'done',
                              'bonus_id':each.id,
                              'apr':apr,
                              'may':may,
                              'june':jun,
                              'july':jul,
                              'aug':aug,
                              'sep':sep,
                              'oct':oct,
                              'nov':nov,
                              'dec':dec,
                              'jan':jan,
                              'feb':feb,
                              'mar':mar,
                              't_days':total_days1,
                              'daily':day_sal2,
                              'basic':day_sal4,
                              'current_advance':curr_loan,
                              
                             }
                
                cr.execute("delete from payment_management_bonus_line where employee_id ='"+str(line.id)+"' and bonus_id = '"+str(each.id)+"'")
                if rnd_total_pay == 0.0:
                    continue
                count += 1
                new_id = self.pool.get('payment.management.bonus.line').create(cr, uid, line_dict)
                print "<------------------- NEW RECORD CREATED  --------------->",count,str(month) + ' month',rnd_total_pay
        return True
    
    def print_report(self, cr, uid, ids, data, context=None):
        obj = self.browse(cr,uid,ids)
        wb = Workbook()
        ws = wb.add_sheet('Payment Bonus')
        fnt = Font()
        fnt.name = 'Arial'
        fnt.height= 275
        content_fnt = Font()
        content_fnt.name ='Arial'
        content_fnt.height =150
        align_content = Alignment()
        align_content.horz= Alignment.HORZ_CENTER
        borders = Borders()
        borders.left = 0x02
        borders.right = 0x02
        borders.top = 0x02
        borders.bottom = 0x02
        align = Alignment()
        align.horz = Alignment.HORZ_CENTER
        align.vert = Alignment.VERT_CENTER
        pattern = Pattern()
        pattern.pattern = Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour =  0x1F
        style_header= XFStyle()
        style_header.font= fnt
        style_header.pattern= pattern
        style_header.borders = borders
        style_header.alignment=align
        ws.row(0).height=1000
        ws.write(0,0,'Name',style_header)
        ws.write(0,1,'Joining Date',style_header)
        ws.write(0,2,'Bonus From',style_header)
        ws.write(0,3,'Bonus Till',style_header)
        ws.write(0,4,'Total Month',style_header)
        ws.write(0,5,'Amount',style_header)
        ws.write(0,6,'Created By',style_header)
        ws.write(0,7,'Current Advance',style_header)
        ws.write(0,8,'Basic',style_header)
        ws.write(0,9,'Daily',style_header)
        ws.write(0,10,'APR',style_header)
        ws.write(0,11,'MAY',style_header)
        ws.write(0,12,'JUNE',style_header)
        ws.write(0,13,'JULY',style_header)
        ws.write(0,14,'AUG',style_header)
        ws.write(0,15,'SEP',style_header)
        ws.write(0,16,'OCT',style_header)
        ws.write(0,17,'NOV',style_header)
        ws.write(0,18,'DEC',style_header)
        ws.write(0,19,'JAN',style_header)
        ws.write(0,20,'FEB',style_header)
        ws.write(0,21,'MAR',style_header)
        ws.write(0,22,'T. Days',style_header)
        
        for row in obj:
            print row
            print "aaaaaaaaaaaaa ",row.name
            if len(row.bonus_line) > 0:
                columnno = 1
                for inlinerow in row.bonus_line:
                    
                    ws.write(columnno,0,str("["+inlinerow.employee_id.sinid+"] ")+inlinerow.employee_id.name)
                    ws.write(columnno,1,inlinerow.joining_date)
                    ws.write(columnno,2,inlinerow.bonus_from)
                    ws.write(columnno,3,inlinerow.bonus_till)
                    ws.write(columnno,4,inlinerow.bonus_month)
                    ws.write(columnno,5,inlinerow.bonus)
                    ws.write(columnno,6,inlinerow.user_id.name)
                    ws.write(columnno,7,    inlinerow.current_advance)
                    ws.write(columnno,8,inlinerow.basic)
                    ws.write(columnno,9,inlinerow.daily)
                    ws.write(columnno,10,inlinerow.apr)
                    ws.write(columnno,11,inlinerow.may)
                    ws.write(columnno,12,inlinerow.june)
                    ws.write(columnno,13,inlinerow.july)
                    ws.write(columnno,14,inlinerow.aug)
                    ws.write(columnno,15,inlinerow.sep)
                    ws.write(columnno,16,inlinerow.oct)
                    ws.write(columnno,17,inlinerow.nov)
                    ws.write(columnno,18,inlinerow.dec)
                    ws.write(columnno,19,inlinerow.jan)
                    ws.write(columnno,20,inlinerow.feb)
                    ws.write(columnno,21,inlinerow.mar)
                    ws.write(columnno,22,inlinerow.t_days)
                    columnno += 1
        f = cStringIO.StringIO()
        wb.save(f)
        out=base64.encodestring(f.getvalue())
        
        return self.write(cr, uid, ids, {'export_data':out,'filename':'export.xls'}, context=context)
    
class payment_management_bonus_line(osv.osv):
    _name='payment.management.bonus.line'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'joining_date':fields.date('Joining Date',required=True, readonly=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'bonus_from':fields.date('Bonus From',required=True,readonly=True),
              'bonus_till':fields.date('Bonus Till',required=True,readonly=True),
              'bonus_month':fields.char('Total Month',size=64,readonly=True),
              'bonus':fields.float('Amount',digits_compute= dp.get_precision('Account'),readonly=True),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'bonus_id':fields.many2one('payment.management.bonus','Bonus',ondelete='cascade'),
              'current_advance':fields.float('Current Advance'),
              'basic':fields.float('Basic'),
              'daily':fields.float('Daily'),
	          'apr':fields.float('APR'),
              'may':fields.float('MAY'),
              'june':fields.float('JUNE'),
              'july':fields.float('JULY'),
              'aug':fields.float('AUG'),
              'sep':fields.float('SEP'),
              'oct':fields.float('OCT'),
              'nov':fields.float('NOV'),
              'dec':fields.float('DEC'),
              'jan':fields.float('JAN'),
              'feb':fields.float('FEB'),
              'mar':fields.float('MAR'),
              't_days':fields.float('T.DAYS'),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           }

    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
        
class payment_management_conveyance(osv.osv):
    _name='payment.management.conveyance'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'conveyance_date' in vals and vals['conveyance_date']:
            tm_tuple = datetime.strptime(vals['conveyance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_conveyance, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'conveyance_date' in vals and vals['conveyance_date']:
            tm_tuple = datetime.strptime(vals['conveyance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_conveyance, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.conveyance_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.conveyance_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'conveyance_date':fields.date('Conveyance Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'conveyance':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           'year':time.strftime('%Y'),
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select conveyance_date from payment_management_conveyance order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'conveyance_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class payment_management_miscellaneous(osv.osv):
    _name='payment.management.miscellaneous'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.miscellaneous_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.miscellaneous_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'miscellaneous_date':fields.date('Miscellaneous Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'miscellaneous':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select miscellaneous_date from payment_management_miscellaneous order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'miscellaneous_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'done'      
        res = super(payment_management_miscellaneous, self).create(cr, uid, vals, context)
        
        return res
    
class payment_management_telephone(osv.osv):
    _name='payment.management.telephone'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'telephone_date' in vals and vals['telephone_date']:
            tm_tuple = datetime.strptime(vals['telephone_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_telephone, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'telephone_date' in vals and vals['telephone_date']:
            tm_tuple = datetime.strptime(vals['telephone_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_telephone, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.telephone_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.telephone_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'telephone_date':fields.date('Telephone Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'telephone':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           'year':time.strftime('%Y'),
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select telephone_date from payment_management_telephone order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'telephone_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
class payment_management_security(osv.osv):
    _name='payment.management.security'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'security_date' in vals and vals['security_date']:
            tm_tuple = datetime.strptime(vals['security_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_security, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'security_date' in vals and vals['security_date']:
            tm_tuple = datetime.strptime(vals['security_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_security, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.security_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.security_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'security_date':fields.date('Telephone Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'security':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           'year':time.strftime('%Y'),
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select security_date from payment_management_security order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'security_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    
class payment_management_previous_advance(osv.osv):
    _name='payment.management.previous.advance'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'advance_date' in vals and vals['advance_date']:
            tm_tuple = datetime.strptime(vals['advance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_previous_advance, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'advance_date' in vals and vals['advance_date']:
            tm_tuple = datetime.strptime(vals['advance_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(payment_management_previous_advance, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.advance_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.advance_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'advance_date':fields.date('Advance Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'paid':fields.float('Amount',digits_compute= dp.get_precision('Account'),required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,month,year_id)','Duplicate entry for the same employee and month.')]
    
    _defaults={
           'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
           'user_id': lambda obj, cr, uid, context: uid,
           'state':'draft',
           'year':time.strftime('%Y'),
           }
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select advance_date from payment_management_previous_advance order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'advance_date':date1}
        return res
    
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
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
#    
#class payment_management_outside(osv.osv):
#    _name='payment.management.outside'
#    
#    def _calculate_month(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for each in self.browse(cr, uid, ids):
#            tm_tuple = datetime.strptime(each.from_time,'%Y-%m-%d %H:%M:%S').timetuple()
#            month = tm_tuple.tm_mon
#            res[each.id] = month     
#        return res
#    
#    def _calculate_working_time(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for each in self.browse(cr, uid, ids):
#            if datetime.strptime(each.from_time,'%Y-%m-%d %H:%M:%S') > datetime.strptime(each.to_time,'%Y-%m-%d %H:%M:%S'):
#                raise osv.except_osv(_('Invalid action !'), _('From time cannot be greater than To time.!'))
#
#            time = datetime.strptime(each.to_time,'%Y-%m-%d %H:%M:%S') - datetime.strptime(each.from_time,'%Y-%m-%d %H:%M:%S')
#            time = time.total_seconds()
#            work_min = float(time / 60)
#            work_hr = float(work_min / 60)
#            work_hr = divmod(work_hr,1)[0]
#            if work_hr:
#                nw_min = work_min - work_hr * 60
#            else:
#                nw_min = work_min
#            
#            if nw_min > 2 and nw_min < 33:
#                nm_min = 0.5
#            elif nw_min > 32:
#                work_hr = work_hr + 1
#                nm_min = 0.0
#            else:
#                nm_min = 0.0
#            new_hrs = work_hr + nm_min
#            res[each.id]=new_hrs
#        return res
#        
#    def _calculate_year(self, cr, uid, ids, name, args, context=None):
#        res = {}
#        for each in self.browse(cr, uid, ids):
#            tm_tuple = datetime.strptime(each.from_time,'%Y-%m-%d %H:%M:%S').timetuple()
#            year = tm_tuple.tm_year
#            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
#            if year_id:
#                res[each.id] = year_id[0]  
#            else:
#                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
#        return res
#        
#    _columns={
#              'name':fields.date('Create Date',readonly=True),
#              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
#              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
#              'employee_id':fields.many2one('hr.employee','Employee',required=True),
#              'from_time':fields.datetime('From Time',required=True),
#              'to_time':fields.datetime('To Time',required=True),
#              'out_time':fields.function(_calculate_working_time,method=True,type='float',string='Total Time',digits=(4,2),store=True),
#              'remark':fields.char('Remark',size=512),
#              'approve_date':fields.datetime('Approve Date',readonly=True),
#              'approved_id':fields.many2one('res.users','Approved By',readonly=True),
#              'state':fields.selection([('draft','Draft'),('approved','Approved')],'State',readonly=True),
#              }
#    _defaults={'state':'draft',
#               'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
#               }
#    
#    _sql_constraints = [('unique_name_employee_from_time','unique(name,employee_id,from_time)','Outside time is already created for this date, employee and time.')]
#    
#
#    
#    def approval_done(self,cr,uid,ids,context=None):
#        res={}
#        self.write(cr,uid,ids,{'state':'approved','approved_id':uid,'approve_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
#        return True
#    
#    def unlink(self, cr, uid, ids, context=None):
#        payment = self.read(cr, uid, ids, ['state'], context=context)
#        unlink_ids = []
#        for line in payment:
#            if line['state'] in ['draft']:
#                unlink_ids.append(line['id'])
#            else:
#                raise osv.except_osv(_('Invalid action !'), _('You cannot delete approved payment'))
#
#        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
class payment_management_adjust(osv.osv):
    _name='payment.management.adjust'
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
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
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
#              'adjust_date':fields.date('Adjustment Date',required=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.many2one('holiday.list','Month',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'days':fields.float('Days',digits=(3,1), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'working_ot':fields.float('Working Day OT',digits=(16,2), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'penalty':fields.float('Penalty',digits=(16,2), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'sunday_ot':fields.float('Leave Day OT',digits=(16,2), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'old_total_days':fields.float('Old Total Days',digits=(16,2), readonly=True, select=True),
              'old_total_ot':fields.float('Old Total OT',digits=(16,2), readonly=True, select=True),
              'old_total_penalty':fields.float('Old Penalty',digits=(16,2), readonly=True, select=True),
              'old_days_amt':fields.float('Old Days AMT',digits=(16,2), readonly=True, select=True),
              'old_ot_amt':fields.float('Old OT AMT',digits=(16,2), readonly=True, select=True),
              'old_oneday_amt':fields.float('Old 1Day AMT',digits=(16,2), readonly=True, select=True),
              'old_remday_amt':fields.float('Old 1D R.AMT',digits=(16,2), readonly=True, select=True),
              'old_total_amt':fields.float('Old Total AMT',digits=(16,2), readonly=True, select=True),
              'new_total_amt':fields.float('New Total AMT',digits=(16,2), readonly=True, select=True),
              'new_remday_amt':fields.float('New 1D R.AMT',digits=(16,2), readonly=True, select=True),
              'new_oneday_amt':fields.float('New 1Day AMT',digits=(16,2), readonly=True, select=True),
              'new_total_days':fields.float('New Total Days',digits=(16,2), readonly=True, select=True),
              'new_total_ot':fields.float('New Total OT',digits=(16,2), readonly=True, select=True),
              'new_days_amt':fields.float('New Days AMT',digits=(16,2), readonly=True, select=True),
              'new_ot_amt':fields.float('New OT AMT',digits=(16,2), readonly=True, select=True),
              'new_total_penalty':fields.float('New Penalty',digits=(16,2), readonly=True, select=True),
              'old_grand_total':fields.float('Old Grand Total',digits_compute= dp.get_precision('Account'), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'new_grand_total':fields.float('New Grand Total',digits_compute= dp.get_precision('Account'), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'diff_salary':fields.float('Difference',digits_compute= dp.get_precision('Account'), readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'user_done_id':fields.many2one('res.users','Paid By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
              'payment_update':fields.boolean('Update Salary', readonly=True, select=True, states={'draft': [('readonly', False)],'done': [('readonly', False)]}),
              'state':fields.selection([('draft','Draft'),('done','Done'),('paid','Paid')],'State',readonly=True),
              'day_in_month':fields.float('Day in month'),
              'holiday_no':fields.float('Holiday'),
              'total_wk_days':fields.float('Total wk Days'),
              'year':fields.selection([('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),
                                         ('2017','2017'),('2018','2018'),('2019','2019'),('2020','2020'),
                                         ('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
                                         ('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
                                         ('2030','2030'),('2031','2031'),('2032','2032'),('2033','2033'),
                                         ('2034','2034'),('2035','2035'),],'YEAR'),
              'year_related':fields.related('month','year_id',type='many2one',relation='holiday.year',string='Year'),                          
              }
    
    
    _defaults={
             'salary_type':'Salary',
             'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
             'user_id': lambda obj, cr, uid, context: uid,
             'payment_update':False,
             'state':'draft',
             'year':time.strftime('%Y')
           }
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    
    def paid_payment(self, cr, uid, ids, context=None):
        salline_obj = self.pool.get('salary.payment.line')
        for each in self.browse(cr, uid, ids):
            salline_id=salline_obj.search(cr,uid,[('employee_id','=',each.employee_id.id),('month','=',each.month.month),('year_id','=',each.month.year_id.id),('salary_type','=','Salary')])
            if not salline_id:
                raise osv.except_osv(_('Warning!'), _('Salary Payment Line does not exist for this employee in selected month!'))
            if not each.payment_update:
                raise osv.except_osv(_('Warning!'), _('Please check Update Salary field, to update salary.!'))
            else:                
                salline_obj.write(cr, uid, salline_id,{
                'days_amount':each.new_days_amt,
                'total_amount':each.new_total_amt,
                'days':each.new_total_days,
                'over_time':each.new_total_ot,
                'total_wk_day':each.total_wk_days,
                'leaves':(each.day_in_month-each.new_total_days),
                'overtime_amount':each.new_ot_amt,
                'day_amount':each.new_oneday_amt,
                'day_remaining_amount':each.new_remday_amt,
                'rnd_grand_total':each.new_grand_total,
                'salary_editted':True,
                'state':'Paid'})
                self.write(cr, uid, ids, {'state':'paid','user_done_id':uid})
        return True
    
    def done_payment(self, cr, uid, ids, context=None):
        salline_obj = self.pool.get('salary.payment.line')
        for each in self.browse(cr, uid, ids):
            salline_id=salline_obj.search(cr,uid,[('employee_id','=',each.employee_id.id),('month','=',each.month.month),('year_id','=',each.month.year_id.id),('salary_type','=','Salary')])
            if not salline_id:
                raise osv.except_osv(_('Warning!'), _('Salary Payment Line does not exist for this employee in selected month!'))
            self.write(cr, uid, ids, {'state':'done'})
        return True
    
    
    def calculate_payment(self, cr, uid, ids, context=None):
        res = {}
        emp_obj = self.pool.get('hr.employee')
        shift_obj = self.pool.get('hr.shift.line')
        att_obj = self.pool.get('attendance.timing')
        salline_obj = self.pool.get('salary.payment.line')
        month = off_day = sunday = off_day1 = sunday1 = 0
        for line in self.browse(cr, uid, ids):
            
            if int(line.month.month) in [1,3,5,7,8,10,12]:
                month = 31
            if int(line.month.month) in [4,6,9,11]:
                month = 30
            if int(line.month.month) in [2]:
                if int(line.year_id.name) % 4 == 0:
                    month = 29
                else:
                    month = 28
            days1=line.days
            
            input_ot=line.working_ot
            input_sunday_ot = line.sunday_ot
            emp_id=line.employee_id
            input_penalty = line.penalty
            month1=int(line.month.month)
            
            year_id=line.month.year_id
            
            salline_id=salline_obj.search(cr,uid,[('employee_id','=',emp_id.id),('month','=',month1),('year_id','=',year_id.id),('salary_type','=','Salary')])
            
            if not salline_id:
                raise osv.except_osv(_('Warning!'), _('Salary Payment Line does not exist for this employee in selected month!'))
            old_salary_line = salline_obj.browse(cr,uid,salline_id[0])
            old_grand_total=old_salary_line.rnd_grand_total
            
            start_date = end_date = str(year_id.name)+'-'+str(line.month.month)+'-01'
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
            
            next_date = datetime.strptime(start_date,"%Y-%m-%d")
            for i in range(month):
                next_date1 = next_date.strftime('%Y-%m-%d')
                for sun in line.month.holiday_lines:
                    if datetime.strptime(next_date1,"%Y-%m-%d").date() == datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                        if sun.week == 'Sunday':
                            sunday += 1 
                        else:
                            off_day += 1
                next_date += timedelta(days=1)
                wk_day += 1 
                
            daily_part =  month - off_day - sunday
            
            if line.salary_type == 'Kharcha':
                off_day = sunday = wk_day = 0
                new_wk_day = 15
                end_date = str(year_id.name)+'-'+str(line.month.month)+'-15'
            
                for i in range(new_wk_day):
                    next_date1 = next_date.strftime('%Y-%m-%d')
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
            holiday_no=len(holiday_date)    
            for val in emp_obj.browse(cr, uid, [line.employee_id.id]):
                working_day = working_day1
                if val.monthly:
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
                            if datetime.strptime(joining,"%Y-%m-%d").date() < datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                                if sun.week == 'Sunday':
                                    sunday += 1 
                                else:
                                    off_day += 1
                        working_day = working_day - off_day - sunday
                    if emp_sunday <> sunday:
                        emp_sunday = sunday
                    
                hrs = 0
                att_list = []
                
                day_remaining_amount = basic_part1 = basic_part2 = hrs = daily = OT_amt = 0.0
                daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                salary = days = total_days = penalty = over_time = over_time_amt = daily_amt = 0.0
                
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
                        if daily_part > 0:
                            basic_part2 = round(val.salary / daily_part,0)
                            basic_part1 = val.salary - basic_part2
                            daily = basic_part1
                            OT_amt = basic_part1 / 8
                    elif val.salary > 0:
                        basic_part1 = round(val.salary, 0)
                        daily = basic_part1
                        OT_amt = basic_part1 / 8
                        
                
#                salary = days = total_days = day = penalty = over_time = day_sal = total_OT = total_OT1 = over_time_amt = over_time_amt1 = daily_amt = 0.0
                        
#                cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and status <> 'D_Miss_Punch'")
                
                if line.salary_type == 'Kharcha':
                    if val.type in ['Wood','Metal']:
                        if val.id in [9654,9658,11244,9700,9695,9679,9853,10817,15951,10150,16823,18675,20825]:
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"'  and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                        else:    
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced')) and dept_status='OK' ")
                            
                    else:
                        cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                else:
                    if val.type in ['Wood','Metal']:
                        if val.id in [9654,9658,11244,9700,9695,9679,9853,10817,15951,10150,16823,18675,20825]:
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                        else:    
                            cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced')) and dept_status='OK' ")
                            
                    else:
                        cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and year_id='"+str(line.month.year_id.id)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced'))")
                temp = cr.fetchall()
                for data in temp:
                    att_list.append(data[0])
                
#                 tick = False
#                 for rec in att_obj.browse(cr, uid, att_list):
#                     if rec.employee_id.type in ['Wood','Metal']:
#                         if datetime.strptime(rec.name,'%Y-%m-%d') == datetime.strptime('2013-05-13','%Y-%m-%d'):
#                             days = 0
#                             tick = False
#                             total_days = 0
#                             break
#                         else:
#                             days = 1
#                             total_days = 1
#                             tick = True
                
                
                for rec in att_obj.browse(cr, uid, att_list):
                    
                    if rec.working == 'P':
                        days += 1
                        total_days += 1
                    elif rec.working == 'HD':
                        days += 0.5
                        total_days += 1
                    elif rec.working == 'L':
                        days += 0
                        total_days += 0
                    else:
                        days += 0
                        total_days += 1
                        
                if days1 > 0:
                    days= days + days1
                    total_days = total_days + int(days1)
                if val.salary > 0 and not val.daily and not val.monthly:
                    raise osv.except_osv(_('Warning !'), _('Tick daily or month for Pcard %s having salary greater than zero.') % (val.sinid))
                
                if line.salary_type == 'Kharcha':
                
                    day_amount = 0.0
                    day_remaining_amount = 0.0
                             
                             
                    if val.monthly:
                        if emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 24:
                            emp_sunday = emp_sunday - 6
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 20:
                            emp_sunday = emp_sunday - 5
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 16:
                            emp_sunday = emp_sunday - 4
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 12:
                            emp_sunday = emp_sunday - 3
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 8:
                            emp_sunday = emp_sunday - 2
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 4:
                            emp_sunday = emp_sunday - 1
                        
                        
                        if days < 0:
                            days = 0
                            
                        if days > 0:
                            days = days + off_day + emp_sunday
                        
                else:
                    if val.daily:
                        if basic_part2:
                            if days >= 22:
                                day_amount = basic_part1
                            else:
                                day_amount = 0.0
                        else:
                            day_amount = 0.0
                        
                        if days >= working_day:
                            day_remaining_amount = basic_part1
                        else:
                            day_remaining_amount = 0.0
                            
                             
                    if val.monthly:
                        if emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 24:
                            emp_sunday = emp_sunday - 6
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 20:
                            emp_sunday = emp_sunday - 5
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 16:
                            emp_sunday = emp_sunday - 4
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 12:
                            emp_sunday = emp_sunday - 3
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 8:
                            emp_sunday = emp_sunday - 2
                        elif emp_sunday > 0 and total_days > 0 and (working_day - total_days) >= 4:
                            emp_sunday = emp_sunday - 1
                        
                        
                        if days < 0:
                            days = 0
                            
                        if days > 0:
                            days = days + off_day + emp_sunday
                        if basic_part2:
                            if days >= 22:
                                day_amount = basic_part2
                            else:
                                day_amount = 0.0
                        else:
                            day_amount = 0.0
                        
                        if days >= month:
                            if basic_part2:
                                day_remaining_amount = basic_part2
                            else:
                                day_remaining_amount = round(daily,0)
                        else:
                            day_remaining_amount = 0.0
                            
                    if days >= month:
                        days = month
                        day_remaining_amount = day_remaining_amount                        
        
                    
#                 if tick:
#                     days -= 1
            
                
                
                daily_amt = round(days * daily,0)
                salary = days * daily
                TOTAL_PENALTY = TOTAL_SAL = CUTT_OFF = ALLOW_HR = DAILY_AMT = AMT_HR =  WORK_OT = SUN_OT = HALF_OT = HALF_OT_HR = TOTAL_OT = ACTUAL_OT = 0.0
                for rec in att_obj.browse(cr, uid, att_list):
                    if rec.name in holiday_date:
                        SUN_OT += rec.over_time
                    else:
                        WORK_OT += rec.over_time
                    TOTAL_PENALTY += rec.penalty 
                SUN_OT += input_sunday_ot
                SUN_OT = round(SUN_OT,1)
                TOTAL_PENALTY += input_penalty 
                WORK_OT = round(WORK_OT - TOTAL_PENALTY,1)
                WORK_OT = round(WORK_OT + input_ot,1)
                if val.category5 == 'A':
                    if WORK_OT > 0 :  
                        WORK_OT = WORK_OT/2
                    else:
                        WORK_OT = WORK_OT
                else:    
                    WORK_OT = WORK_OT
                if val.monthly:
                    DAILY_AMT = round((val.salary / month) * days, 0)
                    AMT_HR = round(val.salary / (month * 8), 2) 
                elif val.daily:
                    DAILY_AMT = round(val.salary  * days, 0)
                    AMT_HR = round(val.salary / 8, 2)
                
                TOTAL_SAL = daily_amt + (WORK_OT * OT_amt)  + (SUN_OT * OT_amt) + day_amount + day_remaining_amount 
                if val.salary >= 9000:
                    if (WORK_OT) > 0:
                        WORK_OT = WORK_OT / 2
                    ACTUAL_OT = WORK_OT + SUN_OT
                else:
                    if TOTAL_SAL > 9000:
                        if (WORK_OT) > 0:
                            if DAILY_AMT > 9000:
                                TOTAL_OT = WORK_OT / 2
                                ACTUAL_OT = TOTAL_OT + SUN_OT
                            else:
                                CUTT_OFF = 9000 - DAILY_AMT
                                if CUTT_OFF > 0:
                                    ALLOW_HR = round(CUTT_OFF / AMT_HR,1)
                                if ALLOW_HR and WORK_OT > ALLOW_HR:
                                    HALF_OT = round(WORK_OT - ALLOW_HR,1)
                                    HALF_OT_HR = round(HALF_OT / 2,1)
                                    ACTUAL_OT = round(SUN_OT + ALLOW_HR + HALF_OT_HR , 1)
                                else:
                                    ACTUAL_OT = round(SUN_OT + WORK_OT, 1)
                                
                        else:        
                            ACTUAL_OT = WORK_OT + SUN_OT
                    
                
                    else:
                        ACTUAL_OT = WORK_OT + SUN_OT
                
                
                extra_over_time = 0.0
                if line.salary_type == 'Salary':
                    if salary > 0 and val.monthly and hrs == 10.0:
                        extra_over_time = 2
                        
                over_time = ACTUAL_OT + extra_over_time
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
                
                if basic_part1 == 0:
                    daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                
                if days == 0:
                    daily_amt = over_time_amt = day_amount = day_remaining_amount = OT_amt = days = over_time = 0.0
                    
                
                total = daily_amt + over_time_amt + day_amount + day_remaining_amount
                                
                rnd_grand_total = grand_total = tds = epf = chk = conveyance = penalty = advance = loan = security = telephone = previous_advance = current_loan = 0.0 
                if line.salary_type == 'Salary':
                    cr.execute("select sum(conveyance) from payment_management_conveyance  where employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            conveyance = data[0]
                
                if line.salary_type == 'Salary':
                    cr.execute("select sum(tds) from payment_management_tds  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            tds = data[0]
                            
                if line.salary_type == 'Salary':
                    cr.execute("select sum(epf) from payment_management_epf  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            epf = data[0]
                
                if line.salary_type == 'Salary':
                    cr.execute("select sum(check_amt) from employee_check_deduction  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            chk = data[0]            
                            
                if line.salary_type == 'Salary':
                    cr.execute("select sum(amount) from payment_management_panalty  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            penalty = data[0]
                            
                if line.salary_type in ['Salary','Kharcha']:
                    cr.execute("select sum(total_amount) from payment_management_advance  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            advance = data[0]
                            
                if line.salary_type == 'Salary':
                    cr.execute("select max(line.loan_line_amt) from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(line.month.month)+"' and holi.year_id='"+str(year_id.id)+"' and loan.emp_id='"+str(emp_id.id)+"' and loan.state='done' and line.state='not_paid' ")
#                    cr.execute("select max(amount_emi) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            loan = data[0]
                            
                if line.salary_type == 'Salary':
                    cr.execute("select sum(paid) from payment_management_previous_advance  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            previous_advance = data[0]
                
                
                if line.salary_type == 'Salary':
                    cr.execute("select sum(loan.balance) from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(line.month.month)+"' and holi.year_id='"+str(year_id.id)+"' and loan.emp_id='"+str(val.id)+"' and loan.state='done'")
#                    cr.execute("select sum(balance_amount) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            current_loan = data[0]
                            
                if line.salary_type == 'Salary':
                    cr.execute("select sum(security) from payment_management_security  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            security = data[0]
                            
                if line.salary_type == 'Salary':
                    cr.execute("select sum(telephone) from payment_management_telephone  where month='"+str(line.month.month)+"' and year_id='"+str(year_id.id)+"' and employee_id = '"+str(val.id)+"'")
                    temp = cr.fetchall()
                    for data in temp:
                        if data and data[0] != None:
                            telephone = data[0]
               
                
                get_advance=advance
                get_penalty=penalty
                get_epf=epf
                get_chk=chk
                get_tds=tds
                get_loan=loan
                get_conveyance=conveyance
                get_security=security
                get_telephone=telephone
                get_curr_loan=current_loan
                get_previous_advance=previous_advance
                if days <= 0 and not (get_advance or get_penalty or get_epf or get_chk or get_tds or get_loan or get_conveyance or get_security or get_telephone or get_curr_loan or get_previous_advance):   
                    cr.execute("delete from salary_payment_line where id = '"+str(val.id)+"'")
                    continue
                if get_curr_loan < 0:
                    raise osv.except_osv(_('Warning !'), _('Current loan can not be negative'))
                if get_advance < 0:
                    raise osv.except_osv(_('Warning !'), _('Kharcha can not be negative'))
                if get_penalty < 0:
                    raise osv.except_osv(_('Warning !'), _('Penalty can not be negative'))
                if get_tds < 0:
                    raise osv.except_osv(_('Warning !'), _('TDS can not be negative'))
                if get_conveyance < 0:
                    raise osv.except_osv(_('Warning !'), _('Conveyance can not be negative'))
                if get_epf < 0:
                    raise osv.except_osv(_('Warning !'), _('EPF can not be negative'))
                if get_chk < 0:
                    raise osv.except_osv(_('Warning !'), _('CHK can not be negative'))
                if get_loan < 0:
                    raise osv.except_osv(_('Warning !'), _('Loan amount can not be negative'))
                if get_security < 0:
                    raise osv.except_osv(_('Warning !'), _('Security amount can not be negative'))
                if get_telephone < 0:
                    raise osv.except_osv(_('Warning !'), _('Telephone amount can not be negative'))
                #print"total - get_penalty - get_tds - get_epf + get_conveyance - get_advance - get_loan - get_security - get_telephone - previous_advance....",total,get_penalty,get_tds,get_epf,get_conveyance,get_advance,get_loan,get_security,get_telephone,previous_advance
                grand_total=total - get_penalty - get_tds - get_epf - get_chk + get_conveyance - get_advance - get_loan - get_security - get_telephone - previous_advance
                rnd_grand_total = grand_total
                rnd = grand_total % 10
                if rnd >= 0 and rnd < 3:
                    rnd_grand_total = grand_total - rnd
                elif rnd > 2 and rnd < 6:
                    if rnd == 3:
                        rnd = 2
                    elif rnd == 4:
                        rnd = 1 
                    else:
                        rnd = 0
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
                
                if input_penalty >= TOTAL_PENALTY:
                    old_total_penalty = input_penalty - TOTAL_PENALTY
                else:   
                    old_total_penalty = TOTAL_PENALTY - input_penalty
                
                if old_grand_total <= 0 and rnd_grand_total <= 0:
                    diff_salary = rnd_grand_total
                    
                elif old_grand_total <= 0 and rnd_grand_total >= 0:
                    diff_salary = rnd_grand_total
                
                elif old_grand_total >= 0 and rnd_grand_total >= 0:
                    diff_salary = rnd_grand_total - old_grand_total
                    
                elif old_grand_total >= 0 and rnd_grand_total < 0:
                    diff_salary = rnd_grand_total - old_grand_total
                else:
                    diff_salary = rnd_grand_total - old_grand_total
                
                if val.daily:
                    month=month-holiday_no
                    total_wk_days=days
                    
                else:
                    month=month 
                    total_wk_days=days-holiday_no
                
                self.write(cr ,uid ,ids,{
                        'old_total_days':old_salary_line.days,
                        'old_total_ot':old_salary_line.over_time,
                        'old_total_penalty':old_total_penalty,
                        'old_days_amt':old_salary_line.days_amount,
                        'old_ot_amt':old_salary_line.overtime_amount,
                        'old_oneday_amt':old_salary_line.day_amount,
                        'old_remday_amt':old_salary_line.day_remaining_amount,
                        'old_total_amt':old_salary_line.total_amount,
                        'old_grand_total':old_salary_line.rnd_grand_total,
                        
                        'total_wk_days':total_wk_days,
                        'holiday_no':holiday_no,
                        'day_in_month':month,
                        'new_total_days':days,
                        'new_total_ot':over_time,
                        'new_total_penalty':TOTAL_PENALTY,
                        'new_days_amt':daily_amt,
                        'new_ot_amt':over_time_amt,
                        'new_oneday_amt':day_amount,
                        'new_remday_amt':day_remaining_amount,
                        'new_total_amt':total,
                        'new_grand_total':rnd_grand_total,
                        'diff_salary':diff_salary,})
                    
                    
                print "<----------------------------SALARY CALCULATED----------------------------------->",line.employee_id.sinid,total
        return res
    
    
    