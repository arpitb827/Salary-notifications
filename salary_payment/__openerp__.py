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

{
    "name": "Salary Payment",
    "version": "1.0",
    "depends": ["base","attendance_synchronize"],
    "author": "Robin Bahadur",
    "category": "Custom",
    "description": """
    This module provide salary of employee based on attendance,
    salary is calculated over attendance, penalty and over time""",
    "init_xml": [],
    'update_xml': [
                   'security/security_view.xml',
                   'security/ir.model.access.csv',
                   'wizard/wiz_salary_view.xml',
                   'report/salary_report_view.xml',
                   'wizard/report_type_view.xml',
                   'wizard/employee_slip_view.xml',
                   'wizard/budget_view.xml',
                   'wizard/wiz_loan_stop.xml',
# 				   'wizard/wiz_loan_deduction_view.xml',
                   'payment_view.xml',
                   'employee_view.xml',
                   'wizard/employee_salary_view.xml',
#                   'wizard/wiz_salary_increment.xml',
                   'loan_deduction_view.xml',
                   'security_deposit_view.xml',
                   'check_deduction.xml',
                   'wizard/wiz_salary_payment_report_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
