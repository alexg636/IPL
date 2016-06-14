require 'dicom'
include DICOM

i = 2

# Hard code parent directory path
print "Please enter Dicom path: "
path = gets.chomp
#path = 'C:\Users\IpsUser\Desktop\LAD1_DCM_real\'
files = Dir.entries(path)
num_files = files.count # compensates for first two unneeded files
print num_files

while i < num_files

	# Read dicom file
	dcm = DObject.read(path + files[i]);
	instance_creator = dcm.value("0008,0014")
	print "\n" + "Old: " + dcm.value("0008,0018") + "\n"
	dcm["0008,0018"].value = instance_creator[0..-2] + 0.to_s + (i-1).to_s

	dcm.write(path + files[i])

	print "\n" + "New: " + dcm.value("0008,0018") + "\n"

	i = i + 1

end
