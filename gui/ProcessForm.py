# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 02:56:46 2018

@author: aelshaha
"""

import wx
import wx.grid
import DataConfig as config
import GridDataTable as gdt
import BasicForm as bf
import copy as cpy

from pubsub import pub
from Events import EVENTS


class ProcessDialog ( bf.BasicForm ):
    
    _gridCols = config.DataConfig.PROCESS_PARAMS
    
    def __init__(self, parent):
        super().__init__(parent, "Process data", wx.Size(800, 650))
        contentLayout = wx.BoxSizer( wx.VERTICAL )
        
        layout0 = self.CreateGeneralLayout()

        
        h1 = wx.StaticBox(self, wx.ID_ANY, u"Parameters:" )
        h1.SetForegroundColour('white')
        layout1 = wx.StaticBoxSizer(h1, wx.VERTICAL )
        #Grid and its data table
        self._gridTable1 = gdt.GridDataTable(self._gridCols)
        self._yearsGrid1 = wx.grid.Grid(h1, -1)
        self._yearsGrid1.SetTable(self._gridTable1, True)
        self._yearsGrid1.AutoSizeColumns(False)
        layout1.Add(self._yearsGrid1, 1, wx.ALL, 3)

        contentLayout.Add(layout0, 0, wx.ALL, 5)
        contentLayout.Add(layout1, 1, wx.ALL|wx.EXPAND, 1)
        super().SetContent(contentLayout, wx.ALIGN_CENTER_HORIZONTAL)        
        
    def CreateGeneralLayout(self):
        
        layout = wx.BoxSizer( wx.VERTICAL )
        
        #Name Part
        layout0 = wx.BoxSizer( wx.HORIZONTAL )
        label = wx.StaticText(self, -1, "Process name:")
        label.SetForegroundColour(wx.WHITE)
        layout0.Add(label, 0, wx.ALL, 5)
        self._txtProcessName = wx.TextCtrl(self, size = wx.Size(200, 25))        
        layout0.Add(self._txtProcessName, 0, wx.ALL, 5)
        #######################################################################
        
        layout1 = wx.BoxSizer( wx.HORIZONTAL )
        layout1_1 = self.CreateInCommLayout()
        layout1.Add(layout1_1, 1, wx.ALL|wx.EXPAND, 5)
        
        layout1_2 = self.CreateOutCommLayout()
        layout1.Add(layout1_2, 1, wx.ALL, 5)
        
        layout.Add(layout0, 0, wx.ALL, 5)
        layout.Add(layout1, 0, wx.ALL, 5)
        
        return layout
    
    def CreateInCommLayout(self):        
        #Input Commodities
        sb = wx.StaticBox(self, wx.ID_ANY, u"Input Commodities:" )
        sb.SetForegroundColour('white')
        layout1_1 = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        #Grid and its data table
        self._inCommTbl = gdt.GridDataTable(config.DataConfig.COMMODITY_COLS)
        self._inCommGrid = wx.grid.Grid(sb, -1, wx.DefaultPosition, wx.Size( 350, 200 ), 0 )
        self._inCommGrid.SetTable(self._inCommTbl)
        self._inCommGrid.SetColSize(0, 20)
        self._inCommGrid.SetColSize(1, 200)
        self._inCommGrid.SetRowLabelSize(0)
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        self._inCommGrid.SetColAttr(1, attr)
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        attr.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self._inCommGrid.SetColAttr(2, attr)
        self._inCommGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnInConnEdit)
        layout1_1.Add(self._inCommGrid, 1, wx.ALL|wx.EXPAND, 1)        
        
        return layout1_1
        
    def CreateOutCommLayout(self):
        #Output Commodities
        sb = wx.StaticBox(self, wx.ID_ANY, u"Output Commodities:" )
        sb.SetForegroundColour('white')
        layout1_2 = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        #Grid and its data table
        self._outCommTbl = gdt.GridDataTable(config.DataConfig.COMMODITY_COLS)
        self._outCommGrid = wx.grid.Grid(sb, -1, wx.DefaultPosition, wx.Size( 350, 200 ), 0 )
        self._outCommGrid.SetTable(self._outCommTbl)
        self._outCommGrid.SetColSize(0, 20)
        self._outCommGrid.SetColSize(1, 200)        
        self._outCommGrid.SetRowLabelSize(0)
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        self._outCommGrid.SetColAttr(1, attr)
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        attr.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self._outCommGrid.SetColAttr(2, attr)
        self._outCommGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnOutConnEdit)
        layout1_2.Add(self._outCommGrid, 1, wx.ALL|wx.EXPAND, 5)
        
        return layout1_2
        
    def PopulateProcess(self, process, commList):
        self._orgProc = cpy.deepcopy(process)
        self._process = process
        self._txtProcessName.SetValue(process['Name'])
        ##
        inCommList = cpy.deepcopy(commList)
        for k, v in inCommList.items():
            if k in process['IN']:
                v['selected'] = True
        
        outCommList = cpy.deepcopy(commList)
        for k, v in outCommList.items():
            if k in process['OUT']:
                v['selected'] = True
        ##
        super().PopulateGrid(self._inCommTbl, inCommList)
        super().PopulateGrid(self._outCommTbl, outCommList)
        super().PopulateGrid(self._gridTable1, process['Years'])
        #super().PopulateGrid(self._gridTable2, dataPerYear)
    
    def OnOk(self, event):
        self._process['Name'] = self._txtProcessName.GetValue()
        self._inCommTbl.Commit()
        self._process['IN'] = self.GetSelectedCommodities(self._inCommTbl)
        self._outCommTbl.Commit()
        self._process['OUT'] = self.GetSelectedCommodities(self._outCommTbl)
        self._gridTable1.Commit()
        pub.sendMessage(EVENTS.PROCESS_SAVE, data=self._process)
        
    def GetSelectedCommodities(self, gridTbl):
        x = []
        data = gridTbl.GetData()
        for k in sorted(data):
            if data[k]['selected'] == True:
                x.append(k)
        
        return x
        
    def OnCancel(self, event):
        self._process.update(self._orgProc)
        super().OnCancel(event)
      
    def OnInConnEdit(self, event):
        self.OnCellDblClk(event, 'IN')
        
    def OnOutConnEdit(self, event):
        self.OnCellDblClk(event, 'OUT')
    
    def OnCellDblClk(self, event, In_Out):
        col = event.GetCol()
        if col != 2: return
        
        row = event.GetRow()
        #grid = wx.grid.Grid(sb, -1, wx.DefaultPosition, wx.Size( 350, 200 ), 0 )
        grid = event.GetEventObject()
        selected = grid.GetCellValue(row, 0)#selected
        if selected:
            pub.sendMessage(EVENTS.CONNECTION_EDITING, procId=self._process['Id'], commId=grid.GetRowLabelValue(row), In_Out=In_Out)
        else:
            wx.MessageBox('You have to select the commodity first.', 'Info', wx.OK|wx.ICON_INFORMATION)