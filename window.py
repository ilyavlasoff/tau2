from views.ui import Ui_Form
from PyQt5 import QtWidgets
from tablemodel import TableModel
from serializer import Serializer
from netplanner import NetPlanner
import numpy as np


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.saveToFileButton.clicked.connect(lambda: self.save_to_file())
        self.ui.loadFromFileButton.clicked.connect(lambda: self.load_from_file())
        self.ui.tasksQuantitySpinBox.valueChanged.connect(lambda: self.tasks_quantity_changed())
        self.ui.eventsQuantitySpinBox.valueChanged.connect(lambda: self.events_quantity_changed())
        self.ui.tasksParamsTable.verticalHeader().setVisible(True)
        self.ui.eventsParamsTable.verticalHeader().setVisible(True)
        self.ui.mark3SysRadio.toggled.connect(lambda: self.method_changed(self.ui.mark3SysRadio))
        self.ui.startCalcButton.clicked.connect(lambda: self.calculate_indicators())
        self.setup_data()
        self.previous_calculated_flag = False

    def method_changed(self, button):
        if button.isChecked():
            self.ui.tasksParamsTable.model().add_column([], 'Вероятное')
        else:
            self.ui.tasksParamsTable.model().remove_last_column()

    def tasks_quantity_changed(self):
        old_tasks_quantity = self.ui.tasksParamsTable.model().row_count
        new_tasks_quantity = self.ui.tasksQuantitySpinBox.value()
        delta_count = new_tasks_quantity - old_tasks_quantity
        if delta_count > 0:
            self.ui.tasksParamsTable.model().add_rows(delta_count)
        else:
            self.ui.tasksParamsTable.model().remove_last_row(abs(delta_count))

    def events_quantity_changed(self):
        old_events_quantity = self.ui.eventsParamsTable.model().row_count
        new_tasks_quantity = self.ui.eventsQuantitySpinBox.value()
        delta_count = new_tasks_quantity - old_events_quantity
        if (delta_count > 0):
            self.ui.eventsParamsTable.model().add_rows(delta_count)
        else:
            self.ui.eventsParamsTable.model().remove_last_row(abs(delta_count))

    def setup_data(self, event_params_model_data=[], tasks_params_model_data=[],
                   tasks_quantity=0, events_quantity=0, use3mark_system=False):
        events_params_title = ['Нач. событие', 'Кон. событие', 'Оптим.', 'Пессим.']
        if use3mark_system:
            events_params_title.append('Наиб. вероятное')
        self.ui.tasksParamsTable.setModel(TableModel(tasks_params_model_data, events_params_title))
        self.ui.eventsParamsTable.setModel(TableModel(event_params_model_data,
                                                      ['Директ. срок']))
        self.ui.eventsResultsTable.setModel(TableModel([], []))
        self.ui.tasksResultsTable.setModel(TableModel([], []))
        self.ui.tasksQuantitySpinBox.setValue(tasks_quantity)
        self.ui.eventsQuantitySpinBox.setValue(events_quantity)
        if use3mark_system:
            self.ui.mark3SysRadio.setChecked(True)
        else:
            self.ui.mark2SysRadio.setChecked(True)

    def save_to_file(self):
        try:
            save_file_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file...', './')[0]
            save_data = dict()
            save_data['event_params_model_data'] = self.ui.eventsParamsTable.model().get_data_matrix()
            save_data['tasks_params_model_data'] = self.ui.tasksParamsTable.model().get_data_matrix()
            save_data['tasks_quantity'] = self.ui.tasksQuantitySpinBox.value()
            save_data['events_quantity'] = self.ui.eventsQuantitySpinBox.value()
            save_data['use3mark_system'] = True if self.ui.mark3SysRadio.isChecked() else False
            Serializer.serialize(save_file_path, save_data)
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Во время сохранения файла произошла ошибка')

    def load_from_file(self):
        try:
            load_file_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Save file...', './')[0]
            loaded_data = Serializer.deserialize(load_file_path)
            self.setup_data(
                loaded_data['event_params_model_data'],
                loaded_data['tasks_params_model_data'],
                loaded_data['tasks_quantity'],
                loaded_data['events_quantity'],
                loaded_data['use3mark_system']
            )
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Произошла ошибка во время открытия файла')

    def calculate_indicators(self):
        if self.previous_calculated_flag:
            resp = QtWidgets.QMessageBox.question(self, 'Очистить вычисления',
                                           'Вычисления, произведенные ранее, будут потеряны. Продолжить?',
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if resp == QtWidgets.QMessageBox.No:
                return
        tasks_params = self.ui.tasksParamsTable.model().get_data_matrix()
        events_params = self.ui.eventsParamsTable.model().get_data_matrix()
        possible_params = (tasks_params[:, 4]).T.tolist() if self.ui.mark3SysRadio.isChecked() else None

        planner = NetPlanner(self.ui.tasksQuantitySpinBox.value(),
                             self.ui.eventsQuantitySpinBox.value(),
                             self.ui.mark3SysRadio.isChecked(),
                             tasks_params[:, 2].tolist(),
                             tasks_params[:, 3].tolist(),
                             [int(x) for x in tasks_params[:, 0].tolist()],
                             [int(x) for x in tasks_params[:, 1].tolist()],
                             events_params[:, 0].tolist(),
                             possible_params
                             )
        tasks_expected, dispersion = planner.calc_t_exp()
        t_cr, t_early, t_task_early_start, t_task_early_end, t_late, \
        t_task_late_start, t_task_late_end, task_full_time_reserve, task_independent_time_reserve, \
        task_private_time_reserve_1, task_private_time_reserve_2 = planner.calc_determ_net_params()
        full_reserves_data = planner.calc_full_path_reserves()
        planner.calc_probabilistic_net_params()

        for i in {
            'Tdir': events_params[:, 0].T.tolist(),
            'Tp': t_early,
            'Tп': t_late,
        }.items():
            self.ui.eventsResultsTable.model().add_column(i[1], i[0])
        for i in {
            'Tож': tasks_expected,
            'Dож': dispersion,
            'Tрн': t_task_early_start,
            'Tро': t_task_early_end,
            'Tпн': t_task_late_start,
            'Tпо': t_task_late_end,
            'Pполн': task_full_time_reserve,
            'P\'': task_private_time_reserve_1,
            'P\'\'': task_private_time_reserve_2,
            'Pнезав': task_independent_time_reserve
        }.items():
            self.ui.tasksResultsTable.model().add_column(i[1], i[0])
        QtWidgets.QMessageBox.information(self, 'Успешно',
                                          'Расчет успешно произведен. Результаты на вкладках "СОБЫТИЯ" и "РАБОТЫ"')
        self.previous_calculated_flag = True

