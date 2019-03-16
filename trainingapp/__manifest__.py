{
    'name': "Employee Training App",

    'summary': """Employee Facing Client for Competency Management""",

    'description': """
    """,

    'author': "Waite Perspectives, LLC - Zach Waite",
    'website': "http://www.waiteperspectives.com",

    'category': 'HR',
    'version': '0.1',

    'depends': ['web', 'hr_competency_base'],

    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/templates.xml',
    ],

    'application': True,
}
