from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TodoTask(models.Model):
    _name = 'todo.task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'To-do Task'
    _order = 'priority desc, deadline asc, create_date desc'

    name = fields.Char(string='Task Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        default=lambda self: self.env.user,
        tracking=True,
    )
    created_by_id = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
        copy=False,
    )
    department = fields.Char(string='Responsible Department')
    priority = fields.Selection(
        [('0', 'No Priority'), ('1', 'Low'), ('2', 'Medium'), ('3', 'High')],
        string='Priority',
        default='0',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('waiting', 'Waiting'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
    )
    deadline = fields.Date(string='Deadline', tracking=True)
    start_date = fields.Date(string='Start Date')
    completion_date = fields.Date(string='Completion Date', readonly=True, tracking=True)
    tag_ids = fields.Many2many(
        'todo.tag',
        'todo_task_tag_rel',
        'task_id',
        'tag_id',
        string='Tags',
    )
    color = fields.Integer(string='Color', default=0)
    progress = fields.Integer(string='Progress', default=0, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(string='Active', default=True)
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')
    recurring_task = fields.Boolean(string='Recurring Task', default=False)
    recurrence_type = fields.Selection(
        [('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly'), ('year', 'Yearly')],
        string='Recurrence Type',
        default='day',
    )
    recurrence_interval = fields.Integer(string='Recurrence Interval', default=1)
    next_recurrence_date = fields.Date(string='Next Recurrence Date')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'todo_task_attachment_rel',
        'task_id',
        'attachment_id',
        string='Attachments',
    )
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue', search='_search_is_overdue')

    _sql_constraints = [
        ('progress_range', 'CHECK (progress >= 0 AND progress <= 100)', 'Progress must be between 0 and 100.'),
    ]

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].strip()
        if not vals.get('created_by_id'):
            vals['created_by_id'] = self.env.user.id
        if not vals.get('assigned_user_id'):
            vals['assigned_user_id'] = self.env.user.id
        if vals.get('state') == 'completed' and not vals.get('completion_date'):
            vals['completion_date'] = fields.Date.context_today(self)
        if vals.get('state') == 'completed' and 'progress' not in vals:
            vals['progress'] = 100
        if vals.get('state') == 'cancelled' and 'progress' not in vals:
            vals['progress'] = 0
        return super().create(vals)

    def write(self, vals):
        if vals.get('state') == 'completed' and not vals.get('completion_date'):
            vals['completion_date'] = fields.Date.context_today(self)
        if vals.get('state') == 'cancelled' and 'progress' not in vals:
            vals['progress'] = 0
        if vals.get('state') == 'new' and 'progress' not in vals:
            vals['progress'] = 0
        if vals.get('state') == 'in_progress' and 'progress' not in vals:
            vals['progress'] = 50
        if vals.get('state') == 'waiting' and 'progress' not in vals:
            vals['progress'] = 50
        if vals.get('state') == 'completed' and 'progress' not in vals:
            vals['progress'] = 100
        return super().write(vals)

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(_('Task name cannot be empty.'))

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError(_('Progress must be between 0 and 100.'))

    @api.constrains('recurrence_interval')
    def _check_recurrence_interval(self):
        for record in self:
            if record.recurring_task and record.recurrence_interval <= 0:
                raise ValidationError(_('Recurrence interval must be greater than zero.'))

    @api.constrains('start_date', 'completion_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.completion_date and record.completion_date < record.start_date:
                raise ValidationError(_('Completion date cannot be before the start date.'))
            if record.deadline and record.start_date and record.deadline < record.start_date:
                raise ValidationError(_('Deadline cannot be before the start date.'))

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.deadline and record.deadline < today and record.state not in ('completed', 'cancelled')
            )

    def _search_is_overdue(self, operator, value):
        today = fields.Date.context_today(self)
        if operator not in ('=', '!='):
            return []
        overdue = bool(value)
        if overdue:
            return [
                '&',
                ('deadline', '<', today),
                ('state', 'not in', ['completed', 'cancelled']),
            ]
        return ['|', ('deadline', '>=', today), ('state', 'in', ['completed', 'cancelled'])]

    def action_start(self):
        for record in self:
            record.write({'state': 'in_progress', 'progress': 50, 'start_date': record.start_date or fields.Date.context_today(record)})

    def action_pause(self):
        self.write({'state': 'waiting', 'progress': 50})

    def action_complete(self):
        for record in self:
            if record.state == 'completed':
                continue
            record.write({
                'state': 'completed',
                'progress': 100,
                'completion_date': record.completion_date or fields.Date.context_today(record),
            })
            if record.recurring_task:
                record._create_next_recurrence()

    def action_cancel(self):
        self.write({'state': 'cancelled', 'progress': 0, 'completion_date': False})

    def action_reopen(self):
        self.write({'state': 'new', 'progress': 0, 'completion_date': False})

    def _create_next_recurrence(self):
        if not self.recurring_task:
            return False
        if not self.recurrence_type or self.recurrence_interval <= 0:
            return False
        base_day = self.next_recurrence_date or self.deadline or fields.Date.context_today(self)
        next_date = fields.Date.from_string(base_day)
        if self.recurrence_type == 'day':
            next_date = next_date + relativedelta(days=self.recurrence_interval)
        elif self.recurrence_type == 'week':
            next_date = next_date + relativedelta(weeks=self.recurrence_interval)
        elif self.recurrence_type == 'month':
            next_date = next_date + relativedelta(months=self.recurrence_interval)
        elif self.recurrence_type == 'year':
            next_date = next_date + relativedelta(years=self.recurrence_interval)
        existing = self.env['todo.task'].search_count([
            ('name', '=', self.name),
            ('assigned_user_id', '=', self.assigned_user_id.id),
            ('deadline', '=', next_date),
            ('state', '=', 'new'),
        ])
        if existing:
            self.next_recurrence_date = next_date
            return False
        task = self.copy(default={
            'state': 'new',
            'progress': 0,
            'completion_date': False,
            'start_date': False,
            'assigned_user_id': self.assigned_user_id.id,
            'created_by_id': self.env.user.id,
            'deadline': next_date,
            'next_recurrence_date': False,
            'recurring_task': True,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
        })
        self.next_recurrence_date = next_date
        return task

    def _get_task_action(self, name, domain):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'todo.task',
            'view_mode': 'kanban,list,form',
            'domain': domain,
            'target': 'current',
            'context': {'default_assigned_user_id': self.env.user.id},
        }
