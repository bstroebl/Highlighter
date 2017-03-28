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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
from qgis.core import *
from qgis.gui import *
# Import the code for the dialog
from Highlighter_dialog import HighlighterDialog
import os.path


class Highlighter:
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
        self.pointHighlightLayer = None
        self.lineHighlightLayer = None

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

    def initLayers(self):
        return True
        settings = QSettings()
        crs = settings.value( "/Projections/projectDefaultCrs", "EPSG:4326", type=str )
        crsString = "?crs=" + crs

        if self.pointHighlightLayer == None:
            geomType = "multipoint" + crsString
            self.pointHighlightLayer = QgsVectorLayer(geomType, self.tr("Highlight Point"), "memory")
            self.pointHighlightLayer.layerDeleted.connect(self.onPointHighlightLayerDeleted)
            QgsMapLayerRegistry.instance().addMapLayers( [self.pointHighlightLayer] )
            sym = QgsSymbolV2.defaultSymbol( QGis.Point )
            sym.setColor( Qt.yellow )
            sym.setSize( 20.0 )
            sym.setOutputUnit( QgsSymbolV2.MM )
            sym.setAlpha( 0.5 )
            self.pointHighlightLayer.setRendererV2( QgsSingleSymbolRendererV2( sym ) )
            self.iface.legendInterface().moveLayer( self.pointHighlightLayer, markerGroup )

        if self.lineHighlightLayer == None:
            geomType = "multilinestring" + crsString
            self.lineHighlightLayer = QgsVectorLayer(geomType, self.tr("Highlight Line"), "memory")
            self.lineHighlightLayer.layerDeleted.connect(self.onLineHighlightLayerDeleted)
            QgsMapLayerRegistry.instance().addMapLayers( [self.lineHighlightLayer] )
            sym = QgsLineSymbolV2()
            sym.setColor( Qt.yellow )
            sym.setAlpha( 0.5 )
            sym.setWidth( 2 )
            self.lineHighlightLayer.setRendererV2( QgsSingleSymbolRendererV2( sym ) )
            self.iface.legendInterface().moveLayer( self.lineHighlightLayer, markerGroup )

        return True

    def getVectorLayersByType(self,  geomType = None,  skipActive = False):
        '''
        Returns a dict of layers [name: id] in the project for the given
        *geomType*; geomTypes are 0: point, 1: line, 2: polygon
        If *skipActive* is True the active Layer is not included.
        '''

        layerList = {}
        for aLayer in self.iface.legendInterface().layers():
            if 0 == aLayer.type():   # vectorLayer
                if  skipActive and (self.iface.mapCanvas().currentLayer().id() == aLayer.id()):
                    continue
                else:
                    if geomType:
                        if isinstance(geomType,  int):
                            if aLayer.geometryType() == geomType and \
                                    aLayer not in [self.pointHighlightLayer, self.lineHighlightLayer]:
                                layerList[aLayer.id()] =  aLayer.name()
                        else:
                            layerList[aLayer.id()] =  aLayer.name()

        return layerList

    def onPointHighlightLayerDeleted(self):
        self.pointHighlightLayer = None

    def onLineHighlightLayerDeleted(self):
        self.lineHighlightLayer = None

    def onLineLayerDeleted(self):
        self.lineLayer = None

    def onPointLayerDeleted(self):
        self.pointLayer = None

    def run(self):
        """Run method that performs all the real work"""
        self.initLayers()
        pointLayers = self.getVectorLayersByType(0)
        lineLayers = self.getVectorLayersByType(1)
        # Create the dialog (after translation)
        dlg = HighlighterDialog(pointLayers, lineLayers)
        # show the dialog
        dlg.show()
        # Run the dialog event loop
        result = dlg.exec_()
        # See if OK was pressed

        if result == 1:
            pointLayerId = dlg.pointLayerId
            lineLayerId = dlg.lineLayerId

            if pointLayerId == "None":
                self.pointLayer = None
            else:
                self.pointLayer = QgsMapLayerRegistry.instance().mapLayer(pointLayerId)

                try:
                    self.pointLayer.selectionChanged.disconnect(self.highlightPoints)
                except:
                    pass

                self.pointLayer.selectionChanged.connect(self.highlightPoints)

                try:
                    self.pointLayer.layerDeleted.disconnect(self.onPointLayerDeleted)
                except:
                    pass

                self.pointLayer.layerDeleted.connect(self.onPointLayerDeleted)

            if lineLayerId == "None":
                self.lineLayer = None
            else:
                self.lineLayer = QgsMapLayerRegistry.instance().mapLayer(lineLayerId)

                try:
                    self.lineLayer.selectionChanged.disconnect(self.highlightLines)
                except:
                    pass

                self.lineLayer.selectionChanged.connect(self.highlightLines)

                try:
                    self.lineLayer.layerDeleted.disconnect(self.onLineLayerDeleted)
                except:
                    pass

                self.lineLayer.layerDeleted.connect(self.onLineLayerDeleted)

    def highlightLines(self):
        self.clearHighlight(self.lineHighlightLayer)
        self.copySelected(self.lineLayer, self.lineHighlightLayer)

    def highlightPoints(self):
        self.clearHighlight(self.pointHighlightLayer)
        self.copySelected(self.pointLayer, self.pointHighlightLayer)

    def clearHighlight(self, highlightLayer):
        if self.setEditable(highlightLayer):
            highlightLayer.removeSelection()
            highlightLayer.invertSelection()
            highlightLayer.deleteSelectedFeatures()

    def copySelected(self, sourceLayer, highlightLayer):
        if self.setEditable(highlightLayer):
            crsSrc = sourceLayer.crs()
            crsDest = highlightLayer.crs()

            if crsSrc.toProj4() != crsDest.toProj4():
                trans = QgsCoordinateTransform(crsSrc, crsDest)
            else:
                trans = None

            for aFeat in sourceLayer.selectedFeatures():
                aGeom = aFeat.geometry()

                if trans != None:
                    aGeom = trans.transform(aGeom)

                self.addFeature(highlightLayer, aGeom)

    def addFeature(self, highlightLayer, geom):
        newFeature = QgsFeature()
        provider = highlightLayer.dataProvider()
        fields = highlightLayer.pendingFields()
        newFeature.initAttributes(fields.count())

        for i in range(fields.count()):
            newFeature.setAttribute(i,provider.defaultValue(i))

        newFeature.setGeometry(geom)
        return highlightLayer.addFeature(newFeature)

    def setEditable(self, highlightLayer):
        ok = highlightLayer.isEditable() # is already in editMode

        if not ok:
            # try to start editing
            ok = highlightLayer.startEditing()

        return ok
