from tkinter import *
from point.point.telescope_control import LST
from point.point.nexstar import NexStar
import datetime
from threading import Thread


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master

        self.port = "COM7"
        self.active = False
        self.aligned = False
        self.location = [47.3686498, 8.5391825]
        #################
        #Init mount button
        #################
        self.active_frame = LabelFrame(self.master, text='Initialize mount')
        self.active_var = StringVar()
        self.active_var.set('OFF')
        self.activation_button = Button(self.active_frame, textvariable=self.active_var,
                                        command=self.init_mount, bg='firebrick2')
        self.activation_button.grid(column=0, row=0)
        self.active = False

        ################
        # Info frame
        #################
        self.info_frame = Frame(self.master)
        ################
        # Display Current RA/DEC
        #################
        self.current_radec_var = StringVar()
        self.current_radec_var.set("RA: 0.0, DEC: 90.0")
        self.current_radec_label = Label(self.info_frame, textvariable=self.current_radec_var)
        self.current_radec_label.grid(column=0, row=0)
        ################
        # Display Sidereal time
        #################

        self.sidereal_var = StringVar()
        self.update_LST()
        self.sidereal_label = Label(self.info_frame, textvariable=self.sidereal_var)
        self.sidereal_label.grid(column=0, row=1)
        self.lst_thread = Thread(target=self.update_LST)
        self.lst_thread.start()

        self.sync_zenith_button = Button(self.info_frame, text="Sync Zenith", command=self.sync_zenith)
        self.sync_zenith_button.grid(column=1, row=1)
        #####################
        # Arrow panel
        #####################
        self.arrow_frame = LabelFrame(self.master, text="Slew")

        self.slewing = False
        self.slewing_ax = None
        self.slewrate_var = StringVar()
        self.slewrate_var.set('1000')
        self.slewrate_entry = Entry(self.arrow_frame, textvariable=self.slewrate_var, width=10)
        #self.slewrate_entry.grid()
        self.slewrate_entry.bind("<Return>", self.set_slewrate)

        self.ra_up_btn = Button(self.arrow_frame, text='RA +', command=lambda: self.slew('ra', 1))
        self.ra_down_btn = Button(self.arrow_frame, text='RA -', command=lambda: self.slew('ra', -1))

        self.dec_up_btn = Button(self.arrow_frame, text='DEC +', command=lambda: self.slew('dec', 1))
        self.dec_down_btn = Button(self.arrow_frame, text='DEC -', command=lambda: self.slew('dec', -1))

        self.ra_up_btn.grid(column=0, row=1)
        self.ra_down_btn.grid(column=2, row=1)
        self.dec_up_btn.grid(column=1, row=0)
        self.dec_down_btn.grid(column=1, row=2)
        self.slewrate_entry.grid(column=1, row=1)

        ##############################
        # GOTO RA DEC
        ##############################
        self.goto_frame = LabelFrame(self.master, text="Goto RA/DEC")
        self.rago_var = StringVar()
        self.rago_var.set("0.")
        self.decgo_var = StringVar()
        self.decgo_var.set("90.0")
        self.rago_lab = Label(self.goto_frame, text="RA: ")
        self.decgo_lab = Label(self.goto_frame, text="DEC: ")
        self.rago_entry = Entry(self.goto_frame, textvariable=self.rago_var, width=10)
        self.decgo_entry = Entry(self.goto_frame, textvariable=self.decgo_var, width=10)

        self.go_btn = Button(self.goto_frame, text="Go!", command=self.goto_radec)
        self.abortgo_btn = Button(self.goto_frame, text="Abort", command=self.abortgoto_radec)

        self.rago_lab.grid(column=0, row=0)
        self.decgo_lab.grid(column=0, row=1)
        self.rago_entry.grid(column=1, row=0)
        self.decgo_entry.grid(column=1, row=1)
        self.go_btn.grid(column=2, row=0)
        self.abortgo_btn.grid(column=2, row=1)


    def LST(self):
        """
        Calculates local sidereal time based on location
        """
        t_utc = datetime.datetime.utcnow()
        YY = t_utc.year
        MM = t_utc.month
        DD = t_utc.day
        UT = t_utc.hour + (t_utc.minute/60)
        JD = (367*YY) - int((7*(YY+int((MM+9)/12)))/4) + int((275*MM)/9) + DD + 1721013.5 + (UT/24)
        GMST = 18.697374558 + 24.06570982441908*(JD - 2451545)
        GMST = GMST % 24
        Long = self.location[0]/15      #Convert longitude to hours
        LST = GMST+Long     #Fraction LST. If negative we want to add 24...
        if LST < 0:
            LST = LST +24

        LSTmm = (LST - int(LST))*60          #convert fraction hours to minutes
        LSTss = (LSTmm - int(LSTmm))*60      #convert fractional minutes to seconds
        LSThh = int(LST)
        LSTmm = int(LSTmm)
        LSTss = int(LSTss)

        return LST*15

    def sync_time_location(self):
        self.cgx.set_location(lat=self.location[0], lon=self.location[1])
        # set time
        self.cgx.set_time()
        print(self.cgx.get_radec(), self.cgx.get_location(), self.cgx.get_time())
        return

    def goto_radec(self):
        if self.aligned == False:
            print("not aligned!")
            return
        ra_go = float(self.rago_var.get())
        dec_go = float(self.decgo_var.get())
        try:
            assert (abs(ra_go) <= 180 and abs(dec_go) < 90)
        except AssertionError:
            print("Invalid RA or DEC")
            return
        self.cgx.goto_radec(ra=ra_go, dec=dec_go)

    def abortgoto_radec(self):
        self.cgx.cancel_goto()
        self.after(1000, self.update_RADEC)
        return



    def slew(self, ax, s):
        if self.slewing:
            rate = 0
            #self.cgx.slew_var(self.slewing_ax, rate)
            print("stop slewing %s"%self.slewing_ax)
            self.slewing = False
        else:
            self.slewing = True
            self.slewing_ax = ax
            rate = abs(int(self.slewrate_var.get()))
            try:
                assert rate < 16000
            except AssertionError:
                return
            print("slewing %s with rate %i" % (self.slewing_ax, s*rate))
            #self.cgx.slew_var(self.slewing_ax, s*rate)
        return



    def set_slewrate(self, e):
        print(self.slewrate_var.get())


    def init_mount(self):
        if self.active:
            self.active = False
            self.activation_button.config(bg='firebrick2')
            self.active_var.set('OFF')
        else:
            self.active = True
            print("Initializing CGX-L mount...")
            try:
                self.cgx = NexStar(device=self.port)
                print(self.cgx)
            except Exception as e:
                print(e)
                return
            self.sync_time_location()
            self.activation_button.config(bg='PaleGreen2')
            self.active_var.set('ON')
        return

    def update_LST(self):
        lst = self.LST()/15
        LSTmm = (lst - int(lst)) * 60  # convert fraction hours to minutes
        LSTss = (LSTmm - int(LSTmm)) * 60  # convert fractional minutes to seconds
        LSThh = int(lst)
        LSTmm = int(LSTmm)
        LSTss = int(LSTss)
        self.sidereal_var.set('\nLocal Sidereal Time %s:%s:%s \n\n' % (LSThh, LSTmm, LSTss))
        self.after(1000, self.update_LST)
        
    def update_RADEC(self):
        self.current_radec_var.set("RA: %f, DEC: %f"%self.cgx.get_radec())

    def sync_zenith(self):
        raz, decz = self.LST(), 90.0
        self.cgx.sync(ra=raz, dec=decz)
        self.update_RADEC()
        self.aligned = True


# initialize tkinter
root = Tk()
app = Window(root)

# set window title
root.wm_title("CGXL mount control")
app.active_frame.grid(column=0, row=0)
app.info_frame.grid(column=0, row=1)
app.arrow_frame.grid(column=1, row=2)
app.goto_frame.grid(column=0, row=2)
# show window
root.mainloop()
