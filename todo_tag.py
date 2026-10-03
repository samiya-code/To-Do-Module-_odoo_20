from odoo import fields, models


class TodoTag(models.Model):
    _name = 'todo.tag'
    _description = 'Task Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=0)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('todo_tag_name_uniq', 'unique(name)', 'Tag name must be unique.'),
    ]
