# -*- coding: utf-8 -*-
"""
DHM file autobot 4-well
Autor: Gernot Scheerer, team UMI, CNP-CHUV Lausanne
gernot.scheerer@hotmail.de

Version 01 - 17.04.2024

This program is used to post-process data recorded during an experience with a LynceeTec DHM,
where four sequences are recorded simultaneously with the stage-control tool.

This programme converts the single-frame bin files to sequence tif files.
Then calls imageJ and a macro to do registrarion of the four sequences with FIJI.
Then converts the four aligned sequences from TIFF to "LynceeTec-bnr" file format and renames the files.

Under "Choose folder", browse for the "date-time" folder created by Koala.
"""
import sys
from threading import Thread
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from tifffile import imwrite, imread
import numpy

import binkoala
from Call_imageJ_SIFTreg import Call_imageJ_SIFTreg_Single


# Linear Stack Alignment with SIFT parameter string
SIFT_paras_string = "Linear Stack Alignment with SIFT parameter:\n\ninitial_gaussian_blur = 1.60\nsteps_per_scale_octave = 3\nminimum_image_size = 64\nmaximum_image_size = 1024\nfeature_descriptor_size = 4\nfeature_descriptor_orientation_bins = 8\nclosest/next_closest_ratio = 0.92\nmaximal_alignment_error = 25\ninlier_ratio = 0.05\nexpected_transformation = Translation\ninterpolate\nshow_transformation_matrix\n\nTranslation per frame (x,y):\n\n"


class ConsoleRedirector(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

def manage_widgets(frame,state):
    for child in frame.winfo_children():
        try:
            child.configure(state=state)
        except tk.TclError:
            print(child)
            pass   # some widgets (e.g. frames, labels) don't have a "state"

def all_off(widgetlist,framelist):
    for W in widgetlist:
        W.config(state="disabled")
        
    for F in framelist:
        manage_widgets(F,"disabled")

def all_on(widgetlist,framelist):
    for W in widgetlist:
        W.config(state="normal")
        
    for F in framelist:
        manage_widgets(F,"normal")

def bin2tif(binfolder,output_file,Q):
    '''
    converts LynceeTec Koala bin files from one folder into a tiff stack file
    the bin files need to end with _00000_phase.bin, _00001_phase.bin, _00002_phase.bin, ..
    '''
    
    def safe_update(v):
        Prog_bar["value"] = v
    
    # get the list of bin files to process
    bin_files = []
    bin_files = sorted([f for f in os.listdir(binfolder) if f.endswith(('.bin'))])
    
    total_files = len(bin_files)
    x = 100 / total_files
    
    for i in range(total_files):
        
        infile = binfolder+'/'+ bin_files[i]
        phase_map, in_file_header = binkoala.read_mat_bin(infile)
        
        imwrite(output_file,
                phase_map,
                photometric='minisblack',
                compression=None,
                append=True,
                bitspersample=32,
                planarconfig='contig',
                subfiletype=3)
        
        # update_progress(round(i*x))
        root.after(0, safe_update, round(i*x))
    
    # update_progress(0)
    root.after(0, safe_update, 0)
    

def tif2bnr(input_file,timestampsfile,wv,n_1,n_2,pz,output_file,Q):
    '''
    convert a tiff sequence (data from LynceeTec Koala) into a bnr sequence (LynceeTec format)

    input_file: filepath of the tiff sequence
    timestampsfile: int32 array from 3rd column of Koala timestamps file
    output_file: destination of the bnr sequence file
    '''    
    def safe_update(v):
        Prog_bar["value"] = v
        
    #read timestamps from timestampsfile
    with open(timestampsfile, 'r') as infile:
        k=0
        timelist=[]
        for line in infile:
            # Split the line into a list of numbers
            numbers = line.split()
            time=numpy.single(float(numbers[3]))
            timelist.append(time)
            k=k+1          
        timestamps=numpy.array(timelist)
    nImages=len(timestamps) #sequence length
    
    #get first image from tiff stack
    phase_map = imread(input_file, key=0)
    w = len(phase_map[0,:])
    h = len(phase_map[:,0])
    
    #write meta data to bnr file
    fileID=open(output_file,'w')
    numpy.array(nImages, dtype=numpy.int32).tofile(fileID)
    numpy.array(w, dtype=numpy.int32).tofile(fileID)
    numpy.array(h, dtype=numpy.int32).tofile(fileID)
    numpy.array(pz, dtype=numpy.float32).tofile(fileID)
    numpy.array(wv, dtype=numpy.float32).tofile(fileID)
    numpy.array(n_1, dtype=numpy.float32).tofile(fileID)
    numpy.array(n_2, dtype=numpy.float32).tofile(fileID)
    
    # Write timestamps to bnr file
    for k in range(0,nImages):
        numpy.array(timestamps[k], dtype=numpy.float32).tofile(fileID)
    
    x = 100 / nImages

    #write images to bnr file
    for k in range(0,nImages):
        phase_map = imread(input_file, key=k)
        
        phase_map.astype(numpy.float32).tofile(fileID)
        
        root.after(0, safe_update, round(k*x))

    fileID.close()
    root.after(0, safe_update, 0)
    
    
# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
# # imageJ executable default path
# FIJIexeDefault = None
# if os.path.isfile("imageJ_EXE_path.txt"):
#     f = open("imageJ_EXE_path.txt")
#     FIJIexeDefault = f.read().strip()

fixedSuffixPath = "/Phase/Float/Bin"

tif_suffix = "_phase.tif"
tif_aligned_suffix = "_phase_aligned.tif"

Wells = ["00001_00001", "00001_00002", "00002_00001", "00002_00002"]

thisdate = datetime.today().strftime('%Y%m%d')
unitlist = ['M', 'mM', 'uM', 'nM']

root = tk.Tk()
root.title("Autobot")
root.iconbitmap("auto.ico")

# -------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------
vars = {
    'mainfolder': tk.StringVar(),
    # 'FIJIexe': tk.StringVar(),
    'wv': tk.StringVar(value='665.8'),
    'n_1': tk.StringVar(value='1'),
    'n_2': tk.StringVar(value='2'),
    'pz': tk.StringVar(value='1.1520307e-06'),
    'date': tk.StringVar(value=thisdate),
    'micro': tk.StringVar(value='F'),
    'exp': tk.StringVar(),
    'lin1': tk.StringVar(),
    'lin2': tk.StringVar(),
    'lin3': tk.StringVar(),
    'lin4': tk.StringVar(),
    'drug': tk.StringVar(),
    'conc': tk.StringVar(),
    'unit': tk.StringVar(value='uM'),
    'bloq': tk.StringVar(),
    'Bconc': tk.StringVar(),
    'Bunit': tk.StringVar(value='uM'),
}

# -------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------
def choose_folder():
    folder = filedialog.askdirectory(title="Choose a Koala folder")
    if folder:
        vars['mainfolder'].set(folder)
        
        print("Selected Koala folder:")
        print(folder)
        
        # Get pixel size from bin file
        for i in range(len(Wells)):
            
            binfile = folder +os.sep+ Wells[i] + fixedSuffixPath +os.sep+ "00000_phase.bin"
            
            if os.path.isfile(binfile):
                phase_map, in_file_header = binkoala.read_mat_bin(binfile)
                vars['pz'].set(str(in_file_header['px_size'][0]))
                break

# def choose_FIJI():
#     file = filedialog.askopenfilename(title="Select the imageJ executable")
#     if file:
#         vars['FIJIexe'].set(file)
#         with open("imageJ_EXE_path.txt", "w") as F:
#             F.write(file)

def rename_folder():
    mainfolder = vars['mainfolder'].get()
    if not mainfolder:
        messagebox.showerror("Error", "Please choose a folder.")
    else:
        output_file_name_A = f"{thisdate}_{vars['micro'].get()}_Exp{vars['exp'].get()}"
        
        if vars['bloq'].get() == '':
            output_file_name_B = f"_{vars['drug'].get()}_{vars['conc'].get()}{vars['unit'].get()}"
        else:
            output_file_name_B = f"_{vars['drug'].get()} {vars['conc'].get()}{vars['unit'].get()}_{vars['bloq'].get()}_{vars['Bconc'].get()}{vars['Bunit'].get()}"
        
        output_path = output_file_name_A + output_file_name_B
        
        base_folder = os.path.dirname(mainfolder)
    
        print(base_folder)
        
        new_name = base_folder +os.sep+ output_path
        
        print(output_path)
        
        os.rename(mainfolder,new_name)
        
        vars['mainfolder'].set(new_name)
        
        print("New working folder:")
        print(new_name)
        root.after(0, append_info, "New working folder:\n" + new_name)

def append_info(text):
    info_box.config(state='normal')
    info_box.insert('end', text + '\n')
    info_box.see('end')
    info_box.config(state='disabled')

def start_process(mode):
    
    if mode == "auto":
        thread = Thread(target = run_process, daemon=True)
        thread.start()
    elif mode == "sinlge":
        thread = Thread(target = Conv_align_single, daemon=True)
        thread.start()
    elif mode == "b2t":
        thread = Thread(target = Convert_single_bin2tif, daemon=True)
        thread.start()
    elif mode == "t2b":
        thread = Thread(target = Convert_single_tif2bnr, daemon=True)
        thread.start()
    
def run_process():
        
    all_off([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
    mainfolder = vars['mainfolder'].get()
    if not mainfolder:
        messagebox.showerror("Error", "Please choose a folder.")
        return
    
    # Check if output files exist already
    files_exist = False
    for i in range(len(Wells)):
        tif_file = mainfolder +os.sep+ Wells[i] + tif_suffix
        if os.path.isfile(tif_file):
            files_exist = True
        tif_file_aligned = mainfolder +os.sep+ Wells[i] + tif_aligned_suffix
        if os.path.isfile(tif_file_aligned):
            files_exist = True
        # BNR file
        output_file_name_A = os.path.join(mainfolder, f"{thisdate}_{vars['micro'].get()}_Exp{vars['exp'].get()}")
        if vars['bloq'].get() == '':
            output_file_name_B = f"_{vars['drug'].get()}_{vars['conc'].get()}{vars['unit'].get()}.bnr"
        else:
            output_file_name_B = f"_{vars['drug'].get()} {vars['conc'].get()}{vars['unit'].get()}_{vars['bloq'].get()}_{vars['Bconc'].get()}{vars['Bunit'].get()}.bnr"
        output_path = output_file_name_A +"_" + "w" + str(i).rjust(3, '0') + "_" + vars[f'lin{i+1}'].get() + output_file_name_B
        if os.path.isfile(output_path):
            files_exist = True
    
    go_on = True
    if files_exist:
        print('/!\\ Some output files exit already!')
        result = tk.messagebox.askquestion('/!\\/!\\/!\\ Some output files exits already!', 'Do you want to proceed and overwrite these files?')
        if not result == 'yes':
            go_on = False
    
    if go_on:
        print("Autobots roll out!\n -> Starting file conversion and image alignment...")        
        root.after(0, append_info, "Autobots roll out!\n -> Starting file conversion and image alignment...")
        
        wv = float(vars['wv'].get())
        n_1 = float(vars['n_1'].get())
        n_2 = float(vars['n_2'].get())
        pz = float(vars['pz'].get())
        
        bnr_files=[]
        
        # Loop through wells
        for i in range(len(Wells)):
            
            binfolder = mainfolder +"/"+ Wells[i] + fixedSuffixPath
            
            if not os.path.isdir(binfolder):
                print("Warning: Files missing for well "+Wells[i])
                root.after(0, append_info, "Warning: Files missing for well "+Wells[i])
            else:
                print("\nProcessing well",Wells[i])
                root.after(0, append_info, "Processing well " + Wells[i])
    
                # Convert files from LynceeTec bin to tif
                print("1. Converting from LynceeTec bin to tif...")
                root.after(0, append_info, "1. Converting from LynceeTec bin to tif...")
                
                tif_file = mainfolder +os.sep+ Wells[i] + tif_suffix
                
                # Enable overwriting of existing out file
                if os.path.isfile(tif_file):
                    os.remove(tif_file)
                
                # Transform files from LynceeTec bin to tif
                bin2tif(binfolder,tif_file,Wells[i])
                
                # Registration of sequences with "linear stack alignment with SIFT"
                print('2. Registration with SIFT...')
                root.after(0, append_info, '2. Registration with SIFT...')
                
                aligned_file = mainfolder +os.sep+ Wells[i] + tif_aligned_suffix
                
                log_out_file = mainfolder +os.sep+ Wells[i] +os.sep+ "SIFT alignment log.txt"
                
                Call_imageJ_SIFTreg_Single(tif_file,aligned_file,log_out_file)
                
                # Get translation shift per frame and write SIFT parameter file
                with open(log_out_file, 'r') as file:
                    shiftstr = ""
                    for line in file:
                        lin = line.strip()
                        if "Transformation Matrix: AffineTransform" in line:
                            string = lin.split("AffineTransform")[1]
                            string = string.replace("[", "")
                            string = string.replace("]", "")
                            xxx = string.split(",")
                            aaa = [yy.strip() for yy in xxx]
                            shiftstr = shiftstr + aaa[2] + "," + aaa[5] + "\n"
                with open(log_out_file, 'w') as file:
                    file.write(SIFT_paras_string)
                    file.write(shiftstr)
            
                # remove the initial tif file
                if os.path.isfile(tif_file):
                    os.remove(tif_file)
        
                # Convert files from tif to LynceeTec bnr
                print("3. Converting from tif to LynceeTec bnr...")
                root.after(0, append_info, "3. Converting  from tif to LynceeTec bnr...")
    
                ts_path = mainfolder +os.sep+ Wells[i] +os.sep+ "timestamps.txt"
                    
                output_file_name_A = os.path.join(mainfolder, f"{thisdate}_{vars['micro'].get()}_Exp{vars['exp'].get()}")
                if vars['bloq'].get() == '':
                    output_file_name_B = f"_{vars['drug'].get()}_{vars['conc'].get()}{vars['unit'].get()}.bnr"
                else:
                    output_file_name_B = f"_{vars['drug'].get()} {vars['conc'].get()}{vars['unit'].get()}_{vars['bloq'].get()}_{vars['Bconc'].get()}{vars['Bunit'].get()}.bnr"
                output_path = output_file_name_A +"_" + "w" + str(i+1).rjust(3, '0') + "_" + vars[f'lin{i+1}'].get() + output_file_name_B
                
                bnr_files.append(output_path)
                
                # Enable overwriting of existing out files
                if os.path.isfile(output_path):
                    os.remove(output_path)
                    
                tif2bnr(aligned_file, ts_path, wv, n_1, n_2, pz, output_path, Wells[i])
                    
                # Remove aligned tif file
                os.remove(aligned_file)
    
        root.after(0, append_info, "File conversion and image alignment done.\nNo more decepticons\n")
        print("File conversion and image alignment done.\nNo more decepticons\n")
        
        print("Checking BNR files...")
        root.after(0, append_info, "Checking BNR files...")
        
        BNR_check = False
        BNR_errors = "Something is wrong with the BNR files:\n"
        # Loop through wells
        for bnr in bnr_files:
            
            #get header info:
            fileID = open(bnr, 'rb')
            nImages = numpy.fromfile(fileID, dtype="i4", count=1)
            nImages = nImages[0]
            w = numpy.fromfile(fileID, dtype="i4", count=1)
            w = w[0]
            h = numpy.fromfile(fileID, dtype="i4", count=1)
            h = h[0]
            _ = numpy.fromfile(fileID, dtype="f4", count=1)
            _ = numpy.fromfile(fileID, dtype="f4", count=1)
            _ = numpy.fromfile(fileID, dtype="f4", count=1)
            _ = numpy.fromfile(fileID, dtype="f4", count=1)
            timestamps = [0] * nImages
            for k in range(0,nImages):
                x=numpy.fromfile(fileID, dtype="i4", count=1)
                timestamps[k] = x[0]
                
            #get first image from sequence
            phase_map = numpy.zeros((h,w))
            for k in range(h):
                phase_map[k,:] = numpy.fromfile(fileID, dtype="f4", count=w)
            phase_map=numpy.single(phase_map)
            fileID.close
            
            phasemin=phase_map.min()
            phasemax=phase_map.max()
            
            if phasemin < -100 or phasemax > 100:
                
                print("Problem with BNR file", os.path.basename(bnr))
                root.after(0, append_info, "Problem with BNR file " + os.path.basename(bnr))
            
                BNR_errors = BNR_errors + os.path.basename(bnr) +"\n"
                BNR_check = True
            
        
        if BNR_check:
            
            messagebox.showerror("Attention!", BNR_errors + "Please check these files.")
        
        print("Checking BNR files done.\n")
        root.after(0, append_info, "Checking BNR files done.\n")
    
    all_on([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])

def Convert_single_bin2tif():
    
    all_off([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
    binfolder = filedialog.askdirectory(title="Choose a bin folder")
    
    if binfolder:
        print("Selected Bin folder:")
        print(binfolder)
        
        # Get meta data of bin files, show
        binfile = binfolder +os.sep+ "00000_phase.bin"
        if not os.path.isfile(binfile):
            print("Error: file 00000_phase.bin not found")
            append_info("Error: file 00000_phase.bin not found")
        else:
            outfolder = filedialog.askdirectory(title="Choose an output folder")
            tif_file = outfolder +os.sep+ "0000X_0000X_phase.tif"
            
            go_on = True
            if os.path.isfile(tif_file):
                print('/!\\ Output tif file exits already!')
                result = tk.messagebox.askquestion('/!\\/!\\/!\\ Output tif file exits already!', 'Do you want to proceed and overwrite?')
                if not result == 'yes':
                    go_on = False
                if go_on:
                    os.remove(tif_file)
            
            if go_on:
                print("Converting from BIN to TIF...")
                
                phase_map, in_file_header = binkoala.read_mat_bin(binfile)
                vars['pz'].set(str(in_file_header['px_size'][0]))
                
                bin2tif(binfolder,tif_file,"0000X_0000X")
                
                print("Conversion done.")
                
    all_on([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
            
def Convert_single_tif2bnr():
    
    all_off([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
    file = filedialog.askopenfilename(title="Select a tif sequence")    
    if file:
        print("Selected TIF file:")
        print(file)
        bnr_file = os.path.splitext(file)[0]+".bnr"
        
        go_on = True
        if os.path.isfile(bnr_file):
            print('/!\\ BNR output file exits already!')
            result = tk.messagebox.askquestion('/!\\/!\\/!\\ BNR output file exits already!', 'Do you want to proceed and overwrite?')
            if not result == 'yes':
                go_on = False
            if go_on:
                os.remove(bnr_file)
          
        pz = float(vars['pz'].get())
        result = tk.messagebox.askquestion('Please check pixel size', f"Is this the correct pixel size: {pz} ?")
        if not result == 'yes':
            go_on = False
                
        if go_on:
            ts_path = filedialog.askopenfilename(title="Select a timestamps file")
            if ts_path:
                print("Converting from TIF to BNR...")
                wv = float(vars['wv'].get())
                n_1 = float(vars['n_1'].get())
                n_2 = float(vars['n_2'].get())
                pz = float(vars['pz'].get())
                
                tif2bnr(file, ts_path, wv, n_1, n_2, pz, bnr_file, "0000X_0000X")
                
                print("Conversion done.")
    
    all_on([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
def Align_single():
    
    all_off([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
    file = filedialog.askopenfilename(title="Select a tif sequence")    
    if file:
        print("Selected TIF file:")
        print(file)
        aligned_file = os.path.splitext(file)[0]+"_aligned.tif"
        go_on = True
        if os.path.isfile(aligned_file):
            print('/!\\ Alignment output file exits already!')
            result = tk.messagebox.askquestion('/!\\/!\\/!\\ Alignment output file exits already!', 'Do you want to proceed and overwrite?')
            if not result == 'yes':
                go_on = False
            if go_on:
                os.remove(aligned_file)
        if go_on:
            print("Aligning images...")
            log_out_file = os.path.splitext(file)[0] + "_alignment log.txt"
            
            Call_imageJ_SIFTreg_Single(file,aligned_file,log_out_file)
                        
            # Get translation shift per frame and write SIFT parameter file
            with open(log_out_file, 'r') as file:
                shiftstr = ""
                for line in file:
                    lin = line.strip()
                    if "Transformation Matrix: AffineTransform" in line:
                        string = lin.split("AffineTransform")[1]
                        string = string.replace("[", "")
                        string = string.replace("]", "")
                        xxx = string.split(",")
                        aaa = [yy.strip() for yy in xxx]
                        shiftstr = shiftstr + aaa[2] + "," + aaa[5] + "\n"
            with open(log_out_file, 'w') as file:
                file.write(SIFT_paras_string)
                file.write(shiftstr)
                        
            print("Alignement done.")
    all_on([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
def Conv_align_single():
    
    all_off([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
    binfolder = filedialog.askdirectory(title="Choose a bin folder")
    
    if binfolder:
        print("Selected Bin folder:")
        print(binfolder)
        
        ts_path = filedialog.askopenfilename(title="Select a timestamps file")
        
        if ts_path:
            
            # Get meta data of bin files, show
            binfile = binfolder +os.sep+ "00000_phase.bin"
            if not os.path.isfile(binfile):
                print("Error: file 00000_phase.bin not found")
                root.after(0, append_info, "Error: file 00000_phase.bin not found")
            else:
                outfolder = filedialog.askdirectory(title="Choose an output folder")
                
                if outfolder:

                    print("Starting file conversion and image alignment...")        
                    root.after(0, append_info, "Starting file conversion and image alignment...")

                    tif_file = outfolder +os.sep+ "0000X_0000X_phase.tif"
                    aligned_file = os.path.splitext(tif_file)[0]+"_aligned.tif"
                    bnr_file = os.path.splitext(aligned_file)[0]+".bnr"
                    
                    go_on = True
                    if os.path.isfile(tif_file) or os.path.isfile(aligned_file) or os.path.isfile(bnr_file):
                        print('/!\\ Some output files exit already!')
                        result = tk.messagebox.askquestion('/!\\/!\\/!\\ Some output files exits already!', 'Do you want to proceed and overwrite these files?')
                        if not result == 'yes':
                            go_on = False
     
                    if go_on:
                        phase_map, in_file_header = binkoala.read_mat_bin(binfile)
                        vars['pz'].set(str(in_file_header['px_size'][0]))
                        
                        print("1. Converting sequence from LynceeTec bin to tif...")
                        root.after(0, append_info, "1. Converting sequence from LynceeTec bin to tif...")
                        
                        # Enable overwriting of existing out files
                        if os.path.isfile(tif_file):
                            os.remove(tif_file)
                
                        bin2tif(binfolder,tif_file,"0000X_0000X")
    
                        print("2. Aligning sequence with SIFT...")
                        root.after(0, append_info, "2. Aligning sequence with SIFT...")
                        
                        # Enable overwriting of existing out files
                        if os.path.isfile(aligned_file):
                            os.remove(aligned_file)
                            
                        log_out_file = os.path.splitext(tif_file)[0] + "_alignment log.txt"
                        
                        Call_imageJ_SIFTreg_Single(tif_file,aligned_file,log_out_file)
                        
                        # Get translation shift per frame and write SIFT parameter file
                        with open(log_out_file, 'r') as file:
                            shiftstr = ""
                            for line in file:
                                lin = line.strip()
                                if "Transformation Matrix: AffineTransform" in line:
                                    string = lin.split("AffineTransform")[1]
                                    string = string.replace("[", "")
                                    string = string.replace("]", "")
                                    xxx = string.split(",")
                                    aaa = [yy.strip() for yy in xxx]
                                    shiftstr = shiftstr + aaa[2] + "," + aaa[5] + "\n"
                        with open(log_out_file, 'w') as file:
                            file.write(SIFT_paras_string)
                            file.write(shiftstr)
                        
                        wv = float(vars['wv'].get())
                        n_1 = float(vars['n_1'].get())
                        n_2 = float(vars['n_2'].get())
                        pz = float(vars['pz'].get())
     
                        print("3. Converting sequence from tif to LynceeTec bnr...")
                        root.after(0, append_info, "3. Converting sequence from tif to LynceeTec bnr...")
                        
                        # Enable overwriting of existing out files
                        if os.path.isfile(bnr_file):
                            os.remove(bnr_file)
                    
                        tif2bnr(aligned_file, ts_path, wv, n_1, n_2, pz, bnr_file, "0000X_0000X")
                        
                        os.remove(tif_file)
                        os.remove(aligned_file)
                        
                        print("Conversion and alignement done.\n")
                        root.after(0, append_info, "Conversion and alignement done.\n")
                        
                        print("Checking BNR files...")
                        root.after(0, append_info, "Checking BNR files...")
                            
                        #get header info:
                        fileID = open(bnr_file, 'rb')
                        nImages = numpy.fromfile(fileID, dtype="i4", count=1)
                        nImages = nImages[0]
                        w = numpy.fromfile(fileID, dtype="i4", count=1)
                        w=w[0]
                        h = numpy.fromfile(fileID, dtype="i4", count=1)
                        h=h[0]
                        _ = numpy.fromfile(fileID, dtype="f4", count=1)
                        _ = numpy.fromfile(fileID, dtype="f4", count=1)
                        _ = numpy.fromfile(fileID, dtype="f4", count=1)
                        _ = numpy.fromfile(fileID, dtype="f4", count=1)
                        #timestamps = numpy.fromfile(fileID, dtype="i4", count=nImages)
                        timestamps = [0] * nImages
                        for k in range(0,nImages):
                            x=numpy.fromfile(fileID, dtype="i4", count=1)
                            timestamps[k] = x[0]
                        #get first image from sequence
                        phase_map = numpy.zeros((h,w))
                        for k in range(h):
                            phase_map[k,:] = numpy.fromfile(fileID, dtype="f4", count=w)
                        phase_map=numpy.single(phase_map)
                        fileID.close
                        
                        phasemin=phase_map.min()
                        phasemax=phase_map.max()
                        
                        if phasemin < -100 or phasemax > 100:
                            
                            print("Problem with BNR file", os.path.basename(bnr_file))
                            root.after(0, append_info, "Problem with BNR file " + os.path.basename(bnr_file))
                        
                            messagebox.showerror("Attention!", "Something is wring with the BNR file\n" + bnr_file + "\nPlease check.")
                            
                        print("Checking BNR files done.\n")
                            
    all_on([renamebutt,autobutt,allbutt,CSbutt,ASbutt,CS2butt],[fileframe,paraframe,outframe,linframe,drugframe])
    
# -------------------------------------------------------------------
# Layout
# -------------------------------------------------------------------
frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0, sticky="nsew")

# Parameters
fileframe = ttk.Frame(frame, padding=10)
fileframe.grid(row=0, column=0, sticky="nsew", columnspan = 6)

# Folder selection
ttk.Label(fileframe, text="Choose folder: ").grid(row=0, column=0, sticky="w")
E1=ttk.Entry(fileframe, textvariable=vars['mainfolder'], width=50)
E1.grid(row=0, column=1, sticky="we")
B1=ttk.Button(fileframe, text="Browse", command=choose_folder)
B1.grid(row=0, column=2)

ttk.Label(fileframe, text="                            ").grid(row=0, column=3, sticky="w")

# Progress bar
Prog_bar = ttk.Progressbar(fileframe, mode="determinate", length=250, maximum=100)
Prog_bar.grid(row=0, column=4)
Prog_label = ttk.Label(fileframe, text="   Progress bar").grid(row=0, column=5)

# # imageJ exe file
# ttk.Label(fileframe, text="      imageJ EXE file: ").grid(row=0, column=3, sticky="w")
# ttk.Entry(fileframe, textvariable=vars['FIJIexe'],width=50).grid(row=0, column=4, sticky="we")
# ttk.Button(fileframe, text="Browse", command=choose_FIJI).grid(row=0, column=5)
# # imageJ exe default:
# if FIJIexeDefault:
#     vars['FIJIexe'].set(FIJIexeDefault)
    
ttk.Label(frame, text=" ").grid(row=1, column=0, sticky="w")

# Parameters
paraframe = ttk.Frame(frame, padding=10)
paraframe.grid(row=2, column=0, sticky="nsew", columnspan = 6)

ttk.Label(paraframe, text="Wavelength (nm): ").grid(row=1, column=0, sticky="w")
E2=ttk.Entry(paraframe, textvariable=vars['wv'], width=6)
E2.grid(row=1, column=1, sticky="w")
ttk.Label(paraframe, text="      n₁: ").grid(row=1, column=2, sticky="e")
E3=ttk.Entry(paraframe, textvariable=vars['n_1'], width=6)
E3.grid(row=1, column=3, sticky="w")
ttk.Label(paraframe, text="      n₂: ").grid(row=1, column=4, sticky="e")
E4=ttk.Entry(paraframe, textvariable=vars['n_2'], width=6)
E4.grid(row=1, column=5, sticky="w")
ttk.Label(paraframe, text="      Pixel size: ").grid(row=1, column=6, sticky="e")
E5=ttk.Entry(paraframe, textvariable=vars['pz'], width=15)
E5.grid(row=1, column=7, sticky="w")

ttk.Label(frame, text=" ").grid(row=3, column=0, sticky="w")

# Output tags
outframe = ttk.Frame(frame, padding=10)
outframe.grid(row=4, column=0, sticky="nsew", columnspan = 6)

ttk.Label(outframe, text="Date: ").grid(row=0, column=0, sticky="e")
ED=ttk.Entry(outframe, textvariable=vars['date'], width=10)
ED.grid(row=0, column=1, sticky="w")
ttk.Label(outframe, text="      Microscope: ").grid(row=0, column=2, sticky="e")
EM=ttk.Entry(outframe, textvariable=vars['micro'], width=4)
EM.grid(row=0, column=3, sticky="w")
ttk.Label(outframe, text="      N° Expérience: ").grid(row=0, column=4, sticky="e")
EE=ttk.Entry(outframe, textvariable=vars['exp'], width=6)
EE.grid(row=0, column=5, sticky="w")

ttk.Label(frame, text=" ").grid(row=5, column=0, sticky="w")

# Lignees
linframe = ttk.Frame(frame, padding=10)
linframe.grid(row=6, column=0, sticky="nsew", columnspan = 6)

for i in range(4):
    ttk.Label(linframe, text=f"Lignée Q{i}: ").grid(row=0, column=(i) * 3, sticky="e")
    ttk.Entry(linframe, textvariable=vars[f'lin{i+1}'], width=6).grid(row=0, column=i*3+1, sticky="w")
    ttk.Label(linframe, text="      ").grid(row=0, column=i*3+2, sticky="e")

ttk.Label(frame, text=" ").grid(row=7, column=0, sticky="w")

# Drug & blockers
drugframe = ttk.Frame(frame, padding=10)
drugframe.grid(row=8, column=0, sticky="nsew", columnspan = 6)

ttk.Label(drugframe, text="Drogue: ").grid(row=0, column=0, sticky="e")
EDG=ttk.Entry(drugframe, textvariable=vars['drug'], width=8)
EDG.grid(row=0, column=1, sticky="w")
ttk.Label(drugframe, text="      Concentration: ").grid(row=0, column=2, sticky="e")
EC=ttk.Entry(drugframe, textvariable=vars['conc'], width=6)
EC.grid(row=0, column=3, sticky="w")
ECU=ttk.Combobox(drugframe, values=unitlist, textvariable=vars['unit'], width=4)
ECU.grid(row=0, column=4, sticky="w")
ttk.Label(drugframe, text="      Bloqueur: ").grid(row=0, column=5, sticky="e")
EB=ttk.Entry(drugframe, textvariable=vars['bloq'], width=8)
EB.grid(row=0, column=6, sticky="w")
ttk.Label(drugframe, text="      Concentration: ").grid(row=0, column=7, sticky="e")
EBC=ttk.Entry(drugframe, textvariable=vars['Bconc'], width=6)
EBC.grid(row=0, column=8, sticky="w")
EBU=ttk.Combobox(drugframe, values=unitlist, textvariable=vars['Bunit'], width=4)
EBU.grid(row=0, column=9, sticky="w")

# rename main-folder button
renamebutt = ttk.Button(frame, text="--- ---   Rename Koala folder   --- ---", command=rename_folder)
renamebutt.grid(row=8, column=4, sticky="w")

endframe = ttk.Frame(frame, padding=10)
endframe.grid(row=9, column=0, sticky="nsew", columnspan = 6)
# Run button
autobutt = ttk.Button(endframe, text="\n\n   Autobots rollout!   \n\n", command=lambda: start_process('auto'))
autobutt.grid(row=0, column=0)
ttk.Label(endframe, text="   ").grid(row=0, column=1)
# Info box
info_box = scrolledtext.ScrolledText(endframe, 
                                      wrap = tk.WORD, 
                                      width = 120, 
                                      height = 6, 
                                      # font = ("Times New Roman",
                                              # 15),
                                      state='disabled')
# info_box = tk.Text(endframe, width=60, height=6, state='disabled')
info_box.grid(row=0, column=2)

ttk.Label(frame, text="\nSinlge file stuff:").grid(row=10, column=0, sticky="w")

allbutt = ttk.Button(frame, text="Convert and align single sequence", command=lambda: start_process('sinlge'))
allbutt.grid(row=11, column=0, sticky="w")

ttk.Label(frame, text=" ").grid(row=12, column=0, sticky="w")

CSbutt = ttk.Button(frame, text="Convert single - bin to tif", command=lambda: start_process('b2t'))
CSbutt.grid(row=13, column=0, sticky="w")
ASbutt = ttk.Button(frame, text="Align single sequence", command=Align_single)
ASbutt.grid(row=13, column=1, sticky="w")
CS2butt = ttk.Button(frame, text="Convert single - tif to bnr", command=lambda: start_process('t2b'))
CS2butt.grid(row=13, column=2, sticky="w")

ttk.Label(frame, text="\nConsole text field:").grid(row=14, column=0, sticky="w")

# Console text field
console_box = scrolledtext.ScrolledText(root, width=80, height=10)
console_box.grid(row=15, column=0, sticky="we")

# redirect output
sys.stdout = ConsoleRedirector(console_box)
sys.stderr = ConsoleRedirector(console_box)

# -------------------------------------------------------------------
root.mainloop()
