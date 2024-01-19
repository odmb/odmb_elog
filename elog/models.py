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
  r_point0 = models.FloatField(null=True, blank=True)
  r_point1 = models.FloatField(null=True, blank=True)
  r_point2 = models.FloatField(null=True, blank=True)
  r_point3 = models.FloatField(null=True, blank=True)
  r_point4 = models.FloatField(null=True, blank=True)
  r_summary = models.IntegerField(null=True, blank=True)
  r_summary_log_id = models.IntegerField(null=True, blank=True)
  v_point0 = models.FloatField(null=True, blank=True)
  v_point1 = models.FloatField(null=True, blank=True)
  v_point2 = models.FloatField(null=True, blank=True)
  v_point3 = models.FloatField(null=True, blank=True)
  v_point4 = models.FloatField(null=True, blank=True)
  v_summary = models.IntegerField(null=True, blank=True)
  v_summary_log_id = models.IntegerField(null=True, blank=True)
  led_0 = models.BooleanField(null=True, blank=True)
  led_1 = models.BooleanField(null=True, blank=True)
  led_2 = models.BooleanField(null=True, blank=True)
  led_summary = models.IntegerField(null=True, blank=True)
  led_summary_log_id = models.IntegerField(null=True, blank=True)

  def __str__(self):
    """String for representing Model object."""
    return str(self.id)

