path = input('Please input path to DICOM parent folder: ', 's');
%'/Users/alexgeorge/Documents/LAD1_test'
addpath(path);
files = dir(path);
num_files = length(files);
i = 3;

while i <= num_files
   curr_file = files(i).name;
   curr_file
   
   X = dicomread(curr_file);
   disp('File read')
   
   metadata = dicominfo(curr_file);
   metadata.(dicomlookup('0002','0000')) = 200;
   disp('File info changed')
   
   dicomwrite(X,strcat(path,curr_file), metadata)
   disp('File written')
   
   i = i + 1;
end
