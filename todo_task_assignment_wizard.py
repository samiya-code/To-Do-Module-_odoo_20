from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TodoTaskAssignWizard(models.TransientModel):
    _name = 'todo.task.assign.wizard'
    _description = 'Bulk Task Assignment Wizard'

    assigned_user_id = fields.Many2one('res.users', string='Assign To', required=True)
    task_ids = fields.Many2many('todo.task', string='Tasks')

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            result['task_ids'] = [(6, 0, active_ids)]
        return result

    def action_assign(self):
        if not self.task_ids:
            raise ValidationError(_('Please select at least one task.'))
        self.task_ids.write({'assigned_user_id': self.assigned_user_id.id})
        return {'type': 'ir.actions.act_window_close'}
