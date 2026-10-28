from odoo import models, fields, api                                              #import core from the odoo frameworks
class DocumentRejectionWizard(models.TransientModel):                             #python class banai
    _name = 'hr.document.request.reject.wizard'                                   #wizard ka name rakha
    _description = 'Reject reason Wizard'                                         #description 

    reason = fields.Text(string='Reject reason', required=True)                   #field baan rhi han jahan pa rejection ki reason likhi jy gi #tracking= true q k ya mandatory ha 

    def action_confirm_reject(self):                                              # kab tk chlay ga ( jab tk user confirm ni krta us k bd auto delete
        active_id = self.env.context.get('active_id')                             # mtlb acive id uid k through odoo catch krtta ha so usi id pa wo action perform ho sky
        if active_id:
            record = self.env['hr.document.request'].browse(active_id)            #find record of the model 
            record.write({                                                        #state ko rejection ma dal dena jo pechly sa submit hai.
                'state': 'rejected',
                'rejection_reason': self.reason
            })
        return {'type': 'ir.actions.act_window_close'}
