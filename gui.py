"""
Author: Filip Vlasic
		@s4vgR
		
Date: 30-Oct-2013

Using Team Cymru IP2ASN service.		
"""	

import wx
import wx.lib.mixins.listctrl as listmix
import os
import csv
import re
import webbrowser
import urllib
import urllib2

import cymru


_SIZE = (950, 1000)
_ValidIpAddressRegex = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'


def get_info_url(org, asn):
    ARIN_URL = 'http://whois.arin.net/rest/asn/'
    RIPE_URL = 'http://apps.db.ripe.net/whois/lookup/ripe/aut-num/AS'
    LACNIC_URL = 'http://lacnic.net/cgi-bin/lacnic/whois?lg=EN&query=AS'
    APNIC_URL = 'http://wq.apnic.net/apnic-bin/whois.pl?searchtext=AS'

    def prepare_afrinic_request():
        url = 'https://www.afrinic.net/en/services/whois-query'
        values = {'query' : 'as%s' %asn,
                  'alt_database' : 'AFRINIC',
                  'object_type' : 'All',
                  'ip_search_lvl' : 'Default',
                  'inverse_attributes' : None,
                  'queryType' : 'simple',
                  'option' : 'com_whois',
                  'controller' : 'whois' }

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)        
        the_page = response.read()
        with open('afrinic.html', 'wb') as f:
            f.write(the_page)

    if asn != 'NA':
        if org == 'arin':
            return ARIN_URL + asn
        elif org == 'ripencc':
            return RIPE_URL + asn
        elif org == 'lacnic':
            return LACNIC_URL + asn
        elif org == 'apnic':
            return APNIC_URL + asn
        elif org == 'afrinic':
            prepare_afrinic_request()
            return 'file://' + os.path.join(os.getcwd(), 'afrinic.html').replace('\\', '/')
    else:
        return ''


class MyDialog(wx.Dialog):    
    def __init__(self, parent, object):
        super(MyDialog, self).__init__(parent)
        self.parent = parent       
        self.panel =  object(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetInitialSize()
        #self.SetSize(_SIZE)
        self.Show(True)
        self.ip = None      

    def OnOK(self, e):        
        self.parent.mtable.enterItems([self.panel.ip.GetValue()])
        self.parent.ips.add(self.panel.ip.GetValue())
        self.Destroy()
        e.Skip()


class AddSingleIPPanel(wx.Panel):
    def __init__(self, parent):
        super(AddSingleIPPanel, self).__init__(parent)
             
        self.ip = wx.TextCtrl(self)
        self.parent = parent

        sizer = wx.FlexGridSizer(2, 2, 8, 8)
        sizer.Add(wx.StaticText(self, label='IP address:'), 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.ip, 0, wx.EXPAND)

        msizer = wx.BoxSizer(wx.VERTICAL)
        msizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 20)
        btnszr = wx.StdDialogButtonSizer()
        buttonOK = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, parent.OnOK, buttonOK)
        buttonOK.SetDefault()
        buttonCancel = wx.Button(self, wx.ID_CANCEL)
        btnszr.AddButton(buttonOK)
        btnszr.AddButton(buttonCancel)
        msizer.Add(btnszr, 0, wx.ALIGN_CENTER|wx.ALL, 12)
        btnszr.Realize()

        self.SetSizer(msizer)    


class InPanelWithSort(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.selectedItem = False        
        self.InitUI()        

    def InitUI(self):
        # table
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT)
        
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected) 
        self.list.InsertColumn(0, '', width=30)
        self.list.InsertColumn(1, 'IP address', width=120)
        self.list.InsertColumn(2, 'ASN', width=50)      
        self.list.InsertColumn(3, 'Country', width=50)
        self.list.InsertColumn(4, 'Organization', width=360)
        self.list.InsertColumn(5, 'RIR', width=120)
        self.list.InsertColumn(6, 'More info', width=200)

        # load DB data
        #self.dbrecords = []              
        #self.updateItems()
        self.whois_dict = {}
        self.itemDataMap = {}

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(hbox)        
        self.Show(True)

        # for sort
        listmix.ColumnSorterMixin.__init__(self, 6)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)

    def enterItems(self, ip_list):
        existing_items_count = self.list.GetItemCount()      
        for no, ip in enumerate(ip_list):
            index = existing_items_count + no
            #index = self.list.InsertStringItem(sys.maxint, str(no+1))            
            self.list.InsertStringItem(index, str(index + 1))
            self.list.SetStringItem(index, 1, str(ip))
            self.list.SetStringItem(index, 2, '')
            self.list.SetStringItem(index, 3, '')
            self.list.SetStringItem(index, 4, '')
            self.list.SetStringItem(index, 5, '')
            self.list.SetStringItem(index, 6, '')
            self.list.SetItemData(index, index)
            self.itemDataMap[index] = (str(index), str(ip), '', '', '', '', '')

    def updateItems(self, whois_dict):
        self.deleteAllItems()
        self.whois_dict = whois_dict               
        for index, ip in enumerate(whois_dict.keys()):
            #index = self.list.InsertStringItem(sys.maxint, str(no+1))
            self.list.InsertStringItem(index, str(index+1))
            self.list.SetStringItem(index, 1, str(ip))
            self.list.SetStringItem(index, 2, str(whois_dict[ip][0])) # asn
            self.list.SetStringItem(index, 3, str(whois_dict[ip][1])) # cc
            self.list.SetStringItem(index, 4, str(whois_dict[ip][2])) # org
            self.list.SetStringItem(index, 5, str(whois_dict[ip][3])) # rir
            self.list.SetStringItem(index, 6, get_info_url(str(whois_dict[ip][3]), str(whois_dict[ip][0])))
            self.whois_dict[ip].append(self.list.GetItem(index, 6).GetText())
            #if self.list.GetItem(index, 3).GetText() in ['HR']:                    
            #    self.list.SetItemBackgroundColour(index, col='#FFEC8B')
            self.list.SetItemData(index, index)    
            self.itemDataMap[index] = (str(index), str(ip), str(whois_dict[ip][0]), str(whois_dict[ip][1]), str(whois_dict[ip][2]),\
                                     str(whois_dict[ip][3]), get_info_url(str(whois_dict[ip][3]), str(whois_dict[ip][0])))    

    def deleteAllItems(self):
        self.whois_dict.clear()
        self.itemDataMap.clear()     
        self.list.DeleteAllItems()

    def getSelectedItems(self):  # get indexes
        selection = []
        index = self.list.GetFirstSelected()
        selection.append(index)
        while len(selection) != self.list.GetSelectedItemCount():
            index = self.list.GetNextSelected(index)
            selection.append(index)            
        return selection

    def getItems(self):
        items = []
        if self.selectedItem: # get selection
            indexes = self.getSelectedItems()
            for no, ip in enumerate(self.whois_dict.keys()):
                if no in indexes:
                    item = ( str(ip), str(self.whois_dict[ip][0]), str(self.whois_dict[ip][1]),\
                     str(self.whois_dict[ip][2]), str(self.whois_dict[ip][3]), str(self.whois_dict[ip][4]) )
                    items.append(item)
            self.selectedItem = False        
            return items
        else: # get all
            for ip in self.whois_dict.keys():
                item = ( str(ip), str(self.whois_dict[ip][0]), str(self.whois_dict[ip][1]),\
                 str(self.whois_dict[ip][2]), str(self.whois_dict[ip][3]), str(self.whois_dict[ip][4]) ) 
                #print item
                items.append(item)
            return items

    def getMoreInfoURL(self):
        return self.list.GetItem(self.selectedItem, 6).GetText()

    def OnItemSelected(self, event):
        self.selectedItem = event.m_itemIndex # index
        
    def OnItemDeselected(self, event):
        self.selectedItem = False

    # sort (mixin)
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list 
    
    def OnColClick(self, event):
        #print "column clicked"
        event.Skip()


class MainFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, size = _SIZE)
        self.toolbar = self.CreateToolBar()
        self.mtable =  InPanelWithSort(self, -1)        
        # big box
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        #self.statusbar = self.CreateStatusBar()
        self.InitUI()        
        self.ips = set()                       

    def InitUI(self):
            add_ip = self.toolbar.AddLabelTool(wx.ID_ANY, 'Add a single IP address', wx.Bitmap('media/add_ip.png'), shortHelp = 'Add a single IP address')                                
            import_ips = self.toolbar.AddLabelTool(wx.ID_ANY, 'Load IP address(es) from file', wx.Bitmap('media/open.png'), shortHelp = 'Load IP address(es) from file')
            delete_ips = self.toolbar.AddLabelTool(wx.ID_ANY, 'Clear', wx.Bitmap('media/delete.png'), shortHelp = 'Clear')
            whois = self.toolbar.AddLabelTool(wx.ID_ANY, 'Run WHOIS', wx.Bitmap('media/whois.png'), shortHelp = 'Run WHOIS')
            export = self.toolbar.AddLabelTool(wx.ID_ANY, 'Export to CSV file', wx.Bitmap('media/csv.png'), shortHelp = 'Export to CSV file')
            more_info = self.toolbar.AddLabelTool(wx.ID_ANY, 'More info online', wx.Bitmap('media/www.png'), shortHelp = 'More info online')            
            self.toolbar.AddSeparator()
            info = self.toolbar.AddLabelTool(wx.ID_ANY, 'About', wx.Bitmap('media/info.png'), shortHelp = 'About')        
            quit = self.toolbar.AddLabelTool(wx.ID_ANY, 'Quit', wx.Bitmap('media/quit.png'), shortHelp = 'Quit')
            self.toolbar.Realize()
                       
            self.vbox.Add(self.mtable, 1, wx.EXPAND)
                       
            self.Bind(wx.EVT_TOOL, self.OnAddIP, add_ip)
            self.Bind(wx.EVT_TOOL, self.OnIPImport, import_ips)
            self.Bind(wx.EVT_TOOL, self.OnDeleteIPs, delete_ips)
            self.Bind(wx.EVT_TOOL, self.OnStartWhois, whois)
            self.Bind(wx.EVT_TOOL, self.OnExport, export)
            self.Bind(wx.EVT_TOOL, self.OnGetMoreInfo, more_info)            
            self.Bind(wx.EVT_TOOL, self.OnAbout, info)        
            self.Bind(wx.EVT_TOOL, self.OnQuit, quit)              

            self.SetSizer(self.vbox)
            self.SetTitle('AutoIs')
            self.Centre()            
            
            self.Show(True)

    def OnAddIP(self, e):
        MyDialog(self, AddSingleIPPanel)
        #self.mtable.enterItems([dialog.ip])

    def OnDeleteIPs(self, e):
        self.ips = set()
        self.mtable.deleteAllItems()

    def OnIPImport(self, e):
        wildcard = "All files (*.*)|*.*"
        dlg = wx.FileDialog(self, message="Choose a file",\
            defaultDir = os.getcwd(), defaultFile = "", wildcard = wildcard,\
            style = wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            with open(filename) as f:
                #self.ips = f.readlines()
                for line in f.readlines():                                     
                    self.ips |= set(re.findall(_ValidIpAddressRegex, line))                    
            self.mtable.enterItems(self.ips)
        dlg.Destroy()

    def OnStartWhois(self, e):
        result = cymru.whoare(self.ips)        
        self.mtable.updateItems(result)

    def OnExport(self, e):
        wildcard = "CSV files (*.csv)|*.csv|""Text files (*.txt)|*.txt|""All files (*.*)|*.*"
        dlg = wx.FileDialog(self, message="Choose a file",\
            defaultDir = os.getcwd(), defaultFile = "", wildcard = wildcard,\
            style = wx.SAVE | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()            
            with open(filename, 'wb') as f:
                csvr = csv.writer(f)
                for item in self.mtable.getItems():
                    csvr.writerow(item)
        dlg.Destroy()

    def OnGetMoreInfo(self, e):        
        url = self.mtable.getMoreInfoURL()
        if url:
            webbrowser.open(url, new = 2)

    def OnAbout(self, e):        
        info = wx.AboutDialogInfo()
        #info.SetIcon(wx.Icon('media/.png', wx.BITMAP_TYPE_PNG))
        info.SetName('AutoIs')
        info.SetVersion('1.1')
        info.SetCopyright('(c) 2013 Filip Vlasic')
        info.SetWebSite('www.securitynuggets.co.uk')
        wx.AboutBox(info)
        
    def OnQuit(self, e):        
        #self.refresh_thread.Stop()       
        #for t in self.pingthreads:        
            #t.Stop()
        #self.Close()
        self.Destroy()


def main():     
    guiapp = wx.App() #redirect = True, filename = "error_log.txt") # DEBUG
    MainFrame(None, -1)
    guiapp.MainLoop()


if __name__ == '__main__':
    main()