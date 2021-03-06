# -*- coding: utf-8 -*-
"""
/***************************************************************************
 cTAB2SHP
                                 A QGIS plugin
 This plugin converts a whole tab files directory to shapefiles
                             -------------------
        begin                : 2015-12-08
        copyright            : (C) 2015 by Geo-Hyd/Antea Group
        email                : robin.prest@anteagroup.com
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
    """Load cTAB2SHP class from file cTAB2SHP.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .cTAB2SHP import cTAB2SHP
    return cTAB2SHP(iface)
