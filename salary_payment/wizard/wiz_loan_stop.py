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



class wiz_loan_stop(osv.osv_memory):
    _name="wiz.loan.stop"
   
   
    def stop_done(self,cr,uid,ids,context=None):
        last=[]
        wiz_id=self.browse(cr,uid,ids)
        if wiz_id[0].emp_id :
            loan_ded_id=self.pool.get('loan.deduction').search(cr,uid,[('emp_id','=',wiz_id[0].emp_id.id),('state','=','done')])
            if loan_ded_id:
                loan_ids=self.pool.get('loan.deduction').browse(cr,uid,loan_ded_id)
                p=loan_ids[0].period
                p=p+1
                for val in loan_ids[0].loan_deduct_line:
                    all_line_id=self.pool.get('loan.deduction.line').search(cr,uid,[('loan_deduct_id','in',loan_ded_id)])
                    line_id=self.pool.get('loan.deduction.line').search(cr,uid,[('loan_id','=',wiz_id[0].loan_id.id),('loan_deduct_id','in',loan_ded_id)])
                last=all_line_id[-1:]
                line_ids1=self.pool.get('loan.deduction.line').browse(cr,uid,last)
                #holiday_id=self.pool.get('holiday.list').search(cr,uid,[('id','=',line_ids1[0].loan_id.id+1)])
                holiday_id=self.pool.get('holiday.list').search(cr,uid,[('id','=',line_ids1[0].loan_id.id)])
                holiday_ids=self.pool.get('holiday.list').browse(cr,uid,holiday_id)
                if holiday_ids[0].month == '12':
                    holiday_ids[0].month='1'
                    holiday_ids[0].year_id.id = holiday_ids[0].year_id.id + 1
                    set_holiday_id=self.pool.get('holiday.list').search(cr,uid,[('year_id','=',holiday_ids[0].year_id.id),('month','=',holiday_ids[0].month)])
                    #set_holiday_ids=self.pool.get('holiday.list').browse(cr,uid,set_holiday_id)
                else:
                    holiday_ids[0].month=int(holiday_ids[0].month)
                    (holiday_ids[0].month) = (holiday_ids[0].month) + 1  
                    set_holiday_id=self.pool.get('holiday.list').search(cr,uid,[('year_id','=',holiday_ids[0].year_id.id),('month','=',holiday_ids[0].month)])  
                if set_holiday_id:
                    line_ids=self.pool.get('loan.deduction.line').browse(cr,uid,line_id)
                    if line_ids:
                        cr.execute("""update loan_deduction_line set state=%s where id=%s""",('stop', line_id[0]))
                        cr.execute("""update loan_deduction_line set loan_line_amt=%s where id=%s""",(line_ids[0].loan_line_amt, last[0]))
                        self.pool.get('loan.deduction.line').create(cr,uid,{'loan_deduct_id':loan_ded_id[0],'loan_id':set_holiday_id[0],'loan_line_amt':line_ids1[0].loan_line_amt,'state':'not_paid'})     
                        cr.execute("""update loan_deduction set period=%s where id=%s""",(p, loan_ded_id[0]))
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please check month in Employee Loan Form "))     
                else:
                    raise osv.except_osv(_('Warning !'),_("Please create month in holiday list "))  
        if wiz_id[0].type :
            all_emp=self.pool.get('hr.employee').search(cr,uid,[('type','=',wiz_id[0].type),('active','=',True)])
            all_emp_ids= self.pool.get('hr.employee').browse(cr,uid,all_emp)
            for val in all_emp_ids:
                loan_ded_id=self.pool.get('loan.deduction').search(cr,uid,[('emp_id','=',val.id),('state','=','done')])
                if loan_ded_id:
                    loan_ids=self.pool.get('loan.deduction').browse(cr,uid,loan_ded_id)
                    p=loan_ids[0].period
                    p=p+1
                    for val in loan_ids[0].loan_deduct_line:
                        all_line_id=self.pool.get('loan.deduction.line').search(cr,uid,[('loan_deduct_id','in',loan_ded_id)])
                        line_id=self.pool.get('loan.deduction.line').search(cr,uid,[('loan_id','=',wiz_id[0].loan_id.id),('loan_deduct_id','in',loan_ded_id)])
                    last=all_line_id[-1:]
                    line_ids1=self.pool.get('loan.deduction.line').browse(cr,uid,last)
                    holiday_id=self.pool.get('holiday.list').search(cr,uid,[('id','=',line_ids1[0].loan_id.id)])
                    holiday_ids=self.pool.get('holiday.list').browse(cr,uid,holiday_id)
                    if holiday_ids[0].month == '12':
                        holiday_ids[0].month='1'
                        holiday_ids[0].year_id.id = holiday_ids[0].year_id.id + 1
                        set_holiday_id=self.pool.get('holiday.list').search(cr,uid,[('year_id','=',holiday_ids[0].year_id.id),('month','=',holiday_ids[0].month)])
                        #set_holiday_ids=self.pool.get('holiday.list').browse(cr,uid,set_holiday_id)
                    else:
                        holiday_ids[0].month=int(holiday_ids[0].month)
                        (holiday_ids[0].month) = (holiday_ids[0].month) + 1  
                        set_holiday_id=self.pool.get('holiday.list').search(cr,uid,[('year_id','=',holiday_ids[0].year_id.id),('month','=',holiday_ids[0].month)])  
                    if set_holiday_id:
                        line_ids=self.pool.get('loan.deduction.line').browse(cr,uid,line_id)
                        if line_ids:
                            cr.execute("""update loan_deduction_line set state=%s where id=%s""",('stop', line_id[0]))
                            cr.execute("""update loan_deduction_line set loan_line_amt=%s where id=%s""",(line_ids[0].loan_line_amt, last[0]))
                            self.pool.get('loan.deduction.line').create(cr,uid,{'loan_deduct_id':loan_ded_id[0],'loan_id':set_holiday_id[0],'loan_line_amt':line_ids1[0].loan_line_amt,'state':'not_paid'})     
                            cr.execute("""update loan_deduction set period=%s where id=%s""",(p, loan_ded_id[0]))
                    else:
                        raise osv.except_osv(_('Warning !'),_("Please create month in holiday list ")) 
        return {'type':'ir.actions.act_window_close'}
            
            
               
   
    _columns={
              'emp_id':fields.many2one("hr.employee","Employee" ),
              'loan_id':fields.many2one('holiday.list','Months'),
              'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT'),
              }