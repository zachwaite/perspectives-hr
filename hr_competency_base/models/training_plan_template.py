# © 2018 Waite Perspectives, LLC - Zach Waite
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class TrainingPlanTemplate(models.Model):
    _name = 'hr.training.plan.template'
    _description = 'Employee Training Plan Template'

    name = fields.Char(
        string=_('Name'),
    )

    active = fields.Boolean(
        string=_('Active'),
        default=True,
    )

    template_detail_ids = fields.One2many(
        comodel_name='hr.training.plan.template.detail',
        inverse_name='training_plan_template_id',
        string=_('Template Details'),
    )


class TrainingPlanTemplateDetail(models.Model):
    _name = 'hr.training.plan.template.detail'
    _description = 'Employee Training Plan Template Detail'
    _inherit = ['hr.training.detail.mixin']

    name = fields.Char(
        string=_('Name'),
    )

    training_plan_template_id = fields.Many2one(
        comodel_name='hr.training.plan.template',
        string=_('Training Plan'),
    )

    training_plan_detail_ids = fields.One2many(
        comodel_name='hr.training.plan.detail',
        inverse_name='training_plan_template_detail_id',
        string=_('Associated Training Plan Details'),
    )

    training_plan_scheduler_ids = fields.One2many(
        comodel_name='hr.training.detail.scheduler',
        inverse_name='template_detail_id',
        string=_('Associated Training Plan Schedulers'),
    )

    credits = fields.Float(
        string=_('Credits Required'),
        default=1.0,
        digits=dp.get_precision('Evaluation Credits Precision'),
        required=True,
        help=_('Number of credits required to satisfy the competency requirement for this period'),
    )


    @api.model
    def create(self, vals):
        res = super(TrainingPlanTemplateDetail, self).create(vals)
        # update existing plans with this template
        associated_plans = self.env['hr.training.plan'].search([
            ('training_plan_template_ids', 'in', res.training_plan_template_id.id),
        ])

        for plan in associated_plans:
            new_scheduler = self.env['hr.training.detail.scheduler'].create({
                'training_plan_id': plan.id,
                'template_detail_id': res.id,
                'nextcall': datetime.datetime.now(),
                'numbercall': res.numbercall,
            })
            plan.training_detail_scheduler_ids += new_scheduler

        return res

    @api.multi
    def unlink(self):
        associated_schedulers = self.env['hr.training.detail.scheduler'].search([
            ('template_detail_id', 'in', self.ids),
        ])
        associated_schedulers.unlink()
        return super(TrainingPlanTemplateDetail, self).unlink()

    @api.multi
    def write(self, vals):
        success = super(TrainingPlanTemplateDetail, self).write(vals)
        associated_schedulers = self.env['hr.training.detail.scheduler'].search([
            ('template_detail_id', 'in', self.ids),
        ])
        # don't write all vals, due to conflicts on e.g. nextcall
        update_fields = ['template_detail_id']
        scheduler_vals = {}
        for fld in update_fields:
            if fld in vals:
                scheduler_vals.update({fld: vals[fld]})
        associated_schedulers.write(scheduler_vals)
        return success

