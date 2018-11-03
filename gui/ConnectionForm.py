# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 02:56:46 2018

@author: aelshaha
"""

import wx
import wx.grid
import collections


class ConnectionDialog ( wx.Dialog ):
    
    _gridCols = {'ratio': 'Ratio (1)', 'ratioMin': 'Ratio-Min'}
    
    def __init__(self, parent):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = "Connection data", size= wx.Size(600, 400))
        self.SetBackgroundColour("black")
        
        mainLayout = wx.StaticBoxSizer( wx.StaticBox(self, wx.ID_ANY, u"" ), wx.VERTICAL )
  
        self._yearsGrid = wx.grid.Grid(mainLayout.GetStaticBox(), -1)
        self._yearsGrid.CreateGrid(0, len(self._gridCols))
        for i, item in enumerate(self._gridCols.items()):
            self._yearsGrid.SetColSize(i, 200)
            self._yearsGrid.SetColLabelValue(i, item[1])
        #self._yearsGrid.AutoSizeColumns(False)
        mainLayout.Add(self._yearsGrid, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        btnsLayout = wx.BoxSizer( wx.HORIZONTAL )
        btnOk = wx.Button(self, label="Ok")
        btnCancel = wx.Button(self, label="Cancel")
        btnFillAll = wx.Button(self, label="Fill all as first year")
        btnsLayout.Add(btnOk, 0, wx.ALL, 5)
        btnsLayout.Add(btnCancel, 0, wx.ALL, 5)
        btnsLayout.Add(btnFillAll, 0, wx.ALL, 5)        
        mainLayout.Add(btnsLayout, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        
        self.SetSizer( mainLayout )
        self.Layout()
        #mainLayout.Fit(self)    
        self.Centre( wx.BOTH )
        
    def PopulateConnectionGrid(self, dataPerYear):       
        i = self._yearsGrid.GetNumberRows()
        if i > 0:
            self._yearsGrid.DeleteRows(0, i)
            i = 0
            
        dataPerYear = collections.OrderedDict(sorted(dataPerYear.items()))
        for year, data in dataPerYear.items():
            self._yearsGrid.InsertRows(i, 1)
            self._yearsGrid.SetRowLabelValue(i, year)
            for j, key in enumerate(self._gridCols.keys()):
                self._yearsGrid.SetCellValue(i, j, data[key])
            i += 1      
    
    def __del__( self ):
        pass
