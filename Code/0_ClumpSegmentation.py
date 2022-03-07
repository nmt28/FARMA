# -*- coding: utf-8 -*-
''' Author: Nathan Thomas
    Email: nathan.m.thomas@nasa.gov, @DrNASApants
    Date: 11/26/2020
    Version: 2.0
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
import rsgislib.tools.filetools
import argparse
import os


def ClumpSegmentation(args):

    segs = args.input
    
    basename = rsgislib.tools.filetools.get_file_basename(segs)
    dir_path = os.path.dirname(segs)
    out_img_name = '{}_clumps.kea'.format(basename)
    out_img_path = os.path.join(dir_path, out_img_name)
    print(out_img_path)
    if not os.path.isfile(out_img_path):
        ClumpMethod = args.method
        
        if ClumpMethod == "CLUMP_RAM":
            rsgislib.segmentation.clump(args.input, out_img_path, 'KEA', True, 0, False)
        elif ClumpMethod == "CLUMP_DISK":
            rsgislib.segmentation.clump(args.input, out_img_path, 'KEA', False, 0, False)
        elif ClumpMethod == "TILED_SINGLE":
            rsgislib.segmentation.tiledclump.perform_clumping_single_thread(segs, out_img_path, tmp_dir='tmp', width=args.tilesize, height=args.tilesize, gdalformat='KEA')
        elif ClumpMethod == "TILED_MULTI":
            rsgislib.segmentation.tiledclump.perform_clumping_multi_process(segs, out_img_path, tmp_dir='tmp', width=args.tilesize, height=args.tilesize, gdalformat='KEA', nCores=args.cores)
        else:
            raise Exception("Specified method ({}) was not recognised".format(ClumpMethod))
                
        rsgislib.rastergis.pop_rat_img_stats(clumps_img=out_img_path, add_clr_tab=True, calc_pyramids=True, ignore_zero=True)
    else:
        print("CLUMP FILE EXISTS: SKIPPING")

    


def main():
    print("Use 'python 0_ClumpSegmentation.py -h' for help")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Specify the input Segmentation")
    parser.add_argument("-m", "--method", type=str, help="Specify the clumping method from CLUMP_RAM, CLUMP_DISK, TILED_SINGLE, TILED_MULTI")
    parser.add_argument("-c", "--cores", type=int, help="Specify the number of cores")
    parser.add_argument("-t", "--tilesize", type=int, help="Specify the tilesize in pixels in the X dimension")
    args = parser.parse_args()

    if args.input == None:
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


