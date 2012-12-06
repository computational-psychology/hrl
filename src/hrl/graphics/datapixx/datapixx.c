#include <Python.h>
#include <libdpx.h>
#include <stdint.h>
#include <math.h>
#include <sched.h>
#include <time.h>

#include <stdio.h>
#include <string.h>
#include <GL/gl.h>
#include <GL/glx.h>
#include <GL/glu.h>
#include <GL/glxext.h>

#define GLX_GLXEXT_PROTOTYPES 1

#define pi      3.14159265358979323846264338327950288
#undef SQUARE


#define BWHITE  0x100000
#define BBLUE   BWHITE >>1
#define BGREEN  BWHITE >>2
#define BYELLOW BWHITE >>3
#define BRED    BWHITE >>4


extern int glXGetVideoSyncSGI(uint *);
extern int glXWaitVideoSyncSGI(int, int, unsigned int *);



typedef struct {
	PyObject_HEAD
//	additional variables;
} DpixxObject;

static PyObject *error;

staticforward PyTypeObject Dpixx_Type;


static char dpixx_open__doc__[]=
"open() -> dpixx handle\n"
"allocate descriptor for communication with the device";

static PyObject*
py_dpixx_open(PyObject* unused, PyObject* args)
{
	DpixxObject *self;
	int dinBuffAddr, dinBuffSize;
	int mypid, mysched;
	struct sched_param schedparam;

	mypid = getpid();
	schedparam.sched_priority = sched_get_priority_max(SCHED_RR);
	sched_setscheduler(0,SCHED_RR,&schedparam);

	mysched = sched_getscheduler(0);

	DPxOpen();

        if (DPxGetError() != DPX_SUCCESS) {
		PyErr_SetFromErrno(PyExc_ValueError);
		return NULL;
        }

	DPxSetVidMode(DPREG_VID_CTRL_MODE_C24); //straight passthrough

        DPxUpdateRegCache();

	if(DPxIsVidDviActive())
	{
		printf("Getting data over DVI\n");
		if(DPxIsVidOverClocked())
			printf("Input is overclocked!\n");
		else
			printf("Frequency is OK\n");

	} else {
		printf("No data over DVI\n");
	}

	// prepare respbox
        DPxSetDinDataDir(0x00FF0000);
        DPxEnableDinStabilize();
        DPxEnableDinDebounce();

        DPxEnableDinLogTimetags();
        DPxEnableDinLogEvents();
        dinBuffAddr     = 0x800000;
        dinBuffSize     = 0x400000;
        DPxSetDinBuff(dinBuffAddr, dinBuffSize);
        DPxUpdateRegCache();

	self = PyObject_New(DpixxObject, &Dpixx_Type);
	if (self == NULL){
		return NULL;
	}

	return (PyObject*)self;
}

static void
dpixx_dealloc(DpixxObject *self)
{
	//clean-up functions
	PyObject_Del(self);
}

static char Dpixx_close__doc__[]=
"close() stops all schedulers and finishes the work with the device\n";

static PyObject*
Dpixx_close(PyObject* unused, PyObject* args)
{
        DPxStopAllScheds();
        DPxUpdateRegCache();
        DPxClose();
        if (DPxGetError() != DPX_SUCCESS) {
                printf("ERROR: DATAPixx error = %d!\n", DPxGetError());
                PyErr_SetFromErrno(PyExc_ValueError);
                return NULL;
        }
	Py_INCREF(Py_None);
	return Py_None;
}

static char Dpixx_isReady__doc__[]=
"Returns non-0 if device has been successfully opened\n";

static PyObject*
Dpixx_isReady(PyObject* unused, PyObject* args)
{
	int res;
	res = DPxIsReady();
	return Py_BuildValue("i",res);
}

static char Dpixx_GetVidVFreq__doc__[]=
"Get video vertical frame rate in Hz\n";

static PyObject*
Dpixx_GetVidVFreq(PyObject* unused, PyObject* args)
{
	return Py_BuildValue("f",DPxGetVidVFreq());
}

static char Dpixx_SetVidMode__doc__[]=
"Set the video processing mode\n"
"vidMode is one of the following predefined constants:\n"
"DPREG_VID_CTRL_MODE_C24 Straight passthrough from DVI 8-bit\n"
"     (or HDMI \"deep\" 10/12-bit) RGB to VGA 8/10/12-bit RGB\n"
"DPREG_VID_CTRL_MODE_L48 DVI RED[7:0] is used as an index into\n"
"     a 256-entry 16-bit RGB colour lookup table\n" 
"DPREG_VID_CTRL_MODE_M16 DVI RED[7:0] & GREEN[7:0] concatenate into\n"
"     a VGA 16-bit value sent to all three RGB components\n"
"DPREG_VID_CTRL_MODE_C48 Even/Odd pixel RED/GREEN/BLUE[7:0] concatenate\n"
"     to generate 16-bit RGB components at half the horizontal resolution\n" 
"DPREG_VID_CTRL_MODE_L48D DVI RED[7:4] & GREEN[7:4] concatenate\n"
"     to form an 8-bit index into a 256-entry 16-bit RGB colour lookup table\n" 
"DPREG_VID_CTRL_MODE_M16D DVI RED[7:3] & GREEN[7:3] & BLUE[7:2] concatenate\n"
"     into a VGA 16-bit value sent to all three RGB components\n" 
"DPREG_VID_CTRL_MODE_C36D Even/Odd pixel RED/GREEN/BLUE[7:2] concatenate\n"
"     to generate 12-bit RGB components at half the horizontal resolution\n";


static PyObject*
Dpixx_SetVidMode(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	int vidMode;
        if (!PyArg_ParseTuple(args, "i", &vidMode))
		return NULL;

	DPxSetVidMode(vidMode);
        DPxUpdateRegCache();
	Py_INCREF(Py_None);
	return Py_None;
}

static char Dpixx_EnableVidVertStereo__doc__[]=
"Top/bottom halves of input image are output in two sequencial video frames.\n"
"VESA L/R output is set to 1 when first frame (left eye) is displayed,\n"
"and set to 0 when second frame (right eye) is displayed.\n";

static PyObject*
Dpixx_EnableVidVertStereo(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	printf("Vertical period in [ns]: %d\n",DPxGetVidVPeriod());
	DPxEnableVidVertStereo();
        DPxUpdateRegCache();
	Py_INCREF(Py_None);
	return Py_None;
}

static char Dpixx_DisableVidVertStereo__doc__[]=
"Switch to normal display mode without vertical stereo\n";

static PyObject*
Dpixx_DisableVidVertStereo(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
        DPxDisableVidVertStereo();
        DPxUpdateRegCache();
	Py_INCREF(Py_None);
        return Py_None;
}


int64_t timespecDiff(struct timespec *timeA_p, struct timespec *timeB_p)
{
  return ((timeA_p->tv_sec * 1000000000) + timeA_p->tv_nsec) -
           ((timeB_p->tv_sec * 1000000000) + timeB_p->tv_nsec);
}

static int GLXExtensionSupported(Display *dpy, const char *extension)
{
        const char *extensionsString, *pos;
        extensionsString = glXQueryExtensionsString(dpy, DefaultScreen(dpy));
        pos = strstr(extensionsString, extension);
        if (pos != NULL && (pos == extensionsString || pos[-1] == ' ') &&
            (pos[strlen(extension)] == ' ' || pos[strlen(extension)] == '\0'))
                return 1;
        return 0;
}


static char Dpixx_frametest__doc__[]=
"Function for testing LUT cycling on DataPixx\n";

static PyObject*
Dpixx_frametest(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	uint16_t *clutData1,*clutData2;
	uint16_t val;
	double fl_val;
	int i;
	int mypid, mysched;
	double inc,x;
	struct timespec start, stop;
	uint64_t timeElapsed;
	struct sched_param schedparam;
	struct timespec s;

	Display        *dpy;
 	int screen;
	int nDummy;
    	XVisualInfo          *pvi;
    	XSetWindowAttributes swa;
    	Window               winGL;
    	GLXContext context;
    	unsigned int retraceCount;

	// int64_t ust,msc,sbc;

        int attrib[] = { GLX_RGBA,
                     GLX_RED_SIZE, 1,
                     GLX_GREEN_SIZE, 1,
                     GLX_BLUE_SIZE, 1,
                     GLX_DOUBLEBUFFER,
                     GLX_DEPTH_SIZE, 1,
                     None };
	void (*swap_interval)();
	void (*glXGetSyncValuesOML)();

	glXGetSyncValuesOML = (void *)glXGetProcAddress((unsigned char *)"glXGetSyncValuesOML");

	if (!glXGetSyncValuesOML)
		printf("Sorry, unable to find glXGetSyncValuesOML()\n");

	swap_interval = glXGetProcAddress((unsigned char *)"glXSwapIntervalSGI");
	swap_interval(1);

    	dpy = XOpenDisplay (NULL);

    	screen = DefaultScreen (dpy);

    	if(!glXQueryExtension(dpy, &nDummy, &nDummy))
        	printf("Sorry, no glx-extention\n");

    	if(!GLXExtensionSupported(dpy, "GLX_SGI_video_sync"))
        	printf("Sorry, no GLX_SGI_video_sync available\n");

    	if(!GLXExtensionSupported(dpy, "GLX_OML_sync_control"))
        	printf("Sorry, no GLX_OML_sync_control available\n");


	// Choose a visual
	pvi=glXChooseVisual(dpy, DefaultScreen(dpy), attrib);
	if(pvi==NULL)
        	printf("Sorry, glXChooseVisual failed\n");

	pvi->screen = DefaultScreen(dpy); 

   	// Create the dummy OpenGL window
    	swa.colormap=XCreateColormap(dpy, RootWindow(dpy, pvi->screen), pvi->visual, AllocNone);
        swa.border_pixel = 0;
        swa.event_mask = ExposureMask | KeyPressMask | ButtonPressMask |
                StructureNotifyMask;


        winGL = XCreateWindow(dpy, RootWindow(dpy, pvi->screen),
                              0, 0,
                              1, 1,
                              0, pvi->depth, InputOutput, pvi->visual,
                              CWBorderPixel | CWColormap | CWEventMask, &swa);
        if (!winGL) {
                fprintf(stderr, "window creation failed\n");
        }

//    	winGL=XCreateWindow(dpy, RootWindow(dpy, pvi->screen), 0, 0, 1, 1, 0, pvi->depth,
//                InputOutput, pvi->visual, CWColormap, &swa);

	    // Create a GLX context
    	context=glXCreateContext(dpy, pvi, None, GL_TRUE);
    	if(context==NULL)
        	printf("Sorry, glXCreateContext failed\n");
    	// Make context current
    	glXMakeCurrent(dpy, winGL, context);

/*
    	for(i=0;i<133;i++)
    	{
            clock_gettime(CLOCK_MONOTONIC, &start);
            // Wait for vertical retrace
            glXGetVideoSyncSGI(&retraceCount);
            glXWaitVideoSyncSGI(2, (retraceCount+1)%2, &retraceCount);

            // Perform video output
            //printf("ping!\n");
            // Flush output buffer
            XFlush(dpy);
            clock_gettime(CLOCK_MONOTONIC, &stop);
    	}

    	timeElapsed = timespecDiff(&stop, &start);
	printf("duration: %f\n",(double)timeElapsed/1e9);
*/
	//XDestroyWindow(dpy, winGL);
	//glXDestroyContext(dpy, context);

	inc = pi/255;

	mypid = getpid();
	schedparam.sched_priority = sched_get_priority_max(SCHED_RR);
	sched_setscheduler(0,SCHED_RR,&schedparam);

	mysched = sched_getscheduler(0);
	printf("mypid: %d\tmysched: %d\n",mypid,mysched);


        clutData1 = malloc(768*sizeof(uint16_t));
	x = 0.0;
        for(i=3;i<768;i = i+3)
        {
		val = sin(x)*32768;

//
                fl_val = sin(x);
		//printf("fl_val: %lf\n",fl_val);
                fl_val = pow(fl_val,1/2.305);
                //val = (uint16_t)(round(fl_val*32768));
                val = (uint16_t)(round(fl_val*65535));
		//printf("val: %d\n",val);
//
		x += inc;
                clutData1[i] = 0;
                clutData1[i+1] = val;
                clutData1[i+2] = 0;
        }

        clutData2 = malloc(768*sizeof(uint16_t));
	x = 0.0;
        for(i=3;i<768;i = i+3)
        {
		val = (1-sin(x))*32768;
//
                fl_val = (1-sin(x));
                //printf("fl_val: %lf\n",fl_val);
                fl_val = pow(fl_val,1/2.305);
                //val = (uint16_t)(round(fl_val*32768));
                val = (uint16_t)(round(fl_val*65535));
                //printf("val: %d\n",val);
//
		x += inc;
                clutData2[i] = 0;
                clutData2[i+1] = val;
                clutData2[i+2] = 0;
        }
	clutData1[1] = (uint16_t)0;
#ifdef SQUARE
	clutData1[4] = (uint16_t)0; //black
	clutData1[601] = (uint16_t)13311; //white
	clutData1[361] = (uint16_t)12287; //some stable background
#endif
	clutData2[1] = (uint16_t)0;
#ifdef SQUARE
	clutData2[4] = (uint16_t)13311; //white
	clutData2[601] = (uint16_t)0; //black
	clutData2[361] = (uint16_t)12287; //some stable background
#endif

	printf("start\n");
	//s.tv_sec = 2;
	//s.tv_nsec = 0;
	s.tv_sec = 0;
	//s.tv_nsec = 7575757; //frame
	s.tv_nsec = 2759398; //half-frame
	//s.tv_nsec = (long)(1.0/DPxGetVidVFreq() * 1e9); //frame
	printf("framedelay: %ld\n",s.tv_nsec);

	//DPxUpdateRegCacheAfterVideoSync();
        DPxSetVidClut(clutData1);
	sleep(2);
        DPxSetVidClut(clutData2);
        DPxSetVidClut(clutData1);
	
	clock_gettime(CLOCK_MONOTONIC, &start);
	for(i=0;i<590;i++)
	//for(i=0;i<39000;i++)
	{
// works in 6 of 10 cases:
		glFinish();
            	glXGetVideoSyncSGI(&retraceCount);
            	glXWaitVideoSyncSGI(2, (retraceCount+1)%2, &retraceCount);
		//glXSwapBuffers(dpy, winGL);
		glFlush(); 
		glFinish();
		nanosleep(&s,NULL);
		//glXGetSyncValuesOML(dpy,winGL,&ust,&msc,&sbc);

                if(i & 1)
                        DPxSetVidClut(clutData1);
                else
                        DPxSetVidClut(clutData2);

	}
	clock_gettime(CLOCK_MONOTONIC, &stop);
	timeElapsed = timespecDiff(&stop, &start);
	printf("duration: %f\n",(double)timeElapsed/1e9);
        DPxSetVidClut(clutData2);
	Py_INCREF(Py_None);
	return Py_None;
}

static char Dpixx_SetVidClut__doc__[]=
"setVidClut(clut) -> None\n\n"
"Configure the Color Look-up-Table\n\n"
"For color output clut must have 768 values (256 values * 3 channels)\n" 
"and contain a sequence of R,G,B values, e.g. [R0,G0,B0,R1,G1,B1...]\n\n"
"For grayscale output clut must have 256 values representing the desired\n"
"intensities.\n\n"
"The values for both are integers in the range 0 .. 65535\n"
"Remember that the corresponding luminance range is not linear";


static PyObject*
Dpixx_SetVidClut(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
        int i,n;
	uint16_t val;
	uint16_t *clutData;	
	PyObject *tup;

        if (!PyArg_ParseTuple(args, "O", &tup))
                return NULL;

        clutData = malloc(768*sizeof(uint16_t));

	if (PyList_Size(tup) == 768) {
	  for(i=0;i<768;i++)
	    {
	      clutData[i] = PyInt_AsLong(PyList_GetItem(tup,i));
	    }
	} else if (PyList_Size(tup) == 256) {
	  n = 0;
	  for(i=0;i<768;i = i+3)
	    {
	      val = PyInt_AsLong(PyList_GetItem(tup,n));
	      clutData[i] = val;
	      clutData[i+1] = val;
	      clutData[i+2] = val;
	      n++;
	    }

        } else {
	  Py_INCREF(PyExc_ValueError);
	  PyErr_SetString(PyExc_ValueError, "CLUT length must be 256 or 768");
	  Py_INCREF(Py_None);
	  return Py_None;
	}


        DPxSetVidClut(clutData);
        DPxUpdateRegCache();
	Py_INCREF(Py_None);
	return Py_None;
}



static char Dpixx_blink__doc__[]=
"blink(buttons, delay=1.0) -> None\n\n"
"Makes a blink with the ResponseBox\n\n"
"buttons is one or more button numbers (combined with OR)\n"
"delay is optional and is specified in seconds. The timing is not precise\n";

static PyObject*
Dpixx_blink(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	int keynum;
	double delay = 1.0;

	if (!PyArg_ParseTuple(args, "i|d", &keynum, &delay))
        	return NULL;
	

        DPxSetDinDataDir(0x00FF0000);
	DPxSetDinDataOut(keynum);

        DPxUpdateRegCache();
        sleep(delay);
        DPxSetDinDataOut(0);
        DPxUpdateRegCache();

	Py_INCREF(Py_None);
	return Py_None;
}

static char Dpixx_configLights__doc__[]=
"configLights(buttons) -> None\n\n"
"Enables the selected lights on the Responce Box\n"
"buttons is one or more button numbers (combined with OR)\n"
"Without parameters will switch everything off\n";

static PyObject*
Dpixx_configLights(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	int keynum = 0x000000;

	if (!PyArg_ParseTuple(args, "|i", &keynum))
        	return NULL;
	

        DPxSetDinDataDir(0x00FF0000);
	DPxSetDinDataOut(keynum);
        DPxUpdateRegCache();

	Py_INCREF(Py_None);
	return Py_None;
}


static char Dpixx_waitButton__doc__[]=
"waitButton(delay) -> (button, reaktion time)\n\n" 
"Waits for input from ResponseBox for the given amount of time in seconds\n"
"Without any parameters this function will wait for a week for new input\n\n"
"Returns a tuple with button number and reaction time or None if nothing\n"
"was pressed\n";

static PyObject*
Dpixx_waitButton(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	short rxBuff[5];     
	int dinBuffAddr, dinBuffSize;
	int keyDown;
        double startTime;
        double my_reactionTime, my_timetag;
	uint32_t my_ttl,my_tth;
	double delay = 604800.0; // one week :-)

        dinBuffAddr = 0x800000;
        dinBuffSize = 0x400000;

        // Wait until all keys are up
        do {
        	DPxUpdateRegCache();
        } while ((DPxGetDinValue() & 0xffff) != 0xffff);

        // Get rid of any old keypress data
        DPxSetDinBuff(dinBuffAddr, dinBuffSize);
        DPxUpdateRegCache();
	
	if (DPxGetDinBuffWriteAddr() != dinBuffAddr)
	  printf("Address mismatch\n");

	PyArg_ParseTuple(args, "|d", &delay);

        startTime = DPxGetTime();
        do {
		DPxUpdateRegCache();
                if (DPxGetDinBuffWriteAddr() != dinBuffAddr)
                	break;
           } while (DPxGetTime() - startTime < delay);


        // Read the keydown from memory

        // If they didn't hit a key, it's a fail
	if (DPxGetDinBuffWriteAddr() == dinBuffAddr)
	{
	  Py_INCREF(Py_None);
	  return Py_None;
	}

        DPxReadRam(dinBuffAddr, 10, rxBuff);
        keyDown = ~rxBuff[4];

	my_ttl = *(uint32_t*)(rxBuff + 0);
	my_tth = *(uint32_t*)(rxBuff + 2);


	my_timetag = (4294967296.0 * my_tth + my_ttl) / 1.0e9;
        my_reactionTime = my_timetag - startTime;

        // Get rid of any old keypress data
        DPxSetDinBuff(dinBuffAddr, dinBuffSize);
        DPxUpdateRegCache();

	return Py_BuildValue("if",keyDown,my_reactionTime);
}


static char Dpixx_readButton__doc__[]=
"readButton() -> (button, reaction time)\n\n"
"Reads button and reaction time from ResponseBox since last call\n" 
"of this function. The first call is needed for initialisation\n"
"This function is a bit faster than waitButton(0). For example,\n"
"You can use it to check for button events in every frame\n\n"
"Returns a tuple with button number and reaction time or None\n"
"if nothing was pressed\n";

double start_time = 0.0;

static PyObject*
Dpixx_readButton(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
	short rxBuff[5];     
	int dinBuffAddr, dinBuffSize;
	int keyDown;
        double my_reactionTime, my_timetag;
	uint32_t my_ttl,my_tth;

        DPxReadRam(dinBuffAddr, 10, rxBuff);
        keyDown = ~rxBuff[4];

	my_ttl = *(uint32_t*)(rxBuff + 0);
	my_tth = *(uint32_t*)(rxBuff + 2);

	my_timetag = (4294967296.0 * my_tth + my_ttl) / 1.0e9;

        my_reactionTime = my_timetag - start_time;

        DPxSetDinBuff(dinBuffAddr, dinBuffSize);
        DPxUpdateRegCache();

	if (start_time == 0.0) {
	  Py_INCREF(Py_None);
	  start_time = DPxGetTime();
	  return Py_None;
	}

	start_time = DPxGetTime();

	if (my_reactionTime < 0)
	{
	  Py_INCREF(Py_None);
	  return Py_None;
	} else {
	  return Py_BuildValue("if",keyDown,my_reactionTime);
	}
}

static char Dpixx_beep__doc__[]=
"Makes a short beep with DataPixx\n";

static PyObject*
Dpixx_beep(DpixxObject *self, PyObject *args, PyObject* kwargs)
{
        short txBuff[256];      // Big enough to hold 1 period of audio waveform
        int i;



        DPxInitAudCodec();
        DPxSetAudLRMode(DPXREG_AUD_CTRL_LRMODE_MONO);                   // Single audio datum goes to both the Left/Right ears
        DPxSetAudBuff(0, 64);                                                                   
        for (i = 0; i < 32; i++)                                                                // Fill up the audio buffer 
                txBuff[i] = 32767.0 * sin(2.0 * pi * i / 32.0);
        DPxWriteRam(0, 64, txBuff);                                                             // Write the local audio buffer 
        DPxSetAudVolume(0.6);                                                                             

        // All register configuration up until now has been cached locally.
        // DPxUpdateRegCache() transmits the register writes over USB to the DATAPixx.
        DPxUpdateRegCache();

        DPxSetAudBuff(0, 64);           // Specify address and size of our audio buffer
        DPxSetAudSched(0, 40000, DPXREG_SCHED_CTRL_RATE_HZ, 16000);
        DPxStartAudSched();

        DPxUpdateRegCache();


        sleep(1);
        DPxStopAudSched();
        //DPxSetDinDataOut(0);
        DPxUpdateRegCache();


	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef Dpixx_methods[] = {
	{"beep",	(PyCFunction)Dpixx_beep,	
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_beep__doc__},
	{"setVidMode",	(PyCFunction)Dpixx_SetVidMode,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_SetVidMode__doc__},
	{"enableVidVertStereo",	(PyCFunction)Dpixx_EnableVidVertStereo,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_EnableVidVertStereo__doc__},
	{"disableVidVertStereo",	(PyCFunction)Dpixx_DisableVidVertStereo,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_DisableVidVertStereo__doc__},
	{"frametest",	(PyCFunction)Dpixx_frametest,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_frametest__doc__},
	{"setVidClut",	(PyCFunction)Dpixx_SetVidClut,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_SetVidClut__doc__},
	{"configLights",	(PyCFunction)Dpixx_configLights,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_configLights__doc__},
	{"blink",	(PyCFunction)Dpixx_blink,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_blink__doc__},
	{"close",	(PyCFunction)Dpixx_close,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_close__doc__},
	{"getVidVFreq",	(PyCFunction)Dpixx_GetVidVFreq,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_GetVidVFreq__doc__},
	{"isReady",	(PyCFunction)Dpixx_isReady,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_isReady__doc__},
	{"readButton",	(PyCFunction)Dpixx_readButton,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_readButton__doc__},
	{"waitButton",	(PyCFunction)Dpixx_waitButton,
	 METH_KEYWORDS|METH_VARARGS,	Dpixx_waitButton__doc__},
	{NULL,		NULL}		/* sentinel */
};

static PyObject *
Dpixx_getattr(PyObject *self, char *name)
{
	return Py_FindMethod(Dpixx_methods, self, name);
}

static char Dpixx_doc[] = 
	"Device handle class for interaction with DataPixx hardware";

static PyTypeObject Dpixx_Type = {
	PyObject_HEAD_INIT(NULL)
	0,				/* ob_size           */
	"datapixx.Dpixx",      		/* tp_name           */
	sizeof(DpixxObject),		/* tp_basicsize      */
	0,				/* tp_itemsize       */
	(destructor)dpixx_dealloc,	/* tp_dealloc        */
	0,				/* tp_print          */
	(getattrfunc)Dpixx_getattr,	/* tp_getattr        */
	0,				/* tp_setattr        */
	0,				/* tp_compare        */
	0,				/* tp_repr           */
	0,				/* tp_as_number      */
	0,				/* tp_as_sequence    */
	0,				/* tp_as_mapping     */
	0,				/* tp_hash           */
	0,				/* tp_call           */
	0,				/* tp_str            */
	0,				/* tp_getattro       */
	0,				/* tp_setattro       */
	0,				/* tp_as_buffer      */
	Py_TPFLAGS_DEFAULT,		/* tp_flags          */
	Dpixx_doc,			/* tp_doc            */
	0,				/* tp_traverse       */
	0,				/* tp_clear          */
	0,				/* tp_richcompare    */
	0,				/* tp_weaklistoffset */
	0,				/* tp_iter           */
	0,				/* tp_iternext       */
	Dpixx_methods,	     		/* tp_methods        */
	0,			/* tp_members        */
	0,				/* tp_getset         */
	0,				/* tp_base           */
	0,				/* tp_dict           */
	0,				/* tp_descr_get      */
	0,				/* tp_descr_set      */
	0,				/* tp_dictoffset     */
	0,		/* tp_init           */
};


/* statichere PyTypeObject Dpixx_Type = { */
/* 	PyObject_HEAD_INIT(NULL) */
/* 	0,			/\*ob_size*\/ */
/* 	"Dpixx",		/\*tp_name*\/ */
/* 	sizeof(DpixxObject),	/\*tp_basicsize*\/ */
/* 	0,			/\*tp_itemsize*\/ */
/* 	/\* methods *\/ */
/* 	(destructor)dpixx_dealloc, /\*tp_dealloc*\/ */
/* 	0,			/\*tp_print*\/ */
/* 	(getattrfunc)Dpixx_getattr, /\*tp_getattr*\/ */
/* 	0,			/\*tp_setattr*\/ */
/* 	0,			/\*tp_compare*\/ */
/* 	0,			/\*tp_repr*\/ */
/* 	0,			/\*tp_as_number*\/ */
/* 	0,			/\*tp_as_sequence*\/ */
/* 	0,			/\*tp_as_mapping*\/ */
/* 	0,			/\*tp_hash*\/ */
/* }; */



static PyMethodDef dpixx_methods[] = {
	{"open",	py_dpixx_open,
	 METH_VARARGS,	dpixx_open__doc__},
	{NULL,		NULL}		/* sentinel */
};

static char __doc__[]=
"The datapixx module provides an interface to the DATAPixx device.";

DL_EXPORT(void)
initdatapixx(void)
{
	PyObject *m, *d;
	PyMethodDef *def;

	Dpixx_Type.tp_new = PyType_GenericNew;
	if (PyType_Ready(&Dpixx_Type) < 0)
		return;

	Dpixx_Type.ob_type = &PyType_Type;

	/* Create the module and add the functions */
	m = Py_InitModule4("datapixx", dpixx_methods, __doc__, 
			   NULL, PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	error = PyErr_NewException("dpixx.error", PyExc_ValueError, NULL);
	PyDict_SetItemString(d, "error", error);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_C24", DPREG_VID_CTRL_MODE_C24);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_L48", DPREG_VID_CTRL_MODE_L48);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_M16", DPREG_VID_CTRL_MODE_M16);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_C48", DPREG_VID_CTRL_MODE_C48);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_L48D", DPREG_VID_CTRL_MODE_L48D);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_M16D", DPREG_VID_CTRL_MODE_M16D);
	PyModule_AddIntConstant(m, "DPREG_VID_CTRL_MODE_C36D", DPREG_VID_CTRL_MODE_C36D);

	PyModule_AddIntConstant(m, "BWHITE", BWHITE);
	PyModule_AddIntConstant(m, "BGREEN", BGREEN);
	PyModule_AddIntConstant(m, "BBLUE", BBLUE);
	PyModule_AddIntConstant(m, "BRED", BRED);
	PyModule_AddIntConstant(m, "BYELLOW", BYELLOW);

	/* add class Dpixx */
	PyObject *classDict = PyDict_New();
	PyObject *className = PyString_FromString("Dpixx");
	PyObject *fooClass = PyClass_New(NULL, classDict, className);
	PyDict_SetItemString(d, "Dpixx", fooClass);
	Py_DECREF(classDict);
	Py_DECREF(className);
	Py_DECREF(fooClass);
    
	/* add methods to class */
	for (def = Dpixx_methods; def->ml_name != NULL; def++) {
	  PyObject *func = PyCFunction_New(def, NULL);
	  PyObject *method = PyMethod_New(func, NULL, fooClass);
	  PyDict_SetItemString(classDict, def->ml_name, method);
	  Py_DECREF(func);
	  Py_DECREF(method);
	}

	/* add our Dpixx type */
	Py_INCREF(&Dpixx_Type);
	PyModule_AddObject(m, "Dpixx", (PyObject *)&Dpixx_Type);


}


