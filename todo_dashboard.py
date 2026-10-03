from odoo import _, api, fields, models


class TodoDashboard(models.Model):
    _name = 'todo.dashboard'
    _description = 'To-do Dashboard'
    _rec_name = 'name'

    name = fields.Char(default='Task Studio Dashboard', readonly=True)
    total_tasks = fields.Integer(string='Total Tasks', compute='_compute_stats')
    my_tasks = fields.Integer(string='My Tasks', compute='_compute_stats')
    new_tasks = fields.Integer(string='New Tasks', compute='_compute_stats')
    in_progress_tasks = fields.Integer(string='In Progress', compute='_compute_stats')
    waiting_tasks = fields.Integer(string='Waiting', compute='_compute_stats')
    completed_tasks = fields.Integer(string='Completed', compute='_compute_stats')
    overdue_tasks = fields.Integer(string='Overdue', compute='_compute_stats')
    high_priority_tasks = fields.Integer(string='High Priority', compute='_compute_stats')

    @api.depends_context('uid')
    def _compute_stats(self):
        user = self.env.user
        today = fields.Date.context_today(self)
        for record in self:
            record.total_tasks = self.env['todo.task'].search_count([])
            record.my_tasks = self.env['todo.task'].search_count([('assigned_user_id', '=', user.id)])
            record.new_tasks = self.env['todo.task'].search_count([('state', '=', 'new')])
            record.in_progress_tasks = self.env['todo.task'].search_count([('state', '=', 'in_progress')])
            record.waiting_tasks = self.env['todo.task'].search_count([('state', '=', 'waiting')])
            record.completed_tasks = self.env['todo.task'].search_count([('state', '=', 'completed')])
            record.overdue_tasks = self.env['todo.task'].search_count([
                ('deadline', '<', today),
                ('state', 'not in', ['completed', 'cancelled']),
            ])
            record.high_priority_tasks = self.env['todo.task'].search_count([('priority', '=', '3')])

    def _open_tasks(self, name, domain):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'todo.task',
            'view_mode': 'kanban,list,form',
            'domain': domain,
            'target': 'current',
            'context': {'default_assigned_user_id': self.env.user.id},
        }

    def action_open_total_tasks(self):
        return self._open_tasks(_('All Tasks'), [])

    def action_open_my_tasks(self):
        return self._open_tasks(_('My Tasks'), [('assigned_user_id', '=', self.env.user.id)])

    def action_open_new_tasks(self):
        return self._open_tasks(_('New Tasks'), [('state', '=', 'new')])

    def action_open_in_progress(self):
        return self._open_tasks(_('In Progress'), [('state', '=', 'in_progress')])

    def action_open_waiting(self):
        return self._open_tasks(_('Waiting Tasks'), [('state', '=', 'waiting')])

    def action_open_completed(self):
        return self._open_tasks(_('Completed Tasks'), [('state', '=', 'completed')])

    def action_open_overdue(self):
        return self._open_tasks(_('Overdue Tasks'), [
            ('deadline', '<', fields.Date.context_today(self)),
            ('state', 'not in', ['completed', 'cancelled']),
        ])

    def action_open_high_priority(self):
        return self._open_tasks(_('High Priority Tasks'), [('priority', '=', '3')])
