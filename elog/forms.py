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
      'board_id', 'board_type', 'location', 'terragreen', 'status', 'test_query', 'test_or_query',
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
    self.fields['picture_compunetix_id_num'] = forms.CharField(label='Compunetix label for ODMB7/5 board (ex. WVVHC-004)', required=False)
    self.fields['picture_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'picture_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    #print(cleaned_data)
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
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

class ShortCircuitForm(forms.Form):
  template_name = "board_tests/shortcircuitform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    resistance_labels =["3.6V PPIB (ODMB7, exp. ~320 Ohm)","0.95V core (exp. ~10 Ohm)","1.2V MGT (exp. ~95 Ohm)","1.0V MGT (exp. ~60 Ohm)","2.5V CLK (exp. ~1850 Ohm)","3.3V OPTICAL (exp. ~1750 Ohm; exp. ~1850 Ohm w/o T12)",
                        "3.3V (exp. ~310 Ohm)","VCCO Bank 0 & 65 (exp. ~125 Ohm)","1.8V VCCO (exp. ~115 Ohm)","1.8V MGT (exp. ~135 Ohm)","1.8V AUX (exp. ~130 Ohm)","1.8V (exp. ~130 Ohm)",
                        "1.8V CLK (exp. ~2200 Ohm; exp. ~1250 Ohm w/o T12)","3.3V CLK (exp. ~3100 Ohm)","1.5V supply (exp. ~8760 Ohm)","3.3V supply (exp. ~3600 Ohm)","5V supply (exp. ~2300 Ohm)","F21 5V fuse",
                        "F22 3.3V fuse","F23 1A fuse","F24 1A fuse (ODMB7 only)"]
    for ipoint in range(21):
      self.fields[f'r_point{ipoint}'] = forms.FloatField(label=(f'Resistance of ' + resistance_labels[ipoint]), required=False)
    #self.fields[f'r_summary'] = forms.BooleanField(label=f'Pass test', required=False)
    self.fields[f'r_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'r_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    #print(cleaned_data)
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
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
    power_supply_labels = ["1.5V power supply", "3.3V power supply", "5V power supply"]
    for ipoint in range(3):
      self.fields[f'a_point{ipoint}'] = forms.FloatField(label=(power_supply_labels[ipoint] + f' current (A)'), required=False)
    self.fields[f'a_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'a_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
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
    for ipoint in range(12):
      self.fields[f'led_{ipoint}'] = forms.BooleanField(label=f'LED {ipoint}', required=False)
    self.fields[f'led_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'led_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class EEPROMConfigurationForm(forms.Form):
  template_name = "board_tests/eepromconfiguration.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'eeprom_programmed'] = forms.BooleanField(label=f'EEPROM has been programmed', required=False)
    self.fields[f'eeprom_done_led'] = forms.BooleanField(label=f'Done LED is lit', required=False)
    self.fields[f'eeprom_5V_current'] = forms.FloatField(label=('Current for 5V supply (expect ~2.9A)'), required=False)
    self.fields[f'eeprom_3p3V_current'] = forms.FloatField(label=('Current for 3.3V supply (expect ~2.1A)'), required=False)
    self.fields[f'eeprom_1p5V_current'] = forms.FloatField(label=('Current for 1.5V supply (expect ~0A)'), required=False)
    self.fields[f'eeprom_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'eeprom_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')
          
class JitterAnalysisForm(forms.Form):
  template_name = "board_tests/jitteranalysisform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['jitter_picture'] = forms.ImageField(label='Screenshot of oscilloscope', required=False)
    self.fields['jitter_tie'] = forms.FloatField(label='TIE measurement (in ps)', required=False)
    self.fields['jitter_mean_freq'] = forms.FloatField(label=('Mean frequency (in MHz)'), required=False)
    self.fields['jitter_min_freq'] = forms.FloatField(label=('Minimum frequency (in MHz)'), required=False)
    self.fields['jitter_max_freq'] = forms.FloatField(label=('Maximum frequency (in MHz)'), required=False)
    self.fields['jitter_sd'] = forms.FloatField(label=('Standard deviation (in kHz)'), required=False)
    self.fields['jitter_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'jitter_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class VMEBasicTestForm(forms.Form):
  template_name = "board_tests/basicvmetest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'vme_done_led'] = forms.BooleanField(label=f'Board successfully progammed itself from the EEPROM', required=False)
    self.fields[f'vme_basic_communication'] = forms.BooleanField(label=f'Communication with VCC was successful', required=False)
    self.fields[f'vme_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'vme_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class FPGAClockTestForm(forms.Form):
  template_name = "board_tests/fpgaclocktest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'fpgaclk_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'fpgaclk_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class SysmonTestForm(forms.Form):
  template_name = "board_tests/sysmontest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    #Labels corresponding to what is being recorded in each field
    current_labels = ["current_5v","current_3v3","current_3v3_reg_op","current_3v3_reg_clk","current_3v6_pp","current_2v5_fc","current_1v2_mgt","current_1v0_mgt","current_0v95","current_3v3_unreg",
                      "current_1v8","current_1v8_aux","current_1v8_mgt","current_1v8_vcco","current_vcco_0_65","current_1v8_reg_clk"]
    
    #Labels corresponding to what is being recorded in each field
    voltage_labels = ["voltage_5v","voltage_5v_lvmb","voltage_3v3","voltage_vphy_3v3","voltage_vpll_3v3","voltage_3v3_reg_op","voltage_3v3_reg_clk","voltage_3v3_clk","voltage_3v3_rx12_1","voltage_3v3_rx12_10",
                      "voltage_3v3_tx12_1","voltage_3v3_tx12_10","voltage_3v3_b04_tx","voltage_3v3_b04_rx","voltage_3v3_spy_vcct","voltage_3v3_spy_vccr","voltage_3v3_pp_fuse","voltage_3v3_pp","voltage_2v5_fc",
                      "voltage_2v5","voltage_2v5_clk_0","voltage_1v2_mgt","voltage_1v0_mgt","voltage_0v95","voltage_3v3_unreg","voltage_1v8","voltage_1v8_aux","voltage_1v8_mgt","voltage_1v8_vcco",
                      "voltage_vcco_0_65","voltage_therm1","voltage_1v8_reg_clk","voltage_1v8_clk_l1","voltage_1v8_clk_l2","voltage_1v8_clk_l3","voltage_1v8_clk_io","voltage_1v8_clk_o",
                      "voltage_vref_gtlp"]
    
    current_fields = len(current_labels)
    voltage_fields = len(voltage_labels)

    #Adds fields for each current value to measure
    for ipoint in range(current_fields):
      self.fields[f'sysmon_current{ipoint}'] = forms.FloatField(label=(current_labels[ipoint] + f' sysmon current pin (pin {ipoint})'), required=False)
    
    #Adds fields for each voltage value to measure
    for ipoint in range(voltage_fields):
      self.fields[f'sysmon_voltage{ipoint}'] = forms.FloatField(label=(voltage_labels[ipoint] + f' sysmon voltage pin (pin {ipoint})'), required=False)

    #Summary button
    self.fields[f'sysmon_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'sysmon_logurl'] = forms.URLField(label=f'URL', required=False)

  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class PROMTestForm(forms.Form):
  template_name = "board_tests/promtest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'prom_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'prom_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class CCBTestForm(forms.Form):
  template_name = "board_tests/ccbtest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'ccb_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'ccb_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class OTMBTestForm(forms.Form):
  template_name = "board_tests/otmbtest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'otmb_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'otmb_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class LVMBTestForm(forms.Form):
  template_name = "board_tests/lvmbtest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for ipoint in range(7):
      self.fields[f'lvmb_adc_{ipoint}'] = forms.BooleanField(label=f'LVMB ADC{ipoint} passes', required=False)
    self.fields[f'lvmb_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'lvmb_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class DCFEBJTAGTestForm(forms.Form):
  template_name = "board_tests/dcfebjtagtest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for ipoint in range(7):
      self.fields[f'dcfebjtag_{ipoint}_connected'] = forms.BooleanField(label=f'xDCFEB{ipoint} passes', required=False)
    self.fields[f'dcfebjtag_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'dcfebjtag_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')



class DCFEBFastSignalTestForm(forms.Form):
  template_name = "board_tests/dcfebfastsignaltest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    labels_signal = ["INJPLS","EXTPLS","BC0","L1A","L1A_MATCH"]
    for ipoint in range(35):
      label_temp = "xDCFEB" + str(ipoint//5) + " " + labels_signal[ipoint%5] +  " succesfully sent"
      self.fields[f'dcfebfastsignal_signal{ipoint}'] = forms.FloatField(label=label_temp, required=False)
    self.fields[f'dcfebfastsignal_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'dcfebfastsignal_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')


class OpticalPRBSTestForm(forms.Form):
  template_name = "board_tests/opticalprbstest.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields[f'opticalprbs_0_pass'] = forms.BooleanField(label=f'Test of B04 Rx - links 1-3', required=False)
    self.fields[f'opticalprbs_1_pass'] = forms.BooleanField(label=f'Test of B04 Tx - all 4 links', required=False)
    self.fields[f'opticalprbs_2_pass'] = forms.BooleanField(label=f'Test of R12 - all 12 links', required=False)
    self.fields[f'opticalprbs_3_pass'] = forms.BooleanField(label=f'Test of T12 - all 12 links', required=False)
    self.fields[f'opticalprbs_4_pass'] = forms.BooleanField(label=f'Test of SPY Tx', required=False)
    self.fields[f'opticalprbs_5_pass'] = forms.BooleanField(label=f'Test of SPY Rx', required=False)
    self.fields[f'opticalprbs_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields[f'opticalprbs_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')
 
 
class MedtermTestForm(forms.Form):
  template_name = "board_tests/medtermtestform.html"
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['medterm_r12_ber'] = forms.FloatField(label='R12 BER (10^-14)', required=False)
    self.fields['medterm_r12_duration'] = forms.IntegerField(label='R12 testing duration (in min)', required=False)
    self.fields['medterm_t12_ber'] = forms.FloatField(label='T12 BER (10^-14)', required=False)
    self.fields['medterm_t12_duration'] = forms.IntegerField(label='T12 testing duration (in min)', required=False)
    self.fields['medterm_summary'] = forms.TypedChoiceField(label='Pass test', required=False, choices=((-1,"Not tested"),(1,"Pass"),(0,"Fail")), coerce=int, empty_value=None, initial=-1)
    self.fields['medterm_logurl'] = forms.URLField(label=f'URL', required=False)
  def clean(self):
    cleaned_data = super().clean()
    # Find filled summary fields
    filled_summary_basenames = []
    for field in cleaned_data:
      if re.search('summary(?!_)',field) and cleaned_data[field] != -1: filled_summary_basenames.append(field.split('_')[0])
    # Make sure if value is filled, that summary is filled.
    for field in cleaned_data:
      if re.search('summary(?!_)',field): continue
      value = cleaned_data[field]
      if value:
        field_basename = field.split('_')[0]
        if field_basename not in filled_summary_basenames:
          raise ValidationError(f'Please change state of "Not tested"')

class TestFilterForm(forms.Form):
  testforms_dict = {'visual inspection': VisualInspectionsForm, 'short circuit':ShortCircuitForm, 'power':PowerForm, 'clock configuration':ClockConfigurationForm, 'eeprom configuration':EEPROMConfigurationForm, 'jitter analysis': JitterAnalysisForm,
                    'vme basic test': VMEBasicTestForm, 'fpga clock test': FPGAClockTestForm, 'sysmon test': SysmonTestForm, 'prom test': PROMTestForm, 'ccb test': CCBTestForm, 'otmb test': OTMBTestForm,
                    'lvmb test': LVMBTestForm, 'dcfeb jtag test': DCFEBJTAGTestForm, 'dcfeb fast signal test': DCFEBFastSignalTestForm, 'optical prbs test': OpticalPRBSTestForm, 'med-term test': MedtermTestForm}
  initial_dict = {'visual inspection': True, 'short circuit': True, 'power': True, 'clock configuration': True, 'eeprom configuration': True, 'jitter analysis': True, 'vme basic test': True, 'fpga clock test':True, 'sysmon test': True,
                  'prom test': True, 'ccb test': True, 'otmb test': True, 'lvmb test': True, 'dcfeb jtag test': True, 'dcfeb fast signal test': True, 'optical prbs test': True, 'med-term test': True}
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for testname in self.testforms_dict:
      self.fields[testname] = forms.BooleanField(label=f'{testname}', required=False)
    self.fields['deselect'] = forms.BooleanField(label='deselect all', required=False)
    #for itest in range(5):
    #  self.fields[f'test{itest+1}'] = forms.BooleanField(label=f'Test {itest+1}', required=False)


