from .models import Board, Log


SITE_CONFIG = {
  'ucsb': {'location_id': 1, 'status_field': 'ucsb_test_status', 'auto_field': 'ucsb_status_auto_update'},
  'b904': {'location_id': 5, 'status_field': 'b904_test_status', 'auto_field': 'b904_status_auto_update'},
}

TEST_SUMMARY_FIELDS = (
  'picture_summary', 'r_summary', 'a_summary', 'led_summary',
  'eeprom_summary', 'jitter_summary', 'vme_summary', 'fpgaclk_summary',
  'sysmon_summary', 'prom_summary', 'ccb_summary', 'otmb_summary',
  'lvmb_summary', 'dcfebjtag_summary', 'dcfebfastsignal_summary',
  'opticalprbs_summary', 'medterm_summary', 'hist_summary', 'dlfix_summary',
)


def calculate_test_status(board, site):
  config = SITE_CONFIG[site]
  required_fields = TEST_SUMMARY_FIELDS[:17] if site == 'ucsb' else TEST_SUMMARY_FIELDS
  logs = list(
    Log.objects.filter(board=board, location_id=config['location_id'], tests__isnull=False)
    .select_related('tests').order_by('-pk')
  )
  results = []
  for test_field in required_fields:
    result = None
    for log in logs:
      value = getattr(log.tests, test_field, None)
      if value in (0, 1):
        result = value
        break
    results.append(result)

  current_status = getattr(board, config['status_field'])
  if 0 in results:
    if current_status == Board.TestStatus.UNDER_REPAIRING:
      return Board.TestStatus.UNDER_REPAIRING
    return Board.TestStatus.UNDER_DEBUGGING
  if None in results:
    return Board.TestStatus.NOT_FULLY_TESTED
  return Board.TestStatus.FULLY_TESTED


def update_board_test_status(board, site):
  config = SITE_CONFIG[site]
  if not getattr(board, config['auto_field']):
    return False
  new_status = calculate_test_status(board, site)
  status_field = config['status_field']
  if getattr(board, status_field) == new_status:
    return False
  Board.objects.filter(pk=board.pk).update(**{status_field: new_status})
  setattr(board, status_field, new_status)
  return True


def update_all_board_test_statuses(board):
  for site in SITE_CONFIG:
    update_board_test_status(board, site)


def initialize_existing_board_test_statuses():
  for board in Board.objects.all().iterator():
    update_all_board_test_statuses(board)
