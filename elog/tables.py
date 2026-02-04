import django_tables2 as tables
from django_tables2.utils import A 
from .models import Board, Log
from django.utils.html import format_html
import re

class BoardTable(tables.Table):
  #board_id = tables.Column(linkify=True)
  def render_board_id(self, value, record):
    return format_html("<a href={}> #{} </a>", record.get_absolute_url(), value)
  def render_tests(self, record):
    test_summary = ''
    for db_field in record.tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): 
        test_summary += '1' if db_field.value_from_object(record.tests)==1 else '0' if db_field.value_from_object(record.tests)==0 else '-'
        #print(db_field, db_field.value_from_object(record.tests))
        #print(db_field.name, db_field.value_from_object(record.tests))
    #r_summary = 1 if record.tests.r_summary else 0
    return format_html("{}", test_summary)
  class Meta:
    model = Board
    template_name = "django_tables2/bootstrap.html"
    fields = ("board_type", "board_id", "location", "terragreen", "status", "tests")


from django.urls import reverse
class LogTable(tables.Table):
  edit = tables.Column(empty_values=(), orderable=False)
  delete = tables.Column(empty_values=(), orderable=False)
  date = tables.DateTimeColumn(format = 'Y-m-d, h:i A')
  def render_id(self, value, record):
    return format_html("<a href={}> #{} </a>", record.get_absolute_url(), value)
  def render_edit(self, record):
    #return format_html("<a href={}> Edit </a>", reverse('log-update', args=[str(record.id)]))
    return format_html("<a href={}> Edit </a>", reverse('boardtest-update', args=[str(record.id)]))
  def render_tests(self, record):
    test_summary = ''
    for db_field in record.tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): test_summary += '1' if db_field.value_from_object(record.tests)==1 else '0' if db_field.value_from_object(record.tests)==0 else '-'
        #print(db_field.name, db_field.value_from_object(record.tests))
    #r_summary = 1 if record.tests.r_summary else 0
    return format_html("{}", test_summary)
  def render_delete(self, record):
    #print('debug',self)
    #print('record', record)
    #print('record', repr(record))
    #if record:
    #  result = format_html("<a href={}> Delete </a>", reverse('log-delete', args=[str(record.id)]))
    #else:
    #  #print('strange')
    #  result = format_html('strange')
    result = format_html("<a href={}> Delete </a>", reverse('log-delete', args=[str(record.id)]))
    return result
  def render_board(self, value, record):
    return format_html("<a href={}> {} </a>", record.board.get_absolute_url(), value)
  class Meta:
    model = Log
    template_name = "django_tables2/bootstrap.html"
    fields = ("id", "board", "date", "text", "location", "tests", "edit", "delete")
