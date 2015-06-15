import time
from osv import osv, fields
from tools.translate import _
import decimal_precision as dp
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
import base64, urllib
import urllib, urllib2
import csv
import cStringIO
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment,  easyxf

class employee_check_deduction(osv.osv):
    _name='employee.check.deduction'
    
    def create(self, cr, uid, vals, context=None):
        year_name = ''
        if 'chk_date' in vals and vals['chk_date']:
            tm_tuple = datetime.strptime(vals['chk_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(employee_check_deduction, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        year_name = ''
        if 'chk_date' in vals and vals['chk_date']:
            tm_tuple = datetime.strptime(vals['chk_date'],'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                year_name = self.pool.get('holiday.year').browse(cr, uid,year_id[0]).name
                vals['year'] = year_name

        res = super(employee_check_deduction, self).write(cr, uid, ids, vals, context)
        return res
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.chk_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.chk_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={
              'name':fields.date('Create Date',readonly=True),
              'chk_date':fields.date('Check Date',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
              'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
              'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'check_amt':fields.float('Check Amt',required=True, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'remark':fields.char('Remark',size=512, readonly=True, select=True, states={'draft': [('readonly', False)]}),
              'user_id':fields.many2one('res.users','Created By',readonly=True),
              'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
              'state':fields.selection([('draft','Draft'),('done','Done'),('messg_sent','Message Sent')],'State',readonly=True),
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
    
    _sql_constraints = [('unique_name_employee_chk_date','unique(employee_id,chk_date)','chk line is already created for this date and employee.')]
    
    def sending_salary_notifications(self,cr,uid,ids,context=None):
        url=''
        usn='openerp4you278697'
        pwd='81975'
        sndr='OPERPU'
        for data in self.browse(cr,uid,ids):
            To=[]
            message=''
            if data.state=='draft':
                if data.employee_id.bank_account_id.name:
                    message= message + "Dear %s,"%(data.employee_id.name)+'\n'+"ID No,%s"%(data.employee_id.sinid)+'\n'+"Bank Acc,%s"%(data.employee_id.bank_account_id.name)+'\n'+'Amount,Rs.%s has been credited in your Acc.'%(data.check_amt)+'\n'+'send by Acc. Dept.'
                else:
                    message= message + "Dear %s,"%(data.employee_id.name)+'\n'+"ID No,%s"%(data.employee_id.sinid)+'\n'+"Bank Acc,XXXXX"+'\n'+'Amount,Rs.%s has been credited in your Acc.'%(data.check_amt)+'\n'+'send by Acc. Dept.'
                if data.employee_id.personal_mobile:
                    mb_no=str(data.employee_id.personal_mobile)
                    To.append(unicode(mb_no[-10:]))
                if len(To) > 0:
                    for rcvr in To:
                        url = 'http://www.sms19.info/ComposeSMS.aspx?'+ urllib.urlencode({"username": usn, "password": pwd,'sender':sndr,'to':rcvr,'message':message,'priority':1,'dnd':1,'unicode':0})
                        time.sleep(5.5)
                        try:
                            result = urllib2.urlopen(url)
                            write_obj=self.write(cr,uid,ids,{'state':'messg_sent'})
                        except urllib2.URLError, e:
                            write_obj=self.write(cr,uid,ids,{'state':'draft'})                    
            else:
                raise osv.except_osv(_('Invalid action !'), _('choose some Draft State.'))
        return "Message Sent Sucessfully"
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        if not employee:
            return res
        cr.execute("select chk_date from employee_check_deduction order by id desc limit 1") 
        temp = cr.fetchall()
        for data in temp:
            if data and len(data) > 0 and data[0] != None:
                date1 = data[0]
                res['value'] = {'chk_date':date1}
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    