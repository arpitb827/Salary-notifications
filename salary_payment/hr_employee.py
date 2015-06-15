from osv import osv,fields
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import decimal_precision as dp
from tools.translate import _


class hr_employee(osv.osv):
    _inherit="hr.employee"
    
        
    def _empsalary(self, cr, uid, ids, prop, unknow_none, context=None):
        res={}
        for val in self.browse(cr,uid,ids,context):
            pf = 0.0
#            if val.salary==0.0:
#                raise osv.except_osv(('Warning'),("Please Enter Salary"))  
            if val.daily:  
                res[val.id]=val.salary
                
            if val.monthly:
                if val.pf:
                    if val.salary > 6500:
                        pf = 780
                    else:
                        pf = val.salary * 0.12
                    res[val.id]=val.salary - pf
                else:
                    sal=val.salary   
                    res[val.id]=sal  

    
        
                         
        return res   
    
       
    def _calpf(self, cr, uid, ids, prop, unknow_none, context=None):
        res={} 
        pf = 0.0
        for val in self.browse(cr,uid,ids,context):
            if val.monthly:
                if val.salary > 6500:
                    pf = 780
                else:
                    pf = val.salary * 0.12
            res[val.id]=pf  
    
    
        return res
    
    
    
    def _calcsh(self, cr, uid, ids, prop, unknow_none, context=None):
        res={}
        for val in self.browse(cr,uid,ids,context):
            cs = 0.0
            if val.monthly:
                if val.pf:
                    if val.salary > 6500:
                        cs = 884.65
                    else:
                        cs = val.salary * 0.1361
                res[val.id]=cs
                
    
        return res
    
    
    _columns={"emp_id":fields.many2one("hr.employee","Employee Name"),
              "daily":fields.boolean("Daily"),
              "monthly":fields.boolean("Monthly"),
              "salary":fields.float("Current Salary"),
              "new_salary":fields.float("Joining Salary"),
              "pf":fields.boolean("PF"),
#              "payable":fields.function(_empsalary,method=True,type='float',string="Payable",store=True,),
#              "pfsh":fields.function(_calpf,method=True,type='float',string="pf",store=True,),
#             "cashshare":fields.function(_calcsh,method=True,type='float',string="Company Share",store=True,),
             "state1":fields.selection([("draft","Draft"),("confirmed","Confirmed")],"state",readonly=True),
             'salary_line':fields.one2many('employee.salary','employee_id','Salary Lines'),
              }
    
    def onchange_daily(self,cr,uid,ids,process):
        res={}
        if process:
            res['value']={ 'monthly':False,}
        return res
    
    def onchange_monthly(self,cr,uid,ids,process):
        res={}
        if process:
            res['value']={ 'daily':False,}
        return res
    
    def draft_con(self,cr,uid,ids,context=None):
        for vals in self.browse(cr,uid,ids,context=None):
            if vals.state1=="draft":
                self.write(cr,uid,ids,{"state1":'confirmed'})
        return True    
    

    
    _sql_constraints=[('unique_searial_no','unique(emp_id)','Name must be unique !')]
          
     
    _defaults={"state1":'draft',}
    
class employee_salary(osv.osv):
    _name = 'employee.salary'
    
    def _calculate_month(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.increment_date,'%Y-%m-%d').timetuple()
            month = tm_tuple.tm_mon
            res[each.id] = month     
        return res
    
    def _calculate_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        for each in self.browse(cr, uid, ids):
            tm_tuple = datetime.strptime(each.increment_date,'%Y-%m-%d').timetuple()
            year = tm_tuple.tm_year
            year_id = self.pool.get('holiday.year').search(cr, uid, [('name','=',year)])
            if year_id:
                res[each.id] = year_id[0]  
            else:
                raise osv.except_osv(_('Invalid action !'), _('Unable to found year specified.!'))
        return res
    
    
    _columns = {
                'employee_id':fields.many2one('hr.employee','Employee',required=True,readonly=True, states={'draft': [('readonly', False)]}),
                'department_id':fields.related('employee_id','department_id',relation='hr.department',string='Department',type="many2one",readonly=True,store=True),
                'designation_id':fields.related('employee_id','designation_id',relation='hr.designation',string='Designation',type="many2one",readonly=True,store=True),
                'salary_type':fields.selection([('Daily','Daily'),('Monthly','Monthly')],'Salary Type',required=True,readonly=True, states={'draft': [('readonly', False)]}),
                'increment_date':fields.date('Increment Date',required=True,readonly=True, states={'draft': [('readonly', False)]}),
                'old_salary':fields.float('Old Salary',digits=(16,2),required=True,readonly=True, states={'draft': [('readonly', False)]}),
                'increment_amt':fields.float('Increment Amt.',digits=(16,2),required=True,readonly=True, states={'draft': [('readonly', False)]}),
                'month':fields.function(_calculate_month,method=True,type='integer',string='Month',store=True),
                'year_id':fields.function(_calculate_year,relation="holiday.year",method=True,type='many2one',string='Year',store=True),
                'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
                'type':fields.related('employee_id','type',selection=[('Wood','Wood'),('Metal','Metal'),('Lohia','Lohia'),('Kashipur','Kashipur'),('Lodhipur','Lodhipur'),('Prabhat Market','Prabhat Market'),('Galshahid','Galshahid'),('Rajan','Rajan ENC'),('LB Unit-III','LB Unit-III')],string='Working AT',type="selection",readonly=True),
                }
    _defaults = {
                 'increment_date':time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 'state':'draft',
                 }
    
    _sql_constraints = [('unique_employee_month_year','unique(employee_id,increment_date)','Employee salary line for this date is already exist.')]
    
    def create(self, cr, uid, vals, context=None):
        hr_obj = self.pool.get('hr.employee')
        old = new = curr = 0.0
        if 'increment_amt' in vals and vals['increment_amt'] and 'employee_id' in vals and vals['employee_id']:
            old = hr_obj.browse(cr, uid, hr_obj.search(cr, uid, [('id','=',vals['employee_id'])]))
            if not old:
                raise osv.except_osv(('Warning'),("Current salary is zero, waiting for updation."))
            else:
                curr = old[0].new_salary
                old = old[0].salary
            new = old + vals['increment_amt']
            if new <> 0.0 and curr > 0.0:
                hr_obj.write(cr, uid, [vals['employee_id']], {'salary':new,'daily':True if vals['salary_type'] == 'Daily' else False,'monthly':True if vals['salary_type'] == 'Monthly' else False,})
            if new <> 0.0 and curr == 0.0:
                hr_obj.write(cr, uid, [vals['employee_id']], {'salary':new,'new_salary':new,'daily':True if vals['salary_type'] == 'Daily' else False,'monthly':True if vals['salary_type'] == 'Monthly' else False,})
                
        if 'increment_amt' in vals and vals['increment_amt'] <> 0.0:
            vals.update({'state':'done'})
        
        res = super(employee_salary, self).create(cr, uid, vals)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        hr_obj = self.pool.get('hr.employee')
        old = new = 0.0
        for each in self.browse(cr, uid, ids):
            emp_id = each.employee_id and each.employee_id.id or False
            old = each.employee_id and each.employee_id.salary or 0.0
        
        if 'increment_amt' in vals and vals['increment_amt'] and 'employee_id' in vals and vals['employee_id']:
            old = hr_obj.browse(cr, uid, hr_obj.search(cr, uid, [('id','=',vals['employee_id'])]))
            if not old:
                raise osv.except_osv(('Warning'),("Current salary is zero, waiting for updation."))
            else:
                old = old[0].salary
            new = old + vals['increment_amt']
            if new <> 0.0:
                hr_obj.write(cr, uid, [vals['employee_id']], {'salary':new})
        
        if 'increment_amt' in vals and vals['increment_amt'] and 'salary_type' in vals and vals['salary_type']:
            new = old + vals['increment_amt']
            if new <> 0.0:
                hr_obj.write(cr, uid, [emp_id], {'salary':new,'daily':True if vals['salary_type'] == 'Daily' else False,'monthly':True if vals['salary_type'] == 'Monthly' else False,})
        
        elif 'increment_amt' in vals and vals['increment_amt']:
            new = old + vals['increment_amt']
            if new <> 0.0:
                hr_obj.write(cr, uid, [emp_id], {'salary':new})
        
        if new == 0.0:
            raise osv.except_osv(('Warning'),("Unable to process, increment amount is zero."))
        vals['state'] = 'done'
        
        res = super(employee_salary, self).write(cr, uid, ids, vals)
        return res
    
    def onchange_employee(self, cr, uid, ids, employee, context=None):
        res = {}
        salary_type = False
        if not employee:
            res['value'] = {'old_salary':0.0,'salary_type':salary_type}
            return res
        employee_data = self.pool.get('hr.employee').browse(cr, uid, employee)
        if employee_data.daily:
            salary_type = 'Daily'
        elif employee_data.monthly:
            salary_type = 'Monthly'
        else:
            salary_type = False
            
        res['value'] = {'old_salary':employee_data.salary,'salary_type':salary_type}
        return res
    
    
    def unlink(self, cr, uid, ids, context=None):
        
        unlink_ids = []
        for line in self.browse(cr, uid, ids, context):
            if line.state in ['draft']:
                unlink_ids.append(line.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('You cannot delete posted entry.'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
    
    
    
    