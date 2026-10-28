{
    'name': 'Office Visitor Management System',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage office visitors, check-in/check-out and badges',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/visitor_views.xml',
        'views/dashboard_views.xml',
        'views/dashboard_action.xml',
        'report/visitor_badge.xml',
        'data/mail_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'office_visitor/static/src/css/dashboard.css',
            'office_visitor/static/src/js/dashboard.js',
            'office_visitor/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
