args = getArgument();

lines = split(args, "?");

in = lines[0];
out = lines[1];
outlog = lines[2];

print("Processing in/out file:");
print(in);
print(out);

// Open input without changing its bit depth or scaling, i.e., no auto-scaling on conversions (safety if any conversion occurs)
setOption("ScaleConversions", false);

open(in);

// Run SIFT alignment
run("Linear Stack Alignment with SIFT", "initial_gaussian_blur=1.60 steps_per_scale_octave=3 minimum_image_size=64 maximum_image_size=1024 feature_descriptor_size=4 feature_descriptor_orientation_bins=8 closest/next_closest_ratio=0.92 maximal_alignment_error=25 inlier_ratio=0.05 expected_transformation=Translation interpolate show_transformation_matrix");

// Ensure we overwrite existing output
if (File.exists(out)) File.delete(out);

// Save with current pixel type preserved
// Uses ImageJ's current TIFF save preferences (compression, etc.)
saveAs("Tiff", out);

// Make sure the Log window exists
if (!isOpen("Log")) {
    showMessage("Error", "Log window is not open.");
    
    // Save log contents
    saveAs("ERROR: No LOG window open!", outlog);

    close();
    close();

    run("Quit");
}

// Activate the Log window
selectWindow("Log");

// Save log contents
saveAs("Text", outlog);

print("Log saved to: " + outlog);

close();
close();

run("Quit");