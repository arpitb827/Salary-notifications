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

class wiz_salary_payment(osv.osv):
    _name = 'wiz.salary.payment'
    
    def _calculate_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for val in self.browse(cr, uid, ids):
            res[val.id] = val.month and val.month.name or False
        return res
    
    def update_new_salary(self, cr, uid, ids, context=None):
        sline_obj=self.pool.get('salary.payment.line')
        salary_obj=self.pool.get('salary.payment')
        for line1 in self.browse(cr, uid, ids):
            salary_ids = salary_obj.search(cr, uid, [('month','=',line1.month.id),('year_id','=',line1.year_id.id),('salary_type','=',line1.salary_type)])
            for line in line1.salary_payment_line:
                cr.execute("delete from salary_payment_line where employee_id ='"+str(line.employee_id.id)+"' and month = '"+str(line1.month.month)+"' and year_id = '"+str(line1.year_id.id)+"'")
                                
                salary = {
                'salary_id':salary_ids[0],
                'employee_id':line.employee_id.id,
                'department_id':line.department_id.id,
                'basic':line.basic,
                'basic_part1':line.basic_part1,
                'basic_part2':line.basic_part2,
                'days':line.days,
                'days_amount':line.days_amount,
                'over_time':line.over_time,
                'overtime_amount':line.overtime_amount,
                'day_amount':line.day_amount,
                'day_remaining_amount':line.day_remaining_amount,
                'total_amount':line.total_amount,
                'month':line.month,
                'year_id':line.year_id.id,
                'previous_advance':line.previous_advance,
                'current_loan':line.current_loan,
                'panalty':line.panalty,
                'security':line.security,
                'telephone':line.telephone,
                'loan':line.loan,
                'kharcha':line.kharcha,
                'epf':line.epf,
                'tds':line.tds,
                'reward':line.reward,
                'grand_total':line.grand_total,
                'rnd_grand_total':line.rnd_grand_total,
                'type':line.type,
                'employee_type':line.employee_type,
                'difference':line.difference,
                'reason':'Update by Audit',
                'state':line.state,
                'salary_type':line.salary_type,
                }
                
                sline_obj.create(cr, uid, salary)
        return {'type':'ir.actions.act_window_close'}
            
    _columns = {
                'name':fields.function(_calculate_name,method=True,store=True,string='Name',type='char',size=64),
                'month':fields.many2one('holiday.list','Month',required=True),
                'year_id':fields.many2one('holiday.year','Year',required=True),
                'salary_payment_line':fields.one2many('wiz.salary.payment.line','salary_id','Employee Lines'),
                'old_salary_payment_line':fields.one2many('salary.payment.line','wiz_salary_id','Employee Lines',readonly=True),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
                'employee_id':fields.many2one('hr.employee','Employee',required=True),
                
                }
    
    _defaults = {
                 'salary_type':'Salary',
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
    
    def calculate_payment(self, cr, uid, ids, context=None):
        res = {}
        lines = []
        emp_obj = self.pool.get('hr.employee')
        shift_obj = self.pool.get('hr.shift.line')
        att_obj = self.pool.get('attendance.timing')
        salline_obj = self.pool.get('wiz.salary.payment.line')
        
        month = off_day = sunday = 0
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
#                if line.month.month != tm_tuple2.tm_mon:
#                    continue
                for sun in line.month.holiday_lines:
                    if datetime.strptime(next_date1,"%Y-%m-%d").date() == datetime.strptime(sun.leave_date,"%Y-%m-%d").date():
                        if sun.week == 'Sunday':
                            sunday += 1 
                        else:
                            off_day += 1
                next_date += timedelta(days=1)
                wk_day += 1 
#            if wk_day > 1:
#                wk_day += 1 
            
            working_day = wk_day - off_day - sunday
            working_day1 = working_day
            off_day1 = off_day
            sunday1 = sunday
            holiday_date = []
            for leave in line.month.holiday_lines:
                holiday_date.append(leave.leave_date)
            for val in emp_obj.browse(cr, uid, [line.employee_id.id]):
                
                date1 = datetime.strptime(str(line.year_id.name)+'-'+str(line.month.month)+'-'+'1','%Y-%m-%d')
                for i in range(31):
                    emp_ids = emp_obj.search(cr, uid, [('active','=',True)])
                    date2 = date1.strftime('%Y-%m-%d')
                    tm_tuple2 = datetime.strptime(date2,'%Y-%m-%d').timetuple()
                    if line.month.month != tm_tuple2.tm_mon:
                        break
                    for line in emp_obj.browse(cr, uid, [line.employee_id.id]):
                        att_ids = att_obj.search(cr, uid, [('method','=','Manual'),('name','=',date2),('employee_id','=',line.id)])
                        if att_ids:
                            cr.execute("delete from attendance_timing where name='"+str(date2)+"' and method='Auto' and employee_id = '"+str(line.id)+"'")
                    date1 += timedelta(days=1)
                
                if val.monthly:
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
                    
                hrs = 0
                att_list = []
                
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
                        if working_day > 0:
                            basic_part2 = round(val.salary / working_day,0)
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
                    cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and name <= '"+str(end_date)+"' and (status is null or status in ('A_OK','B_Reduced','C_Dept_Absent'))")
                else:
                    cr.execute("select id from attendance_timing where employee_id ='"+str(val.id)+"' and DATE_PART('MONTH',name)='"+str(line.month.month)+"' and (status is null or status in ('A_OK','B_Reduced','C_Dept_Absent'))")
                temp = cr.fetchall()
                for data in temp:
                    att_list.append(data[0])
                
                tick = False
                for rec in att_obj.browse(cr, uid, att_list):
                    if rec.employee_id.type in ['Wood','Metal']:
                        if datetime.strptime(rec.name,'%Y-%m-%d') == datetime.strptime('2013-05-13','%Y-%m-%d'):
                            days = 0
                            tick = False
                            total_days = 0
                            break
                        else:
                            days = 1
                            total_days = 1
                            tick = True
                
                
                for rec in att_obj.browse(cr, uid, att_list):
                    
                    if rec.working == 'P':
                        days += 1
                        day = 1
                        total_days += 1
                    elif rec.working == 'HD':
                        days += 0.5
                        day = 0.5
                        total_days += 1
                    elif rec.working == 'L':
                        days += 0
                        day = 0
                        total_days += 0
                    else:
                        days += 0
                        day = 0
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
                    
                if tick:
                    days -= 1
                    
                
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
                    continue
                
                total_amount = daily_amt + over_time_amt + day_amount + day_remaining_amount
                cr.execute("delete from wiz_salary_payment_line")
                cr.execute("update salary_payment_line set wiz_salary_id=Null")
                old_salary_ids = self.pool.get('salary.payment.line').search(cr, uid, [('employee_id','=',val.id),('month','=',line.month.month),('year_id','=',line.year_id.id)])
                if len(old_salary_ids) == 1:
                    self.pool.get('salary.payment.line').write(cr, uid, [old_salary_ids[0]], {'wiz_salary_id':line.id})
                salline_obj.create(cr, uid, {'salary_id':line.id,'year_id':line.year_id.id,'employee_id':val.id,'basic':val.salary,'basic_part1':basic_part1,
                'basic_part2':basic_part2,'days':days,'days_amount':daily_amt,'over_time':over_time,'overtime_amount':over_time_amt,
                'day_amount':day_amount,'day_remaining_amount':day_remaining_amount,'total_amount':total_amount,'month':line.month.month,'state':'Draft','salary_type':line.salary_type})
                print "<----------------------------SALARY CALCULATED----------------------------------->",total_amount
                
                self.get_paid_salary(cr, uid, ids, context)
                
        return True
    
    def get_paid_salary(self, cr, uid, ids, context=None):
        res = {}
        tds_obj = self.pool.get('payment.management.tds')
        panalty_obj = self.pool.get('payment.management.panalty')
        advance_obj = self.pool.get('payment.management.advance')
        loan_obj = self.pool.get('payment.management.loan')
        line_obj = self.pool.get('wiz.salary.payment.line')
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
                    cr.execute("select line.loan_line_amt from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(each.month.month)+"' and loan.emp_id='"+str(val.employee_id.id)+"' and line.state='not_paid'")
#                    cr.execute("select sum(amount_emi) from payment_management_loan  where month='"+str(each.month.month)+"' and year_id='"+str(val.year_id.id)+"' and employee_id = '"+str(val.employee_id.id)+"'")
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
                    cr.execute("select loan.balance from loan_deduction_line as line left join loan_deduction as " \
                               "loan on (line.loan_deduct_id = loan.id) left join holiday_list as holi on (line.loan_id = holi.id) " \
                               "where holi.month='"+str(each.month.month)+"' and loan.emp_id='"+str(val.employee_id.id)+"' and line.state='not_paid'")
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

class wiz_salary_payment_line(osv.osv):
    _name = 'wiz.salary.payment.line'
    _order = 'employee_id'
    



    _columns = {
                'salary_id':fields.many2one('wiz.salary.payment','Salary',ondelete="cascade"),
                'employee_id':fields.many2one('hr.employee','Employee',required=True,readonly=True),
                'department_id':fields.related('employee_id','department_id',relation='hr.department',string='Department',type="many2one",readonly=True),
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
                'reward':fields.float('Reward',digits_compute= dp.get_precision('Account'),required=True, readonly=True),
                'grand_total':fields.float('Grd Total',digits_compute= dp.get_precision('Account'),readonly=True),
                'rnd_grand_total':fields.float('Rnd Grd Total',digits_compute= dp.get_precision('Account'), readonly=True),
                'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
                'employee_type':fields.related('employee_id','employee_type',selection=[('employee','Employees'), ('artisian','Artisian'),('contractor','Inhouse Contractors')],string='Employee Type',type="selection",readonly=True),
                'difference':fields.float('Difference',digits_compute= dp.get_precision('Account')),
                'reason':fields.char('Reason',size=255),
                'state':fields.selection([('Draft','Draft'),('Paid','Paid')],'Status',readonly=True),
                'salary_type':fields.selection([('Kharcha','Kharcha'),('Salary','Salary')],'Salary Type',required=True),
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
                 'security':0.0,
                 'telephone':0.0,
                 }
    
   
    def unlink(self, cr, uid, ids, context=None):
        order = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for line in order:
            if line['state'] in ['Draft']:
                unlink_ids.append(line['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete Paid Salary.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    def payment_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Paid'})
        return True
    def payment_reset(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Draft'})
        return True