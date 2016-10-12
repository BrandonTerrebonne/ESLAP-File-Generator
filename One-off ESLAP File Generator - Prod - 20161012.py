# -*- coding: utf-8 -*-
## ^^Defining Source Code Encoding

## Import modules into namespace
import pandas as pd
import numpy as np
import datetime
import os
import glob
import time
from os import listdir
from os.path import isfile, join

def get_file_names(directory_path):
    dir_files = [f for f in listdir(directory_path) if isfile(join(directory_path, f))]
    dir_files_final = [s for s in dir_files if s[0] != '~'] # Excluding excel litter files
    return dir_files_final

def read_file(file_path):
    try:
        data = pd.read_csv(file_path)
    except:
        data = pd.read_excel(file_path)
    return data

# Pull files from the specified directory ('base_path') and turning them into data frames
base_path = r'C:\Users\brandon.terrebonne\Desktop\vm_org'
file_names = get_file_names(base_path)
if len(file_names) != 2:
    print "Error - incorrect number of files in directory. Two files should be present."

df1 = read_file(base_path + '\\' + file_names[0])
df2 = read_file(base_path + '\\' + file_names[1])

# Naming data frames, either spend_df or input_df
if list(df1.columns.values) == ['questions', 'answers']:
    input_df = df1
else:
    spend_df = df1
if list(df2.columns.values) == ['questions', 'answers']:
    input_df = df2
else:
    spend_df = df2

if not (list(df1.columns.values) == ['questions', 'answers'] or list(df2.columns.values) == ['questions', 'answers']):
    print "Error - input file not found in your directory"
    
## Create list of original field names based on info from input file - field will not be created if it is not mapped in the input file
orig_fields = input_df[0:18]['answers']
orig_fields = orig_fields.tolist()
cleaned_orig_fields = [x for x in orig_fields if str(x) != 'nan']

# Dataframe with original field names but only relevant fields
spend = pd.DataFrame(spend_df, columns=cleaned_orig_fields)

# Create list of eslap field names
sub_input = input_df.loc[input_df['answers'].isin(cleaned_orig_fields)]
eslap_fields = sub_input['questions'].tolist()
eslap_fields

# Rename fields in Spend data to correct ESLAP names
# ToDo - pull buyer file mappings and name fields correctly per buyer specs (will need to add buyer_name field in input file)
spend.rename(columns=dict(zip(cleaned_orig_fields, eslap_fields)), inplace=True)

spend_check_file = spend

## Cleaning IDs Begins ##

# ToDo - improve above comment
def check_type(x):
    p = x.split('.')
    try:
        if x == 'nan':
            y = np.nan
        elif float(x) / float(p[0]) > 1.0:
                y = x
        else:
            y = p[0]
    except:
        y = x
    return y

# Strip leading/trailing spaces
def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text
    
## Not sure if needed - strips company_id and, if existent, division_id
spend['company_id'] = strip(spend['company_id'])
if 'division_id' in spend.columns:
    spend['division_id'] = strip(spend['division_id'])

spend['company_id'] = spend['company_id'].astype(str)
spend['company_id'] = spend['company_id'].map(check_type)

# ToDo - need to test this if statement
if 'division_id' in spend.columns:
    spend['division_id'] = spend['division_id'].astype(str)
    spend['division_id'] = spend['division_id'].map(check_type)
    
if 'postal_code' in spend.columns:
    spend['postal_code'] = spend['postal_code'].astype(str)
    spend['postal_code'] = spend['postal_code'].map(check_type)    

## Cleaning IDs Ends ##

## Cleaning reserves
# ToDo - improve this method and/or test existing method
def filling(column):
    new_column = []
    for item in column:
        if item == '22222222222222222222':
            item = np.nan
            new_column.append(item)
        else:
            item = float(item)
            item = ("{0:.2f}".format(round(item,2)))
            new_column.append(item)
    return new_column

if 'reserve_amount' in spend.columns:
    spend['reserve_amount'] = spend['reserve_amount'].fillna(value=22222222222222222222)
    spend['reserve_amount'] = spend['reserve_amount'].astype(str)
    spend['reserve_amount'] = filling(spend['reserve_amount'])
    spend.fillna(value="", inplace=True)
    
## Add leading zeros
def leading(x, y):
    new_id = []
    field_length = int(y)
    for item in x:
        try:
            leng = field_length - len(str(item))
            if str(item) == 'nan':
                new_id.append(item)
            elif len(str(item)) < field_length:
                item2 = str("0000000000000000000000000000000000000000")
                item3 = str(item2[0:leng]) + str(item)
                new_id.append(item3)
            else:
                new_id.append(item)
        except:
            new_id.append(item)
    return new_id

company_id_leading_zeros_input = input_df.get_value(index = 18, col = 'answers')
division_id_leading_zeros_input = input_df.get_value(index = 19, col = 'answers')

def RepresentsInt(leading_zero_input, field):
    try: 
        int(leading_zero_input)
        field = leading(field, leading_zero_input)
        return field
    except ValueError:
        return field

spend['company_id'] = RepresentsInt(company_id_leading_zeros_input, spend['company_id'])
if 'division_id' in spend.columns:
    spend['division_id'] = RepresentsInt(division_id_leading_zeros_input, spend['division_id'])    
    
def create_final_eslap_files(fields_needed):
    column_list = []
    for x in fields_needed:
        if x in spend.columns:
            column_list.append(x)
    return column_list
    
standard_organization_columns = ['company_id','company_name','address_1','address_2',
            'city', 'state', 'postal_code','country','tax_id','reserve_percentage',
            'reserve_amount','reserve_invoice_priority','reserve_before_adjustments']
standard_user_columns = ['company_id','division_id','email_address',
            'first_name','last_name','phone_number','address_1','address_2',
            'city', 'state', 'postal_code', 'country']

customized_organization_columns = create_final_eslap_files(standard_organization_columns)
customized_user_columns = create_final_eslap_files(standard_user_columns) 

final_organization_file = pd.DataFrame(spend, columns = customized_organization_columns)
final_user_file = pd.DataFrame(spend, columns = customized_user_columns)

dummy_data = final_organization_file['company_id']
dummy_user_df = pd.DataFrame(dummy_data)
dummy_user_df['email_address'] = 'please.remove@c2fo.com'

organization_output_path = base_path + '\\' + input_df.get_value(index = 20, col = 'answers') + '_organization_manual_' + (time.strftime('%Y%m%d')) + '.csv'
user_output_path = base_path + '\\' + input_df.get_value(index = 20, col = 'answers') + '_user_manual_' + (time.strftime('%Y%m%d')) + '.csv'
dummy_user_output_path = base_path + '\\' + input_df.get_value(index = 20, col = 'answers') + '_DUMMY_user_manual_' + (time.strftime('%Y%m%d')) + '.csv'

final_organization_file.to_csv(organization_output_path, index=False, encoding='utf-8')
final_user_file.to_csv(user_output_path, index=False, encoding='utf-8')
dummy_user_df.to_csv(dummy_user_output_path, index=False, encoding='utf-8')

### Checking files and outputs audit files if differences are found ###
checker_org_column_names = list(final_organization_file.columns.values)
checker_user_column_names = list(final_user_file.columns.values)
spend_org_check_file = pd.DataFrame(spend_check_file, columns = checker_org_column_names)
spend_user_check_file = pd.DataFrame(spend_check_file, columns = checker_user_column_names)

## Creates a dataframe outlining the changes
def changes_df(x,y,z):
    changed_df = pd.DataFrame(columns = z)
    col_names = list(x.columns.values)
    for col in col_names:
        changed_array = []
        for index, row in x.iterrows():
            if row[col] != y.loc[index][col] and (str(row[col]) != 'nan' and str(y.loc[index][col]) != 'nan'):
                change_str = str(row[col]) + ' ---> ' + str(y.loc[index][col])
                changed_array.append(change_str)
            else:
                changed_array.append('')
        changed_df[col] = changed_array
    changed_df['index'] = changed_df.index.tolist()
    cols = list(changed_df.columns.values)
    cols_final = cols[-1:] + cols[:-1]
    changed_df_final = pd.DataFrame(changed_df, columns = cols_final)
    final_df = pd.DataFrame(columns = cols_final)
    changed_df_final_number_of_columns = len(changed_df_final.columns)
    for index, row in changed_df_final.iterrows():
        t = 0
        for value in row:
            if value == '':
                t += 1
        if t != changed_df_final_number_of_columns - 1:
            row = pd.DataFrame(row)
            row = row.transpose()
            final_df = final_df.append(row)
    return final_df
#     return changed_df_final # if this is the return and the above 10 lines are commented out, you'll get a 971 x 10 DF with a bunch of blanks

change_org_df = changes_df(spend_org_check_file, final_organization_file, checker_org_column_names)
change_user_df = changes_df(spend_user_check_file, final_user_file, checker_user_column_names)

if str(change_org_df.shape)[:3] != '(0,':
    audit_output_path_org = base_path + '\\' + 'AUDIT_organization_' + input_df.get_value(index = 20, col = 'answers') + (time.strftime('%Y%m%d')) + '.csv'
    change_org_df.to_csv(audit_output_path_org, index=False, encoding='utf-8')
    
if str(change_user_df.shape)[:3] != '(0,':
    audit_output_path_user = base_path + '\\' + 'AUDIT_user_' + input_df.get_value(index = 20, col = 'answers') + (time.strftime('%Y%m%d')) + '.csv'
    change_user_df.to_csv(audit_output_path_user, index=False, encoding='utf-8')