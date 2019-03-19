from odoo import tools
from odoo import models, fields, api, _


class TrainingPlanCategorized(models.Model):
    _name = 'hr.training.plan.detail.categorized'
    _description = 'Denormalized view on training plan details for use in cliend'
    _auto = False

    id = fields.Integer()
    name = fields.Char()
    training_plan_detail_id = fields.Many2one(comodel_name = 'hr.training.plan.detail')
    training_plan_detail_name = fields.Char()
    competency_requirement_id = fields.Many2one(comodel_name='hr.competency.requirement')
    competency_requirement_name = fields.Char()
    employee_id = fields.Many2one(comodel_name='hr.employee')

    def _select(self):
        s = """
            t.id as id,
            t.name as name,
            t.id as training_plan_detail_id,
            t.name as training_plan_detail_name,
            c.id as competency_requirement_id,
            c.name as competency_requirement_name,
            p.employee_id
        """
        return s

    def _from(self):
        f = """
            hr_training_plan_detail as t,
            hr_competency_requirement as c,
            hr_training_plan as p,
            hr_training_plan_template_detail as x
        """
        return f

    def _where(self):
        w = """
            t.training_plan_template_detail_id = x.id
            AND
            x.competency_requirement_id = c.id
            AND
            t.training_plan_id = p.id
        """
        return w

    def _query(self):
        q ="""
        SELECT %s
            FROM %s
            WHERE %s
        """ % (self._select(), self._from(), self._where())
        return q

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
        CREATE or REPLACE VIEW %s AS (%s)
        """ % (self._table, self._query())
        print(sql)
        self.env.cr.execute(sql)
