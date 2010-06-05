#!/usr/bin/env python
#coding:utf-8
################################
#  author:observer
#  email:jingchaohu@gmail.com
#
#  blog:http://obmem.com
#  website:
#      http://www.avfun001.org
#      http://www.simplecd.org
################################

import wx
import wx.lib.sized_controls as sc
import json
import socket
import time

HOST = "avfun001.org"
PORT = 1818

class FormDialog(sc.SizedDialog):
    def __init__(self, parent, id, title):
        self.js = None # 保存批量弹幕json
        self.syntax = False # 判断语法是否正确
        self.apikey = '' # 保存apikey

        sc.SizedDialog.__init__(self, None, -1, title, 
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        # partid 
        wx.StaticText(pane, -1, "Partid")
        self.pidCtrl = wx.TextCtrl(pane, -1, u"100384.001")
        self.pidCtrl.SetSizerProps(expand=True)

        # apikey
        wx.StaticText(pane, -1, "APIKEY")
        self.apiCtrl = wx.TextCtrl(pane, -1, u"请输入您的APIKEY")
        self.apiCtrl.SetSizerProps(expand=True)
        
        # 弹幕说明
        wx.StaticText(pane, -1, u"弹幕格式")
        wx.StaticText(pane, -1, u"每个弹幕以|分隔，单个弹幕格式如下\n"
                                u"        time,txt,mode,color,fontsize\n"
                                u"time为播放器时间，浮点数，txt为弹幕文本\n"
                                u"mode为弹幕模式，<4为滚动，4底部渐隐，5顶部渐隐\n"
                                u"color为颜色int(r*65536+g*256+b)，fontsize为字体大小\n")
        #弹幕control
        wx.StaticText(pane, -1, u"批量弹幕")
        self.subCtrl = wx.TextCtrl(pane, -1,
                        u"1.1,弹幕1:白色滚动字号25弹幕,1,16777215,25|"
                        u"1.2,弹幕2:蓝色顶部渐隐字号35弹幕,5,255,35|"
                        u"1.3,弹幕3:红色底部渐隐字号45弹幕,4,16711680,45|"
                        u"1.4,弹\n幕\n4:\n竖\n排\n白\n色\n弹\n幕,3,16777215,25",
                       size=(400, 100), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
            
        self.subCtrl.SetSizerProps(expand=True)
        
        # row 3
        #checkCtrl = wx.Button(pane, -1, u"检查语法")
        #self.Bind(wx.EVT_BUTTON, self.onCheck, checkCtrl)
        sendCtrl = wx.Button(pane,-1,u"发射弹幕")
        self.Bind(wx.EVT_BUTTON, self.onSend, sendCtrl)
        
        # add dialog buttons
        #self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    def alert(self,msg,type=u"语法错误"):
        pane = self.GetContentsPane()
        dlg = wx.MessageDialog(self, type+u':%s'%msg,
                           type,
                           wx.OK | wx.ICON_INFORMATION
                           #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                           )
        dlg.ShowModal()
        dlg.Destroy()
       
    # check syntax
    def onCheck(self,event):
        self.syntax = False
        self.apikey = self.apiCtrl.GetValue()
        partid = self.pidCtrl.GetValue()
        subs = self.subCtrl.GetValue()
        try:
            partid = float(partid)
        except:
            self.alert(u"Partid必须是浮点数")
            return
        try:
            pass
            self.apikey = self.apikey.encode("ascii")
            if len(self.apikey) != 64:
                self.alert(u"APIKEY格式不正确")
                return
        except:
            self.alert(u"APIKEY格式不正确")
            return
        try:
            subs = subs.split('|')
            dl = []
            for sub in subs:
                sub = sub.split(',')
                if sub[0] == '':
                    continue
                if len(sub) != 5:
                    self.alert(u"单个弹幕参数个数为5,%s"%",".join(sub))
                    return
                d = {}
                d["partid"] = partid
                d["date"] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                d["time"] = float(sub[0])
                d["txt"] = sub[1]
                d["mode"] = int(sub[2])
                d["color"] = int(sub[3])
                d["fontsize"] = int(sub[4])
                if int(sub[4])>100:
                    self.alert(u"字体太大了吧？")
                    return
                dl.append(d)
            self.js = { "protocol":"batchmsg","length":len(dl), "data":dl }
            self.js = json.dumps(self.js) + '\n'
        except Exception as what:
            self.alert(u"弹幕格式错误-%s"%what.__str__())
            return

        self.syntax = True

    def onSend(self,event):
        self.onCheck(event)
        if self.syntax:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            # negotiate using apikey
            apistr = '{"protocol":"apikey","apikey":"%s"}\n'%self.apikey
            s.send(apistr)
            data = s.recv(1024)
            j = json.loads(data)
            if j.has_key("ok"):
                #self.alert(u"登录成功",u"OK")
                pass
            else:
                #self.alert(data,u"Error")
                self.alert(u"无法认证，请检查APIKEY")
                return
            # send batch msg
            s.send(self.js)
            data = s.recv(1024)
            j = json.loads(data)
            if j.has_key("ok"):
                self.alert(j["ok"],u"OK")
            else:
                self.alert(data,u"OK")
            s.close()

if __name__ == "__main__":
        app = wx.PySimpleApp(0)
        wx.InitAllImageHandlers()
        dlg = FormDialog(None, -1, u"Avfun弹幕发射器")
        dlg.ShowModal()
        dlg.Destroy()
