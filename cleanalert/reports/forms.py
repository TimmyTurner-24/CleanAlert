from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class ReportForm(FlaskForm):
    category = SelectField('Category', validators=[DataRequired()], choices=['Sewage',
                                                                             'Dumping',
                                                                             'Overfull (Roadblockage)',
                                                                             'Stinking',
                                                                             'Others'])
    description = TextAreaField('Description', validators=[DataRequired()])
    upload = FileField('Upload Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Submit Report')
    
class UpdateReportStatus(FlaskForm):
    status = SelectField('Status', validators=[DataRequired()], choices=['pending',
                                                                         'in progress',
                                                                         'declined',
                                                                         'resolved'])
    submit = SubmitField('Update Status')