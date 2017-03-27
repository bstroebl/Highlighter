# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Highlighter
                                 A QGIS plugin
 Highlight selected features
                             -------------------
        begin                : 2017-03-24
        copyright            : (C) 2017 by Bernhard Ströbl/Kommunale Immobilien Jena
        email                : bernhard.stroebl@jena.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Highlighter class from file Highlighter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .HighlightModule import Highlighter
    return Highlighter(iface)
