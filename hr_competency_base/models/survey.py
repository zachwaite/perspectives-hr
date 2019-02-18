from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SurveyEvaluationMixin(models.AbstractModel):
    _name = 'survey.evaluation.mixin'
    _description = 'Survey Evaluation Mixin'

    evaluation_id = fields.Many2one(
        comodel_name='hr.evaluation',
        string=_('Evaluation'),
        help=_('Related knowledge test or return demo, if one exists'),
    )

    eligible_evaluators_user_ids = fields.Many2many(
        related='evaluation_id.eligible_evaluators_user_ids',
    )

    eligible_employees_user_ids = fields.Many2many(
        related='evaluation_id.eligible_employees_user_ids',
    )

class Survey(models.Model):
    _name = 'survey.survey'
    _inherit = ['survey.survey', 'survey.evaluation.mixin']

    total_available_points = fields.Float(
        string=_('Total Available Points'),
        compute='_compute_total_available_points',
    )

    @api.multi
    def _compute_total_available_points(self):
        for survey in self:
            points_1 = sum(survey.mapped('page_ids.question_ids.labels_ids.quizz_mark'))
            points_2 = sum(survey.mapped('page_ids.question_ids.labels_ids_2.quizz_mark'))
            survey.total_available_points = points_1 + points_2


class SurveyPage(models.Model):
    _inherit = 'survey.page'

    evaluation_id = fields.Many2one(
        related='survey_id.evaluation_id',
    )


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    evaluation_id = fields.Many2one(
        related='page_id.evaluation_id',
    )


class SurveyLabel(models.Model):
    _inherit = 'survey.label'

    evaluation_id = fields.Many2one(
        related='question_id.evaluation_id',
    )

    # don't allow negative quizz_mark on evaluations
    # because we normalize scores to percentages
    @api.multi
    @api.constrains('evaluation_id', 'quizz_mark')
    def _check_quizz_mark(self):
        for label in self:
            if label.evaluation_id:
                if label.quizz_mark < 0:
                    raise ValidationError(_('Negative points are not allowed for evaluations.'))

    @api.multi
    @api.constrains('question_id', 'question_id_2')
    def _check_evaluation_id(self):
        for label in self:
            if label.question_id.type == 'multiple_choice':
                if (label.question_id.evaluation_id and not label.question_id_2.evaluation_id) or \
                   (label.question_id_2.evaluation_id and not label.question_id.evaluation_id):
                    raise ValidationError(_("Both questions should be associated to evaluation"))


class SurveyUserInput(models.Model):
    _name = 'survey.user_input'
    _inherit = ['survey.user_input', 'survey.evaluation.mixin']

    evaluation_id = fields.Many2one(
        related='survey_id.evaluation_id',
    )

    evaluator_user_id = fields.Many2one(
        comodel_name='res.users',
        string=_('Evaluator')
    )

    employee_user_id = fields.Many2one(
        comodel_name='res.users',
        string=_('Evaluatee'),
    )

    total_available_points = fields.Float(
        related='survey_id.total_available_points',
    )

    @api.multi
    @api.constrains('evaluator_user_id', 'employee_user_id')
    def _check_users(self):
        for user_input in self:
            if user_input.evaluation_id.evaluation_type == 'return_demo':
                if user_input.evaluator_user_id == user_input.employee_user_id:
                    raise ValidationError(_('Employee can not evaluate himself for return demos'))
            elif user_input.evaluation_id.evaluation_type == 'knowledge_test':
                if user_input.evaluator_user_id != user_input.employee_user_id:
                    raise ValidationError(_('Employee must evaluate himself for knowledge test'))

    # called by server action
    @api.multi
    def process_evaluation_results(self):
        EvaluationResult = self.env['hr.competency.result.evaluation'].sudo()
        SudoEmployee = self.env['hr.employee'].sudo()
        for answer in self:
            if answer.evaluation_id:
                existing_results = EvaluationResult.search([('user_input_id', '=', answer.id)])
                if not existing_results:
                    # create a result for each of the employees associated to this user
                    # even though this should only be one user
                    employee_user_employees = SudoEmployee.search([('user_id', '=', answer.employee_user_id.id)])
                    for employee in employee_user_employees:
                        vals = {
                            'result_type': 'evaluation',
                            'evaluation_id': answer.evaluation_id.id,
                            'user_input_id': answer.id,
                            'employee_id': employee.id,
                            'evaluator_user_id': answer.evaluator_user_id.id,
                            'competency_requirement_ids': [(6, 0, answer.evaluation_id.competency_requirement_ids.ids)],
                        }
                        new_result = EvaluationResult.create(vals)
                        new_result.set_name()
                        new_result.set_scores()
                        new_result.set_credits()
        return True


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    evaluation_id = fields.Many2one(
        related='user_input_id.evaluation_id',
    )

