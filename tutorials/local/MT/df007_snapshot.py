import PyRDF
import ROOT

ROOT.ROOT.EnableImplicitMT()

# A simple helper function to fill a test tree: this makes the example stand-alone.
def fill_tree(treeName, fileName):
    rdf = PyRDF.RDataFrame(10000)
    rdf.Define("b1", "(int) rdfentry_")\
       .Define("b2", "(float) rdfentry_ * rdfentry_").Snapshot(treeName, fileName)

# We prepare an input tree to run on
fileName = "df007_snapshot_py.root"
outFileName = "df007_snapshot_output_py.root"
outFileNameAllColumns = "df007_snapshot_output_allColumns_py.root"
treeName = "myTree"
fill_tree(treeName, fileName)

# We read the tree from the file and create a RDataFrame.
d = PyRDF.RDataFrame(treeName, fileName)

# ## Select entries
# We now select some entries in the dataset
d_cut = d.Filter("b1 % 2 == 0")

# ## Enrich the dataset
# Build some temporary columns: we'll write them out
PyRDF.include_headers("tutorials/headers/df007_snapshot.h")
d2 = d_cut.Define("b1_square", "b1 * b1") \
          .Define("b2_vector", "getVector( b2 )")

# ## Write it to disk in ROOT format
# We now write to disk a new dataset with one of the variables originally
# present in the tree and the new variables.
# The user can explicitly specify the types of the columns as template
# arguments of the Snapshot method, otherwise they will be automatically
# inferred.
branchList = ROOT.vector('string')()
for branchName in ["b1", "b1_square", "b2_vector"]:
    branchList.push_back(branchName)
d2.Snapshot(treeName, outFileName, branchList)

# Open the new file and list the columns of the tree
f1 = ROOT.TFile(outFileName)
t = f1.myTree
print("These are the columns b1, b1_square and b2_vector:")
for branch in t.GetListOfBranches():
    print("Branch: %s" %branch.GetName())
f1.Close()

# We are not forced to write the full set of column names. We can also
# specify a regular expression for that. In case nothing is specified, all
# columns are persistified.
d2.Snapshot(treeName, outFileNameAllColumns)

# Open the new file and list the columns of the tree
f2 = ROOT.TFile(outFileNameAllColumns)
t = f2.myTree
print("These are all the columns available to this tdf:")
for branch in t.GetListOfBranches():
    print("Branch: %s" %branch.GetName())
f2.Close()

# We can also get a fresh RDataFrame out of the snapshot and restart the
# analysis chain from it.
branchList.clear()
branchList.push_back("b1_square")
snapshot_tdf = d2.Snapshot(treeName, outFileName, branchList);
h = snapshot_tdf.Histo1D("b1_square")
c = ROOT.TCanvas()
h.Draw()
