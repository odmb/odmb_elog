import django_filters
from .models import BoardType, Board, Location, Log, BoardStatus
from django.db.models import Q
from django.forms.widgets import TextInput

class BoardFilter(django_filters.FilterSet):
  class Meta:
    model = Board
    fields = ['board_id', 'board_type', 'location', 'status']

class LogFilter(django_filters.FilterSet):
  date = django_filters.DateFromToRangeFilter(widget=django_filters.widgets.RangeWidget(attrs={'placeholder': 'YYYY-MM-DD'}))
  board_query = django_filters.CharFilter(method='board_search', label="Board", widget=TextInput(attrs={'placeholder': 'BOARD_TYPE#BOARD_ID'}))
  query = django_filters.CharFilter(method='universal_search', label="Search log")
  class Meta:
    model = Log
    fields = ['board_query', 'location', 'status', 'query', 'date']

  def universal_search(self, queryset, name, value):
    return Log.objects.filter(
        Q(text__icontains=value) 
    )

  def board_search(self, queryset, name, value):
    board_name_split = value.split('#')
    if len(board_name_split) !=2:
      in_board_type = ''
      in_board_id = -1
    else:
      in_board_type = board_name_split[0]
      in_board_id = int(board_name_split[1])
      print(in_board_type, in_board_id)
    return Log.objects.filter(board__board_type__name=in_board_type).filter(board__board_id=in_board_id)
