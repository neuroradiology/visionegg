"""VisionEgg Core Library
"""

# Copyright (c) 2001, 2002 Andrew Straw.  Distributed under the terms
# of the GNU General Public License (GPL).

####################################################################
#
#        Import all the necessary packages
#
####################################################################

import string
__version__ = string.split('$Revision$')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__author__ = 'Andrew Straw <astraw@users.sourceforge.net>'

from VisionEgg import *                         # Vision Egg package

import pygame                                   # pygame handles OpenGL window setup
import pygame.locals
			                        # from PyOpenGL:
from OpenGL.GL import *                         #   main package
from OpenGL.GLU import *                        #   utility routines

from Numeric import * 				# Numeric Python package
from MLab import *                              # Matlab function imitation from Numeric Python

############# What function do we use to swap the buffers? ############
swap_buffers = pygame.display.flip

####################################################################
#
#        Screen
#
####################################################################

class Screen:
    """Contains one or more viewports.

    Currently only one screen is supported, but hopefully multiple
    screens will be supported in the future.

    """
    def __init__(self,
                 size=(config.VISIONEGG_SCREEN_W,
                       config.VISIONEGG_SCREEN_H),
                 fullscreen=config.VISIONEGG_FULLSCREEN,
                 preferred_bpp=config.VISIONEGG_PREFERRED_BPP,
                 bgcolor=config.VISIONEGG_SCREEN_BGCOLOR):
        self.size = size
        self.fullscreen = fullscreen 

        pygame.init()
        pygame.display.set_caption("Vision Egg")
        flags = pygame.locals.OPENGL | pygame.locals.DOUBLEBUF
        if self.fullscreen:
            flags = flags | pygame.locals.FULLSCREEN

        # Choose an appropriate framebuffer pixel representation
        try_bpps = [32,24,0] # bits per pixel (32 = 8 bits red, 8 green, 8 blue, 8 alpha, 0 = any)
        try_bpps.insert(0,preferred_bpp) # try the preferred size first

        if sys.platform=='linux2': # linux will report it can do 32 bpp, but fails on init
            try:
                while 1:
                    try_bpps.remove(32)
            except:
                pass
        
        found_mode = 0
        for bpp in try_bpps:
            modeList = pygame.display.list_modes( bpp, flags )
            if modeList == -1: # equal to -1 if any resolution will work
                found_mode = 1
            else:
                if len(modeList) == 0: # any resolution is OK
                    found_mode = 1
                else:
                    if self.size in modeList:
                        found_mode = 1
                    else:
                        self.size = modeList[0]
                        print "WARNING: Using %dx%d video mode instead of requested size."%(self.size[0],self.size[1])
            if found_mode:
                break
        if found_mode == 0:
            print "WARNING: Could not find acceptable video mode! Trying anyway..."

        print "Initializing graphics at %d x %d ( %d bpp )."%(self.size[0],self.size[1],bpp)
        try:
            pygame.display.set_mode(self.size, flags, bpp )
        except pygame.error, x:
            print "FATAL VISION EGG ERROR:",x
            sys.exit(1)
        self.bpp = pygame.display.Info().bitsize
        self.cursor_visible_func = pygame.mouse.set_visible
        if self.fullscreen:
            self.cursor_visible_func(0)

        self.parameters = Parameters()
        self.parameters.bgcolor = bgcolor

    def clear(self):
        c = self.parameters.bgcolor # Shorthand
        glClearColor(c[0],c[1],c[2],c[3])
        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)

    def make_current(self):
        """Makes screen active for drawing.

        Can not be implemented until multiple screens are possible."""
        pass

    def __del__(self):
        """Make sure mouse is visible after screen closed."""
        self.cursor_visible_func(1)
        
####################################################################
#
#        Viewport
#
####################################################################

class Viewport:
    """A portion of a screen which shows stimuli."""
    def __init__(self,screen,lower_left,size,projection=None):
        self.screen = screen
        self.stimuli = []
        self.lower_left = lower_left
        self.size = size

        if projection is None:
            projection = OrthographicProjection(left=lower_left[0],
                                                right=lower_left[0]+size[0],
                                                bottom=lower_left[1],
                                                top=lower_left[1]+size[1],
                                                z_clip_near=0.1,
                                                z_clip_far=100.0)            
        
        self.parameters = Parameters()
        self.parameters.projection = projection

    def add_stimulus(self,stimulus,draw_order=-1):
        """Add a stimulus to the list of those drawn in the viewport

        By default, the stimulus is drawn last, but this behavior
        can be changed with the draw_order argument.
        """
        if draw_order == -1:
            self.stimuli.append(stimulus)
        else:
            self.stimuli.insert(draw_order,stimulus)

    def remove_stimulus(self,stimulus):
        self.stimuli.remove(stimulus)

    def draw(self):
        """Set the viewport and draw stimuli."""
        self.screen.make_current()
        glViewport(self.lower_left[0],self.lower_left[1],self.size[0],self.size[1])

        self.parameters.projection.set_GL_projection_matrix()
        
        for stimulus in self.stimuli:
            stimulus.draw()

####################################################################
#
#        Projection and derived classes
#
####################################################################

class Projection:
    """Abstract base class to define interface for OpenGL projection matrices"""
    def __init__(self):
        raise RuntimeError("Trying to instantiate an abstract base class.")

    def set_GL_projection_matrix(self):
        """Set the OpenGL projection matrix, return to original matrix mode."""
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE) # Save the GL of the matrix state
        glMatrixMode(GL_PROJECTION) # Set OpenGL matrix state to modify the projection matrix
        glLoadMatrixf(self.parameters.matrix)
        if matrix_mode != GL_PROJECTION:
            glMatrixMode(matrix_mode) # Set the matrix mode back
    def translate(self,x,y,z):
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE) # Save the GL of the matrix state
        glMatrixMode(GL_PROJECTION) # Set OpenGL matrix state to modify the projection matrix
        glLoadMatrixf(self.parameters.matrix)
        glTranslatef(x,y,z)
        self.parameters.matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        if matrix_mode != GL_PROJECTION:
            glMatrixMode(matrix_mode) # Set the matrix mode back

class OrthographicProjection(Projection):
    """An orthographic projection"""
    def __init__(self,left=-1.0,right=1.0,bottom=-1.0,top=1.0,z_clip_near=0.1,z_clip_far=100.0):
        self.parameters = Parameters()
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE) # Save the GL of the matrix state
        glMatrixMode(GL_PROJECTION) # Set OpenGL matrix state to modify the projection matrix
        glLoadIdentity() # Clear the projection matrix
        glOrtho(left,right,bottom,top,z_clip_near,z_clip_far) # Let GL create a matrix and compose it
        self.parameters.matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        if matrix_mode != GL_PROJECTION:
            glMatrixMode(matrix_mode) # Set the matrix mode back

class SimplePerspectiveProjection(Projection):
    """A simplified perspective projection"""
    def __init__(self,fov_x=45.0,z_clip_near = 0.1,z_clip_far=100.0,aspect_ratio=4.0/3.0):
        self.parameters = Parameters()
        fov_y = fov_x / aspect_ratio
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE) # Save the GL of the matrix state
        glMatrixMode(GL_PROJECTION) # Set OpenGL matrix state to modify the projection matrix
        glLoadIdentity() # Clear the projection matrix
        gluPerspective(fov_y,aspect_ratio,z_clip_near,z_clip_far) # Let GLU create a matrix and compose it
        self.parameters.matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        if matrix_mode != GL_PROJECTION:
            glMatrixMode(matrix_mode) # Set the matrix mode back

class PerspectiveProjection(Projection):
    """A perspective projection"""
    def __init__(self,left,right,bottom,top,near,far):
        self.parameters = Parameters()
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE) # Save the GL of the matrix state
        glMatrixMode(GL_PROJECTION) # Set OpenGL matrix state to modify the projection matrix
        glLoadIdentity() # Clear the projection matrix
        glFrustrum(left,right,top,bottom,near,far) # Let GL create a matrix and compose it
        self.parameters.matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        if matrix_mode != GL_PROJECTION:
            glMatrixMode(matrix_mode) # Set the matrix mode back

####################################################################
#
#        Parameters
#
####################################################################

class Parameters:
    """Hold stimulus parameters.

    This abstraction of parameters is useful so that parameters can be
    controlled via any number of means: evaluating a python function,
    acquiring some data with a digital or analog input, etc.

    All parameters (such as contrast, position, etc.) which should be
    modifiable in runtime should be attributes of an instance of this
    class, which serves as a nameholder for just this purpose.

    See the Presentation class for more information about parameters
    and controllers.
    """
    pass

####################################################################
#
#        Stimulus - Base class
#
####################################################################

class Stimulus:
    """Base class for a stimulus.

    Use this class if your projection is associated with the viewport,
    which you normally want to do with 3D stimuli.  If your stimulus
    defines its own projection, use StimulusWithProjection instead.
    """
    def __init__(self):
        self.parameters = Parameters()
        
    def draw(self):
    	"""Draw the stimulus.  This method is called every frame.
    
        This method actually performs the OpenGL calls to draw the
        stimulus. In this base class, however, it does nothing."""
        pass
        
    def init_gl(self):
        """Get OpenGL ready to do everything in the draw() method.

        This method typically loads texture objects and creates
        display lists.  In this base class, however, it does nothing."""
        pass

####################################################################
#
#        FixationSpot
#
####################################################################

class FixationSpot(Stimulus):
    def __init__(self):
        self.parameters = Parameters()
        self.parameters.on = 1
        self.parameters.modelview_matrix = eye(4)
        self.parameters.projection_matrix = eye(4)
        self.parameters.size = 0.25
        self.parameters.color = (1.0,1.0,1.0,1.0)

    def init_gl(self):
        # impose our own measurement grid on the viewport
        viewport_aspect = 4.0/3.0 # guess for the default
        pseudo_width = 100.0
        pseudo_height = 100.0 / viewport_aspect
        (l,r,b,t) = (-0.5*pseudo_width,0.5*pseudo_width,-0.5*pseudo_height,0.5*pseudo_height)
        z_near = -1.0
        z_far = 1.0
        
        matrix_mode = glGetIntegerv(GL_MATRIX_MODE)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(l,r,b,t,z_near,z_far)
        self.parameters.projection_matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        glPopMatrix()

        glMatrixMode(matrix_mode)

    def draw(self):
        if self.parameters.on:
            # save current matrix mode
            matrix_mode = glGetIntegerv(GL_MATRIX_MODE)

            glMatrixMode(GL_MODELVIEW)
            glPushMatrix() # save the current modelview to the stack
            glLoadMatrixf(self.parameters.modelview_matrix) # set the modelview matrix

            # before we clear the projection matrix, save its state
            glMatrixMode(GL_PROJECTION) 
            glPushMatrix()
            glLoadMatrixf(self.parameters.projection_matrix) # set the projection matrix

            c = self.parameters.color
            glColor(c[0],c[1],c[2],c[3])
            glDisable(GL_TEXTURE_2D)

            # This could go in a display list to speed it up, but then
            # size wouldn't be dynamically adjustable this way.  Could
            # still use one of the matrices to make it change size.
            size = self.parameters.size
            glBegin(GL_QUADS)
            glVertex3f(-size,-size, 0.0);
            glVertex3f( size,-size, 0.0);
            glVertex3f( size, size, 0.0);
            glVertex3f(-size, size, 0.0);
            glEnd() # GL_QUADS
            glEnable(GL_TEXTURE_2D)

            glPopMatrix() # restore projection matrix

            glMatrixMode(GL_MODELVIEW)
            glPopMatrix() # restore modelview matrix

            glMatrixMode(matrix_mode)   # restore matrix state

####################################################################
#
#        Presentation
#
####################################################################

class Presentation:
    """Handles the timing and coordination of stimulus presentation.

    This class is the key to the real-time operation of the Vision
    Egg. It associates controllers with the parameters they control
    and updates the parameters.  A controller can be either realtime,
    which means it will be called once every frame, or transitional,
    which will be called before and after any stimulus presentations.
    A transitional controller is also called as frequently as possible
    between stimuli.

    There is no class named Controller that must be subclassed.
    Instead, any function which takes a single argument (the time
    elapsed since the start of a stimulus presentation) can be used as
    a controller.  (However, for a controller which can be used from a
    remote computer, see the PyroController class of the PyroHelpers
    module.)

    Please note that the term realtime here is a bit hopeful at this
    stage, because no OpenGL environment I know of can guarantee that
    a new frame is drawn and the double buffers swapped before the
    monitor's next vertical retrace sync pulse.  Still, although one
    can worry endlessly about this problem, it works.  In other words,
    on a fast computer with a fast graphics card running even a
    pre-emptive multi-tasking operating system (insert name of your
    favorite operating system here), a new frame is drawn before every
    vertical retrace sync pulse.
    """
    def __init__(self,viewports=[],duration_sec=5.0):
        self.parameters = Parameters()
        self.parameters.viewports = viewports
        self.parameters.duration_sec = duration_sec
        self.realtime_controllers = []
        self.transitional_controllers = []

    def add_realtime_controller(self, parameters, name, controller):
        if not isinstance(parameters,Parameters):
            raise ValueError('"%s" is not an instance of %s'%(parameters,Parameters))
        if not hasattr(parameters,name):
            raise AttributeError('"%s" not an attribute of %s'%(name,parameters))
        self.realtime_controllers.append((parameters,name,controller))

    def remove_realtime_controller(self, parameters, name):
        if not isinstance(parameters,Parameters):
            raise ValueError('"%s" is not an instance of %s'%(parameters,Parameters))
        if not hasattr(parameters,name):
            raise AttributeError('"%s" not an attribute of %s'%(name,parameters))
        i = 0
        while i < len(self.realtime_controllers):
            orig_parameters,orig_name,orig_controller = self.realtime_controllers[i]
            if orig_parameters == parameters and orig_name == name:
                del self.realtime_controllers[i]
            else:
                i = i + 1

    def add_transitional_controller(self, parameters, name, controller):
        if not isinstance(parameters,Parameters):
            raise ValueError('"%s" is not an instance of %s'%(parameters,Parameters))
        if not hasattr(parameters,name):
            raise AttributeError('"%s" not an attribute of %s'%(name,parameters))
        self.transitional_controllers.append((parameters,name,controller))

    def remove_transitional_controller(self, parameters, name):
        if not isinstance(parameters,Parameters):
            raise ValueError('"%s" is not an instance of %s'%(parameters,Parameters))
        if not hasattr(parameters,name):
            raise AttributeError('"%s" not an attribute of %s'%(name,parameters))
        i = 0
        while i < len(self.transitional_controllers):
            orig_parameters,orig_name,orig_controller = self.transitional_controllers[i]
            if orig_parameters == parameters and orig_name == name:
                del self.transitional_controllers[i]
            else:
                i = i + 1

    def go(self):
        """Main control loop during stimulus presentation.

        This is the heart of realtime control in the Vision Egg, and
        contains the main loop during a stimulus presentation.

        First, all controllers (realtime and transitional) are called
        and update their parameters for the start of the
        stimulus. Next, data acquisition is readied. Finally, the main
        loop is entered.

        In the main loop, the current stimulus-relative time is
        computed, the realtime controllers are called with this
        information, the screen is cleared, each viewport is drawn to
        the back buffer (while the video card continues painting the
        front buffer on the display), and the buffers are
        swapped. Unfortunately, there is no system independent way to
        synchronize buffer swapping with the vertical retrace period.
        It usually depends on your operating system, your video card,
        and your video drivers.  (This should be remedied in OpenGL 2.)
        """
        # First, make sure I have the most up to date parameters
        for parameters,name,controller in self.realtime_controllers:
            setattr(parameters,name,controller(0.0))
        for parameters,name,controller in self.transitional_controllers:
            setattr(parameters,name,controller(0.0))

        # Create a few shorthand notations, which speeds
        # the main loop by not performing name lookup each time.
        duration_sec = self.parameters.duration_sec 
        viewports = self.parameters.viewports

        # Get list of screens
        screens = []
        for viewport in viewports:
            if viewport.screen not in screens:
                screens.append(viewport.screen)

        # Still need to add DAQ hooks...
        
        start_time_absolute = timing_func()
        cur_time = 0.0
        while (cur_time <= duration_sec):
            # Update all the realtime parameters
            for parameters,name,controller in self.realtime_controllers:
                setattr(parameters,name,controller(cur_time))
            # Clear the screen(s)
            for screen in screens:
                screen.clear()
            # Draw each viewport
            for viewport in viewports:
                viewport.draw()
            swap_buffers()
            cur_time_absolute = timing_func()
            cur_time = cur_time_absolute-start_time_absolute
            
        self.between_presentations() # At least call once at end of stimulus

    def between_presentations(self):
        """Maintain display while between stimulus presentations.

        This function gets called as often as possible when not
        in the 'go' loop.

        To indicate to the controllers that a stimulus is not in
        progress, instead of passing a positive stimulus-relative
        time, it passes a negative value to the controller.
        Therefore, a controller should assume any negative time value
        means it is between stimulus presentations.

        It would be cleaner to have a separate parameter passed to the
        controller that indicates this status, but because the
        controller code is performance-critical, we'll just make do
        with this.

        Other than the difference in the time passed to the
        controllers, this routine is very similar to the inside of the
        main loop in the go method.
        """
        # For each controller, let it do its thing
        # Pass value of -1.0 to indicate between stimulus status
        #
        # This works by evaluating the function "controller" and
        # putting the results in parameters.name.
        # It's like "parameters.name = controller(-1.0)", but name is
        # a string, so it must be called this way.
        for parameters,name,controller in self.realtime_controllers:
            setattr(parameters,name,controller(-1.0))
        for parameters,name,controller in self.transitional_controllers:
            setattr(parameters,name,controller(-1.0))

        viewports = self.parameters.viewports

        # Get list of screens
        screens = []
        for viewport in viewports:
            if viewport.screen not in screens:
                screens.append(viewport.screen)
            
        # Clear the screen(s)
        for screen in screens:
            screen.clear()
        # Draw each viewport
        for viewport in viewports:
            viewport.draw()
        swap_buffers()

    def export_movie_go(self, frames_per_sec=12.0, filename_suffix=".tif", filename_base="visionegg_movie", path="."):
        """Call this method rather than go() to save a movie of your experiment.
        """
        import Image # Would be nice to import this above, but it breaks stuff!
        
        for parameters,name,controller in self.realtime_controllers:
            setattr(parameters,name,controller(0.0))
        for parameters,name,controller in self.transitional_controllers:
            setattr(parameters,name,controller(0.0))

        # Create a few shorthand notations, which speeds
        # the main loop by not performing name lookup each time.
        duration_sec = self.parameters.duration_sec 
        viewports = self.parameters.viewports

        # Get list of screens
        screens = []
        for viewport in viewports:
            if viewport.screen not in screens:
                screens.append(viewport.screen)

        if len(screens) > 1:
            raise EggError("Can only export movie of one screen")

        cur_time = 0.0
        image_no = 1
        while (cur_time <= duration_sec):
            # Update all the realtime parameters
            for parameters,name,controller in self.realtime_controllers:
                setattr(parameters,name,controller(cur_time))
            # Clear the screen(s)
            for screen in screens:
                screen.clear()
            # Draw each viewport
            for viewport in viewports:
                viewport.draw()
            swap_buffers()

            # Now save the contents of the framebuffer
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            framebuffer = glReadPixels(0,0,screen.size[0],screen.size[1],GL_RGB,GL_UNSIGNED_BYTE)
            fb_image = Image.fromstring('RGB',screen.size,framebuffer)
            fb_image = fb_image.transpose( Image.FLIP_TOP_BOTTOM )
            filename = "%s%04d%s"%(filename_base,image_no,filename_suffix)
            savepath = os.path.join( path, filename )
            print "Saving '%s'"%filename
            fb_image.save( savepath )
            image_no = image_no + 1
            cur_time = cur_time + 1.0/frames_per_sec
        
####################################################################
#
#        Error handling
#
####################################################################
    
class EggError(Exception):
    """Created whenever an exception happens in the Vision Egg package
    """
    def __init__(self,str):
        Exception.__init__(self,str)

