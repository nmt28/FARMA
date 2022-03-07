# -*- coding: utf-8 -*-
''' Author: Nathan Thomas
    Email: nathan.m.thomas@nasa.gov, @DrNASApants
    Date: 11/26/2020
    Version: 2.0
    Copyright 2020 Nathan M Thomas
    
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

# A script to use RSGISLib to prepare a KEA format
# segmentation for the FARMA workflow.
# A Regular grid with a user specifed tile size is generated
# and is populated into the segmentation, alongside the dimensions
# (max extent) of each object

import rsgislib.segmentation
import rsgislib.rastergis
import argparse
import os


def PrepareSegmentation(args):

    segs = args.input

    # Create Regular Grid
    RegGrid = segs.replace('.kea','_regGrid.kea')
    if os.path.isfile(RegGrid):
        print('Regular Grid Exists: Skipping')
    else:
        rsgislib.segmentation.generate_regular_grid(segs, RegGrid, 'KEA', args.tilesize, args.tilesize)

    # Populate RAT with statistics
    rsgislib.rastergis.pop_rat_img_stats(clumps_img=segs, add_clr_tab=True, calc_pyramids=True, ignore_zero=True)

    # Populate RAT with Mode Regular Grid Value
    rsgislib.rastergis.populate_rat_with_mode(input_img=RegGrid, clumps_img=segs, out_cols_name='tiles', use_no_data=False, no_data_val=0, out_no_data=False, mode_band=1, rat_band=1)

    # Populate RAT with spatial extent of each object
    rsgislib.rastergis.clumps_spatial_extent(clumps_img=segs, min_xx='MinXX', min_xy='MinXY', max_xx='MaxXX', max_xy='MaxXY', min_yx='MinYX', min_yy='MinYY', max_yx='MaxYX', max_yy='MaxYY')
    
    # Create a an image of the tiles.
    modeTileMsk = segs.replace('.kea','_modeTileMsk.kea')
    if os.path.isfile(modeTileMsk):
        print('File Exists: skipping')
    else:
        rsgislib.rastergis.export_col_to_gdal_img(segs, modeTileMsk, 'KEA', rsgislib.TYPE_16UINT, 'tiles')
        rsgislib.rastergis.pop_rat_img_stats(clumps_img=modeTileMsk, add_clr_tab=True, calc_pyramids=True, ignore_zero=True)


def main():
    print("Use 'python 1_CreateRegGrid.py -h' for help")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Specify the input Segmentation KEA file")
    parser.add_argument("-t", "--tilesize", type=int, help="Specify the tiling size (X dimension) in pixels (e.g. 1000)")
    args = parser.parse_args()

    if str(args.input).endswith('.kea'):
        pass
    else:
        print("INPUT SEGMENTATION FILE MUST END '.kea'")
        os._exit(1)
        
    if args.tilesize == None:
        print("SPECIFY THE TILE SIZE IN PIXELS")
        os._exit(1)

    PrepareSegmentation(args)


if __name__ == "__main__":
    main()

