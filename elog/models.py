from django.db import models
from django.urls import reverse
import datetime

# Create your models here.
class Location(models.Model):
  """Model representing location of board."""
  name = models.CharField(max_length=200, help_text='Enter a location for boards')
  def __str__(self):
    """String for representing Model object."""
    return self.name

class TestResult(models.Model):
  """Model representing test result."""
  name = models.CharField(max_length=200, help_text='Enter test result')
  def __str__(self):
    """String for representing Model object."""
    return self.name

class BoardType(models.Model):
  """Model representing type of board."""
  name = models.CharField(max_length=200, help_text='Enter board type')
  description = models.TextField(help_text='Enter description of board type', null=True, blank=True)

  def __str__(self):
    """String for representing Model object."""
    return self.name

from django.dispatch import receiver
from django.db.models.signals import post_delete

class Board(models.Model):
  """Model representing each board."""
  board_id = models.IntegerField(help_text="Enter board id number")
  board_type = models.ForeignKey('BoardType', on_delete=models.RESTRICT)
  location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
  location_log_id = models.IntegerField(null=True, blank=True)
  status = models.ForeignKey('BoardStatus', on_delete=models.SET_NULL, null=True, blank=True)
  tests = models.OneToOneField('Tests', on_delete=models.SET_NULL, null=True, blank=True)

  def get_absolute_url(self):
    """Returns the URL to access a particular instance of the model."""
    return reverse('board-detail', args=[str(self.id)])

  class Meta:
    ordering = ['board_type', 'board_id']

  def __str__(self):
    """String for representing Model object."""
    return f"{self.board_type}#{self.board_id}"
  def save(self, *args, **kwargs):
    if not self.tests:
      self.tests = Tests.objects.create()
    super().save(*args, **kwargs)

# Delete test when board is deleted
@receiver(post_delete, sender=Board)
def post_delete_tests(sender, instance, *args, **kwargs):
  if instance.tests: 
    instance.tests.delete()


def get_now():
  #return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
  return datetime.datetime.now()

class Log(models.Model):
  """Model representing a log."""
  id = models.AutoField(help_text="log ID", primary_key=True)
  board = models.ForeignKey('Board', on_delete=models.CASCADE)
  date = models.DateTimeField(default=get_now, help_text="Format is YYYY-MM-DD HH:MM")
  location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="board location")
  file = models.FileField(null=True, blank=True)
  text = models.TextField(null=True, blank=True, verbose_name="log")
  status = models.ForeignKey('BoardStatus', on_delete=models.SET_NULL, null=True, blank=True)
  tests = models.OneToOneField('Tests', on_delete=models.CASCADE, null=True, blank=True)
  class Meta:
    ordering = ['-date']
  def __str__(self):
    """String for representing Model object."""
    return str(self.id)
  def get_absolute_url(self):
    """Returns the URL to access a particular instance of the model."""
    return reverse('log-detail', args=[str(self.id)])

# Delete test when log is deleted
from django.db.models import Q
@receiver(post_delete, sender=Log)
def post_delete_tests(sender, instance, *args, **kwargs):
  if instance.tests: 
    instance.tests.delete()
    # Find all summary_log_id fields
    summary_log_id_names = []
    for field in Tests._meta.fields:
      if 'summary_log_id' in field.name: summary_log_id_names.append(field.name)
    #print(summary_log_id_fields)
    # Find [board_id,summary_log_id_name] to modify
    to_modify = []
    for summary_log_id_name in summary_log_id_names:
      #print(summary_log_id_name, instance.id, Board.objects.filter(**{f'tests__{summary_log_id_name}':instance.id}))
      board_search = Board.objects.filter(**{f'tests__{summary_log_id_name}':instance.id})
      if board_search: 
        #print(board_search)
        to_modify.append([board_search[0].board_id, summary_log_id_name])
    #print('to modify', to_modify)
    # Remove board.summary_log_id_names
    for board_id, summary_log_id_name in to_modify:
      # Find related field names
      related_field_names = []
      for field in Tests._meta.fields:
        if len(field.name.split('_')) <= 1: continue
        if summary_log_id_name.split('_')[0] == field.name.split('_')[0]: related_field_names.append(field.name)
      #print('related field names: ', related_field_names)
      # Find if there is an earlier log
      summary_name = summary_log_id_name.replace('_log_id','')
      log_search = Log.objects.filter(Q(**{f'tests__{summary_name}':0})|Q(**{f'tests__{summary_name}':1}))
      #print('Is there an earlier log', log_search)
      if log_search:
        #print('Change to earlier log')
        log = log_search[0]
        board_obj = Board.objects.get(board_id=board_id)
        for related_field_name in related_field_names:
          board_obj.tests.__dict__[related_field_name] = log.tests.__dict__[related_field_name]
        board_obj.tests.__dict__[summary_log_id_name] = log.id
        #print('New log id is: ',log.id,summary_log_id_name)
        board_obj.tests.save()
      else:
        #print('Remove log information')
        board_obj = Board.objects.get(board_id=board_id)
        for related_field_name in related_field_names:
          board_obj.tests.__dict__[related_field_name] = None
        board_obj.tests.save()


class BoardStatus(models.Model):
  """Model representing board status."""
  status = models.CharField(max_length=200, help_text='Enter board status')

  def __str__(self):
    """String for representing Model object."""
    return self.status


class Tests(models.Model):
  """Model representing Tests."""
  id = models.AutoField(help_text="test ID", primary_key=True)
  # Tests need to follow format TESTSUMMARYNAME_TESTNAME. TESTSUMMARYNAME must NOT have underscore.
  picture_front = models.ImageField(null=True, blank=True)
  picture_back = models.ImageField(null=True, blank=True)
  picture_summary = models.IntegerField(null=True, blank=True)
  picture_summary_log_id = models.IntegerField(null=True, blank=True)

  ##Short circuit test##
  #All resistance measurements for the regulators
  r_point0 = models.FloatField(null=True, blank=True)
  r_point1 = models.FloatField(null=True, blank=True)
  r_point2 = models.FloatField(null=True, blank=True)
  r_point3 = models.FloatField(null=True, blank=True)
  r_point4 = models.FloatField(null=True, blank=True)
  r_point5 = models.FloatField(null=True, blank=True)
  r_point6 = models.FloatField(null=True, blank=True)
  r_point7 = models.FloatField(null=True, blank=True)
  r_point8 = models.FloatField(null=True, blank=True)
  r_point9 = models.FloatField(null=True, blank=True)
  r_point10= models.FloatField(null=True, blank=True)
  r_point11= models.FloatField(null=True, blank=True)
  r_point12= models.FloatField(null=True, blank=True)
  r_point13= models.FloatField(null=True, blank=True)

  #Resistance values for the power supply 
  r_point14= models.FloatField(null=True, blank=True)
  r_point15= models.FloatField(null=True, blank=True)
  r_point16= models.FloatField(null=True, blank=True)

  #Checkbox for if fuses pass resistance requirement
  r_point17= models.FloatField(null=True, blank=True)
  r_point18= models.FloatField(null=True, blank=True)
  r_point19= models.FloatField(null=True, blank=True)
  r_point20= models.FloatField(null=True, blank=True)

  #Summary checkbox
  r_summary = models.IntegerField(null=True, blank=True)
  r_summary_log_id = models.IntegerField(null=True, blank=True)
  ####################################################

  ##Power test on the bench
  #Measurements of each voltage regulator
  a_point0 = models.FloatField(null=True, blank=True)
  a_point1 = models.FloatField(null=True, blank=True)
  a_point2 = models.FloatField(null=True, blank=True)
 
  #Summary checkbox
  a_summary = models.IntegerField(null=True, blank=True)
  a_summary_log_id = models.IntegerField(null=True, blank=True)
  ###################################################


  ##LEDs for clock configuration test
  #Various LEDs on front panel
  led_0 = models.BooleanField(null=True, blank=True)
  led_1 = models.BooleanField(null=True, blank=True)
  led_2 = models.BooleanField(null=True, blank=True)
  led_3 = models.BooleanField(null=True, blank=True)
  led_4 = models.BooleanField(null=True, blank=True)
  led_5 = models.BooleanField(null=True, blank=True)
  led_6 = models.BooleanField(null=True, blank=True)
  led_7 = models.BooleanField(null=True, blank=True)
  led_8 = models.BooleanField(null=True, blank=True)
  led_9 = models.BooleanField(null=True, blank=True)
  led_10= models.BooleanField(null=True, blank=True)
  led_11= models.BooleanField(null=True, blank=True)

  #Summary checkbox
  led_summary = models.IntegerField(null=True, blank=True)
  led_summary_log_id = models.IntegerField(null=True, blank=True)
  ##################################################

  ##FPGA & EEPROM Programming Test
  #Various requirements for the EEPROM programming test
  eeprom_programmed = models.BooleanField(null=True, blank=True)
  eeprom_done_led = models.BooleanField(null=True, blank=True)

  #Summary checkbox
  eeprom_summary = models.IntegerField(null=True, blank=True)
  eeprom_summary_log_id = models.IntegerField(null=True, blank=True)

  ##Basic VME tests 
  #Checkboxes for basic VME test
  vme_done_led = models.BooleanField(null=True, blank=True)
  vme_basic_communication = models.BooleanField(null=True, blank=True)

  #Summary checkbox
  vme_summary = models.IntegerField(null=True, blank=True)
  vme_summary_log_id = models.IntegerField(null=True, blank=True)
  #################################################

  ##FPGA Clock test
  #Summary checkbox
  fpgaclk_summary = models.IntegerField(null=True, blank=True)
  fpgaclk_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################


  ##System monitor test
  #Sysmon currents
  sysmon_current0 = models.FloatField(null=True, blank=True)
  sysmon_current1 = models.FloatField(null=True, blank=True)
  sysmon_current2 = models.FloatField(null=True, blank=True)
  sysmon_current3 = models.FloatField(null=True, blank=True)
  sysmon_current4 = models.FloatField(null=True, blank=True)
  sysmon_current5 = models.FloatField(null=True, blank=True)
  sysmon_current6 = models.FloatField(null=True, blank=True)
  sysmon_current7 = models.FloatField(null=True, blank=True)
  sysmon_current8 = models.FloatField(null=True, blank=True)
  sysmon_current9 = models.FloatField(null=True, blank=True)
  sysmon_current10= models.FloatField(null=True, blank=True)
  sysmon_current11= models.FloatField(null=True, blank=True)
  sysmon_current12= models.FloatField(null=True, blank=True)
  sysmon_current13= models.FloatField(null=True, blank=True)
  sysmon_current14= models.FloatField(null=True, blank=True)
  sysmon_current15= models.FloatField(null=True, blank=True)
  sysmon_current16= models.FloatField(null=True, blank=True)


  #Sysmon voltages
  sysmon_voltage0 = models.FloatField(null=True, blank=True)
  sysmon_voltage1 = models.FloatField(null=True, blank=True)
  sysmon_voltage2 = models.FloatField(null=True, blank=True)
  sysmon_voltage3 = models.FloatField(null=True, blank=True)
  sysmon_voltage4 = models.FloatField(null=True, blank=True)
  sysmon_voltage5 = models.FloatField(null=True, blank=True)
  sysmon_voltage6 = models.FloatField(null=True, blank=True)
  sysmon_voltage7 = models.FloatField(null=True, blank=True)
  sysmon_voltage8 = models.FloatField(null=True, blank=True)
  sysmon_voltage9 = models.FloatField(null=True, blank=True)
  sysmon_voltage10= models.FloatField(null=True, blank=True)
  sysmon_voltage11= models.FloatField(null=True, blank=True)
  sysmon_voltage12= models.FloatField(null=True, blank=True)
  sysmon_voltage13= models.FloatField(null=True, blank=True)
  sysmon_voltage14= models.FloatField(null=True, blank=True)
  sysmon_voltage15= models.FloatField(null=True, blank=True)
  sysmon_voltage16= models.FloatField(null=True, blank=True)
  sysmon_voltage17= models.FloatField(null=True, blank=True)
  sysmon_voltage18= models.FloatField(null=True, blank=True)
  sysmon_voltage19= models.FloatField(null=True, blank=True)
  sysmon_voltage20= models.FloatField(null=True, blank=True)
  sysmon_voltage21= models.FloatField(null=True, blank=True)
  sysmon_voltage22= models.FloatField(null=True, blank=True)
  sysmon_voltage23= models.FloatField(null=True, blank=True)
  sysmon_voltage24= models.FloatField(null=True, blank=True)
  sysmon_voltage25= models.FloatField(null=True, blank=True)
  sysmon_voltage26= models.FloatField(null=True, blank=True)
  sysmon_voltage27= models.FloatField(null=True, blank=True)
  sysmon_voltage28= models.FloatField(null=True, blank=True)
  sysmon_voltage29= models.FloatField(null=True, blank=True)
  sysmon_voltage30= models.FloatField(null=True, blank=True)
  sysmon_voltage31= models.FloatField(null=True, blank=True)
  sysmon_voltage32= models.FloatField(null=True, blank=True)
  sysmon_voltage33= models.FloatField(null=True, blank=True)
  sysmon_voltage34= models.FloatField(null=True, blank=True)
  sysmon_voltage35= models.FloatField(null=True, blank=True)
  sysmon_voltage36= models.FloatField(null=True, blank=True)
  sysmon_voltage37= models.FloatField(null=True, blank=True)
  sysmon_voltage38= models.FloatField(null=True, blank=True)

  #Summary checkbox
  sysmon_summary = models.IntegerField(null=True, blank=True)
  sysmon_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################


  ##PROM test
  #Summary checkbox
  prom_summary = models.IntegerField(null=True, blank=True)
  prom_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################


  ##CCB test
  #Summary checkbox
  ccb_summary = models.IntegerField(null=True, blank=True)
  ccb_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################



  ##OTMB test
  #Summary checkbox
  otmb_summary = models.IntegerField(null=True, blank=True)
  otmb_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################



  ##LVMB test
  #Checkboxes if ADCs have passed voltage test
  lvmb_adc_0 = models.BooleanField(null=True, blank=True)
  lvmb_adc_1 = models.BooleanField(null=True, blank=True)
  lvmb_adc_2 = models.BooleanField(null=True, blank=True)
  lvmb_adc_3 = models.BooleanField(null=True, blank=True)
  lvmb_adc_4 = models.BooleanField(null=True, blank=True)
  lvmb_adc_5 = models.BooleanField(null=True, blank=True)
  lvmb_adc_6 = models.BooleanField(null=True, blank=True)

  #Summary checkbox
  lvmb_summary = models.IntegerField(null=True, blank=True)
  lvmb_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################



  ##DCFEB JTAG test
  dcfebjtag_0_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_1_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_2_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_3_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_4_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_5_connected = models.BooleanField(null=True, blank=True)
  dcfebjtag_6_connected = models.BooleanField(null=True, blank=True)

  #Summary checkbox
  dcfebjtag_summary = models.IntegerField(null=True, blank=True)
  dcfebjtag_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################



  ##DCFEB fast signal test
  #INJPLS, EXTPLS, BC0, L1A, L1A_MATCH values
  dcfebfastsignal_signal0 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal1 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal2 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal3 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal4 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal5 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal6 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal7 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal8 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal9 = models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal10= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal11= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal12= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal13= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal14= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal15= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal16= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal17= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal18= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal19= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal20= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal21= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal22= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal23= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal24= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal25= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal26= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal27= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal28= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal29= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal30= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal31= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal32= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal33= models.FloatField(null=True, blank=True)
  dcfebfastsignal_signal34= models.FloatField(null=True, blank=True)

  #Summary checkbox
  dcfebfastsignal_summary = models.IntegerField(null=True, blank=True)
  dcfebfastsignal_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################



  ##Optical PRBS test
  #Checkboxes if Tx12, Rx12, B04, and SPY link have passed optical loopback test
  opticalprbs_0_pass = models.BooleanField(null=True, blank=True)
  opticalprbs_1_pass = models.BooleanField(null=True, blank=True)
  opticalprbs_2_pass = models.BooleanField(null=True, blank=True)

  #Summary checkbox
  opticalprbs_summary = models.IntegerField(null=True, blank=True)
  opticalprbs_summary_log_id = models.IntegerField(null=True, blank=True)
  ################################################


  def __str__(self):
    """String for representing Model object."""
    return str(self.id)

