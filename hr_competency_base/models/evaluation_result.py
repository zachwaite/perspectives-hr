from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class CompetencyResult(models.Model):
    """Base class for Evaluation Result and Result Voucher
    """
    _name = 'hr.competency.result'
    _description = 'Employee Competency Result'

    name = fields.Char(
        string=_('Name'),
    )

    competency_requirement_ids = fields.Many2many(
        comodel_name='hr.competency.requirement',
        relation='hr_competency_result_rel',
        string=_('Competency Requirements'),
        help=_('Enter what competencies this voucher satisfies'),
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string=_('Employee'),
    )

    employee_user_id = fields.Many2one(
        comodel_name='res.users',
        string=_('Employee User'),
        related='employee_id.user_id',
    )

    evaluator_user_id = fields.Many2one(
        comodel_name='res.users',
        string=_('Evaluating User'),
    )

    result_type = fields.Selection([
        ('evaluation', 'Evaluation Result'),
        ('voucher', 'Result Voucher'),
    ], string=_('Result Type'),
    )

    credits = fields.Float(
        string=_('Credits'),
        help=_('Credits of evaluation, if passing, or manually overriden for e.g. voucher. Credits from the same evaluation will not be double counted.'),
        required=True,
        default=0.0,
        digits=dp.get_precision('Evaluation Credits Precision'),
    )

    score = fields.Float(
        string=_('Score'),
        help=_('Result Score if Evaluation'),
        digits=dp.get_precision('Evaluation Score Precision'),
        default=0.0,
        compute='_compute_evaluation_score',
    )

    completion_date = fields.Datetime(
        string=_('Completion Date'),
        help=_('Completion date from survey user input, or manually entered for manual or voucher'),
        required=True,
        default=fields.Datetime.now(),
    )

    @api.multi
    def _compute_evaluation_score(self):
        for result in self:
            if result.result_type == 'evaluation':
                child = self.env['hr.competency.result.evaluation'].search([
                    ('competency_result_id', '=', result.id),
                ])
                child.ensure_one()
                result.score = child.score

    @api.constrains('credits')
    def _check_credits(self):
        for result in self:
            if result.credits < 0.0:
                raise ValidationError(_('Credits must be greater than 0.0'))

    @api.multi
    def split_results_by_type(self):
        """Return a {CompetencyResult.result_type: CompetencyResult()} dict.
        """
        selections = self._fields['result_type'].selection
        out = {tup[0]: self.filtered(
            lambda rs: rs.result_type == tup[0]
        ) for tup in selections}
        return out

    @api.multi
    def split_results_by_evaluation(self):
        """Return a {Evaluation(): EvaluationResult()} from the call to
        the child set.
        """
        evaluation_results = self.get_evaluation_results()
        return evaluation_results.split_results_by_evaluation()

    def get_child_results(self, model):
        results = self.env[model].search([
            ('competency_result_id', 'in', self.ids),
        ])
        return results

    @api.multi
    def get_evaluation_results(self):
        return self.get_child_results('hr.competency.result.evaluation')

    @api.multi
    def get_voucher_results(self):
        return self.get_child_results('hr.competency.result.voucher')


class EvaluationResult(models.Model):
    """Store Results for both Knowledge Test and Return Demo
    """
    _name = 'hr.competency.result.evaluation'
    _description = 'Employee Competency Evaluation Result'
    _inherits = {'hr.competency.result': 'competency_result_id'}

    competency_result_id = fields.Many2one(
        comodel_name='hr.competency.result',
        string=_('Competency Result'),
        required=True,
        ondelete='cascade',
    )

    # normalized score, not raw
    score = fields.Float(
        string=_('Result Score'),
        digits=dp.get_precision('Evaluation Score Precision'),
        required=True,
        default=0.0,
    )

    user_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string=_('Survey User Input'),
        help=_('The user input record if online, else False if manual entry'),
    )

    # evaluation_id cant be computed on manual entries
    evaluation_id = fields.Many2one(
        comodel_name='hr.evaluation',
        string=_('Evaluation'),
    )

    print_user_input_upload = fields.Binary(
       string=_('Manual Quiz Result Upload'),
    )

    print_user_input_name = fields.Char(
        string=_('Manual Quiz Result Upload Name'),
    )

    @api.constrains('passing_score')
    def _check_passing_score(self):
        for result in self:
            if result.score > 100.0 or result.score < 0.0:
                raise ValidationError(_('Passing score should be between 0.0 and 100.0'))

    @api.onchange('evaluation_id', 'completion_date')
    def _onchange_name_criteria(self):
        self.set_name()

    @api.onchange('competency_requirement_ids')
    def _onchange_competency_reqs(self):
        return {
            'domain': {
                'evaluation_id': [('competency_requirement_ids', 'in', self.competency_requirement_ids.ids)],
            }
        }

    @api.onchange('evaluation_id')
    def _onchange_evaluation_id(self):
        self.credits = self.evaluation_id.credits
        if self.evaluation_id.evaluation_type == 'knowledge_test':
            return {
                'domain': {
                    'employee_id': [('id', 'in', self.evaluation_id.eligible_evaluator_ids.ids)],
                    'evaluator_user_id': [('id', 'in', self.evaluation_id.eligible_evaluators_user_ids.ids)],
                }
            }
        elif self.evaluation_id.evaluation_type == 'return_demo':
            return {
                'domain': {
                    'employee_id': [('id', 'in', self.evaluation_id.eligible_employee_ids.ids)],
                    'evaluator_user_id': [('id', 'in', self.evaluation_id.eligible_evaluators_user_ids.ids)],
                }
            }

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.evaluation_id.evaluation_type == 'knowledge_test':
            self.evaluator_user_id = self.employee_id.user_id.id

    @api.constrains('user_input_id', 'print_user_input_upload')
    def _check_single_quiz_result(self):
        for result in self:
            if result.user_input_id and result.print_user_input_upload:
                raise ValidationError(_("Having online and print quiz on the same record is not allowed. Please create a separate manual entry for the print version."))

    # not making these computed fields, but call the setters directly as needed
    @api.multi
    def set_scores(self):
        for result in self:
            quizz_score = result.user_input_id.quizz_score
            total_points = result.user_input_id.survey_id.total_available_points
            result.score = result.normalize_score(quizz_score, total_points)
        return True

    @api.multi
    def set_credits(self):
        for result in self:
            if result.score >= result.evaluation_id.passing_score:
                result.credits = result.evaluation_id.credits
        return True

    @api.multi
    def set_name(self):
        for result in self:
            prefix = result.evaluation_id.name
            suffix = result.completion_date
            result.name = "%s - %s" % (prefix, suffix)
        return True

    @api.multi
    def split_results_by_evaluation(self):
        """Return a {Evaluation(): EvaluationResult()} map
        where the keys are unique Evaulation() sets. This 
        is ensured because mapped() returns a set-like.
        """
        evaluations = self.mapped('evaluation_id')
        out = {e: self.filtered(
            lambda rs: rs.evaluation_id == e
        ) for e in evaluations}
        return out

    @api.multi
    def get_result_with_max_credits(self):
        """Return an EvaluationResult() of length 0 or 1.

        This represents the EvaluationResult() with the most
        credits, ties broken with completion_date.
        """
        if len(self) < 2:
            return self
        else:
            sorted_results = self.sorted(
                key=lambda rs: (rs.credits, rs.completion_date),
                reverse=True,
            )
            return sorted_results[0]

    @api.multi
    def get_results_with_passing_scores(self):
        return self.filtered(
            lambda rs: rs.score >= rs.evaluation_id.passing_score
        )

    def normalize_score(self, quizz_score, total_points):
        if total_points == 0:
            return False
        else:
            return quizz_score / total_points * 100


class CompetencyResultVoucher(models.Model):
    _name = 'hr.competency.result.voucher'
    _description = 'Employee Competency Result Voucher'
    _inherits = {'hr.competency.result': 'competency_result_id'}

    competency_result_id = fields.Many2one(
        comodel_name='hr.competency.result',
        string=_('Competency Result'),
        required=True,
        ondelete='cascade',
    )

    employee_user_id = fields.Many2one(
        related='employee_id.user_id',
    )

    description = fields.Html(
        string=_('Description'),
        help=_('Explain why this is worth the allocated number of credits'),
    )

    supporting_documents = fields.Many2many(
        # see /mail/wizard/mail_compose_message_view.xml
        comodel_name='ir.attachment',
        relation='competency_voucher_attachments_rel',
        string=_('Supporting Documents'),
    )

    @api.model
    def create(self, vals):
        vals.update({'result_type': 'voucher'})
        return super(CompetencyResultVoucher, self).create(vals)
