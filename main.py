import wx
import visualizer
try:
    from wx import glcanvas

    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False

class ButtonPanel(wx.Panel):
    global canvases
    def __init__(self, parent):     # parent is the frame from runTest
        wx.Panel.__init__(self, parent, -1)

        box = wx.BoxSizer(wx.VERTICAL)

        # btn_draw = wx.Button(self, 10, "Sync'd Draw")
        # btn_draw = wx.ToggleButton(self, 10, "Sync'd Draw")
        # box6.Add(btn_draw, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # self.Bind(wx.EVT_BUTTON, self.SyncDraw, btn_draw)
        # self.Bind(wx.EVT_TOGGLEBUTTON, self.SyncDraw, btn_draw)

        # With this enabled, you see how you can put a GLCanvas on the wx.Panel
        if 1:
            self.context1 = visualizer.Model1Canvas(self)
            self.context1.SetMinSize((400, 400))
            box.Add(self.context1, 3, wx.ALL | wx.BOTTOM | wx.GROW, 5)

        btn_load = wx.Button(self,10,"Load CSV")
        self.Bind(wx.EVT_BUTTON, self.load_csv, btn_load)
        box.Add(btn_load, 0, wx.ALIGN_CENTER, 2)

        self.SetAutoLayout(True)
        self.SetSizer(box)

        self.csv_counter = 1

    def load_csv(self, evt):
        self.context1.read_csv()
        self.context1.choose_model(self.csv_counter)
        self.context1.load_model()
        self.csv_counter += 1

    def OnButton(self, evt):
        if not haveGLCanvas:
            dlg = wx.MessageDialog(self,
                                   'The GLCanvas class has not been included with this build of wxPython!',
                                   'Sorry', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        elif not haveOpenGL:
            dlg = wx.MessageDialog(self,
                                   'The OpenGL package was not found.  You can get it at\n'
                                   'http://PyOpenGL.sourceforge.net/',
                                   'Sorry', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            canvasClassName = 'Model1Canvas'
            canvasClass = eval(canvasClassName)
            cx = 0
            if canvasClassName == 'ConeCanvas':
                cx = 400
                # print "Making a Cone"
            frame = wx.Frame(None, -1, canvasClassName, size=(400, 400), pos=(cx, 400))
            canvasClass(frame)  # CubeCanvas(frame) or ConeCanvas(frame); frame passed to MyCanvasBase
            frame.Show(True)


# ----------------------------------------------------------------------
class RunDemoApp(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        frame = wx.Frame(None, -1, "RapidVizDemo: ", pos=(0, 0),
                     style=wx.DEFAULT_FRAME_STYLE, name="run a sample")
        # frame.CreateStatusBar()

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        item = menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Exit demo")
        self.Bind(wx.EVT_MENU, self.OnExitApp, item)
        menuBar.Append(menu, "&File")

        frame.SetMenuBar(menuBar)
        frame.Show(True)
        frame.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        win = runTest(frame)    # win is a panel objext (ButtonPanel, to be precise)

        # set the frame to a good size for showing the two buttons
        frame.SetSize((600, 600))
        win.SetFocus()  # sets panel to accept keyboard input
        self.window = win
        frect = frame.GetRect()

        self.SetTopWindow(frame)    # tells app what the top window is
        self.frame = frame
        return True

    def OnExitApp(self, evt):
        self.frame.Close(True)

    def OnCloseFrame(self, evt):
        if hasattr(self, "window") and hasattr(self.window, "ShutdownDemo"):
            self.window.ShutdownDemo()
        evt.Skip()


def runTest(frame):
    win = ButtonPanel(frame)
    return win

def beginGUI(p_list, p_loc, r_list):
    app = RunDemoApp()
    print "in gui"
    # app.window.context1.load_model(p_list, p_loc, r_list)
    openGLcanvas = app.window.context1
    openGLcanvas.set_model(p_list, p_loc, r_list)
    app.MainLoop()


# app = RunDemoApp()
# app.MainLoop()
