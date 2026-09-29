from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlencode

from .forms import AnalysisForm, TestPortionAnalysisForm, ANALYSIS_TEST_CHOICES
from .models import Board, Log


SITE_LOCATION_IDS = {'ucsb': 1, 'b904': 5}
RESULT_VALUES = {1: 'pass', 0: 'fail'}
STATUS_DISPLAY = (
  (Board.TestStatus.FULLY_TESTED, 'Fully tested with no known issues', 'status-fully-tested'),
  (Board.TestStatus.NOT_FULLY_TESTED, 'Not fully tested', 'status-not-fully-tested'),
  (Board.TestStatus.UNDER_DEBUGGING, 'Under debugging', 'status-under-debugging'),
  (Board.TestStatus.UNDER_REPAIRING, 'Under repairing', 'status-under-repairing'),
  (Board.TestStatus.TEST_STAND, 'Test stand', 'status-test-stand'),
)


def _board_list_url(parameters):
  return f"{reverse('boards')}?{urlencode(parameters)}"


def analysis(request):
  requested_chart = request.GET.get('chart')
  summary_data = request.GET if requested_chart == 'summary' or (not requested_chart and 'site' in request.GET) else None
  portion_data = request.GET if requested_chart == 'portion' else None
  form = AnalysisForm(summary_data)
  portion_form = TestPortionAnalysisForm(portion_data, prefix='portion')
  chart_groups = []
  total_boards = 0
  portion_rows = []
  portion_total_boards = 0
  portion_axis_ticks = []

  if form.is_valid():
    status_field = f"{form.cleaned_data['site']}_test_status"
    selected_board_type_ids = [int(value) for value in form.cleaned_data['board_types']]
    grouping = form.cleaned_data['grouping']
    board_type_labels = {int(value): label for value, label in form.fields['board_types'].choices}
    boards = list(
      Board.objects.filter(board_type_id__in=selected_board_type_ids)
      .select_related('board_type', 'location', 'terragreen')
      .order_by('board_type_id', 'board_id')
    )

    counts = {}
    for board in boards:
      if grouping == 'location':
        group_label = str(board.location) if board.location else 'No location'
        group_value = board.location_id if board.location_id is not None else 'none'
      elif grouping == 'terragreen':
        group_label = str(board.terragreen) if board.terragreen else 'No TerraGreen'
        group_value = board.terragreen_id if board.terragreen_id is not None else 'none'
      else:
        group_label = 'All boards'
        group_value = ''
      group_key = (group_label, group_value)
      bar_counts = counts.setdefault(group_key, {}).setdefault(
        board.board_type_id,
        {status: 0 for status, label, css_class in STATUS_DISPLAY},
      )
      board_status = getattr(board, status_field)
      if board_status not in bar_counts:
        board_status = Board.TestStatus.NOT_FULLY_TESTED
      bar_counts[board_status] += 1
      total_boards += 1

    max_count = max(
      (sum(type_counts.values()) for group_counts in counts.values() for type_counts in group_counts.values()),
      default=0,
    )
    for group_key in sorted(counts, key=lambda item: item[0].casefold()):
      group_label, group_value = group_key
      bars = []
      for board_type_id in selected_board_type_ids:
        type_counts = counts[group_key].get(
          board_type_id,
          {status: 0 for status, label, css_class in STATUS_DISPLAY},
        )
        total = sum(type_counts.values())
        bars.append({
          'label': board_type_labels[board_type_id],
          'total': total,
          'height': round((total / max_count) * 100, 2) if max_count else 0,
          'segments': [
            {
              'label': label,
              'css_class': css_class,
              'count': type_counts[status],
              'height': round((type_counts[status] / total) * 100, 2) if total else 0,
              'url': _board_list_url({
                'analysis_status': status,
                'analysis_site': form.cleaned_data['site'],
                'analysis_board_type': board_type_id,
                'analysis_grouping': grouping,
                'analysis_group': group_value,
              }),
            }
            for status, label, css_class in STATUS_DISPLAY
            if type_counts[status]
          ],
        })
      chart_groups.append({'label': group_label, 'bars': bars})

  if portion_form.is_valid():
    site_location_id = SITE_LOCATION_IDS[portion_form.cleaned_data['site']]
    selected_board_type_ids = [int(value) for value in portion_form.cleaned_data['board_types']]
    selected_locations = portion_form.cleaned_data['locations']
    selected_terragreens = portion_form.cleaned_data['terragreens']
    selected_tests = portion_form.cleaned_data['tests']
    display_mode = portion_form.cleaned_data['display_mode']
    test_labels = dict(ANALYSIS_TEST_CHOICES)

    location_ids = [int(value) for value in selected_locations if value != 'none']
    location_query = Q(location_id__in=location_ids)
    if 'none' in selected_locations:
      location_query |= Q(location__isnull=True)
    terragreen_ids = [int(value) for value in selected_terragreens if value != 'none']
    terragreen_query = Q(terragreen_id__in=terragreen_ids)
    if 'none' in selected_terragreens:
      terragreen_query |= Q(terragreen__isnull=True)

    portion_boards = list(
      Board.objects.filter(board_type_id__in=selected_board_type_ids)
      .filter(location_query).filter(terragreen_query)
      .order_by('board_type_id', 'board_id')
    )
    portion_total_boards = len(portion_boards)
    logs_by_board = {}
    logs = (
      Log.objects.filter(
        board_id__in=[board.pk for board in portion_boards],
        location_id=site_location_id,
        tests__isnull=False,
      )
      .select_related('tests').order_by('board_id', '-pk')
    )
    for log in logs:
      logs_by_board.setdefault(log.board_id, []).append(log)

    for test_field in selected_tests:
      counts = {'pass': 0, 'fail': 0, 'not_tested': 0}
      for board in portion_boards:
        result = 'not_tested'
        for log in logs_by_board.get(board.pk, []):
          value = getattr(log.tests, test_field, None)
          if value in RESULT_VALUES:
            result = RESULT_VALUES[value]
            break
        counts[result] += 1
      widths = {
        result: round((count / portion_total_boards) * 100, 2) if portion_total_boards else 0
        for result, count in counts.items()
      }
      values = (
        {result: f'{round(width)}%' for result, width in widths.items()}
        if display_mode == 'percentage'
        else {result: str(count) for result, count in counts.items()}
      )
      urls = {
        result: _board_list_url({
          'analysis_result': result,
          'analysis_site': portion_form.cleaned_data['site'],
          'analysis_test': test_field,
          'analysis_board_types': ','.join(str(value) for value in selected_board_type_ids),
          'analysis_locations': ','.join(selected_locations),
          'analysis_terragreens': ','.join(selected_terragreens),
        })
        for result in counts
      }
      portion_rows.append({
        'label': test_labels[test_field],
        'counts': counts,
        'widths': widths,
        'values': values,
        'urls': urls,
      })

    portion_axis_ticks = (
      ['0%', '25%', '50%', '75%', '100%']
      if display_mode == 'percentage'
      else [str(round(portion_total_boards * fraction / 4)) for fraction in range(5)]
    )

  return render(request, 'elog/analysis.html', {
    'form': form,
    'portion_form': portion_form,
    'chart_groups': chart_groups,
    'status_legend': [
      {'label': label, 'css_class': css_class}
      for status, label, css_class in STATUS_DISPLAY
    ],
    'total_boards': total_boards,
    'portion_rows': portion_rows,
    'portion_total_boards': portion_total_boards,
    'portion_axis_ticks': portion_axis_ticks,
  })
