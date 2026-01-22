# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 11:24:19 2025

@author: user
"""
from pathlib import Path
import subprocess

# # Path to Fiji Executable
# cwd = str(Path.cwd()).replace("\\", "/")
# fiji_exe = cwd +"/"+ "FIJI.app2/ImageJ-win64.exe"

def Call_imageJ_SIFTreg(in_paths,out_paths):
    
    fiji_exe = r"C:\DATA\FIJI.app2/ImageJ-win64.exe"
    if not Path(fiji_exe).exists():
        raise SystemExit(f"[Error] Fiji executable not found: {fiji_exe}")
    
    macro_file = "D:/02_Python/DHM_tools/DHM_Autobot_4well/imageJ_Macro_SIFT.ijm"
    
    # Make arguments dictionnary to give to macro
    macro_args = ""
    
    in_paths_str = ""
    out_paths_str = ""
    
    for i in range(len(in_paths)-1):
        
        # Enable overwriting of existing out files
        if Path(out_paths[i]).exists():
            Path(out_paths[i]).unlink()
        
        in_paths_str = in_paths_str + in_paths[i] + "*"
        out_paths_str = out_paths_str + out_paths[i] + "*"
    in_paths_str = in_paths_str + in_paths[-1]
    out_paths_str = out_paths_str + out_paths[-1]
        
    macro_args = in_paths_str +"?" + out_paths_str
    
    print("Macro arguments assembled.")
    
    # Compose the Fiji command. Set "--console" flag to route plugin
    # output to stdout for real-time logging
    cmd = [fiji_exe, "--console", "-macro", str(macro_file), macro_args]
    
    print("[CMD]", " ".join(cmd))
    print("\n[ImageJ] Running... (press Ctrl+C to stop)\n")
    
    # Run ImageJ and stream outputlogs live to the console
    process = subprocess.Popen(
        cmd)
    #     ,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT,  # merge stderr into stdout
    #     text=True,
    #     bufsize=1,  # line-buffered
    #     universal_newlines=True,
    # )
    
    # Wait for ImageJ process to complete
    process.wait()
    print("\n[ImageJ] Done.")
    
if __name__ == "__main__":
    in_path = r"I:\New folder\00000_phase.tif"
    out_path = r"I:\New folder\w1_test_aligned.tif"
    Call_imageJ_SIFTreg(in_path,out_path)


def Call_imageJ_SIFTreg_Single(in_path,out_path,out_log_path):
    
    fiji_exe = r"C:\DATA\FIJI.app2/ImageJ-win64.exe"
    if not Path(fiji_exe).exists():
        raise SystemExit(f"[Error] Fiji executable not found: {fiji_exe}")
    
    macro_file = "D:/02_Python/DHM_tools/DHM_Autobot_4well/imageJ_Macro_SIFT_single.ijm"
    
    macro_args = in_path +"?"+ out_path +"?"+ out_log_path
    
    print("Macro arguments assembled.")
    
    # Compose the Fiji command. Set "--console" flag to route plugin
    # output to stdout for real-time logging
    cmd = [fiji_exe, "--console", "-macro", str(macro_file), macro_args]
    
    print("[CMD]", " ".join(cmd))
    print("\n[ImageJ] Running... (press Ctrl+C to stop)\n")
    
    # Run ImageJ and stream outputlogs live to the console
    process = subprocess.Popen(
        cmd)
    #     ,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT,  # merge stderr into stdout
    #     text=True,
    #     bufsize=1,  # line-buffered
    #     universal_newlines=True,
    # )
    
    # Wait for ImageJ process to complete
    process.wait()
    print("\n[ImageJ] Done.")
    
# if __name__ == "__main__":
#     in_path = r"I:\New folder\00000_phase.tif"
#     out_path = r"I:\New folder\w1_test_aligned.tif"
#     Call_imageJ_SIFTreg(in_path,out_path)