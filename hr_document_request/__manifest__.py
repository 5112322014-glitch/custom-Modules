{
'name':'HR Document Request',
'version':'18.0.1.0.0',
'category': 'Human Resources',
'summary':'Manage employee document and letter requests with approvals,rejection and PDF generation',
'depends':['base' ,'mail' ,'hr'],
'data':[
'security/hr_document_request_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/hr_document_reject_wizard_views.xml',         # <-- Yeh line yahan views se PEHLE aayegi
        'views/hr_document_request_views.xml', 
        'views/hr_employee_views.xml',                             # <-- Main view baad mein load hogi
        'report/hr_document_request_report.xml',

],
'installable':True,
'application':True,
'license':'LGPL-3',
}
