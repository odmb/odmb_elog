from django import forms
from .models import BoardType, Board, Location, Log, BoardStatus
import re

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
    #self.fields['board'].help_text = 'Format is BOARD_TYPE#BOARD_ID <br> BOARD_TYPE: '+", ".join([str(bt) for bt in BoardType.objects.all()])
    self.fields['board'].help_text = 'Format is BOARD_TYPE#BOARD_ID <br> BOARD_TYPE: '+", ".join([str(bt) for bt in BoardType.objects.all()]) if len(BoardType.objects.all())!= 0 else 'Format is BOARD_TYPE#BOARD_ID <br> But there are no BOARD_TYPEs.'
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
      'board_id', 'board_type', 'location', 'status', 'test_query', 'test_or_query',
      Submit('submit', 'Apply Filter'),
  )

class LogFilterFormHelper(FormHelper):
  form_method = 'GET'
  help_text_inline = True
  board_query = forms.CharField()
  layout = Layout(
      'board_query', 'location', 'status', 'date', 'query', 'test_query', 'test_or_query',
      Submit('submit', 'Apply Filter'),
  )

from django import forms
from django.core.exceptions import ValidationError
def validate_board_id(value):
  if '#' not in value:
    raise ValidationError(f'{value} does not have #')
  board_name_split = value.split('#')
  in_board_type = board_name_split[0]
  in_board_id = board_name_split[1]
  if not in_board_id.isdigit():
    raise ValidationError(f'{in_board_id} is not an integer')
  in_board_id = int(in_board_id)
  board_objects = Board.objects.filter(board_type__name=in_board_type).filter(board_id=in_board_id)
  if len(board_objects) == 0:
    raise forms.ValidationError(f"board_type={in_board_type} with board_id={in_board_id} can not be found")

import datetime
class BoardTestForm(forms.ModelForm):
  def __init__(self, *args, **kwargs):
    super(BoardTestForm, self).__init__(*args, **kwargs)
    self.fields['board'].help_text = 'Format is BOARD_TYPE#BOARD_ID <br> BOARD_TYPE: '+", ".join([str(bt) for bt in BoardType.objects.all()]) if len(BoardType.objects.all())!= 0 else 'Format is BOARD_TYPE#BOARD_ID <br> But there are no BOARD_TYPEs.'
    self.fields['date'].help_text = 'Format is YYYY-MM-DD HH:MM'
  board = BoardChoiceField()
  class Meta:
    model = Log
    fields = ['board', 'date', 'location', 'text']

class VisualInspectionsForm(forms.Form):
  template_name = "board_tests/visualinspectionform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['picture_front'] = forms.ImageField(label='Front picture', required=False)
    self.fields['picture_back'] = forms.ImageField(label='Back picture', required=False)
    self.fields['picture_summary'] = forms.ChoiceField(label=f'Pass test', required=False, choices=(("-1","Not tested"),("1","Pass"),("0","Fail")), initial='-1')
    self.fields[f'picture_logurl'] = forms.URLField(label=f'URL', required=False)

class ShortCircuitForm(forms.Form):
  template_name = "board_tests/shortcircuitform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for ipoint in range(5):
      self.fields[f'r_point{ipoint}'] = forms.FloatField(label=f'Point {ipoint} resistance (ohm)', required=False)
    #self.fields[f'r_summary'] = forms.BooleanField(label=f'Pass test', required=False)
    self.fields[f'r_summary'] = forms.ChoiceField(label=f'Pass test', required=False, choices=(("-1","Not tested"),("1","Pass"),("0","Fail")), initial='-1')
    self.fields[f'r_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    #print(cleaned_data)
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != '-1': filled_summary_basenames.append(field.split('_')[0])
    #print(filled_summary_basenames)
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          #print(f'error {field}, {cleaned_data[field]}')
          raise ValidationError(f'Please change state of "Not tested"')

class PowerForm(forms.Form):
  template_name = "board_tests/powerform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for ipoint in range(5):
      self.fields[f'v_point{ipoint}'] = forms.FloatField(label=f'Point {ipoint} voltage (V)', required=False)
    self.fields[f'v_summary'] = forms.ChoiceField(label=f'Pass test', required=False, choices=(("-1","Not tested"),("1","Pass"),("0","Fail")), initial='-1')
    self.fields[f'v_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != '-1': filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class ClockConfigurationForm(forms.Form):
  template_name = "board_tests/clockconfiguration.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for ipoint in range(3):
      self.fields[f'led_{ipoint}'] = forms.BooleanField(label=f'LED {ipoint}', required=False)
    self.fields[f'led_summary'] = forms.ChoiceField(label=f'Pass test', required=False, choices=(("-1","Not tested"),("1","Pass"),("0","Fail")), initial='-1')
    self.fields[f'led_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != '-1': filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class TestFilterForm(forms.Form):
  testforms_dict = {'visual inspection': VisualInspectionsForm, 'short circuit':ShortCircuitForm, 'power':PowerForm, 'clock configuration':ClockConfigurationForm}
  initial_dict = {'visual inspection': True, 'short circuit': True, 'power': True, 'clock configuration':True}
  #initial_dict = {'short circuit': True}
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for testname in self.testforms_dict:
      self.fields[testname] = forms.BooleanField(label=f'{testname}', required=False)
    self.fields['deselect'] = forms.BooleanField(label='deselect all', required=False)
    #for itest in range(5):
    #  self.fields[f'test{itest+1}'] = forms.BooleanField(label=f'Test {itest+1}', required=False)
