# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HighlighterDialog
                                 A QGIS plugin
 Highlight selected features
                             -------------------
        begin                : 2017-03-24
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Bernhard Ströbl/Kommunale Immobilien Jena
        email                : bernhard.stroebl@jena.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from builtins import range
import os

from qgis.PyQt import QtWidgets, QtGui,  QtCore, uic
from qgis.gui import QgsColorDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Highlightdialog_base.ui'))

class HighlighterDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, pointLayers, lineLayers, pointLayerId = None, lineLayerId = None,
        pointColor = None,  lineColor = None,  parent=None):
        """Constructor."""
        super(HighlighterDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.pointLayerId = pointLayerId
        self.lineLayerId = lineLayerId
        self.defaultColor = QtGui.QColor.fromRgb(255, 255, 0)

        if pointColor == None:
            self.pointColor =  self.defaultColor
        else:
            self.pointColor = pointColor

        if lineColor == None:
            self.lineColor =  self.defaultColor
        else:
            self.lineColor = lineColor

        self.initialize(pointLayers, lineLayers)

    def initialize(self, pointLayers, lineLayers):
        self.fillComboBoxFromDict(self.cbxPointLayer, pointLayers)

        if self.pointLayerId != None:
            for i in range(self.cbxPointLayer.count()):
                if self.cbxPointLayer.itemData(i) == self.pointLayerId:
                    self.cbxPointLayer.setCurrentIndex(i)
                    break

        self.fillComboBoxFromDict(self.cbxLineLayer, lineLayers)

        if self.lineLayerId != None:
            for i in range(self.cbxLineLayer.count()):
                if self.cbxLineLayer.itemData(i) == self.lineLayerId:
                    self.cbxLineLayer.setCurrentIndex(i)
                    break

        self.setButtonColor(self.btnPointColor, self.pointColor)
        self.setButtonColor(self.btnLineColor, self.lineColor)

    def setButtonColor(self, button, thisColor):
        sStylesheet = "background: " + thisColor.name() + ";"
        button.setStyleSheet(sStylesheet)
        button.update()

    def fillComboBoxFromDict(self, cbx, thisDict):
        cbx.addItem(" ", None)

        for key, value in thisDict.items():
            cbx.addItem( value, key )

    def chooseColor(self, color):
        clrDlg = QgsColorDialog(None,  color = color)
        clrDlg.setAllowOpacity(True)
        clrDlg.show()
        result = clrDlg.exec_()

        if result == 1:
            color = clrDlg.color()

        return color

    @QtCore.pyqtSlot(   )
    def on_btnPointColor_clicked(self, checked = False):
        self.pointColor = self.chooseColor(self.pointColor)
        self.setButtonColor(self.btnPointColor, self.pointColor)

    @QtCore.pyqtSlot(   )
    def on_btnLineColor_clicked(self, checked = False):
        self.lineColor = self.chooseColor(self.lineColor)
        self.setButtonColor(self.btnLineColor, self.lineColor)

    def accept(self):
        self.pointLayerId = self.cbxPointLayer.itemData(self.cbxPointLayer.currentIndex())
        self.lineLayerId = self.cbxLineLayer.itemData(self.cbxLineLayer.currentIndex())
        self.done(1)

    def reject(self):
        self.done(0)
