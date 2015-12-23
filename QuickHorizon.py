try:
    from Tkinter import *
except ImportError:
    from tkinter import *

from PIL import Image, ImageTk
import sys
import os
import math
import csv
import tkFileDialog
import tkMessageBox

import tkSimpleDialog

import logging

####################################################################
# AzimuthWheelDialog
####################################################################
class GridDialog(tkSimpleDialog.Dialog):

    def __init__(self,parent,title=None,center=(0,0),radius=0):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent
        self.center = center
        self.radius = radius

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):

        Label(master, text="X:").grid(row=0)
        Label(master, text="Y:").grid(row=1)
        Label(master, text="Radius:").grid(row=2)

        c1 = StringVar()
        self.e1 = Entry(master, textvariable=c1)
        c1.set(str(self.center[0]))

        c2 = StringVar()
        self.e2 = Entry(master, textvariable=c2)
        c2.set(str(self.center[1]))

        r = StringVar()
        self.e3 = Entry(master, textvariable=r)
        r.set(str(self.radius))

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)

        return self.e1    

    def apply(self):

        X = self.e1.get()
        Y = self.e2.get()
        R = self.e3.get()

        self.center = (int(X), int(Y))
        self.radius = int(R)
        self.result = True

####################################################################
# FieldAzimuth Dialog (green line)
####################################################################
class AzimuthDialog(tkSimpleDialog.Dialog):

    def __init__(self,parent,title=None,center=(0,0),azimuth=-1):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent
        self.center = center
        self.azimuth = azimuth

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):

        Label(master, text="Grid Center X:").grid(row=0)
        Label(master, text="Grid Center Y:").grid(row=1)
        Label(master, text="Field Azimuth:").grid(row=2)

        c1 = StringVar()
        self.e1 = Entry(master, textvariable=c1, state=DISABLED)
        c1.set(str(self.center[0]))

        c2 = StringVar()
        self.e2 = Entry(master, textvariable=c2, state=DISABLED)
        c2.set(str(self.center[1]))

        r = StringVar()
        self.e3 = Entry(master, textvariable=r)
        r.set(str(self.azimuth))

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)

        return self.e1    

    def apply(self):

        A = self.e3.get()
        self.azimuth = int(A)


####################################################################
# Main functions
####################################################################
class LoadImageApp:

    button_1 = "up"        
    tool = "move"          
    xold, yold = None, None
    viewport = (0,0)       # Used for zoom and pan
    zoomcycle = 0          
    MIN_ZOOM = -10
    MAX_ZOOM = 30
    raw_image = None       
    zoomed_image = None    
    showGrid = False


    # list of digitized dots.  Columns contain X, Y, Elevation, Az

    dots = []

    ####################################################################
    # Function: __init__
    ####################################################################
    def __init__(self,root,image_file):

        self.parent = root
        self.frame = Frame(root,bg='white')
        self.imageFile = image_file

        
        # zoom
        self.mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.mux[n] = round(self.mux[n-1] * 1.5, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.mux[n] = round(self.mux[n+1] * 1.5, 5)

        # Create canvas 
        self.canvas = Canvas(self.frame,width=800,height=600,bg='white')

        # Create the image on canvas
        if image_file:
            self.init_canvas(self.canvas,image_file)

        self.frame.pack(fill='both', expand=1)
        self.canvas.pack(fill='both', expand=1)

        #file types 
        self.file_opt = options = {}
        options['defaultextension'] = '.gif'
        options['filetypes'] = [('all files', '.*'),
                                ('ppm files', '.ppm'),
                                ('pgm files', '.pgm'),
                                ('gif files', '.gif'),
                                ('jpg files', '.jpg'),
                                ('jpeg files', '.jpeg')]
        options['initialdir'] = '.'

        # Importing csv file 
        self.csv_opt = csv_options = {}
        csv_options['defaultextension'] = '.csv'
        csv_options['filetypes'] = [('all files', '.*'),
                                ('csv files', '.csv')]
        csv_options['initialdir'] = '.'

        # Menu items
        menubar = Menu(root)
        filemenu = Menu(menubar,tearoff=0)
        filemenu.add_command(label="Open Image", command=self.open_file)
        filemenu.add_command(label="Export CSV", command=self.save_csv)
        filemenu.add_command(label="Import CSV", command=self.open_csv)
        filemenu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=filemenu)

        drawmenu = Menu(menubar,tearoff=0)
        drawmenu.add_command(label="Position", command=self.move)
        drawmenu.add_command(label="Digitize", command=self.dot)
        drawmenu.add_command(label="Display Info", command=self.show_dots)
        drawmenu.add_command(label="Delete", command=self.select)
        
        #drawmenu.add_command(label="Draw Line", command=self.line)
        menubar.add_cascade(label="Tools", menu=drawmenu)

        gridmenu = Menu(menubar, tearoff=0)
        gridmenu.add_command(label="Show Azimuth Wheel", command=self.show_grid)
        gridmenu.add_command(label="Hide Azimuth Wheel", command=self.hide_grid)
        gridmenu.add_command(label="Enter Field Azimuth", command=self.define_azimuth)
        menubar.add_cascade(label="Azimuth",menu=gridmenu)

        zoommenu = Menu(menubar, tearoff=0)
        zoommenu.add_command(label="Zoom In", command=self.zoomin)
        zoommenu.add_command(label="Zoom Out", command=self.zoomout)
        menubar.add_cascade(label="Zoom",menu=zoommenu)

        # Attach menu bar to interface
        root.config(menu=menubar)

        # Show XY coords in in bottom left 
        self.status = Label(root, text="X,Y", bd=1, relief=SUNKEN, anchor=W)
        self.status.pack(side=BOTTOM, fill=X)

        # Events 
        self.canvas.bind("<MouseWheel>",self.zoomer)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<ButtonPress-1>", self.b1down)
        self.canvas.bind("<ButtonRelease-1>", self.b1up)
        self.canvas.bind("<Configure>", self.resize_window)

    ####################################################################
    # Canvas and Image File
    ####################################################################
    def init_canvas(self, canvas, image_file):

        # Reset when a new image opened
        self.button_1 = "up"
        self.tool = "move"
        self.xold, self.yold = None, None
        self.viewport = (0,0)
        self.zoomcycle = 0
        self.showGrid = False

        del self.dots[:]

        if image_file:

            self.imageFile = image_file
            self.raw_image = Image.open(image_file)
            (width, height) = self.raw_image.size

            # Image larger than 1000 pixels, resize to 800 x 600
            if width > 1000 or height > 1000:
                self.raw_image.thumbnail((800,600),Image.ANTIALIAS)
                (width, height) = self.raw_image.size
                print "Downsizing image to ", width, "x", height

            self.zoomed_image = self.raw_image

            # Save reference to the image object in order to show it
            self.p_img = ImageTk.PhotoImage(self.raw_image)

            # Change size of canvas to new width and height 
            canvas.config(width=width, height=height)

            # Remove all canvas items
            canvas.delete("all")
            canvas.create_image(0,0,image=self.p_img, anchor="nw")

            # Find default center of image and radius
            self.center = (int(width/2), int(height/2))
            self.radius = int(math.sqrt(self.center[0] * self.center[0] + self.center[1] * self.center[1]))
            self.field_azimuth = -1

    def to_raw(self,(x,y)):

        # Translate the x,y coordinate from window to raw image coordinate
        (vx, vy) = self.viewport
        return (int((x + vx)/ self.mux[self.zoomcycle]),int((y + vy)/ self.mux[self.zoomcycle]))

    def to_window(self, (x,y)):
        
        # Translate the x,y coordinate from raw image coordinate to window coordinate
        (vx, vy) = self.viewport
        return (int(x * self.mux[self.zoomcycle]) - vx,int(y * self.mux[self.zoomcycle]) - vy)

    def drawDots(self, my_canvas):

        rows = len(self.dots)
        for row in xrange(rows):

            dot = self.dots[row]

            (x,y) = self.to_window((dot[0],dot[1]))
            item = my_canvas.create_oval(x-2,y-2,x+2,y+2,fill="blue")
            my_canvas.itemconfig(item, tags=("dot", str(dot[0]), str(dot[1])))

    def drawGrid(self, my_canvas, center, radius):

        # Remove old grid before drawing new one
        my_canvas.delete("grid")

        (wX,wY) = self.to_window(center)
        wR = radius * self.mux[self.zoomcycle]

        x = wX - wR
        y = wY - wR

        my_canvas.create_oval(x,y,x+(2*wR),y+(2*wR),outline="red",tag="grid")

        # Draw spokes on Az wheel 
        for n in range(15,365,15):
            rX = center[0] + int(radius * math.cos(math.radians(n)))
            rY = center[1] + int(radius * math.sin(math.radians(n)))
            pX,pY = self.to_window((rX,rY))
            my_canvas.create_line(wX,wY,pX,pY,fill="red",tag="grid")

    def drawAzimuth(self, my_canvas, center, radius, azimuth):
     
        if azimuth >= 0 and azimuth <= 360:
            my_canvas.delete("azimuth")

            (wX,wY) = self.to_window(center)

            # Draw field azimuth
            rX = center[0] + int(radius * math.cos(math.radians(azimuth)))
            rY = center[1] + int(radius * math.sin(math.radians(azimuth)))
            pX,pY = self.to_window((rX,rY))
            my_canvas.create_line(wX,wY,pX,pY, tag="azimuth", fill="green", width=2)


    def scale_image(self):

        # Resize image 
        raw_x, raw_y = self.raw_image.size
        new_w, new_h = int(raw_x * self.mux[self.zoomcycle]), int(raw_y * self.mux[self.zoomcycle])
        self.zoomed_image = self.raw_image.resize((new_w,new_h), Image.ANTIALIAS)

    def display_region(self, my_canvas):

        my_canvas.delete("all")

        # Display the region of the zoomed image starting at viewport and window size
        (x,y) = self.viewport
        w,h = self.frame.winfo_width(), self.frame.winfo_height()

        tmp = self.zoomed_image.crop((x,y,x+w,y+h))

        self.p_img = ImageTk.PhotoImage(tmp)
        my_canvas.config(bg="white")
        my_canvas.create_image(0,0,image=self.p_img, anchor="nw")

        # Draw  saved dots
        if self.dots:
            self.drawDots(my_canvas)

        if self.showGrid:
            self.drawGrid(my_canvas, self.center, self.radius)
            self.drawAzimuth(my_canvas, self.center, self.radius, self.field_azimuth)

    ########################################################
    # Menu options
    ########################################################

    def open_file(self):
        file = tkFileDialog.askopenfilename(**self.file_opt)

        if file:
            # Initialize the canvas with an image file
            self.init_canvas(self.canvas,file)

        else:
            logging.info('No file selected')

    def open_csv(self):

        # Open a CSV file with previous XY coordinates
        file = tkFileDialog.askopenfilename(**self.csv_opt)

        if file:

            # Delete  existing dots from canvas and data 
            self.canvas.delete("dot")
            del self.dots[:]

            # start canvas with image file
            f = open(file,'rt')
            try:
                reader = csv.reader(f)
                rownum = 0

                for row in reader:

                    
                    if rownum == 0:
                        header = row
                        
                    else:
                        self.dots.append((int(row[0]),int(row[1])))
                    rownum += 1
            finally:
                f.close()

            self.drawDots(self.canvas)
        else:
            logging.info('No file selected')

    def save_csv(self):

        # Save the dots to CSV file
        if self.dots:
            f_name = tkFileDialog.asksaveasfile(mode='wt', defaultextension=".csv")
            if f_name:
                try:
                    writer = csv.writer(f_name)

                    writer.writerow(('X', 'Y', 'Horizon', 'Azimuth'))

                    rows = len(self.dots)
                    for row in xrange(rows):
                        writer.writerow(self.dots[row])

                finally:
                    f_name.close()

    def exit_app(self):
        sys.exit(0)

    def move(self):
        self.tool = "move"

    def select(self):
        self.tool = "select"

    def show_dots(self):
       tkMessageBox.showinfo("Dot Info", self.print_dots())

    def print_dots(self):

        text = "X , Y = "

        rows = len(self.dots)
        for row in xrange(rows):
            i = self.dots[row]

            text = text + "(" + str(i[0]) + " , " + str(i[1]) + "), "

        return text

    def show_grid(self):

        # Get x,y coords and radius for of wheel 
        if self.raw_image:

            d = GridDialog(self.parent, title="Wheel Preferences", center=self.center, radius=self.radius)

            print "D = ", d, self.showGrid, d.result

            if d:
                self.center = d.center
                self.radius = d.radius
                if not self.showGrid:
                    self.showGrid = d.result

                if self.showGrid:
                    self.drawGrid(self.canvas, d.center, d.radius)

    def hide_grid(self):
        if self.raw_image:
            self.showGrid = False
            self.canvas.delete("grid")

    def define_azimuth(self):

        if self.raw_image and self.showGrid:

            d = AzimuthDialog(self.parent, title="Azimuth Preferences", center=self.center, azimuth=self.field_azimuth)
            if d:
                self.field_azimuth = d.azimuth
                self.drawAzimuth(self.canvas, self.center, self.radius, self.field_azimuth)
                self.azimuth_calculation(self.center, self.radius, self.field_azimuth)

    def dot(self):
        if self.raw_image:
            self.tool = "dot"

    def line(self):
        if self.raw_image:
            self.tool = "line"

    def zoomin(self):
        if self.raw_image:
            if self.zoomcycle < self.MAX_ZOOM:
                self.zoomcycle += 1
                self.scale_image()
                self.display_region(self.canvas)
            else:
                print "Max zoom reached!"

    def zoomout(self):
        if self.raw_image:
            if self.zoomcycle > self.MIN_ZOOM:
                self.zoomcycle -= 1
                self.scale_image()
                self.display_region(self.canvas)
            else:
                print "Min zoom reached!"

    #######################################################
    # Mouse options
    #######################################################

    def zoomer(self,event):

        

        # Zoom image and update viewport based on mouse position
        if self.raw_image:
            (x,y) = self.to_raw((event.x,event.y))

            if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
                self.zoomcycle += 1
            elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
                self.zoomcycle -= 1
            else:
                logging.info('Max/Min zoom reached!')
                return

            self.scale_image()

            self.viewport = (int(x * self.mux[self.zoomcycle]) - x, int(y * self.mux[self.zoomcycle]) - y)
            self.display_region(self.canvas)

    def b1down(self,event):

        
        if self.raw_image:
            if self.tool is "dot":

                item = event.widget.create_oval(event.x-2,event.y-2,event.x+2,event.y+2,fill="blue")

                # Save dots 
                raw = self.to_raw((event.x,event.y))
                event.widget.itemconfig(item, tags=("dot", str(raw[0]), str(raw[1])))

                # Only calcualte horizon elevation and azimuth if field azimuth and grid are defined! 
                if self.showGrid and self.field_azimuth >= 0 and self.field_azimuth <= 360:

                    rX = self.center[0] + int(self.radius * math.cos(math.radians(self.field_azimuth)))
                    rY = self.center[1] + int(self.radius * math.sin(math.radians(self.field_azimuth)))

                    azimuth = self.find_angle(self.center, (rX,rY), (raw[0], raw[1]))

                    
                    dot_radius = math.sqrt(math.pow(raw[0]-self.center[0],2)+math.pow(raw[1]-self.center[1],2))
                    
                    horizon = self.find_horizon(dot_radius, self.radius)
                    logging.info('Dot (%d,%d) has Horizon Elevation = %f, Azimuth = %f', raw[0], raw[1], horizon, azimuth)

                    new_dot = [raw[0], raw[1], round(horizon,5), round(azimuth,5)]
                    self.dots.append(new_dot)

                else:
                    self.dots.append(raw)
            else:
                self.select_X, self.select_Y = event.x, event.y
                self.button_1 = "down"

    def b1up(self,event):

        
        if not self.raw_image:
            return

        self.button_1 = "up"
        self.xold = None            
        self.yold = None

        # Delete the selection 
        if self.tool is "select":
            items = event.widget.find_enclosed(self.select_X, self.select_Y, event.x, event.y)

            # Delete the rectangle 
            rect = event.widget.find_withtag("selection_rectangle")
            if rect:
                event.widget.delete(rect)

            found_dots = {}     # Stores dot coords as value

            for i in items:

                # Change colour of the selected dots to red
                event.widget.itemconfig(i,fill="red")

                tags = event.widget.gettags(i)
                

                if tags[0] == "dot":
                    found_dots[i] = (int(tags[1]),int(tags[2]))       

            # Dialog to confirm deletion
            if found_dots:
                result = tkMessageBox.askokcancel("Confirm deletion?","Press OK to delete selected dots")

                
                if result:
                    # Delete the selected dots and remove from list
                    for i,coords in found_dots.items():
                        

                        rows = len(self.dots)
                        for row in xrange(rows):
                            dot = self.dots[row]

                            if coords[0] == dot[0] and coords[1] == dot[1]:
                                self.dots.remove(dot)
                                break

                        event.widget.delete(i)

                else: # Option to cancel deletion 
                    logging.info('Deletion cancelled')

                    # Change colour of dot back to blue if cancelled
                    for i in found_dots.keys():
                        event.widget.itemconfig(i,fill="blue")

    # Handles mouse events
    def motion(self,event):

        # Only do anything if left button is clicked 
        if self.raw_image and self.button_1 == "down":
            if self.xold is not None and self.yold is not None:

                
                if self.tool is "line":
                    
                    event.widget.create_line(self.xold,self.yold,event.x,event.y,smooth=TRUE,fill="blue",width=5)
                    
                    # Panning
                elif self.tool is "move":     
                    
                        self.viewport = (self.viewport[0] - (event.x - self.xold), self.viewport[1] - (event.y - self.yold))
                        self.display_region(self.canvas)

                elif self.tool is "select":
                    # Draw a dotted rectangle for deletion
                    rect = event.widget.find_withtag("selection_rectangle")
                    if rect:
                        event.widget.delete(rect)
                    event.widget.create_rectangle(self.select_X,self.select_Y,event.x,event.y,fill="",dash=(4,2),tag="selection_rectangle")

            self.xold = event.x
            self.yold = event.y

        # Status bar will show coordinates
        (rX,rY) = self.to_raw((event.x,event.y))
        str = "(", rX , ",", rY, ")"
        self.status.config(text=str)

    def resize_window(self, event):
        if self.zoomed_image:
            self.display_region(self.canvas)

    def azimuth_calculation(self, center, radius, azimuth):

        

        if azimuth >= 0 and azimuth <= 360:

            rX = center[0] + int(radius * math.cos(math.radians(azimuth)))
            rY = center[1] + int(radius * math.sin(math.radians(azimuth)))

            # Calculate horizon elevation and azimuth for each point, add to list
            new_dots = []

            rows = len(self.dots)
            for row in xrange(rows):
                dot = self.dots.pop()

                azimuth = self.find_angle(center, (rX,rY), (dot[0], dot[1]))

                
                dot_radius = math.sqrt(math.pow(dot[0]-center[0],2)+math.pow(dot[1]-center[1],2))
                
                horizon = self.find_horizon(dot_radius, radius)
                

                new_dot = [dot[0], dot[1], round(horizon,5), round(azimuth,5)]
                new_dots.append(new_dot)

            self.dots = new_dots

    def find_angle(self, C, P2, P3):

        angle = math.atan2(P2[1]-C[1], P2[0]-C[0]) - math.atan2(P3[1]-C[1], P3[0]-C[0])
        angle_in_degree = math.degrees(angle)

        if angle_in_degree < 0:
            angle_in_degree += 360

        return angle_in_degree

    def find_horizon(self, dot_radius, grid_radius):
        
        # Enter total field of view of Sunex camera (based on lens/camera model)
        camera = 185   

        # Calculate Horizon Elevation
        elev = (camera/2) - ((dot_radius/grid_radius) * (camera/2))
        
        # Adjust horizon elevation using calibration polynomial
        return ((-0.00003 * (elev * elev)) + (1.0317 * (elev)) - 2.4902)

# Main Program 

if __name__ == '__main__':
    root = Tk()
    root.title("QuickHorizon")
    image_file = None


    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            image_file = sys.argv[1]
            
        else:
            exit_string = "Image File " + sys.argv[1] + " doesn't exist!"
            sys.exit(exit_string)

    
    App = LoadImageApp(root,image_file)

    root.mainloop()
