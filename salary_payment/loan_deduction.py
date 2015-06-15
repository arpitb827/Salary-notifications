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

class loan_deduction(osv.osv):
    _name = "loan.deduction"
    
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d %H:%M:%S').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.name,'%Y-%m-%d %H:%M:%S').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns={ 

                'name':fields.datetime('Creation Date',required = True),
                'emp_id':fields.many2one("hr.employee","Employee" ,required=True),
                'loan_amt':fields.float('Loan Amount',digits=(16,2),required=True),
                'emi':fields.float('EMI',digits=(16,2),required=True),
                'balance':fields.float('Balance',digits=(16,2)),           
                'period':fields.integer('Period (months)'),
                'loan_deduct_line':fields.one2many('loan.deduction.line','loan_deduct_id','Loan Deduction Lines'),
                'state':fields.selection([('draft','Draft'),('done','Done'),('stop','Stop')],'State',readonly=True),
                'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
                'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
                'approved':fields.many2one("hr.employee","Approved By" ,required=True),
                'type':fields.selection([('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],'Working AT',required=True,),

              }
    _defaults = {'state':'draft',
                 'name': lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                 } 
    
    def loan_fix(self, cr, uid, ids, context=None):
        for val in self.browse(cr, uid, self.search(cr, uid,[])):
            tm = datetime.strptime(val.name,'%Y-%m-%d %H:%M:%S').timetuple()
            month = tm.tm_mon
            year = tm.tm_year
            for line in val.loan_deduct_line:
                if month == 1:
                    new_mon = 'January'
                elif month == 2:
                    new_mon = 'February'
                elif month == 3:
                    new_mon = 'March'
                elif month == 4:
                    new_mon = 'April'
                elif month == 5:
                    new_mon = 'May'
                elif month == 6:
                    new_mon = 'June'
                elif month == 7:
                    new_mon = 'July'
                elif month == 8:
                    new_mon = 'August'
                elif month == 9:
                    new_mon = 'September'
                elif month == 10:
                    new_mon = 'October'
                elif month == 11:
                    new_mon = 'November'
                else:
                    new_mon = 'December'
                    month = 0
                mon_year = new_mon +' '+ str(year)
                if new_mon == 'December':
                    year = year + 1
                month += 1
                hol_obj = self.pool.get('holiday.list').search(cr, uid, [('name','=',mon_year)])
                if hol_obj and len(hol_obj) == 1:
                    self.pool.get('loan.deduction.line').write(cr,uid,[line.id],{'loan_id':hol_obj[0]})
                else:
                    pass
        return True
            
    
    def done_security(self, cr, uid, ids,context=None):
        res = {}
        loan_type=self.browse(cr,uid,ids[0])
        loan_deduct_line = loan_type.loan_deduct_line
        for val in loan_deduct_line:        
            if val.state == 'not_paid':
                self.pool.get('loan.deduction.line').write(cr, uid,[val.id],{'state':'stop',})
        balance1 = loan_type.balance
        loan_amt1 = loan_type.loan_amt
        if balance1 == 0.0:
            self.pool.get('loan.deduction').write(cr, uid,[loan_type.id],{'state':'stop',})
        else:
            self.pool.get('loan.deduction').write(cr, uid,[loan_type.id],{'state':'stop',})
              
        return res   
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Allows to delete order in draft,cancel states"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['draft']:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a line which is in state \'%s\'!') %(rec.state,))
        return super(loan_deduction, self).unlink(cr, uid, ids, context=context)
     
    def time_period(self, cr, uid, ids,emi,loan_amt, context=None):
        res = {}
        period1 = 0
        if emi and loan_amt:
            period1 = float(loan_amt)/float(emi) or 0.0
            if int(period1) < period1:
                period1 = int(period1) + 1
        res = {'value': {'period': period1,'balance': loan_amt}}
        return res 
    
    def onchange_emp_id(self, cr, uid, ids, emp_id, context=None):
        res = {}
        if emp_id:
            employee_data = self.pool.get('hr.employee').browse(cr, uid, emp_id)
            res['value'] = {'type':employee_data.type}
        return res
        
    def calculate_month(self, cr, uid, ids, context=None):
        res = {}
        res1 = {}
        mon_obj =self.pool.get('loan.deduction').browse(cr,uid,ids[0]) 
        for data in self.browse(cr,uid,ids):
            existing_id = self.search(cr, uid, [('emp_id','=',data.emp_id.id),('state','=','done')])
            if existing_id:
                raise osv.except_osv(_('Invalid action !'), _('You cannot have two active loan at the same time. Delete this record to proceed further.'))
            m =0
            period = data.period 
            while (m < period):
                tm=datetime.strptime((datetime.strptime(data.name,'%Y-%m-%d %H:%M:%S')+relativedelta(months=m)).strftime('%Y-%m-%d'),'%Y-%m-%d')
                tm_tuple = tm.timetuple()
                month = tm_tuple.tm_mon
                year = tm_tuple.tm_year
                if month == 1:
                    new_mon = 'January'
                elif month == 2:
                    new_mon = 'February'
                elif month == 3:
                    new_mon = 'March'
                elif month == 4:
                    new_mon = 'April'
                elif month == 5:
                    new_mon = 'May'
                elif month == 6:
                    new_mon = 'June'
                elif month == 7:
                    new_mon = 'July'
                elif month == 8:
                    new_mon = 'August'
                elif month == 9:
                    new_mon = 'September'
                elif month == 10:
                    new_mon = 'October'
                elif month == 11:
                    new_mon = 'November'
                else:
                    new_mon = 'December'
                    month = 0
                mon_year = new_mon +' '+ str(year)
                if new_mon == 'December':
                    year = int(year) + 1
                month += 1
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
                    
                    #cr.execute("delete from loan_deduction_line where loan_id = '"+str(val)+"'")     
                    a1 = self.pool.get('loan.deduction.line').create(cr,uid,{'name':time.strftime(DEFAULT_SERVER_DATE_FORMAT),'loan_id':val,'loan_line_amt':emi,'loan_deduct_id':data.id})
                m = m+1
                if data.loan_amt < data.emi:
                    raise osv.except_osv(_('Invalid action !'), _('Loan EMI cannot be greater than loan amount.'))
                if mon_obj.state == 'draft':
                    self.pool.get('loan.deduction').write(cr, uid,[mon_obj.id],{'state':'done',})
                else:
                    return True               
        return res
loan_deduction()

class loan_deduction_line(osv.osv):
    _name = "loan.deduction.line"
    _columns={ 
                'name':fields.date('Create Date',readonly=True),
                'loan_deduct_id':fields.many2one('loan.deduction','Loan Deduction'),
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
        raise osv.except_osv(_('Invalid action !'), _('Cannot delete a loan line.!'))
        return super(loan_deduction_line, self).unlink(cr, uid, ids, context=context)
       
    def balance_paid(self, cr, uid, ids, context=None):
        ded_line_obj=self.pool.get('loan.deduction.line')
        for val in self.browse(cr, uid, ids):
            balance = val.loan_deduct_id.balance - val.loan_line_amt
            ded_ids = ded_line_obj.search(cr, uid, [('id','<',val.id),('state','=','not_paid'),('loan_deduct_id','=',val.loan_deduct_id.id)])
            if ded_ids:
                raise osv.except_osv(_('Invalid action !'), _('You have not paid EMI for previous months'))
            if balance < 0:
                raise osv.except_osv(_('Invalid action !'), _('Balance cannot be negative.'))
            if balance == 0:
                self.pool.get('loan.deduction').write(cr, uid,[val.loan_deduct_id.id],{'balance':balance,'state':'stop'})
            else:
                self.pool.get('loan.deduction').write(cr, uid,[val.loan_deduct_id.id],{'balance':balance})
            if val.state == 'not_paid':
                self.write(cr, uid,[val.id],{'state':'paid',})
        return True
       
#     def balance_paid(self, cr, uid, ids, context=None):
#     
#         res = {}
#         res1 = {}
#         month = 0
#         ded_line_obj=self.pool.get('loan.deduction.line')
#         line_data = ded_line_obj.browse(cr,uid,ids[0])
#         amount=line_data.loan_line_amt
#         loan_type1=line_data.loan_deduct_id
#         loan_type3=line_data
#         if loan_type3.state == 'not_paid':
#             self.pool.get('loan.deduction.line').write(cr, uid,[loan_type3.id],{'state':'paid',})
#         else:
#             return True
#         new_period = 0.0
#         balance1 = loan_type1.balance - amount
#         flag=False
#         loan_type2=loan_type1.loan_deduct_line
#         flag=False
#         for val3 in loan_type2:
#             state=val3.state
#             if flag == True:
#                 continue
#             if not (loan_type3.id <> val3.id):
#                 flag=True
#         
#         if state=='not_paid' and flag == False:
#             raise osv.except_osv(_('Invalid action !'), _('You have not paid EMI for previous months'))
#         
#         for val3 in loan_type2:
#             if not (loan_type3.id <> val3.id):
#                 flag=True
#             if flag ==True and( not (loan_type3.id <> val3.id)):
#                 pass
#             elif flag ==True and val3.state == 'not_paid':
#                 a=ded_line_obj.unlink(cr ,uid ,[val3.id] )
#         month=int(loan_type3.loan_id.month)
#         year=str(loan_type3.loan_id.year_id.name)
#         if balance1 < 0:
#             raise osv.except_osv(_('Invalid action !'), _('Balance cannot be negative.'))
#         if balance1 == 0:
#             self.pool.get('loan.deduction').write(cr, uid,[loan_type1.id],{'balance':balance1,'state':'stop'})
#         else:
#             self.pool.get('loan.deduction').write(cr, uid,[loan_type1.id],{'balance':balance1})
#         period = float(balance1)/float(loan_type1.emi) or 0.0
#         if int(period) < period:
#             period3 = int(period) + 1
#         else:
#             period3 = period   
#         period3=int(period3)
#         bal1=balance1
#         m = 1
#         for data in range(period3):
#             if month == 1:
#                 new_mon = 'January'
#             elif month == 2:
#                 new_mon = 'February'
#             elif month == 3:
#                 new_mon = 'March'
#             elif month == 4:
#                 new_mon = 'April'
#             elif month == 5:
#                 new_mon = 'May'
#             elif month == 6:
#                 new_mon = 'June'
#             elif month == 7:
#                 new_mon = 'July'
#             elif month == 8:
#                 new_mon = 'August'
#             elif month == 9:
#                 new_mon = 'September'
#             elif month == 10:
#                 new_mon = 'October'
#             elif month == 11:
#                 new_mon = 'November'
#             else:
#                 new_mon = 'December'
#                 month = 0
#             mon_year = new_mon +' '+ str(year)
#             if new_mon == 'December':
#                 year = int(year) + 1
#             month += 1
#             hol_obj = self.pool.get('holiday.list').search(cr, uid, [('name','=',mon_year)])
#             new_period1 = 0.0
#             period1 = float(balance1)/float(loan_type1.emi) or 0.0
#             if int(period1) < period1:
#                 new_period1 = period1 - int(period1)
#             for val in hol_obj:
#                 if m <= int(period1):
#                     emi = loan_type1.emi
#                 else:
#                     emi = loan_type1.emi * new_period1
#             a=self.pool.get('loan.deduction.line').create(cr,uid,{'loan_id':val,'loan_line_amt':emi,'loan_deduct_id':loan_type1.id})
#             m = m + 1
#         if line_data.state == 'not_paid':
#             self.pool.get('loan.deduction.line').write(cr, uid,[line_data.id],{'state':'paid',})
#         else:
#             return True                      
#         
#           
#         return {
#                     'name':'Loan Deduction',
#                     'res_model':'loan.deduction',
#                     'type':'ir.actions.act_window',
#                     'view_type':'form',
#                     'view_mode':'form,tree',
#                     'target':'current',
#                     'res_id':int(loan_type1.id),
#                     'nodestroy': True,
#                     'context':context.update({'active_model':'loan.deduction','active_ids':[loan_type1.id],'active_id':loan_type1.id}),
#                     'domain':[('id','in',[loan_type1.id])],
#                 }
loan_deduction_line()
