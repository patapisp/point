from .nexstar import NexStar
import numpy as np
import serial
import datetime
import time

def LST(Long=8.55):
    """
    Calculates local siderreal time based on location
    """
    t_utc = datetime.datetime.utcnow()
    YY = t_utc.year
    MM = t_utc.month
    DD = t_utc.day
    UT = t_utc.hour + (t_utc.minute/60)
    JD = (367*YY) - int((7*(YY+int((MM+9)/12)))/4) + int((275*MM)/9) + DD + 1721013.5 + (UT/24)
    GMST = 18.697374558 + 24.06570982441908*(JD - 2451545)
    GMST = GMST % 24
    Long = Long/15      #Convert longitude to hours
    LST = GMST+Long     #Fraction LST. If negative we want to add 24...
    if LST < 0:
        LST = LST +24

    LSTmm = (LST - int(LST))*60          #convert fraction hours to minutes
    LSTss = (LSTmm - int(LSTmm))*60      #convert fractional minutes to seconds
    LSThh = int(LST)
    LSTmm = int(LSTmm)
    LSTss = int(LSTss)
    return LST*15

class CGXL_mount:
    def __init__(self, location, port):
        self. location = location
        self.port = port
        self.connected = False
        self.aligned = False


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

        print('\nLocal Sidereal Time %s:%s:%s \n\n' %(LSThh, LSTmm, LSTss))
        return LST*15

    def connect_to_mount(self):
        print("Initializing CGX-L mount...")
        try:
            self.cgx = NexStar(device=self.port)
            print(self.cgx)
            return 1
        except Exception as e:
            print(e)
            return 0

    def sync_time_location(self):
        self.cgx.set_location(lat=self.location[0], lon=self.location[1])
        # set time
        self.cgx.set_time()
        print(self.cgx.get_radec(), self.cgx.get_location(), self.cgx.get_time())
        return


    def align_zenith(self):
        print("Please move telescope to Zenith")
        al_in = input("Finished? y/n :")
        if al_in == "y" or al_in == "yes":
            raz, decz = self.LST(), 90.0
            self.cgx.sync(ra=raz, dec=decz)
            alinged =True
            print("Alignment complete", self.cgx.alignment_complete())
        print(self.cgx.get_radec())
        return 1

    def init_mount(self):
        print("Welcome to the CGX-L mount")
        print("Is the mount initialized and in the home position?")
        home = input("Finished? y/n :")
        port = input("Provide serial port: ")
        if "COM" not in port:
            print("Wrong port, try something like COM7")
            return None

        self.port = port
        if home == "y" or home == "yes":
            print("Connecting to mount")
        else:
            print("Failed. First quick align the mount")
            return None
        self.connected = False
        err = self.connect_to_mount()
        if err == 0:
            print("Failed")
            return
        self.connected = True
        if self.connected:
            #sync north
            raz, decz = 0.0, 90.0
            self.cgx.sync(ra=raz, dec=decz)
            err = self.align_zenith()
            if err == 1:
                print("Alignment complete.")
            self.aligned = True
        return

    def slew(self, ax, rate=10000):
        err = self.cgx.slew_var(ax, rate)
        return err

    def stop_slew(self):
        self.cgx.slew_var('ra', 0)
        self.cgx.slew_var('dec', 0)
        return

    def read_radec_from_file(self):
        pass



    def run(self):
        print("Welcome to the CGX-L mount")
        print("Is the mount initialized and in the home position?")
        home = input("Finished? y/n :")
        port = input("Provide serial port: ")
        if "COM" not in port:
            print("Wrong port, try something like COM7")
            return None

        self.port = port
        if home == "y" or home == "yes":
            print("Connecting to mount")
        else:
            print("Failed. First quick align the mount")
            return None
        self.connected = False
        err = self.connect_to_mount()
        if err == 0:
            print("Failed")
            return
        self.connected = True
        if self.connected:
            err = self.align_zenith()
            if err == 1:
                print("Alignment complete.")
            self.aligned = True

        while self.connected and self.aligned:
            try:
                # command where to go
                if self.cgx.goto_in_progress():
                    time.sleep(3)
                    continue
                radec_in = input("Enter RA,DEC in decimal")
                ra_go, dec_go = radec_in.split(",")
                ra_go = float(ra_go)
                dec_go = float(dec_go)
                self.cgx.goto_radec(ra=ra_go, dec=dec_go)
                print("Telecope at RA,DEC:", self.cgx.get_radec())
                ans = input("Continue to next ra dec? y/n")
                if ans =='n':
                    self.working=False
                    break
            except KeyboardInterrupt:
                self.working = False
        else:
            self.cgx.cancel_goto()
            self.cgx.serial.close()
            print("Closed serial connection")











if __name__=="__main__":

    location = [47.3686498, 8.5391825]
    mount = CGXL_mount(location, "COM7")

    mount.run()
    """
    print("Initializing CGX-L mount...")
    cgx = NexStar(device="COM7")
    print(cgx)
    try:
        print("Model ", cgx.get_model())
        # set location
        cgx.set_location(lat=47.3686498, lon=8.5391825)
        # set time
        cgx.set_time()
        print(cgx.get_radec(), cgx.get_location(), cgx.get_time())

        aligned = False
        working = False

        print("Please move telescope to Zenith")
        al_in = input("Finished? y/n :")
        if al_in == "y" or al_in == "yes":
            raz, decz = LST(Long=cgx.get_location()[1]), 90.0
            cgx.sync(ra=raz, dec=decz)
            alinged =True
            print("Alignment complete", cgx.alignment_complete())
        print(cgx.get_radec())
        cgx.set_tracking_mode(2)
        working = True

        while working:
            # command where to go
            if cgx.goto_in_progress():
                time.sleep(3)
                continue
            radec_in = input("Enter RA,DEC in decimal")
            ra_go, dec_go = radec_in.split(",")
            ra_go = float(ra_go)
            dec_go = float(dec_go)
            cgx.goto_radec(ra=ra_go, dec=dec_go)
            print("Telecope at RA,DEC:", cgx.get_radec())
            ans = input("Continue to next ra dec? y/n")
            if ans=='n':
                working=False

        cgx.cancel_goto()
        if working:
            radec_in = input("Enter RA,DEC in decimal")
            ra_go, dec_go = radec_in.split(",")
            ra_go = float(ra_go)
            dec_go = float(dec_go)
            cgx.goto_radec(ra=ra_go, dec=dec_go)
            print("Telecope at RA,DEC:", cgx.get_radec())
    except:
        pass
    """
    #cgx.serial.close()