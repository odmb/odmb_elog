from django import forms
from .models import BoardType, Board, Location, Log, BoardStatus

#class LogForm(forms.ModelForm):
#  log = forms.ModelChoiceField(queryset=Log.objects.all())
#  class Meta:
#    model = Board
#    fields = ['board_type', 'board_id']

# reference: https://stackoverflow.com/questions/12026721/django-form-clean-foreignkey-with-to-field-value
class BoardChoiceField(forms.ModelChoiceField):
  def __init__(self, *args, **kwargs):
    self.widget = kwargs.pop('widget', forms.TextInput)
    queryset=Board.objects.all()
    super(BoardChoiceField, self).__init__(queryset, *args, **kwargs)

  def prepare_value(self, value):
    # return value from original value, a PK.
    value = super(BoardChoiceField, self).prepare_value(value)
    if type(value) != int:
      return value
    try:
      return self.queryset.model.objects.get(id=value)
    except self.queryset.model.DoesNotExist:
      return ''

  def clean(self, value):
    board_name = value
    if board_name is not None:
      board_name_split = board_name.split('#')
      if len(board_name_split) != 2:
        raise forms.ValidationError("Board name is not correct")
      in_board_type = board_name_split[0]
      in_board_id = int(board_name_split[1])
      board_objects = Board.objects.filter(board_type__name=in_board_type).filter(board_id=in_board_id)
      if len(board_objects) == 0:
        raise forms.ValidationError("Board name is not correct")
      else: 
        board_object = board_objects[0]
    else:
      raise forms.ValidationError("This field cannot be null")
    return board_object


# Maybe improve reference: https://simpleisbetterthancomplex.com/tutorial/2018/11/28/advanced-form-rendering-with-django-crispy-forms.html
class LogForm(forms.ModelForm):
  def __init__(self, *args, **kwargs):
    super(LogForm, self).__init__(*args, **kwargs)
    self.fields['board'].help_text = 'Format is BOARD_TYPE#BOARD_ID <br> BOARD_TYPE: '+", ".join([str(bt) for bt in BoardType.objects.all()])
    self.fields['date'].help_text = 'Format is YYYY-MM-DD HH:MM'

  board = BoardChoiceField()
  class Meta:
    model = Log
    fields = ['board', 'date', 'location', 'file', 'text', 'status']


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
class BoardFilterFormHelper(FormHelper):
  form_method = 'GET'
  layout = Layout(
      'board_id', 'board_type', 'location', 'status', 
      Submit('submit', 'Apply Filter'),
  )

class LogFilterFormHelper(FormHelper):
  form_method = 'GET'
  help_text_inline = True
  board_query = forms.CharField()
  layout = Layout(
      'board_query', 'location', 'status', 'date', 'query',
      Submit('submit', 'Apply Filter'),
  )
