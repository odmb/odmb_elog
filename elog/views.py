from django.shortcuts import render
from django.views import generic
from .models import BoardType, Board, Location, TerraGreen, Log, BoardStatus, Tests
import re

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
    #print(filterset)
    return filterset


class BoardListView(FilteredSingleTableView):
  template_name = "elog/board_list.html"
  model = Board
  paginate_by = 25
  filterset_class = BoardFilter
  formhelper_class = BoardFilterFormHelper
  table_class = BoardTable
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    #print('table context', context)
    return context

class BoardDetailView(generic.DetailView):
  model = Board
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    testfilterbase = TestFilterForm()
    testforms_view = []
    for testform_name in testfilterbase.testforms_dict:
      form = testfilterbase.testforms_dict[testform_name]()
      # Fill form if field is in object.tests
      if self.object.tests == None: continue
      filled_field_names = []
      for field_name in form.fields:
        for db_field in self.object.tests._meta.get_fields():
          if field_name == db_field.name:
            form.fields[field_name].initial = db_field.value_from_object(self.object.tests)
            filled_field_names.append(field_name)
            break
      # Fill log_url using summary_log_id in form
      log_url = ''
      for field_name in filled_field_names:
        test_basename = field_name.split('_')[0]
        log_id_name = f'{test_basename}_summary_log_id'
        log_id = self.object.tests.__dict__[log_id_name]
        log_url_name = f'{test_basename}_logurl'
        #print(log_id_name, log_url, log_id)
        if log_id != None:
          form.fields[log_url_name].initial = reverse_lazy('log-detail', kwargs={'pk': log_id})
      testforms_view.append(form)
    # Fill filter form
    context['testforms'] = testforms_view
    context['board_logs'] = context['board'].log_set.all().order_by('-pk')
    context['readonly'] = True
    ## Show test_summary_log_id
    return context

#class LogListView(generic.ListView):
#  model = Log
class LogListView(FilteredSingleTableView):
  template_name = "elog/log_list.html"
  model = Log
  table_class = LogTable
  paginate_by = 25
  filterset_class = LogFilter
  formhelper_class = LogFilterFormHelper
  ordering = ['-id']

class LogDetailView(generic.DetailView):
  model = Log

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    testfilterbase = TestFilterForm()
    testforms_view = []
    for testform_name in testfilterbase.testforms_dict:
      form = testfilterbase.testforms_dict[testform_name]()
      # Fill form if field is in object.tests
      if self.object.tests == None: continue
      for field_name in form.fields:
        #print(self.object.tests._meta.get_fields())
        #print(testform_name, field_name)
        for db_field in self.object.tests._meta.get_fields():
          if field_name == db_field.name:
            #print(db_field.value_from_object(self.object.tests))
            form.fields[field_name].initial = db_field.value_from_object(self.object.tests)
            break
      #if testform_name == 'short circuit':
      #  #print(dir(form.fields['r_point1']))
      #  form.fields['r_point1'].initial = self.object.tests.r_point1
      testforms_view.append(form)
    #testform = testfilterbase.testforms_dict['short circuit'](initial={'r_point1':self.object.tests.r_point1})
    #testforms_view.append(testform)
    # Fill filter form
    context['testforms'] = testforms_view
    context['readonly'] = True
    return context


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


class LogDelete(DeleteView):
  model = Log
  success_url = reverse_lazy('logs')

class BoardCreate(CreateView):
  model = Board
  fields = ['board_id', 'board_type', 'location', 'terragreen']
  def form_valid(self, form):
    self.object = form.save()
    return HttpResponseRedirect(self.get_success_url())

class BoardDelete(DeleteView):
  model = Board
  success_url = reverse_lazy('boards')

testform_display_names = {
    "VisualInspectionsForm": "Visual inspection",
    "ShortCircuitForm": "Short circuit test",
    "PowerForm": "Power test",
    "ClockConfigurationForm": "Clock configuration",
    "EEPROMConfigurationForm": "EEPROM configuration",
    "JitterAnalysisForm": "Jitter analysis",
    "VMEBasicTestForm": "Basic VME Test",
    "FPGAClockTestForm": "FPGA clock test",
    "SysmonTestForm": "System monitoring test",
    "PROMTestForm": "PROM test",
    "CCBTestForm": "CCB test",
    "OTMBTestForm": "OTMB test",
    "LVMBTestForm": "LVMB/LVMB7 test",
    "DCFEBJTAGTestForm": "DCFEB JTAG test",
    "DCFEBFastSignalTestForm": "DCFEB fast signal test",
    "OpticalPRBSTestForm": "Optical PRBS test",
    "MedtermTestForm": "Med-term board-to-board IBERT test",
    "Step27Form": "Step 27 test"
}


# Make a view for update boardtest
from .forms import BoardTestForm, TestFilterForm
def get_boardtest(request, *args, **kwargs):
  # Setup filter
  testforms_view = []
  testfilterbase = TestFilterForm()
  readonly = False

  if request.method == 'POST':
    # Fill form
    form = BoardTestForm(request.POST, request.FILES, prefix='boardtest')
    testfilter = TestFilterForm(request.POST, prefix='testfilter')
    # Fill filter form
    #print('testfilter.is_valid',testfilter.is_valid())
    if testfilter.is_valid():
      if testfilter.cleaned_data.get('deselect'):
        testfilter = TestFilterForm(prefix='testfilter')
        testforms_view.clear()
      else:
        for testform_name in testfilterbase.testforms_dict:
          if testfilter.cleaned_data.get(testform_name): testforms_view.append(testfilterbase.testforms_dict[testform_name](request.POST, request.FILES, prefix=testform_name))



    #print('(0)testforms_view: ',testforms_view)
    # Check if form is valid
    forms_valid = True
    for testform in testforms_view:
      if not testform.is_valid(): 
        forms_valid = False
    # Action after successful submit
    if 'submit_test' in request.POST:
      popup_errors = []
      for testform in testforms_view:
        errors = testform.non_field_errors()
        if errors:
          class_name = testform.__class__.__name__
          friendly_name = testform_display_names[class_name]
          for error in errors:
            popup_errors.append(f'{error} for {friendly_name}')

      if popup_errors or not form.is_valid() or not forms_valid:
          return render(request, 'board_tests/boardtest.html', {'form':form, 'testforms': testforms_view, 'testfilter':testfilter, 'readonly': readonly, 'popup_errors': popup_errors})
      print('cleaned form',form.cleaned_data)
      for itestform, testform in enumerate(testforms_view):
        print(f'cleaned testform {itestform}',testform.cleaned_data)
      board_obj = form.cleaned_data['board']
      date_obj = form.cleaned_data['date']
      location_obj = form.cleaned_data['location']
      text_obj = form.cleaned_data['text']
      # Fill form data
      form_data = {}
      #print('(1)testforms_view: ',testforms_view)
      for testform in testforms_view:
        #form_data.update(testform.cleaned_data)
        #print('testforms.cleaned_data: ',testform.cleaned_data)
        for testform_field in testform.cleaned_data:
          if 'logurl' in testform_field: continue
          form_data[testform_field] = testform.cleaned_data[testform_field]
        #form_data.update(testform.cleaned_data)
      #tests_obj = Tests(**{'r_point1':testforms_view[0].cleaned_data['r_point1'], 'r_summary':True})
      # Create objects in db
      #print('test_form: ',form_data)
      tests_obj = Tests(**form_data)
      tests_obj.save()
      log_obj = Log(board=board_obj, date=date_obj, location=location_obj, tests=tests_obj, text=text_obj)
      log_obj.save()
      # Update objects in db
      board_obj.location_log_id = log_obj.id
      board_obj.location = location_obj
      board_obj.save()
      #print(board_obj.pk)
      #print('pre',tests_obj.r_summary_log_id)
      # Update tests summary_log_id that have been modified.
      test_summary_dict = {}
      for obj_field in tests_obj._meta.get_fields():
        if re.search('summary(?!_)',obj_field.name):
          obj_value = obj_field.value_from_object(tests_obj)
          #print(obj_field, repr(obj_value))
          if obj_value in (0, 1):
            test_summary_dict[f'{obj_field.name}_log_id'] = log_obj.id
      #print(test_summary_dict)
      tests_obj.__dict__.update(test_summary_dict)
      tests_obj.save()
      #print('post',tests_obj.r_summary_log_id)
      # Update board.tests that have summary modified. Check if log_id is most recent.
      modified_test_basenames = [summary_field.split('_summary')[0] for summary_field in test_summary_dict]
      #print(modified_test_basenames)
      is_board_obj_modified = False
      for test_field in tests_obj._meta.get_fields():
        if len(test_field.name.split('_')) == 1: continue # Ignore fields that are not tests
        test_basename = test_field.name.split('_')[0]
        if test_basename not in modified_test_basenames: continue # Ignore fields that have not been modified
        #print(test_basename)
        # Check if board.tests exists
        print('check if board_obj.tests exist',board_obj.tests)
        if board_obj.tests == None:
          print('Filling in new test for board')
          board_tests_obj = Tests(**form_data)
          board_tests_obj.__dict__.update(test_summary_dict)
          board_tests_obj.save()
          board_obj.tests = board_tests_obj
          board_obj.save()
          break
        else:
          #print('board_obj.tests', board_obj.tests.id)
          # Check if board test summary log id is older
          #print(f'{test_basename}_summary_log_id', board_obj.tests.__dict__[f'{test_basename}_summary_log_id'])
          board_log_id = -1 if board_obj.tests.__dict__[f'{test_basename}_summary_log_id']==None else int(board_obj.tests.__dict__[f'{test_basename}_summary_log_id']==None)
          log_id = int(tests_obj.__dict__[f'{test_basename}_summary_log_id'])
          #print('board.test log id',board_log_id,'log.test log id',log_id)
          if log_id >= board_log_id:
            #print(f'Updating {test_field.name} from {board_obj.tests.__dict__[test_field.name]} to {tests_obj.__dict__[test_field.name]}')
            board_obj.tests.__dict__[test_field.name] = tests_obj.__dict__[test_field.name]
            is_board_obj_modified = True
      if is_board_obj_modified: 
        print('Trying to save board obj')
        board_obj.tests.save()
      #Board.objects.filter(pk=board_obj.pk).update()

      #print(form.cleaned_data['picture'].image)
      #return HttpResponseRedirect(reverse_lazy('index'))
      # If most recent, update board db
      return HttpResponseRedirect(reverse_lazy('logs'))
  else:
    # Fill form
    form = BoardTestForm(prefix='boardtest')
    testfilter = TestFilterForm(prefix='testfilter', initial=testfilterbase.initial_dict)
    for testform_name in testfilterbase.testforms_dict:
      if testform_name in testfilterbase.initial_dict:
        testforms_view.append(testfilterbase.testforms_dict[testform_name](prefix=testform_name))
  return render(request, 'board_tests/boardtest.html', {'form':form, 'testforms': testforms_view, 'testfilter':testfilter, 'readonly': readonly})

def update_boardtest(request, *args, **kwargs):
  # Setup filter
  testforms_view = []
  testfilterbase = TestFilterForm()
  log_id = kwargs['pk']
  log_obj = Log.objects.get(pk=log_id)
  test_id = log_obj.tests.id
  readonly = False

  if request.method == 'POST':
    # Fill form
    form = BoardTestForm(request.POST, request.FILES, instance=log_obj, prefix='boardtest')
    testfilter = TestFilterForm(request.POST, prefix='testfilter')
    # Fill filter form
    if testfilter.is_valid():
      if testfilter.cleaned_data.get('deselect'):
        testfilter = TestFilterForm(prefix='testfilter')
        testforms_view.clear()
      else:
        for testform_name in testfilterbase.testforms_dict:
          if testfilter.cleaned_data.get(testform_name):
            testforms_view.append(testfilterbase.testforms_dict[testform_name](request.POST,request.FILES,prefix=testform_name))
    
    # Check if form is valid
    forms_valid = True
    for testform in testforms_view:
      if not testform.is_valid(): 
        forms_valid = False
      #print('was it inserted?',testform.cleaned_data)
    # Action after successful submit
          
    if 'submit_test' in request.POST:
        popup_errors = []
        for testform in testforms_view:
            errors = testform.non_field_errors()
            if errors:
                class_name = testform.__class__.__name__
                friendly_name = testform_display_names[class_name]
                for error in errors:
                    popup_errors.append(f'{error} for {friendly_name}')
     
        if popup_errors or not form.is_valid() or not forms_valid:
            return render(request, 'board_tests/boardtest.html', {'form':form, 'testforms': testforms_view, 'testfilter':testfilter, 'readonly': readonly, 'popup_errors': popup_errors})
        board_obj = form.cleaned_data['board']
        date_obj = form.cleaned_data['date']
        location_obj = form.cleaned_data['location']
        text_obj = form.cleaned_data['text']
        # Fill form data
        form_data = {}
        for testform in testforms_view:
            #print('to fill',testform.cleaned_data)
            #form_data.update(testform.cleaned_data)
            for testform_field in testform.cleaned_data:
                if 'logurl' in testform_field: continue
                form_data[testform_field] = testform.cleaned_data[testform_field]
        #tests_obj = Tests(**{'r_point1':testforms_view[0].cleaned_data['r_point1'], 'r_summary':True})
        #print('to_fill',form_data)

        tests_obj = Tests.objects.get(pk=test_id)
        for testform in testforms_view:
            for key, value in testform.cleaned_data.items():
                full_name = f"{testform.prefix}-{key}"
                field = testform.fields[key]
                if isinstance(field, forms.ImageField):
                    if full_name not in request.FILES:
                        continue
                if full_name not in request.POST and full_name not in request.FILES:
                    continue
                setattr(tests_obj, key, value)

        tests_obj.save()
        #print(Tests.objects.get(pk=test_id).r_summary)
        log_obj.board = board_obj
        log_obj.date = date_obj
        log_obj.location = location_obj
        log_obj.text = text_obj
        log_obj.save()
        #Log.objects.filter(pk=log_id).update(board=board_obj, date=date_obj, location=location_obj, text=text_obj)
        #log_obj = Log(board=board_obj, date=date_obj, location=location_obj, tests=tests_obj, text=text_obj)
        #log_obj.save()

        #print(form.cleaned_data['picture'].image)
        #return HttpResponseRedirect(reverse_lazy('index'))
        # If most recent, update board db
        #print('location log id',board_obj.location_log_id, 'current log id', log_obj.id)
        if log_obj.id == board_obj.location_log_id:
            board_obj.location = location_obj
            board_obj.save()
        # Update board status if test_log_id == log_obj.id
        modified_test_basenames = []
        for obj_field in board_obj.tests._meta.get_fields():
            if 'summary_log_id' in obj_field.name:
                obj_value = obj_field.value_from_object(board_obj.tests)
                if obj_value != log_obj.id: continue
                print(obj_field.name, obj_value, log_obj.id)
                modified_test_basenames.append(obj_field.name.split('_')[0])
        is_board_obj_modified = False
        for test_field in tests_obj._meta.get_fields():
            if len(test_field.name.split('_')) == 1: continue # Ignore fields that are not tests
            test_basename = test_field.name.split('_')[0]
            if test_basename not in modified_test_basenames: continue # Ignore fields that have not been modified
            print(f'Updating {test_field.name} from {board_obj.tests.__dict__[test_field.name]} to {tests_obj.__dict__[test_field.name]}')
            board_obj.tests.__dict__[test_field.name] = tests_obj.__dict__[test_field.name]
            is_board_obj_modified = True
        if is_board_obj_modified:
            print('Trying to save board obj')
            board_obj.tests.save()

        return HttpResponseRedirect(reverse_lazy('logs'))
  else:
    # Get data from database
    testforms_view = []
    testforms_initial = {}
    for testform_name in testfilterbase.testforms_dict:
      form = testfilterbase.testforms_dict[testform_name](prefix=testform_name)
      for field_name in form.fields:
        for db_field in log_obj.tests._meta.get_fields():
          if field_name == db_field.name:
            form.fields[field_name].initial = db_field.value_from_object(log_obj.tests)
            break
      testforms_view.append(form)
      testforms_initial[testform_name] = True
    boardtest_initial = {'board':log_obj.board, 'date':log_obj.date, 'location':log_obj.location, 'text':log_obj.text}
    # Fill form
    form = BoardTestForm(prefix='boardtest', initial=boardtest_initial)
    testfilter = TestFilterForm(prefix='testfilter', initial=testforms_initial)
  return render(request, 'board_tests/boardtest.html', {'form':form, 'testforms': testforms_view, 'testfilter':testfilter, 'readonly': readonly})
