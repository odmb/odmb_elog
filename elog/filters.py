import django_filters
from .models import BoardType, Board, Location, Log, BoardStatus, Tests
from django.db.models import Q
from django.forms.widgets import TextInput
import re

class BoardFilter(django_filters.FilterSet):
  ntests = 0
  for db_field in Tests._meta.get_fields():
    if re.search('summary(?!_)',db_field.name): ntests += 1
    
  test_ucsb_query = django_filters.CharFilter(method='test_search_ucsb', label="Tests at UCSB (AND)", widget=TextInput(attrs={'placeholder': ''.join(['*'] * ntests)}))
  test_ucsb_or_query = django_filters.CharFilter(method='test_search_ucsb_or', label="Tests at UCSB (OR)", widget=TextInput(attrs={'placeholder': ''.join(['*'] * ntests)}))
  test_b904_query = django_filters.CharFilter(method='test_search_b904', label="Tests at B904 (AND)", widget=TextInput(attrs={'placeholder': ''.join(['*'] * ntests)}))
  test_b904_or_query = django_filters.CharFilter(method='test_search_b904_or', label="Tests at B904 (OR)", widget=TextInput(attrs={'placeholder': ''.join(['*'] * ntests)}))
  
  
  class Meta:
    model = Board
    fields = ['board_id', 'board_type', 'location', 'terragreen']
  def _summary_field_names(self):
    names = []
    for db_field in Tests._meta.get_fields():
        if not hasattr(db_field, "attname"):
            continue
        if re.search(r"summary(?!_)", db_field.name):
            names.append(db_field.name)
    return names

  def _board_summary_for_location(self, board, location_id):
    if board.tests is None:
        return ""

    logs = list(board.log_set.filter(location_id=location_id).select_related("tests").order_by("-pk"))

    summary = ""
    for field_name in self._summary_field_names():
        char = "-"
        for log in logs:
            if log.tests is None:
                continue
            v = getattr(log.tests, field_name, None)
            if v in (0, 1):
                char = str(v)
                break
        summary += char
    return summary

  def _matches_pattern(self, summary, pattern, use_or=False):
    matched_any = False
    has_condition = False
    for i, char in enumerate(pattern):
        if i >= len(summary):
            break
        if char == '*':
            continue
        has_condition = True
        ok = (summary[i] == char)
        if use_or:
            if ok:
                matched_any = True
        else:
            if not ok:
                return False

    if use_or:
        return matched_any if has_condition else True
    return True

  def _filter_by_location_pattern(self, queryset, value, location_id, use_or=False):
    matched_ids = []
    for board in queryset:
        summary = self._board_summary_for_location(board, location_id)
        if self._matches_pattern(summary, value, use_or=use_or):
            matched_ids.append(board.pk)
    return queryset.filter(pk__in=matched_ids)

  def test_search_ucsb(self, queryset, name, value):
    return self._filter_by_location_pattern(queryset, value, location_id=1, use_or=False)

  def test_search_ucsb_or(self, queryset, name, value):
    return self._filter_by_location_pattern(queryset, value, location_id=1, use_or=True)

  def test_search_b904(self, queryset, name, value):
    return self._filter_by_location_pattern(queryset, value, location_id=5, use_or=False)

  def test_search_b904_or(self, queryset, name, value):
    return self._filter_by_location_pattern(queryset, value, location_id=5, use_or=True)

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
