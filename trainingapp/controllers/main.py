import datetime
import json
from odoo import http, _
from odoo.http import request, Controller


class TrainingAppController(Controller):
    @http.route(['/training'], auth='user', type='http', website=True)
    def training_app_main(self, **post):
        return request.render('trainingapp.app_page')

    # serve data to components
    @http.route(['/training/dashboard'], auth='user', type='json', website=True)
    def training_app_dashboard(self, user_id=False, **kw):
        user = request.env['res.users'].browse(user_id)
        payload = {}

        # all active knowledge tests
        count_all = request.env['hr.evaluation.knowledge'].search_count([])
        payload.update({'count_all': count_all})

        # all mandatory trainings
        my_training_plan = request.env['hr.training.plan'].search([
            ('employee_id', 'in', user.employee_ids),
        ])
        my_training_details = my_training_plan.mapped('training_plan_detail_ids')
        count_my = len(my_training_details)
        payload.update({'count_my': count_my})

        # all overdue trainings
        my_odue_details = my_training_details.filtered(
            lambda d: d.date_deadline < datetime.date.today()
        )
        count_my_odue = len(my_odue_details)
        payload.update({'count_my_odue': count_my_odue})

        return payload
