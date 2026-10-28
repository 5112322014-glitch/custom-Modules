{
    # Module name shown in the Apps list
    'name': 'Basic Form',
    # Version for Odoo 18
    'version': '18.0.1.0.0',
    'summary': 'Employee records with a dashboard',
    # This module depends on the core "base" module
    'depends': ['base'],
    # Files loaded when the module is installed or updated
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/basic_form_views.xml',
        'views/dashboard_views.xml',
    ],
    # JavaScript, template and style files of the dashboard
    'assets': {
        'web.assets_backend': [
            'basic_form/static/src/dashboard/dashboard.js',
            'basic_form/static/src/dashboard/dashboard.xml',
            'basic_form/static/src/dashboard/dashboard.scss',
        ],
    },
    # Show as a standalone app in the Apps menu
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
