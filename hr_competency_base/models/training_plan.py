import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class TrainingPlan(models.Model):
    _name = 'hr.training.plan'
    _description = 'Employee Training Plan'

    name = fields.Char(
        string=_('Name'),
        compute='_compute_training_plan_name',
        store=True,
    )

    competency_requirement_ids = fields.Many2many(
        comodel_name='hr.competency.requirement',
        relation='hr_training_plan_competency_rel',
        string=_('Competecy Requirements'),
        compute='_compute_competency_requirments',
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string=_('Employee'),
        required=True,
    )

    training_plan_template_ids = fields.Many2many(
        comodel_name='hr.training.plan.template',
        relation='training_plan_template_plan_rel',
        string=_('Training Plan Templates'),
    )

    training_detail_scheduler_ids = fields.Many2many(
        comodel_name="hr.training.detail.scheduler",
        relation='training_detail_scheduler_rel',
        string=_('Training Plan Scheduler'),
    )

    training_plan_detail_ids = fields.One2many(
        comodel_name='hr.training.plan.detail',
        inverse_name='training_plan_id',
        string=_('Training Plan Details'),
    )

    @api.multi
    @api.depends('employee_id.name')
    def _compute_training_plan_name(self):
        for plan in self:
            plan.name = "Training Plan - %s" % plan.employee_id.name

    @api.multi
    def _compute_competency_requirements(self):
        for plan in self:
            plan.competency_requirement_ids = plan.training_plan_detail_ids.mapped(
                'training_plan_template_detail_id.competency_requirement_id'
            )

    @api.model
    def create(self, vals):
        res = super(TrainingPlan, self).create(vals)
        for tmpl in res.training_plan_template_ids:
            for detail in tmpl.template_detail_ids:
                new_scheduler = self.env['hr.training.detail.scheduler'].create({
                    'training_plan_id': res.id,
                    'template_detail_id': detail.id,
                    'nextcall': datetime.datetime.now(),
                    'numbercall': detail.numbercall,
                })
                res.training_detail_scheduler_ids += new_scheduler
        return res

    @api.multi
    def write(self, vals):
        success = super(TrainingPlan, self).write(vals)
        if 'training_plan_template_ids' in vals:
            self.synchronize_schedulers()
        return success

    @api.multi
    def synchronize_schedulers(self):
        for plan in self:
            expected_detail_ids = self.env['hr.training.plan.template.detail'].search([
                ('training_plan_template_id', 'in', plan.training_plan_template_ids.ids),
            ])
            observed_detail_ids = plan.training_detail_scheduler_ids.mapped('template_detail_id')
            missing = expected_detail_ids - observed_detail_ids
            for rs in missing:
                new_scheduler = self.env['hr.training.detail.scheduler'].create({
                    'training_plan_id': plan.id,
                    'template_detail_id': rs.id,
                    'nextcall': datetime.datetime.now(),
                    'numbercall': rs.numbercall,
                })
                plan.training_detail_scheduler_ids += new_scheduler

            unexpected = observed_detail_ids - expected_detail_ids
            unexpected_schedulers = plan.training_detail_scheduler_ids.filtered(
                lambda x: x.template_detail_id.id in unexpected.ids
            )
            unexpected_schedulers.unlink()
        return True 

    @api.model
    def _cron_schedule_plan_details(self):
        """This is a global classmethod
        """
        current_date = datetime.date.today()
        eligible_schedulers = self.env['hr.training.detail.scheduler'].search([
            ('nextcall', '<=', current_date),
            ('numbercall', '!=', 0),
        ])

        for scheduler in eligible_schedulers:
            date_deadline = scheduler.get_deadline()
            date_minimum = scheduler.get_date_minimum()

            self.env['hr.training.plan.detail'].create({
                'training_plan_id': scheduler.training_plan_id.id,
                'training_plan_template_detail_id': scheduler.template_detail_id.id,
                'date_deadline': date_deadline,
                'date_minimum': date_minimum,
            })

            scheduler.nextcall = scheduler.get_next_nextcall()

            if scheduler.numbercall > 0:
                scheduler.numbercall -= 1
        return True

    @api.multi
    def plan_training(self):
        self.synchronize_schedulers()
        self._cron_schedule_plan_details()

    def get_represented_competency_requirements(self):
        return self.training_plan_detail_ids.mapped('training_plan_template_detail_id.competency_requirement_id')

    @api.multi
    def update_default_evaluation_offerings(self):
        for plan in self:
            represented_competency_reqs = plan.get_represented_competency_requirements()
            plan.env['hr.evaluation.knowledge'].update_evaluation_offerings(represented_competency_reqs, plan.employee_id)
            plan.env['hr.evaluation.demonstration'].update_evaluation_offerings(represented_competency_reqs, plan.employee_id)
        return True

    @api.model
    def _cron_update_default_evaluation_offerings(self):
        plans = self.search([])
        plans.update_default_evaluation_offerings()


class TrainingPlanDetail(models.Model):
    _name = 'hr.training.plan.detail'
    _description = 'Employee Training Plan Details'

    name = fields.Char(
        string=_('Name'),
        compute='_compute_name',
        store=True,
    )

    training_plan_id = fields.Many2one(
        comodel_name='hr.training.plan',
        string=_('Training Plan'),
    )

    training_plan_template_detail_id = fields.Many2one(
        comodel_name='hr.training.plan.template.detail',
        string=_('Training Plan Template Detail'),
        required=True,
        help=_('The template detail that manages this plan detail'),
    )

    date_minimum = fields.Date(
        string=_('Date Available'),
        required=True,
        default=fields.Date.today(),
    )

    date_deadline = fields.Date(
        string=_('Deadline'),
        required=True,
    )

    raw_results_ids = fields.Many2many(
        comodel_name='hr.competency.result',
        relation='training_plan_detail_results_rel',
        string=_('All Results'),
        compute='_compute_raw_results',
    )

    qualifying_results_ids = fields.Many2many(
        comodel_name='hr.competency.result',
        relation='training_plan_detail_results_rel',
        string=_('Qualifying Results'),
        compute='_compute_qualifying_results',
    )

    credits = fields.Float(
        string=_('Credits'),
        digits=dp.get_precision('Evaluation Credits Precision'),
        help=_('Total qualifying credits. Equal to the sum of the credits of unique qualifying results. If duplicate results exist, the max credits are used.'),
        compute='_compute_accumulated_credits',
    )

    credits_required = fields.Float(
        related='training_plan_template_detail_id.credits',
    )

    is_complete = fields.Boolean(
        string=_('Is Complete'),
        compute='_compute_is_complete',
    )

    is_overdue = fields.Boolean(
        string=_('Is Overdue'),
        compute='_compute_is_overdue',
    )

    @api.multi
    @api.depends('training_plan_template_detail_id.name')
    def _compute_name(self):
        for plan_detail in self:
            plan_detail.name = plan_detail.training_plan_template_detail_id.name

    @api.multi
    def _compute_raw_results(self):
        for plan_detail in self:
            plan_detail.raw_results_ids = plan_detail.get_raw_results().ids

    @api.multi
    def _compute_qualifying_results(self):
        for plan_detail in self:
            plan_detail.qualifying_results_ids = plan_detail.get_qualifying_results().ids

    @api.multi
    def _compute_accumulated_credits(self):
        for plan_detail in self:
            plan_detail.credits = plan_detail.get_accumulated_credits()

    @api.multi
    def _compute_is_complete(self):
        for plan_detail in self:
            plan_detail.is_complete  = (plan_detail.credits >= plan_detail.credits_required)

    @api.multi
    def _compute_is_overdue(self):
        for plan_detail in self:
            plan_detail.is_overdue = (plan_detail.date_deadline < datetime.date.today() and not plan_detail.is_complete)

    @api.multi
    def get_raw_results(self):
        """All results with a matching competency requirement and within the
        date range.
        """
        self.ensure_one()
        CompetencyResult = self.env['hr.competency.result']
        results = CompetencyResult.search([
            ('competency_requirement_ids', 'in', [self.training_plan_template_detail_id.competency_requirement_id.id]),
            ('completion_date', '>', self.date_minimum),
            ('completion_date', '<=', self.date_deadline),
            ('employee_id', '=', self.training_plan_id.employee_id.id),
        ])
        return results

    @api.multi
    def get_qualifying_results(self):
        """Raw results, only counting each EvaluationResult once so a user
        can't just redo the same quiz to hit the competency credits level
        """
        CompetencyResult = self.env['hr.competency.result']
        for plan_detail in self:
            # split into a {CompetencyResult.result_type: CompetencyResult} dict
            grouped_results = plan_detail.raw_results_ids.split_results_by_type()

            # remove evaluation results and filter for max credit results
            evaluation_results = grouped_results.pop('evaluation', False)
            if evaluation_results:
                # now working with EvaluationResult records
                results_by_eval = evaluation_results.split_results_by_evaluation()
                # filter out failing scores
                passing_results_by_eval = {k: results_by_eval[k].get_results_with_passing_scores() for k in results_by_eval}
                best_results_by_eval = {k: passing_results_by_eval[k].get_result_with_max_credits() for k in passing_results_by_eval}

                # add back the evaluation results as CompetencyResults
                best_result_ids = [best_results_by_eval[k].competency_result_id.id for k in best_results_by_eval if best_results_by_eval[k]]
                grouped_results['evaluation'] = CompetencyResult.browse(best_result_ids)

            results_ids = []
            for grp in grouped_results:
                results_ids += grouped_results[grp].ids
            results = CompetencyResult.browse(results_ids)
            return results

    @api.multi
    def get_accumulated_credits(self):
        EvaluationResult = self.env['hr.competency.result.evaluation']
        for plan_detail in self:
            results = plan_detail.qualifying_results_ids
            if results:
                return sum(results.mapped('credits'))
            else:
                return 0.0


class TrainingPlanDetailScheduler(models.Model):
    _name = 'hr.training.detail.scheduler'
    _description = 'Employee Training Plan Detail Scheduler'

    name = fields.Char(
        string=_('Name'),
        related='template_detail_id.name',
    )

    training_plan_id = fields.Many2one(
        comodel_name='hr.training.plan',
        string=_('Training Plan'),
    )

    template_detail_id = fields.Many2one(
        comodel_name='hr.training.plan.template.detail',
        string=_('Template Detail ID'),
    )

    # used on instances for instructing cron
    nextcall = fields.Date(
        string=_('Next Execution'),
    )

    numbercall = fields.Integer(
        string=_('Number of Calls'),
        help=_('Use -1 for unlimited'),
    )

    def get_deadline(self):
        employee = self.training_plan_id.employee_id
        anchor = self.template_detail_id.get_relative_anchor_date(employee)
        delta = self.template_detail_id.get_date_deadline_relativedelta()
        if anchor and delta:
            return anchor + delta
        elif anchor and not delta:
            return anchor
        else:
            return False

    def get_date_minimum(self):
        employee = self.training_plan_id.employee_id
        anchor = self.template_detail_id.get_relative_anchor_date(employee)
        delta = self.template_detail_id.get_date_minimum_relativedelta()
        if anchor and delta:
            return anchor - delta
        elif anchor and not delta:
            return anchor
        else:
            return False

    def get_next_nextcall(self):
        if not self.nextcall:
            return False

        # subtract 1 to get expected next numbercall
        if (self.numbercall - 1) == 0:
            return False
        else:
            delta = self.template_detail_id.get_schedule_relativedelta()
            return self.nextcall + delta

