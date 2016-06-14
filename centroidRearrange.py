import csv
import collections
import operator
import numpy
import os
import argparse
import exifread


# INPUT: path to csv file
# OUTPUT: names of all image names 
def titles(path):
	name = collections.Counter()
	with open(path) as input_file:
		for row in csv.reader(input_file, delimiter=','):
			name[row[0]] += 1
		return name

# OUTPUT: Returns a dictionary with file names and number of centroid occurrences
def indexDict(collection):
	indexDict = {}
	i = 0
	while i < len(collection):
		name = (collection.most_common()[i])[0]
		num = (collection.most_common()[i])[1]
		indexDict[num] = name
		i += 1
	return indexDict

# INPUT: image name corresponding to centroid set, path
# OUTPUT: Returns rows with matching image name and corresponding x,y coords
# INPUT: array containing all file names
def sliceOut(modelName, path, modality):
	max_entries = []
	sorted_entries = []
	with open(path) as input_file:
		for row in csv.reader(input_file):
			if modelName in row:
				max_entries.append(row)
		for item in max_entries:
			item[1] = float(item[1])
			item[2] = float(item[2])
		if modality == "p":
			for item in sorted(max_entries, key = operator.itemgetter(1)):
				sorted_entries.append(item)
		elif modality == "s":
			for item in sorted(max_entries, key = operator.itemgetter(2)):
				sorted_entries.append(item)
		return sorted_entries

# INPUT: path to ONE of the images in the sequence
# OUTPUT: will output the scan step number out of all the metadata
def metaTag(path):
	f = open(path, 'rb')
	tags = exifread.process_file(f)
	for item in tags.key():
		print tags[item]

# INPUT: index dictionary containing tiff image label and number of beads detected
# OUTPUT: Returns name of dictionary entry associated with largest number of beads
def maxName(dictionaryName):
	return dictionaryName[max(dictionaryName)]


class Rearranger(object):
	'''Includes meta data for restructuring'''

	def __init__(self, PATH, outputPATH, TYPE):
		self.path 			= PATH
		self.pathParts 		= os.path.split(self.path)
		self.pathParent		= self.pathParts[0] + '\\' 
		self.pathFile		= self.pathParts[1]
		self.fileHeader		= self.pathFile.rpartition('.')[0]
		
		self.outputpath 	= outputPATH
		
		self.outpath 		= outputPATH
		self.outpathParts	= os.path.split(self.outpath)
		self.outpathParent 	= self.outpathParts[0] + '\\'
		self.outpathFile	= self.outpathParts[1]
		self.outfileHeader	= self.outpathFile.rpartition('.')[0]
		self.type 			= TYPE.lower()
		self.allFiles 		= titles(self.path)
		self.allNames 		= sorted(self.allFiles)
		self.lenSeq			= len(self.allNames)
		self.indexed 		= indexDict(self.allFiles)
		self.maxBeads 		= max(self.indexed)
		self.maxBeadsName	= maxName(self.indexed)

		#self.outputName		= self.outpathParent + self.outfileHeader + '.txt'
		self.outputName		= self.pathParent + self.fileHeader + '.txt'

	# INPUT: tiff image label
	# OUTPUT: Returns matrix of original coordinates, restructured in ascending x-coordinates
	def rearrange(self, arrayName):
		coords = numpy.zeros((self.maxBeads, 2))
		newEntry = sliceOut(arrayName, self.path, self.type)
		k = 0
		for item in newEntry:
			coords[k][0] = item[1]
			coords[k][1] = item[2]
			k += 1
		return coords


	# OUTPUT: Returns rearranged max matrix, in ascending x-coordinates
	def maxMTX(self):
		return self.rearrange(self.maxBeadsName)	

	# INPUT: tiff image label (located in csv), small abs tol for non aberation points, large abs tol for aberation points
	# OUTPUT: returns restructured array, repositioning genArray elements to match closest maxMatrix element
	def compArray(self, genArrayname, smallTol, bigTol):
		matrix = self.rearrange(genArrayname)
		maxMatrix = self.maxMTX()
		maxRow = maxMatrix.shape[0]
		maxColumn = maxMatrix.shape[1]

		new_coords = numpy.zeros((maxRow, maxColumn))
		i = 0
		for item1 in maxMatrix:
			actual = item1
			for item2 in matrix:
				desired = item2
				if i > 0: 
					if numpy.isclose(desired[0], actual[0], atol = (actual[0]*smallTol)) == True:
						new_coords[i][0] = desired[0]
						new_coords[i][1] = desired[1]

				# Uses large tolerance for 0th bead (experiences most lens aberation effects)
				else:
					if numpy.isclose(desired[0], actual[0], atol = (actual[0]*bigTol)) == True:
						new_coords[i][0] = desired[0]
						new_coords[i][1] = desired[1]				
			i += 1

		return numpy.reshape(new_coords,(1, self.maxBeads*2))


	def PFI(self):
		if self.outputpath == '':
			myFile = open(self.outputName, 'a')
			myFile.write("PFI Image Based Bead Centroids (px)\n")
			myFile.write(str(len(self.allNames)) + '\n')
			for item in self.allNames:
				numpy.savetxt(myFile, self.compArray(item, 0.10, 0.35), delimiter = ',')
			myFile.close()

			print "Output data located in: " + self.outputName

		else:
			myFile = open(self.outputpath, 'a')
			myFile.write("PFI Image Based Bead Centroids (px)\n")
			myFile.write(str(len(self.allNames)) + '\n')
			for item in self.allNames:
				numpy.savetxt(myFile, self.compArray(item, 0.10, 0.35), delimiter = ',')
			myFile.close()

			print "Output data located in: " + self.outputpath			

	# def PFI(self):
	# 	myFile = open(self.outputName, 'a')
	# 	myFile.write("PFI Image Based Bead Centroids (px)\n")
	# 	myFile.write(str(len(self.allNames)) + '\n')
	# 	for item in self.allNames:
	# 		numpy.savetxt(myFile, self.compArray(item, 0.10, 0.35), delimiter = ',')
	# 	myFile.close()

	# 	print "Output data located in: " + self.outputName

	def Skyscan(self):
		myFile = open(self.outputName, 'a')
		myFile.write("SkyScan Physical Bead Centroids (mm)\n")
		j = 0
		for item in self.allNames:
			if j < 1:
				skyMtx = self.rearrange(item)
			else:
				skyMtx = numpy.vstack([skyMtx, self.rearrange(item)])
			j += 1
		# Flipped Left/Right to align with PFI scan axes
		# Flipped Up/Down ONLY if cylinder is scanned from BOTTOM to TOP

		#flipskyMtx = numpy.fliplr(numpy.flipud(skyMtx))
		flipskyMtx = numpy.fliplr(skyMtx)
		print flipskyMtx

		# flipRow = flipskyMtx.shape[0]/2 + 1
		# flipCol = flipskyMtx.shape[1]
		# new_coords = numpy.zeros((flipRow, flipCol))

		# k = 0
		# for row in new_coords:
		# 	if k == 0:
		# 		new_coords[k][0] = float(0)
		# 		new_coords[k][1] = float(0)
		# 	else:
		# 		new_coords[k/2][0] = flipskyMtx[k-1][0] - flipskyMtx[k-2][0] + new_coords[k/2 -1][0]
		# 		new_coords[k/2][1] = flipskyMtx[k-1][1] - flipskyMtx[k-2][1] + new_coords[k/2 -1][1]
		# 	k += 2
		# newSky = numpy.reshape(new_coords, (1, flipRow*2))
		
		# # Currently 4.46 microns/pixel
		# numpy.savetxt(myFile, abs(newSky*0.00446), delimiter = ',')
		# print "Output data located in: " + self.outputName
		# myFile.close()

	def unWarped(self):
		with open(self.path) as f:
			for i in range(6):
				f.next()
			for item in f:
				itemList = list(item)


# skyPath = raw_input("PATH to SkyScan centroidFinder.csv file (leave blank if no file): \n")
# pfiPath = raw_input("PATH to PFI centroidFinder.csv file (leave blank if no file): \n")
# #unWarpedPath = raw_input("PATH to PFI unwarped centroidFinder.csv file (leave blank if no file): \n")

# if (os.path.exists(skyPath)) and (os.path.exists(pfiPath)):
# 	Rearranger(skyPath, pfiPath, 's').Skyscan()
# 	Rearranger(pfiPath, pfiPath, 'p').PFI()
# else:
# 	print "Failed path(s)"

TYPE = raw_input("Skyscan or PFI? (s/p): ")
PATH = raw_input("PATH to centroidFinder.csv file: \n")
outputPATH = raw_input("PATH to existing SkyScan centroidFinder.txt (leave blank if no file): \n")


if TYPE.lower() == 'p':
	Rearranger(PATH, outputPATH, TYPE).PFI()
elif TYPE.lower() == 's':
	Rearranger(PATH, outputPATH, TYPE).Skyscan()


