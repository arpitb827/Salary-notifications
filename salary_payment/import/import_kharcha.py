#!/usr/bin/python

import sys
import csv
import openerplib
import logging
import datetime
import string


def run(filename=None, host='localhost', db=None, login=None, passw=None):
    
    global line
    if filename:
        try: 
            data=csv.reader(open(filename), delimiter=',', quotechar='"')
        except IOError:
            print "No such file exists :%s",filename
    else:
        print "No such file exists :%s",filename
        return False
    count = 0
    code = 0
    amt = 1
    adv_date= 2
    date = 3
    conn=openerplib.get_connection(hostname=host, database=db, login=login, password=passw)
    import ast
                              
    paid_obj=conn.get_model("payment.management.advance")
    emp_obj= conn.get_model('hr.employee')
    mon_obj= conn.get_model('holiday.list')
    year_obj= conn.get_model('holiday.year')
    revert_paid = []
    exist_emp = []
    remaining_emp = []
    remaining_emp_list = []
    for row in data:
    
        emp_ids=[]
        sinid = row[code].strip()
#         sp_sinid = sinid.split('.')
# 
#         if len(sp_sinid) == 2 and len(sp_sinid[1]) == 1:
#             sinid = str(sp_sinid[0])+'.'+str(sp_sinid[1])+'00'
#         if len(sp_sinid) == 2 and len(sp_sinid[1]) == 2:
#             sinid = str(sp_sinid[0])+'.'+str(sp_sinid[1])+'0'
#         sinid = sinid.replace('.','')
#         sinid = sinid.replace("'",'')
#         sinid = sinid.replace("-",'')
#         if len(sinid) == 1:
#             sinid = '000' + str(sinid)
#         elif len(sinid) == 2:
#             sinid = '00' + str(sinid)
#         elif len(sinid) == 3:
#             sinid = '0' + str(sinid)
#         else:
#             sinid = sinid
        emp_ids = emp_obj.search([('sinid','=',sinid),('active','=',True)])   
        if not emp_ids:
            emp = sinid,row[date],row[adv_date],row[amt]
            remaining_emp_list.append(list(emp))
            continue
        
        try:
        
            paid_id=paid_obj.create({'name':row[date],'advance_date':row[adv_date],'total_amount':row[amt],
            'employee_id':emp_ids[0],'month_id':7,'year_id':2,'user_id':158})
            print "Counter------->",count,"<------------Match found----------->",emp_ids[0],"<------------created employee and salary id------------->",paid_id
            if paid_id:
                revert_paid.append(paid_id)
        except:
            paid_obj.unlink(revert_paid)
            print "Database restore to its original state. !"
            
            writer = csv.writer(open("/tmp/kharcha.csv", "wb"))
            for data in remaining_emp_list:
                row = []
                for d in data:
                    if isinstance(d, basestring):
                        d = d.replace('\n',' ').replace('\t',' ')
                        try:
                            d = d.encode('utf-8')
                        except:
                            pass
                    if d is False: d = None
                    row.append(d)
                writer.writerow(row)
            sys.exit()

        count += 1
    
    writer = csv.writer(open("/tmp/kharcha.csv", "wb"))

    for data in remaining_emp_list:
        row = []
        for d in data:
            if isinstance(d, basestring):
                d = d.replace('\n',' ').replace('\t',' ')
                try:
                    d = d.encode('utf-8')
                except:
                    pass
            if d is False: d = None
            row.append(d)

        writer.writerow(row)

    
    return count

if __name__=='__main__':
    import argparse
    import os
    import shutil
    import time
 
    parser=argparse.ArgumentParser(prog='csv_import')
    parser.add_argument('--file')
    parser.add_argument('--hostname')
    parser.add_argument('--database')
    parser.add_argument('--login')
    parser.add_argument('--password')
    
    args=vars(parser.parse_args(sys.argv[1:]))
    res=run(filename=args['file'], host=args['hostname'], db=args['database'], login=args['login'], passw=args['password'])
        
    
    if res:
        sys.stdout.flush()
        print "Completed!"
    
    else:
        print "Script_name --help"
        
