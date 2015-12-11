# -*- coding: utf-8 -*-
"""
/***************************************************************************
 cTAB2SHP
                                 A QGIS plugin
 This plugin converts a whole tab files directory to shapefiles
                              -------------------
        begin                : 2015-12-08
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Geo-Hyd/Antea Group
        email                : robin.prest@anteagroup.com
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon,QMessageBox,QFileDialog
from qgis.core import *
from qgis.gui import *

try:
  from osgeo import ogr
  print('Import of ogr from osgeo worked.  Hurray!\n')
except:
  print('Import of ogr from osgeo failed\n\n')

# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from cTAB2SHP_dockwidget import cTAB2SHPDockWidget
import os.path

class cTAB2SHP:
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
            'cTAB2SHP_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TAB files to shapefile')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'cTAB2SHP')
        self.toolbar.setObjectName(u'cTAB2SHP')

        #print "** INITIALIZING cTAB2SHP"

        self.pluginIsActive = False
        self.dockwidget = None


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
        return QCoreApplication.translate('cTAB2SHP', message)


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

        icon_path = ':/plugins/cTAB2SHP/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Convert TAB to SHP'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING cTAB2SHP"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD cTAB2SHP"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&TAB files to shapefile'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""


        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING cTAB2SHP"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = cTAB2SHPDockWidget()

                #SIGNAUX ici (le widget est initialisé ci-dessus)

                # Signal 1 : En cliquant sur le bouton tbRep on lance la fonction fRep qui charge le répertoire
                self.dockwidget.tbRep.clicked.connect(self.fRep)

                # Signal 2 : En cliquant sur le bouton pbLister on lance la fonction fLister qui liste les TAB à convertir
                self.dockwidget.pbLister.clicked.connect(self.fLister)

                # Signal : En cliquant sur le bouton pbConvert on lance la fonction fConvert
                self.dockwidget.pbConvert.clicked.connect(self.fConvert)

                # connect to provide cleanup on closing of dockwidget
                self.dockwidget.closingPlugin.connect(self.onClosePlugin)

                # show the dockwidget
                # TODO: fix to allow choice of dock location
                self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
                self.dockwidget.show()

                #Message de démarrage
                self.iface.mainWindow().statusBar().showMessage(u"Sélectionner le répertoire")


    #FONCTIONS DEF PERSO ICI

    # Assistant pour charger le chemin du répertoire dans la boite de texte txtRep
    def fRep(self):
        dirName = QFileDialog.getExistingDirectory(self.dockwidget,"Open a folder",self.dockwidget.txtRep.text(),QFileDialog.ShowDirsOnly)
        self.dockwidget.txtRep.setText(dirName)

    def fLister(self):
        self.iface.mainWindow().statusBar().showMessage("")
        # Ajoute ce qui est dans la boite de texte dans home_directory
        home_directory = self.dockwidget.txtRep.text()

        if os.path.exists(home_directory):
            # Liste les fichiers de ce répertoire
            file_list = os.listdir(home_directory)
            #tab_list : contenant final de la liste de TAB
            tabListComplet = []
            tabListMin = []
            self.dockwidget.lwTABFiles.clear()
            # creation du texte X:/monrep/monfichier.ext

            for file in file_list:
                fPath = "{lechemin}/{lefichier}".format(lechemin=home_directory,lefichier=file)
                # A partir d'un path, recuperer le nom et l'extension
                filename, filextension = os.path.splitext(fPath)

                #Filtre selon l'extension
                if filextension.upper() == ".TAB":
                    #ajoute le path dans une liste
                    if os.path.isfile(fPath):
                        tabListComplet.append(fPath)
                        tabListMin.append(file)

            self.dockwidget.lwTABFiles.addItems(tabListMin)

            # Ajouter un message pour rendre compte de l'execution
            if len(tabListMin) == 0:
                self.iface.mainWindow().statusBar().showMessage(u"Aucun fichier trouvé")
            else:
                self.iface.mainWindow().statusBar().showMessage(u"OK : {n} couches trouvées".format(n = str(len(tabListMin))))
        else:
            self.iface.mainWindow().statusBar().showMessage(u"Problème de répertoire")
            self.dockwidget.lwTABFiles.clear()

    def fConvert(self):
        #on recupère le répertoire
        tabDir = self.dockwidget.txtRep.text()

        #On récupère la liste de tous les fichiers
        tabListAll = []
        for i in range(0,len(self.dockwidget.lwTABFiles)):
            tabListAll.append(self.dockwidget.lwTABFiles.item(i).text())

        #On récupère la liste des noms de fichiers sélectionnés
        itemListSel = []
        tabListSel = []
        itemListSel = self.dockwidget.lwTABFiles.selectedItems()
        for itemSel in itemListSel:
            mText = itemSel.text()
            tabListSel.append(mText)

        #on crée tabListFinale (qui contient les noms des fichiers) en fonction de si c'est sélectionné ou pas
        tabListFinale = []
        if itemListSel != []:
            tabListFinale = tabListSel
        else:
            tabListFinale = tabListAll

        #On initialise la liste qui va nourrir ogr
        tabListComplet = []

        for itemTab in tabListFinale:
            tabListComplet.append("{}\{}".format(tabDir,itemTab))

        appel_ogr = ""
        progress = 0
        for f in tabListComplet:
            driver_tab = ogr.GetDriverByName("MapInfo File")
            tab_tab = driver_tab.Open(f)
            layer_tab = tab_tab.GetLayer()
            type_tab = layer_tab.GetGeomType()

            fichier_nom, fichier_extension = os.path.splitext(f)
            print (fichier_extension)
            if str(type_tab) == '0':
                appel_ogr = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='Polygon'" -f "ESRI Shapefile" "{fichier_nom}_polygon.shp" "{fichier_nom}{fichier_extension}" """.format(**locals())
                print (appel_ogr)
                os.system(appel_ogr)
            if str(type_tab) == '1':
                appel_ogr = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='Point'" -f "ESRI Shapefile" "{fichier_nom}_point.shp" "{fichier_nom}{fichier_extension}" """.format(**locals())
                print (appel_ogr)
                os.system(appel_ogr)
            if str(type_tab) == '2':
                appel_ogr = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='LineString'" -f "ESRI Shapefile" "{fichier_nom}_polyligne.shp" "{fichier_nom}{fichier_extension}" """.format(**locals())
                print (appel_ogr)
                os.system(appel_ogr)
            progress = progress + 1
            self.dockwidget.progressBar.setValue(progress)




        # cmd = ""
        # progress = 0
        # self.dockwidget.progressBar.setMinimum(0)
        # self.dockwidget.progressBar.setMaximum(len(tabListComplet))

        # for file in tabListComplet:
            # filename, filextension = os.path.splitext(file)
            # cmd = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='Polygon'" -f "ESRI Shapefile" {filename}_polygon.shp {filename}.tab -nlt POLYGON""".format(**locals())
            # os.system(cmd)
            # cmd = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='LineString'" -f "ESRI Shapefile" {filename}_linestring.shp {filename}.tab -nlt LINESTRING""".format(**locals())
            # os.system(cmd)
            # cmd = """ogr2ogr -overwrite -skipfailures -where "OGR_GEOMETRY='Point'" -f "ESRI Shapefile" {filename}_point.shp {filename}.tab -nlt POINT""".format(**locals())
            # os.system(cmd)
            # progress += 1
            # self.dockwidget.progressBar.setValue(progress)
