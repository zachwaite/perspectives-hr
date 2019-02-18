# © 2018 Waite Perspectives, LLC - Zach Waite
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

def get_relativedelta(interval_period, interval):
    if interval_period == 'days':
        return relativedelta(days=interval)
    elif interval_period == 'weeks':
        return relativedelta(weeks=interval)
    elif interval_period == 'months':
        return relativedelta(months=interval)


class TrainingDetailMixin(models.AbstractModel):
    _name = 'hr.training.detail.mixin'
    _description = 'Employee Training Detail Mixin'

    competency_requirement_id = fields.Many2one(
        comodel_name='hr.competency.requirement',
        string=_('Competency Requirement'),
        required=True,
    )

    # just like cron
    scheduling_interval_period = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], help=_('Recurrence frequency period to schedule the new training plan detail.'),
    string=_('Scheduling Interval Period'),
    default='months')

    scheduling_interval_interval = fields.Integer(
        string=_('Scheduling Interval'),
        default=12,
        help=_('Multiplier for Interval Type'),
    )

    # used on instances for instructing cron
    nextcall = fields.Datetime(
        string=_('Next Execution'),
    )

    numbercall = fields.Integer(
        string=_('Number of Calls'),
        help=_('Use -1 for unlimited'),
    )

    # metadata to establish deadline
    reference_model_id = fields.Many2one(
        comodel_name='ir.model',
        default=lambda self: self.get_hr_employee_model_id()
    )

    reference_date_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string=_('Reference Date Field'),
        help=_('Date field on Employee model used to compute deadline'),
        domain="[('model_id', '=', reference_model_id), ('ttype', 'in', ('date', 'datetime'))]",
    )

    date_deadline_relative_period = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string=_('Date Deadline Relative Period'),
        help=_('The compute deadline in days or months relative to the reference date'),
        default='days',
    )

    date_deadline_relative_interval = fields.Integer(
        string=_('Date Deadline Relative Interval'),
        help=_('The number of days or months relative to the reference date to compute the deadline'),
        default=1,
    )

    # metadata to establish date minimum
    date_minimum_relative_period = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string=_('Date Minimum Relative Period'),
        help=_('The computed date minimum in days or months relative to the reference date'),
        default='days',
    )

    date_minimum_relative_interval = fields.Integer(
        string=_('Date Minimum Relative Interval'),
        help=_('The number of days or months relative to the reference date to compute the date minimum'),
        default=0,
    )

    def get_hr_employee_model_id(self):
        return self.env.ref('hr.model_hr_employee').id

    def get_schedule_relativedelta(self):
        return get_relativedelta(self.scheduling_interval_period, self.scheduling_interval_interval)

    def get_date_deadline_relativedelta(self):
        return get_relativedelta(self.date_deadline_relative_period, self.date_deadline_relative_interval)

    def get_date_minimum_relativedelta(self):
        return get_relativedelta(self.date_minimum_relative_period, self.date_minimum_relative_interval)

    def get_next_nextcall(self):
        if not self.nextcall:
            return False

        if self.numbercall == 0:
            return False
        else:
            delta = self.get_schedule_relativedelta()
            return self.nextcall + delta

    def get_relative_anchor_date(self, recordset):
        if not recordset._name == self.reference_model_id.model:
            raise ValidationError(_('Reference model is not the same as model of recordset parameter'))
        else:
            date_field_name = self.reference_date_field_id.name
            anchor_date = recordset[date_field_name]
        return anchor_date

