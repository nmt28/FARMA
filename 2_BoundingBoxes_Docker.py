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
    
     
from rios import rat
import numpy as np
import os.path
import osgeo.gdal as gdal
import rsgislib
import rsgislib.imageutils
import rsgislib.rastergis
import rsgislib.imagecalc
import rsgislib.segmentation
import subprocess
from rsgislib import vectorutils
from multiprocessing import Pool
import argparse

def CreateMasks(tile, ModeMaskImage, out_tiles_dir, tile_msk_dir):
    try:
        #########
        # STEP 2: MAKE A MASK OF THE VALID OBJECTS PER TILE (All objects are 1 object)
        # USING EXTENT OF BLANK IMAGE
        ##########
        # in tile name (blank image)
        img_tile = os.path.join(out_tiles_dir, "tile_{0}.kea".format(tile))
        # Input tile objects mosaic image
        tile_mosaic = './tiles_mask.kea'
        # output tile mask name
        out_msk_img = os.path.join(tile_msk_dir, "tile_msk_{0}.kea".format(tile))
        print("Creating {}".format(out_msk_img))
        # Hack to export the segs per tile to a new image
        # Uses bandmath which subsets the resulst to smallest input image
        # step1: put the bands into the banddefns
        bandDefnSeq = [rsgislib.imagecalc.BandDefn('b1', ModeMaskImage, 1), rsgislib.imagecalc.BandDefn('tile', img_tile, 1)]
        # Makes a binary image if b1 (the number in the tiles image) matches the tile number (based on mode).
        # Blank mask image used for image extent only
        if os.path.isfile(out_msk_img):
            pass
            print('Out Mask Image Exists...')
        else:
            rsgislib.imagecalc.bandMath(out_msk_img, 'b1=={}?1:0'.format(tile), 'KEA', rsgislib.TYPE_8UINT, bandDefnSeq)
            # Populate the stats (stats, pyramids etc)
            rsgislib.rastergis.populateStats(clumps=out_msk_img, addclrtab=True, calcpyramids=True, ignorezero=True)
    except Exception as e:
        print(e)
            
def MaskTiles(tile, tile_segs_dir):
    try:
        ########
        # STEP 3: CUT OUT OBJECTS FROM SEGS BASED ON TILE EXTENT (BLANK IMAGE EXTENT)
        ###########
        # set output
        out_segs_img = os.path.join(tile_segs_dir, "tile_segs_{0}.kea".format(tile))
        print("Creating {}".format(out_segs_img))
        # Use the seg file and the blank file
        bandDefnSeq = [rsgislib.imagecalc.BandDefn('b1', file, 1), rsgislib.imagecalc.BandDefn('tile', img_tile, 1)]
        # create new image (binary) of all segs within tile (will cut objects)
        if os.path.isfile(out_segs_img):
            print('out_segs_img exists')
            pass
        else:
            rsgislib.imagecalc.bandMath(out_segs_img, 'b1', 'KEA', rsgislib.TYPE_32UINT, bandDefnSeq)
            # Add stats
            rsgislib.rastergis.populateStats(clumps=out_segs_img, addclrtab=True, calcpyramids=True, ignorezero=True)
    except Exception as e:
        print(e)

def ExtractObjects(tile, tile_segs_msk_dir):
    try:
        ############
        # STEP 4: USE MASK (STEP 2) TO MASK SEGS KEEPING ONLY RELEVANT ONES
        # EACH OBJECT IS ITS OWN OBJECT UNLIKE ALL BEING 1 OBJECT AS IN MASK
        ##############
        # set output
        out_segs_mskd_img = os.path.join(tile_segs_msk_dir, "tile_segs_mskd_{0}.kea".format(tile))
        if os.path.isfile(out_segs_mskd_img):
            print('out_segs_maskd_img exists')
            pass
        else:
            print("Creating {}".format(out_segs_mskd_img))
            # Mask the objects in tile (step 3) by valid objects (mask: step 2)
            rsgislib.imageutils.maskImage(out_segs_img, out_msk_img, out_segs_mskd_img, 'KEA', rsgislib.TYPE_32UINT, 0, 0)
            # Add stats
            rsgislib.rastergis.populateStats(clumps=out_segs_mskd_img, addclrtab=True, calcpyramids=True, ignorezero=True)
    except Exception as e:
        print(e)


def RelabelSegs(tile, tile_segs_msk_lbl_dir):
    try:
        ############
        # STEP 5: RELABEL RAT IN EACH ONE SO ID BEGINS AT 0
        #############
        out_segs_mskd_lbl_img = os.path.join(tile_segs_msk_lbl_dir, "tile_segs_mskd_lbl_{0}.kea".format(tile))
        if os.path.isfile(out_segs_mskd_lbl_img):
            print('out_segs_mskd_lbl_img exists')
        else:
            print("Creating {}".format(out_segs_mskd_lbl_img))
            # Relabel
            rsgislib.segmentation.relabelClumps(out_segs_mskd_img, out_segs_mskd_lbl_img, 'KEA', False)
            rsgislib.rastergis.populateStats(clumps=out_segs_mskd_lbl_img, addclrtab=True, calcpyramids=True, ignorezero=True)
    except Exception as e:
        print(e)
        
def VectorizeSegs(tile, tile_vec_segs_dir):
    try:
        ###############
        # STEP 6: Vecotrize and add layer to GPKG
        ###############
        out_vec = os.path.join(tile_vec_segs_dir, "tile_segs_mskd_lbl_vec{0}.gpkg".format(tile))
        if os.path.isfile(out_vec):
            print('out_vec exists')
            pass
        else:
            out_vec_segs_lyr = "tile_segs_mskd_lbl_vec{0}.gpkg".format(tile)
            rsgislib.vectorutils.polygoniseRaster2VecLyr(out_vec, out_vec_segs_lyr, 'GPKG', out_segs_mskd_lbl_img, imgBandNo=1, maskImg=out_segs_mskd_lbl_img, imgMaskBandNo=1, replace_file=False, replace_lyr=True, pxl_val_fieldname='PXLVAL')
    except Exception as e:
        print(e)
            
        
def main():
    print("Use 'python 2_BoundingBoxes_Docker.py -h' for help")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Specify the input Segmentation KEA file")
    parser.add_argument("-m", "--mode", type=str, help="Specify the mode tiles mask KEA file (from script 1)")
    parser.add_argument("-r", "--resolution", type=float, help="Specify the segmentation KEA resolution")
    parser.add_argument("-c", "--cores", type=int, help="Specify the number of cores to use")
    args = parser.parse_args()

    segs = args.input
    
    # Create folders
    # Base directory
    basedir = '/'.join(segs.split('/')[:-2]) + '/'
    # Base tiles
    out_tiles_dir = basedir + '/1_base_tiles/'
    if os.path.isdir(out_tiles_dir):
        pass
    else:
        subprocess.call('mkdir ' + out_tiles_dir)
    # Tile masks
    tile_msk_dir = basedir + '/2_tile_msks/'
    if os.path.isdir(tile_msk_dir):
        pass
    else:
        subprocess.call('mkdir ' + tile_msk_dir)
    # Tile segs
    tile_segs_dir = basedir + '/3_seg_tiles/'
    if os.path.isdir(tile_segs_dir):
        pass
    else:
        subprocess.call('mkdir ' + tile_segs_dir)
    # Seg mask tiles
    tile_segs_msk_dir = basedir + '/4_seg_msk_tiles/'
    if os.path.isdir(tile_segs_msk_dir):
        pass
    else:
        subprocess.call('mkdir ' + tile_segs_msk_dir)
    # Seg mask tiles labels
    tile_segs_msk_lbl_dir = basedir + '/5_seg_msk_lbl_tiles/'
    if os.path.isdir(tile_segs_msk_lbl_dir):
        pass
    else:
        subprocess.call('mkdir ' + tile_segs_msk_lbl_dir)
    # tiled vector segs
    tile_vec_segs_dir = basedir + '/6_GPKGs/'
    if os.path.isdir(tile_vec_segs_dir):
        pass
    else:
        subprocess.call('mkdir ' + tile_vec_segs_dir)


    # get segmentation projection
    wkt_str = rsgislib.imageutils.getWKTProjFromImage(file)
    #open segmentation
    ratDataset = gdal.Open(segs, gdal.GA_Update)

    # Import Columns
    print("Importing Columns...")
    try:
        TileID = rat.readColumn(ratDataset, "tiles")
    except:
        print('Run 1_CreateRegGrid.py first')
        os._exit(1)
    
    # Get extent per object
    MinXX = rat.readColumn(ratDataset, "MinXX")
    MinXY = rat.readColumn(ratDataset, "MinXY")
    MaxXX = rat.readColumn(ratDataset, "MaxXX")
    MaxXY = rat.readColumn(ratDataset, "MaxXY")
    MinYX = rat.readColumn(ratDataset, "MinYX")
    MinYY = rat.readColumn(ratDataset, "MinYY")
    MaxYX = rat.readColumn(ratDataset, "MaxYX")
    MaxYY = rat.readColumn(ratDataset, "MaxYY")


    # Reuce tile id numbers to a unique list of ID's
    tiles = np.unique(TileID)

    ###########
    # STEP 1: CREATE A BLANK IMAGE FROM THE BBOX OF EACH OBJECT THAT IS WITHIN BOUNDS OF A TILE
    ############

    # Set up blank list to hold files we will use
    tiles_used = []
    for tile in tiles:
        # bin_tiles: where the TileID matches the tile number (array of true or false)
        bin_tiles = TileID==tile
        # Get MinXX for True values and get their minimum (np.min) X dimension
        # Gets the overall min per tile extent
        minX = np.min(MinXX[bin_tiles])
        minY = np.min(MinYY[bin_tiles])
        maxX = np.max(MaxXX[bin_tiles])
        maxY = np.max(MaxYY[bin_tiles])
        
        # Set the bounding box dimensions
        bbox = [minX, maxX, minY, maxY]
        print("{0}: [{1}, {2}, {3}, {4}]".format(tile, minX, maxX, minY, maxY))
        # Check the tile is valid
        if (minX!=maxX) and (minY!=maxY):
            # Set the tile name
            img_tile = os.path.join(out_tiles_dir, "tile_{0}.kea".format(tile))
            print("Creating {}".format(img_tile))
            # create a blank image per tile
            rsgislib.imageutils.createBlankImgFromBBOX(bbox, wkt_str, img_tile, args.resolution, 0, 1, 'KEA', rsgislib.TYPE_32UINT, snap2grid=True)
            # HACK TO REMOVE REALLY BIG TILES: Only appends small tiles
            # Appends the tile number only
            if ((maxX-minX) < 50000) and ((maxY-minY) < 50000):
                tiles_used.append(tile)

    # Close the Seg file
    ratDataset = None

    ncores = int(args.cores)
    p = Pool(ncores)
    p.map(CreateMasks, tiles_used, out_tiles_dir, tile_msk_dir)
    p.map(MaskTiles, tile, tile_segs_dir)
    p.map(ExtractObjects, tile, tile_segs_msk_dir)
    p.map(RelabelSegs, tile, tile_segs_msk_lbl_dir)
    p.map(VectorizeSegs, tile, tile_vec_segs_dir)


if __name__ == "__main__":
    main()
