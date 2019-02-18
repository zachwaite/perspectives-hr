from odoo import models, fields, api, _


class CompetencyRequirement(models.Model):
    _name = 'hr.competency.requirement'
    _description = 'Employee Competency Requirement'
    _inherit = ['base.active_period.mixin']

    name = fields.Char(
        string=_('Name'),
    )

    description = fields.Html(
        string=_('Description'),
    )

