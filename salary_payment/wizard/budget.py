from osv import osv, fields
from tools.translate import _
import os
import base64, urllib
import netsvc

from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import time
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import cStringIO
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf
from PIL import Image
import addons
import csv

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
              }
    
    _defaults = {
                 'date':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 }
    
    def account_budget(self,cr,uid,ids,context=None):
        this=self.browse(cr,uid,ids[0])
        year = this.year_id.name
        year_id = this.year_id.id
        month = this.month
        if int(month) in [1,3,5,7,8,10,12]:
            join_date=year +'-'+month+'-'+'31'
        if int(month) in [4,6,9,11]:
            join_date=year +'-'+month+'-'+'30'
        if int(month) in [2]:
            if int(year) % 4 == 0:
                join_date=year +'-'+month+'-'+'29'
            else:
                join_date=year +'-'+month+'-'+'28'
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
        
        
        #Define the font attributes for header
        fnt2 = Font()
        fnt2.name = 'Arial'
        fnt2.height= 275
        
        #Define the font attributes for header
        content_fnt2 = Font()
        content_fnt2.name ='Arial'
        content_fnt2.height =220
        align_content2 = Alignment()
        align_content2.horz= Alignment.HORZ_CENTER
     
        borders2 = Borders()
        borders2.left = 0x02
        borders2.right = 0x02
        borders2.top = 0x02
        borders2.bottom = 0x02
        
        #The text should be centrally aligned
        align2 = Alignment()
        align2.horz = Alignment.HORZ_CENTER
        align2.vert = Alignment.VERT_CENTER
        
        #We set the backgroundcolour here
        pattern2 = Pattern()
        pattern2.pattern = Pattern.SOLID_PATTERN
        pattern2.pattern_fore_colour =  0x0A

        #apply the above settings to the row(0) header
        style_header2= XFStyle()
        style_header2.font= fnt2
        style_header2.pattern= pattern2
        style_header2.borders = borders2
        style_header2.alignment=align2   
        
        
        
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
        ws.write(0,2,'RO of HOD',style_header)
        ws.col(2).width = 8000
        ws.write(0,3,'Allocated Budget',style_header)
        ws.col(3).width = 8000
        ws.write(0,4,'Salary Amount',style_header)
        ws.col(4).width = 5000
        ws.write(0,5,month_name,style_header)
        ws.col(5).width = 8000
        ws.write(0,6,'Difference',style_header)
        ws.col(6).width = 8000
        ws.write(0,7,'No Of Emp',style_header)
        ws.col(7).width = 8000
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
        emp_obj=self.pool.get('hr.employee')
        pay_obj=self.pool.get('salary.payment.line')
        if this.dept_id:
            cr.execute("select emp.id from hr_employee as emp left join resource_resource " \
             "as res on (emp.resource_id=res.id) left join hr_department as dept on " \
             "(emp.department_id=dept.id) where emp.department_id = '"+str(this.dept_id.id)+"' and " \
             "emp.department_id is not null and res.active=True and emp.joining_date <'"+str(join_date)+"' order by dept.dept_code, " \
             "(substring(emp.sinid, '^[0-9]+'))::int ,substring(emp.sinid, '[^0-9_].*$')")
            temp = cr.fetchall()
            for data in temp:
                if len(data)>0 and data[0] != None:
                    emp_ids.append(data[0])
            
        else:
            cr.execute("select emp.id from hr_employee as emp left join resource_resource " \
             "as res on (emp.resource_id=res.id) left join hr_department as dept on (emp.department_id=dept.id) " \
             "where res.active=True and emp.joining_date <'"+str(join_date)+"' order by dept.dept_code,(substring(emp.sinid, '^[0-9]+'))::int ,substring(emp.sinid, '[^0-9_].*$')")
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
               
        i=1
        dept_dict = {}
        grand = total = pay_total = pay_grand = budget = total_budget = 0.0
        pay_data = False
        flag = True
        count1=0.0
        for each in emp_obj.browse(cr, uid, emp_ids):
            pay_ids = pay_obj.search(cr, uid, [('employee_id','=',each.id),('month','=',this.month),('year_id','=',this.year_id.id),('salary_type','=','Salary')])
            if pay_ids:
                pay_data = pay_obj.browse(cr, uid, pay_ids[0])
            if dept_dict.has_key(str(each.department_id.id)):
                if each.department_id:
                    salary = 0.0
                    if pay_data.employee_id.daily:
                        salary = pay_data.basic * working_day
                    else:
                        salary = pay_data.basic
                    total += salary
                    grand +=  salary
#                    if pay_data.employee_id.id == each.id:
#                        print"ssssssssssssssssssss minssssssssss",count1
#                        count1=count1+1
                    if pay_data and pay_data.employee_id.id == each.id:
                        pay_total += pay_data.total_amount or 0.0
                        pay_grand +=  pay_data.total_amount or 0.0
                        count1=count1+1
                    else:
                        pay_total += 0.0
                        pay_grand += 0.0
               
            elif not each.department_id:
                if flag:
                    i -= 1
                    ws.write(i,3, total)
                    ws.write(i,4, pay_total)
                    if budget:
                        diff = float(budget) - pay_total 
                    else:
                        diff = pay_total
                    if budget and diff > 0:
                        ws.write(i,5, diff,style_header1)
                    elif budget and diff < 0:
                        ws.write(i,5, diff,style_header2)
                    else:
                        ws.write(i,5, diff,style_header2)
                    ws.write(i,6, count1)
                    count1=0.0
                    flag = False
                    i += 1
#                 salary = 0.0
#                 name = '[' + str(each.sinid) +'] '+ str(each.name)
#                 
#                 ws.write(i,0, 'X Department')                
#                 ws.write(i,1,'X Reporting Officer')
#                 ws.write(i,2, name)
#                 
#                 if each.daily:
#                     salary = each.salary * working_day
#                 else:
#                     salary = each.salary
#                 ws.write(i,3, salary)
#                 if pay_data and pay_data.employee_id.id == each.id:
#                     ws.write(i,4,pay_data.total_amount or 0.0)
#                 else:
#                     ws.write(i,4, 0.0)
               
                
                        
            else:
                dept_dict[str(each.department_id.id)] = ''
                
                if i != 1:
                    i -= 1
                    ws.write(i,4, total)
                    ws.write(i,5, pay_total)
                    if budget:
                        diff = float(budget) - pay_total 
                    else:
                        diff = pay_total
                    if budget and diff > 0:
                        ws.write(i,6, diff,style_header1)
                    elif budget and diff < 0:
                        ws.write(i,6, diff,style_header2)
                    else:
                        ws.write(i,6, diff,style_header2)
                    ws.write(i,7, count1)
                    count1=0.0
                    i += 1
                    
                
                if each.department_id:
                    total = pay_total = budget = 0.0
                    salary = 0.0
                    budget = each.department_id.dept_budget
                    dept = '[' + str(each.department_id.dept_code) +'] '+ str(each.department_id.name)
                    ws.write(i,0, dept)
                
                    ws.write(i,1, each.department_id.manager_id and each.department_id.manager_id.name or '')
                    ws.write(i,2, each.department_id.manager_id.parent_id and each.department_id.manager_id.parent_id.name or '')
                    ws.write(i,3, budget)
                    total_budget += budget
                    if pay_data.employee_id.daily:
                        salary = pay_data.basic * working_day
                    else:
                        salary = pay_data.basic
                    total += salary
                    grand +=  salary
#                    if pay_data.employee_id.id == each.id:
#                        print"saaaaaaaaaaaaaallllllllllllllllllllllllllll",count1
#                        count1=count1+1
                    if pay_data and pay_data.employee_id.id == each.id:
                        pay_total += pay_data.total_amount or 0.0
                        pay_grand +=  pay_data.total_amount or 0.0
                        count1=count1+1
                    else:
                        pay_total += 0.0
                        pay_grand += 0.0
                    
                    
                        
                i += 1
                    
        ws.write(i+3,1, 'Grand Total',style_header)
        ws.write(i+3,3, total_budget,style_header)
        ws.write(i+3,4, grand,style_header)
        ws.write(i+3,5, pay_grand,style_header)
        
        diff_grand = total_budget - pay_grand
        
        ws.write(i+3,6, diff_grand,style_header1)
        f = cStringIO.StringIO()
        wb.save(f)
        out=base64.encodestring(f.getvalue())
               
               
               
        return self.write(cr, uid, ids, {'export_data':out, 'filename':'export.xls'}, context=context)
    
    
    def detail_budget(self,cr,uid,ids,context=None):
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
        if int(month) in [1,3,5,7,8,10,12]:
            join_date=year +'-'+month+'-'+'31'
        if int(month) in [4,6,9,11]:
            join_date=year +'-'+month+'-'+'30'
        if int(month) in [2]:
            if int(year) % 4 == 0:
                join_date=year +'-'+month+'-'+'29'
            else:
                join_date=year +'-'+month+'-'+'28'
        
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
        ws.write(0,2,'RO of HOD',style_header)
        ws.col(2).width = 8000
        ws.write(0,3,'Employee Name',style_header)
        ws.col(3).width = 9000
        
        ws.write(0,4,'Designation',style_header)
        ws.col(4).width = 8000
        ws.write(0,5,'Working Days',style_header)
        ws.col(5).width = 5000
        ws.write(0,6,'Working Hours',style_header)
        ws.col(6).width = 5000
        ws.write(0,7,'Working Month',style_header)
        ws.col(7).width = 5000
        
        ws.write(0,8,'Salary Amount',style_header)
        ws.col(8).width = 5000
        ws.write(0,9,month_name,style_header)
        ws.col(9).width = 8000
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
        emp_obj=self.pool.get('hr.employee')
        pay_obj=self.pool.get('salary.payment.line')
        if this.dept_id:
            cr.execute("select emp.id from hr_employee as emp left join resource_resource "\
             "as res on (emp.resource_id=res.id) where emp.department_id = "\
             "'"+str(this.dept_id.id)+"' and emp.department_id is not null and "\
             "res.active=True and emp.joining_date <'"+str(join_date)+"' order by emp.department_id, (substring(emp.sinid, '^[0-9]+'))::int ,substring(emp.sinid, '[^0-9_].*$')")
            temp = cr.fetchall()
            for data in temp:
                if len(data)>0 and data[0] != None:
                    emp_ids.append(data[0])
            
        else:
            cr.execute("select emp.id from hr_employee as emp left join resource_resource "\
             "as res on (emp.resource_id=res.id) where res.active=True and emp.joining_date < '"+str(join_date)+"' order by emp.department_id, "\
             "(substring(emp.sinid, '^[0-9]+'))::int ,substring(emp.sinid, '[^0-9_].*$')")
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
        for each in emp_obj.browse(cr, uid, emp_ids):
            tolal_months = 0
            if not each.joining_date:
                continue
            dt1 = datetime.strptime(each.joining_date,'%Y-%m-%d')
            dt2 = datetime.strptime(time.strftime(DEFAULT_SERVER_DATE_FORMAT),'%Y-%m-%d')
            start_month=dt1.month
            end_months=(dt2.year-dt1.year)*12 + dt2.month+1
            dates=[datetime(year=yr, month=mn, day=1) for (yr, mn) in (
                      ((m - 1) / 12 + dt1.year, (m - 1) % 12 + 1) for m in range(start_month, end_months)
                  )]
            for val in dates:
                tolal_months += 1
            pay_ids = pay_obj.search(cr, uid, [('employee_id','=',each.id),('month','=',this.month),('year_id','=',this.year_id.id),('salary_type','=','Salary')])
            if pay_ids:
                pay_data = pay_obj.browse(cr, uid, pay_ids[0])
            
                i+=1
                if dept_dict.has_key(str(each.department_id.id)):
                    if each.department_id:
                        salary = 0.0
                        dept = '[' + str(each.department_id.dept_code) +'] '+ str(each.department_id.name)
                        ws.write(i,0, dept)
                    
                        ws.write(i,1, each.department_id.manager_id and each.department_id.manager_id.name or '')
                        ws.write(i,2, each.department_id.manager_id.parent_id and each.department_id.manager_id.parent_id.name or '')
                        name = '[' + str(each.sinid) +'] '+ str(each.name)
                        ws.write(i,3, name)
                        ws.write(i,4, each.designation_id and each.designation_id.name or '')
                        ws.write(i,5, pay_data.days or '0.0')
                        ws.write(i,6, pay_data.over_time)
                        ws.write(i,7, str(tolal_months) + ' Month')
                        
                        if pay_data.employee_id.daily:
                            salary = pay_data.basic * working_day
                        else:
                            salary = pay_data.basic
                        ws.write(i,8, salary)
                        if pay_data and pay_data.employee_id.id == each.id:
                            ws.write(i,9,pay_data.total_amount or 0.0)
                        else:
                            ws.write(i,9, 0.0)
                        total += salary
                        grand +=  salary
                        if pay_data and pay_data.employee_id.id == each.id:
                            pay_total += pay_data.total_amount or 0.0
                            pay_grand +=  pay_data.total_amount or 0.0
                        else:
                            pay_total += 0.0
                            pay_grand += 0.0
                            
                elif not each.department_id:
                    salary = 0.0
                    if flag:
                        ws.write(i,0, 'Allocated Budget',style_header)
                        ws.write(i,1, 0.0,style_header)
                        ws.write(i,2, 'Total',style_header)
                        ws.write(i,3, '',style_header)
                        ws.write(i,4, '',style_header)
                        ws.write(i,5, '',style_header)
                        ws.write(i,6, '',style_header)
                        ws.write(i,7, '',style_header)
                        ws.write(i,8, total,style_header)
                        if pay_total:
                            ws.write(i,9,pay_total,style_header)
                        else:
                            ws.write(i,9, 0.0,style_header)
                        if budget:
                            diff = pay_total - float(budget)
                        else:
                            diff = pay_total
                            
                        ws.write(i,10, diff,style_header1)
                        flag = False
                        i += 2
                        total = pay_total = budget = 0.0
                    name = '[' + str(each.sinid) +'] '+ str(each.name)
                    
                    ws.write(i,0, 'X Department')                
                    ws.write(i,1,'X Reporting Officer')
                    ws.write(i,2,'X Reporting Officer')
                    ws.write(i,3, name)
                    ws.write(i,4, each.designation_id and each.designation_id.name or '')
                    ws.write(i,5, pay_data.days or '0.0')
                    ws.write(i,6, pay_data.over_time)
                    ws.write(i,7, str(tolal_months) + ' Month')
                    
                    if pay_data.employee_id.daily:
                            salary = pay_data.basic * working_day
                    else:
                            salary = pay_data.basic
                    ws.write(i,8, salary)
                    if pay_data and pay_data.employee_id.id == each.id:
                        ws.write(i,9,pay_data.total_amount or 0.0)
                    else:
                        ws.write(i,9, 0.0)
                    total += salary
                    grand +=  salary
                    if pay_data and pay_data.employee_id.id == each.id:
                        pay_total += pay_data.total_amount or 0.0
                        pay_grand +=  pay_data.total_amount or 0.0
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
                        ws.write(i,3, '',style_header)
                        ws.write(i,4, '',style_header)
                        ws.write(i,5, '',style_header)
                        ws.write(i,6, '',style_header)
                        ws.write(i,7, '',style_header)
                        ws.write(i,8, total,style_header)
                        if pay_total:
                            ws.write(i,9,pay_total,style_header)
                        else:
                            ws.write(i,9, 0.0,style_header)
                        if budget:
                            diff = pay_total - float(budget)
                        else:
                            diff = pay_total
                            
                        ws.write(i,10, diff,style_header1)
                        i += 2
                    total = pay_total = budget = 0.0
                    if each.department_id:
                        salary = 0.0
                        budget = each.department_id.dept_budget
                        dept = '[' + str(each.department_id.dept_code) +'] '+ str(each.department_id.name)
                        ws.write(i,0, dept)
                    
                        ws.write(i,1, each.department_id.manager_id and each.department_id.manager_id.name or '')
                        ws.write(i,2, each.department_id.manager_id.parent_id and each.department_id.manager_id.parent_id.name or '')
                        name = '[' + str(each.sinid) +'] '+ str(each.name)
                        ws.write(i,3, name)
                        ws.write(i,4, each.designation_id and each.designation_id.name or '')
                        ws.write(i,5, pay_data.days)
                        ws.write(i,6, pay_data.over_time)
                        ws.write(i,7, str(tolal_months) + ' Month')
                        
                        if pay_data.employee_id.daily:
                            salary = pay_data.basic * working_day
                        else:
                            salary = pay_data.basic
                        ws.write(i,8, salary)
                        if pay_data and pay_data.employee_id.id == each.id:
                            ws.write(i,9,pay_data.total_amount or 0.0)
                        else:
                            ws.write(i,9, 0.0)
                        total += salary
                        grand +=  salary
                        if pay_data and pay_data.employee_id.id == each.id:
                            pay_total += pay_data.total_amount or 0.0
                            pay_grand +=  pay_data.total_amount or 0.0
                        else:
                            pay_total += 0.0
                            pay_grand += 0.0
                        
            
                    
        i += 1
                    
        ws.write(i+1,7, 'Total',style_header)
        ws.write(i+1,8, total,style_header)
        ws.write(i+3,7, 'Grand Total',style_header)
        ws.write(i+3,8, grand,style_header)
        ws.write(i+1,9, pay_total,style_header)
        ws.write(i+3,9, pay_grand,style_header)
        
        diff_pay = pay_total - total
        diff_grand = pay_grand - grand
        
        ws.write(i+1,10, diff_pay,style_header1)
        ws.write(i+3,10, diff_grand,style_header1)
        f = cStringIO.StringIO()
        wb.save(f)
        out=base64.encodestring(f.getvalue())
               
               
               
        return self.write(cr, uid, ids, {'export_data':out, 'filename':'export.xls'}, context=context)
