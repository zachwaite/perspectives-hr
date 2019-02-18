import datetime
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class Evaluation(models.Model):
    _name = 'hr.evaluation'
    _description = 'Employee Evaluation Base Model'
    _inherit = ['base.active_period.mixin']

    name = fields.Char(
        string=_('Name'),
        related='survey_id.title',
    )

    active = fields.Boolean(
        string=_('Active'),
        default=True,
    )

    description = fields.Html(
        string=_('Description'),
    )

    eligible_evaluator_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_employee_eval_evaluators_rel',
        string=_('Eligible Evaluators'),
    )

    eligible_evaluators_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='evaluation_evaluator_user_rel',
        string=_('Eligible Evaluator Users'),
        compute='_compute_eligible_evaluators_user_ids',
        store=True,
    )

    eligible_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_employee_eval_employees_rel',
        string=_('Eligible Employees'),
    )

    eligible_employees_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='evaluation_employee_user_rel',
        string=_('Eligible Employee Users'),
        compute='_compute_eligible_employees_user_ids',
        store=True,
    )

    competency_requirement_ids = fields.Many2many(
        comodel_name='hr.competency.requirement',
        relation='hr_competency_evaluation_rel',
        string=_('Applicable Competencies'),
    )

    evaluation_type = fields.Selection([
        ('knowledge_test', 'Knowledge Test'),
        ('return_demo', 'Return Demonstration')],
        string=_('Evaluation Type'),
        required=True,
    )

    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string=_('Survey'),
        required=True,
    )

    passing_score = fields.Float(
        string=_('Passing Score'),
        digits=dp.get_precision('Evaluation Score Precision'),
        default=0.0,
        required=True,
    )

    credits = fields.Float(
        string=_('Credits'),
        default=1.0,
        digits=dp.get_precision('Evaluation Credits Precision'),
        required=True,
    )

    is_closed = fields.Boolean(
        string=_('Closed'),
        compute='_compute_evaluation_is_closed',
        store=True,
    )

    @api.model
    def create(self, vals):
        res = super(Evaluation, self).create(vals)
        if 'survey_id' in vals and vals.get('survey_id', False):
            survey = self.env['survey.survey'].browse(vals['survey_id'])
            survey.write({'evaluation_id': res.id})
        return res

    @api.multi
    @api.depends('eligible_evaluator_ids')
    def _compute_eligible_evaluators_user_ids(self):
        for evaluation in self:
            evaluation.eligible_evaluators_user_ids = self.get_employees_users(self.eligible_evaluator_ids)

    @api.multi
    @api.depends('eligible_employee_ids')
    def _compute_eligible_employees_user_ids(self):
        for evaluation in self:
            evaluation.eligible_employees_user_ids = self.get_employees_users(self.eligible_employee_ids)

    @api.multi
    @api.depends('survey_id.stage_id.closed')
    def _compute_evaluation_is_closed(self):
        for evaluation in self:
            # elevate to handle survey security
            survey = evaluation.survey_id.sudo()
            evaluation.is_closed = survey.stage_id.closed

    @api.constrains('credits')
    def _check_credits(self):
        if self.credits < 0.0:
            raise ValidationError(_('Credits must be greater than 0.0'))

    @api.constrains('passing_score')
    def _check_passing_score(self):
        if self.passing_score > 100.0 or self.passing_score < 0.0:
            raise ValidationError(_('Passing score should be between 0.0 and 100.0'))

    def get_employees_users(self, employees):
        return employees.mapped('user_id')

    def get_employees_for_competencies(self):
        TrainingPlanDetail = self.env['hr.training.plan.detail']
        plan_details = TrainingPlanDetail.search([
            ('training_plan_template_detail_id.competency_requirement_id', 'in', self.competency_requirement_ids.ids),
        ])
        employees = plan_details.mapped('training_plan_id.employee_id')
        return employees

    def get_represented_employees(self):
        represented_template_details = self.env['hr.training.plan.template.detail'].search([
            ('competency_requirement_id', 'in', self.competency_requirement_ids.ids),
        ])
        represented_training_plans = represented_template_details.mapped('training_plan_detail_ids.training_plan_id')
        represented_employees = represented_training_plans.mapped('employee_id')
        return represented_employees

    @api.multi
    def update_default_evaluation_offerings(self):
        raise NotImplementedError(_('This is an abstract method'))

    @api.model
    def unlink_unrepresented_evaluations(self, represented_competency_reqs, employee):
        raise NotImplementedError(_('This is an abstract method'))

    @api.model
    def link_represented_evaluations(self, represented_competency_reqs, employee):
        raise NotImplementedError(_('This is an abstract method'))

    @api.model
    def update_evaluation_offerings(self, represented_competency_reqs, employee):
        raise NotImplementedError(_('This is an abstract method'))

    @api.multi
    def open_eligible_evaluations(self):
        eligible_surveys = self.mapped('survey_id')
        eligible_surveys.write({
            'stage_id': self.env.ref('survey.stage_in_progress').id,
        })
        return True

    @api.model
    def _cron_open_eligible_evaluations(self):
        eligible_evaluations = self.search([
            ('survey_id.stage_id', '=', self.env.ref('survey.stage_draft').id),
            ('available_on', '<=', datetime.date.today()),
        ])
        eligible_evaluations.open_eligible_evaluations()


class KnowledgeTest(models.Model):
    _name = 'hr.evaluation.knowledge'
    _description = 'Employee Knowledge Test'
    _inherits = {'hr.evaluation': 'evaluation_id'}

    evaluation_id = fields.Many2one(
        comodel_name='hr.evaluation',
        string=_('Evaluation'),
        required=True,
        ondelete='cascade',
    )

    content_url = fields.Char(
        string=_('Youtube Video URL'),
    )

    embed_url = fields.Char(
        string=_('Youtube Video Embed URL'),
        compute='_compute_embed_url',
    )

    @api.multi
    def _compute_embed_url(self):
        for test in self:
            test.embed_url = test.get_youtube_embed_url(test.content_url)

    @api.model
    def create(self, vals):
        if 'evaluation_type' not in vals or not vals.get('evaluation_type', False):
            vals['evaluation_type'] = 'knowledge_test'
        return super(KnowledgeTest, self).create(vals)

    def get_youtube_document_id(self, url):
        # same as website_slides _find_document_data_from_url, but only serving
        # youtube vidoes here, no need to handle multiple content types
        expr = re.compile(r'^.*((youtu.be/)|(v/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
        arg = expr.match(url)
        document_id = arg and arg.group(7) or False
        return document_id

    def get_youtube_embed_url(self, url):
        document_id = self.get_youtube_document_id(url)
        if document_id:
            return "https://www.youtube.com/embed/%s" % document_id
        else:
            return False

    @api.model
    def unlink_unrepresented_evaluations(self, represented_competency_reqs, employee):
        """Generic method to cover all types of eval

        Args:
            represented_competency_reqs (recordset): A recordset of type CompetencyRequirement
            employee (recordset): A recordset of type employee of length 1
        """
        employee.ensure_one()
        unrepresented_evaluations = self.search([
            ('eligible_evaluator_ids', 'in', employee.id),
            ('competency_requirement_ids', 'not in', represented_competency_reqs.ids),
        ])
        unrepresented_evaluations.write({'eligible_evaluator_ids': [(3, employee.id)]})
        return True

    @api.model
    def link_represented_evaluations(self, represented_competency_reqs, employee):
        employee.ensure_one()
        represented_evaluations = self.search([
            ('competency_requirement_ids', 'in', represented_competency_reqs.ids),
        ])
        represented_evaluations.write({'eligible_evaluator_ids': [(4, employee.id)]})
        return True

    @api.model
    def update_evaluation_offerings(self, represented_competency_reqs, employee):
        self.unlink_unrepresented_evaluations(represented_competency_reqs, employee)
        self.link_represented_evaluations(represented_competency_reqs, employee)
        return True

    @api.multi
    def update_default_evaluation_offerings(self):
        """Add expected employees (evaluators) based on their training plans
        """
        for knowledge_test in self:
            represented_employees = knowledge_test.evaluation_id.get_represented_employees()
            for employee in represented_employees:
                knowledge_test.eligible_evaluator_ids += employee
        return True

    @api.multi
    def open_eligible_evaluations(self):
        return self.evaluation_id.open_eligible_evaluations()


class ReturnDemo(models.Model):
    _name = 'hr.evaluation.demonstration'
    _description = 'Employee Competency Return Demonstration'
    _inherits = {'hr.evaluation': 'evaluation_id'}

    evaluation_id = fields.Many2one(
        comodel_name='hr.evaluation',
        string=_('Evaluation'),
        required=True,
        ondelete='cascade',
    )

    @api.model
    def create(self, vals):
        if 'evaluation_type' not in vals or not vals.get('evaluation_type', False):
            vals['evaluation_type'] = 'return_demo'
        return super(ReturnDemo, self).create(vals)

    @api.multi
    def add_expected_eligible_employees(self):
        employees = self.evaluation_id.get_employees_for_competencies()
        self.eligible_employee_ids += employees

    @api.model
    def unlink_unrepresented_evaluations(self, represented_competency_reqs, employee):
        """Generic method to cover all types of eval

        Args:
            represented_competency_reqs (recordset): A recordset of type CompetencyRequirement
            employee (recordset): A recordset of type employee of length 1
        """
        employee.ensure_one()
        unrepresented_evaluations = self.search([
            ('eligible_employee_ids', 'in', employee.id),
            ('competency_requirement_ids', 'not in', represented_competency_reqs.ids),
        ])
        unrepresented_evaluations.write({'eligible_employee_ids': [(3, employee.id)]})
        return True

    @api.model
    def link_represented_evaluations(self, represented_competency_reqs, employee):
        employee.ensure_one()
        represented_evaluations = self.search([
            ('competency_requirement_ids', 'in', represented_competency_reqs.ids),
        ])
        represented_evaluations.write({'eligible_employee_ids': [(4, employee.id)]})
        return True

    @api.model
    def update_evaluation_offerings(self, represented_competency_reqs, employee):
        self.unlink_unrepresented_evaluations(represented_competency_reqs, employee)
        self.link_represented_evaluations(represented_competency_reqs, employee)
        return True

    @api.multi
    def update_default_evaluation_offerings(self):
        """Add expected employees based on their training plans
        """
        for return_demo in self:
            represented_employees = return_demo.evaluation_id.get_represented_employees()
            for employee in represented_employees:
                return_demo.eligible_employee_ids += employee
        return True

    @api.multi
    def open_eligible_evaluations(self):
        return self.evaluation_id.open_eligible_evaluations()

