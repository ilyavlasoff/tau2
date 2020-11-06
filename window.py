from views.ui import Ui_Form
from PyQt5 import QtWidgets, QtCore
from tablemodel import TableModel
from serializer import Serializer
from netplanner import NetPlanner
from PyQt5.QtGui import QIcon, QPixmap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import random as rand
import math
import os
import string
matplotlib.use('Agg')


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
        self.ui.timeReservesTable.setModel(TableModel([], ['Номера событий', 'Полный резерв времени']))
        self.ui.timeReservesTable.resizeColumnsToContents()
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
        except OSError:
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
        except OSError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Произошла ошибка во время открытия файла')

    def draw_plot(self, tasks):
        fig, gnt = plt.subplots()

        y_lim = 100
        x_lim = max([float(t['len']) + float(t['start_time']) for t in tasks])

        gnt.set_ylim(0, y_lim)
        gnt.set_xlim(0, x_lim)

        gnt.set_xlabel('Time')
        gnt.set_ylabel('Tasks')

        gnt.grid(True)

        available_colors = [
            'tab:blue',
            'tab:orange',
            'tab:green',
            'tab:red',
            'tab:purple',
            'tab:brown',
            'tab:pink',
            'tab:gray',
            'tab:olive',
            'tab:cyan',
        ]

        tasks.sort(key=lambda x: (x['start_event'], x['term_event']))

        spacing = math.floor(y_lim / len(tasks))
        position = [(spacing * int(i/spacing), spacing - 2) for i in range(y_lim) if i % spacing == 0]
        y_ticks = [(int(i/spacing) + 0.5) * spacing - 1 for i in range(y_lim - 1) if i % spacing == 0]

        x_step = int(x_lim / 10) if int(x_lim / 10) >= 3 else 1
        x_ticks = [i for i in range(math.ceil(x_lim)) if i % x_step == 0]

        gnt.set_yticks(y_ticks)
        gnt.set_xticks(x_ticks)

        y_labels = []
        for i in range(len(tasks)):
            gnt.broken_barh([(tasks[i]['start_time'], tasks[i]['len'])], position[i],
                            facecolors=(rand.choice(available_colors)))
            y_labels.append('%s-%s' % (str(tasks[i]['start_event']), str(tasks[i]['term_event'])))
        gnt.set_yticklabels(y_labels)

        filename = './plots/' + ''.join([rand.choice(string.ascii_lowercase) for i in range(10)]) + '.png'
        if not os.path.exists(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))
        plt.savefig(filename)
        return filename

    def calculate_indicators(self):
        if self.previous_calculated_flag:
            resp = QtWidgets.QMessageBox.question(self, 'Очистить вычисления',
                                           'Вычисления, произведенные ранее, будут потеряны. Продолжить?',
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if resp == QtWidgets.QMessageBox.No:
                return
            else:
                self.ui.eventsResultsTable.model().clear()
                self.ui.tasksResultsTable.model().clear()
        try:
            tasks_params = self.ui.tasksParamsTable.model().get_data_matrix()
            events_params = self.ui.eventsParamsTable.model().get_data_matrix()
            possible_params = (tasks_params[:, 4]).T.tolist() if self.ui.mark3SysRadio.isChecked() else None

            start_events = [int(x) for x in tasks_params[:, 0].tolist()]
            term_events = [int(x) for x in tasks_params[:, 1].tolist()]
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Произошла ошибка при считывании параметров.'
                                                           ' Проверьте ошибки и попробуйте заново', QtWidgets.QMessageBox.Close)
            return
        try:
            planner = NetPlanner(self.ui.tasksQuantitySpinBox.value(),
                                 self.ui.eventsQuantitySpinBox.value(),
                                 self.ui.mark3SysRadio.isChecked(),
                                 tasks_params[:, 2].tolist(),
                                 tasks_params[:, 3].tolist(),
                                 start_events,
                                 term_events,
                                 events_params[:, 0].tolist(),
                                 possible_params
                                 )
            tasks_expected, dispersion = planner.calc_t_exp()
            t_cr, t_early, t_task_early_start, t_task_early_end, t_late, \
            t_task_late_start, t_task_late_end, task_full_time_reserve, task_independent_time_reserve, \
            task_private_time_reserve_1, task_private_time_reserve_2 = planner.calc_determ_net_params()
            full_reserves_data = planner.calc_full_path_reserves()
            events_dispersion, probabilities = planner.calc_probabilistic_net_params()
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Произошла ошибка при вычислении результатов',
                                  QtWidgets.QMessageBox.Close)
            return

        try:
            for i in {
                'Tdir': events_params[:, 0].T.tolist(),
                'Tp': t_early,
                'Tп': t_late,
                'Dp': events_dispersion,
                'P(Tp < Td)': probabilities
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

            for i in full_reserves_data:
                self.ui.timeReservesTable.model().add_row([i['events'], i['len']])

            tasks_properties = []
            for i in range(self.ui.tasksQuantitySpinBox.value()):
                tasks_properties.append({'start_event': start_events[i], 'term_event': term_events[i],
                                         'start_time': t_task_early_start[i], 'len': tasks_expected[i]})
            file_diagram = self.draw_plot(tasks_properties)

            pixmap = QPixmap(file_diagram)
            self.ui.imgLabel.setPixmap(pixmap)
            self.ui.imgLabel.resize(pixmap.width(), pixmap.height())
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Произошла ошибка при выводе результатов',
                                  QtWidgets.QMessageBox.Close)
            return

        QtWidgets.QMessageBox.information(self, 'Успешно',
                                          'Расчет успешно произведен. Результаты на вкладках "СОБЫТИЯ" и "РАБОТЫ"')
        self.ui.tab_2.setEnabled(True)
        self.ui.tab_3.setEnabled(True)
        self.ui.tab_4.setEnabled(True)
        self.ui.ganttTab.setEnabled(True)
        self.previous_calculated_flag = True






