# © 2018 Waite Perspectives, LLC - Zach Waite
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class Job(models.Model):
    _inherit = 'hr.job'

    training_plan_template_ids = fields.Many2many(
        comodel_name='hr.training.plan.template',
        relation='training_plan_template_def_job_rel',
        string=_('Default Training Plan Templates'),
        help=_('These templates will be assigned to new employees in this position by default'),
    )


class Department(models.Model):
    _inherit = 'hr.department'

    training_plan_template_ids = fields.Many2many(
        comodel_name='hr.training.plan.template',
        relation='training_plan_template_def_dept_rel',
        string=_('Default Training Plan Templates'),
        help=_('These templates will be assigned to new employees in this position by default'),
    )

    # all are bulk capable
    def get_ancestor_ids(self):
        # this should usually be a list of 1
        ancestor_ids = self.ids
        for record in self:
            if record.parent_id:
                ancestor_ids = ancestor_ids + record.parent_id.get_ancestor_ids()
        return ancestor_ids

    def get_ancestors(self):
        ancestor_ids = self.get_ancestor_ids()
        return self.browse(ancestor_ids)


class Employee(models.Model):
    ## 01private: Private attributes
    _inherit = 'hr.employee'

    ## 02defaults: Default methods
    ## 03fields: Fields declaration
    training_plan_id = fields.Many2one(
        comodel_name='hr.training.plan',
        string=_('Training Plan'),
    )

    hire_date = fields.Date(
        string=_('Hire Date'),
        default=fields.Date.today()
        # required=True,
    )

    default_training_plan_template_ids = fields.Many2many(
        comodel_name='hr.training.plan.template',
        relation='training_template_employee_rel',
        string=_('Training Plan Templates'),
        compute='_compute_default_training_plan_template_ids',
    )

    ## 04compute: Compute, search, inverse field methods, in the order of field declaration
    @api.multi
    def _compute_default_training_plan_template_ids(self):
        for employee in self:
            employee.default_training_plan_template_ids = employee.get_default_training_templates()

    ## 05onchange: Onchange and constraints methods, declarations
    @api.onchange('department_id')
    def _onchange_department(self):
        return {
            'domain': {
                'job_id': [('id', 'in', self.department_id.jobs_ids.ids)],
            }
        }

    ## 06crud: CRUD methods, ORM overrides
    ## 07action: Action methods
    @api.multi
    def action_employee_training_plan(self):
        self.ensure_one()
        return {
            'name': _('Training Plan'),
            'res_model': 'hr.training.plan',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    ## 08other: Other business methods
    def get_default_job_training_templates(self):
        return self.mapped('job_id.training_plan_template_ids')

    def get_default_department_training_templates(self):
        ancestors = self.department_id.get_ancestors()
        return ancestors.mapped('training_plan_template_ids')

    @api.multi
    def get_default_training_templates(self):
        job_templates = self.get_default_job_training_templates()
        dept_templates =self.get_default_department_training_templates()
        return job_templates + dept_templates
