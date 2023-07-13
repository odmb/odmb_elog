from django.shortcuts import render
from django.views import generic
from .models import BoardType, Board, Location, Log, BoardStatus

# Create your views here.
def index(request):
  num_boards = Board.objects.all().count() 
  num_logs = Log.objects.all().count()
  context = {
    'num_boards': num_boards,
    'num_logs': num_logs
  }
  return render(request, 'index.html', context=context)

#class BoardListView(generic.ListView):
#  model = Board

from django_filters.views import FilterView
from django_tables2 import SingleTableView
from .tables import BoardTable, LogTable
from .filters import BoardFilter, LogFilter
from .forms import * 
import django_tables2 as tables
from django_tables2 import SingleTableMixin


# reference: https://gist.github.com/ckrybus/1c597830ed6d0dead642fd4cb31f3b7e
class FilteredSingleTableView(SingleTableMixin, FilterView):
  formhelper_class = None

  def get_filterset(self, filterset_class):
    kwargs = self.get_filterset_kwargs(filterset_class)
    filterset = filterset_class(**kwargs)
    filterset.form.helper = self.formhelper_class()
    return filterset


class BoardListView(FilteredSingleTableView):
  template_name = "elog/board_list.html"
  model = Board
  table_class = BoardTable
  paginate_by = 25
  filterset_class = BoardFilter
  formhelper_class = BoardFilterFormHelper

class BoardDetailView(generic.DetailView):
  model = Board

#class LogListView(generic.ListView):
#  model = Log
class LogListView(FilteredSingleTableView):
  template_name = "elog/log_list.html"
  model = Log
  table_class = LogTable
  paginate_by = 25
  filterset_class = LogFilter
  formhelper_class = LogFilterFormHelper

class LogDetailView(generic.DetailView):
  model = Log


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import LogForm
from django.http import HttpResponseRedirect

class LogCreate(CreateView):
  model = Log
  #fields = ['id', 'board', 'date', 'location', 'file', 'text', 'status']
  form_class = LogForm
  def form_valid(self, form):
    self.object = form.save()
    self.object.board.location = self.object.location
    self.object.board.save()
    return HttpResponseRedirect(self.get_success_url())

class LogUpdate(UpdateView):
  model = Log
  #fields = ['id', 'board', 'date', 'location', 'file', 'text', 'status']
  form_class = LogForm
  def form_valid(self, form):
    self.object = form.save()
    # Update if most recent log
    board_logs = Log.objects.filter(board=self.object.board).filter(location__isnull=False).order_by('-date')
    if (self.object == board_logs[0]): 
      self.object.board.location = self.object.location
      self.object.board.save()
    return HttpResponseRedirect(self.get_success_url())

class LogDelete(DeleteView):
  model = Log
  success_url = reverse_lazy('logs')
