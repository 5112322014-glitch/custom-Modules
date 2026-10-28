{
    # Module name shown in the Apps list
    'name': 'Help Desk',
    'version': '18.0.1.0.0',
    'summary': 'Simple ticket system for internal support requests',
    # "mail" gives us the chatter (messages and history) on each ticket
    'depends': ['base', 'mail'],
    # Files loaded on install/update (they are created in the next steps)
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/ticket_views.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'helpdesk_basic/static/src/dashboard/dashboard.js',
            'helpdesk_basic/static/src/dashboard/dashboard.xml',
            'helpdesk_basic/static/src/dashboard/dashboard.scss',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
