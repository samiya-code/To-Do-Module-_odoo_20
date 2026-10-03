{
    'name': 'Task Studio',
    'version': '1.0',
    'summary': 'A colorful workspace for planning and tracking tasks',
    'category': 'Productivity/Task Management',
    'author': 'OpenAI',
    'website': 'https://example.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/todo_security.xml',
        'security/ir.model.access.csv',
        'reports/todo_task_report.xml',
        'views/todo_dashboard_views.xml',
        'views/todo_task_views.xml',
        'views/todo_tag_views.xml',
        'views/todo_menus.xml',
        'wizard/todo_task_assignment_wizard.xml',
    ],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'custom_todo/static/src/scss/todo.scss',
        ],
    },
}
