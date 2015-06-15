from osv import osv,fields
import base64, urllib
import netsvc
import os
import re
from tools.translate import _
import time
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class security_deposit(osv.osv):
    _name = "security.deposit"
    _columns={ 

                'name':fields.datetime('Creation Date',required = True),
                'emp_id':fields.many2one("hr.employee","Employee",required=True),
                'loan_amt':fields.float('Security Amount',digits=(16,2),required=True),
                'emi':fields.float('EMI',digits=(16,2),required=True),
                'balance':fields.float('Total Deposit',digits=(16,2),readonly=True),           
                'period':fields.integer('Period (months)'),
                'security_deposit_line':fields.one2many('security.deposit.line','security_deposit_id','Security Deposit Lines'),
                'approved':fields.many2one("hr.employee","Approved By"),
                'state':fields.selection([('draft','Draft'),('done','Done'),('stop','Stop')],'State',readonly=True),
              }
    _defaults = {'state':'draft',
                 'name': lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
               
                 }
    def done_security(self, cr, uid, ids,context=None):
        res = {}
        loan_type=self.browse(cr,uid,ids[0])
        balance1 = loan_type.balance
        loan_amt1 = loan_type.loan_amt
        approved=loan_type.approved.id
        security_deposit_line = loan_type.security_deposit_line
        
        for val in security_deposit_line:        
            if val.state == 'not_paid':
                self.pool.get('security.deposit.line').write(cr, uid,[val.id],{'state':'stop',})
        if not approved :
            raise osv.except_osv(_('Invalid action !'), _("Please fill responsible person(Approving Authority Name) in 'Approved by' field"))
        
        self.pool.get('security.deposit').write(cr, uid,[loan_type.id],{'state':'stop',})
        return res  

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Allows to delete order in draft,cancel states"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['draft']:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a line which is in state \'%s\'!') %(rec.state,))
        return super(security_deposit, self).unlink(cr, uid, ids, context=context)
    
    
      
    def time_period(self, cr, uid, ids,emi,loan_amt, context=None):
        res = {}
        period1 = 0
        if emi and loan_amt:
            period1 = float(loan_amt)/float(emi) or 0.0
            if int(period1) < period1:
                period1 = int(period1) + 1
        res = {'value': {'period': period1,}}
        return res 
    
    def calculate_month(self, cr, uid, ids,period,context=None):
        res = {}
        res1 = {}
        mon_obj =self.pool.get('security.deposit').browse(cr,uid,ids[0])
        for data in self.browse(cr,uid,ids):
            if data.loan_amt <= 0 and data.emi <= 0:
                raise osv.except_osv(_('Invalid action !'), _('Security Amount and EMI cannot equals to or less than zero.'))
            m =0
            period = data.period 
            while (m < period): 
                   tm=datetime.strptime((datetime.strptime(data.name,'%Y-%m-%d %H:%M:%S')+relativedelta(months=+m)).strftime('%Y-%m-%d'),'%Y-%m-%d')
                   tm_tuple = tm.timetuple()
                   month = tm_tuple.tm_mon
                   if month == 1:
                       month = 'January'
                   elif month == 2:
                       month = 'February'
                   elif month == 3:
                       month = 'March'
                   elif month == 4:
                       month = 'April'
                   elif month == 5:
                       month = 'May'
                   elif month == 6:
                       month = 'June'
                   elif month == 7:
                       month = 'July'
                   elif month == 8:
                       month = 'August'
                   elif month == 9:
                       month = 'September'
                   elif month == 10:
                       month = 'October'
                   elif month == 11:
                       month = 'November'
                   else:
                       month = 'December'
                   year = tm_tuple.tm_year
                   res1[id] = month +' '+ str(year)
                   mon_year = res1[id]
                   hol_obj = self.pool.get('holiday.list').search(cr, uid, [('name','=',mon_year)])
                   new_period1 = 0.0
                   period1 = float(data.loan_amt)/float(data.emi) or 0.0
                   if int(period1) < period1:
                       new_period1 = period1 - int(period1)
                   for val in hol_obj:
                       if m < int(period1):
                           emi = data.emi
                       else:
                           emi = data.emi * new_period1
#                       cr.execute("delete from security_deposit_line where loan_id = '"+str(val)+"'")     
                       a1 = self.pool.get('security.deposit.line').create(cr,uid,{'loan_id':val,'loan_line_amt':emi,'security_deposit_id':data.id})
                   m = m+1
            if data.loan_amt < data.emi:
                raise osv.except_osv(_('Invalid action !'), _('Security EMI cannot be greater than security amount.'))
        if mon_obj.state == 'draft':
               self.pool.get('security.deposit').write(cr, uid,[mon_obj.id],{'state':'done',})
        else:
               return True                          
        return res
security_deposit()

class security_deposit_line(osv.osv):
    _name = "security.deposit.line"
    _columns={ 'name':fields.date('Create Date',readonly=True),
                'security_deposit_id':fields.many2one('security.deposit','security deposit'),
                'loan_line_amt':fields.float('Amount',digits=(16,2)),
                'loan_id':fields.many2one('holiday.list','Months',ondelete="cascade"),
                'state':fields.selection([('not_paid','Not Paid'),('paid','Paid'),('stop','Stop')],'State',readonly=True),
                
              }
    _defaults = {
                 'state':'not_paid',
                 'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 }
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Allows to delete order in draft,cancel states"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['not_paid']:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a line which is in state \'%s\'!') %(rec.state,))
        return super(security_deposit_line, self).unlink(cr, uid, ids, context=context)
    
    
         
    def balance_paid(self, cr, uid, ids, context=None):
        res = {}
        res1 = {}
        month = 0
        ded_line_obj=self.pool.get('security.deposit.line')
        line_data = ded_line_obj.browse(cr,uid,ids[0])
        amount=line_data.loan_line_amt
        loan_type1=line_data.security_deposit_id
        loan_type3=line_data
        if loan_type3.state == 'not_paid':
            self.pool.get('security.deposit.line').write(cr, uid,[loan_type3.id],{'state':'paid',})
        else:
            return True
        new_period = 0.0
        balance1 = loan_type1.balance + amount
        balance2 =  loan_type1.loan_amt - balance1
        print ".....balance2...........",balance2
        flag=False
        loan_type2=loan_type1.security_deposit_line
        flag=False
        for val3 in loan_type2:
           state=val3.state
           if flag == True:
               continue
           if not (loan_type3.id <> val3.id):
               flag=True
           if state=='not_paid' and flag == False:
               raise osv.except_osv(_('Invalid action !'), _('You have not paid EMI for previous months'))
        for val3 in loan_type2:
           if not (loan_type3.id <> val3.id):
               flag=True
           if flag ==True and( not (loan_type3.id <> val3.id)):
               print "skipped id..................",val3.id
           elif flag ==True and val3.state == 'not_paid':
               print "val3.id..................",val3.id
               a=ded_line_obj.unlink(cr ,uid ,[val3.id] )
        month=loan_type3.loan_id.month
        year=loan_type3.loan_id.year_id.name
        print ".....balance1...........",balance1
        
        self.pool.get('security.deposit').write(cr, uid,[loan_type1.id],{'balance':balance1,})
        period = float(balance2)/float(loan_type1.emi) or 0.0
        if int(period) < period:
           period3 = int(period) + 1
        else:
           period3 = period   
        period3=int(period3)
        bal1=balance1
        m = 1
        for data in range(period3):
             
                if month == 12:
                    month = 0
                    year = int(year) + 1
                month=int(month)+1
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
                res1[id] = month1 +' '+ str(year)
                mon_year = res1[id]
                hol_obj = self.pool.get('holiday.list').search(cr, uid, [('name','=',mon_year)])
                new_period1 = 0.0
                period1 = float(balance2)/float(loan_type1.emi) or 0.0
                if int(period1) < period1:
                    new_period1 = period1 - int(period1)
                for val in hol_obj:
                    if m <= int(period1):
                        emi = loan_type1.emi
                    else:
                        emi = loan_type1.emi * new_period1
                self.pool.get('security.deposit.line').create(cr,uid,{'loan_id':val,'loan_line_amt':emi,'security_deposit_id':loan_type1.id})
                m = m + 1
        if line_data.state == 'not_paid':
            self.pool.get('security.deposit.line').write(cr, uid,[line_data.id],{'state':'paid',})
        else:
            return True   
        return {
                    'name':'Security Deposit',
                    'res_model':'security.deposit',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'view_mode':'form,tree',
                    'target':'current',
                    'res_id':int(loan_type1.id),
                    'nodestroy': True,
                    'context':context.update({'active_model':'security.deposit','active_ids':[loan_type1.id],'active_id':loan_type1.id}),
                    'domain':[('id','in',[loan_type1.id])],
                }                 
security_deposit_line()
