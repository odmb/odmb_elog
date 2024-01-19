import django_filters
from .models import BoardType, Board, Location, Log, BoardStatus, Tests
from django.db.models import Q
from django.forms.widgets import TextInput
import re

class BoardFilter(django_filters.FilterSet):
  ntests = 0
  for db_field in Tests._meta.get_fields():
    if re.search('summary(?!_)',db_field.name): ntests += 1
  test_query = django_filters.CharFilter(method='test_search', label="Tests (AND)", widget=TextInput(attrs={'placeholder': ''.join(['*']*ntests)}))
  test_or_query = django_filters.CharFilter(method='test_search_or', label="Tests (OR)", widget=TextInput(attrs={'placeholder': ''.join(['*']*ntests)}))
  class Meta:
    model = Board
    fields = ['board_id', 'board_type', 'location', 'status']
  def test_search(self, queryset, name, value):
    summary_list = []
    # Search for all summary in test
    for db_field in Tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): summary_list.append(db_field.name)
    #print(summary_list)
    query = Q()
    for ichar, char in enumerate(value):
      if ichar >= len(summary_list): continue
      summary_name = summary_list[ichar]
      if char == '*': continue
      if char == '-':
        if query == Q(): query = Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
        else: query = query & (Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1}))
      else:
        if query == Q(): query = Q(**{f'tests__{summary_name}':char})
        else: query = query & Q(**{f'tests__{summary_name}':char})
    return queryset.filter(query)
  def test_search_or(self, queryset, name, value):
    summary_list = []
    # Search for all summary in test
    for db_field in Tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): summary_list.append(db_field.name)
    #print(summary_list)
    query = Q()
    for ichar, char in enumerate(value):
      if ichar >= len(summary_list): continue
      summary_name = summary_list[ichar]
      #print('char',char)
      if char == '*': continue
      if char == '-':
        if query == Q(): query = Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
        else: query = query | Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
      else:
        if query == Q(): query = Q(**{f'tests__{summary_name}':char})
        else: query = query | Q(**{f'tests__{summary_name}':char})
    #print('query',query)
    #print(queryset)
    #print(Board.objects.filter(query))
    #if query == None: Board.objects.filter(**{})
    #else: return Board.objects.filter(query)
    return queryset.filter(query)

class LogFilter(django_filters.FilterSet):
  date = django_filters.DateFromToRangeFilter(widget=django_filters.widgets.RangeWidget(attrs={'placeholder': 'YYYY-MM-DD'}))
  board_query = django_filters.CharFilter(method='board_search', label="Board", widget=TextInput(attrs={'placeholder': 'BOARD_TYPE#BOARD_ID'}))
  query = django_filters.CharFilter(method='universal_search', label="Search log")
  ntests = 0
  for db_field in Tests._meta.get_fields():
    if re.search('summary(?!_)',db_field.name): ntests += 1
  test_query = django_filters.CharFilter(method='test_search', label="Tests (AND)", widget=TextInput(attrs={'placeholder': ''.join(['*']*ntests)}))
  test_or_query = django_filters.CharFilter(method='test_search_or', label="Tests (OR)", widget=TextInput(attrs={'placeholder': ''.join(['*']*ntests)}))
  class Meta:
    model = Log
    fields = ['board_query', 'location', 'status', 'query', 'date']

  def universal_search(self, queryset, name, value):
    #return Log.objects.filter(
    #    Q(text__icontains=value) 
    #)
    return queryset.filter(
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
    #return Log.objects.filter(board__board_type__name=in_board_type).filter(board__board_id=in_board_id)
    return queryset.filter(board__board_type__name=in_board_type).filter(board__board_id=in_board_id)

  def test_search(self, queryset, name, value):
    summary_list = []
    # Search for all summary in test
    for db_field in Tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): summary_list.append(db_field.name)
    #print(summary_list)
    query = Q()
    for ichar, char in enumerate(value):
      if ichar >= len(summary_list): continue
      summary_name = summary_list[ichar]
      if char == '*': continue
      if char == '-':
        if query == Q(): query = Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
        else: query = query & (Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1}))
      else:
        if query == Q(): query = Q(**{f'tests__{summary_name}':char})
        else: query = query & Q(**{f'tests__{summary_name}':char})
    return queryset.filter(query)

  def test_search_or(self, queryset, name, value):
    summary_list = []
    # Search for all summary in test
    for db_field in Tests._meta.get_fields():
      if re.search('summary(?!_)',db_field.name): summary_list.append(db_field.name)
    #print(summary_list)
    query = Q()
    for ichar, char in enumerate(value):
      if ichar >= len(summary_list): continue
      summary_name = summary_list[ichar]
      if char == '*': continue
      if char == '-':
        if query == Q(): query = Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
        else: query = query | Q(**{f'tests__{summary_name}':None})|Q(**{f'tests__{summary_name}':-1})
      else:
        if query == Q(): query = Q(**{f'tests__{summary_name}':char})
        else: query = query | Q(**{f'tests__{summary_name}':char})
    return queryset.filter(query)
