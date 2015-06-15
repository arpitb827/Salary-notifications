from osv import osv, fields
from tools.translate import _
import base64, urllib
import netsvc
import os
import re
import time
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import cStringIO
import xlwt
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf
from PIL import Image
import addons
import csv
from tools import amount_to_text_en

class wiz_salary_payment_report(osv.osv_memory):
    _name="wiz.salary.payment.report"
    _columns={
             'month_ids':fields.many2many('holiday.list','holiday_list_tab','curr_id','holiday_list_id',string='From Date'),
#             'year_ids':fields.many2many('holiday.year','year_list_tab','curr_id','year_id',string='Till Date'),
             'department_id':fields.many2one('hr.department',string='Department'),
             'export_data':fields.binary('File',readonly=True),
             'filename':fields.char('File Name',size=250,readonly=True),
             }
    
    
    
    def salary_payment_report(self,cr,uid,ids,context=None):
        #Define the font attributes for header
        fnt = Font()
        fnt.name = 'Arial'
        fnt.size=16
        fnt.style= 'Regular'
        #Define the font attributes for header
        content_fnt = Font()
        content_fnt.name ='Arial'
        content_fnt.size=16
        content_fnt.style= 'Regular'
        align_content = Alignment()
        align_content.horz= Alignment.HORZ_CENTER
        borders = Borders()
        borders.left = 0x01
        borders.right = 0x01
        borders.top = 0x01
        borders.bottom = 0x01
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
        fnt3 = Font()
        fnt3.name = 'Arial'
        fnt3.size=16
        fnt3.style= 'Regular'
        #Define the font attributes for header
        content_fnt3 = Font()
        content_fnt3.name ='Arial'
        content_fnt3.size=16
        content_fnt3.style= 'Regular'
        align_content3 = Alignment()
        align_content3.horz= Alignment.HORZ_CENTER
        borders3 = Borders()
        borders3.left = 0x01
        borders3.right = 0x01
        borders3.top = 0x01
        borders3.bottom = 0x01
        #The text should be centrally aligned
        align3 = Alignment()
        align3.horz = Alignment.HORZ_CENTER
        align3.vert = Alignment.VERT_CENTER
        #We set the backgroundcolour here
        pattern3 = Pattern()
        #apply the above settings to the row(0) header
        style_header3= XFStyle()
        style_header3.font= fnt3
        style_header3.pattern= pattern3
        style_header3.borders = borders3
        style_header3.alignment=align3   
        #Define the font attributes for header
        fnt4 = Font()
        fnt4.name = 'Arial'
        #Define the font attributes for header
        content_fnt4 = Font()
        content_fnt4.name ='Arial'
        align_content4 = Alignment()
        align_content4.horz= Alignment.HORZ_LEFT
     
        borders4 = Borders()
        borders4.left = 0x01
        borders4.right = 0x01
        borders4.top = 0x01
        borders4.bottom = 0x01
        #The text should be centrally aligned
        align4 = Alignment()
        align4.horz = Alignment.HORZ_LEFT
        align4.vert = Alignment.VERT_CENTER
        #We set the backgroundcolour here
        pattern4 = Pattern()
        #apply the above settings to the row(0) header
        style_header4= XFStyle()
        style_header4.font= fnt4
        style_header4.pattern= pattern4
        style_header4.borders = borders4
        style_header4.alignment=align4
        #Define the font attributes for header
        fnt1 = Font()
        fnt1.name = 'Arial'
        fnt1.size=10
        fnt1.Style= 'Regular'
        #Define the font attributes for header
        content_fnt1 = Font()
        content_fnt1.name ='Arial'
        content_fnt1.size=10
        content_fnt1.Style= 'Regular'
        align_content1 = Alignment()
        align_content1.horz= Alignment.HORZ_RIGHT
        borders1 = Borders()
        borders1.left = 0x01
        borders1.right = 0x01
        borders1.top = 0x01
        borders1.bottom = 0x01
        #The text should be centrally aligned
        align1 = Alignment()
        align1.horz = Alignment.HORZ_RIGHT
        align1.vert = Alignment.VERT_CENTER
        #We set the backgroundcolour here
        pattern1 = Pattern()
        #apply the above settings to the row(0) header
        style_header1= XFStyle()
        style_header1.font= fnt1
        style_header1.pattern= pattern1
        style_header1.borders = borders1
        style_header1.alignment=align1      
        #Define the font attributes for header
        fnt2 = Font()
        fnt2.name = 'Arial'
        fnt2.size=16
        fnt2.Style= 'Regular'
        #Define the font attributes for header
        content_fnt2 = Font()
        content_fnt2.name ='Arial'
        content_fnt2.size=16
        content_fnt2.Style= 'Regular'
        align_content2 = Alignment()
        align_content2.horz= Alignment.HORZ_RIGHT
        borders2 = Borders()
        borders2.left = 0x01
        borders2.right = 0x01
        borders2.top = 0x01
        borders2.bottom = 0x01
        #The text should be centrally aligned
        align2 = Alignment()
        align2.horz = Alignment.HORZ_RIGHT
        align2.vert = Alignment.VERT_CENTER
        #We set the backgroundcolour here
        pattern2 = Pattern()
        #apply the above settings to the row(0) header
        style_header2= XFStyle()
        style_header2.font= fnt2
        style_header2.pattern= pattern
        style_header2.borders = borders2
        style_header2.alignment=align2     

        
        wb = Workbook()
        ws = wb.add_sheet('Salary Report')

        this=self.browse(cr,uid,ids[0],context=context)
        ws.row(0).height=300
        ws.row(1).height=300
        ws.row(2).height=300
#        ws.col(0).width = 5000
#        ws.col(0).width = 5000
#        ws.col(0).width = 5000
#        ws.col(0).width = 5000
        
        ws.write_merge(0,0,0,5, 'SALARY REPORT',style_header)
        ws.write_merge(1,1,0,5, ('DEPARTMENT : ',this.department_id.name),style_header)
        ws.write_merge(2,2,0,1, 'Month',style_header)
        ws.write_merge(2,2,2,3, 'Salary Amount',style_header)
        ws.write_merge(2,2,4,5, 'Remark',style_header)
        
        l=[]
        lst=[]
        for val in this.month_ids:
            i = 3
            query="""select  hy.name,spl.month, sum(spl.total_amount) from salary_payment_line as spl left join holiday_year as hy on spl.year_id = hy.id where month = '"""+str(val.month)+"""'
            and year_id = '"""+str(val.year_id.id)+"""' and curr_department = '"""+str(this.department_id.id)+"""' and salary_type='Salary' 
            group by spl.month, hy.name"""
            cr.execute(query)
            temp = cr.fetchall()
            for year,month, total_amount in temp:
                t=()
                mon = int(month)
                t = (year,mon, total_amount)
                lst.append(t)
        total = 0.0
        lst.sort()
        for  year,month, total_amount in lst:
            if month == 1:
                month1 = 'January'
            elif month == 2:
                month1 = 'February'
            elif month == 3:
                month1 = 'March'
            elif month == 4:
                month1 = 'April'
            elif month == 5:
                month1 = 'May'
            elif month == 6:
                month1 = 'June'
            elif month == 7:
                month1 = 'July'
            elif month == 8:
                month1 = 'August'
            elif month == 9:
                month1 = 'September'
            elif month == 10:
                month1 = 'October'
            elif month == 11:
                month1 = 'November'
            else:
                month1 = 'December'
            total += total_amount
            ws.write_merge(i,i,0,1, (month1,' ',year),style_header4)
            ws.write_merge(i,i,2,3, round(total_amount,2),style_header1)
            ws.write_merge(i,i,4,5, ' ',style_header3)
            i += 1
        ws.write_merge(i,i,0,1, 'Total Amount',style_header2)
        ws.write_merge(i,i,2,3, round(total,2),style_header2)
        ws.write_merge(i,i,4,5, ' ',style_header)
        if len(lst) < 1:
            raise osv.except_osv(_('Warning!'),_('No Record found!'))
        f = cStringIO.StringIO()
        wb.save(f)
        out=base64.encodestring(f.getvalue())
               
        sal_report = self.write(cr, uid, ids, {'export_data':out, 'filename':'Salary Report.xls'}, context=context)
        return sal_report
    