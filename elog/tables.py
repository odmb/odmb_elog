import django_tables2 as tables
from django_tables2.utils import A 
from .models import Board, Log
from django.utils.html import format_html
import re

class BoardTable(tables.Table):
  #board_id = tables.Column(linkify=True)
  tests_ucsb = tables.Column(empty_values=(), verbose_name=format_html('<span title="1: Visual inspection | 2: Short circuit test | 3: Power test | 4: Clock configuration | 5: EEPROM configuration | 6: Jitter analysis | 7: Basic VME test | 8: FPGA clock test | 9: System monitoring test | 10: PROM test | 11: CCB test | 12: OTMB test | 13: LVMB/LVMB7 test | 14: DCFEB JTAG test | 15: DCFEB fast signal test | 16: Optical PRBS test | 17: Med-term IBERT | 18: Step 27 test">Tests at UCSB<br><small>Hover for full details</small></span>'), orderable=False)
  tests_b904 = tables.Column(empty_values=(), verbose_name=format_html('<span title="1: Visual inspection | 2: Short circuit test | 3: Power test | 4: Clock configuration | 5: EEPROM configuration | 6: Jitter analysis | 7: Basic VME test | 8: FPGA clock test | 9: System monitoring test | 10: PROM test | 11: CCB test | 12: OTMB test | 13: LVMB/LVMB7 test | 14: DCFEB JTAG test | 15: DCFEB fast signal test | 16: Optical PRBS test | 17: Med-term IBERT | 18: Step 27 test">Tests at B904<br><small>Hover for full details</small></span>'), orderable=False)
  def render_board_id(self, value, record):
    return format_html("<a href={}> #{} </a>", record.get_absolute_url(), value)
  def _tests_summary_for_location(self, record, location_value):
    if record.tests is None:
            return ""
    logs_qs = record.log_set.filter(location_id=location_value).select_related("tests").order_by("-pk")
    logs = list(logs_qs)
    test_summary = ""
    for db_field in record.tests._meta.get_fields():
            if not hasattr(db_field, "attname"):
                continue
            if not re.search(r"summary(?!_)", db_field.name):
                continue
                
            char = "-"
            for log in logs:
                if getattr(log, "tests", None) is None:
                    continue
                v = db_field.value_from_object(log.tests)
                if v in (0, 1):
                    char = "1" if v == 1 else "0"
                    break
            test_summary += char
    return test_summary
    
  def render_tests_ucsb(self, record):
    return format_html("{}", self._tests_summary_for_location(record, 1))

  def render_tests_b904(self, record):
    return format_html("{}", self._tests_summary_for_location(record, 5))

  class Meta:
    model = Board
    template_name = "django_tables2/bootstrap.html"
    fields = ("board_type", "board_id", "location", "terragreen", "tests_ucsb", "tests_b904")


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
