{
    'name': "hr_competency_base",

    'summary': """Manage Employee Competency Requirements""",

    'description': """
Features
==========

Competency Requirements
------------------------

* Define specific knowledge and skills needed by employees.
* Manage requirements lifecycle by defining when a requirment becomes effective
and when it expires.

Training Plans
---------------

* Assemble employee training plans from reusable templates that specify
competency requirements.
* Rapidly configure training plans for new employees by establishing defaults
based on job position and department.
* Schedule perpetually recurring assignments or fixed amounts (e.g. an assignment
every month vs. one assignment only vs. five weekly assignments).
* Define deadlines and minimum acceptable dates, relative to an employee attribute
(e.g. six months prior to, or 60 days after hire date).

Evaluation Options
-------------------

* Offer self administered knowledge tests and supervised evaluations online
or upload print versions.
* Online results are automatically scored and immediate feedback is provided to
the user
* Passing scores automatically update the training plan to reflect requirements
completion.
* Allow credit for 3rd party training and certifications by entering a result
voucher with supporting documents. Credits are automatically applied to the
relevant training plan items.

Training Content Delivery
--------------------------

* Provide high quality training videos directly from the employee training plan
by leveraging an embedded Youtube player.
* Training videos appear alongside the relevant knowledge test for simple training

Training Lifecycle Management
-------------------------------

* Manage different versions of training content and evaluations by scheduling
the availability and expiry dates.
* Credits for different versions of the same evaluations have the same credit
value

Available Customizations
-------------------------

* Alerts to notify employees of upcoming deadlines via email or text*
* Advanced search filters and reports
* eSignature integration*

* Enterprise edition only
    """,

    'author': "Waite Perspectives, LLC - Zach Waite",
    'website': "http://www.waiteperspectives.com",

    'category': 'HR',
    'version': '0.1',

    'depends': ['decimal_precision', 'base_automation', 'hr', 'website_survey'],

    'data': [
        'security/access_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/precision.xml',
        'data/survey_stage.xml',
        'data/automation.xml',
        'views/competency_requirement_views.xml',
        'views/evaluation_views.xml',
        'views/evaluation_result_views.xml',
        'views/training_plan_views.xml',
        'views/training_plan_template_views.xml',
        'views/hr_views.xml',
        'views/survey_views.xml',
        'views/portal_templates.xml',
        'views/return_demo_templates.xml',
        'views/knowledge_test_templates.xml',
        'views/training_plan_templates.xml',
        'views/survey_templates.xml',
        'views/menu_items.xml',
    ],

    'application': True,
}
