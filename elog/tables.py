import django_tables2 as tables
from django_tables2.utils import A 
from .models import Board, Log
from django.utils.html import format_html

class BoardTable(tables.Table):
  #board_id = tables.Column(linkify=True)
  def render_board_id(self, value, record):
    return format_html("<a href={}> #{} </a>", record.get_absolute_url(), value)
  class Meta:
    model = Board
    template_name = "django_tables2/bootstrap.html"
    fields = ("board_type", "board_id", "location", "status")


from django.urls import reverse
class LogTable(tables.Table):
  edit = tables.Column(empty_values=(), orderable=False)
  delete = tables.Column(empty_values=(), orderable=False)
  date = tables.DateTimeColumn(format = 'Y-m-d, h:i A')
  def render_id(self, value, record):
    return format_html("<a href={}> #{} </a>", record.get_absolute_url(), value)
  def render_edit(self, record):
    return format_html("<a href={}> Edit </a>", reverse('log-update', args=[str(record.id)]))
  def render_delete(self, record):
    return format_html("<a href={}> Delete </a>", reverse('log-delete', args=[str(record.id)]))
  def render_board(self, value, record):
    return format_html("<a href={}> {} </a>", record.board.get_absolute_url(), value)
  class Meta:
    model = Log
    template_name = "django_tables2/bootstrap.html"
    fields = ("id", "board", "date", "text", "location", "edit", "delete")
