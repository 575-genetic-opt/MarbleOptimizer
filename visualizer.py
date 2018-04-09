import wx
import os
import sys
import visualizer
import csv

from load_stl import loader
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

from OpenGLContext.arrays import *
from PIL import Image
import struct
import matplotlib
matplotlib.use('WXAgg')

translate = 0.01
zoom = 0.0
rotx = 0.15
translate_mode = False
canvas1 = None
canvas2 = None
canvases = []

linked_draw = False

xPos = 0.0
yPos = 0.0
scaling = 0.025
xRot = -90.0
yRot = -30.0
zRot = -45.0
deltaRotX = 0.0
deltaRotY = 0.0
deltaRotZ = 0.0

centerpoint = [0.0, 0.0, 0.0]

AccumulatedRotation = []

CurrentView = []

Views = [None, None, None, None, None, None]


class MyCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        global canvases, linked_draw
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        self.context = glcanvas.GLContext(self)

        self.id = 0

        self.colors = [0, 1, 0, 1, 0, 0, 0, 0, 1]
        self.vertices = [0.0, 2.0, 0.0, 0.0, -1.0, 2.0, -1.5, -1.0, -1.0]
        self.indices = [0, 1, 2]
        self.dif_colors = [0, 1, 0, 1, 0, 0, 0, 0, 1]
        self.outlines_colors = [0, 0, 0, 0, 0, 0, 0, 0, 0]


        # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)

        canvases.append(self)

    def OnEraseBackground(self, event):
        pass  # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        wx.CallAfter(self.DoSetViewport)
        event.Skip()

    def DoSetViewport(self):
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnMouseUp(self, evt):
        self.ReleaseMouse()

    def OnRightDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnRightUp(self, evt):
        self.ReleaseMouse()

    def OnMouseMotion(self, evt):
        global translate_mode
        global xRot, yRot, zRot, slider1x, slider1y
        global xPos, yPos, scaling
        global translate
        global deltaRotX, deltaRotY, deltaRotZ

        if evt.Dragging():
            if evt.RightIsDown():
                translate_mode = True
            elif evt.LeftIsDown():
                translate_mode = False
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()

            size = self.GetClientSize()
            w, h = size
            w = max(w, 1.0)
            h = max(h, 1.0)
            xScale = 180.0 / w
            yScale = 180.0 / h

            if translate_mode:
                xPos += (self.x - self.lastx) * translate
                yPos += (self.y - self.lasty) * translate * -1
            elif self.y < (h / 10.0):
                deltaRotZ += (self.x - self.lastx) * xScale * -1
            else:
                deltaRotX += (self.y - self.lasty) * yScale
                deltaRotY += (self.x - self.lastx) * xScale

            if linked_draw:
                i = 1
                for canvas in canvases:
                    canvas.lastx, canvas.lasty = self.lastx, self.lasty
                    canvas.x, canvas.y = self.x, self.y
                    canvas.Refresh(False)
                    i += 1
            else:
                self.Refresh(False)

    def OnWheel(self, evt):
        global zoom
        global scaling
        amt = evt.GetWheelRotation()
        units = amt / (-(evt.GetWheelDelta()))
        scaling += units / 80.0
        if scaling < 0:
            scaling = 0

        self.Refresh()
        if linked_draw:
            for canvas in canvases:
                canvas.Refresh(False)
        else:
            self.Refresh(False)

    def saveView(self, view_idx):
        global xPos, yPos, scaling, AccumulatedRotation
        global CurrentView, Views

        CurrentView = [xPos, yPos, scaling, AccumulatedRotation]  # may need to add params for gluLookAt
        Views[view_idx] = CurrentView
        print "Save view"

    def setView(self, view_idx):
        global xPos, yPos, scaling, AccumulatedRotation
        global CurrentView

        if Views[view_idx] is not None:
            xPos = Views[view_idx][0]
            yPos = Views[view_idx][1]
            scaling = Views[view_idx][2]
            AccumulatedRotation = Views[view_idx][3]
            print "Set view"
        else:
            print "No view saved for this button"


        self.Refresh(False)

    def screenshot(self):
        size = self.GetClientSize()
        w, h = size
        data = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)

        image = Image.frombytes("RGB", (w, h), data)
        image2 = image.transpose(Image.FLIP_TOP_BOTTOM)
        image2.save('C:\Users\Chris\Documents\RepoOfAwesomeness\Temp\image' + str(self.id) + '.eps', 'EPS')
        print "screenshot done"


class Model1Canvas(MyCanvasBase):

    def InitGL(self):
        # global vbo
        global shader
        global AccumulatedRotation

        print "initgl"
        # set viewing projection
        glMatrixMode(GL_PROJECTION)  # now on the PROJECTION matrix stack, for setting up projection screen
        glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 40.0)  # (left, right, bottom, top, near, far)

        # position viewer
        glMatrixMode(GL_MODELVIEW)  # now on the MODELVIEW matrix stack, affects both MODEL and VIEW (same-ish)
        glEnable(GL_DEPTH_TEST)

        glLoadIdentity()
        AccumulatedRotation = glGetFloatv(GL_MODELVIEW_MATRIX)

        glClearColor(0.3, 0.3, 0.4, 0.0)    # background color
        self.color_list = [[1.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 0.0]
                           ]

        self.parts = []
        self.models = []
        self.information = []

        self.det_centerpoint()

        self.load_model(self.p_list, self.p_loc, self.r_list)


        print self.model_center

        # part_name = 'vw_3.stl'
        # scale1 = 1.0
        #
        # # get information
        # self.read_csv()
        #
        # parts = self.information[0]
        # locations = self.information[1]
        # rotations = self.information[2]
        #
        # i = 0
        # for part in parts:
        #     if part == 0.0:
        #         name = 't-bc.stl'   # part 2, t-b.stl is horizontal
        #     elif part == 1.0:
        #         name = 't-1c.stl'   # part 1, t-1.stl is macaroni up
        #     elif part == 2.0:
        #         name = '1-3c.stl'   # part 3, 1-3.stl is vertical
        #     elif part == 3.0:
        #         name = '1-4c.stl'   # part 4, 1-4.stl is macaroni in plane
        #     elif part == 4.0:
        #         name = '1-bc.stl'   # part 5, 1-b.stl is macaroni down
        #
        #     pos = [j * 10 * scale1 for j in [-locations[i*3], locations[i*3+2], locations[i*3+1]]]
        #
        #     # rot1 = [0, 0, 0]
        #     # rot2 = [0, 180, 0]
        #     # rot3 = [0, 90, 0]
        #     # rot4 = [0, 270, 0]
        #
        #     rot = [0, rotations[i]*90 - 90, 0]
        #
        #     self.get_stl(name, pos, rot, scale1)
        #
        #     i += 1

        self.init_shading()

    def read_csv(self):
        with open('good_design.csv', 'r') as f:
            reader = csv.reader(f)

            for row in reader:
                # print row
                next_row = []
                for item in row:
                    next_row.append(float(item))
                self.information.append(next_row)
        print self.information

    def set_model(self, p_list, p_loc, r_list):
        self.p_list = p_list
        self.p_loc = p_loc
        self.r_list = r_list

    def load_model(self, p_list, p_loc, r_list):
        print "loading model"

        # part_name = 'vw_3.stl'
        scale1 = 2.0

        # get information
        # self.read_csv()

        parts = p_list
        locations = p_loc
        rotations = r_list

        i = 0
        for part in parts:
            if part == 0:
                name = 't-bc.stl'  # part 2, t-b.stl is horizontal
            elif part == 1:
                name = 't-1c.stl'  # part 1, t-1.stl is macaroni up
            elif part == 2:
                name = '1-3c.stl'  # part 3, 1-3.stl is vertical
            elif part == 3:
                name = '1-4c.stl'  # part 4, 1-4.stl is macaroni in plane
            elif part == 4:
                name = '1-bc.stl'  # part 5, 1-b.stl is macaroni down
            # print name
            # print part

            # pos = [j * 10 * scale1 for j in [-locations[i * 3], locations[i * 3 + 2], locations[i * 3 + 1]]]
            pos = [-locations[i][0], locations[i][2], locations[i][1]]  # set up position
            pos = [pos[0] - self.model_center[0], pos[1] - self.model_center[1],
                   pos[2] - self.model_center[2]]   # move each piece to be relative to center
            # print pos
            pos = [j * 10 * scale1 for j in pos]    # scale each piece

            rot = [0, rotations[i] * 90 - 90, 0]  # rot1 = [0, 0, 0], rot2 = [0, 180, 0], rot3 = [0, 90, 0], rot4 = [0, 270, 0]

            index = random.randint(0, len(self.color_list))
            color = self.color_list[index]
            self.get_stl(name, pos, rot, scale1, color)

            i += 1
        print "model loaded"

    def det_centerpoint(self):

        locations = self.p_loc
        average_location = [0.0, 0.0, 0.0]
        for location in locations:
            average_location[0] += -location[0]
            average_location[2] += location[1]
            average_location[1] += location[2]
        length = len(locations)
        average_location[0] /= length
        average_location[2] /= length
        average_location[1] /= length

        print average_location
        self.model_center = average_location

    def get_stl(self, model_name, pos, rot, scale, color):
        model = loader()
        model.model = []  # for some reason new instance of loader has model information from last instance??

        try:
            model.load_stl(os.path.abspath('') + '/' + model_name)
        except:
            print "didn't work"
        self.models.append(model)
        self.assemble_part_list(model, pos, rot, scale, color)

    def assemble_part_list(self, model, pos, rot, scale, color):
        self.parts.append([model, pos, rot, scale, color])

    def BindTheBuffers(self):
        # global vertices, colors, indices
        # global outlines_colors

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glBindBuffer(GL_ARRAY_BUFFER, self.buffers[0])
        glBufferData(GL_ARRAY_BUFFER,
                     len(self.vertices) * 4,
                     (ctypes.c_float * len(self.vertices))(*self.vertices),
                     GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.buffers[1])
        glBufferData(GL_ARRAY_BUFFER,
                     len(self.colors) * 4,
                     (ctypes.c_float * len(self.colors))(*self.colors),
                     GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffers[2])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                     len(self.indices) * 4,  # byte size
                     (ctypes.c_uint * len(self.indices))(*self.indices),
                     GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.buffers[3])
        glBufferData(GL_ARRAY_BUFFER,
                     len(self.outlines_colors) * 4,
                     (ctypes.c_float * len(self.outlines_colors))(*self.outlines_colors),
                     GL_STATIC_DRAW)

    def init_shading(self):
        glShadeModel(GL_SMOOTH)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        # glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        # glLight(GL_LIGHT0, GL_POSITION, (0, 0, -100, 0))
        # glLight(GL_LIGHT0, GL_AMBIENT, (.3, .7, .7, 1.0))
        # glLight(GL_LIGHT0, GL_DIFFUSE, (0.5,0.5,0.5, 0.5))

        glLight(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0))
        glLight(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0))
        glLight(GL_LIGHT0, GL_AMBIENT, (1.0, 1.0, 1.0))

        glEnable(GL_LIGHT1)
        glLight(GL_LIGHT1, GL_POSITION, (0, 0, 10, 0))
        glLight(GL_LIGHT1, GL_SPECULAR, (1.0, 1.0, 1.0))
        # glLight(GL_LIGHT0, GL_AMBIENT, (.7,.5,.3,1))
        glMatrixMode(GL_MODELVIEW)

    def OnDraw(self):
        global translate, translate_mode
        global zoom
        global xPos, yPos, scaling, xRot, yRot, zRot
        # global vertices, colors, indices
        global centerpoint
        global AccumulatedRotation
        # global vbo
        global deltaRotX, deltaRotY, deltaRotZ

        # self.SetCurrent(self.context)
        self.context.SetCurrent(self)
        # print "begin context1"
        # print self.context

        # clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        gluLookAt(0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)  # initial point we look at (eye coords, center, up dir)

        # CENTERPOINT MARKER
        glPushMatrix()
        self.CenterpointMarker()
        glPopMatrix()

        # Apply initial transformations
        glTranslatef(xPos, yPos, 0.0)   # this translate is for panning (the last transformation OpenGL will perform (besides the gluLookAt)

        # DO ROTATIONS
        glPushMatrix()  # Set aside the previous matrix
        glLoadIdentity()    # Load an identity matrix (we call it Current Rotation)

        # Apply the rotations to Current Rotation (not absolute, but deltas)
        glRotatef(deltaRotX, 1.0, 0.0, 0.0)
        glRotatef(deltaRotY, 0.0, 1.0, 0.0)
        glRotatef(deltaRotZ, 0.0, 0.0, 1.0)

        # Reset the deltas (or rotations will compound)
        deltaRotX = 0
        deltaRotY = 0
        deltaRotZ = 0

        glMultMatrixf(AccumulatedRotation)  # Multiply Current Rotation by the accumulated rotation matrix
        AccumulatedRotation = glGetFloatv(GL_MODELVIEW_MATRIX)  # store the current result as Accumulated Rotation

        glPopMatrix()   # Get back the first matrix we set aside earlier

        glMultMatrixf(AccumulatedRotation)  # multiply the first matrix by Accumulated Rotation matrix

        # Translate the object so its centerpoint rests on origin (OpenGL will apply this before the rotaitons)
        glScalef(scaling, scaling, scaling)  # scale is essentially our zoom function (First transformation OpenGL will perform)
        glTranslatef(-centerpoint[0], -centerpoint[1], -centerpoint[2])

        # Start drawing

        # glMaterial(GL_FRONT, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
        # glMaterial(GL_FRONT, GL_SHININESS, (0.8, 0.8, 0.8, 1.0))
        # glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,
        #              (1.0, 1.0, 1.0));
        # glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 128);

        # draw marble coaster
        i = 1.0
        current_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        if self.parts is not empty:

            for model in self.parts:
                glPushMatrix()
                glLoadIdentity()
                # glColorMaterial(GL_FRONT, GL_DIFFUSE)
                # index = random.randint(0,len(self.color_list))
                # glColor(model[4])
                glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, model[4])
                # glEnable(GL_COLOR_MATERIAL)
                glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, model[4])
                glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, model[4])
                glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 50);
                             #              (1.0, 1.0, 1.0));
                glMultMatrixf(current_matrix)

                glTranslatef(model[1][0], model[1][1], model[1][2])

                glRotatef(model[2][0], 1.0, 0.0, 0.0)
                glRotatef(model[2][1], 0.0, 1.0, 0.0)
                glRotatef(model[2][2], 0.0, 0.0, 1.0)

                glScale(model[3], model[3], model[3])
                model[0].draw()
                i += 3.0
                # glDisable(GL_COLOR_MATERIAL)
                glPopMatrix()

        self.SwapBuffers()

    def CenterpointMarker(self):
        z_position = -0
        glBegin(GL_TRIANGLES)  # http://pyopengl.sourceforge.net/documentation/manual-3.0/glBegin.html

        glColor3f(0.0, 0.0, 0.5)
        glVertex3f(0.0, 0.0, 0.0 + z_position)
        glVertex3f(0.0, 0.25, -1.0 + z_position)
        glVertex3f(0.5, 0.0, -1.0 + z_position)

        glColor3f(0.0, 0.5, 0.0)
        glVertex3f(0.0, 0.0, 0.0 + z_position)
        glVertex3f(0.0, 0.25, -1.0 + z_position)
        glVertex3f(-0.5, 0.0, -1.0 + z_position)

        glColor3f(0.5, 0.5, 0.5)
        glVertex3f(0.0, 0.0, 0.0 + z_position)
        glVertex3f(0.5, 0.0, -1.0 + z_position)
        glVertex3f(-0.5, 0.0, -1.0 + z_position)

        glColor3f(0.5, 0.5, 0.0)
        glVertex3f(0.0, 0.25, -1.0 + z_position)
        glVertex3f(0.5, 0.0, -1.0 + z_position)
        glVertex3f(-0.5, 0.0, -1.0 + z_position)
        glEnd()



