# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Highlighter
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

from __future__ import absolute_import
from builtins import range
from builtins import object
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

# Initialize Qt resources from file resources.py
from qgis.core import *
from qgis.gui import *
# Import the code for the dialog
from .Highlighter_dialog import HighlighterDialog
import os.path


class Highlighter(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Highlighter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Highlighter')
        # TODO: We are going to let the user set this up in a future iteration
        #self.toolbar = self.iface.addToolBar(u'Highlighter')
        #self.toolbar.setObjectName(u'Highlighter')
        self.pointLayer = None
        self.pointTreeLayer = None
        self.lineLayer = None
        self.lineTreeLayer = None
        self.pointHighlightColor = None
        self.lineHighlightColor = None
        self.lineHighlights = []
        self.pointHighlights = []

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Highlighter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Highlighter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Settings'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            add_to_toolbar = False)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Highlighter'),
                action)

        self.clearHighlight()

    def getVectorLayersByType(self,  geomType):
        '''
        Returns a dict of layers [id:name] in the project for the given
        *geomType*; geomTypes are 0: point, 1: line, 2: polygon
        '''

        layerList = {}
        for aTreeLayer in QgsProject.instance().layerTreeRoot().findLayers():
            if 0 == aTreeLayer.layer().type():   # vectorLayer
                if geomType == aTreeLayer.layer().geometryType():
                    layerList[aTreeLayer.layer().id()] =  aTreeLayer.layer().name()

        return layerList

    def onLineLayerDeleted(self):
        self.disconnectLineSlots()
        self.clearHighlight("line")
        self.lineLayer = None

    def onPointLayerDeleted(self):
        self.disconnectPointSlots()
        self.clearHighlight("point")
        self.pointLayer = None

    def onVisibilityChanged(self, thisLayerTreeNode):
        if thisLayerTreeNode == self.pointTreeLayer:
            if thisLayerTreeNode.isVisible():
                self.highlightPoints()
            else:
                self.clearHighlight("point")
        elif thisLayerTreeNode == self.lineTreeLayer:
            if thisLayerTreeNode.isVisible():
                self.highlightLines()
            else:
                self.clearHighlight("line")

    def disconnectPointSlots(self):
        if self.pointLayer != None: #remove slots from current point layer
            try:
                self.pointLayer.selectionChanged.disconnect(self.highlightPoints)
            except:
                pass
            try:
                self.pointLayer.destroyed.disconnect(self.onPointLayerDeleted)
            except:
                pass
            try:
                self.pointTreeLayer.visibilityChanged.disconnect(self.onVisibilityChanged)
            except:
                pass

    def disconnectLineSlots(self):
        if self.lineLayer != None:
            try:
                self.lineLayer.selectionChanged.disconnect(self.highlightLines)
            except:
                pass
            try:
                self.lineLayer.destroyed.disconnect(self.onLineLayerDeleted)
            except:
                pass
            try:
                self.lineTreeLayer.visibilityChanged.disconnect(self.onVisibilityChanged)
            except:
                pass

    def run(self):
        """Run method that performs all the real work"""
        pointLayers = self.getVectorLayersByType(0)

        if len(pointLayers) >= 0: # wait for result
            lineLayers = self.getVectorLayersByType(1)

            if self.pointLayer != None:
                oldPointLayerId = self.pointLayer.id()
            else:
                oldPointLayerId = None

            if self.lineLayer != None:
                oldLineLayerId = self.lineLayer.id()
            else:
                oldLineLayerId = None

            # Create the dialog (after translation)
            dlg = HighlighterDialog(pointLayers, lineLayers, \
                oldPointLayerId, oldLineLayerId, self.pointHighlightColor,
                self.lineHighlightColor)
            # show the dialog
            dlg.show()
            # Run the dialog event loop
            result = dlg.exec_()
            # See if OK was pressed

            if result == 1:
                pointLayerId = dlg.pointLayerId
                lineLayerId = dlg.lineLayerId
                self.pointHighlightColor = dlg.pointColor
                self.lineHighlightColor = dlg.lineColor

                if pointLayerId == None:
                    self.onPointLayerDeleted()
                else:
                    if oldPointLayerId != pointLayerId:
                        self.disconnectPointSlots()
                        # find new point layer
                        self.pointTreeLayer = QgsProject.instance().layerTreeRoot().findLayer(pointLayerId)

                        if self.pointTreeLayer != None:
                            self.pointLayer = self.pointTreeLayer.layer()
                            self.highlightPoints() # highlight if there is already a selection
                            self.pointLayer.selectionChanged.connect(self.highlightPoints)
                            self.pointLayer.destroyed.connect(self.onPointLayerDeleted)
                            self.pointTreeLayer.visibilityChanged.connect(self.onVisibilityChanged)

                if lineLayerId == None:
                    self.onLineLayerDeleted()
                else:
                    if oldLineLayerId != lineLayerId:
                        self.disconnectLineSlots()
                        self.lineTreeLayer =  QgsProject.instance().layerTreeRoot().findLayer(lineLayerId)

                        if self.lineTreeLayer != None:
                            self.lineLayer = self.lineTreeLayer.layer()
                            self.highlightLines()
                            self.lineLayer.selectionChanged.connect(self.highlightLines)
                            self.lineLayer.destroyed.connect(self.onLineLayerDeleted)
                            self.lineTreeLayer.visibilityChanged.connect(self.onVisibilityChanged)

    def highlightLines(self):
        '''
        slot to be called when selection on line layer has changed
        this code is inspired by: http://gis.stackexchange.com/questions/174664/
        set-selection-color-transparent-and-border-color-red-in-qgis-using-python
        '''
        self.clearHighlight("line")

        if len(self.lineLayer.selectedFeatures()) > 0:
            for aFeat in self.lineLayer.selectedFeatures():
                aGeom = aFeat.geometry()
                h = QgsHighlight(self.iface.mapCanvas(), aGeom, self.lineLayer)

                # set highlight symbol properties
                h.setColor(self.lineHighlightColor)
                h.setWidth(10)

                # write the object to the list
                self.lineHighlights.append(h)

    def highlightPoints(self):
        self.clearHighlight("point")

        if len(self.pointLayer.selectedFeatures()) > 0:
            for aFeat in self.pointLayer.selectedFeatures():
                aGeom = aFeat.geometry()
                h = QgsHighlight(self.iface.mapCanvas(), aGeom, self.pointLayer)

                # set highlight symbol properties
                h.setColor(self.pointHighlightColor)
                h.setWidth(10)

                # write the object to the list
                self.pointHighlights.append(h)

    def clearHighlight(self, mode = "all"):
        if mode == "all" or mode == "point":
            for h in range(len(self.pointHighlights)):
                self.pointHighlights.pop(0)

        if mode == "all" or mode == "line":
            for h in range(len(self.lineHighlights)):
                self.lineHighlights.pop(0)
