import ROOT
from ROOT import TCanvas, TFile, TProfile, TNtuple, TH1F, TH2F,THStack
import numpy as np
import copy
import sys, getopt
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Script to rebin histogram")

    # Define the command-line arguments with default values.
    parser.add_argument("--filename", help="Filename", required=True)
    parser.add_argument("--bin_condition", type=int, default=1, help="Specify bin condition (default: 1)")
    parser.add_argument("--bin_uncert_fraction", type=float, default=100.0, help="Specify bin uncertainty fraction (default: 10.0)")

    return parser.parse_args()

def CreateRebin(filename, fileout, bin_condition, bin_uncert_fraction):
    File1 = ROOT.TFile.Open( filename,"READ")
    Fileout = ROOT.TFile.Open( fileout,"RECREATE");
    for a in File1.GetListOfKeys():
        if ("nominal" in a.GetName()) & ("data_obs" in a.GetName()):
            data = File1.Get(a.GetName())
    total_bkg = TH1F("","", data.GetNbinsX(),
        data.GetXaxis().GetBinLowEdge(1), data.GetXaxis().GetBinLowEdge(data.GetNbinsX()+1))
    for a in File1.GetListOfKeys():
        if ("nominal" in a.GetName()) & ("data_obs" not in a.GetName()):
            total_bkg.Add(File1.Get(a.GetName()))
    nbins = total_bkg.GetNbinsX()
    init_bins = [total_bkg.GetBinLowEdge(i) for i in range(1, nbins + 2)]
    new_bins = FindNewBinning(total_bkg, init_bins, bin_condition, bin_uncert_fraction, 1)
    print(new_bins)
    for a in File1.GetListOfKeys():
        h1 = File1.Get(a.GetName());
        h2 = TH1F("","", h1.GetNbinsX(), h1.GetXaxis().GetBinLowEdge(1), h1.GetXaxis().GetBinLowEdge(h1.GetNbinsX()+1))
        h2.Add(h1)
        h3 = h2.Rebin(len(new_bins)-1, a.GetName(), np.array(new_bins))
        h3.Write()
    Fileout.Write()
    Fileout.Close()
    File1.Close()

def get_maximum_frac_uncert_bin(total_bkg):
    idx = 1
    maximum = 0
    for i in range(1, total_bkg.GetNbinsX() + 1):
        if total_bkg.GetBinError(i) / total_bkg.GetBinContent(i) > maximum:
            maximum = total_bkg.GetBinError(i) / total_bkg.GetBinContent(i)
            idx = i
    return idx

def FindNewBinning(total_bkg, new_bins, bin_condition, bin_uncert_fraction, mode):
    all_bins = True
    v_=1
    # Find the maximum bin
    hbin_idx = total_bkg.GetMaximumBin()
    nbins = total_bkg.GetNbinsX()
    print("Searching for bins failing condition "
          "using algorithm mode:", mode)

    lbin_idx = total_bkg.GetMinimumBin()
    herrbin_idx = get_maximum_frac_uncert_bin(total_bkg)
    bin_tot_flag = total_bkg.GetBinContent(lbin_idx) <= bin_condition
    bin_err_flag = total_bkg.GetBinError(herrbin_idx) / total_bkg.GetBinContent(herrbin_idx) >= bin_uncert_fraction

    if bin_tot_flag or bin_err_flag:
        lbin_idx = lbin_idx if bin_tot_flag else herrbin_idx
        if v_ > 0 and bin_tot_flag:
            print("[AutoRebin::FindNewBinning] Testing bins of total_bkg hist to find those with entry <=", bin_condition, "starting from bin:", lbin_idx)
        if v_ > 0 and not bin_tot_flag:
            print("[AutoRebin::FindNewBinning] Testing bins of total_bkg hist to find those with fractional error >=", bin_uncert_fraction, "starting from bin:", lbin_idx)
        left_tot = total_bkg.GetBinContent(lbin_idx)
        left_err_tot = total_bkg.GetBinError(lbin_idx)
        idx = lbin_idx - 1
        
        while (((bin_tot_flag and left_tot <= bin_condition) or (not bin_tot_flag and left_err_tot / left_tot >= bin_uncert_fraction)) and idx > 0):
            left_err_tot = np.sqrt(left_err_tot**2 + total_bkg.GetBinError(idx)**2)
            left_tot = left_tot + total_bkg.GetBinContent(idx)
            print("Moving left, bin index:", idx, ", Bin content:", total_bkg[idx], ", Running total from combining bins:", left_tot, ", Current fractional error:", left_err_tot / left_tot)
            idx -= 1
            
        left_bins = lbin_idx - idx
        right_tot = total_bkg.GetBinContent(lbin_idx)
        right_err_tot = total_bkg.GetBinError(lbin_idx)
        idx = lbin_idx + 1
        
        while (((bin_tot_flag and right_tot <= bin_condition) or (not bin_tot_flag and right_err_tot / right_tot >= bin_uncert_fraction)) and idx < nbins):
            right_err_tot = np.sqrt(right_err_tot**2 + total_bkg.GetBinError(idx)**2)
            right_tot = right_tot + total_bkg.GetBinContent(idx)
            print("Moving right, bin index:", idx, ", Bin content:", total_bkg[idx], ", Running total from combining bins:", right_tot, ", Current fractional error:", right_err_tot / right_tot)
            idx += 1
            
        right_bins = idx - lbin_idx
        left_pass = left_tot > bin_condition if bin_tot_flag else left_err_tot / left_tot < bin_uncert_fraction
        right_pass = right_tot > bin_condition if bin_tot_flag else right_err_tot / right_tot < bin_uncert_fraction
        
        if left_pass and not right_pass:
            print("Merging left using", left_bins - 1, "bins")
            [new_bins.remove(total_bkg.GetBinLowEdge(i)) for i in range(lbin_idx, lbin_idx - left_bins + 1, -1)]
        elif right_pass and not left_pass:
            if v_ > 0:
                print("Merging right using", right_bins - 1, "bins")
            new_bins = [edge for i, edge in enumerate(new_bins) if i not in range(lbin_idx, lbin_idx + right_bins - 1)]
        elif left_pass and right_pass and left_bins < right_bins:
            if v_ > 0:
                print("Merging left using", left_bins - 1, "bins")
            [new_bins.remove(total_bkg.GetBinLowEdge(i)) for i in range(lbin_idx, lbin_idx - left_bins + 1, -1)]
        elif left_pass and right_pass and left_bins > right_bins:
            if v_ > 0:
                print("Merging right using", right_bins - 1, "bins")
            new_bins = [edge for i, edge in enumerate(new_bins) if i not in range(lbin_idx, lbin_idx + right_bins - 1)]
        elif left_pass and right_pass and left_bins == right_bins and lbin_idx < hbin_idx:
            if v_ > 0:
                print("Merging right using", right_bins - 1, "bins")
            new_bins = [edge for i, edge in enumerate(new_bins) if i not in range(lbin_idx, lbin_idx + right_bins - 1)]
        elif left_pass and right_pass and left_bins == right_bins and lbin_idx > hbin_idx:
            if v_ > 0:
                print("Merging left using", left_bins - 1, "bins")
            [new_bins.remove(total_bkg.GetBinLowEdge(i)) for i in range(lbin_idx, lbin_idx - left_bins + 1, -1)]
        elif not left_pass and not right_pass:
            print("WARNING: No solution found to satisfy condition, try merging all bins")
            new_bins = []
    #TH1F* total_bkg_new
    print(len(new_bins)-1)
    print(new_bins)
    total_bkg_new = total_bkg.Rebin(len(new_bins)-1, "total_bkg_new", np.array(new_bins)) 
            
    nbins_new = len(new_bins) - 1
    new_new = new_bins.copy() 
    if nbins_new != nbins:
        if v_ > 0:
            print()
        if v_ > 0:
            print("[AutoRebin::FindNewBinning] New binning found:")
        for i in range(1, nbins_new + 1):
            if v_ > 0:
                print("Bin index:", i, ", BinLowEdge:", new_bins[i - 1], ", Bin content:", total_bkg_new.GetBinContent(i), ", Bin error fraction:", total_bkg_new.GetBinError(i)/ total_bkg_new.GetBinContent(i))
            if (total_bkg_new.GetBinContent(i) <= bin_condition or total_bkg_new.GetBinError(i) / total_bkg_new.GetBinContent(i) >= bin_uncert_fraction) and i != nbins_new + 1:
                all_bins = False

    if all_bins:
        return new_new
    else:
        return FindNewBinning(total_bkg_new, new_bins, bin_condition, bin_uncert_fraction, mode)

if __name__ == "__main__":
    args = parse_arguments()

    filename = args.filename
    bin_condition = args.bin_condition
    bin_uncert_fraction = args.bin_uncert_fraction
    fileout = filename[:-12] +".root"
    CreateRebin(filename, fileout, bin_condition, bin_uncert_fraction)
    print(f"Output filename : {fileout}")
    print(f"Filename specified: {filename}")
    print(f"Bin condition specified: {bin_condition}")
    print(f"Bin uncertainty fraction specified: {bin_uncert_fraction}")

