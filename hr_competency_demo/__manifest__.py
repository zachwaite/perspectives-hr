# -*- coding: utf-8 -*-
{
    'name': "FHHS Demo Module",

    'summary': """Custom Demo of HR Competency Base for FHHS""",

    'author': "Waite Perspectives, LLC - Zach Waite",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['hr_competency_base'],

    'demo': [
        'demo/departments.xml',
        'demo/jobs.xml',
        'demo/competency_requirements.xml',
        'demo/eval_communication.xml',
        'demo/eval_aed.xml',
    ],

    'application': False,
}
