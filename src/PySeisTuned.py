#!/usr/bin/env python

# This is a simple GUI utility to calculate a seismic tuning wedge
# The base code for this comes from Agile Scientific's Synthetic Tuning Wedge nb
# source: https://github.com/agile-geoscience/xlines/blob/master/notebooks/00_Synthetic_wedge_model.ipynb
# The code to build the wedge model and tuning curves is in wedgebuilder.py

import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QLabel,
    QWidget,
    QPushButton,
    QAction,
    QTabWidget,
    QGridLayout,
    QLineEdit,
    QTextBrowser,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QDialog,
    QFileDialog,
)
from PyQt5.QtGui import QIcon, QValidator, QDoubleValidator
from PyQt5.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import wedgebuilder as wb


class PySeisTuned(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "PySeisTuned"
        self.left = 0
        self.top = 0
        self.width = 900
        self.height = 740

        self.table_widget = tabbedWindow(self)
        self.setCentralWidget(self.table_widget)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # initialize the menu bar
        mainMenu = self.menuBar()

        # add a File menu to the Main menu
        fileMenu = mainMenu.addMenu("File")

        """# add a 'Settings' menu under File menu
		settingsButton = QAction('Settings', self)
		settingsButton.setStatusTip('Adjust settings (color bars, wiggle plots, etc.)')
		settingsButton.triggered.connect(self.settingsMenu)
		fileMenu.addAction(settingsButton)
		"""

        """# add 'Export' option under File menu
		self.exportButton = QAction('Export', self)
		self.exportButton.setStatusTip('Export plots')
		self.exportButton.triggered.connect(self.exportMenu)
		fileMenu.addAction(self.exportButton)
		"""
        # add 'Exit' button under File menu
        exitButton = QAction(QIcon("exit24.png"), "Exit", self)
        exitButton.setShortcut("Ctrl+Q")
        exitButton.setStatusTip("Exit PySeisTuned")
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        # add an About menu to the Main menu
        aboutMenu = mainMenu.addMenu("About")

        # add an About option under About menu
        aboutButton = QAction("About", self)
        aboutButton.setStatusTip("About this program")
        aboutButton.triggered.connect(self.aboutMenuPopUp)
        aboutMenu.addAction(aboutButton)

        """# add a Help menu to the main men
		helpMenu = mainMenu.addMenu('Help')

		# add a button for help on the program
		progHelp = QAction('Program', self)
		progHelp.setStatusTip('Program help')
		helpMenu.addAction(progHelp)
		"""

        """# add a button for help on theory & references
		theoryHelp = QAction('Theory and References', self)
		theoryHelp.setStatusTip('Get background information on seismic tuning')
		helpMenu.addAction(theoryHelp)
		"""

        self.show()

    def settingsMenu(self):
        """
		1) Adjust color bar settings
		2) Change units for velocity & distance (English vs. Metric)
		3) Change tuning wedge plot from interpolated density to wiggle plot
		4) Correct Ricker wavelet for apparent frequency
		"""
        self.settingsWindow = QDialog()
        self.settingsWindow.setWindowTitle("Settings")
        self.settingsWindow.exec_()

    """
	def exportMenu(self):
		
		#Allow export of figures as images
		
		self.exportWindow = QDialog()
		self.exportWindow.setWindowTitle('Export')
		self.layout = QGridLayout(self)
		self.exportWindowButton = QPushButton('Export', self)
		def clickExport():
			self.rickerBox.figure.savefig('test.png', dpi=100*10)
		self.exportWindowButton.clicked.connect(lambda: clickExport())
		grid = QGridLayout()
		grid.addWidget(self.exportWindowButton,1,0)
		self.exportWindow.setLayout(grid)
		self.exportWindow.exec_()
	"""

    def aboutMenuPopUp(self):
        Message = """<b>PySeisTuned v1.0\n</b>This program uses Python 3.6 & PyQt5 for interactive Seismic Tuning Wedge modeling.  The calculations are executed in a python module called wedgebuilder.  The wedge model design is inspired by Agile Scientific's X-lines of code notebooks."""
        QMessageBox.about(self, "About", Message)


class tabbedWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QGridLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(900, 740)

        # Add tabs
        self.tabs.addTab(self.tab1, "Inputs")
        self.tabs.addTab(self.tab2, "Summary")

        # Create the first tab

        # initialize buttons for reseting the input boxes and submitting the
        # input values for calculating the tuning wedge
        self.resetButton = QPushButton("Reset", self)
        self.calculateButton = QPushButton("Calculate", self)
        self.exportButton = QPushButton("Export", self)

        # initialize the labels and input boxes
        inputsLabel = QLabel("<b>Rock Property Inputs:</b>")
        vpLabel = QLabel("Vp (m/s)")
        rhobLabel = QLabel("Rhob (kg/m3)")
        layer1label = QLabel("Layer 1:")
        self.layer1vp = QLineEdit()
        self.layer1rhob = QLineEdit()
        layer2label = QLabel("Layer 2:")
        self.layer2vp = QLineEdit()
        self.layer2rhob = QLineEdit()
        layer3label = QLabel("Layer 3:")
        self.layer3vp = QLineEdit()
        self.layer3rhob = QLineEdit()
        waveletLabel = QLabel("<b>Ricker Wavelet Design:</b>")
        freqLabel = QLabel("Frequency (Hz):")
        self.freqbox = QLineEdit()
        lenLabel = QLabel("Length (s):")
        self.lenbox = QLineEdit()
        sampLabel = QLabel("dt (s):")
        self.sampbox = QLineEdit()

        # initialize the canvases for plotting
        rickerLabel = QLabel("<b>Ricker Wavelet</b>")
        self.rickerBox = PlotCanvas(self, width=3, height=1)
        self._update_ricker_ax = self.rickerBox.figure.subplots()
        modelBoxLabel = QLabel("<b>Tuning Wedge</b>")
        self.modelBox = PlotCanvas(self, width=5, height=4)
        (
            self._update_earthmodel_ax,
            self._update_wedge_ax,
        ) = self.modelBox.figure.subplots(2, sharex=True, sharey=True)
        self.modelBox.figure.subplots_adjust(hspace=0)
        ampPlotBoxLabel = QLabel("<b>Tuning Curve</b>")
        self.ampPlotBox = PlotCanvas(self, width=5, height=1)
        self._update_amp_ax = self.ampPlotBox.figure.subplots()
        self._update_amp_ax2 = self._update_amp_ax.twinx()

        # initialize spacers to help with layout
        vspacerSG1 = QSpacerItem(QSizePolicy.Minimum, QSizePolicy.Expanding)
        vspacerSG2 = QSpacerItem(QSizePolicy.Minimum, QSizePolicy.Expanding)
        vspacerBottom = QSpacerItem(QSizePolicy.Minimum, QSizePolicy.Expanding)

        # define a subGrid for the input fields
        subGrid = QGridLayout()
        subGrid.setSpacing(5)
        subGrid.addWidget(vpLabel, 0, 1)
        subGrid.addWidget(rhobLabel, 0, 2)
        subGrid.addWidget(layer1label, 1, 0)
        subGrid.addWidget(self.layer1vp, 1, 1)
        subGrid.addWidget(self.layer1rhob, 1, 2)
        subGrid.addWidget(layer2label, 2, 0)
        subGrid.addWidget(self.layer2vp, 2, 1)
        subGrid.addWidget(self.layer2rhob, 2, 2)
        subGrid.addWidget(layer3label, 3, 0)
        subGrid.addWidget(self.layer3vp, 3, 1)
        subGrid.addWidget(self.layer3rhob, 3, 2)
        subGrid.addItem(vspacerSG1, 4, 0, 3)
        subGrid.addWidget(waveletLabel, 5, 0)
        subGrid.addWidget(freqLabel, 6, 0)
        subGrid.addWidget(self.freqbox, 6, 1)
        subGrid.addWidget(lenLabel, 7, 0)
        subGrid.addWidget(self.lenbox, 7, 1)
        subGrid.addWidget(sampLabel, 8, 0)
        subGrid.addWidget(self.sampbox, 8, 1)
        subGrid.addItem(vspacerSG2, 9, 0, 3)
        subGrid.addWidget(self.resetButton, 10, 1)
        subGrid.addWidget(self.calculateButton, 10, 2)
        subGrid.addWidget(self.exportButton, 11, 2)

        # attach the widgets to the main grid layout
        mainGrid = QGridLayout()
        mainGrid.setSpacing(5)
        mainGrid.addWidget(inputsLabel, 0, 0)
        mainGrid.addWidget(modelBoxLabel, 0, 1)
        mainGrid.addLayout(subGrid, 1, 0)
        mainGrid.addWidget(self.modelBox, 1, 1)
        mainGrid.addWidget(rickerLabel, 2, 0)
        mainGrid.addWidget(ampPlotBoxLabel, 2, 1)
        mainGrid.addWidget(self.rickerBox, 3, 0)
        mainGrid.addWidget(self.ampPlotBox, 3, 1)
        mainGrid.addItem(vspacerBottom, 5, 0, 3)

        self.tab1.setLayout(mainGrid)

        # Create the second tab

        resultsLabel = QLabel("Detailed Wedge Model Results:")
        self.resultsBox = QTextBrowser()
        # self.resultsBox.setText(wb.results_summary())
        blankLabel = QLabel("\n")
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(resultsLabel, 1, 0)
        grid.addWidget(self.resultsBox, 2, 0)
        grid.addWidget(blankLabel, 3, 0)
        self.tab2.setLayout(grid)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # initialize default values for all input boxes across both tabs
        self.calculateState = 0
        self.set_defaultValues()

        # initialize validators for QLineEdit input boxes
        self.validatorList = []
        self.layer1vp.setValidator(QDoubleValidator(1000.00, 50000.00, 2))
        self.layer1vp.textChanged.connect(self.check_state)
        self.layer1vp.textChanged.emit(self.layer1vp.text())
        self.layer1rhob.setValidator(QDoubleValidator(1500, 3000, 0))
        self.layer1rhob.textChanged.connect(self.check_state)
        self.layer1rhob.textChanged.emit(self.layer1rhob.text())
        self.layer2vp.setValidator(QDoubleValidator(1000.00, 50000.00, 2))
        self.layer2vp.textChanged.connect(self.check_state)
        self.layer2vp.textChanged.emit(self.layer2vp.text())
        self.layer2rhob.setValidator(QDoubleValidator(1500, 3000, 0))
        self.layer2rhob.textChanged.connect(self.check_state)
        self.layer2rhob.textChanged.emit(self.layer2rhob.text())
        self.layer3vp.setValidator(QDoubleValidator(1000.00, 50000.00, 2))
        self.layer3vp.textChanged.connect(self.check_state)
        self.layer3vp.textChanged.emit(self.layer3vp.text())
        self.layer3rhob.setValidator(QDoubleValidator(1500, 3000, 0))
        self.layer3rhob.textChanged.connect(self.check_state)
        self.layer3rhob.textChanged.emit(self.layer3rhob.text())
        self.freqbox.setValidator(QDoubleValidator(1.00, 500.00, 2))
        self.freqbox.textChanged.connect(self.check_state)
        self.freqbox.textChanged.emit(self.freqbox.text())
        self.lenbox.setValidator(QDoubleValidator(0.010, 1.000, 3))
        self.lenbox.textChanged.connect(self.check_state)
        self.lenbox.textChanged.emit(self.lenbox.text())
        self.sampbox.setValidator(QDoubleValidator(0.0001, 0.01, 4))
        self.sampbox.textChanged.connect(self.check_state)
        self.sampbox.textChanged.emit(self.sampbox.text())

        # Link self.resetButton to a function which clears all input widgets
        self.resetButton.clicked.connect(self.set_defaultValues)

        # function to get values and pass to functions
        def calculateValues():
            # check that input values are valid

            self.calculateState = 1

            # layer rock properties
            vp1 = float(self.layer1vp.text())
            rhob1 = float(self.layer1rhob.text())
            vp2 = float(self.layer2vp.text())
            rhob2 = float(self.layer2rhob.text())
            vp3 = float(self.layer3vp.text())
            rhob3 = float(self.layer3rhob.text())

            # create a list of the rock properties to pass to wb.earthmodel()
            # calculate reflection coefficients of the wedge model
            self.rock_props = [vp1, rhob1, vp2, rhob2, vp3, rhob3]
            self.earthmod, self.refCoef = wb.earthmodel(self.rock_props)

            # wavelet design parameters
            self.f = float(self.freqbox.text())
            dur = float(self.lenbox.text())
            dt = float(self.sampbox.text())

            # design Ricker wavelet
            self.w = wb.wavelet(dur, dt, self.f)
            # call a function to update the self.rickerBox MLP Canvas
            self.update_rickerPlot()

            # calculate the tuning wedge
            self.synth = wb.tuningwedge(self.refCoef, self.w)
            # call a function to update the modelBox MLP Canvas
            self.update_wedgePlot()

            # calculate the tuning curve
            self.z, self.z_tuning, self.amp, self.z_apparent, self.z_onset = wb.tuningcurve(
                self.refCoef, self.synth, self.rock_props
            )
            # call a function to update the ampPlotBox MLP Canvas
            self.update_ampPlot()

            # send results to resultsBox
            self.resultsBox.clear()
            self.resultArr = [self.rock_props, self.f, self.z_tuning, self.z_onset]
            # self.resultsBox.setText('Something has happened')
            self.update_resultsBox()

            self.exportButton.setEnabled(True)

        self.calculateButton.clicked.connect(calculateValues)

        self.exportButton.clicked.connect(self.export_figures)

    # function that validates the QLineEdit input fields upon changing text
    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = "#c4df9b"
            if validator not in self.validatorList:
                self.validatorList.append(validator)
        elif state == QValidator.Intermediate:
            color = "#fff79a"
            if validator in self.validatorList:
                self.validatorList.remove(validator)
        else:
            color = "#f6989d"
        sender.setStyleSheet("QLineEdit { background-color: %s }" % color)
        if len(self.validatorList) == 9:
            self.calculateButton.setEnabled(True)
        else:
            self.calculateButton.setEnabled(False)

    # function to set all inputs to default state
    def set_defaultValues(self):
        self.calculateState = 0
        self.layer1vp.clear()
        self.layer1rhob.clear()
        self.layer2vp.clear()
        self.layer2rhob.clear()
        self.layer3vp.clear()
        self.layer3rhob.clear()
        self.freqbox.setText("25")
        self.lenbox.setText("0.100")
        self.sampbox.setText("0.001")
        self.resultsBox.setText("don't panic!")
        self.calculateButton.setEnabled(False)
        self.exportButton.setEnabled(False)
        # clear out the FigureCanvases if there is no existing plots
        if self.calculateState == 0:
            self._update_ricker_ax.clear()
            self._update_ricker_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_ricker_ax.figure.canvas.draw()
            self._update_earthmodel_ax.clear()
            self._update_earthmodel_ax.tick_params(labelleft=False)
            self._update_wedge_ax.clear()
            self._update_wedge_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_earthmodel_ax.figure.canvas.draw()
            self._update_wedge_ax.figure.canvas.draw()
            self._update_amp_ax.clear()
            self._update_amp_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_amp_ax2.clear()
            self._update_amp_ax2.tick_params(labelright=False, labelbottom=False)
            self._update_amp_ax.figure.canvas.draw()
            self._update_amp_ax2.figure.canvas.draw()
        # clear out the FigureCanvases if there are existing plots
        if self.calculateState == 1:
            del self._update_ricker_ax.lines[:]
            self._update_ricker_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_ricker_ax.figure.canvas.draw()
            del self._update_earthmodel_ax.images[:]
            del self._update_wedge_ax.images[:]
            self._update_wedge_ax.set_xlabel("")
            self._update_wedge_ax.set_ylabel("")
            self._update_earthmodel_ax.set_ylabel("")
            self._update_earthmodel_ax.tick_params(labelleft=False)
            self._update_wedge_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_earthmodel_ax.figure.canvas.draw()
            self._update_wedge_ax.figure.canvas.draw()
            del self._update_amp_ax.lines[:]
            del self._update_amp_ax.collections[:]
            del self._update_amp_ax2.lines[:]
            self._update_amp_ax.tick_params(labelleft=False, labelbottom=False)
            self._update_amp_ax.set_xlabel("")
            self._update_amp_ax.set_ylabel("")
            self._update_amp_ax2.tick_params(labelright=False, labelbottom=False)
            self._update_amp_ax2.get_legend().remove()
            self._update_amp_ax.figure.canvas.draw()
            self._update_amp_ax2.figure.canvas.draw()
            self.calculateState = 0

    # this function updates the self.rickerBox MLP Canvas widget when 'Calculate' button is clicked
    def update_rickerPlot(self):
        self._update_ricker_ax.cla()
        self._update_ricker_ax.tick_params(labelleft=True, labelbottom=True)
        x = wb.get_wavelet_plot_parms(self.w)
        y = self.w
        self._update_ricker_ax.plot(x, y)
        self._update_ricker_ax.figure.canvas.draw()

    # this function update the modelBox MLP Canvas widget on 'calculate' button click
    def update_wedgePlot(self):
        self._update_earthmodel_ax.cla()
        self._update_wedge_ax.cla()
        self._update_earthmodel_ax.tick_params(labelleft=True)
        self._update_wedge_ax.tick_params(labelleft=True, labelbottom=True)
        self._update_earthmodel_ax.imshow(
            self.earthmod, cmap="viridis_r", aspect=0.2, interpolation="bilinear"
        )
        self._update_wedge_ax.imshow(
            self.synth, cmap="viridis_r", aspect=0.2, interpolation="bilinear"
        )
        self._update_wedge_ax.imshow(wb.mask_rc(self.refCoef), cmap="Greys", aspect=0.2)
        self._update_earthmodel_ax.set_ylabel("TWT (ms)")
        self._update_wedge_ax.set_xlabel("Thickness, TWT (ms)")
        self._update_wedge_ax.set_ylabel("TWT (ms)")
        self._update_wedge_ax.set_xlim(0, 100)
        self._update_earthmodel_ax.figure.canvas.draw()
        self._update_wedge_ax.figure.canvas.draw()

    # this function updates the ampPlotBox MLP Canvas widget on 'calculate' button click
    def update_ampPlot(self):
        self._update_amp_ax.cla()
        self._update_amp_ax2.cla()
        self._update_amp_ax.tick_params(labelleft=True, labelbottom=True)
        self._update_amp_ax2.tick_params(labelright=True)
        self._update_amp_ax.plot(self.z, self.amp, label="Tuning Curve (top)")
        ampMin, ampMax = wb.tuningVLine(self.amp)
        self._update_amp_ax.vlines(
            self.z_tuning,
            ampMin,
            ampMax,
            label="Measured Tuning Thickness {}ms TWT".format(self.z_tuning),
        )
        self._update_amp_ax.vlines(
            self.z_onset,
            ampMin,
            ampMax,
            linestyles="dashed",
            label="Measured Onset of Tuning {}ms TWT".format(self.z_onset),
        )
        self._update_amp_ax.set_xlabel("Thickness, TWT (ms)")
        self._update_amp_ax.set_ylabel("Amplitude")
        self._update_amp_ax2.plot(self.z, self.z, "g", label="True thickness ms TWT")
        self._update_amp_ax2.plot(
            self.z, self.z_apparent, "r", label="Apparent thickness ms TWT"
        )
        lines, labels = self._update_amp_ax.get_legend_handles_labels()
        lines2, labels2 = self._update_amp_ax2.get_legend_handles_labels()
        lns = lines + lines2
        labs = labels + labels2
        self._update_amp_ax2.legend(lns, labs, prop={"size": 6}, loc="lower right")
        self._update_amp_ax.figure.canvas.draw()
        self._update_amp_ax2.figure.canvas.draw()

    def update_resultsBox(self):
        self.resultsBox.setText(wb.results_summary(self.resultArr))

    def export_figures(self):
        ricker = QFileDialog.getSaveFileName(
            self,
            "Export Ricker Plot",
            os.getenv("HOME"),
            "Image Files (*.png *.jpeg *.tiff)",
        )
        self.rickerBox.figure.savefig(ricker[0], dpi=100 * 10)
        model = QFileDialog.getSaveFileName(
            self,
            "Export Wedge Model",
            os.getenv("HOME"),
            "Image Files (*.png *.jpeg *.tiff)",
        )
        self.modelBox.figure.savefig(model[0], dpi=100 * 10)
        amp = QFileDialog.getSaveFileName(
            self,
            "Export Amplitude Plot",
            os.getenv("HOME"),
            "Image Files (*.png *.jpeg *.tiff)",
        )
        self.ampPlotBox.figure.savefig(amp[0], dpi=100 * 10)

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(
                currentQTableWidgetItem.row(),
                currentQTableWidgetItem.column(),
                currentQTableWidgetItem.text(),
            )


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("wedge.png"))
    ex = PySeisTuned()
    ex.move(380, 170)
    sys.exit(app.exec_())
