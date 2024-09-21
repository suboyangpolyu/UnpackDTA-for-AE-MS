import struct
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import os

def unpack_bin(DTA_path):
    ID = []
    file_size = os.path.getsize(DTA_path)
    with open(DTA_path, "rb") as data:
        byte = data.read(2) 
        count = 1
        pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc='Upacking DTA file')
        while byte != b"":
            [LEN] = struct.unpack('H', byte) 
            [b1] = struct.unpack('B', data.read(1))
            count += 1
            ID.append([b1,count])
            LEN -= 1 
            data.read(LEN) 
            byte = data.read(2)
            count += LEN + 2
            pbar.update(2 + LEN + 1)
        pbar.close()
    return ID

def read_ID42(INDEX):
    gain = {}
    data.seek(INDEX-2)
    byte = data.read(2)
    [LEN] = struct.unpack('H', byte) # massage length of ID-42
    [b1] = struct.unpack('B', data.read(1)) # ID-42
    LEN -= 1
    [b2] = struct.unpack('B', data.read(1)) # SUBID-0
    LEN -= 1
    data.read(2) # MVERN   
    LEN -= 2      
    # Unpack Submassages
    while LEN > 0:
        [LSUB] = struct.unpack('H', data.read(2))
        LEN = LEN-LSUB
        
        [SUBID] = struct.unpack('B', data.read(1))
        LSUB = LSUB-1

        if SUBID == 5:
            # Number of AE characteristics
            [CHID] = struct.unpack('B', data.read(1))
            LSUB = LSUB-1
            # read CHID values
            CHID_list = struct.unpack(str(CHID)+'B', data.read(CHID))
            LSUB = LSUB-CHID
        
        elif SUBID == 23:
            # Gain of each CH
            CID, V = struct.unpack('BB', data.read(2))
            gain[CID] = V
            LSUB = LSUB-2

        elif SUBID == 173:
            # Hardware setup of wfm ID-173,42
            [SUBID2] = struct.unpack('B', data.read(1))
            LSUB = LSUB-1
            if SUBID2 == 42:
                
                data.read(2+1+2+2+1) # MVERN+ADT+SETS+SLEN+CHID(not use)
                LSUB = LSUB-2-1-2-2-1
              
                [HLK] = struct.unpack('H', data.read(2)) # HLK*1024 = wfm length 
                LSUB = LSUB-2
                
                data.read(2) # HITS(not use)
                LSUB = LSUB-2
                
                [SRATE] = struct.unpack('H', data.read(2)) # Sample rate in kHZ
                LSUB = LSUB-2

                data.read(2+2) # TMODE+TSOURCE(not use)
                LSUB = LSUB-2-2

                [TDLY] = struct.unpack('h', data.read(2)) # pre-trigger
                LSUB = LSUB-2
                            
                data.read(2+2) # MXIN+THRD(not use)
                LSUB = LSUB-2-2
                
        data.read(LSUB)
            
    return HLK,SRATE,TDLY,gain

def read_ID8(INDEX):
    gain = {}
    data.seek(INDEX-2)
    byte = data.read(2)
    [LEN] = struct.unpack('H', byte) # massage length of ID-8
    [b1] = struct.unpack('B', data.read(1)) # ID-8
    LEN -= 1
    data.read(8) # Time & Data of continuation
    LEN -= 8
    # complete setup record from the first file of the test
    # LEN2 is refreshed within LEN, finding ID-42 for unpack hardware setups
    byte = data.read(2)
    LEN -= 2
    while LEN > 0:
        [LEN0] = struct.unpack('H', byte)
        [b1] = struct.unpack('B', data.read(1))
        LEN -= 1
        if b1 != 42:
            data.read(LEN0-1)
            LEN = LEN - (LEN0-1)
        else: # b1 == 42
            LEN0 -= 1
            [b2] = struct.unpack('B', data.read(1))
            LEN0 -= 1
            data.read(2) # MVERN
            LEN0 -= 2
            while LEN0 > 0:
                [LSUB] = struct.unpack('H', data.read(2))
                LEN0 = LEN0-LSUB
                [SUBID] = struct.unpack('B', data.read(1))
                LSUB = LSUB-1
                if SUBID == 23:
                    # Gain of each CH
                    CID, V = struct.unpack('BB', data.read(2))
                    gain[CID] = V
                    LSUB = LSUB-2
                elif SUBID == 173:
                    # Hardware setup of wfm ID-173,42
                    [SUBID2] = struct.unpack('B', data.read(1))
                    LSUB = LSUB-1
                    if SUBID2 == 42:
                
                        data.read(2+1+2+2+1) # MVERN+ADT+SETS+SLEN+CHID(not use)
                        LSUB = LSUB-2-1-2-2-1
              
                        [HLK] = struct.unpack('H', data.read(2)) # HLK*1024 = wfm length 
                        LSUB = LSUB-2
                
                        data.read(2) # HITS(not use)
                        LSUB = LSUB-2
                
                        [SRATE] = struct.unpack('H', data.read(2)) # Sample rate in kHZ
                        LSUB = LSUB-2

                        data.read(2+2) # TMODE+TSOURCE(not use)
                        LSUB = LSUB-2-2

                        [TDLY] = struct.unpack('h', data.read(2)) # pre-trigger
                        LSUB = LSUB-2
                            
                        data.read(2+2) # MXIN+THRD(not use)
                        LSUB = LSUB-2-2
                
                data.read(LSUB)                               
            LEN = LEN - (LEN0-1)           
        byte = data.read(2)
        LEN -= 2 
    return HLK,SRATE,TDLY,gain

def _bytes_to_RTOT(bytes):
    """Helper function to convert a 6-byte sequence to a time offset"""
    (i1, i2) = struct.unpack('IH', bytes)
    return ((i1+2**32*i2)*.25e-6)

def read_ID173(HLK,SRATE,TDLY,gain,INDEX,DTA_name,save_path):
    data.seek(INDEX-2)
    byte_LEN = data.read(2)
    [LEN] = struct.unpack('H', byte_LEN)

    byte_ID = data.read(1)
    [ID] = struct.unpack('B', byte_ID)
    LEN -= 1
    
    byte_SUBID = data.read(1)
    [SUBID] = struct.unpack('B', byte_SUBID)  
    LEN -= 1
    
    byte_TOT = data.read(6)
    TOT =_bytes_to_RTOT(byte_TOT)
    LEN -= 6
    
    byte_CID = data.read(1)
    [CH] = struct.unpack('B', byte_CID) 
    LEN -= 1

    byte_ALB = data.read(1)
    LEN -= 1 
    
    MaxInput = 10.0
    Gain = 10**(gain[CH]/20) # linear gain = 10^(dB/20)
    MaxCounts = 32768.0
    AmpScaleFactor = MaxInput/(Gain*MaxCounts)

    if HLK*1024*2 > LEN:
        print('The ID index ',INDEX, ' is not packed waveform')
    else:
        byte_sig = data.read(HLK*1024*2)
        sig_scaled = struct.unpack(str(int(HLK*1024))+'h', byte_sig)
        volt = AmpScaleFactor*np.array(sig_scaled)
        time = (np.arange(0, len(volt))+TDLY)/(SRATE*1e3)
                                                  
    TOT = str(round(TOT*1e6,2))
    TOT_int, TOT_de = TOT.split('.')
    CH = str(CH)
    df = pd.DataFrame({'Time(s)':time,'Volt(V)':volt})
    df.to_csv(f"{save_path}/{DTA_name}_{CH}_{TOT_int}_{TOT_de}.csv", index=False)

    return 

# Select DTA and empty wfm folder
root = tk.Tk()
root.withdraw() 
DTA_path = filedialog.askopenfilename()
DTA_name = DTA_path.split('/')[-1].split('.')[0]
save_path = filedialog.askdirectory()

# Unpack DTA IDs
ID = unpack_bin(DTA_path)

# Save DTA massage IDs
df = pd.DataFrame(ID, columns=['Message_ID', 'ID_position'])
df.to_csv(f"{DTA_name}_Unpacked.csv", index=False)

# Read waveforms
with open(DTA_path, "rb") as data:
    for item in tqdm(ID, desc="Reading wfm as csv"):
        if item[0] == 42:
            INDEX = item[1]
            HLK,SRATE,TDLY,gain=read_ID42(INDEX)
            
        if item[0] == 8:
            INDEX = item[1]
            if INDEX < 10000:
                HLK,SRATE,TDLY,gain=read_ID8(INDEX)

        elif item[0] == 173:
            INDEX = item[1]
            read_ID173(HLK,SRATE,TDLY,gain,INDEX,DTA_name,save_path)
    print(f'Reading wfms of {DTA_name} was complete！')