from odoo import http, _
from odoo.http import request, Controller


class TrainingAppController(Controller):
    @http.route(['/training'], auth='user', type='http', website=True)
    def training_app_main(self, **post):
        return request.render('trainingapp.app_page')
