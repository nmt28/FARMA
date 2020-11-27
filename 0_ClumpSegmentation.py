# -*- coding: utf-8 -*-
''' Author: Nathan Thomas
    Email: nathan.m.thomas@nasa.gov, @DrNASApants
    Date: 11/26/2020
    Version: 1.0
    Copyright 2020 Natha M Thomas
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.'''

# A script to use RSGISLib to prepare KEA format
# segmentation clumps for the FARMA workflow.
# Multiple methods of clumping are avaialable
# depending upon RAM/CORES available

import rsgislib.segmentation
import rsgislib.rastergis
import argparse


def ClumpSegmentation(args):

    segs = args.input
    
    ClumpMethod = args.method
    
    if ClumpMethod == "CLUMP_RAM":
        outputimage = segs.split('.')[0] + '_clumps.kea'
        if os.path.isfile(outputimage):
            print("CLUMP FILE EXISTS: SKIPPING")
        else:
            rsgislib.segmentation.clump(args.input, outputimage, 'KEA', True, 0, False)
            
    if ClumpMethod == "CLUMP_DISK":
        outputimage = segs.split('.')[0] + '_clumps.kea'
        if os.path.isfile(outputimage):
            print("CLUMP FILE EXISTS: SKIPPING")
        else:
            rsgislib.segmentation.clump(args.input, outputimage, 'KEA', False, 0, False)
            
    if ClumpMethod == "TILED_SINGLE":
        outputimage = segs.split('.')[0] + '_clumps.kea'
        if os.path.isfile(outputimage):
            print("CLUMP FILE EXISTS: SKIPPING")
        else:
            rsgislib.segmentation.tiledclump.performClumpingSingleThread(segs, outputimage, tmpDIR='tmp', width=args.tilesize, height=args.tilesize, gdalformat='KEA')
            
    if ClumpMethod == "TILED_MULTI":
        outputimage = segs.split('.')[0] + '_clumps.kea'
        if os.path.isfile(outputimage):
            print("CLUMP FILE EXISTS: SKIPPING")
        else:
            rsgislib.segmentation.tiledclump.performClumpingMultiProcess(segs, outputimage, tmpDIR='tmp', width=args.tilesize, height=args.tilesize, gdalformat='KEA', nCores=args.cores)
        

    


def main():
    print("Use 'python 0_ClumpSegmentation.py -h' for help")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Specify the input Segmentation")
    parser.add_argument("-m", "--method", type=str, help="Specify the clumping method from CLUMP_RAM, CLUMP_DISK, TILED_SINGLE, TILED_MULTI")
    parser.add_argument("-c", "--cores", type=int, help="Specify the number of cores")
    parser.add_argument("-t", "--tilesize", type=int, help="Specify the tilesize in pixels in the X dimension")
    args = parser.parse_args()

    if str(args.input) == None:
        print("INPUT SEGMENTATION MISSING")
        os._exit(1)
    elif args.method == None:
        print("Specify the clumping method from CLUMP_RAM, CLUMP_DISK, TILED_SINGLE, TILED_MULTI")
        os._exit(1)
    else:
        print(args.input, args.method)
        
    if args.method == "TILED_SINGLE":
        if args.tilesize==None:
            print("TILE SIZE IN PIXELS MUST BE SPECIFIED FOR TILED CLUMPING")
        else:
            print(args,method, args.tilesize)
    elif args.method == "TILED_MULTI":
        if args.cores == None:
            print("NUMBER OF CORES MUST BE SPECIFIED")
        elif args.tilesize == None:
            print("TILE SIZE IN PIXELS MUST BE SPECIFIED FOR TILED CLUMPING")
        else:
            print(args.method, args.cores, args.tilesize)

    ClumpSegmentation(args)


if __name__ == "__main__":
    main()


